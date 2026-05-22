# alplakes-da — Code Architecture Plan

> Starting-point document for a module refactor. Written against the current
> codebase (May 2026). The goal is not to rewrite everything at once, but to
> identify the structural problems and agree on a target shape before touching
> anything.

---

## 1. What the project currently does (brief)

The module runs **ensemble-based data assimilation** for Swiss lake temperature
profiles. The model is Simstrat (Fortran), run inside Docker containers. Two
filter algorithms exist:

| Script | Filter | Lake (current) |
|---|---|---|
| `src/main_EnKF.py` | Ensemble Kalman Filter | upperlugano |
| `src/main_PF_fast.py` | Particle Filter | geneva |
| `src/main_PF_resampling.py` | Particle Filter (resampling) | — |

A shared utility (`snapshot/snapshot_io.py`) reads and writes the Simstrat
Fortran binary state files.

---

## 2. The main structural problems

### 2.1 Duplicated infrastructure code

`main_EnKF.py` and `main_PF_fast.py` contain **nearly identical copies** of the
following logic:

- `_container_name(i)` — identical
- `_start_containers()` — 95% identical (only difference: EnKF includes member 0)
- `_stop_containers()` — identical
- `_run_one_window(i, start, end)` — identical structure (patch `.par` dates →
  `docker exec` → return code)
- `_run_window_parallel(start, end)` — identical
- Snapshot bootstrapping logic (find latest dated snapshot → copy to `Results/`)

**Problem:** a bug fix or improvement to any of these must be applied manually in
every copy. This has already caused the two scripts to diverge slightly (e.g.
`_start_containers` differs on which member range is started).

### 2.2 Configuration is hardcoded inside scripts

At the top of each `main_*.py` there is a block of constants:

```python
LAKE             = "upperlugano"
N_MEMBERS        = 20
SIGMA_OBS        = 0.4
INFLATION        = 1.05
OBS_PATH         = os.path.join(ROOT, "data", "filtered_upperlugano.csv")
ENSEMBLE_BASE    = os.path.join(ROOT, "assimilation", LAKE)
...
```

To run on a different lake, you open the script and edit these values by hand.
There is no record of which values were used for which run, and it is easy to
accidentally leave the wrong lake name in.

### 2.3 The filter math is buried inside the main scripts

The actual Kalman gain computation and the particle filter scoring are mixed with
Docker orchestration, file I/O, and output writing inside one large script. This
makes it hard to:
- test the math independently
- reuse the same algorithm with a different model (e.g. not Simstrat)
- understand the algorithm by reading the code

### 2.4 Dead code creates noise

Several folders exist that contain old or unused code:

| Folder / file | Status |
|---|---|
| `src/old/` | Old versions, superseded |
| `src/old_mains/` | Old main scripts |
| `src/old_analyze/` | Old analysis scripts |
| `src/functions/unused_currently/` | Utilities not called by any current script |

These are not deleted because they feel like a backup. They are not a backup —
`git` is the backup. Keeping them makes it hard to know what is actually used.

### 2.5 No clear entry point

To run an experiment you open a script, edit constants at the top, and run the
whole file. There is no command-line interface, no argument parsing, and no way
to run the same code with different parameters without editing source files.

---

## 3. Proposed target structure

The idea is to separate four concerns that are currently mixed together:

```
alplakes_da/
│
├── config/                  ← one file per lake, filter params live here
│   ├── upperlugano.yaml
│   ├── geneva.yaml
│   └── murten.yaml
│
├── model/                   ← everything about running Simstrat
│   ├── runner.py            ← container start/stop/exec (shared by EnKF and PF)
│   └── ensemble.py          ← ensemble directory setup, snapshot bootstrapping,
│                               .par file initialization
│
├── filters/                 ← the DA algorithms (math only, no Docker/file I/O)
│   ├── enkf.py              ← Kalman gain, analysis update, inflation
│   └── particle_filter.py   ← RMSE scoring, resampling / best-member copy
│
├── io/                      ← all file reading and writing
│   ├── observations.py      ← load and preprocess observation CSVs
│   └── snapshot_io.py       ← move here from snapshot/ (already well-isolated)
│
├── main_enkf.py             ← thin: load config → call model → call filter → save
├── main_pf.py               ← thin: same pattern
│
└── cli.py                   ← optional: argparse entry point
```

Each layer only talks to the layer below it:

```
cli / main scripts
      │
      ▼
   filters/              (math: arrays in, arrays out)
      │
      ▼
   model/                (Docker orchestration)
      │
      ▼
   io/                   (file reading/writing)
      │
      ▼
   config/               (constants per lake)
```

---

## 4. What changes, piece by piece

### 4.1 `model/runner.py` — extract shared Docker code

Take the four functions that are duplicated between `main_EnKF.py` and
`main_PF_fast.py` and put them in one place:

```python
# model/runner.py

def container_name(tag: str, member: int) -> str: ...

def start_containers(
    ensemble_base: str, tag: str, n_members: int,
    simstrat_version: str, include_member_zero: bool = False
) -> None: ...

def stop_containers(tag: str, n_members: int, ...) -> None: ...

def run_window_parallel(
    member_range, window_start, window_end, ...
) -> list[int]: ...   # returns list of failed member indices
```

Both `main_enkf.py` and `main_pf.py` import from here. A bug fix in
`start_containers` is fixed once and both algorithms benefit.

### 4.2 `config/upperlugano.yaml` — centralise per-lake constants

Instead of editing Python source, you edit a YAML file:

```yaml
# config/upperlugano.yaml
lake: upperlugano
n_members: 20
simstrat_version: "3.0.4"
ensemble_base: assimilation/upperlugano
obs_file: data/filtered_upperlugano.csv
obs_depths: [0.5]
obs_to_sim_depth: {0.5: 0}

enkf:
  sigma_obs: 0.4
  inflation: 1.05
  results_dir: Results_EnKF_filtered
  par_file: Settings_EnKF_filtered.par
  container_tag: enkf_filt

particle_filter:
  results_dir: Results_PF_filtered
  par_file: Settings_PF_filtered.par
  container_tag: pf_filt
```

The main script loads this once at startup. You never edit Python to change
which lake or which parameters to use.

### 4.3 `filters/enkf.py` — isolate the math

The Kalman gain computation currently lives in the middle of `main_EnKF.py`
mixed with file I/O. It should be a pure function:

```python
# filters/enkf.py

def enkf_analysis(
    X_f: np.ndarray,      # (n_cells, N_members) forecast ensemble
    y_obs: np.ndarray,    # (n_obs,) observation vector
    H: np.ndarray,        # (n_obs, n_cells) observation operator
    sigma_obs: float,
    inflation: float,
) -> np.ndarray:          # (n_cells, N_members) analysis ensemble
    ...
```

This function takes arrays in and returns arrays. It has no knowledge of Docker,
file paths, or lake names. It is easy to test independently and easy to reuse.

### 4.4 `filters/particle_filter.py` — same idea for PF

```python
# filters/particle_filter.py

def score_members(
    T_out_files: list[str],
    obs: pd.DataFrame,
    window_start, window_end,
    obs_to_sim_depth: dict,
) -> np.ndarray:   # (N_members,) RMSE scores
    ...

def best_member_index(scores: np.ndarray) -> int: ...
```

### 4.5 `main_enkf.py` becomes a thin orchestrator

After the refactor, the main script is short and readable:

```python
# main_enkf.py  (sketch)

config = load_config("config/upperlugano.yaml")
obs    = load_observations(config.obs_file, config.obs_depths)

start_containers(config, include_member_zero=True)
try:
    for day in date_range(config.start_date, config.end_date):
        run_window_parallel(config, day, day + timedelta(days=1))

        if has_obs(obs, day):
            X_f = read_ensemble_state(config)
            y   = obs_vector(obs, day)
            X_a = enkf_analysis(X_f, y, H, config.enkf.sigma_obs, config.enkf.inflation)
            write_ensemble_state(config, X_a)

        accumulate_output(config, day)
finally:
    stop_containers(config)
```

### 4.6 Clean up dead code

Delete the following (everything is recoverable from git):

- `src/old/`
- `src/old_mains/`
- `src/old_analyze/`
- `src/functions/unused_currently/`

Move `snapshot/snapshot_io.py` into `alplakes_da/io/snapshot_io.py` since it is
a core utility, not a standalone tool. Keep `snapshot/README.md` and the example
scripts there for reference.

---

## 5. What stays the same

- `snapshot_io.py` internals — already well-isolated, no changes needed to the
  read/write logic
- `src/functions/par.py → overwrite_par_file_dates()` — keep, just move it into
  `model/ensemble.py` or `io/`
- The Simstrat Docker image and volume-mount approach
- The `prep_reanalysis/` pipeline — it is already reasonably structured and
  separate from the DA logic; leave it alone for now
- `src/adaptive_filter_general.py` — keep as-is, it is used as a preprocessing
  step before `main_EnKF.py`

---

## 6. Suggested order of work

Do not try to refactor everything at once. A safe order:

1. **Extract `model/runner.py`** — copy the shared Docker functions out, update
   both mains to import from there. No logic changes, easy to verify.

2. **Add `config/` YAML files** — add config loading to one main at a time.
   Verify the run produces the same results.

3. **Extract `filters/enkf.py`** — pull out the Kalman gain math. Write a small
   unit test against known inputs.

4. **Extract `filters/particle_filter.py`** — same idea.

5. **Delete dead code** — once the above are stable.

6. **CLI entry point** — optional, adds convenience but is lowest priority.

---

## 7. Open questions

These need a decision before or during the refactor:

- **Is `main_PF_resampling.py` still used?** If not, archive it alongside the
  old scripts.
- **How should multi-lake runs be handled?** Run the script once per lake (simple)
  or one run that iterates over lakes (complex)? The YAML approach supports both.
- **Where does `ensembles.py` fit?** It is a data preparation script (AR model
  for ensemble forcings), not an algorithm. It should probably live in
  `prep_reanalysis/` or a `setup/` folder.
- **Where does `EnKFdiagnostics.py` fit?** It is analysis/post-processing, not
  part of the run loop. Could live in `analysis/` alongside the lake-specific
  analysis notebooks.
