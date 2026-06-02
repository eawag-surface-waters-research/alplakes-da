# prep_reanalysis

`alplakes_da.prep_reanalysis` — pipeline to download ICON KENDA-CH1 reanalysis
data from the MeteoSwiss / Alplakes API, reduce it to a lake-mean meteo time
series, and use it to build a **perturbed forcing ensemble** for Simstrat data
assimilation.

This is an importable package, not a collection of standalone scripts: each step
is a function `step(args, ...)` that takes a shared `args` dict, and they are
chained by `pipeline.run`. The package is driven from `src/perturbate.py`, which
reads a JSON args file (e.g. `args/ensemble.json`) and calls `run`.

## Pipeline

```
fetch_contours   →   contours/{lake}.json
       ↓
retrieve         →   raw_data/{lake}/YYYYMMDD.json          (one file per day)
       ↓
parse_json       →   processed/{lake}/flat.csv              (all grid points × all timesteps)
       ↓
lake_mean        →   processed/{lake}/lake_mean.csv         (spatial mean over lake surface)
       ↓
check            →   {ensemble_base}/check.png              (diagnostic plot)
       ↓
perturbate       →   {ensemble_base}/ensemble{1..N}/Forcing.dat   (perturbed Simstrat forcing)
```

**Step 0 — fetch_contours:** Downloads the Alplakes lake contour GeoJSON and
extracts one `{lake}.json` polygon per configured lake. Lakes not in the remote
file can use a local fallback contour.

**Step 1 — retrieve:** Downloads daily JSON files from the ICON KENDA-CH1
reanalysis API for the lake bounding box, in parallel. Already-downloaded files
are skipped (idempotent).

**Step 2 — parse_json:** Reads every daily JSON and flattens the 3-D
(time × lat × lon) grid into a single flat table with one row per timestep per
grid point.

**Step 3 — lake_mean:** Loads the lake contour polygon, identifies which grid
points fall inside the lake, and computes a spatial mean of all variables per
timestep — a compact meteo time series for the lake surface.

**Step 4 — check:** Diagnostic plot (`check.png`) showing the selected in-lake
grid points on a map plus the lake-mean time series for each variable, so the
masking and the reanalysis signal can be eyeballed before perturbing.

**Step 5 — perturbate:** Reads the standard Simstrat `Forcing.dat`, computes
residuals between the ICON lake mean and that standard forcing, fits an **AR(1)**
model per variable (`U`, `V`, `GLOB`), and writes `n_members` perturbed
`Forcing.dat` files — one per ensemble member directory. Temperature is left
unperturbed; `GLOB` perturbations are clipped to zero at night. The member
directories (`ensemble1..N`) must already exist (created by
`copy_standard_inputs.py`); `ensemble0` is the unperturbed control and is not
touched.

Steps 2–4 pass their results in memory to the next step, so `save_intermediates`
can be turned off to skip writing `flat.csv` / `lake_mean.csv` to disk.

## Usage

The pipeline is run through `src/perturbate.py` with a JSON args file:

```bash
cd src
python perturbate.py ../args/ensemble.json
```

Skip steps that are already done (steps are
`contours retrieve parse mean check perturbate`):

```bash
python perturbate.py ../args/ensemble.json --skip contours retrieve   # parse + mean + check + perturbate
python perturbate.py ../args/ensemble.json --skip contours            # everything except contour download
```

Programmatic use:

```python
from alplakes_da.prep_reanalysis.pipeline import run
run(args, skip={"contours", "retrieve"})
```

## Args file

`build_args` in `src/perturbate.py` expands a compact JSON into the full `args`
dict the steps consume. Example (`args/ensemble.json`):

```json
{
    "lake":            "upperlugano",
    "reanalysis_lake": "lugano",
    "lake_bbox":       [45.89, 8.85, 46.03, 9.13],
    "lake_key":        "lugano",

    "n_members":     20,
    "ensemble_base": "../run/upperlugano",
    "start_date":    "2025-01-01",
    "end_date":      "2025-12-31",

    "reanalysis_dir":     "../prep_reanalysis",
    "rng_seed":           42,
    "sigma_scale":        1.0,
    "save_intermediates": false,
    "skip":               []
}
```

| Key | Required | Description |
|---|---|---|
| `lake` | yes | Lake/ensemble name; used for the member directories |
| `lake_bbox` | yes | `[lat1, lon1, lat2, lon2]` download bounding box |
| `n_members` | yes | Number of perturbed members to write |
| `ensemble_base` | yes | Base dir of the Simstrat ensemble (resolved relative to `src/`); holds `ensemble1..N` and `check.png` |
| `start_date` / `end_date` | yes | ISO dates; treated as UTC |
| `reanalysis_dir` | yes | Base dir for the data tree (`raw_data/`, `processed/`, `contours/`) |
| `reanalysis_lake` | no | Reuse data downloaded under a different lake name (defaults to `lake`) |
| `lake_key` | no | Key matching the remote Alplakes GeoJSON feature |
| `lake_contour` | no | Path to a local fallback contour polygon |
| `rng_seed` | no | AR(1) random seed (default `42`) |
| `sigma_scale` | no | Scales the perturbation spread (default `1.0`) |
| `save_intermediates` | no | Write `flat.csv` / `lake_mean.csv` to disk (default `true`) |
| `skip` | no | Steps to skip (same as `--skip`) |

Derived paths (`raw_dir`, `out_dir`, `contour_dir`, `standard_inputs_path`,
`log_dir`) default off these and can be overridden in the JSON.

## Modules

| File | Purpose |
|---|---|
| `config.py` | Static constants: API URL, variable list, contour URL, Simstrat reference year, `Forcing.dat` header |
| `pipeline.py` | `run(args, skip)` — orchestrates the six steps; exposes `STEPS` |
| `fetch_contours.py` | Downloads / copies lake contour polygons |
| `retrieve.py` | Downloads daily ICON reanalysis JSON (parallel, skip-if-exists) |
| `parse_json.py` | Flattens raw JSON into a flat table per lake |
| `lake_mean.py` | Masks grid points inside the lake polygon and computes the spatial mean |
| `check.py` | Diagnostic plot of grid-point selection + lake-mean time series |
| `perturbate.py` | Fits AR(1) on ICON-vs-standard residuals and writes perturbed `Forcing.dat` per member |
| `logging_utils.py` | Shared logging setup — console + timestamped file in `log_dir` |

Note: the package's own `perturbate.py` is the AR(1) step; the *driver* is
`src/perturbate.py` (different file).

## Configuration (`config.py`)

Unlike the per-lake configuration, `config.py` now holds only static constants;
lakes, bounding boxes, dates and paths all come from the args file.

| Constant | Description |
|---|---|
| `API_BASE` | Alplakes internal ICON KENDA-CH1 reanalysis endpoint |
| `VARIABLES` | `T_2M`, `U`, `V`, `GLOB` (2 m temperature, wind components, global radiation) |
| `CONTOURS_URL` | Alplakes lakes GeoJSON on S3 |
| `SIMSTRAT_REF_YEAR` | Reference year for the `Forcing.dat` time axis (days since 1 Jan) |
| `FORCING_HEADER` | Column header written to each perturbed `Forcing.dat` |

## Outputs

| Path | Description |
|---|---|
| `{reanalysis_dir}/raw_data/{lake}/YYYYMMDD.json` | Raw API response per day (time × 2-D grid) |
| `{reanalysis_dir}/processed/{lake}/flat.csv` | All grid points × all timesteps: `time, lat, lon, T_2M, U, V, GLOB` |
| `{reanalysis_dir}/processed/{lake}/lake_mean.csv` | Spatial mean over in-lake grid points per timestep |
| `{reanalysis_dir}/contours/{lake}.json` | GeoJSON polygon used for the spatial mask |
| `{ensemble_base}/check.png` | Diagnostic map + time series plot |
| `{ensemble_base}/ensemble{1..N}/Forcing.dat` | Perturbed Simstrat forcing — the pipeline's main output |
| `{log_dir}/pipeline_YYYYMMDD_HHMMSS.log` | Timestamped log file |

## Notes

- The API serves ICON KENDA-CH1 at ~1 km resolution over Switzerland.
- `retrieve` is idempotent: re-running it will not re-download existing files.
- Only `U`, `V` and `GLOB` are perturbed; temperature (`T`) is passed through
  unperturbed, and `GLOB` is forced to zero at night and clipped to be
  non-negative.
- `ensemble1..N` must be created beforehand (by `copy_standard_inputs.py`);
  `perturbate` overwrites their `Forcing.dat` and raises if a member dir is
  missing.
