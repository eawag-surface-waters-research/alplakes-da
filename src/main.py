"""End-to-end data-assimilation orchestrator. One front door for both engines:

  1. require standard_inputs (provided manually)  -> inputs/<lake>/
  2. copy_standard_inputs -> ensemble0..N   3. perturbate -> Forcing.dat in 1..N
  4-5. run + summarize:  python -> run_enkf / run_pf   |   openda -> run_openda

Step 2 is skipped when already done (override: --force-copy); step 3 (perturbate)
always runs - it fits perturbations/<lake>.json from ICON first if it is missing.
The config selects the engine and points at the arg files:

  {"engine": "python|openda", "ensemble_args": ..., "run_args": ...,  # run_args: python
   "filter": "EnKF|DEnKF|EnSR|PF"}                                    # filter: openda

    python src/main.py args/run_enkf.json   [--dry-run] [--force-*]
    python src/main.py args/run_openda.json [--dry-run] [--skip-oda]  # openda: WSL + Docker
"""

import os
import sys
import argparse

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from perturbate                  import perturbator
from assimilator.functions       import (resolve_src, load_json, standard_inputs_ready,
                                         instances_ready, copy_standard_inputs)
from assimilator.python.enkf    import run_enkf
from assimilator.python.pf      import run_pf
from assimilator.openda.adapter import run_openda

def run(cfg, dry_run=False, skip_oda=False, force=None):
    """Run the pipeline: require standard_inputs, then copy -> perturbate -> engine run.
    Step 2 skips when already done (unless --force-copy); step 3 always perturbates,
    fitting perturbations/<lake>.json from scratch first if it does not exist."""
    force  = force or {}
    engine = cfg.get("engine", "python")
    if engine not in ("python", "openda"):
        raise ValueError(f"unknown engine '{engine}'; choose 'python' or 'openda'")

    ensemble_raw = load_json(cfg["ensemble_args"])

    lake          = ensemble_raw["lake"]
    n_members     = ensemble_raw["n_members"]
    ensemble_base = resolve_src(ensemble_raw["ensemble_base"])
    standard_inputs = os.path.join(ROOT, "inputs", lake)

    # Pin every step to the same absolute ensemble_base (avoids cwd-dependent
    # resolution differences between the sub-scripts).
    ensemble_raw["ensemble_base"] = ensemble_base

    tag = "  (dry-run)" if dry_run else ""
    print(f"=== DA pipeline - lake={lake}  base={os.path.relpath(ensemble_base, ROOT)}"
          f"  engine={engine}{tag} ===")

    # --- 1. standard inputs (provided manually) ---------------------------
    if not standard_inputs_ready(standard_inputs):
        raise FileNotFoundError(
            f"standard_inputs not ready at {os.path.relpath(standard_inputs, ROOT)}: "
            f"provide it manually — a dated simulation-snapshot_*.dat, Forcing.dat, "
            f"Settings.par and the remaining Simstrat inputs.")
    print(f"[1/5] standard inputs present -> {os.path.relpath(standard_inputs, ROOT)}")

    # --- 2. copy into instances -------------------------------------------
    if force.get("copy") or not instances_ready(ensemble_base, n_members):
        why = "forced" if force.get("copy") else "missing instances"
        print(f"[2/5] copy standard inputs -> ensemble0..{n_members} ({why})")
        if not dry_run:
            copy_standard_inputs(ensemble_raw)
    else:
        print(f"[2/5] ensemble0..{n_members} present - skip")

    # --- 3. perturbate forcings (always) ----------------------------------
    #   Source the AR(1) calibration from perturbations/<lake>.json; if it does
    #   not exist yet, fit it from scratch (ICON / EAWAG VPN) first, then apply.
    print(f"[3/5] perturbate Forcing.dat in ensemble1..{n_members}")
    if not dry_run:
        if not os.path.isfile(os.path.join(ROOT, "perturbations", f"{lake}.json")):
            print(f"      no perturbations/{lake}.json - fitting from scratch (ICON / EAWAG VPN)")
            from fit_perturbations import fit   # lazy: pulls in geopandas/requests only when fitting
            fit(ensemble_raw)
        perturbator(ensemble_raw)

    # --- 4-5. engine-specific run + summary --------------------------------
    if engine == "python":
        if dry_run:
            print(f"[4/5] [dry-run] would run {engine} assimilation + summarize")
            return
        run_raw = load_json(cfg["run_args"])
        algo    = run_raw.get("algorithm")
        if algo == "EnKF":
            run_enkf(run_raw, ensemble_raw, ensemble_base, n_members)
        elif algo == "PF":
            run_pf(run_raw, ensemble_raw, ensemble_base, n_members)
        else:
            raise ValueError(f"Unknown algorithm: '{algo}'. Use 'PF' or 'EnKF'.")
    else:
        run_openda(cfg, ensemble_raw, ensemble_base, n_members, dry_run, skip_oda)

    print("=== pipeline complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-end data-assimilation pipeline (Python or OpenDA)")
    parser.add_argument("arg_file", help="Pipeline config JSON (e.g. args/run_enkf.json)")
    parser.add_argument("--dry-run", action="store_true", help="Preview the plan, execute nothing")
    parser.add_argument("--skip-oda", action="store_true", help="OpenDA only: run setup + adapter, but not OpenDA")
    parser.add_argument("--force-copy",       action="store_true", help="Re-run step 2 even if present")
    cli = parser.parse_args()

    cfg = load_json(cli.arg_file)
    run(cfg,
        dry_run=cli.dry_run,
        skip_oda=cli.skip_oda,
        force={"copy": cli.force_copy})
