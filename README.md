# Data Assimilation for Lake Hydrodynamic Models

Improve lake-temperature forecasts by blending in-situ observations into lake models
(e.g. **[Simstrat](https://github.com/Eawag-AppliedSystemAnalysis/Simstrat)**), for the
[Alplakes](https://www.alplakes.eawag.ch) platform at [Eawag](https://www.eawag.ch).

You give it a lake's model setup and a CSV of measured temperatures. It runs an ensemble of simulations, corrects them toward the observations at each assimilation step, and returns a corrected temperature profile through time — with a skill report against the data.

## What you can do

Pick an **assimilation method** by choosing a run config; everything else is the same:

| You want | Run config | Method |
|---|---|---|
| Ensemble Kalman Filter (default) | `args/run_enkf.json` | EnKF |
| Particle Filter | `args/run_pf.json` | PF |
| An independent cross-check via [OpenDA](https://www.openda.org) | `args/run_openda.json` | EnKF / DEnKF / EnSR / PF |

The first two are the native, in-house engine. The OpenDA engine runs the *same* ensemble and
observations through a separate, established toolkit, so you can cross-validate the results or build custom functionalities easily in the native setup.

With the OpenDA engine you also choose *which* EnKF filter variant to run by editing the `filter`
field in `args/run_openda.json` — `EnKF`, `DEnKF`, `EnSR` — without touching anything else.

To tune a run to the desired settings, edit these fields in the run config:

| Field | What it controls |
|---|---|
| `n_members` | Ensemble size (more members → better spread and statistics, with the cost of a slower run) |
| `start_date`, `end_date` | The simulation window |
| `sigma_obs` | Observation error σ in °C — how much to trust the measurements (smaller = pulled harder toward the data). |
| `inflation` | Variance inflation factor (native EnKF only); `1.0` = off, `>1.0` counters ensemble collapse |
| `sigma_scale` | Scales the forcing-perturbation strength applied to the members to artificially increase the spread (1.0 = no scaling)|
| `rng_seed` | Random seed for reproducible runs |

## Quick start

**1. Install prerequisites**

- Python 3 with `numpy`, `pandas`, `geopandas`, `requests`, `tqdm`, `matplotlib`
- [Docker](https://www.docker.com/) with the `eawag/simstrat:3.0.4` image (Simstrat runs in Docker — no local build)

**2. Provide the two inputs for your lake** (here e.g. `upperlugano`)

- `inputs/upperlugano/` — the Simstrat model setup plus a dated warm-start snapshot
  (`simulation-snapshot_<YYYYMMDD>.dat`, `Forcing.dat`, `Settings.par`, bathymetry, grid, …)
- `observations/upperlugano/temperature.csv` — long-format measurements, one row per reading:

  | `time` | `depth` | `value` |
  |---|---|---|
  | `2025-06-01T11:55:00+00:00` (UTC) | `0.5` (m, positive down) | `12.3` (°C) |

**3. Run**

```bash
python src/main.py args/run_enkf.json
```

The pipeline copies the setup into an ensemble, perturbs the forcing, runs the
assimilation, and writes the results. Re-running re-uses any finished steps.

> Multiple lakes in one config? Add `--lake <name>` to pick one.

## Outputs

In the run folder (`run/<lake>/` for the native engine):

- **`<lake>_python_<algo>.csv`** — the corrected temperature profile: posterior mean ± 1σ per
  time and depth.
- **`<lake>_python_<algo>.json`** — a skill report (RMSE / bias) scoring the result against the
  observations it assimilated.

Compare engines or visualize a run with `python notebooks/visualize.py`.

## Notes on setting up a simulation

| Topic | Where |
|---|---|
| Running the OpenDA engine (needs WSL/Linux + OpenDA 3.4.0) | `args/run_openda.json` & `args/run_openda_pf.json`; set `openda_bin` |
| Calibrating the forcing perturbation (one-time, offline) | `notebooks/perturbations_from_icon.py` (needs EAWAG ICON API / VPN) |

## How it works

`src/main.py` is the single entry point of the module. It runs five steps, skipping any already done:

```
1. require model inputs   inputs/<lake>/                  (you provide this)
2. copy to ensemble       -> ensemble0..N  (0 = control, 1..N = members)
3. perturb forcing        AR(1) noise on the members' Forcing.dat
4. assimilate             EnKF / PF / OpenDA update toward the observations
5. summarize              posterior mean ± std + skill report
```

Both engines share a core library (`src/assimilator/`) and they assimilate the identical
observations (for now the centered noon-hour profile each day).
