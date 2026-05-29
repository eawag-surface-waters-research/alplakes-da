import os
import shutil
import subprocess
import concurrent.futures
import traceback
import numpy as np
import pandas as pd
from datetime import datetime


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


def obs_to_sim_col(depth, min_obs_depth):
    return 0.0 if depth == min_obs_depth else -depth


def append_rows(src_path, dst_path):
    if not os.path.exists(src_path):
        return
    with open(src_path) as f:
        lines = f.readlines()
    header, rows = lines[0], lines[1:]
    if not rows:
        return
    if not os.path.exists(dst_path):
        with open(dst_path, "w") as f:
            f.writelines([header] + rows)
        return
    with open(dst_path, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(rows[0].split(",")[0])
    start = 1 if first_t <= last_t else 0
    with open(dst_path, "a") as f:
        f.writelines(rows[start:])


def accumulate_mean(member_ids, args):
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
    mean_df  = frames[0].copy()
    num_cols = mean_df.columns[1:]
    mean_df[num_cols] = np.mean([f[num_cols].values for f in frames], axis=0)
    dst = args["mean_traj_path"]
    if not os.path.exists(dst):
        mean_df.to_csv(dst, index=False)
        return
    with open(dst, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(mean_df.iloc[0, 0])
    start   = 1 if first_t <= last_t else 0
    mean_df.iloc[start:].to_csv(dst, mode="a", index=False, header=False)


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
    from .simstrat import init_par, overwrite_par_dates

    ensemble_dir = os.path.join(args["ensemble_base"], f"ensemble{i}")
    results_dir  = os.path.join(ensemble_dir, args["results_dir"])
    os.makedirs(results_dir, exist_ok=True)

    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))

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
