#!/usr/bin/env python3
"""Collect public feeds for GitHub Pages. No API keys, dependencies, or fabricated data."""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import email.utils
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "live"
UTC = dt.timezone.utc
AIS = "https://hormuz.data-tracking.net"
EUM = "https://view.eumetsat.int/geoserver/wms"
GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"
NS = {"w": "http://www.opengis.net/wms"}


def now():
    return dt.datetime.now(UTC).isoformat().replace("+00:00", "Z")


def fetch(url, as_json=True):
    # curl uses the same TLS/network stack locally and in GitHub-hosted runners.
    result = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--location",
         "--max-time", "40", "--retry", "1", "--retry-delay", "1", url],
        capture_output=True, check=True, timeout=90)
    if len(result.stdout) > 20_000_000:
        raise ValueError("Feed exceeds size limit")
    return json.loads(result.stdout) if as_json else result.stdout


def nonempty_list(data):
    if not isinstance(data, list):
        raise ValueError("Expected a list")
    return data


def source(name, url, license):
    return {"name": name, "url": url, "license": license}


def ais_feed(path, kind):
    data = fetch(AIS + path)
    if kind == "summary":
        if not isinstance(data, dict) or "last_poll" not in data or "total_ships" not in data:
            raise ValueError("Invalid summary response")
        observed = data["last_poll"]
    else:
        nonempty_list(data)
        if kind == "ships":
            if not data or not all(isinstance(x, dict) and "latitude" in x and "timestamp" in x for x in data):
                raise ValueError("Invalid position response")
            # Keep the original site's commercial-shipping scope.
            data = [s for s in data if not re.search(r"military|naval|warship", str(s.get("ship_category", "")), re.I)]
            observed = max((s.get("timestamp", "") for s in data), default=None)
        else:
            observed = None  # Collection check time is not an event time.
    return data, observed, source("Hormuz Ship Monitor", AIS + path, "CC BY 4.0; see provider usage terms")


def incidents():
    raw = fetch(AIS + "/api/incidents")
    table, strings = raw["t"], raw["s"]
    rows = []
    for values in table["r"]:
        row = {key: (strings[value] if index in table["k"] and isinstance(value, int)
                     and 0 <= value < len(strings) else value)
               for index, (key, value) in enumerate(zip(table["c"], values))}
        if isinstance(row.get("ts"), (int, float)):
            row["time"] = dt.datetime.fromtimestamp(row["ts"], UTC).isoformat()
        rows.append(row)
    rows.sort(key=lambda r: r.get("ts", 0), reverse=True)
    observed = dt.datetime.fromtimestamp(raw["built"], UTC).isoformat()
    return rows, observed, source("UKMTO via Hormuz Ship Monitor", "https://www.ukmto.org/", raw.get("attribution", "Open Government Licence v3.0"))


def conditions(kind):
    if kind == "weather":
        url = ("https://api.open-meteo.com/v1/forecast?latitude=26.6&longitude=56.5"
               "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m"
               "&hourly=wind_speed_10m,wind_direction_10m,visibility,temperature_2m"
               "&wind_speed_unit=kn&timezone=UTC&forecast_days=3")
    else:
        url = ("https://marine-api.open-meteo.com/v1/marine?latitude=26.2&longitude=56.5"
               "&current=wave_height,wave_direction,wave_period,sea_surface_temperature"
               "&hourly=wave_height,wave_period&timezone=UTC&forecast_days=3")
    data = fetch(url)
    if "current" not in data or "time" not in data["current"]:
        raise ValueError("Missing model valid time")
    return data, data["current"]["time"] + "Z", source("Open-Meteo / DWD and partner models", url, "CC BY 4.0; free API for non-commercial use")


def satellite():
    root = ET.fromstring(fetch(EUM + "?service=WMS&request=GetCapabilities&version=1.3.0", False))
    wanted = {
        "msg_iodc:ir108": ("Meteosat · thermal infrared", "Infrared cloud imagery, day and night. Regional weather detail; not vessel-resolution imagery."),
        "msg_iodc:rgb_natural": ("Meteosat · natural color", "Visible / near-infrared composite. Daylight required; clouds can obscure the surface."),
        "msg_iodc:rgb_dust": ("Meteosat · dust RGB", "False-color atmospheric dust product; colors are not a photograph of the surface."),
    }
    layers = []
    for item in root.findall(".//w:Layer", NS):
        name = item.findtext("w:Name", "", NS)
        if name in wanted:
            dim = next((x for x in item.findall("w:Dimension", NS) if x.get("name") == "time"), None)
            if dim is None or not dim.get("default"):
                continue
            layers.append({"id": name, "name": wanted[name][0], "description": wanted[name][1],
                           "latest": dim.get("default"), "intervalMinutes": 15,
                           "resolution": "~3 km at nadir; coarser away from satellite center",
                           "range": dim.text, "service": EUM, "type": "wms"})
    if not layers:
        raise ValueError("No Indian Ocean layers in WMS metadata")
    return layers, max(l["latest"] for l in layers), source("EUMETSAT EUMETView", "https://view.eumetsat.int/", "© EUMETSAT; EUMETView attribution required")


def scenes():
    url = ("https://earth-search.aws.element84.com/v1/search?collections=sentinel-2-l2a"
           "&bbox=55.5,25.8,57.1,27.3&limit=12&sortby=-properties.datetime")
    raw = fetch(url)
    rows = []
    for f in raw["features"]:
        p, assets = f["properties"], f["assets"]
        rows.append({"id": f["id"], "time": p["datetime"], "cloudCover": p.get("eo:cloud_cover"),
                     "platform": p.get("platform", "Sentinel-2"), "bbox": f["bbox"],
                     "thumbnail": assets.get("thumbnail", {}).get("href"),
                     "visual": assets.get("visual", {}).get("href"),
                     "url": next((l["href"] for l in f.get("links", []) if l["rel"] == "self"), url)})
    return rows, max((r["time"] for r in rows), default=None), source("Copernicus Sentinel-2 / Element 84 Earth Search", "https://earth-search.aws.element84.com/v1", "Contains modified Copernicus Sentinel data; Element 84 Earth Search")


def earthquakes():
    start = (dt.datetime.now(UTC) - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    url = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
           "&minlatitude=22&maxlatitude=40&minlongitude=44&maxlongitude=65"
           f"&minmagnitude=2.5&orderby=time&limit=100&starttime={start}")
    data = fetch(url)
    if data.get("type") != "FeatureCollection":
        raise ValueError("Invalid GeoJSON")
    return data, dt.datetime.fromtimestamp(data["metadata"]["generated"] / 1000, UTC).isoformat(), source("USGS Earthquake Hazards Program", url, "USGS public domain data")


def news():
    feeds = [
        ("BBC News", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", False),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", True),
    ]
    rows, errors = [], []
    for label, url, filter_region in feeds:
        try:
            root = ET.fromstring(fetch(url, False))
            for item in root.findall(".//item"):
                title, link = item.findtext("title", ""), item.findtext("link", "")
                if filter_region and not re.search(r"iran|hormuz|gulf|oman|israel|lebanon|yemen|shipping|middle east", title, re.I):
                    continue
                if not link.startswith("https://"):
                    continue
                try:
                    published = email.utils.parsedate_to_datetime(item.findtext("pubDate", "")).astimezone(UTC).isoformat()
                except (ValueError, TypeError):
                    continue
                # Headline and link only. No copied article bodies.
                rows.append({"title": title, "url": link, "published": published, "publisher": label})
        except Exception as exc:
            errors.append(label + ": " + type(exc).__name__)
    if not rows:
        raise ValueError("All news feeds unavailable")
    rows.sort(key=lambda r: r["published"], reverse=True)
    return {"articles": rows[:40], "feedErrors": errors}, None, source("BBC News / Al Jazeera RSS", "https://www.bbc.com/news/world/middle_east", "Headlines © their respective publishers; linked articles remain on publisher sites")


JOBS = {
    "summary": lambda: ais_feed("/api/summary?hours=24", "summary"),
    "ships": lambda: ais_feed("/api/ships", "ships"),
    "crossings": lambda: ais_feed("/api/crossings?hours=48&direction=completed&limit=200", "crossings"),
    "daily": lambda: ais_feed("/api/crossings/daily?days=30", "daily"),
    "incidents": incidents,
    "weather": lambda: conditions("weather"),
    "marine": lambda: conditions("marine"),
    "satellite": satellite,
    "scenes": scenes,
    "earthquakes": earthquakes,
    "news": news,
}


def collect(name):
    path = OUT / (name + ".json")
    try:
        data, observed, src = JOBS[name]()
        result = {"schemaVersion": 1, "ok": True, "fetchedAt": now(), "observedAt": observed,
                  "source": src, "data": data}
        status = {"status": "ok", "fetchedAt": result["fetchedAt"], "observedAt": observed}
    except Exception as exc:
        # Preserve the last successful acquisition and timestamps on failures.
        error = type(exc).__name__ + ": source request or validation failed"
        try:
            result = json.loads(path.read_text())
        except (OSError, ValueError):
            result = {"schemaVersion": 1, "ok": False, "data": None, "fetchedAt": None, "observedAt": None}
        result["lastFailure"] = {"time": now(), "message": error}
        status = {"status": "cached" if result.get("ok") else "unavailable", "error": error,
                  "fetchedAt": result.get("fetchedAt"), "observedAt": result.get("observedAt")}
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temp.replace(path)
    return name, status


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        statuses = dict(pool.map(collect, JOBS))
    (OUT / "status.json").write_text(json.dumps({"generatedAt": now(), "feeds": statuses}, indent=2))
    for key, value in statuses.items():
        print(key + ": " + value["status"])
    if all(s["status"] == "unavailable" for s in statuses.values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
