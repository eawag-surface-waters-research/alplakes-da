# alplakes-da — Architecture Plan

> What the three DA backends do today, what is messy about the current setup,
> and how to reorganise them into one operational tool that can run any of the
> three from a single command.
>
> Written May 2026 against the current codebase.

---

## 1. The three backends

Every DA experiment runs one of three backends. A **backend** is the engine that
performs the data assimilation update — how the model is corrected when
observations arrive. The three backends currently live in three separate places
with no shared structure.

**Backend A — Python EnKF** (`src/main_EnKF.py`, Lake Lugano)

Runs 20 perturbed Simstrat instances (ensemble members) in parallel, one per
Docker container. Each day: if observations are available, reads the temperature
state from each member's binary file, computes the **Kalman correction** (a
weighted average between model and observations, where the weight depends on
how uncertain each source is), and writes the corrected state back. Saves
diagnostics (innovation statistics, Kalman gain profile).

**Backend B — Python Particle Filter** (`src/main_PF_fast.py`, Lake Geneva)

Same parallel Docker run. Each day: scores each member by its RMSE (root-mean-
square error — a number measuring how far the model is from observations), then
copies the best-scoring member's binary state file to all other members. Simpler
than the EnKF but loses the spread of the ensemble after each update.

**Backend C — OpenDA** (`OpenDA_Simstrat/`, Lake Lugano)

The same EnKF (and also EnSR, EWPF) implemented inside the OpenDA Java
framework. OpenDA manages the full ensemble loop; a Python wrapper
(`simstrat_wrapper_enkf.py`) handles the Docker calls and state injection per
member. The DA mathematics are performed by OpenDA's internal Java code.
This is a **parallel operational backend** developed alongside the Python
implementation. The two approaches are compared to understand trade-offs —
algorithm correctness, ease of configuration, available filter variants, and
long-term maintainability — before committing to one as the primary system.

---

## 2. The six components every backend needs

Every DA experiment, regardless of backend, requires exactly six things:

| Component | What it does |
|---|---|
| **0. Ensemble setup** | Generates N perturbed Forcing.dat files (AR(1) noise on wind and radiation); copies static inputs to each ensemble directory |
| **1. Model runner** | Starts N Simstrat instances, runs each one for a time window, stops them |
| **2. Observations** | Loads measured temperatures, specifies which depth, which time, how much to trust them |
| **3. State exchange** | Reads model temperature state before the DA update; writes corrected state back |
| **4. Algorithm config** | Ensemble size, observation error, how often to update, which filter to use |
| **5. Output** | Where results are written and in what format |

The table below shows where each component currently lives for each backend:

| Component | Backend A (Python EnKF) | Backend B (Python PF) | Backend C (OpenDA EnKF) |
|---|---|---|---|
| **0. Ensemble setup** | `src/ensembles.py` or `src/ensembles_fromstandard.py` → writes `assimilation/{lake}/ensembleN/Forcing.dat` | same scripts | `src/ensembles*.py` + manual copy to `OpenDA_Simstrat/forcings/Forcing_N.dat`; injected per step in `simstrat_wrapper_enkf.py:step 4` |
| **1. Model runner** | `_start/stop_containers()` + `_run_one_window()` in `main_EnKF.py` | same functions copy-pasted in `main_PF_fast.py` | `parallel_enkf.xml` + `simstratWrapperEnKF.xml` + `simstrat_wrapper_enkf.py` |
| **2. Observations** | `_load_obs()` in `main_EnKF.py` | `_load_obs()` in `main_PF_fast.py` (identical) | `stochObserver/timeSeriesFormatter.xml` + `T_*m_real.csv` files |
| **3. State exchange** | `snapshot_io.py` (read + write snapshot binary) | file copy only (`shutil.copy2` of entire snapshot) | `simstratStochModelEnKF.xml` declares state vector; `snapshot_io.py` (via wrapper) reads/writes; intermediate `temperature_state.txt` per member |
| **4. Algorithm config** | constants at top of `main_EnKF.py` (`SIGMA_OBS=0.4`, `INFLATION=1.05`, `N_MEMBERS`) | constants at top of `main_PF_fast.py` | `algorithms/EnKF.xml` (ensemble size, analysis times) + `timeSeriesFormatter.xml` (σ=0.5 per depth) |
| **5. Output** | `T_out_enkf_filtered_mean.dat` + diagnostic CSVs in `assimilation/upperlugano/` | `T_out_ens_filtered.dat` in `assimilation/geneva/` | `enkf_results.py` in `Results_AssimilationExp/` + `T_out.dat` per member in `work_enkf/` |

**The problems made visible:**

- Components 0, 1, and 2 are copy-pasted between Backends A and B.
- Component 0 has two near-identical scripts (`ensembles.py` and `ensembles_fromstandard.py`) differing only in base signal source; their AR(1) math functions are duplicated verbatim.
- Component 4 has a silent inconsistency: Python uses `σ_obs = 0.4 °C`; OpenDA uses `standardDeviation="0.5"` per depth in XML. These are not the same parameter set.
- Component 0 has a path split: Python backends write forcings to `assimilation/{lake}/ensembleN/Forcing.dat`; OpenDA reads from `OpenDA_Simstrat/forcings/Forcing_N.dat`. There is no automated link between the two locations.
- There is no common entry point or shared config format.

---

## 3. Reading `EnKF.oda` — the OpenDA master config

`EnKF.oda` is the file you pass to OpenDA to start a run. It is 30 lines of XML
and acts as a **table of contents** — it names every component and points to
the file where that component is configured. Reading it is the fastest way to
understand how the OpenDA backend is wired together.

```xml
<!-- EnKF.oda — annotated -->

<stochObserver ...>                              <!-- COMPONENT 2: observations -->
    <workingDirectory>./stochObserver</workingDirectory>
    <configFile>timeSeriesFormatter.xml</configFile>
    <!-- → stochObserver/timeSeriesFormatter.xml lists the 15 depth CSVs
           and their standard deviations (how much we trust each sensor) -->
</stochObserver>

<stochModelFactory ...ThreadStochModelFactory>   <!-- COMPONENT 1: model runner -->
    <workingDirectory>.</workingDirectory>
    <configFile>parallel_enkf.xml</configFile>
    <!-- → parallel_enkf.xml sets thread count (21) and points to
           simstratStochModelEnKF.xml, which points to simstratWrapperEnKF.xml,
           which calls simstrat_wrapper_enkf.py (Docker + snapshot_io) per member -->
</stochModelFactory>

<algorithm ...EnKF>                              <!-- COMPONENT 4: algorithm config -->
    <workingDirectory>./algorithms</workingDirectory>
    <configString>EnKF.xml</configString>
    <!-- → algorithms/EnKF.xml: ensembleSize=20, analysisTimes=fromObservationTimes -->
</algorithm>

<resultWriters>                                  <!-- COMPONENT 5: output -->
    <resultWriter ...PythonResultWriter>
        <configFile>enkf_results.py</configFile>
        <!-- → writes x_f_central, x_a_central, pred_f_central per analysis step -->
    </resultWriter>
</resultWriters>

<!-- COMPONENT 3 (state exchange) is not in this file.
     It is declared inside the stochModel chain:
     simstratStochModelEnKF.xml defines the state vector (576 temperature cells)
     simstratWrapperEnKF.xml tells OpenDA to call simstrat_wrapper_enkf.py,
     which uses snapshot_io.py to inject the corrected state into the binary file. -->
```

Each level of the chain does one thing and hands off to the next:

```
EnKF.oda                        ← master config (what runs, where)
   ├── stochObserver/
   │   └── timeSeriesFormatter.xml  ← which obs files, σ per depth
   ├── parallel_enkf.xml            ← thread pool size
   │   └── simstratStochModelEnKF.xml ← state vector definition (576 cells)
   │       └── simstratWrapperEnKF.xml ← Docker call + state file paths
   │           └── simstrat_wrapper_enkf.py ← Python: runs Docker, calls snapshot_io
   │               └── snapshot_io.py       ← reads/writes Fortran binary
   ├── algorithms/EnKF.xml          ← ensembleSize, analysis schedule
   └── enkf_results.py              ← output file written by OpenDA
```

This chain is the OpenDA equivalent of what `main_EnKF.py` does in 600 lines
of Python — but broken across six files instead of one.

---

## 4. Target: one tool, three backends

The goal is to bring all three backends under a single command, following the
conventions already established in the alplakes ecosystem by two companion tools:

- **lake-calibrator** — uses `args/` JSON files and a `backend` dispatch pattern
- **operational-simstrat** — splits config into two levels: `args/` (run-level
  flags) and `static/lake_parameters.json` (fixed per-lake properties); adds a
  `Config` class with defaults and validation, a model class with per-step
  methods, and supports command-line overrides

Combining both:

```
python run.py args/enkf.json
python run.py args/enkf.json lakes=upperlugano n_members=10
python run.py args/openda_enkf.json
python run.py args/pf.json lakes=geneva
```

The `args/` file sets the backend and algorithm parameters. Two static files store
what is fixed per lake: `static/lake_parameters.json` (physical properties, shared
with operational-simstrat) and `static/lake_da.json` (DA-specific additions).
Command-line `key=value` pairs override anything in the JSON — useful for quick tests.

---

## 5. The integrated file structure

The key design decision: **OpenDA files stay where they are.** The Python
package does not absorb the XML stack. Instead, a thin bridge module
(`backends/openda.py`) reads the JSON config and triggers the OpenDA run.
Three things are genuinely shared between both worlds: `io/snapshot_io.py`,
the observation CSV files, and the perturbed `Forcing.dat` files generated
by `ensemble/forcing.py`.

```
alplakes_da/                            ← Python package
│
├── args/                               ← run-level config (one per experiment type)
│   ├── enkf.json                       ← Backend A: algorithm params + which lakes
│   ├── pf.json                         ← Backend B: algorithm params + which lakes
│   ├── openda_enkf.json                ← Backend C: EnKF via OpenDA
│   └── openda_ensr.json                ← Backend C: EnSR via OpenDA
│
├── static/
│   ├── lake_parameters.json           ← physical lake properties (mirrors operational-
│   │                                     simstrat — do not add DA-specific fields here)
│   └── lake_da.json                   ← DA-specific additions per lake: ensemble_base,
│                                         obs_file, obs_depth_map, container_tag, etc.
│                                         Linked to lake_parameters.json via "key" field
│
├── src/
│   ├── run.py                          ← entry point (mirrors operational-simstrat/main.py)
│   ├── configuration.py               ← Config class: defaults + verify + load
│   │                                     (mirrors operational-simstrat/configuration.py)
│   ├── assimilation.py                ← EnsembleDA class: orchestrates one lake's DA run
│   │                                     (mirrors operational-simstrat/model.py → Simstrat)
│   │
│   ├── ensemble/
│   │   └── forcing.py                  ← Component 0 (shared by A, B, and C)
│   │                                     fit_ar1 + simulate_ar1 + generate_ensemble()
│   │                                     replaces ensembles.py + ensembles_fromstandard.py
│   │                                     writes forcings to assimilation/ and OpenDA_Simstrat/forcings/
│   │
│   ├── model/
│   │   └── runner.py                   ← Component 1 (shared by A and B)
│   │                                     start/stop Docker containers, run one window
│   │
│   ├── io/
│   │   ├── snapshot_io.py              ← Component 3 (shared by A and C)
│   │   │                                 read/write Simstrat Fortran binary state
│   │   └── observations.py             ← Component 2 (shared by A and B)
│   │                                     load CSV, hourly average
│   │
│   └── backends/
│       ├── base.py                     ← BaseFilter ABC
│       │                                 update(X_f, H, y_obs, R) → X_a
│       │                                 Python-internal contract only; OpenDA does not implement it
│       ├── enkf.py                     ← Component 4 for Backend A
│       │                                 Kalman gain + state update (pure math)
│       ├── denkf.py                    ← deterministic EnKF variant
│       ├── locenkf.py                  ← EnKF with covariance localisation
│       ├── particle_filter.py          ← Component 4 for Backend B
│       │                                 RMSE scoring + best-member copy
│       └── openda.py                   ← bridge to Backend C (not a BaseFilter subclass)
│                                         checks XML consistency, calls oda_run.sh,
│                                         collects results from Results_AssimilationExp/

OpenDA_Simstrat/                        ← OpenDA package (separate, not reorganised)
│
├── EnKF.oda  ◄── master config         (equivalent role to args/enkf.json)
├── EnSR.oda
├── EWPF.oda
│
├── parallel_enkf.xml                   ← Component 1: thread pool (21 threads)
├── parallel_ensr.xml
│
├── algorithms/
│   ├── EnKF.xml                        ← Component 4: ensembleSize, analysis times
│   ├── EnSR.xml
│   └── EWPF.xml
│
├── stochModel/
│   ├── simstratStochModelEnKF.xml      ← Component 3: state vector (576 T cells)
│   │                                     + 15 predictor depths
│   ├── simstratWrapperEnKF.xml         ← Component 1+3: Docker call + state file paths
│   ├── simstrat_wrapper_enkf.py        ← runs Docker, injects state via snapshot_io
│   └── template/                       ← base files cloned into each work/ dir at runtime
│
├── stochObserver/
│   ├── timeSeriesFormatter.xml         ← Component 2: obs config (σ=0.5°C per depth)
│   └── T_1m_real.csv … T_40m_real.csv ← Component 2: observation data (15 depths)
│
├── forcings/
│   └── Forcing_0.dat … Forcing_20.dat ← perturbed wind/solar inputs per member
│
└── work_enkf/                          ← runtime: created by OpenDA at run time
    └── work0/ … work20/               ← one working directory per member
        └── Results/T_out.dat          ← Component 5: per-member hourly output
```

### How the pieces connect at runtime

```
python run.py args/enkf.json lakes=upperlugano
    └── Config.load()
        ├── reads args/enkf.json         → backend="enkf", n_members=20, sigma_obs=0.4
        ├── reads static/lake_parameters.json → upperlugano: elevation, forcing, ...
        ├── reads static/lake_da.json        → upperlugano: obs_file, ensemble_base, ...
        └── applies key=value overrides  → n_members=10 (if passed on command line)
    └── EnsembleDA("upperlugano", lake_params, args)
        └── process()
            ├── runner.start_containers()
            ├── for each day:
            │   ├── runner.run_window_parallel()
            │   ├── observations.load_window()
            │   └── backends/enkf.update()   ← or particle_filter / openda
            └── runner.stop_containers()

python run.py args/openda_enkf.json lakes=upperlugano
    └── same Config.load()
    └── EnsembleDA → process() → backends/openda.run()
        ├── checks algorithms/EnKF.xml ensembleSize == n_members
        ├── calls subprocess("wsl bash oda_run.sh EnKF.oda")
        └── collects results → Results_AssimilationExp/
```

The OpenDA XML files are **not generated** by Python. The bridge only checks
that the key numbers agree and then triggers the run.

---

## 6. Component map across all three backends

Bringing together sections 2 and 5 — exactly which file handles which component
in the target structure:

| Component | Backend A (Python EnKF) | Backend B (Python PF) | Backend C (OpenDA) |
|---|---|---|---|
| **0. Ensemble setup** | `ensemble/forcing.py` | `ensemble/forcing.py` | `ensemble/forcing.py` → writes to `OpenDA_Simstrat/forcings/` as well |
| **1. Model runner** | `model/runner.py` | `model/runner.py` | `parallel_enkf.xml` → `simstratWrapperEnKF.xml` → `simstrat_wrapper_enkf.py` |
| **2. Observations** | `io/observations.py` | `io/observations.py` | `stochObserver/timeSeriesFormatter.xml` + CSV files |
| **3. State exchange** | `io/snapshot_io.py` (read + write) | file copy only (`shutil.copy2`) | `simstratStochModelEnKF.xml` + `io/snapshot_io.py` via wrapper + `temperature_state.txt` per member |
| **4. Algorithm config** | `args/enkf.json` + `static/lake_da.json` | `args/pf.json` + `static/lake_da.json` | `algorithms/EnKF.xml` + σ in `timeSeriesFormatter.xml` |
| **5. Output** | `assimilation/upperlugano/T_out_enkf_*.dat` + diagnostic CSVs | `assimilation/geneva/T_out_ens_*.dat` | `Results_AssimilationExp/enkf_results.py` + `work_enkf/workN/Results/T_out.dat` |

Three files are physically shared between the Python package and OpenDA:
`io/snapshot_io.py` (imported by both), the observation CSV files (read by
both sides independently), and the `Forcing.dat` files generated by
`ensemble/forcing.py` (Python reads them from `assimilation/`; OpenDA reads
from `OpenDA_Simstrat/forcings/` — same generation logic, two output locations).

---

## 7. Configuration

Configuration is split across three files. Things that change per *run* go in
`args/`. Things fixed per lake are split in two: physical properties that are
shared with operational-simstrat stay in `static/lake_parameters.json`
(untouched); DA-specific lake additions go in `static/lake_da.json` so the two
concerns never mix.

### 7.1 DA config — `args/`

One JSON file per backend type — the same pattern lake-calibrator uses
(`simstrat_scipy_neldermead_example.json`, `simstrat_pest_example.json`, etc.).
These files describe **the algorithm only**, not the lake. The `lakes` key sets
a default but is always overridable on the command line.

```
args/
  enkf.json           ← Python EnKF algorithm params
  pf.json             ← Python Particle Filter params
  openda_enkf.json    ← OpenDA EnKF params
  openda_ensr.json    ← OpenDA EnSR params
```

**`args/enkf.json`**
```json
{
  "lakes": ["upperlugano"],
  "backend": "enkf",
  "n_members": 20,
  "sigma_obs": 0.4,
  "inflation": 1.05,
  "debug": false,
  "log": true,
  "reset": false
}
```

**`args/pf.json`**
```json
{
  "lakes": ["upperlugano"],
  "backend": "particle_filter",
  "n_members": 20,
  "debug": false,
  "log": true,
  "reset": false
}
```

**`args/openda_enkf.json`**
```json
{
  "lakes": ["upperlugano"],
  "backend": "openda",
  "algorithm": "EnKF",
  "oda_file": "EnKF.oda",
  "debug": false,
  "log": true
}
```

**`args/openda_ensr.json`** — identical to above, two fields changed:
```json
{
  "lakes": ["upperlugano"],
  "backend": "openda",
  "algorithm": "EnSR",
  "oda_file": "EnSR.oda",
  "debug": false,
  "log": true
}
```

To run on a different lake: `python run.py args/enkf.json lakes=geneva`.
No file editing required.

### 7.2 Physical lake config — `static/lake_parameters.json`

Shared with operational-simstrat. Contains physical properties, forcing sources,
and calibrated Simstrat parameters. **Do not add DA-specific fields here.**

```json
[
  {
    "key": "upperlugano",
    "name": "Lake Lugano (upper basin)",
    "elevation": 270.0,
    "max_depth": 288.0,
    "latitude": 46.00,
    "longitude": 9.01,
    "a_seiche": 0.0056,
    "f_wind": 0.67,
    ...
  }
]
```

### 7.3 DA lake config — `static/lake_da.json`

DA-specific additions only. Linked to `lake_parameters.json` via the same `key`.
`Config.load()` merges both files by key at startup.

```json
[
  {
    "key": "upperlugano",
    "ensemble_base": "assimilation/upperlugano",
    "obs_file": "data/filtered_upperlugano.csv",
    "obs_depth_map": {"0.5": 0},
    "simstrat_version": "3.0.4",
    "par_file": "Settings_EnKF_filtered.par",
    "results_subdir": "Results_EnKF_filtered",
    "container_tag": "enkf_filt",
    "include_member_zero": true,
    "openda_dir": "OpenDA_Simstrat"
  },
  {
    "key": "geneva",
    "ensemble_base": "assimilation/geneva",
    "obs_file": "data/T_obs_geneva.csv",
    "obs_depth_map": {"0.25": 0},
    "simstrat_version": "3.0.4",
    "par_file": "Settings_PF_filtered.par",
    "results_subdir": "Results_PF_filtered",
    "container_tag": "pf",
    "include_member_zero": false
  }
]
```

### 7.3 The `Config` class — validation before the run starts

Following operational-simstrat's `configuration.py`, every argument has a
default, a validation function, and a description. The loader merges the JSON
file, applies command-line overrides, validates all values, and then returns
clean `(args, lake_parameters)` to `run.py`.

```python
# src/configuration.py (sketch)
class Config:
    default_args = {
        "lakes":      {"default": ["upperlugano"], "verify": verify_list,    "desc": "Lakes to run"},
        "backend":    {"default": "enkf",          "verify": verify_string,  "desc": "enkf | particle_filter | openda"},
        "n_members":  {"default": 20,              "verify": verify_integer, "desc": "Ensemble size"},
        "sigma_obs":  {"default": 0.4,             "verify": verify_float,   "desc": "Observation error std (°C)"},
        "inflation":  {"default": 1.05,            "verify": verify_float,   "desc": "Covariance inflation factor"},
        "debug":      {"default": False,            "verify": verify_bool,    "desc": "Raise errors immediately"},
        "log":        {"default": True,             "verify": verify_bool,    "desc": "Write log to file"},
        "reset":      {"default": False,            "verify": verify_bool,    "desc": "Clear snapshots before run"},
    }
```

This means a typo in the JSON (`"n_memebers": 20`) fails loudly at startup
with a clear message rather than silently using the wrong value mid-run.

---

## 8. Step-by-step plan

Each step is small and independently verifiable. Run a 7-day test window after
each step and confirm outputs match before continuing.

| Step | What you do | Files affected | Risk |
|---|---|---|---|
| **1** | Move shared Docker code to `model/runner.py` | New file; both `main_*.py` import from it | Low — no logic change |
| **2** | Create `args/*.json` + `static/lake_da.json` + `Config` class | New files; both `main_*.py` read config instead of top-of-file constants | Low — constants only |
| **3** | Move `_enkf_update` + `_build_H` to `backends/enkf.py` | New file; `main_EnKF.py` imports from it | Low — copied verbatim |
| **4** | Move scoring + copy logic to `backends/particle_filter.py` | New file; `main_PF_fast.py` imports from it | Low — copied verbatim |
| **5** | Move `snapshot_io.py` to `io/`; update import in 3 files | `main_EnKF.py`, `main_PF_fast.py`, `simstrat_wrapper_enkf.py` | Low — one line each |
| **6** | Write `assimilation.py` — `EnsembleDA` class with `process()` and per-step methods | One new file; replaces the monolithic loop in both main scripts | Medium — restructuring |
| **7** | Write `run.py` — `Config.load()` → select lakes → dispatch to backend | One new file | Medium — first full integration |
| **8** | Write `backends/openda.py` — checks XML consistency, calls `oda_run.sh`, collects output | One new file | Medium — subprocess handling |
| **9** | Delete `src/old/`, `src/old_mains/`, `src/old_analyze/`, `src/functions/unused_currently/` | Deleted (recoverable from git) | Irreversible |

After step 7: one command runs all three backends.
After step 9: the codebase contains only what is actively used.

---

## 9. What stays the same

- Simstrat Docker image and how it is invoked
- `snapshot_io.py` internals — only its location changes
- `prep_reanalysis/` data preparation pipeline
- `src/adaptive_filter_general.py` pre-processing step
- All OpenDA XML files — `.oda`, `parallel_enkf.xml`, `algorithms/*.xml`,
  `simstratStochModelEnKF.xml`, `simstratWrapperEnKF.xml`, `timeSeriesFormatter.xml`
- `src/analyze_results_*.py` — read outputs from all backends for comparison;
  not part of the run loop

---

## 10. Open questions

- **`main_PF_resampling.py`**: still used? If not, archive alongside old scripts.
- **Multi-lake runs**: run once per lake (simple) or loop over lakes in one
  invocation? The YAML-per-lake approach supports both.
- **`ensembles.py` vs `ensembles_fromstandard.py`**: both do the same job with different base signal sources. Merge into `ensemble/forcing.py` (see section 11). The merged script also needs to write to `OpenDA_Simstrat/forcings/` so OpenDA gets the same perturbed inputs automatically.
- **OpenDA on Windows**: `oda_run.sh` requires WSL. `backends/openda.py` should
  detect the platform and call `oda_run.sh` via WSL or `od.bat` on Windows CMD.
- **`EnKFdiagnostics.py`**: post-processing, not part of the run loop. Belongs
  in an `analysis/` folder.
- **`e0_runner.py`**: imports from `main_PF` (old script). Needs to be updated to import from the new `model/runner.py` once that exists.
- **σ_obs alignment**: Python uses `SIGMA_OBS = 0.4` °C; OpenDA XML uses `standardDeviation="0.5"`. Decide the canonical value and store it in `static/lake_da.json`; `ensemble/forcing.py` generates both Python config and a tool to patch `timeSeriesFormatter.xml` before each OpenDA run.

---

## 11. Specific code considerations

This section maps concrete current code to the target structure, function by
function, so that each refactoring step has a clear starting point.

### 11.1 Forcing perturbation — merge `ensembles.py` + `ensembles_fromstandard.py` → `ensemble/forcing.py`

The two scripts are structurally identical. The only difference is where the
base signal comes from:

| Script | Base signal |
|---|---|
| `ensembles.py` | observation CSV (`T_obs`, `U_obs`, `V_obs`, `GLOB_obs`) |
| `ensembles_fromstandard.py` | standard `Forcing.dat` (`U_std`, `V_std`, `GLOB_std`) |

The AR(1) core is **verbatim copy-paste** in both files:

- `fit_ar1()` — `ensembles.py:83–89` ≡ `ensembles_fromstandard.py:76–82`
- `simulate_ar1()` — `ensembles.py:93–98` ≡ `ensembles_fromstandard.py:83–87`

Target: a single `generate_ensemble(base_source, lake, n_members, rng_seed)` in
`ensemble/forcing.py` where `base_source` is `"obs_csv"` or `"standard_dat"`.
`fit_ar1` and `simulate_ar1` become module-level functions shared by both paths.

The function must write to **two output locations**:
1. `assimilation/{lake}/ensembleN/Forcing.dat` — consumed by Python backends
2. `OpenDA_Simstrat/forcings/Forcing_N.dat` — consumed by `simstrat_wrapper_enkf.py:step 4`

Currently the second location is filled manually. Automating it removes the
silent divergence risk between Python and OpenDA ensemble inputs.

### 11.2 Container management — extract to `model/runner.py`

`_start_containers`, `_stop_containers`, and `_run_one_window` (with its helper
`_run_window_parallel`) are **identical** in `main_EnKF.py` and `main_PF_fast.py`
with only `CONTAINER_TAG`, `PAR_FILE`, and `RESULTS_DIR` differing:

| Function | `main_EnKF.py` lines | `main_PF_fast.py` lines |
|---|---|---|
| `_container_name` | 88–89 | 93–94 |
| `_start_containers` | 92–113 | 96–122 |
| `_stop_containers` | 116–124 | 125–134 |
| `_run_one_window` | 141–167 | — (similar, check lines ~155–185) |
| `_run_window_parallel` | 170–181 | — |

Target: `model/runner.py` with a `SimstratRunner` class or parameterised
functions that accept `container_tag`, `par_file`, and `results_subdir`. Both
`main_EnKF.py` and `main_PF_fast.py` are reduced to calling into this module.

Note: `_init_enkf_par` (`main_EnKF.py:129–138`) and `_init_pf_par`
(`main_PF_fast.py:139–150`) are also near-identical — both copy `Settings.par`,
set `Output.Path`, and write a new file. Merge into a single
`init_par(ensemble_dir, results_subdir, par_filename)` in `model/runner.py`.

### 11.3 Observation loading — extract to `io/observations.py`

`_load_obs` and `_window_obs_vector` in `main_EnKF.py` (lines 186–213) are
either identical or functionally equivalent to their counterparts in
`main_PF_fast.py`. Both read the same CSV format, hourly-average by depth, and
window-filter by date.

Target: `io/observations.py` with `load_obs(path)` and
`window_obs_vector(obs_df, window_start, window_end, depth_map)`. The `depth_map`
parameter replaces the module-level `OBS_TO_SIM_DEPTH` dict, which is a per-lake
config value, not a constant.

### 11.4 DA algorithm — extract to `backends/`

The two Python backends have fundamentally different internal approaches:
EnKF works on in-memory numpy arrays; the PF works on output files. A
two-level class hierarchy handles this cleanly:

```
BaseFilter          ← interface seen by EnsembleDA (all Python filters)
├── BaseKalmanFilter  ← shared snapshot read → math → write plumbing
│   ├── EnKF          ← stochastic Kalman math  (current only implementation)
│   └── DEnKF         ← deterministic variant   (example future extension)
└── ParticleFilter    ← file-based scoring + snapshot copy (no array math)
```

`BaseKalmanFilter.update()` owns the I/O plumbing shared by all array-based
filters — read snapshots → build H → call `_compute_analysis` → write snapshots.
Only `_compute_analysis` is abstract, so adding DEnKF later means writing only
the math, not re-implementing the snapshot read/write.

`ParticleFilter` skips `BaseKalmanFilter` entirely and implements `BaseFilter`
directly, because it never builds an `X_f` matrix.

```python
# backends/base.py
class BaseFilter(ABC):
    @abstractmethod
    def update(self, ensemble_dirs, obs_window, config) -> dict:
        """Update ensemble state in-place. Returns diagnostics."""
        ...

class BaseKalmanFilter(BaseFilter):
    def update(self, ensemble_dirs, obs_window, config):
        X_f, z_vol, lake_level = self._read_ensemble(ensemble_dirs)
        H    = build_H(z_vol, lake_level, obs_window)
        X_a, diags = self._compute_analysis(X_f, H, obs_window.to_array(), config)
        self._write_ensemble(ensemble_dirs, X_a)
        return diags

    @abstractmethod
    def _compute_analysis(self, X_f, H, y_obs, config) -> tuple[np.ndarray, dict]:
        ...
```

**EnKF** (`main_EnKF.py:282–379`):

- `_build_H(z_volume, lake_level, sim_depths)` (`main_EnKF.py:264–277`) —
  maps obs depths to model grid indices. Belongs in `io/observations.py`
  (observation-side logic) and is called from `BaseKalmanFilter.update()`.
- `_enkf_update(X_f, y_obs, H, sigma_obs, inflation, rng)` — pure numpy.
  Becomes `EnKF._compute_analysis()` in `backends/enkf.py`.
- The diagnostics dict (`main_EnKF.py:551–591`) drives three CSV outputs
  (innovation, Kalman gain by depth, summary stats). This should move into
  `EnKF._compute_analysis()` return value or a companion helper, not stay
  inline in the main loop.

**Particle filter** (`main_PF_fast.py`):

- RMSE scoring and best-member selection operate on `T_out.dat` files — the
  PF never builds `X_f`. `class ParticleFilter(BaseFilter)` in
  `backends/particle_filter.py` implements `update()` directly as:
  score files → find best member → copy snapshot.

**DEnKF** (example future extension, currently explored via OpenDA):

- Differs from EnKF only in `_compute_analysis` (no observation perturbations).
  Adding it means creating `backends/denkf.py` with `class DEnKF(BaseKalmanFilter)`
  and implementing `_compute_analysis` — no other changes needed.

### 11.5 Output accumulation — `_append_rows` + `_accumulate_mean`

`_append_rows` (`main_EnKF.py:384–407`) and `_accumulate_mean`
(`main_EnKF.py:410–437`) are output utilities that append per-window results
to growing trajectory files. A parallel pattern exists in `main_PF_fast.py`.

These do not belong in the filter backends (pure math) or in the runner
(Docker management). They should live in `io/output.py` as standalone functions,
called by `EnsembleDA.process()` after each window.

### 11.6 OpenDA wrapper — `simstrat_wrapper_enkf.py` stays, three things change

The OpenDA wrapper (`OpenDA_Simstrat/stochModel/bin/simstrat_wrapper_enkf.py`)
does not move. But three things need attention:

1. **Forcing injection path** (step 4, lines 186–195): currently reads from
   `OpenDA_Simstrat/forcings/Forcing_N.dat`. Once `ensemble/forcing.py` writes
   there automatically this step requires no change. If the path is hard-coded
   relative to the exercise directory, verify it still resolves correctly when
   `ensemble/forcing.py` writes the files.

2. **`snapshot_io` import path** (lines 36–40): currently navigates up four
   directory levels to find `snapshot/snapshot_io.py`. Once `snapshot_io.py`
   moves to `io/snapshot_io.py` inside the package, this relative path must be
   updated. The simplest fix is to add the package root to `sys.path` using an
   environment variable set by `backends/openda.py` before launching the OpenDA
   subprocess.

3. **`temperature_state.txt` vs direct snapshot injection**: the wrapper uses
   a text file as an intermediate state carrier between OpenDA analysis steps.
   This is the OpenDA-side equivalent of `_write_T_to_snap()` in `main_EnKF.py`.
   The mechanism is different by necessity (OpenDA manages the cycle, not Python)
   and should remain as-is.
