# Update your IRAN Tracker repository

1. Extract **IRAN-Tracker-upgraded.zip**.
2. Copy the contents of the extracted folder into the root of `Kshot3000/IRAN-Tracker`, replacing matching files. Upload the **contents**, not the ZIP itself or another enclosing folder. Include the `.github` folder.
3. Delete the old `data/demo_ships.json` if it remains in the repository. The upgraded site never reads it.
4. On GitHub, open **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**.
5. Open **Actions → Refresh public data and deploy Pages → Run workflow**. Enable workflows first if GitHub asks. When the deploy job succeeds, reload your existing Pages URL.

The included snapshots are real collected data, so the dashboard can render immediately. The workflow retrieves new public data and redeploys twice an hour. It does not need API keys. GitHub schedules may be delayed; the Sources & status screen makes delays visible. Scheduled workflows in inactive public repositories may stop after 60 days; running/re-enabling the workflow restores collection.

If you keep Pages set to **Deploy from a branch**, the dashboard will still show the bundled snapshots, but shipping, news, and weather snapshots will not automatically update. Select **GitHub Actions** for ongoing refreshes.

## Local preview

Use Python 3 from the extracted folder:

```sh
python -m http.server 8000
```

Open `http://localhost:8000`. Opening `index.html` directly as a local file will not work correctly because browsers block module and JSON requests on `file://` URLs.

## What is included

- A responsive desktop and mobile dashboard, plus dark and light themes.
- Real commercial AIS positions, searchable vessel records, filters, sorting, local watchlists and CSV downloads.
- Source-detected crossings, 48-hour records and a 30-day chart.
- EUMETSAT Meteosat Indian Ocean infrared, natural-color and dust imagery, plus six-hour frame playback.
- NASA VIIRS daily imagery, explicitly historical Esri reference imagery, and recent Sentinel-2 scene previews with full-resolution data links.
- Marine and weather models, UKMTO public incident reports, regional news headlines, and USGS earthquakes.
- Original observation timestamps, visible stale/cached/unavailable states, attribution, collector tests and deployment automation.

No deployment has been made to your live repository by this ZIP. Uploading and running the workflow publishes the upgrade at your existing URL.
