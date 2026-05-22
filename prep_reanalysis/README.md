# prep_reanalysis

Pipeline to download and pre-process ICON KENDA-CH1 reanalysis data from the MeteoSwiss / Alplakes API for use for Simstrat ensemble creation.

## Pipeline

```
fetch_contours.py    →   contours/{lake}.json
        ↓
retrieve.py          →   raw_data/{lake}/YYYYMMDD.json     (one file per day)
        ↓
parse_json.py        →   processed/{lake}/flat.csv          (all grid points × all timesteps)
        ↓
lake_mean.py         →   processed/{lake}/lake_mean.csv     (spatial mean over lake surface)
```

**Step 0 — fetch_contours:** Downloads the Alplakes lake contour GeoJSON and extracts one `{lake}.json` polygon per configured lake. Lakes not in the remote file can use a local fallback contour.

**Step 1 — retrieve:** Downloads daily JSON files from the ICON KENDA-CH1 reanalysis API for the lake bounding box, in parallel. Already-downloaded files are skipped (idempotent).

**Step 2 — parse_json:** Reads every daily JSON and flattens the 3-D (time × lat × lon) grid into a single CSV with one row per time step per grid point.

**Step 3 — lake_mean:** Loads the lake contour polygon, identifies which grid points fall inside the lake, and computes a spatial mean of all variables per timestep. The output is a compact time series ready for Simstrat forcing.

## Usage

Run the full pipeline (all configured lakes, default date range):
```bash
python pipeline.py
```

Run for specific lakes or date range:
```bash
python pipeline.py lugano --start 2025-01-01 --end 2025-12-31
```

Skip steps already completed:
```bash
python pipeline.py --skip contours retrieve    # only parse + mean
python pipeline.py --skip contours             # retrieve + parse + mean
```

Each script can also be run standalone:
```bash
python fetch_contours.py
python retrieve.py lugano --start 2025-01-01 --end 2025-12-31
python parse_json.py lugano
python lake_mean.py lugano
```

## Scripts

| File | Purpose |
|---|---|
| `config.py` | Central configuration: API URL, variables, date range, lake bounding boxes, paths |
| `pipeline.py` | Orchestrates all four steps with `--skip` support |
| `fetch_contours.py` | Downloads lake contour polygons from the Alplakes S3 bucket |
| `retrieve.py` | Downloads daily ICON reanalysis JSON files (parallel, skip-if-exists) |
| `parse_json.py` | Flattens raw JSON into a flat CSV per lake |
| `lake_mean.py` | Masks grid points inside the lake polygon and computes spatial mean |
| `logging_utils.py` | Shared logging setup — console + timestamped file in `logs/` |

## Configuration (`config.py`)

| Parameter | Description |
|---|---|
| `API_BASE` | Alplakes internal ICON KENDA-CH1 reanalysis endpoint |
| `VARIABLES` | `T_2M`, `U`, `V`, `GLOB` (2 m temperature, wind components, global radiation) |
| `DATE_START / DATE_END` | Default date range |
| `LAKES` | Dict of lake names → bounding boxes and contour keys |
| `RAW_DIR` | `raw_data/` — downloaded JSON files |
| `OUT_DIR` | `processed/` — CSV outputs |
| `CONTOUR_DIR` | `contours/` — lake polygon files |

To add a new lake, append an entry to `LAKES` with its bounding box `(lat1, lon1, lat2, lon2)` and either a `key` (matching the remote GeoJSON) or a `contour` (path to a local polygon file).

## Outputs

| File | Description |
|---|---|
| `raw_data/{lake}/YYYYMMDD.json` | Raw API response per day (time × 2-D grid) |
| `processed/{lake}/flat.csv` | All grid points × all timesteps: `time, lat, lon, T_2M, U, V, GLOB` |
| `processed/{lake}/lake_mean.csv` | Spatial mean over lake grid points per timestep — main output for Simstrat |
| `contours/{lake}.json` | GeoJSON polygon used for the spatial mask |
| `logs/pipeline_YYYYMMDD_HHMMSS.log` | Timestamped log file |

## Notes

- The API serves ICON KENDA-CH1 at ~1 km resolution over Switzerland.
- Currently configured for Lake Lugano. Geneva and Murten entries are present in `config.py` but commented out.
- `retrieve.py` is idempotent: re-running it will not re-download existing files.
