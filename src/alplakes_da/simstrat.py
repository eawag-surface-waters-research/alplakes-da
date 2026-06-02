import os
import json
import sys
import pandas as pd
from datetime import datetime, timedelta, timezone


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
    with open(par_path) as f:
        par = json.load(f)
    par["Simulation"]["Start d"] = datetime_to_simstrat_time(window_start + timedelta(hours=1), ref_date)
    par["Simulation"]["End d"]   = datetime_to_simstrat_time(window_end   - timedelta(hours=1), ref_date)
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


def _snapshot_io():
    from .snapshot_io import read_snapshot, write_snapshot
    return read_snapshot, write_snapshot


def read_snapshot_T(member_id, args):
    read_snapshot, _ = _snapshot_io()
    snap_path = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["results_dir"], "simulation-snapshot.dat")
    par_path  = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["par_file"])
    snap  = read_snapshot(snap_path, par_path=par_path)
    T     = snap.model["T"]
    z_vol = snap.grid["z_volume"][-len(T):]
    return T.copy(), z_vol.copy(), float(snap.grid["lake_level"])


def write_snapshot_T(member_id, T_new, args):
    read_snapshot, write_snapshot = _snapshot_io()
    snap_path = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["results_dir"], "simulation-snapshot.dat")
    par_path  = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["par_file"])
    snap = read_snapshot(snap_path, par_path=par_path)
    snap.model["T"][:] = T_new
    tmp = snap_path + ".tmp"
    write_snapshot(tmp, snap)
    os.replace(tmp, snap_path)
