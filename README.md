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
(see [Providing model_inputs](#providing-model_inputs)) and the **observations** in
`observations/<lake>/temperature.csv` (see [Providing observations](#providing-observations)).
`src/main.py` then orchestrates the chain end‑to‑end, skipping any step already done:

```
1. require model_inputs   (provided manually)   -> inputs/<lake>/                [error if missing]
2. copy_model_inputs      run_*.json      clone -> run/<lake>/ensemble0..N       (0 = control)
3. perturbate                run_*.json      AR(1) noise from perturbations/<lake>.json
                                              -> perturbed Forcing.dat in ensemble1..N
4. run                       engine=python:  native EnKF/PF daily updates (algorithm: EnKF|PF)
                             engine=openda:  render the OpenDA config + launch the filter
5. summarize                 posterior mean+std + skill report -> the run's own folder (under run/)
```

Run either engine with one command — it re‑uses any already‑completed preprocessing:

```bash
python src/main.py args/run_enkf.json                # native EnKF (single-lake config: auto-selected)
python src/main.py args/run_pf.json    --lake geneva  # native PF on a chosen lake
python src/main.py args/run_openda.json               # OpenDA
```

Add `--force-copy` to re‑run the copy step that otherwise looks done.
(Step 3 perturbate always runs — it requires a committed `perturbations/<lake>.json` and errors if missing.)

Each `run_*.json` carries the engine knobs and the run window (`start_date`, `end_date`,
`n_members`, `sigma_obs`, …) at the top level, plus a `lakes` map of lake‑identity blocks
(`reanalysis_lake`, `lake_bbox`, `lake_key`). `--lake <name>` picks one block (the only one by
default) and merges it in; adding a lake is one more block.

### The forcing-perturbation calibration (one-time, offline)

Step 3 perturbs the wind/solar forcing with AR(1) noise whose statistics `(phi, sigma)` are fit
once from ICON reanalysis and cached in **`perturbations/<lake>.json`** (committed). That fit
needs the EAWAG ICON API (VPN) and is run separately, rarely:

```bash
python notebooks/perturbations_from_icon.py args/run_enkf.json [--check]   # writes perturbations/<lake>.json
```

`--check` also writes QA plots to `run/<lake>/` (`check.png`: grid mask + lake-mean series;
`check_fit.png`: residual ACF vs fitted φ, residual distribution, preview perturbed ensemble).
Once `perturbations/<lake>.json` exists, `main.py` step 3 needs no ICON access. If it's missing,
step 3 errors with instructions.

### Providing model_inputs

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
│   └── assimilator/             Importable package (core library shared by both engines)
│       ├── functions.py            Model-agnostic shared base: path/config helpers (loads
│       │                           static/general.json), obs loaders, lake/obs resolvers,
│       │                           arg validation, build_python_run_args
│       ├── perturbate.py           Step 3 (apply): simulate AR(1) -> perturbed Forcing.dat per member
│       ├── summarize.py            Posterior summary (.csv) + skill/bias report (.json) + report_summary
│       ├── models/                 Forward models, selected by the "model" arg / -m. Add a model = add a file
│       │   ├── base.py                Model interface — the methods any model must implement
│       │   └── simstrat.py            ALL Simstrat behaviour: Docker run, .par, z_out/T_out, binary snapshot I/O
│       ├── algorithms/             Native engines (engine="python")
│       │   ├── enkf.py                Ensemble Kalman Filter (run_enkf)
│       │   └── pf.py                  Particle Filter (run_pf)
│       └── openda/                 OpenDA cross-validation bridge
│           ├── adapter.py             Sync inputs/forcings/warmup + build observations (run_openda)
│           └── config.py              Render run.oda + every .gen.xml from the FILTERS spec
│
├── notebooks/               Standalone scripts (add src/ to the path, import assimilator)
│   ├── perturbations_from_icon.py  Offline calibration: ICON acquisition + AR(1) fit -> perturbations/<lake>.json
│   ├── check_perturbations.py      QA plots for the fit (acquisition + fit diagnostics)
│   └── visualize.py                Comparison plots + RMSE table across engines
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
│   ├── <lake>/                  native-engine run folder: ensemble0..N (control + members; DA writes
│   │                            Results_* here) + the posterior summary <lake>_python_<algo>.{csv,json}
│   └── openda_<model>_<lake>_<filter>/   self-contained OpenDA run dir, e.g. openda_simstrat_upperlugano_enkf
│       │                              (generated, git-ignored):
│       ├── Results/work0..N/           per-member scratch (each: Results/T_out.dat + simstrat_wrapper log)
│       ├── Results/<filter>_results.py OpenDA PythonResultWriter output
│       ├── log/openda_logfile.txt      OpenDA run log
│       └── <lake>_openda_<filter>.{csv,json}   posterior summary (mean+std) + skill/bias report
│
│   Summaries (.csv = posterior mean + std per time/depth; .json = skill/bias report vs obs)
│   are written into each run's own folder above — no top-level final_output/.
├── logs/                    Timestamped pipeline logs
└── docs/ + mkdocs.yml       Documentation site
```

## Configuration (`args/`)

Run configs (`run_*.json`) are the entry points passed to `main.py`. Each holds the engine/model
selection + engine knobs + the run window at the top level, plus a `lakes` map; `--lake <name>`
selects a block (the only one by default) and merges it on top. No nested files.

| Section | Engine | Key fields |
|---|---|---|
| top level — `run_enkf.json` / `run_pf.json` | python | `engine:"python"`, `algorithm` (`EnKF`\|`PF`), `results_dir`, `par_file`, `inflation` (native-EnKF only), `reset` |
| top level — `run_openda.json` / `run_openda_pf.json` | openda | `engine:"openda"`, `filter` (EnKF\|DEnKF\|EnSR\|PF), `openda_bin`, `openda_dir` |
| top level — run window (every config) | both | `n_members`, `start_date`, `end_date`, `sigma_obs` (obs error σ — shared by native EnKF + OpenDA), `rng_seed`, `sigma_scale` |
| top level — file overrides (optional) | both | `obs_file` (observation CSV; default `observations/<lake>/temperature.csv`), `perturbations_file` (AR(1) calibration JSON; default `perturbations/<lake>.json`) — paths relative to the repo root or absolute. Also settable on the CLI: `--obs-file` / `--perturbations-file` (flag > config key > default) |
| `lakes.<name>` — one block per lake | both + fit | `reanalysis_lake`, `lake_bbox`, `lake_key` (the lake identity; bbox/key used by the fit). `ensemble_base` defaults to `../run/<lake>` |

The `lake` field resolves data and run paths by convention: observations from
`observations/<lake>/temperature.csv`, ensemble from `run/<lake>/`, calibration from `perturbations/<lake>.json`.

## The OpenDA engine (`run/openda_<model>_<lake>_<filter>/`)

OpenDA runs Simstrat as a "black box": it clones a template directory once per ensemble member,
calls a wrapper script that runs Simstrat in Docker, and applies the Kalman update to each
member's temperature state at every analysis (observation) time.

`run/openda_<model>_<lake>_<filter>/` (e.g. `run/openda_simstrat_upperlugano_enkf/`) is a
**fully generated working directory** (git-ignored, built on demand):

- `src/assimilator/openda/config.py` renders `run.oda`, `parallel.gen.xml`,
  `algorithms/<filter>.gen.xml`, `stochModel/simstrat{Model,StochModel}.gen.xml`,
  `stochModel/template/{time_control.yaml,obs_depths.json,timeSeriesFormatter.gen.xml}`, and
  `stochObserver/timeSeriesFormatter.gen.xml` — driven by `filter`, `n_members`, and the
  observation depths (auto‑detected from `observations/<lake>/temperature.csv`, restricted to model output depths).
- `src/assimilator/openda/adapter.py` syncs `model_inputs` → `stochModel/template/`,
  the perturbed `Forcing_{0..N}.dat` → `forcings/`, the warmup snapshot →
  `template/Results/simulation-snapshot.dat`, seeds `temperature_state.txt`, builds the
  observation CSVs, and **copies the two hand-maintained files from `static/openda/`**
  (`simstratWrapperEnKF.xml`, `simstrat_wrapper_enkf.py`) into the working tree.

So the **only OpenDA source of truth** is `src/assimilator/openda/config.py` + the two files in
`static/openda/`. Adding a new filter is a one‑line entry in the `FILTERS` spec.

### Running the OpenDA engine

Requires WSL/Linux with Docker running and an OpenDA 3.4.0 install. Set `"openda_bin"` in the run
config (`args/run_openda*.json`) to the OpenDA `bin/` dir, e.g. `"~/openda_3.4.0/bin"`; `run_openda`
then builds the full OpenDA environment (OPENDADIR/OPENDALIB, the bundled JRE + bin on PATH,
LD_LIBRARY_PATH) for the `oda_run.sh` subprocess only — no shell sourcing needed, and nothing leaks
into your shell. (Override the native tag with `"openda_native"`, default `linux64_gnu`.)

Alternatively, omit `"openda_bin"` and source the environment yourself once per shell:

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
python src/main.py args/run_openda.json --skip-oda # generate config, don't launch
```

Set `"filter"` in `args/run_openda.json` to `EnKF`, `DEnKF`, or `EnSR`, or use the
`args/run_openda_pf.json` preset for `PF`. Output for each filter goes to
`run/openda_<model>_<lake>_<filter>/Results/workN/Results/T_out.dat` (hourly, full water column) plus
`run/openda_<model>_<lake>_<filter>/Results/<filter>_results.py` (OpenDA `PythonResultWriter`), and a posterior summary +
skill/bias report are auto‑written to `run/openda_<model>_<lake>_<filter>/<lake>_openda_<filter>.{csv,json}`.

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
`run/<lake>/<lake>_python_<algo>.{csv,json}`.

## Prerequisites

- Python 3 with `numpy`, `pandas`, `geopandas`, `requests`, `tqdm`, `matplotlib`.
- **Docker** with the `eawag/simstrat:3.0.4` image available.
- For the forcing-perturbation fit only: access to the EAWAG ICON reanalysis API (VPN).
- For the OpenDA engine only: an **OpenDA 3.4.0** installation, run under WSL/Linux.
```
