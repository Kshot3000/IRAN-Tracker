# Upgrade validation

Validated against real downloaded feeds and a locally served copy of the site on 2026-10-03.

- All 11 collected source envelopes parsed successfully and contained real data.
- JavaScript and Python syntax checks passed.
- Core tests cover source freshness / future clock mismatch, missing values vs zero, combined vessel filters, correct completed-crossing aggregation, invalid map coordinates, safe markup / links, and CSV formula protection.
- Collector tests cover last-good retention with original timestamps, unavailable first-run data, and recovery that clears failure status.
- Chromium desktop checks at 1440 px: no uncaught application errors; vessel search, details dialog, watchlist filter, CSV download, all navigation views, weather and report panels.
- Actual OpenStreetMap geographic tiles visually inspected. Replaced a third-party dark-map endpoint that had started returning API-key-required images.
- EUMETSAT Indian Ocean infrared tiles and NASA VIIRS daily tiles loaded. Sentinel-2 scene previews loaded with genuine timestamps and metadata links.
- Mobile check at 390 px: page width equals viewport width; responsive layout and bottom navigation; no uncaught application errors.
- Light-theme and satellite-page screenshots visually inspected.
- Simulated complete JSON feed failure produces missing-value dashes and an unavailable label. A later failure after successful loading retains genuine cached snapshots and shows a cached warning.
- Workflow YAML parsed; archive verified to include Pages workflow, tests, complete source, bundled map library, and live JSON envelopes.

Not exercised: publishing to the user's GitHub repository or a hosted GitHub Actions run. Configure Pages to use GitHub Actions and run the included workflow as described in START-HERE.md. Public provider uptime, data coverage and GitHub scheduling delays remain outside this site's control.
