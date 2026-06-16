"""Export framework outputs into the standalone openda_simstrat/ layout.

Replaces openda_simstrat/generate_ensemble_forcings.py, generate_warmup_snapshot.py
and prepare_real_obs.py: instead of regenerating perturbed forcings (its own AR(1)),
a separate spin-up snapshot, and the observation CSVs by hand, this COPIES the Python
framework's already-generated inputs into OpenDA's layout and builds the stochObserver
observation files in one step.  Result: the OpenDA EnKF reference runs on byte-identical
forcings + warmup as the Python EnKF, so the cross-validation is rigorous, with no
duplicated generation.

Syncs:
  inputs/<lake>/*               (except OpenDA coupling files + Results/ + dated snapshots)
      -> openda_simstrat/stochModel/template/*                                 (Bathymetry, Grid, Settings.par,
                                                                                Absorption, Qin/Qout/Sin/Tin,
                                                                                InitialConditions, aed2.nml, AED2_*, ...)
  run/<lake>/ensemble{i}/Forcing.dat
      -> openda_simstrat/forcings/Forcing_{i}.dat                              (i = 0..N; 0 = control)
  inputs/<lake>/simulation-snapshot_<date>.dat
      -> openda_simstrat/stochModel/template/Results/simulation-snapshot.dat   (the warmup OpenDA reads)

Builds (formerly prepare_real_obs.py):
  observations/<lake>/temperature.csv  (raw 10-min profile observations; override with "obs_csv")
      -> openda_simstrat/stochObserver/T_{depth}m_real.csv                     (one reading/day nearest noon UTC,
                                                                                time in fractional Simstrat days)

OpenDA-specific coupling files in the template are NEVER overwritten:
  temperature_state.txt, time_control.yaml, timeSeriesFormatter.xml.

OpenDA reads the warmup from template/Results/simulation-snapshot.dat (cloned into
each work dir; Simstrat "Continue from last snapshot" reads it).  The dated
simulation-snapshot_*.dat at the template ROOT is only an archive for diagnostics
and is left untouched.

OpenDA's XML configs / wrappers are left untouched (this only writes data files).
Prerequisite: run main.py (its copy + perturbate steps) first so the
ensemble Forcing.dat files exist.

Usage:  python src/assimilator/openda/adapter.py args/ensemble.json [--dry-run]
"""

import os
import sys
import csv
import glob
import json
import shutil
import argparse
from collections import defaultdict
from datetime import date, datetime, timezone

# this file lives at src/assimilator/openda/adapter.py
SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # src/
ROOT    = os.path.dirname(SRC_DIR)                                                       # repo root
sys.path.insert(0, SRC_DIR)

import subprocess

from assimilator.functions import verify_args, resolve_src, resolve_root, SIMSTRAT_REF_YEAR
from assimilator.models.snapshot import read_snapshot
from assimilator.summarize import report_summary
from .config import FILTERS, render as render_oda

REQUIRED = ["lake", "n_members", "ensemble_base"]

# Black-box coupling files OpenDA owns — never overwrite these in the template.
OPENDA_SPECIFIC = {"temperature_state.txt", "time_control.yaml", "timeSeriesFormatter.xml"}

# Observations: each day, keep the single reading nearest this UTC hour (noon snapshot).
OBS_TARGET_HOUR = 12

# The only hand-maintained OpenDA pieces (everything else in openda_simstrat/ is
# generated/synced). Copied into the working dir at adapt time so the working dir
# stays fully reproducible from static/openda/.
STATIC_OPENDA = os.path.join(ROOT, "static", "openda")


def _copy(src, dst, dry_run):
    if dry_run:
        print(f"  [dry-run] {os.path.relpath(src, ROOT)} -> {os.path.relpath(dst, ROOT)}")
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def _copy_path(src, dst, dry_run):
    """Copy a file or a directory (dirs replaced wholesale)."""
    if dry_run:
        kind = "dir " if os.path.isdir(src) else "file"
        print(f"  [dry-run] ({kind}) {os.path.relpath(src, ROOT)} -> {os.path.relpath(dst, ROOT)}")
        return
    if os.path.isdir(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def _noon_simstrat_day(day_str, ref_date):
    """Fractional Simstrat day at noon (integer day + 0.5) for a YYYY-MM-DD string."""
    return (date.fromisoformat(day_str) - ref_date).days + 0.5


def _utc_minutes_since_midnight(iso_str):
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.hour * 60 + dt.minute + dt.second / 60.0


def _model_output_depths(inputs_dir):
    """Depths (positive metres) the model outputs, read from <inputs_dir>/z_out.dat. Reads the
    canonical source (standard_inputs) rather than the template copy, so it also works under
    --dry-run (when the template isn't populated). Returns [] if absent (no depth filtering)."""
    path = os.path.join(inputs_dir, "z_out.dat")
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


def _build_observations(raw, openda_dir, standard_inputs, dry_run):
    """Build the OpenDA stochObserver obs files from the raw profile CSV.

    For each depth/day, writes the mean of samples in the centered noon hour [11:30, 12:30) to
    stochObserver/T_{depth}m_real.csv (time in fractional Simstrat days since 1 Jan
    SIMSTRAT_REF_YEAR), mirroring functions.load_obs so OpenDA and the native engines assimilate
    identical obs. Depths are auto-detected from the CSV, dropped if they have fewer than
    `obs_min_days` days or no matching model-output depth (standard_inputs/z_out.dat), and
    returned sorted for the config generator to wire everywhere.
    """
    lake      = raw["lake"]
    stoch_dir = os.path.join(openda_dir, "stochObserver")
    obs_csv   = resolve_src(raw["obs_csv"]) if raw.get("obs_csv") \
        else os.path.join(ROOT, "observations", lake, "temperature.csv")
    if not os.path.isfile(obs_csv):
        raise FileNotFoundError(
            f"observation source not found: {obs_csv} (set 'obs_csv' or add observations/{lake}/temperature.csv)")

    ref_date     = date(SIMSTRAT_REF_YEAR, 1, 1)
    start = date.fromisoformat(raw["start_date"][:10]) if raw.get("start_date") else None
    end   = date.fromisoformat(raw["end_date"][:10])   if raw.get("end_date")   else None
    min_days       = raw.get("obs_min_days", 1)
    target_minutes = OBS_TARGET_HOUR * 60

    # acc[depth][day_str] = [sum, count] over samples in the centered noon hour [11:30, 12:30).
    # Mirrors functions.load_obs's centered hourly bin, so OpenDA and the native engines assimilate
    # byte-identical obs. (A day with no sample in that hour emits no obs, like load_obs's empty bin.)
    acc = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    with open(obs_csv, newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("value"):
                continue
            day_str = row["time"][:10]
            day = date.fromisoformat(day_str)
            if (start and day < start) or (end and day > end):
                continue
            minutes = _utc_minutes_since_midnight(row["time"])
            if not (target_minutes - 30 <= minutes < target_minutes + 30):
                continue
            depth = float(row["depth"])
            cell = acc[depth][day_str]
            cell[0] += float(row["value"])
            cell[1] += 1

    depths = sorted(d for d in acc if len(acc[d]) >= min_days)

    # Keep only depths the model actually outputs (z_out.dat): an obs depth with no
    # matching model output depth (e.g. 0.5 m on a whole-metre grid) can't be
    # assimilated, since there is no model prediction to compare it against.
    model_depths = _model_output_depths(standard_inputs)
    if model_depths:
        matched = [d for d in depths if any(abs(d - m) <= 1e-6 for m in model_depths)]
        dropped = [d for d in depths if d not in matched]
        if dropped:
            print(f"[adapter] dropping obs depths with no matching model output depth (z_out.dat): "
                  f"{[f'{d:g}' for d in dropped]} m")
        depths = matched

    window = f"{start or 'start'}..{end or 'end'}"
    print(f"[adapter] observations: {os.path.relpath(obs_csv, ROOT)} -> "
          f"stochObserver/T_*_real.csv  ({len(depths)} depths {[f'{d:g}' for d in depths]}, window {window})")
    if not dry_run:
        os.makedirs(stoch_dir, exist_ok=True)
    for depth in depths:
        out_path = os.path.join(stoch_dir, f"T_{depth:g}m_real.csv")
        records  = acc[depth]
        if dry_run:
            print(f"  [dry-run] T_{depth:g}m_real.csv  ({len(records)} days)")
            continue
        with open(out_path, "w", newline="") as f:
            f.write("time,value\n")
            for day_str in sorted(records):
                s, c = records[day_str]
                f.write(f"{_noon_simstrat_day(day_str, ref_date):.6f},{s / c:.6f}\n")
    if not dry_run:
        print(f"  wrote {len(depths)} depth files -> {os.path.relpath(stoch_dir, ROOT)}")
    return depths


def adapt(raw, dry_run=False):
    verify_args(raw, REQUIRED)

    lake          = raw["lake"]
    n_members     = raw["n_members"]
    ensemble_base = resolve_src(raw["ensemble_base"])
    standard_inputs = raw.get("standard_inputs_path")
    standard_inputs = resolve_src(standard_inputs) if standard_inputs \
        else os.path.join(ROOT, "inputs", lake)

    openda_dir   = resolve_src(raw["openda_dir"]) if raw.get("openda_dir") \
        else os.path.join(ROOT, "run", "openda_simstrat")
    forcings_dir = os.path.join(openda_dir, "forcings")
    template_dir = os.path.join(openda_dir, "stochModel", "template")

    # openda_simstrat/ is fully generated — create the working dir + template skeleton
    # on demand (nothing is committed; the static wrapper lives in static/openda/).
    if not dry_run:
        os.makedirs(template_dir, exist_ok=True)   # also creates openda_dir/stochModel

    print(f"[adapter] lake={lake}  framework={os.path.relpath(ensemble_base, ROOT)}  "
          f"-> openda={os.path.relpath(openda_dir, ROOT)}{'  (dry-run)' if dry_run else ''}")

    # ------------------------------------------------------------------
    # 0. Hand-maintained wrapper: static/openda/* -> working dir
    #    (the only non-generated OpenDA pieces; everything else is rendered/synced)
    # ------------------------------------------------------------------
    print("[adapter] wrapper (static/openda) -> stochModel/:")
    _copy(os.path.join(STATIC_OPENDA, "simstratWrapperEnKF.xml"),
          os.path.join(openda_dir, "stochModel", "simstratWrapperEnKF.xml"), dry_run)
    _copy(os.path.join(STATIC_OPENDA, "simstrat_wrapper_enkf.py"),
          os.path.join(openda_dir, "stochModel", "bin", "simstrat_wrapper_enkf.py"), dry_run)

    # ------------------------------------------------------------------
    # 1. Standard model inputs: standard_inputs/* -> template/
    #    (skip OpenDA coupling files, the heavy Results/, the visualization-only
    #    ref/, and dated snapshot archives — the warmup is placed into
    #    template/Results/ in step 3)
    # ------------------------------------------------------------------
    if not os.path.isdir(standard_inputs):
        raise FileNotFoundError(
            f"standard_inputs not found: {standard_inputs} (provide it manually — Simstrat inputs + a dated simulation-snapshot_*.dat)")
    print(f"[adapter] standard inputs -> template/ (skipping OpenDA-specific {sorted(OPENDA_SPECIFIC)}):")
    for name in sorted(os.listdir(standard_inputs)):
        if name in OPENDA_SPECIFIC or name in ("Results", "ref") or name.startswith("simulation-snapshot_"):
            continue
        _copy_path(os.path.join(standard_inputs, name),
                   os.path.join(template_dir, name), dry_run)

    # ------------------------------------------------------------------
    # 2. Perturbed forcings: ensemble{i}/Forcing.dat -> forcings/Forcing_{i}.dat
    # ------------------------------------------------------------------
    print(f"[adapter] forcings (0..{n_members}):")
    for i in range(n_members + 1):                       # 0 = control, 1..N = members
        src = os.path.join(ensemble_base, f"ensemble{i}", "Forcing.dat")
        if not os.path.isfile(src):
            raise FileNotFoundError(
                f"{src} missing — run main.py (copy + perturbate steps) first")
        _copy(src, os.path.join(forcings_dir, f"Forcing_{i}.dat"), dry_run)
    if not dry_run:
        print(f"  copied {n_members + 1} forcing files -> {os.path.relpath(forcings_dir, ROOT)}")

    # ------------------------------------------------------------------
    # 3. Warmup snapshot -> template/Results/simulation-snapshot.dat
    #    (the live name OpenDA clones into each work dir and continues from).
    #    Source: the dated warmup archive in standard_inputs (stable; the live
    #    standard_inputs/Results/ copy may have been overwritten by later runs).
    # ------------------------------------------------------------------
    dated = sorted(glob.glob(os.path.join(standard_inputs, "simulation-snapshot_*.dat")))
    if not dated:
        print(f"[adapter] WARNING: no simulation-snapshot_*.dat in "
              f"{os.path.relpath(standard_inputs, ROOT)} — skipping warmup sync")
    else:
        snap_src = dated[-1]
        target   = os.path.join(template_dir, "Results", "simulation-snapshot.dat")
        print(f"[adapter] warmup: {os.path.basename(snap_src)} "
              f"-> {os.path.relpath(target, openda_dir)} (overwrites OpenDA's current warmup)")
        _copy(snap_src, target, dry_run)

        # Seed OpenDA's initial state (temperature_state.txt) from the warmup
        # snapshot's full-grid T profile — one value per cell.  Replaces the legacy
        # 7-value placeholder and is automatically the right size for this lake's grid.
        state_path = os.path.join(template_dir, "temperature_state.txt")
        if dry_run:
            print(f"  [dry-run] would seed {os.path.relpath(state_path, openda_dir)} from warmup")
        else:
            T = read_snapshot(snap_src, par_path=os.path.join(template_dir, "Settings.par")).model["T"]
            with open(state_path, "w") as f:
                for t in T:
                    f.write(f"{float(t):.6f}\n")
            print(f"[adapter] temperature_state.txt seeded from warmup ({len(T)} cells)")

    # ------------------------------------------------------------------
    # 4. Observations: observations/<lake>/temperature.csv -> stochObserver/T_{depth}m_real.csv
    #    (noon-snapshot per depth; formerly prepare_real_obs.py).  Returns the
    #    auto-detected depth list for the config generator to wire everywhere.
    # ------------------------------------------------------------------
    obs_depths = _build_observations(raw, openda_dir, standard_inputs, dry_run)

    print("[adapter] done." if not dry_run else "[adapter] dry-run complete (nothing written).")
    return obs_depths


# ---------------------------------------------------------------------------
# End-to-end OpenDA run (adapt -> render config -> launch oda_run.sh -> summarise)
# ---------------------------------------------------------------------------

def run_openda(cfg, ensemble_raw, ensemble_base, n_members, dry_run=False, skip_oda=False,
               model_cfg=None, model_name="simstrat"):
    """OpenDA engine driver: sync inputs/forcings/warmup + build observations (adapt),
    render run.oda + the .gen.xml chain, launch oda_run.sh, then summarise.

    `model_cfg` is the selected model's runtime config (from main.py's -m/--model, i.e.
    models.MODELS). Its Docker image is written to template/model.json so the standalone
    OpenDA wrapper — a separate WSL subprocess that can't receive Python args — reads it
    from there instead of hardcoding the version.

    The generated working dir is named per run — run/openda_<model>_<lake>_<filter> (e.g.
    run/openda_simstrat_upperlugano_enkf) — so runs are self-describing and don't clash.
    Override with cfg["openda_dir"].

    cfg["openda_bin"] (the dir holding the OpenDA binaries, e.g. .../openda_3.4.0/bin) is used to
    build the full OpenDA environment (OPENDADIR/OPENDALIB, the bundled JRE + bin on PATH,
    LD_LIBRARY_PATH) for the oda_run.sh subprocess only, so it need not be sourced in the shell; the
    env is temporary to the run. Omit it (or set cfg["openda_native"], default linux64_gnu) to use an
    externally-sourced environment."""
    filter_type = cfg.get("filter", "EnKF")
    if filter_type not in FILTERS:
        raise ValueError(f"unknown filter '{filter_type}'; choose from {sorted(FILTERS)}")
    default_dir = f"run/openda_{model_name}_{ensemble_raw['lake']}_{filter_type.lower()}"
    openda_dir  = resolve_root(cfg.get("openda_dir") or default_dir)

    # --- 4. adapter (always): sync inputs/forcings/warmup + build observations,
    #         returning the auto-detected obs depth list for the render below ----
    print(f"[4/5] adapt framework -> {os.path.relpath(openda_dir, ROOT)}")
    obs_depths = adapt({**ensemble_raw, "openda_dir": openda_dir}, dry_run=dry_run)

    # Bridge the model's Docker image to the (separate-process) wrapper via a generated
    # file. Single source of truth: models.py. Version-only base "eawag/simstrat" mirrors
    # functions.py; the wrapper falls back to the same default if the file is absent.
    if model_cfg and not dry_run:
        image = f"eawag/simstrat:{model_cfg.get('simstrat_version', '3.0.4')}"
        model_json = os.path.join(openda_dir, "stochModel", "template", "model.json")
        with open(model_json, "w") as f:
            json.dump({"image": image}, f)
        print(f"      wrote {os.path.relpath(model_json, openda_dir)} (image={image})")

    # --- 5. render filter config + run OpenDA ------------------------------
    if dry_run:
        print(f"[5/5] [dry-run] would render run.oda + chain for filter={filter_type}, "
              f"then oda_run.sh run.oda")
        return
    # Note: obs error std comes from the shared ensemble.json "sigma_obs" (the same key the native
    # EnKF reads), so the two engines can't silently diverge. (config.py's internal param is still
    # named obs_std.)
    oda_file = render_oda(openda_dir, filter_type, n_members, obs_depths,
                          ensemble_raw["start_date"], ensemble_raw["end_date"],
                          obs_std=ensemble_raw.get("sigma_obs", 0.5))
    print(f"[5/5] rendered {oda_file} + chain for filter={filter_type} "
          f"(Results/work0..N, {len(obs_depths)} obs depths)")
    # OpenDA launch: build the full OpenDA environment in-process from cfg["openda_bin"] (the dir
    # holding the OpenDA binaries, e.g. .../openda_3.4.0/bin) so it does NOT need sourcing in the
    # shell first. Everything is derived from that one path — OPENDADIR/OPENDALIB, the bundled JRE
    # and bin on PATH, LD_LIBRARY_PATH — mirroring the manual `export`s in the README. The env lives
    # only in this subprocess (temporary to the run; the parent process/shell is untouched). Omit
    # "openda_bin" to fall back to an externally-sourced environment.
    openda_bin = cfg.get("openda_bin")
    env = os.environ.copy()
    if openda_bin:
        openda_bin  = os.path.expanduser(openda_bin)
        openda_root = os.path.dirname(openda_bin)                 # e.g. .../openda_3.4.0
        native      = cfg.get("openda_native", "linux64_gnu")
        openda_lib  = os.path.join(openda_bin, native)
        jre_bin     = os.path.join(openda_root, "jre", "bin")
        env["OPENDADIR"]       = openda_bin
        env["OPENDA_NATIVE"]   = native
        env["OPENDALIB"]       = openda_lib
        env["PATH"]            = os.pathsep.join([jre_bin, openda_bin, env.get("PATH", "")])
        env["LD_LIBRARY_PATH"] = os.pathsep.join([os.path.join(openda_lib, "lib"),
                                                  env.get("LD_LIBRARY_PATH", "")])
        oda_exe = os.path.join(openda_bin, "oda_run.sh")
    else:
        oda_exe = "oda_run.sh"

    if skip_oda:
        print(f"      --skip-oda: run manually: "
              f"cd {os.path.relpath(openda_dir, ROOT)} && {oda_exe} {oda_file}")
        return
    # Results/ holds both the per-member work dirs (Results/work0..N) and the PythonResultWriter
    # output; create it up front so OpenDA's result writer has somewhere to write.
    os.makedirs(os.path.join(openda_dir, "Results"), exist_ok=True)
    print(f"      {oda_exe} {oda_file}  (cwd={os.path.relpath(openda_dir, ROOT)})")
    try:
        subprocess.run([oda_exe, oda_file], cwd=openda_dir, check=True, env=env)
    except FileNotFoundError:
        raise RuntimeError(
            "oda_run.sh not found — set \"openda_bin\" in the arg file to the OpenDA bin dir, "
            "or source the OpenDA environment so oda_run.sh is on PATH")

    # Tidy the run dir: OpenDA writes its run log into the .oda cwd — move it into log/.
    log_src = os.path.join(openda_dir, "openda_logfile.txt")
    if os.path.isfile(log_src):
        log_dir = os.path.join(openda_dir, "log")
        os.makedirs(log_dir, exist_ok=True)
        shutil.move(log_src, os.path.join(log_dir, "openda_logfile.txt"))
        print(f"      moved openda_logfile.txt -> {os.path.relpath(os.path.join(log_dir, 'openda_logfile.txt'), ROOT)}")

    # Per-member work dirs live inside this run's dir at Results/work0..N.
    work_base = os.path.join(openda_dir, "Results")
    member_files = [os.path.join(work_base, f"work{i}", "Results", "T_out.dat")
                    for i in range(1, n_members + 1)]
    obs_csv = ensemble_raw.get("obs_csv")
    obs_csv = resolve_root(obs_csv) if obs_csv else os.path.join(ROOT, "observations", ensemble_raw["lake"], "temperature.csv")
    report_summary("openda", filter_type, member_files, ensemble_raw["lake"], obs_csv, openda_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export framework forcings + warmup into openda_simstrat/")
    parser.add_argument("arg_file", help="Path to JSON args file (e.g. args/ensemble.json)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied, write nothing")
    cli = parser.parse_args()

    arg_file = cli.arg_file
    if not os.path.isfile(arg_file):
        arg_file = os.path.join(ROOT, arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        raw_args = json.load(f)

    adapt(raw_args, dry_run=cli.dry_run)
