# IRAN Tracker — Strait of Hormuz Ship Monitor

A static, no-build-step website that monitors commercial vessel traffic in the
Strait of Hormuz — inspired by [hormuz.data-tracking.net](https://hormuz.data-tracking.net/) —
plus a satellite basemap viewer, a key-locations directory, and OSINT news links.

**Live site:** https://kshot3000.github.io/IRAN-Tracker/

## ⚠ Demo data

All ship positions, names, and crossing counts are **simulated** (`data/demo_ships.json`).
No live AIS feed is connected. Every panel is labeled `DEMO` with a snapshot timestamp.

To go live: get an AIS API key (e.g. [AISStream.io](https://aisstream.io/) or MarineTraffic),
then replace the demo loader in `app.js` (see the Methodology tab on the site).

## Satellite view

The Satellite tab uses Esri World Imagery — a **basemap mosaic, not live imagery**.
For recent imagery, use [Sentinel Hub EO Browser](https://www.sentinel-hub.com/explore/eobrowser/).

## Scope

- Commercial shipping only. No military facility coordinates and no real-time
  military movement tracking — out of scope by design.
- Key locations directory: Strait of Hormuz chokepoint + major cities/islands only.

## Deploy

Pure HTML/CSS/JS served from repo root via GitHub Pages. No build step.
