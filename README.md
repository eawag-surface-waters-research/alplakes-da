# Data Assimilation for Lake Hydrodynamic Models

Integrating observations into operational lake models to improve forecast accuracy for the
[Alplakes](https://www.alplakes.eawag.ch) platform at [Eawag](https://www.eawag.ch).

## Overview

This repository implements an ensemble data-assimilation (DA) framework for the 1‑D lake model
**[Simstrat](https://github.com/Eawag-AppliedSystemAnalysis/Simstrat)**. It blends in‑situ
temperature profiles into the model state in near‑real time to improve forecasts and quantify
uncertainty.

Two assimilation engines run on the **same** ensemble and observations, so results can be
cross‑validated:

Both engines share one entry point, `src/assimilator.py`, selected by the `"engine"` field
in the config:

| Engine | `"engine"` | Filters | Role |
|---|---|---|---|
| **Native Python** | `"python"` | EnKF, PF | Primary in‑house implementation |
| **OpenDA black‑box** | `"openda"` | EnKF, DEnKF, EnSR, PF | Independent reference / cross‑check |

Simstrat itself always runs in **Docker** (`eawag/simstrat:3.0.4`); no local Simstrat binary is
needed. The OpenDA engine additionally requires an OpenDA installation (see
[Running the OpenDA engine](#running-the-openda-engine)).

## Workflow

`assimilator.py` orchestrates the whole chain end‑to‑end, skipping any preprocessing that is
already done. A single run config in `args/` selects the engine and points at the per‑step
arg files; the underlying stages are:

```
1. initial_conditions_snapshot   snapshot.json   spin-up -> run/<lake>/standard_inputs + warmup snapshot
2. copy_standard_inputs          ensemble.json   clone     -> run/<lake>/ensemble0..N  (0 = control)
3. perturbate                    ensemble.json   ICON reanalysis -> AR(1)-perturbed Forcing.dat in ensemble1..N
                                                 (runs the prep_reanalysis pipeline)
4. run                           engine=python:  native EnKF/PF daily updates (run_args = enkf.json|pf.json)
                                 engine=openda:  generate the OpenDA config and launch the filter
5. summarize                     posterior ensemble -> final_output/
```

Run either engine with one command — it re‑uses any already‑completed preprocessing:

```bash
python src/assimilator.py args/run_enkf.json     # native EnKF
python src/assimilator.py args/run_pf.json       # native PF
python src/assimilator.py args/run_openda.json   # OpenDA
```

Shared facts (`lake`, `start_date`, `end_date`, `n_members`) live only in `ensemble.json`; the
run args (`enkf.json`/`pf.json`) carry just the engine‑specific knobs.

## Repository layout

```
.
├── src/                     Python source
│   ├── assimilator.py                   Single entry point. Orchestrates the whole chain (steps
│   │                                    1–5, skipping done ones) and dispatches to the engine
│   │                                    named in the run config. Takes one args/run_*.json.
│   │   ─ Stage scripts called by assimilator.py (each also runnable standalone with its args/*.json) ─
│   ├── initial_conditions_snapshot.py   Step 1. Builds every Simstrat input from the data API and
│   │                                    runs a Docker spin-up to the snapshot date, saving a warmup
│   │                                    state; inputs span the whole simulation window.
│   ├── copy_standard_inputs.py          Step 2. Clones standard_inputs into ensemble0..N (0 = control).
│   ├── perturbate.py                    Step 3. Thin CLI over prep_reanalysis: fits AR(1) noise from
│   │                                    ICON reanalysis → perturbed Forcing.dat in ensemble1..N.
│   │
│   └── alplakes_da/         Importable package (core library shared by both engines)
│       ├── functions.py        Docker/data-API helpers, Simstrat run + Settings.par / state
│       │                       read-write helpers, logging, arg validation
│       ├── snapshot_io.py      Read/write Simstrat Fortran binary snapshots
│       ├── EnKF_assimilate.py  Native Ensemble Kalman Filter engine
│       ├── PF_assimilate.py    Native Particle Filter engine
│       ├── summarize.py        Post-run posterior summary (.csv) + skill/bias report (.json)
│       ├── visualize.py        Plots: time series, RMSE, ensemble spread, OpenDA results
│       ├── prep_reanalysis/    Meteo pipeline: ICON reanalysis → AR(1)-perturbed forcing ensemble
│       │   ├── pipeline.py        Step runner: contours → retrieve → parse → mean → check → perturbate
│       │   ├── fetch_contours.py  Resolve lake-boundary polygons from bundled GeoJSON (in memory)
│       │   ├── retrieve.py        Parallel day-by-day ICON reanalysis download (in memory)
│       │   ├── parse_json.py      ICON JSON → flat (time, lat, lon, vars) table
│       │   ├── lake_mean.py       Spatial mean over in-lake grid points
│       │   ├── check.py           QA / sanity diagnostics
│       │   ├── perturbate.py      AR(1) fit on (ICON − Forcing) residuals → perturbed forcings
│       │   ├── config.py          API URLs, variable list, Simstrat reference year
│       │   └── logging_utils.py   Logging setup   (full detail: prep_reanalysis/README.md)
│       └── openda/            OpenDA cross-validation bridge (data + config)
│           ├── adapter.py         Sync framework inputs/forcings/warmup + build observations
│           └── config.py          Render run.oda + every .gen.xml from the FILTERS spec
│
├── args/                    One JSON config per entry point (see Configuration)
├── static/                  Version/lake-independent templates: simstrat_<ver>.par, aed2.nml,
│                            lake_parameters.json
├── data/                    Observations (T_obs_<lake>.csv) and lake-mean meteo
│                            (lake_mean_<lake>_<year>.csv); large files are git-ignored
├── run/                     Working area (git-ignored per lake)
│   ├── <lake>/standard_inputs/   spun-up inputs + dated warmup snapshot
│   ├── <lake>/ensemble0..N/      control (0) + perturbed members; DA writes Results_* here
│   └── openda/work_<filter>/work0..N/   OpenDA per-member scratch (Results/T_out.dat)
├── final_output/            Per-run summaries (auto-written), named <lake>_<engine>_<label>:
│                            .csv  = posterior ensemble mean + std (time, depth, T_mean, T_std)
│                            .json = skill/bias report vs observations (bias, rmse, mae,
│                                    spread, coverage), overall + per depth
│
├── openda_simstrat/         OpenDA black-box configuration (see below; mostly generated)
├── logs/                    Timestamped pipeline logs
└── docs/ + mkdocs.yml       Documentation site
```

## Configuration (`args/`)

Run configs (`run_*.json`) are the entry points passed to `assimilator.py`; they reference the
per‑step arg files below.

| File | Used by | Key fields |
|---|---|---|
| `run_enkf.json` / `run_pf.json` | `assimilator.py` | `engine:"python"`, `snapshot_args`, `ensemble_args`, `run_args` |
| `run_openda.json` / `run_openda_pf.json` | `assimilator.py` | `engine:"openda"`, `snapshot_args`, `ensemble_args`, `filter` (EnKF\|DEnKF\|EnSR\|PF), `openda_dir` (`run_openda_pf.json` is the PF preset) |
| `snapshot.json` | step 1 | `lake`, `snapshot_date`, `ensemble_base`, `external` |
| `ensemble.json` | steps 2–3 | `lake`, `n_members`, `start_date`, `end_date`, `lake_bbox`, `reanalysis_dir` |
| `enkf.json` | python `run_args` | `algorithm:"EnKF"`, `results_dir`, `par_file`, `sigma_obs`, `inflation`, `reset` |
| `pf.json` | python `run_args` | `algorithm:"PF"`, `results_dir`, `par_file`, `reset` |

The `lake` field resolves data and run paths by convention: observations from
`data/T_obs_<lake>.csv`, ensemble from `run/<lake>/`.

## The OpenDA engine (`openda_simstrat/`)

OpenDA runs Simstrat as a "black box": it clones a template directory once per ensemble member,
calls a wrapper script that runs Simstrat in Docker, and applies the Kalman update to each
member's temperature state at every analysis (observation) time.

The setup is **almost entirely generated per run** from a single source of truth
(`src/alplakes_da/openda/config.py`), driven by three inputs — the chosen `filter`, `n_members`, and the
observation depths (auto‑detected from `data/T_obs_<lake>.csv`, restricted to the depths the model
actually outputs). The observation depth list flows into every coupled file, so a different lake
needs no manual edits.

```
openda_simstrat/
├── run.oda                          GENERATED  entry point (selects the filter's algorithm + results)
├── parallel.gen.xml                 GENERATED  thread/ensemble config (maxThreads = n_members + 1)
├── algorithms/<filter>.gen.xml      GENERATED  algorithm config (EnKF/DEnKF/EnSR/PF, ensembleSize)
├── stochObserver/
│   ├── timeSeriesFormatter.gen.xml  GENERATED  observations + time window + obs std
│   └── T_<d>m_real.csv              built by the adapter (one reading/day nearest noon UTC)
├── stochModel/
│   ├── simstratModel.gen.xml        GENERATED  instanceDir + exchange items (per depth)
│   ├── simstratStochModel.gen.xml   GENERATED  state + predictor spec
│   ├── simstratWrapperEnKF.xml      static, lake-independent wrapper config
│   ├── template/                    base Simstrat files cloned into each work dir
│   │   ├── Settings.par, *.dat, aed2.nml, ...   synced from run/<lake>/standard_inputs
│   │   ├── time_control.yaml        GENERATED  run window (Simstrat days)
│   │   ├── temperature_state.txt    seeded from the warmup snapshot's full-grid T profile
│   │   ├── obs_depths.json          GENERATED  depth list the wrapper reads
│   │   ├── timeSeriesFormatter.gen.xml  GENERATED  model-output (predictor) config
│   │   └── Results/simulation-snapshot.dat   warmup snapshot
│   └── bin/simstrat_wrapper_enkf.py  black-box wrapper OpenDA calls (runs Simstrat via Docker)
└── forcings/Forcing_{0..N}.dat       perturbed forcings, synced from the ensemble by the adapter
```

Only `simstratWrapperEnKF.xml`, `bin/`, and the base files in `template/` are hand‑maintained;
everything marked GENERATED (and `run.oda`) is rewritten on each run by `assimilator.py`
(`alplakes_da/openda/adapter.py` syncs inputs/forcings/warmup and builds observations;
`alplakes_da/openda/config.py` renders the config). Adding a new filter is a one‑line entry in the `FILTERS` spec.

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
python src/assimilator.py args/run_openda.json            # full run
python src/assimilator.py args/run_openda.json --dry-run  # preview, write nothing
python src/assimilator.py args/run_openda.json --skip-oda # generate config, don't launch
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

One command runs preprocessing (skipping any already done) and the assimilation:

```bash
python src/assimilator.py args/run_enkf.json     # or args/run_pf.json
```

Add `--dry-run` to preview the plan, or `--force-initial` / `--force-copy` / `--force-perturbate`
to re‑run a preprocessing step that otherwise looks done. The stage scripts can still be run
standalone if needed:

```bash
python src/initial_conditions_snapshot.py args/snapshot.json
python src/copy_standard_inputs.py        args/ensemble.json
python src/perturbate.py                  args/ensemble.json
```

Per‑member results are written to `run/<lake>/ensemble{i}/Results_<algo>/`, with the ensemble‑mean
trajectory and diagnostics alongside in `run/<lake>/`. On completion a posterior summary (ensemble
mean + 1σ per time/depth) and a skill/bias report are auto‑written to
`final_output/<lake>_python_<algo>.{csv,json}`.

## Prerequisites

- Python 3 with `numpy`, `pandas`, `geopandas`, `requests`, `tqdm`, `matplotlib`.
- **Docker** with the `eawag/simstrat:3.0.4` image available.
- For the OpenDA engine only: an **OpenDA 3.4.0** installation, run under WSL/Linux.
