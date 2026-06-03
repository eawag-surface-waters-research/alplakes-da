"""End-to-end OpenDA EnKF orchestrator.

Runs the full chain, skipping the expensive setup steps that are already done:

  1. initial_conditions_snapshot  -> run/<lake>/standard_inputs (+ warmup snapshot)
                                     [skip if standard_inputs already present]
  2. copy_standard_inputs         -> run/<lake>/ensemble0..N
                                     [skip if instances already exist]
  3. perturbate                   -> perturbed Forcing.dat in ensemble1..N
                                     [skip if forcings already perturbed]
  4. openda_adapter               -> sync inputs + forcings + warmup + observations into openda_simstrat/
                                     [always]
  5. openda_config.render + oda_run.sh run.oda
                                     -> render the filter's run.oda + chain, then run OpenDA
                                     [always render; launch unless --skip-oda]

Overrides: --force-initial / --force-copy / --force-perturbate re-run a step even
if it looks done; --dry-run previews without executing; --skip-oda renders the
config then stops before launching OpenDA.

Config JSON references the per-step arg files + the OpenDA target + the filter:
  {
    "snapshot_args": "args/snapshot.json",
    "ensemble_args": "args/ensemble.json",
    "filter":        "EnKF",            # one of EnKF | DEnKF | EnSR
    "openda_dir":    "openda_simstrat"
  }

Run in WSL/bash (steps 1 and 5 use Docker with `$(id -u)` and oda_run.sh), with the
OpenDA environment sourced and Docker running:

    python src/openda_assimilation.py args/openda_assimilation.json [--dry-run] [--skip-oda] [--force-*]
"""

import os
import sys
import glob
import json
import filecmp
import argparse
import subprocess

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from initial_conditions_snapshot import create_standard_inputs
from copy_standard_inputs        import copy_standard_inputs
from perturbate                  import perturbator
from openda_adapter              import adapt
from openda_config               import FILTERS, render as render_oda, work_dir_name
from alplakes_da.summarize        import summarize_run


def _resolve(path):
    """Resolve a possibly-relative ensemble_base ('../run/<lake>') against src/."""
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(SRC_DIR, path))


def _resolve_root(path):
    """Resolve a possibly-relative repo path ('openda_simstrat', 'args/x.json') against ROOT."""
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(ROOT, path))


def _load_json(path):
    p = path if os.path.isfile(path) else _resolve_root(path)
    if not os.path.isfile(p):
        raise FileNotFoundError(f"args file not found: {path}")
    with open(p) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Availability checks ("already done?")
# ---------------------------------------------------------------------------

def _standard_inputs_ready(standard_inputs):
    return (bool(glob.glob(os.path.join(standard_inputs, "simulation-snapshot_*.dat")))
            and os.path.isfile(os.path.join(standard_inputs, "Forcing.dat")))


def _instances_ready(ensemble_base, n_members):
    return all(os.path.isfile(os.path.join(ensemble_base, f"ensemble{i}", "Settings.par"))
               for i in range(n_members + 1))


def _forcings_perturbed(ensemble_base):
    """True if member forcings differ from the control (i.e. perturbate has run)."""
    ctrl = os.path.join(ensemble_base, "ensemble0", "Forcing.dat")
    mem  = os.path.join(ensemble_base, "ensemble1", "Forcing.dat")
    if not (os.path.isfile(ctrl) and os.path.isfile(mem)):
        return False
    return not filecmp.cmp(ctrl, mem, shallow=False)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run(cfg, dry_run=False, skip_oda=False, force=None):
    force = force or {}

    snapshot_raw = _load_json(cfg["snapshot_args"])
    ensemble_raw = _load_json(cfg["ensemble_args"])

    lake          = ensemble_raw["lake"]
    n_members     = ensemble_raw["n_members"]
    ensemble_base = _resolve(ensemble_raw["ensemble_base"])
    standard_inputs = os.path.join(ensemble_base, "standard_inputs")
    openda_dir    = _resolve_root(cfg.get("openda_dir", "openda_simstrat"))
    filter_type   = cfg.get("filter", "EnKF")
    if filter_type not in FILTERS:
        raise ValueError(f"unknown filter '{filter_type}'; choose from {sorted(FILTERS)}")

    # Pin every step to the same absolute ensemble_base (avoids cwd-dependent
    # resolution differences between the sub-scripts).
    snapshot_raw["ensemble_base"] = ensemble_base
    ensemble_raw["ensemble_base"] = ensemble_base

    # The snapshot builds time-varying inputs (forcing/inflows/absorption); they
    # must cover the full simulation window, so hand it the run's end_date. The
    # spin-up itself still stops at snapshot_date.
    snapshot_raw.setdefault("simulation_end_date", ensemble_raw["end_date"])

    tag = "  (dry-run)" if dry_run else ""
    print(f"=== OpenDA pipeline - lake={lake}  base={os.path.relpath(ensemble_base, ROOT)}"
          f"  filter={filter_type}{tag} ===")

    # --- 1. standard inputs ------------------------------------------------
    if force.get("initial") or not _standard_inputs_ready(standard_inputs):
        why = "forced" if force.get("initial") else "missing"
        print(f"[1/5] create standard inputs ({why}) -> {os.path.relpath(standard_inputs, ROOT)}")
        if not dry_run:
            create_standard_inputs(snapshot_raw)
    else:
        print(f"[1/5] standard inputs present - skip")

    # --- 2. copy into instances -------------------------------------------
    if force.get("copy") or not _instances_ready(ensemble_base, n_members):
        why = "forced" if force.get("copy") else "missing instances"
        print(f"[2/5] copy standard inputs -> ensemble0..{n_members} ({why})")
        if not dry_run:
            copy_standard_inputs(ensemble_raw)
    else:
        print(f"[2/5] ensemble0..{n_members} present - skip")

    # --- 3. perturbate forcings -------------------------------------------
    if force.get("perturbate") or not _forcings_perturbed(ensemble_base):
        why = "forced" if force.get("perturbate") else "not perturbed"
        print(f"[3/5] perturbate Forcing.dat in ensemble1..{n_members} ({why})")
        if not dry_run:
            perturbator(ensemble_raw)
    else:
        print(f"[3/5] forcings already perturbed - skip")

    # --- 4. adapter (always): sync inputs/forcings/warmup + build observations,
    #         returning the auto-detected obs depth list for step 5 ------------
    print(f"[4/5] adapt framework -> {os.path.relpath(openda_dir, ROOT)}")
    obs_depths = adapt({**ensemble_raw, "openda_dir": openda_dir}, dry_run=dry_run)

    # --- 5. render filter config + run OpenDA ------------------------------
    if dry_run:
        print(f"[5/5] [dry-run] would render run.oda + chain for filter={filter_type}, "
              f"then oda_run.sh run.oda")
        return
    oda_file = render_oda(openda_dir, filter_type, n_members, obs_depths,
                          ensemble_raw["start_date"], ensemble_raw["end_date"],
                          obs_std=ensemble_raw.get("obs_std", 0.5))
    print(f"[5/5] rendered {oda_file} + chain for filter={filter_type} "
          f"(work_{filter_type.lower()}, {len(obs_depths)} obs depths)")
    if skip_oda:
        print(f"      --skip-oda: run manually: "
              f"cd {os.path.relpath(openda_dir, ROOT)} && oda_run.sh {oda_file}")
        return
    print(f"      oda_run.sh {oda_file}  (cwd={os.path.relpath(openda_dir, ROOT)})")
    try:
        subprocess.run(["oda_run.sh", oda_file], cwd=openda_dir, check=True)
    except FileNotFoundError:
        raise RuntimeError("oda_run.sh not found on PATH - source the OpenDA environment first")

    # Posterior ensemble summary (members 1..N) -> final_output/
    work_base = os.path.join(os.path.dirname(openda_dir), "run", "openda", work_dir_name(filter_type))
    member_files = [os.path.join(work_base, f"work{i}", "Results", "T_out.dat")
                    for i in range(1, n_members + 1)]
    obs_csv = ensemble_raw.get("obs_csv")
    obs_csv = _resolve_root(obs_csv) if obs_csv else os.path.join(ROOT, "data", f"T_obs_{lake}.csv")
    _, n_mem, T, D = summarize_run(os.path.join(ROOT, "final_output"),
                                   lake, "openda", filter_type, member_files, obs_csv=obs_csv)
    print(f"[summary] {n_mem} members, {T} steps x {D} depths "
          f"-> final_output/{lake}_openda_{filter_type}.csv")
    print("=== pipeline complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-end OpenDA EnKF pipeline")
    parser.add_argument("arg_file", help="Pipeline config JSON (e.g. args/openda_assimilation.json)")
    parser.add_argument("--dry-run", action="store_true", help="Preview the plan, execute nothing")
    parser.add_argument("--skip-oda", action="store_true", help="Run setup + adapter, but not OpenDA")
    parser.add_argument("--force-initial",    action="store_true", help="Re-run step 1 even if present")
    parser.add_argument("--force-copy",       action="store_true", help="Re-run step 2 even if present")
    parser.add_argument("--force-perturbate", action="store_true", help="Re-run step 3 even if present")
    cli = parser.parse_args()

    cfg = _load_json(cli.arg_file)
    run(cfg,
        dry_run=cli.dry_run,
        skip_oda=cli.skip_oda,
        force={"initial": cli.force_initial, "copy": cli.force_copy, "perturbate": cli.force_perturbate})
