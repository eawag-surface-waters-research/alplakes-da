# prep_reanalysis

`assimilator.prep_reanalysis` — builds the **perturbed forcing ensemble** for Simstrat
data assimilation, split into a one-time **fit** and a per-run **apply**:

- **Fit (Part 1, `fit_perturbations.py`)** — heavy, rare, needs the ICON API (EAWAG VPN).
  Downloads ICON KENDA-CH1, reduces it to a lake-mean meteo series, computes residuals
  against the control `Forcing.dat`, fits an **AR(1)** model `(phi, sigma)` per variable
  (`U`, `V`, `GLOB`), and writes the calibration to **`perturbations/<lake>.json`** (committed).
- **Apply (Part 2, `perturbate.py`)** — light, every run, `numpy`/`pandas` only. Reads
  `perturbations/<lake>.json`, simulates fresh AR(1) noise, adds it to the control forcing, and
  writes `n_members` perturbed `Forcing.dat` files. This is what `main.py` step 3 runs — no ICON.

The split means ICON access is needed **once per lake** (to produce the JSON); thereafter the
assimilation pipeline reuses the committed calibration.

## Fit pipeline (`fit_perturbations.py`)

```
fetch_contours   →   {lake} polygon                  (in memory; from static/lakes.geojson)
       ↓
retrieve         →   {date: ICON JSON}               (in memory, one per day, parallel)
       ↓
parse_json       →   flat grid table                 (all points × timesteps, in memory)
       ↓
lake_mean        →   lake-mean meteo series           (spatial mean over in-lake points)
       ↓
(residuals ICON − control Forcing.dat)  →  _fit_ar1 per var  →  perturbations/<lake>.json
       ↓
check (optional, --check)  →  run/<lake>/check.png + check_fit.png
```

All download→fit runs in memory; only the JSON (and, with `--check`, the QA plots) is written.
The fit window defaults to the most recent full calendar year (override with `fit_start`/`fit_end`).
A control-vs-ICON correlation table is logged as a sanity check (the matched variable must
correlate most strongly — the diagonal must dominate).

## Apply (`perturbate.py`)

Reads `perturbations/<lake>.json`, simulates an independent AR(1) trajectory per member with the
fitted `(phi, sigma)` (scaled by `sigma_scale`), adds it to the control `Forcing.dat`, and writes
`ensemble1..N/Forcing.dat`. Only `U`, `V`, `GLOB` are perturbed; `T`/`vap`/`cloud`/`rain` pass
through unperturbed; `GLOB` perturbations are zeroed at night (mask from the control's solar) and
clipped non-negative. `ensemble1..N` must already exist (created by `main.py`'s copy step);
`ensemble0` is the unperturbed control and is left untouched. Errors if the JSON is missing.

## Usage

```bash
python src/fit_perturbations.py args/ensemble.json [--check]   # Part 1: write perturbations/<lake>.json
python src/perturbate.py        args/ensemble.json             # Part 2: apply (usually via main.py step 3)
```

Programmatic:

```python
from assimilator.prep_reanalysis.ar1_fit   import fit_perturbations
from assimilator.prep_reanalysis.ar1_apply import perturbate
```

## Args (`args/ensemble.json`)

```json
{
    "lake":            "upperlugano",
    "reanalysis_lake": "lugano",
    "lake_bbox":       [45.89, 8.85, 46.03, 9.13],
    "lake_key":        "lugano",
    "n_members":       20,
    "ensemble_base":   "../run/upperlugano",
    "start_date":      "2025-01-01",
    "end_date":        "2025-12-31",
    "rng_seed":        42,
    "sigma_scale":     1.0
}
```

| Key | Used by | Description |
|---|---|---|
| `lake` | both | Lake/ensemble name; member dirs + `perturbations/<lake>.json` |
| `lake_bbox`, `lake_key` | fit | ICON download bbox + key into `static/lakes.geojson` |
| `reanalysis_lake` | fit | Reuse bbox/contour under a different name (default `lake`) |
| `n_members` | apply | Number of perturbed members |
| `ensemble_base` | both | Simstrat ensemble base (relative to `src/`); holds `ensemble1..N`, `check*.png` |
| `start_date` / `end_date` | apply | Assimilation window (ISO, UTC) |
| `fit_start` / `fit_end` | fit (opt) | Fixed fit window; default = most recent full year |
| `rng_seed` / `sigma_scale` | apply | AR(1) seed / spread multiplier (tune without re-fitting) |

Static constants (`SIMSTRAT_REF_YEAR`, `FORCING_HEADER`, ICON `API_BASE`/`VARIABLES`) live in
`static/general.json`, loaded via `assimilator.functions`.

## Modules

| File | Purpose |
|---|---|
| `fit_perturbations.py` | Part 1: ICON acquisition (folds fetch_contours/retrieve/parse/lake_mean) + AR(1) fit → JSON; `setup_logging` |
| `perturbate.py` | Part 2: simulate AR(1) → perturbed `Forcing.dat` per member |
| `check.py` | QA plots: `check.png` (grid mask + lake-mean series) and `check_fit.png` (residual ACF / distribution / preview ensemble) |

## Outputs

| Path | Description |
|---|---|
| `perturbations/<lake>.json` | Fitted AR(1) `(phi, sigma)` per variable + provenance (committed) |
| `run/<lake>/ensemble{1..N}/Forcing.dat` | Perturbed Simstrat forcing — the apply step's output |
| `run/<lake>/check.png`, `check_fit.png` | QA plots (with `--check`) |
| `logs/fit_YYYYMMDD_HHMMSS.log` | Timestamped fit log |
