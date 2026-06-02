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

| Engine | Entry point | Filters | Role |
|---|---|---|---|
| **Native Python** | `src/assimilate.py` | EnKF, PF | Primary in‑house implementation |
| **OpenDA black‑box** | `src/openda_assimilation.py` | EnKF, DEnKF, EnSR | Independent reference / cross‑check |

Simstrat itself always runs in **Docker** (`eawag/simstrat:3.0.4`); no local Simstrat binary is
needed. The OpenDA engine additionally requires an OpenDA installation (see
[Running the OpenDA engine](#running-the-openda-engine)).

## Workflow

Both engines share the same preprocessing. Each step is driven by a JSON file in `args/`:

```
1. initial_conditions_snapshot.py  snapshot.json   spin-up -> run/<lake>/standard_inputs + warmup snapshot
2. copy_standard_inputs.py         ensemble.json   clone     -> run/<lake>/ensemble0..N  (0 = control)
3. perturbate.py                   ensemble.json   ICON reanalysis -> AR(1)-perturbed Forcing.dat in ensemble1..N
                                                   (runs the prep_reanalysis pipeline)
4. assimilate.py                   enkf.json|pf.json   native EnKF/PF, daily updates
   — or —
   openda_assimilation.py          openda_assimilation.json   runs steps 1–3 (skipping done ones),
                                                   then generates the OpenDA config and launches it
```

- **Native path:** run steps 1→2→3→4 (`assimilate.py`).
- **OpenDA path:** run `openda_assimilation.py` alone — it orchestrates the whole chain and re‑uses
  any already‑completed preprocessing.

## Repository layout

```
.
├── src/                     Python source
│   ├── alplakes_da/         Importable package (core library)
│   │   ├── functions.py        Docker/Simstrat helpers, logging, arg validation
│   │   ├── simstrat.py         Simstrat run + state read/write helpers
│   │   ├── snapshot_io.py      Read/write Simstrat Fortran binary snapshots
│   │   ├── EnKF_assimilate.py  Native Ensemble Kalman Filter
│   │   ├── PF_assimilate.py    Native Particle Filter
│   │   ├── visualize.py        Plotting helpers
│   │   └── prep_reanalysis/    Meteo pipeline: ICON reanalysis → perturbed forcing ensemble
│   │                           (see src/alplakes_da/prep_reanalysis/README.md)
│   ├── initial_conditions_snapshot.py   step 1 (spin-up + warmup snapshot)
│   ├── copy_standard_inputs.py          step 2 (build ensemble instances)
│   ├── perturbate.py                    step 3 (reanalysis + AR(1) forcing perturbation)
│   ├── assimilate.py                    step 4 — native EnKF/PF
│   ├── openda_adapter.py                OpenDA: sync inputs/forcings/warmup + build observations
│   ├── openda_config.py                 OpenDA: single source of truth that generates the config
│   └── openda_assimilation.py           OpenDA: end-to-end orchestrator
│
├── args/                    One JSON config per entry point (see Configuration)
├── static/                  Version/lake-independent templates: simstrat_<ver>.par, aed2.nml,
│                            lake_parameters.json
├── standard_inputs/         Per-lake baseline Simstrat packages (bathymetry, grid, calibrated
│                            Settings.par, inflows) — the source inputs for step 1
├── data/                    Observations (T_obs_<lake>.csv) and lake-mean meteo
│                            (lake_mean_<lake>_<year>.csv); large files are git-ignored
├── run/                     Working area (git-ignored per lake)
│   ├── <lake>/standard_inputs/   spun-up inputs + dated warmup snapshot
│   ├── <lake>/ensemble0..N/      control (0) + perturbed members; DA writes Results_* here
│   └── openda/work_<filter>/work0..N/   OpenDA per-member scratch (Results/T_out.dat)
│
├── openda_simstrat/         OpenDA black-box configuration (see below; mostly generated)
├── experiments/             Research/dev scripts (main_EnKF.py, main_PF_*.py, analysis, old*/)
├── snapshot_examples/       Examples + sample binaries for snapshot_io (git-ignored data)
├── logs/                    Timestamped pipeline logs
├── docs/ + mkdocs.yml       Documentation site
└── assimilation/            Git-ignored scratch/output
```

## Configuration (`args/`)

| File | Used by | Key fields |
|---|---|---|
| `snapshot.json` | `initial_conditions_snapshot.py` | `lake`, `snapshot_date`, `ensemble_base`, `external` |
| `ensemble.json` | `copy_standard_inputs.py`, `perturbate.py` | `lake`, `n_members`, `start_date`, `end_date`, `lake_bbox`, `reanalysis_dir` |
| `enkf.json` | `assimilate.py` | `algorithm:"EnKF"`, `lake`, `sigma_obs`, `inflation`, dates |
| `pf.json` | `assimilate.py` | `algorithm:"PF"`, `lake`, dates |
| `openda_assimilation.json` | `openda_assimilation.py` | `snapshot_args`, `ensemble_args`, `filter` (EnKF\|DEnKF\|EnSR), `openda_dir` |

The `lake` field resolves data and run paths by convention: observations from
`data/T_obs_<lake>.csv`, ensemble from `run/<lake>/`.

## The OpenDA engine (`openda_simstrat/`)

OpenDA runs Simstrat as a "black box": it clones a template directory once per ensemble member,
calls a wrapper script that runs Simstrat in Docker, and applies the Kalman update to each
member's temperature state at every analysis (observation) time.

The setup is **almost entirely generated per run** from a single source of truth
(`src/openda_config.py`), driven by three inputs — the chosen `filter`, `n_members`, and the
observation depths (auto‑detected from `data/T_obs_<lake>.csv`, restricted to the depths the model
actually outputs). The observation depth list flows into every coupled file, so a different lake
needs no manual edits.

```
openda_simstrat/
├── run.oda                          GENERATED  entry point (selects the filter's algorithm + results)
├── parallel.gen.xml                 GENERATED  thread/ensemble config (maxThreads = n_members + 1)
├── algorithms/<filter>.gen.xml      GENERATED  algorithm config (EnKF/DEnKF/EnSR, ensembleSize)
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
everything marked GENERATED (and `run.oda`) is rewritten on each run by `openda_assimilation.py`
(`openda_adapter.py` syncs inputs/forcings/warmup and builds observations; `openda_config.py`
renders the config). Adding a new filter is a one‑line entry in the `FILTERS` spec.

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
python src/openda_assimilation.py args/openda_assimilation.json            # full run
python src/openda_assimilation.py args/openda_assimilation.json --dry-run  # preview, write nothing
python src/openda_assimilation.py args/openda_assimilation.json --skip-oda # generate config, don't launch
```

Set `"filter"` in `args/openda_assimilation.json` to `EnKF`, `DEnKF`, or `EnSR`. Output for each
filter goes to `run/openda/work_<filter>/workN/Results/T_out.dat` (hourly, full water column) plus
`openda_simstrat/<filter>_results.py` (OpenDA `PythonResultWriter`).

> **Output convention:** in `<filter>_results.py`, `pred_a_central` is `H·x_f` (the forecast
> prediction), not `H·x_a`. To see the true analysis correction at observation depths, read the
> `x_a_central` columns directly.

## Running the native engine

```bash
# preprocessing (once per lake/period)
python src/initial_conditions_snapshot.py args/snapshot.json
python src/copy_standard_inputs.py        args/ensemble.json
python src/perturbate.py                  args/ensemble.json
# assimilation
python src/assimilate.py                  args/enkf.json     # or args/pf.json
```

Per‑member results are written to `run/<lake>/ensemble{i}/Results_<algo>/`, with the ensemble‑mean
trajectory and diagnostics alongside in `run/<lake>/`.

## Prerequisites

- Python 3 with `numpy`, `pandas`, `geopandas`, `requests`, `tqdm`, `matplotlib`.
- **Docker** with the `eawag/simstrat:3.0.4` image available.
- For the OpenDA engine only: an **OpenDA 3.4.0** installation, run under WSL/Linux.
