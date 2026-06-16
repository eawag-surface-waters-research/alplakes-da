"""All Simstrat-specific model behaviour, in one place.

Simstrat is a 1D lake model run in Docker (`eawag/simstrat:<version>`). This module
holds everything that knows about Simstrat's mechanics — Docker container lifecycle,
`Settings.par` editing, the day-since-reference-year time convention, the output
formats (`z_out.dat` / `T_out.dat`), the input layout, and the binary snapshot I/O
(in the sibling `snapshot.py`) — and exposes it through the `Model` interface as the
`Simstrat` class.  Adding another model means writing a sibling module with the same
surface and registering it in `models/__init__.py`; the engines call only the
interface, so they don't change.

The functions below keep their original signatures (taking the pipeline's `args`/`raw`
dicts) and are bound onto `Simstrat` as static methods at the bottom.
"""

import os
import glob
import json
import shutil
import subprocess
import concurrent.futures
import pandas as pd
from datetime import datetime, timezone

from ..functions import ROOT, resolve_src, verify_args
from .base import Model
from .snapshot import read_snapshot, write_snapshot


# ---------------------------------------------------------------------------
# Input readiness / instance setup
# ---------------------------------------------------------------------------

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
# Output formats (z_out.dat / T_out.dat)
# ---------------------------------------------------------------------------

def model_output_depths(ensemble_base):
    """Depths (positive metres) the model outputs, read from a member's z_out.dat.
    Mirrors openda/adapter._model_output_depths so the two engines filter obs against the
    same grid. Returns [] if the file is absent (then no depth filtering is applied)."""
    path = os.path.join(ensemble_base, "ensemble1", "z_out.dat")
    if not os.path.isfile(path):
        return []
    depths = []
    with open(path) as f:
        for line in f:
            try:
                depths.append(abs(float(line.strip())))
            except ValueError:
                continue  # header line ("Depths [m]")
    return depths


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


def load_T(ensemble_dir, args):
    path = os.path.join(ensemble_dir, args["results_dir"], "T_out.dat")
    ref  = pd.Timestamp(args["ref_date"])
    df = pd.read_csv(path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = (ref + pd.to_timedelta(df["Datetime"], unit="D")).dt.round("1h")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df.columns = df.columns.astype(float)
    return df


# ---------------------------------------------------------------------------
# Per-window run machinery (Docker container lifecycle + Settings.par dates)
# ---------------------------------------------------------------------------

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
# Time convention + Settings.par (JSON) read/write
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


# ---------------------------------------------------------------------------
# Snapshot temperature column read/write (full-grid T as the DA state)
# ---------------------------------------------------------------------------

def read_snapshot_T(member_id, args):
    """Read member `member_id`'s warmup snapshot -> (T column, z_volume, lake_level)."""
    snap_path = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["results_dir"], "simulation-snapshot.dat")
    par_path  = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["par_file"])
    snap  = read_snapshot(snap_path, par_path=par_path)
    T     = snap.model["T"]
    # VERIFIED: there is a vertical-alignment assumption. This takes the TOP len(T) cells of
    # z_volume, i.e. it assumes T is surface-aligned (z_volume[-1] == surface). If T is
    # bottom-aligned in the Fortran grid this silently maps every obs to the wrong depth.
    # Verified on inputs/upperlugano
    z_vol = snap.grid["z_volume"][-len(T):]
    return T.copy(), z_vol.copy(), float(snap.grid["lake_level"])


def write_snapshot_T(member_id, T_new, args):
    """Write the analysis temperature column back into member `member_id`'s snapshot."""
    snap_path = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["results_dir"], "simulation-snapshot.dat")
    par_path  = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["par_file"])
    snap = read_snapshot(snap_path, par_path=par_path)
    snap.model["T"][:] = T_new
    tmp = snap_path + ".tmp"
    write_snapshot(tmp, snap)
    os.replace(tmp, snap_path)


# ---------------------------------------------------------------------------
# The model: binds the functions above onto the Model interface.
# ---------------------------------------------------------------------------

class Simstrat(Model):
    """The Simstrat 1D lake model, run in Docker (eawag/simstrat:<version>)."""

    name              = "simstrat"
    image             = "eawag/simstrat"
    version           = "3.0.4"
    binary            = "/entrypoint.sh"
    workdir           = "/simstrat/run"
    snapshot_filename = "simulation-snapshot.dat"

    def run_config(self):
        """Runtime defaults the engines read (merged into the run args). Single source of
        truth for the model's Docker invocation; the OpenDA adapter also writes the image
        (eawag/simstrat:<version>) into model.json for the standalone wrapper."""
        return {
            "simstrat_version": self.version,
            "simstrat_binary":  self.binary,
            "simstrat_workdir": self.workdir,
        }

    # input readiness / setup
    standard_inputs_ready = staticmethod(standard_inputs_ready)
    instances_ready       = staticmethod(instances_ready)
    copy_standard_inputs  = staticmethod(copy_standard_inputs)
    # per-window run machinery
    start_containers      = staticmethod(start_containers)
    stop_containers       = staticmethod(stop_containers)
    run_window            = staticmethod(run_window_parallel)
    # state / output IO
    read_ref_date         = staticmethod(read_ref_date)
    model_output_depths   = staticmethod(model_output_depths)
    load_T                = staticmethod(load_T)
    clear_member_outputs  = staticmethod(clear_member_outputs)
    accumulate_mean       = staticmethod(accumulate_mean)
    read_snapshot_T       = staticmethod(read_snapshot_T)
    write_snapshot_T      = staticmethod(write_snapshot_T)
