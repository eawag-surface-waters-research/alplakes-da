# prep_reanalysis

Pipeline to download and pre-process ICON KENDA-CH1 reanalysis data from the MeteoSwiss / Alplakes API for use as Simstrat forcing.

## Overview

```
retrieve.py  →  raw_data/{lake}/YYYYMMDD.json
parse_json.py →  processed/{lake}/flat.csv
```

Each step can be run independently or for a single lake.

## Scripts

| File | Purpose |
|---|---|
| `config.py` | Central configuration: API URL, variables, date range, lake bounding boxes, paths |
| `retrieve.py` | Download daily JSON files from the API (parallel, skips already-downloaded files) |
| `parse_json.py` | Flatten raw JSON files into a single CSV per lake (one row per time × grid point) |
| `logging_utils.py` | Shared logging setup — writes to console and a timestamped file in `logs/` |

## Usage

```bash
# Download all lakes
python retrieve.py

# Download a specific lake and date range
python retrieve.py lugano --start 2025-01-01 --end 2025-12-31 --workers 8

# Parse all lakes
python parse_json.py

# Parse a specific lake
python parse_json.py lugano
```

## Configuration (`config.py`)

| Parameter | Description |
|---|---|
| `API_BASE` | Alplakes internal ICON reanalysis endpoint |
| `VARIABLES` | Retrieved fields: `T_2M`, `U`, `V`, `GLOB` (2 m temperature, wind components, global radiation) |
| `DATE_START / DATE_END` | Default date range |
| `LAKES` | Dict of lake names → bounding boxes `(lat1, lon1, lat2, lon2)` |
| `RAW_DIR` | `raw_data/` — downloaded JSON files |
| `OUT_DIR` | `processed/` — parsed CSV output |

To add a new lake, append an entry to `LAKES` in `config.py` with its bounding box.

## Output

**`raw_data/{lake}/YYYYMMDD.json`** — one file per day, as returned by the API (time × 2D grid).

**`processed/{lake}/flat.csv`** — columns: `time, lat, lon, T_2M, U, V, GLOB`. One row per time step per grid point, all days concatenated.

**`logs/pipeline_YYYYMMDD_HHMMSS.log`** — timestamped log file created on each run.

## Notes

- `retrieve.py` is idempotent: existing JSON files are skipped without re-downloading.
- The API serves ICON KENDA-CH1 reanalysis at ~1 km resolution over Switzerland.
- Currently configured for Lake Lugano (`lugano`). Geneva and Murten entries are present in `config.py` but commented out.
