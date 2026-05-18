# OpenDA EnKF — Simstrat cross-validation

Independent EnKF implementation using [OpenDA](https://www.openda.org) to validate `src/main_EnKF.py`.

Both run the same Simstrat ensemble, the same observations, and equivalent EnKF mathematics. Differences in the analysis state reveal implementation discrepancies.

---

## Architecture

```
OpenDA (Java)
  ├── stochObserver  ← daily mean T obs at 0.5 m depth
  ├── stochModelFactory (ThreadStochModelFactory)
  │     └── BBStochModelFactory × 20 members (parallel)
  │           └── simstratWrapper.xml
  │                 └── run_simstrat.py  ← Python bridge
  │                       ├── writes T → Simstrat snapshot
  │                       ├── docker exec → Simstrat forward run
  │                       └── reads T_out.dat → obs prediction
  └── EnKF algorithm  ← computes gain, updates state vector
```

Each ensemble member communicates with OpenDA through three ASCII files in its instance directory:

| File | Written by | Read by | Contains |
|---|---|---|---|
| `temperature_state.txt` | OpenDA (x_a) / bridge (x_f) | bridge / OpenDA | Full T profile, one value per line |
| `temperature_obs.txt` | bridge | OpenDA | T at 0.5 m depth (H × x_f) |
| `time_config.txt` | OpenDA | bridge | MJD window start, step, end |

---

## Prerequisites

- **OpenDA 3.4.0** — bundled in `openda_3.4.0/` at the project root (no download needed)
- **Docker** — Simstrat image `eawag/simstrat:3.0.4` must be pullable
- **Python ≥ 3.9** with `numpy`, `pandas`, `scipy` (same environment as the rest of this repo)
- Initialised Simstrat ensembles under `assimilation/upperlugano/ensemble{1..20}/`  
  (dated snapshot files `simulation-snapshot_*.dat` must exist)

---

## Setup and run

Run all commands from the **project root** unless stated otherwise.

### 1 — Activate OpenDA

```bash
# Linux / WSL — run from the project root (alplakes-da/)
export OPENDADIR=$(pwd)/openda_3.4.0/bin
source $OPENDADIR/settings_local.sh

# Windows — setup is called automatically by oda_run_batch.bat; no extra step needed
```

### 2 — Initialise instance directories

Reads initial temperature from each member's Simstrat snapshot and creates
`openda_enkf/instances/instance{0..19}/` with the exchange files.

```bash
python openda_enkf/scripts/init_instances.py --lake upperlugano --n-members 20
```

### 3 — Prepare observations

Converts `data/T_obs_castagnola.csv` to a daily-mean CSV in OpenDA format and
writes it to `openda_enkf/stochObserver/obs_depth_0.5m.csv`.

```bash
python openda_enkf/scripts/prep_obs.py --lake upperlugano --start 2025-01-01 --end 2025-12-31
```

### 4 — Start Docker containers

Each member needs a persistent container so Simstrat can be triggered quickly
via `docker exec` without container startup overhead.

```bash
python openda_enkf/scripts/start_containers.py --lake upperlugano --n-members 20
```

### 5 — Run OpenDA

```bash
cd openda_enkf
../openda_3.4.0/bin/oda_run_batch.bat enkf.oda   # Windows
../openda_3.4.0/bin/oda_run.sh enkf.oda          # Linux / WSL
```

OpenDA steps through every observation time, runs all 20 members in parallel
(up to 4 at a time), and applies the EnKF update at each step.

### 6 — Stop containers

```bash
python openda_enkf/scripts/stop_containers.py
```

---

## Configuration

### Paths

All paths in `stochModel/simstratBlackBoxModel.xml` are relative to `stochModel/`:

```xml
<alias key="ensembleBase"  value="../../assimilation/upperlugano"/>
<alias key="instanceDir"   value="../instances/instance"/>
<alias key="scriptsDir"    value="../scripts"/>
```

Update `ensembleBase` if switching lakes.

### EnKF parameters

| Parameter | Location | Value | Matches `main_EnKF.py` |
|---|---|---|---|
| Ensemble size | `algorithms/EnKF.xml` | 20 | ✓ |
| Obs error σ | `stochObserver/timeSeriesFormatter.xml` | 0.4 °C | ✓ |
| Inflation | `scripts/run_simstrat.py` (`INFLATION`) | 1.05 | ✓ |
| Obs depth | `scripts/run_simstrat.py` (`OBS_DEPTHS`) | 0.5 m | ✓ |
| Analysis frequency | `algorithms/EnKF.xml` | from obs times (daily) | ✓ |

> **Note on inflation:** OpenDA's `EnkfConfig` has no native inflation parameter.
> Multiplicative anomaly inflation is instead applied inside `run_simstrat.py`
> before writing the forecast state (`APPLY_INFLATION = True`).
> Set it to `False` to run without inflation for a cleaner algorithm comparison.

### Parallelism

`parallel.xml` limits concurrent Simstrat runs to 4 threads. Raise `<maxThreads>`
if your machine has more cores and enough Docker resources.

---

## Time conventions

| System | Format | Reference |
|---|---|---|
| OpenDA | Modified Julian Date (MJD) | 1858-11-17 |
| Simstrat | Days since 1981-01-01 | 1981-01-01 |
| Conversion | `simstrat_time = MJD − 44239` | — |

Observation timestamps in `obs_depth_0.5m.csv` use **00:00:00 of day+1**, so
the row labelled `2025-01-02T00:00:00` contains the daily mean for 2025-01-01.
This aligns with the one-day analysis window used in `main_EnKF.py`.

---

## Directory layout

```
openda_enkf/
├── enkf.oda                         Main OpenDA application
├── parallel.xml                     Thread model factory
├── algorithms/
│   └── EnKF.xml                     EnKF algorithm parameters
├── stochModel/
│   ├── simstratStochModel.xml        State + predictor vector spec
│   ├── simstratBlackBoxModel.xml     Exchange items and alias paths
│   └── simstratWrapper.xml          Execution spec (calls run_simstrat.py)
├── stochObserver/
│   ├── timeSeriesFormatter.xml       Observation config
│   └── obs_depth_0.5m.csv           Generated by prep_obs.py
├── instances/                        Generated by init_instances.py
│   ├── instance0/
│   │   ├── temperature_state.txt
│   │   ├── temperature_obs.txt
│   │   └── time_config.txt
│   └── instance1/ … instance19/
└── scripts/
    ├── init_instances.py             Pre-run initialisation
    ├── prep_obs.py                   Observation preparation
    ├── run_simstrat.py               OpenDA → Simstrat bridge (called per step)
    ├── start_containers.py           Start Docker containers
    └── stop_containers.py            Stop Docker containers
```

---

## Comparing results

After both `main_EnKF.py` and the OpenDA run have completed, compare the analysis
states by reading the per-member `T_out_full.dat` trajectories (written by
`main_EnKF.py`) against the Simstrat output in each member's `Results_EnKF_openda/`
directory. The ensemble means should agree at each analysis time within numerical
precision if the implementations are equivalent.

The main expected differences are:
- **Inflation timing** — `main_EnKF.py` inflates inside the update step;
  the OpenDA bridge inflates after the forward run. Results should match when
  `APPLY_INFLATION = True`.
- **Observation perturbations** — `main_EnKF.py` draws fresh `ε ~ N(0, R)` per
  member per step; OpenDA's stochastic EnKF does the same internally.
  Different random seeds will cause member-level differences but ensemble
  statistics should agree.
