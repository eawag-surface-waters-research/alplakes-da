# src — Data Assimilation Pipeline

Ensemble-based lake temperature data assimilation driven by the [Simstrat](https://www.eawag.ch) 1-D hydrodynamic model.

---

## Directory layout

```
src/
├── main.py                  # parallel ensemble Docker runner
├── ensembles.py             # AR(1) ensemble forcing perturbation
├── copy_standard_inputs.py  # Populate ensemble dirs with shared inputs
├── main_PF.py               # Sequential daily particle filter
├── main_PF_weekly.py        # Same filter with 7-day windows to speed up simulation time and compare
├── analyze_results.py       # Visualise: raw ensemble spread, PF trajectories and respective RMSE 
└── functions/               # Reusable 
    └── par.py               # overwrite_par_file_dates(): updates only the start/end timestamps
```
---

## Pipeline overview

The workflow runs in four stages. Steps 1–2 are done once to prepare inputs; steps 3–4 are the operational DA loop.

```
**Stage 1** — Input preparation
  
  Download data: 
  
  Source it from Alplakes, Datalakes, then process and ultimately store in /data directory. /
  In our example we use the temperature observations from the Castagnola buoy (and Gandria sampling only for comparison) as observations./
  For meteorological station values we take the ones from the closest station, namely the LUG station./
   Upperlugano inputs for Simstrat are prepackaged and downloaded from Alplakes.

**Stage 2** — Ensemble generation and input copying
  
  ensembles.py             Fit AR(1) to obs–reanalysis residuals → 20 perturbed Forcing.dat files
  copy_standard_inputs.py  Copy all non-forcing inputs into ensemble0–20/

**Stage 3** — Simulation + assimilation  ((main.py) / main_PF.py / main_PF_weekly.py)
  
  Free ensemble runs 
  
  and/or

  Daily (or weekly) loop:
    1. Run 21 Docker containers (ensemble0–20) in parallel for the window
    2. Compute per-member RMSE vs in-situ observations
    3. Copy best member's snapshot to all others  ← particle filter step
    4. Accumulate trajectories (best, mean, persist)

**Stage 4** — Analysis
  
  analyze_results.py    
  
  Three figures:

    Fig 1 — Temperature fan (ensemble spread) at 6 depths vs Castagnola and Gandria obs,
            overlaid with ensemble0 control, daily best (hindsight), ensemble mean, persistence
    Fig 2 — Stacked RMSE bar chart per member ranked by total RMSE, highlighting
            ensemble0 and best perturbed member
    Fig 3 — RMSE comparison across trajectory types (standard, weekly/daily best,
            ensemble mean, persistence) with % gain relative to ensemble0
```

---

## Running the pipeline

### Prerequisites

- Docker daemon running (`eawag/simstrat:3.0.4` image available)
- Python dependencies: `numpy pandas matplotlib scipy netCDF4 pylake statsmodels tqdm`

### Step 1 — Prepare standard inputs
Use alplakes and datalakes and manually provide.

Will be automized in the future.

### Step 2 — Generate ensemble forcing

```bash
python src/ensembles.py
python src/copy_standard_inputs.py
```
`ensembles.py` expects:
- `data/obs_2025.csv` — observed hourly meteorology (time, wind speed/dir, T, radiation, RH, precip)
- `data/lake_mean_ICON_2025.csv` — ICON reanalysis (average over the lake) for the same period

Outputs: `assimilation/upperlugano/ensemble{0..20}/Forcing.dat`

### Step 3 — Run the particle filter

```bash
python src/main_PF.py          # daily windows
python src/main_PF_weekly.py   # 7-day windows
```

Key constants at the top of each file:

| Constant | Description |
|---|---|
| `ENSEMBLE_BASE` | Path to the `assimilation/<lake>/` directory |
| `OBS_PATH` | In-situ temperature observations CSV (`time`, `depth`, `value`) |
| `N_MEMBERS` | Number of perturbed ensemble members (default 20) |
| `PF_RESULTS` | Output subdirectory inside each ensemble dir (default `Results_PF`) |

Set `reset=True` on the first run to clear any stale snapshots and trajectory files prior to running a new assimilation.

### Step 4 — Analyse results

```bash
python src/analyze_results.py  
```
---

## How snapshots pass state between windows

Simstrat writes `Results_PF/simulation-snapshot.dat` at the end of every run. Between windows:

1. `*_out.dat` files are deleted; the snapshot is left in place.
2. Simstrat detects the snapshot and restarts from it automatically.
3. After the RMSE evaluation, `_copy_best_to_all()` overwrites every member's snapshot with the best member's — this is the particle filter resampling step.

On the very first window, a pre-generated dated snapshot (`simulation-snapshot_YYYYMMDD.dat` in the ensemble root) is used as the bootstrap state. Note that this was generated using a standard Simstrat run from 1981 up until 31.12.2024.

---

