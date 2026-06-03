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
fetch_contours   →   {lake} polygon                         (in memory)
       ↓
retrieve         →   {date: ICON JSON}                      (in memory, one per day)
       ↓
parse_json       →   flat table                             (all grid points × all timesteps, in memory)
       ↓
lake_mean        →   lake-mean meteo series                 (spatial mean over lake surface, in memory)
       ↓
check            →   {ensemble_base}/check.png              (diagnostic plot)
       ↓
perturbate       →   {ensemble_base}/ensemble{1..N}/Forcing.dat   (perturbed Simstrat forcing)
```

The whole download→perturbate path runs in memory; only `check.png` and the
member `Forcing.dat` files are written (plus optional `flat.csv` / `lake_mean.csv`
when `save_intermediates` is enabled).

**Step 0 — fetch_contours:** Reads the bundled `static/lakes.geojson`
(`contours_geojson`) and resolves one polygon per configured lake by `key`,
returning them in memory. Lakes not in that file can use a local fallback
contour (`lake_contour`).

**Step 1 — retrieve:** Downloads daily JSON from the ICON KENDA-CH1 reanalysis
API for the lake bounding box, in parallel, and returns `{date: payload}` in
memory — nothing is cached to disk.

**Step 2 — parse_json:** Flattens each daily 3-D (time × lat × lon) grid into a
single flat table with one row per timestep per grid point.

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

Steps 0–4 pass their results in memory to the next step. `save_intermediates`
(default off) can be turned on to additionally write `flat.csv` / `lake_mean.csv`
to `out_dir` for inspection.

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
| `reanalysis_dir` | no | Base dir for optional intermediates (`processed/` when `save_intermediates`); resolved relative to repo root, default `data/reanalysis_data` |
| `reanalysis_lake` | no | Reuse the bbox/contour configured under a different lake name (defaults to `lake`) |
| `lake_key` | no | Key matching a feature in the bundled `static/lakes.geojson` |
| `lake_contour` | no | Path to a local fallback contour polygon |
| `rng_seed` | no | AR(1) random seed (default `42`) |
| `sigma_scale` | no | Scales the perturbation spread (default `1.0`) |
| `save_intermediates` | no | Write `flat.csv` / `lake_mean.csv` to disk (default `false`) |
| `skip` | no | Steps to skip (same as `--skip`) |

Raw ICON responses are downloaded and parsed in memory — they are never written
to disk. As a consequence `retrieve` cannot be skipped independently of `parse`
(there is no cached raw data to fall back on).

Lake contours are read from the bundled `static/lakes.geojson`
(`contours_geojson`) and held in memory — `fetch_contours` writes nothing and,
like `retrieve`, cannot be skipped independently of the steps that consume it.

Derived paths (`out_dir`, `contours_geojson`, `standard_inputs_path`, `log_dir`)
default off these and can be overridden in the JSON. `out_dir` is only used when
`save_intermediates` is enabled.

## Modules

| File | Purpose |
|---|---|
| `config.py` | Static constants: API URL, variable list, contour source URL, Simstrat reference year, `Forcing.dat` header |
| `pipeline.py` | `run(args, skip)` — orchestrates the six steps; exposes `STEPS` |
| `fetch_contours.py` | Resolves lake contour polygons from the bundled GeoJSON (in memory) |
| `retrieve.py` | Downloads daily ICON reanalysis JSON in parallel, returned in memory |
| `parse_json.py` | Flattens the in-memory raw JSON into a flat table per lake |
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
| `CONTOURS_URL` | Canonical S3 source of `static/lakes.geojson` (for manual refresh; not fetched at runtime) |
| `SIMSTRAT_REF_YEAR` | Reference year for the `Forcing.dat` time axis (days since 1 Jan) |
| `FORCING_HEADER` | Column header written to each perturbed `Forcing.dat` |

## Outputs

| Path | Description |
|---|---|
| `{reanalysis_dir}/processed/{lake}/flat.csv` | _(optional, `save_intermediates`)_ All grid points × all timesteps: `time, lat, lon, T_2M, U, V, GLOB` |
| `{reanalysis_dir}/processed/{lake}/lake_mean.csv` | _(optional, `save_intermediates`)_ Spatial mean over in-lake grid points per timestep |
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
