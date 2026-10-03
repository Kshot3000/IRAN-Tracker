# Hormuz HQ — Strait of Hormuz Maritime Observatory

*Formerly IRAN Tracker — now published at [hormuzhq.xyz](https://hormuzhq.xyz/).*

A public-source observatory for Iran, the Strait of Hormuz, and commercial traffic in the Persian Gulf and Gulf of Oman. Plain HTML, CSS, and JavaScript. No frontend build, secret keys, account setup, or paid service is required for the included public-data integrations.

**Start with [START-HERE.md](START-HERE.md) to update the repository and turn on automatic refreshes.**

## Features

- Responsive map dashboard; accessible navigation; light/dark themes; reduced-motion support.
- Real source-provided commercial vessel positions. Fast map filtering, explorer search by name / source identifier / flag / destination, sort, pagination, details, local watchlists and CSV exports.
- Source crossing summary over 24 hours, latest detections over 48 hours, and a 30-day inbound/outbound chart. Today's UTC bar is partial.
- Recent Meteosat Indian Ocean imagery with published timestamps, thermal infrared, natural color and dust RGB, plus six-hour playback. Direct EUMETSAT metadata refresh at 15-minute intervals while this view is open.
- NASA VIIRS daily true-color map with date selection; Esri historical basemap; Sentinel-2 catalog search around Hormuz with acquisition time, scene cloud cover, thumbnail and visual GeoTIFF links.
- Forecast model weather / waves / sea temperature, attributed UKMTO reporting, BBC / Al Jazeera RSS headlines, and USGS regional earthquake events.
- Feed health, separate fetch and observation times, safe rendering, export formula protection, timeout handling, per-source failures and last-good snapshot preservation. No mock shipping data.

## Architecture

`index.html`, `style.css`, `app.js`, `core.mjs` and locally bundled Leaflet 1.9.4 are the frontend. `scripts/refresh_data.py` uses Python standard libraries and curl to fetch public feeds. It writes JSON envelopes to `data/live/` with source, license, fetchedAt, observedAt, data and optional lastFailure fields.

The shipping service and RSS feeds do not expose cross-origin browser access. A server-side GitHub Actions collector legally consumes their documented public endpoints and serves snapshots from the same Pages origin. No public CORS proxy or exposed API key is used. EUMETSAT imagery and metadata can be read directly by browsers.

`.github/workflows/pages.yml` collects and publishes on `main` pushes, manual runs, and at minutes 17 and 47 each hour. A cache restores last-good data before collection. A failed provider keeps its successful snapshot and original timestamps. Every feed failing without any usable snapshot stops the workflow. Partial failures still deploy with visible health warnings. Schedules are best effort, not an uptime SLA.

The frontend reloads snapshots every 30 minutes while visible. Refresh reloads the published snapshots; it cannot trigger the server collector. Satellite metadata is separately fetched from EUMETSAT every 15 minutes while satellite watch is visible. Cached or old data remains explicitly marked. No service worker hides fresh deployments behind an offline cache.

## Source inventory

| Data | Source | Cadence / limitations |
|---|---|---|
| AIS, 24h summary, 48h crossings, 30-day totals | [Hormuz Ship Monitor public API](https://hormuz.data-tracking.net/api-docs) | Provider polls ~30 minutes; Pages refresh adds delay. Partial and potentially erroneous self-reported coverage. |
| UKMTO reports | UKMTO through `/api/incidents` on the same API | Source reports, not independent confirmation. Full dataset retrieval time differs from each incident time. |
| Infrared / natural color / dust | [EUMETSAT EUMETView WMS](https://view.eumetsat.int/geoserver/wms?service=WMS&request=GetCapabilities) | `msg_iodc:ir108`, `msg_iodc:rgb_natural`, `msg_iodc:rgb_dust`; advertised 15-minute frames, processing latency; ~3 km at nadir, coarser away from nadir. |
| Daily true color | [NASA GIBS](https://nasa-gibs.github.io/gibs-api-docs/access-basics/) | `VIIRS_NOAA20_CorrectedReflectance_TrueColor`, GoogleMapsCompatible_Level9. Default yesterday UTC; current day can be incomplete. Display grid is not native sensor resolution. |
| Higher-resolution optical scenes | [Element 84 Earth Search](https://earth-search.aws.element84.com/v1) | Latest 12 Sentinel-2 L2A scenes intersecting bbox 55.5,25.8,57.1,27.3; UI shows 8. Cloud cover is whole-scene, not just Hormuz. Full visual data is 10 m; thumbnails are downsampled. |
| Reference imagery | [Esri World Imagery](https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9) | Historical mosaic, capture dates vary; not a current observation. |
| Weather | [Open-Meteo forecast](https://open-meteo.com/en/docs) | Model valid at 26.6° N, 56.5° E; wind knots, Celsius. Includes 72 hourly forecast values in the data JSON. |
| Marine | [Open-Meteo Marine](https://open-meteo.com/en/docs/marine-weather-api) | Model point 26.2° N, 56.5° E; meters / seconds / Celsius. No on-site sensors. |
| Earthquakes | [USGS FDSN](https://earthquake.usgs.gov/fdsnws/event/1/) | Last 30 days, M2.5+, bbox 44–65 E, 22–40 N, up to 100 events. Zero results differ from an unavailable feed. |
| News | [BBC Middle East RSS](https://feeds.bbci.co.uk/news/world/middle_east/rss.xml), [Al Jazeera RSS](https://www.aljazeera.com/xml/rss/all.xml) | Headline/link/date only. Al Jazeera titles filtered for regional keywords. No copied article bodies. |
| Map | OpenStreetMap | Attribution shown on map. No map tile bulk download. |

## Interpretation and freshness

- The dashboard is informational and not suitable for navigation or tactical decision-making. It retains the original project's commercial-shipping scope; no military tracking is added.
- The fleet card counts the returned commercial vessel records; source summary fields can exclude vessels currently in the strait. These are coverage counts, not the entire regional fleet. Vessel timestamps are source position/poll timestamps as supplied, not independently validated GPS fix times. Some provider `mmsi` fields contain non-MMSI identifiers; UI labels them source IDs rather than making false identity claims.
- Crossings are inferred from zone transitions. Only inbound/outbound rows are graphed; `in_strait` observations are not counted as completed crossings. Detection times can lag passage times.
- Estimated oil is an AIS-derived proxy, not measured cargo. A zero remains a reported zero and is not converted to missing data; it does not establish that physical flow stopped.
- EUMETSAT WMS can return its nearest available image when frames are missing. Playback labels a **service frame** request, not a verified exposure timestamp. The latest available metadata is shown; no claim of real-time video or vessel-scale live imagery is made. An image can contain blank areas even when a server responds successfully.
- Daily mosaics show an observation day, not an exact capture time. Basemap mosaics are not labeled live. Sentinel-2 images can be days old and cloudy; the actual scene acquisition and whole-scene cloud cover are visible.
- Feeds older than 90 minutes are labeled stale (Sentinel-2 acquisition threshold: 14 days). Collection status and scene capture age are distinct. Failed refreshes are cached. Future timestamps beyond five minutes are flagged as clock mismatches.
- The earliest public-data timestamps and data are whatever the providers return; this project performs schema checks, not independent verification of source claims.

## Attribution and terms

- Hormuz Ship Monitor identifies its data as CC BY 4.0. Its current API documentation also says research/non-commercial use, while its public repository describes commercial CC BY reuse. This package uses the public hobby/research route; consult the provider to resolve that wording before commercial deployment. Attribution is included on the site and CSV exports.
- UKMTO reporting: Crown copyright, [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/), supplied through Hormuz Ship Monitor. The site is not endorsed by UKMTO.
- © EUMETSAT; data shown via EUMETView. Read [EUMETSAT data licensing](https://user.eumetsat.int/data-access/data-licensing) for current terms before redistribution beyond viewing.
- NASA Worldview / GIBS. Copernicus Sentinel data, accessed through Element 84 Earth Search. Esri and imagery contributors, and OpenStreetMap contributors.
- Open-Meteo / DWD and partner models, CC BY 4.0. Open-Meteo's free endpoint is for non-commercial use; commercial service use needs the appropriate plan and collector endpoint configuration.
- USGS public-domain data. BBC / Al Jazeera headlines remain attributable to their publishers. Leaflet BSD-2-Clause license is bundled in `assets/vendor/leaflet/LICENSE`.
- Fonts use Google Fonts with system-font fallback. Public map/image requests disclose the visitor's IP to their respective providers. No analytics, automatic location request, tracking cookies, or user account is added. Watchlists, theme and successful snapshots are stored locally in the browser only.

## Support

Tip the build — BTC: `3GnR7TWBXAB3pPztBWpNF4LMNEX5yX8vZK`

## Local use / validation

```sh
python -m http.server 8000
# http://localhost:8000
python scripts/refresh_data.py
node --test tests/core.test.mjs
python -m unittest discover -s tests -p 'test_*.py'
```

Python 3.10+ and curl are needed only to refresh datasets. Node 18+ is needed only for the small pure-function tests. There is no npm install or frontend compilation step. To deploy, include `.github/workflows/pages.yml`, choose **GitHub Actions** as the Pages source, and run the workflow. The live repository has not been modified by generating this package.
