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

## 2. The five components every backend needs

Every DA experiment, regardless of backend, requires exactly five things:

| Component | What it does |
|---|---|
| **1. Model runner** | Starts N Simstrat instances, runs each one for a time window, stops them |
| **2. Observations** | Loads measured temperatures, specifies which depth, which time, how much to trust them |
| **3. State exchange** | Reads model temperature state before the DA update; writes corrected state back |
| **4. Algorithm config** | Ensemble size, observation error, how often to update, which filter to use |
| **5. Output** | Where results are written and in what format |

The table below shows where each component currently lives for each backend:

| Component | Backend A (Python EnKF) | Backend B (Python PF) | Backend C (OpenDA EnKF) |
|---|---|---|---|
| **1. Model runner** | `_start/stop_containers()` + `_run_one_window()` in `main_EnKF.py` | same functions copy-pasted in `main_PF_fast.py` | `parallel_enkf.xml` + `simstratWrapperEnKF.xml` + `simstrat_wrapper_enkf.py` |
| **2. Observations** | `_load_obs()` in `main_EnKF.py` | `_load_obs()` in `main_PF_fast.py` (identical) | `stochObserver/timeSeriesFormatter.xml` + `T_*m_real.csv` files |
| **3. State exchange** | `snapshot_io.py` (read + write) | file copy only (`shutil.copy2`) | `simstratStochModelEnKF.xml` declares state vector; `snapshot_io.py` (via wrapper) does the actual I/O |
| **4. Algorithm config** | constants at top of `main_EnKF.py` (`SIGMA_OBS`, `INFLATION`, `N_MEMBERS`) | constants at top of `main_PF_fast.py` | `algorithms/EnKF.xml` (ensemble size, analysis times) + `timeSeriesFormatter.xml` (σ per depth) |
| **5. Output** | `T_out_enkf_filtered_mean.dat` + diagnostic CSVs in `assimilation/upperlugano/` | `T_out_ens_filtered.dat` in `assimilation/geneva/` | `enkf_results.py` in `Results_AssimilationExp/` + `T_out.dat` per member in `work_enkf/` |

**The problem made visible:** Components 1 and 2 are copy-pasted between
Backends A and B. Component 4 is scattered across the top of two Python files
in one case, and across three XML files in another. There is no common entry
point or shared config format.

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
The only file genuinely shared between both worlds is `io/snapshot_io.py`.

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
│       ├── enkf.py                     ← Component 4 for Backend A
│       │                                 Kalman gain + state update (pure math)
│       ├── particle_filter.py          ← Component 4 for Backend B
│       │                                 RMSE scoring + best-member copy
│       └── openda.py                   ← bridge to Backend C
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
| **1. Model runner** | `model/runner.py` | `model/runner.py` | `parallel_enkf.xml` → `simstratWrapperEnKF.xml` → `simstrat_wrapper_enkf.py` |
| **2. Observations** | `io/observations.py` | `io/observations.py` | `stochObserver/timeSeriesFormatter.xml` + CSV files |
| **3. State exchange** | `io/snapshot_io.py` (read + write) | file copy only | `simstratStochModelEnKF.xml` + `io/snapshot_io.py` via wrapper |
| **4. Algorithm config** | `args/enkf.json` + `static/lake_da.json` | `args/pf.json` + `static/lake_da.json` | `algorithms/EnKF.xml` + σ in `timeSeriesFormatter.xml` |
| **5. Output** | `assimilation/upperlugano/T_out_enkf_*.dat` + diagnostic CSVs | `assimilation/geneva/T_out_ens_*.dat` | `Results_AssimilationExp/enkf_results.py` + `work_enkf/workN/Results/T_out.dat` |

`io/snapshot_io.py` is the one file physically shared: imported by the Python
EnKF backend directly, and imported by `simstrat_wrapper_enkf.py` in the OpenDA
chain.

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
- **`ensembles.py`**: generates perturbed forcings (data prep, not DA). Move to
  `prep_reanalysis/` or a `setup/` folder.
- **OpenDA on Windows**: `oda_run.sh` requires WSL. `backends/openda.py` should
  detect the platform and call `oda_run.sh` via WSL or `od.bat` on Windows CMD.
- **`EnKFdiagnostics.py`**: post-processing, not part of the run loop. Belongs
  in an `analysis/` folder.
