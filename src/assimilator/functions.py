import os
import json
import traceback
import pandas as pd
from datetime import datetime, timezone

# Repo paths, from this file at src/assimilator/functions.py
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # …/src
ROOT    = os.path.dirname(SRC_DIR)                                      # …/alplakes-da

# General config (Simstrat epoch, forcing format, ICON acquisition) — see static/general.json.
# Loaded at import; the file is committed, so every module that imports functions gets these.
with open(os.path.join(ROOT, "static", "general.json"), encoding="utf-8") as _f:
    GENERAL = json.load(_f)
SIMSTRAT_REF_YEAR = GENERAL["simstrat_ref_year"]
FORCING_HEADER    = GENERAL["forcing_header"]
API_BASE          = GENERAL["icon_api_base"]
VARIABLES         = GENERAL["icon_variables"]

# Model-specific behaviour (Docker run, Settings.par editing, snapshot I/O, z_out/T_out formats,
# input layout) lives in assimilator.models.<model>; this module keeps only generic, model-agnostic
# helpers shared across the pipeline.

# ---------------------------------------------------------------------------
# Path / config helpers
# ---------------------------------------------------------------------------

def resolve_src(path):
    """Resolve a possibly-relative ensemble_base ('../run/<lake>') against src/."""
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(SRC_DIR, path))


def resolve_root(path):
    """Resolve a possibly-relative repo path ('openda_simstrat', 'args/x.json') against ROOT."""
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(ROOT, path))


def load_json(path):
    """Load a config JSON, trying the path as given then under ROOT."""
    p = path if os.path.isfile(path) else resolve_root(path)
    if not os.path.isfile(p):
        raise FileNotFoundError(f"args file not found: {path}")
    with open(p) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------
class Logger:
    def __init__(self, path=False):
        self.path = path
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def info(self, string, indent=0):
        out = datetime.now().strftime("%H:%M:%S") + "   " * (indent + 1) + string
        print(out)
        self._write(out)

    def warning(self, string):
        out = datetime.now().strftime("%H:%M:%S") + "   WARNING: " + string
        print("\033[93m" + out + "\033[0m")
        self._write(out)

    def error(self):
        out = datetime.now().strftime("%H:%M:%S") + "   ERROR"
        print("\033[91m" + out + "\033[0m")
        if self.path:
            with open(self.path, "a") as f:
                f.write(out + "\n")
                traceback.print_exc(file=f)

    def initialise(self, string):
        out = "****** " + string + " " + datetime.now().strftime("%H:%M:%S %d.%m.%Y") + " ******"
        print("\033[1m" + out + "\033[0m")
        self._write(out)

    def end(self, string):
        out = "****** " + string + " ******"
        print("\033[92m" + out + "\033[0m")
        self._write(out)

    def newline(self):
        print("")
        self._write("")

    def _write(self, out):
        if self.path:
            with open(self.path, "a") as f:
                f.write(out + "\n")


def verify_args(args, required):
    for key in required:
        if key not in args:
            raise ValueError(f"Required argument '{key}' missing from args file.")


def verify_file(path):
    if os.path.isfile(path):
        return os.path.abspath(path)
    raise ValueError(f"File not found: {os.path.abspath(path)}")


def discover_n_members(ensemble_base):
    return len([
        d for d in os.listdir(ensemble_base)
        if d.startswith("ensemble") and d != "ensemble0"
        and os.path.isdir(os.path.join(ensemble_base, d))
    ])


# ---------------------------------------------------------------------------
# Observations (model-agnostic: read the obs CSV, map depths, filter to model grid)
# ---------------------------------------------------------------------------

# Hourly mean, centered on the label: the value at HH:00 is the mean of samples in
# [HH-30min, HH+30min), computed by flooring (time + 30min) to the hour. Centering aligns the
# obs with Simstrat's instantaneous hourly output, so the noon assimilation pairs the noon obs
# with the noon state. Labels stay on the hour, so the PF's obs<->T_out time intersection
# (rmse_in_window) is unaffected.
def load_obs(obs_path):
    obs = pd.read_csv(obs_path, parse_dates=["time"])
    obs["time"] = pd.to_datetime(obs["time"], utc=True)
    obs["time"] = (obs["time"] + pd.Timedelta(minutes=30)).dt.floor("1h")
    obs = obs.groupby(["depth", "time"])["value"].mean().reset_index()
    return obs


# Depth convention: an obs "X metres below the surface" maps to model column height -X
# (negative = below surface). No surface snapping — obs depths with no matching model-output
# depth are dropped upstream (filter_obs_to_model_depths), so the native and OpenDA engines
# assimilate the identical depth set.
def obs_to_sim_col(depth):
    return -depth


def filter_obs_to_model_depths(obs_df, model_depths, log=None):
    """Drop obs whose depth has no matching model-output depth (abs diff <= 1e-6), so the
    Python engines assimilate the same depths OpenDA does. No-op if model_depths is empty."""
    if not model_depths:
        return obs_df
    obs_depths = sorted(obs_df["depth"].unique())
    matched = {d for d in obs_depths if any(abs(d - m) <= 1e-6 for m in model_depths)}
    dropped = [d for d in obs_depths if d not in matched]
    if dropped:
        msg = (f"dropping obs depths with no matching model output depth (z_out.dat): "
               f"{[f'{d:g}' for d in dropped]} m")
        (log.info(f"  {msg}") if log is not None else print(f"[obs] {msg}"))
    return obs_df[obs_df["depth"].isin(matched)]


def to_utc(iso_str):
    """Parse an ISO date/datetime string to a tz-aware UTC datetime (assumes naive input)."""
    return datetime.fromisoformat(iso_str).replace(tzinfo=timezone.utc)


# =============================================================================
# Python engine run-arg builder (shared by run_enkf / run_pf)
# =============================================================================

def build_python_run_args(run_raw, ensemble_raw, ensemble_base, n_members, model):
    """Merge run-specific knobs with shared ensemble facts; fill defaults (obs path,
    model runtime config), set container_tag, parse UTC dates, derive ref_date (from the
    selected `model`), and (for EnKF) the diagnostics output paths."""
    args = dict(run_raw)
    args["lake"]          = ensemble_raw["lake"]
    args["ensemble_base"] = ensemble_base
    args["n_members"]     = n_members
    args["member_ids"]    = list(range(1, n_members + 1))

    args.setdefault("obs_path", os.path.join(ROOT, "observations", args["lake"], "temperature.csv"))
    for k, v in model.run_config().items():   # model's Docker/runtime defaults (fallback)
        args.setdefault(k, v)

    args["container_tag"] = args["algorithm"].lower()
    args["ref_date"]      = model.read_ref_date(ensemble_base)

    args["start_date"] = to_utc(ensemble_raw["start_date"])
    args["end_date"]   = to_utc(ensemble_raw["end_date"])

    # Observation error std lives in ensemble.json (shared single source with OpenDA, which
    # reads the same key); inflation stays per-run in enkf.json (Python-EnKF-only — OpenDA has
    # no inflation param). Carried into args here so the EnKF code reads it uniformly.
    if "sigma_obs" in ensemble_raw:
        args["sigma_obs"] = ensemble_raw["sigma_obs"]

    algo = args["algorithm"].lower()
    args.setdefault("mean_traj_path", os.path.join(ensemble_base, f"T_out_{algo}_mean.dat"))
    if args["algorithm"] == "EnKF":
        args.setdefault("diag_path",        os.path.join(ensemble_base, "enkf_diagnostics.csv"))
        args.setdefault("innov_depth_path", os.path.join(ensemble_base, "enkf_innov_by_depth.csv"))
        args.setdefault("kgain_depth_path", os.path.join(ensemble_base, "enkf_kgain_by_depth.csv"))
    return args
