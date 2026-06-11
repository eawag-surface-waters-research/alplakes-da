import os
import glob
import json
import shutil
import subprocess
import concurrent.futures
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

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

# ---------------------------------------------------------------------------
# Path / config / pipeline-availability helpers
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


def standard_inputs_ready(standard_inputs):
    """True if a dated simulation-snapshot_*.dat and Forcing.dat exist (step 1 precondition)."""
    return (bool(glob.glob(os.path.join(standard_inputs, "simulation-snapshot_*.dat")))
            and os.path.isfile(os.path.join(standard_inputs, "Forcing.dat")))


def instances_ready(ensemble_base, n_members):
    """True if every ensemble{0..N}/Settings.par exists (step 2 done)."""
    return all(os.path.isfile(os.path.join(ensemble_base, f"ensemble{i}", "Settings.par"))
               for i in range(n_members + 1))


# Heavy spin-up output each member regenerates; skip to avoid copying GBs per dir.
COPY_DEFAULT_SKIP = {"Results", "ref"}


def _copy_dir(src_dir, dst_dir, skip=None):
    """Copy files/subdirs from src_dir into dst_dir (overwriting), skipping names in
    `skip`. Does not wipe dst_dir, so unrelated outputs are preserved."""
    os.makedirs(dst_dir, exist_ok=True)
    for fname in os.listdir(src_dir):
        if skip and fname in skip:
            continue
        src = os.path.join(src_dir, fname)
        dst = os.path.join(dst_dir, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)


def copy_standard_inputs(raw):
    """Step 2: clone inputs/<lake>/ into ensemble0..N (0 = control,
    1..N = members whose Forcing.dat perturbate overwrites later). Skips the heavy
    Results/ dir — each member regenerates it and seeds the warmup from the dated
    simulation-snapshot_*.dat that IS copied."""
    verify_args(raw, ["lake", "n_members", "ensemble_base"])

    lake          = raw["lake"]
    n_members     = raw["n_members"]
    ensemble_base = resolve_src(raw["ensemble_base"])
    standard_inputs = raw.get("standard_inputs_path")
    standard_inputs = resolve_src(standard_inputs) if standard_inputs \
        else os.path.join(ROOT, "inputs", lake)
    skip = set(raw.get("copy_skip", COPY_DEFAULT_SKIP))

    if not os.path.isdir(standard_inputs):
        raise FileNotFoundError(
            f"standard_inputs not found: {standard_inputs} "
            f"(provide it manually — the Simstrat inputs + a dated simulation-snapshot_*.dat)")

    for i in range(n_members + 1):           # 0..N : control + members
        dst = os.path.join(ensemble_base, f"ensemble{i}")
        _copy_dir(standard_inputs, dst, skip=skip)

    print(f"{lake}: copied standard_inputs -> ensemble0..{n_members} "
          f"under {ensemble_base} (skipped: {sorted(skip)})")


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


def load_obs(obs_path):
    obs = pd.read_csv(obs_path, parse_dates=["time"])
    obs["time"] = pd.to_datetime(obs["time"], utc=True)
    obs = (
        obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"]
           .mean().reset_index()
    )
    return obs


# Note: the SHALLOWEST obs depth is snapped to 0.0 (surface) regardless of its true
# depth; all others map to -depth. So a sensor at e.g. 0.5 m for upperlugano is assimilated 
# as if at the surface. Internally consistent (both EnKF build_H and PF use this, so the engines 
# agree), but it is a real depth bias if the shallowest sensor is not actually close to the surface. 
# It is intended.
def obs_to_sim_col(depth, min_obs_depth):
    return 0.0 if depth == min_obs_depth else -depth


# ---------------------------------------------------------------------------
# Per-window DA machinery (used by EnKF + PF):
# ---------------------------------------------------------------------------
def clear_member_outputs(ensemble_base, member_ids, results_dir):
    """Delete accumulated *_out.dat in each member's results_dir. Simstrat APPENDS to its
    output files across the daily windows, so a fresh run must clear them once up front,
    otherwise it would append onto stale data from a previous run. Called on reset."""
    for i in member_ids:
        rdir = os.path.join(ensemble_base, f"ensemble{i}", results_dir)
        if os.path.isdir(rdir):
            for fname in os.listdir(rdir):
                if fname.endswith("_out.dat"):
                    os.remove(os.path.join(rdir, fname))


def accumulate_mean(member_ids, args):
    """Write the ensemble-mean trajectory to args['mean_traj_path'] from each member's
    (full, accumulated) T_out.dat. One-shot: call once after the run. Averages across
    whatever members are present at each timestamp, so it tolerates a member missing a
    failed window."""
    def _read(i):
        path = os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "T_out.dat")
        if not os.path.exists(path):
            return None
        df = pd.read_csv(path)
        df.columns = [c.strip().strip('"') for c in df.columns]
        return df

    with concurrent.futures.ThreadPoolExecutor() as pool:
        frames = [f for f in pool.map(_read, member_ids) if f is not None]
    if not frames:
        return
    time_col = frames[0].columns[0]
    mean_df  = pd.concat(frames).groupby(time_col, as_index=False).mean()
    mean_df.to_csv(args["mean_traj_path"], index=False)


def _container_name(i, args):
    return f"simstrat_{args['container_tag']}_{i}"


def start_containers(args, max_workers=None):
    def _start_one(i):
        name  = _container_name(i, args)
        mount = os.path.join(args["ensemble_base"], f"ensemble{i}").replace("\\", "/")
        subprocess.run(f"docker rm -f {name}", shell=True, capture_output=True)
        cmd = (
            f"docker run -d --name {name} "
            f"-v {mount}:{args['simstrat_workdir']} "
            f"--entrypoint sleep "
            f"eawag/simstrat:{args['simstrat_version']} infinity"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ensemble{i:02d}] container start failed: {result.stderr.strip()}")
        return i, result.returncode

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(_start_one, args["member_ids"]))
    failed = [i for i, code in results if code != 0]
    if failed:
        raise RuntimeError(f"Containers failed to start for members: {failed}")
    print(f"Started {len(args['member_ids'])} persistent containers.\n")


def stop_containers(args):
    def _stop_one(i):
        name = _container_name(i, args)
        subprocess.run(f"docker stop {name}", shell=True, capture_output=True)
        subprocess.run(f"docker rm   {name}", shell=True, capture_output=True)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        list(pool.map(_stop_one, args["member_ids"]))
    print("Containers stopped and removed.")


def run_one_window(i, window_start, window_end, args):
    ensemble_dir = os.path.join(args["ensemble_base"], f"ensemble{i}")
    results_dir  = os.path.join(ensemble_dir, args["results_dir"])
    os.makedirs(results_dir, exist_ok=True)

    # Note: per-window *_out.dat are NOT cleared here. Simstrat appends across windows, so the
    # output files accumulate into the full run trajectory by themselves. They are cleared once
    # up front on reset (clear_member_outputs); a non-reset run continues by appending.

    live_snap = os.path.join(results_dir, "simulation-snapshot.dat")
    if not os.path.exists(live_snap):
        dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
        if dated:
            shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live_snap)

    init_par(ensemble_dir, args)
    overwrite_par_dates(
        os.path.join(ensemble_dir, args["par_file"]),
        window_start, window_end, args["ref_date"],
    )

    name   = _container_name(i, args)
    cmd    = f"docker exec -w {args['simstrat_workdir']} {name} {args['simstrat_binary']} {args['par_file']}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ensemble{i:02d}] FAILED  {window_start.date()}\n{result.stderr[-400:]}")
    return i, result.returncode


def run_window_parallel(window_start, window_end, args, max_workers=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_one_window, i, window_start, window_end, args): i
            for i in args["member_ids"]
        }
        failed = []
        for future in concurrent.futures.as_completed(futures):
            i, code = future.result()
            if code != 0:
                failed.append(i)
    return failed

# ---------------------------------------------------------------------------
# Small helpers for reading/writing Simstrat .par config and the per-window output.
# ---------------------------------------------------------------------------

def datetime_to_simstrat_time(dt, ref_date):
    delta = dt - ref_date
    return delta.days + delta.seconds / 86400


def read_ref_date(ensemble_base):
    par_path = os.path.join(ensemble_base, "ensemble1", "Settings.par")
    with open(par_path) as f:
        par = json.load(f)
    year = par["Simulation"]["Reference year"]
    return datetime(year, 1, 1, tzinfo=timezone.utc)


def init_par(ensemble_dir, args):
    src = os.path.join(ensemble_dir, "Settings.par")
    dst = os.path.join(ensemble_dir, args["par_file"])
    if os.path.exists(dst):
        return
    with open(src) as f:
        par = json.load(f)
    par["Output"]["Path"] = args["results_dir"]
    with open(dst, "w") as f:
        json.dump(par, f, indent=4)


def overwrite_par_dates(par_path, window_start, window_end, ref_date):
    # Run the exact [window_start, window_end] window. Consecutive windows share the boundary
    # instant: window N ends at, and writes its snapshot at, window_end; window N+1 continues
    # from that snapshot starting at the same instant. Simstrat emits its first output one
    # interval AFTER the start (not at t=start), so there is no duplicate row at the seam and
    # the stitched trajectory is continuous. (A former ±1h padding here created a 2h/window
    # simulation gap and was removed.)
    with open(par_path) as f:
        par = json.load(f)
    par["Simulation"]["Start d"] = datetime_to_simstrat_time(window_start, ref_date)
    par["Simulation"]["End d"]   = datetime_to_simstrat_time(window_end,   ref_date)
    with open(par_path, "w") as f:
        json.dump(par, f, indent=4)


def load_T(ensemble_dir, args):
    path = os.path.join(ensemble_dir, args["results_dir"], "T_out.dat")
    ref  = pd.Timestamp(args["ref_date"])
    df = pd.read_csv(path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = (ref + pd.to_timedelta(df["Datetime"], unit="D")).dt.round("1h")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df.columns = df.columns.astype(float)
    return df


# =============================================================================
# Python engine run-arg builder (shared by run_enkf / run_pf)
# =============================================================================

def build_python_run_args(run_raw, ensemble_raw, ensemble_base, n_members):
    """Merge run-specific knobs with shared ensemble facts; fill defaults (obs path,
    Simstrat version/binary/workdir), set container_tag, parse UTC dates, derive
    ref_date, and (for EnKF) the diagnostics output paths."""
    args = dict(run_raw)
    args["lake"]          = ensemble_raw["lake"]
    args["ensemble_base"] = ensemble_base
    args["n_members"]     = n_members
    args["member_ids"]    = list(range(1, n_members + 1))

    args.setdefault("obs_path", os.path.join(ROOT, "observations", args["lake"], "temperature.csv"))
    args.setdefault("simstrat_version", "3.0.4")
    args.setdefault("simstrat_binary",  "/entrypoint.sh")
    args.setdefault("simstrat_workdir", "/simstrat/run")

    args["container_tag"] = args["algorithm"].lower()
    args["ref_date"]      = read_ref_date(ensemble_base)

    tz = timezone.utc
    args["start_date"] = datetime.fromisoformat(ensemble_raw["start_date"]).replace(tzinfo=tz)
    args["end_date"]   = datetime.fromisoformat(ensemble_raw["end_date"]).replace(tzinfo=tz)

    algo = args["algorithm"].lower()
    args.setdefault("mean_traj_path", os.path.join(ensemble_base, f"T_out_{algo}_mean.dat"))
    if args["algorithm"] == "EnKF":
        args.setdefault("diag_path",        os.path.join(ensemble_base, "enkf_diagnostics.csv"))
        args.setdefault("innov_depth_path", os.path.join(ensemble_base, "enkf_innov_by_depth.csv"))
        args.setdefault("kgain_depth_path", os.path.join(ensemble_base, "enkf_kgain_by_depth.csv"))
    return args
