# Data Assimilation for Lake Hydrodynamic Models

Integrating observations into operational lake models to improve forecast accuracy for the
[Alplakes](https://www.alplakes.eawag.ch) platform at [Eawag](https://www.eawag.ch).

## Overview

This repository implements an ensemble data-assimilation (DA) framework for the 1‑D lake model
**[Simstrat](https://github.com/Eawag-AppliedSystemAnalysis/Simstrat)**. It blends in‑situ
temperature profiles into the model state in near‑real time to improve forecasts and quantify
uncertainty.

Two assimilation engines run on the **same** ensemble and observations, so results can be
cross‑validated. Both share one entry point, `src/main.py`, selected by the `"engine"` field
in the config:

| Engine | `"engine"` | Filters | Role |
|---|---|---|---|
| **Native Python** | `"python"` | EnKF, PF | Primary in‑house implementation |
| **OpenDA black‑box** | `"openda"` | EnKF, DEnKF, EnSR, PF | Independent reference / cross‑check |

Simstrat itself always runs in **Docker** (`eawag/simstrat:3.0.4`); no local Simstrat binary is
needed. The OpenDA engine additionally requires an OpenDA installation (see
[Running the OpenDA engine](#running-the-openda-engine)).

## Workflow

You provide two things manually: the **model inputs + warm-start snapshot** in `inputs/<lake>/`
(see [Providing standard_inputs](#providing-standard_inputs)) and the **observations** in
`observations/<lake>/temperature.csv` (see [Providing observations](#providing-observations)).
`src/main.py` then orchestrates the chain end‑to‑end, skipping any step already done:

```
1. require standard_inputs   (provided manually)   -> inputs/<lake>/                [error if missing]
2. copy_standard_inputs      ensemble.json   clone -> run/<lake>/ensemble0..N       (0 = control)
3. perturbate                ensemble.json   AR(1) noise from perturbations/<lake>.json
                                              -> perturbed Forcing.dat in ensemble1..N
4. run                       engine=python:  native EnKF/PF daily updates (run_args = enkf.json|pf.json)
                             engine=openda:  render the OpenDA config + launch the filter
5. summarize                 posterior ensemble -> final_output/
```

Run either engine with one command — it re‑uses any already‑completed preprocessing:

```bash
python src/main.py args/run_enkf.json     # native EnKF
python src/main.py args/run_pf.json       # native PF
python src/main.py args/run_openda.json   # OpenDA
```

Add `--dry-run` to preview, or `--force-copy` to re‑run the copy step that otherwise looks done.
(Step 3 perturbate always runs — it fits `perturbations/<lake>.json` from ICON first if missing.)

Shared facts (`lake`, `start_date`, `end_date`, `n_members`) live only in `ensemble.json`; the
run args (`enkf.json`/`pf.json`) carry just the engine‑specific knobs.

### The forcing-perturbation calibration (one-time, offline)

Step 3 perturbs the wind/solar forcing with AR(1) noise whose statistics `(phi, sigma)` are fit
once from ICON reanalysis and cached in **`perturbations/<lake>.json`** (committed). That fit
needs the EAWAG ICON API (VPN) and is run separately, rarely:

```bash
python src/fit_perturbations.py args/ensemble.json [--check]   # writes perturbations/<lake>.json
```

`--check` also writes QA plots to `run/<lake>/` (`check.png`: grid mask + lake-mean series;
`check_fit.png`: residual ACF vs fitted φ, residual distribution, preview perturbed ensemble).
Once `perturbations/<lake>.json` exists, `main.py` step 3 needs no ICON access. If it's missing,
step 3 errors with instructions.

### Providing standard_inputs

Populate `inputs/<lake>/` manually with the Simstrat input set **plus a dated
warm-start snapshot**:

- a dated `simulation-snapshot_<YYYYMMDD>.dat` (the warmup state the members restart from),
- `Forcing.dat` (the unperturbed control forcing; the base step 3 perturbs),
- `Settings.par` (with the correct `Reference year`, grid, `Output.Path`, and
  `Continue from last snapshot: true`),
- the remaining Simstrat inputs (`Bathymetry.dat`, `Grid.dat`, `z_out.dat`, `t_out.dat`,
  `InitialConditions.dat`, `Absorption.dat`, inflows/outflow, `aed2.nml`, …).

`main.py` step 1 just verifies a `simulation-snapshot_*.dat` + `Forcing.dat` are present.

The depths listed in **`z_out.dat`** (the model's output depths) also determine which observation
depths can be assimilated: an obs depth with no matching `z_out.dat` depth is dropped (see
[Providing observations](#providing-observations)).

### Providing observations

Place the in-situ temperature profiles at **`observations/<lake>/temperature.csv`** — a long-format
CSV with one row per (time, depth) reading. Only these columns are required (any others, e.g.
`latitude`/`longitude`/`weight`, are ignored):

| column | meaning |
|---|---|
| `time`  | ISO-8601 timestamp **with UTC offset**, e.g. `2025-06-01T11:55:00+00:00` |
| `depth` | depth below the surface in **metres, positive** (e.g. `0.5`, `1`, `3`, …) |
| `value` | water temperature in **°C** |

Any sampling rate is fine (the upperlugano file is ~5-minute); the framework handles the rest:

- **Time:** for each day it assimilates the **mean of the samples in the noon hour [11:30, 12:30) UTC**
  (one value per depth), identically for the native and OpenDA engines.
- **Depth:** obs depths are auto-detected and kept only if they match a `inputs/<lake>/z_out.dat`
  output depth (within 1e-6 m); unmatched depths (e.g. a 0.5 m sensor on a whole-metre grid) are dropped
  so every assimilated depth has a model prediction.

No fixed depth list or time grid needs to be declared — both are read from the file.

## Repository layout

```
.
├── src/
│   ├── main.py                  Single entry point. Orchestrates steps 1–5 (skipping done ones)
│   │                            and dispatches to the engine named in the run config.
│   ├── perturbate.py            Step 3 (apply): perturbed Forcing.dat from perturbations/<lake>.json.
│   ├── fit_perturbations.py     Offline calibration (Part 1): ICON -> perturbations/<lake>.json.
│   └── assimilator/             Importable package (core library shared by both engines)
│       ├── functions.py            Shared base: path/config helpers (loads static/general.json),
│       │                           obs loaders, Docker/Simstrat run + .par helpers, arg validation,
│       │                           copy_standard_inputs, build_python_run_args
│       ├── snapshot.py             Read/write Simstrat Fortran binary snapshots
│       ├── summarize.py            Posterior summary (.csv) + skill/bias report (.json) + report_summary
│       ├── python/                 Native engines
│       │   ├── enkf.py                Ensemble Kalman Filter (run_enkf)
│       │   └── pf.py                  Particle Filter (run_pf)
│       ├── openda/                 OpenDA cross-validation bridge
│       │   ├── adapter.py             Sync inputs/forcings/warmup + build observations (run_openda)
│       │   └── config.py              Render run.oda + every .gen.xml from the FILTERS spec
│       └── prep_reanalysis/        ICON reanalysis -> AR(1) forcing perturbation
│           ├── ar1_fit.py            Part 1 impl: acquisition + AR(1) fit -> perturbations/<lake>.json
│           ├── ar1_apply.py          Part 2 impl: simulate AR(1) -> perturbed member forcings
│           └── check.py               QA plots (acquisition + fit diagnostics)
│
├── args/                    One JSON config per entry point (see Configuration)
├── static/                  Version/lake-independent config + templates
│   ├── lake_parameters.json, simstrat_<ver>.par, lakes.geojson
│   ├── general.json            Simstrat epoch, forcing-file format, ICON API/variable list
│   └── openda/                 The two hand-maintained OpenDA files (wrapper + its config)
├── perturbations/           Committed AR(1) calibration per lake (<lake>.json)
├── observations/            Observations (<lake>/temperature.csv); large files are git-ignored
├── inputs/                  Manually-provided model inputs (git-ignored)
│   └── <lake>/                  Simstrat input set + dated warmup snapshot (cloned into ensembles)
│       └── ref/T_out.dat        optional free-run reference, used only by visualize.py (not cloned)
├── run/                     Working area (git-ignored per lake)
│   ├── <lake>/ensemble0..N/      control (0) + perturbed members; DA writes Results_* here
│   └── openda/work_<filter>/work0..N/   OpenDA per-member scratch (Results/T_out.dat)
├── final_output/            Per-run summaries, named <lake>_<engine>_<label>:
│                            .csv  = posterior mean + std (time, depth, T_mean, T_std)
│                            .json = skill/bias report vs observations (bias, rmse, mae, …)
├── scripts/                 Non-essential tooling (visualize.py + local analysis scripts)
├── openda_simstrat/         OpenDA working dir — fully generated on demand, git-ignored
├── logs/                    Timestamped pipeline logs
└── docs/ + mkdocs.yml       Documentation site
```

## Configuration (`args/`)

Run configs (`run_*.json`) are the entry points passed to `main.py`; they reference the
per‑step arg files below.

| File | Used by | Key fields |
|---|---|---|
| `run_enkf.json` / `run_pf.json` | `main.py` | `engine:"python"`, `ensemble_args`, `run_args` |
| `run_openda.json` / `run_openda_pf.json` | `main.py` | `engine:"openda"`, `ensemble_args`, `filter` (EnKF\|DEnKF\|EnSR\|PF), `openda_dir` |
| `ensemble.json` | steps 2–3 + fit + **both engines** | `lake`, `n_members`, `start_date`, `end_date`, `sigma_obs` (obs error σ — shared by native EnKF + OpenDA), `lake_bbox`, `lake_key`, `reanalysis_lake` |
| `enkf.json` | python `run_args` | `algorithm:"EnKF"`, `results_dir`, `par_file`, `inflation` (native-EnKF only), `reset` |
| `pf.json` | python `run_args` | `algorithm:"PF"`, `results_dir`, `par_file`, `reset` |

The `lake` field resolves data and run paths by convention: observations from
`observations/<lake>/temperature.csv`, ensemble from `run/<lake>/`, calibration from `perturbations/<lake>.json`.

## The OpenDA engine (`openda_simstrat/`)

OpenDA runs Simstrat as a "black box": it clones a template directory once per ensemble member,
calls a wrapper script that runs Simstrat in Docker, and applies the Kalman update to each
member's temperature state at every analysis (observation) time.

`openda_simstrat/` is a **fully generated working directory** (git-ignored, built on demand):

- `src/assimilator/openda/config.py` renders `run.oda`, `parallel.gen.xml`,
  `algorithms/<filter>.gen.xml`, `stochModel/simstrat{Model,StochModel}.gen.xml`,
  `stochModel/template/{time_control.yaml,obs_depths.json,timeSeriesFormatter.gen.xml}`, and
  `stochObserver/timeSeriesFormatter.gen.xml` — driven by `filter`, `n_members`, and the
  observation depths (auto‑detected from `observations/<lake>/temperature.csv`, restricted to model output depths).
- `src/assimilator/openda/adapter.py` syncs `standard_inputs` → `stochModel/template/`,
  the perturbed `Forcing_{0..N}.dat` → `forcings/`, the warmup snapshot →
  `template/Results/simulation-snapshot.dat`, seeds `temperature_state.txt`, builds the
  observation CSVs, and **copies the two hand-maintained files from `static/openda/`**
  (`simstratWrapperEnKF.xml`, `simstrat_wrapper_enkf.py`) into the working tree.

So the **only OpenDA source of truth** is `src/assimilator/openda/config.py` + the two files in
`static/openda/`. Adding a new filter is a one‑line entry in the `FILTERS` spec.

### Running the OpenDA engine

Requires WSL/Linux with Docker running and an OpenDA 3.4.0 install. Source the OpenDA environment
once per shell:

```bash
export ROOT="$(pwd)"
export OPENDADIR="$ROOT/openda_3.4.0/bin"
export PATH="$ROOT/openda_3.4.0/jre/bin:$OPENDADIR:$PATH"
export OPENDA_NATIVE=linux64_gnu
export OPENDALIB="$OPENDADIR/$OPENDA_NATIVE"
export LD_LIBRARY_PATH="$OPENDALIB/lib:$LD_LIBRARY_PATH"
```

Then:

```bash
python src/main.py args/run_openda.json            # full run
python src/main.py args/run_openda.json --dry-run  # preview, write nothing
python src/main.py args/run_openda.json --skip-oda # generate config, don't launch
```

Set `"filter"` in `args/run_openda.json` to `EnKF`, `DEnKF`, or `EnSR`, or use the
`args/run_openda_pf.json` preset for `PF`. Output for each filter goes to
`run/openda/work_<filter>/workN/Results/T_out.dat` (hourly, full water column) plus
`openda_simstrat/<filter>_results.py` (OpenDA `PythonResultWriter`), and a posterior summary +
skill/bias report are auto‑written to `final_output/<lake>_openda_<filter>.{csv,json}`.

> **Output convention:** in `<filter>_results.py`, `pred_a_central` is `H·x_f` (the forecast
> prediction), not `H·x_a`. To see the true analysis correction at observation depths, read the
> `x_a_central` columns directly.

> **PF note:** unlike the Kalman filters, the particle filter clones whole particles during
> resampling, so it needs model restart files. Its generated config therefore adds `restartInfo`
> declarations (stoch- and model-layer) that the EnKF/DEnKF/EnSR configs omit — flagged by
> `needs_restart` in the `FILTERS` spec in `openda/config.py`.

## Running the native engine

```bash
python src/main.py args/run_enkf.json     # or args/run_pf.json
```

Per‑member results are written to `run/<lake>/ensemble{i}/Results_<algo>/`, with the ensemble‑mean
trajectory and diagnostics alongside in `run/<lake>/`. On completion a posterior summary (ensemble
mean + 1σ per time/depth) and a skill/bias report are auto‑written to
`final_output/<lake>_python_<algo>.{csv,json}`.

## Prerequisites

- Python 3 with `numpy`, `pandas`, `geopandas`, `requests`, `tqdm`, `matplotlib`.
- **Docker** with the `eawag/simstrat:3.0.4` image available.
- For the forcing-perturbation fit only: access to the EAWAG ICON reanalysis API (VPN).
- For the OpenDA engine only: an **OpenDA 3.4.0** installation, run under WSL/Linux.
```
