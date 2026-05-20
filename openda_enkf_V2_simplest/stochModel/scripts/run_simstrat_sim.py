"""
Minimal OpenDA wrapper script — Step 1 stub.

OpenDA calls this once per analysis time.  The script:
  1. Writes a fixed dummy temperature to instances/instanceN/temperature_obs.txt
  2. Does NOT read time_start.txt / time_end.txt (no OpenDA time exchange)
  3. Does NOT call Docker / Simstrat yet

Once OpenDA can launch this, read the output, and log without Infinity or
NullPointerException, replace the stub body with the real Simstrat runner.

Working directory when called by OpenDA: stochModel/
(blackBoxWrapperConfig.xml sets workingDirectory=".")

Usage (manual test from stochModel/):
    python scripts/run_simstrat_sim.py \
        --instance-number 0 \
        --instance-dir instances/instance0 \
        --ensemble-base ../../assimilation/upperlugano \
        --results-subdir Results_EnKF_openda \
        --container-tag enkf_openda \
        --par-file Settings_EnKF_openda.par
"""

import argparse
import os
import sys

DUMMY_TEMPERATURE = 10.0  # °C — replace with real Simstrat output later

# Observation times matching obs_depth_0.5m.noo — needed for NOOS output format.
OBS_TIMES = ["202501020000", "202501030000", "202501040000"]

NOOS_HEADER = """\
#------------------------------------------------------
# Location    : depth_0.5
# Parameter   : temperature
# Unit        : Celsius
# Timezone    : GMT
#------------------------------------------------------
"""


def _parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance-number", type=int, required=True)
    ap.add_argument("--instance-dir",    required=True)
    ap.add_argument("--ensemble-base",   required=True)
    ap.add_argument("--results-subdir",  required=True)
    ap.add_argument("--container-tag",   required=True)
    ap.add_argument("--par-file",        required=True)
    return ap.parse_args()


def _read_time_files(instance_dir):
    for fname in ("time_start.txt", "time_end.txt"):
        path = os.path.join(instance_dir, fname)
        if os.path.exists(path):
            raw = open(path).read().strip()
            print(f"[time] {fname}: {raw}", flush=True)
        else:
            print(f"[time] {fname}: MISSING", flush=True)


def main():
    args = _parse_args()
    inst = args.instance_number

    # instance_dir may be relative; resolve relative to CWD (= stochModel/)
    instance_dir = os.path.normpath(os.path.join(os.getcwd(), args.instance_dir))
    obs_file = os.path.join(instance_dir, "temperature_obs.txt")

    print(f"[stub inst{inst}]  CWD={os.getcwd()}", flush=True)
    print(f"[stub inst{inst}]  instance_dir={instance_dir}  exists={os.path.isdir(instance_dir)}", flush=True)
    _read_time_files(instance_dir)

    os.makedirs(instance_dir, exist_ok=True)

    with open(obs_file, "w") as fh:
        fh.write(NOOS_HEADER)
        for t in OBS_TIMES:
            fh.write(f"{t}   {DUMMY_TEMPERATURE}\n")

    print(f"[stub inst{inst}]  wrote {obs_file}  T={DUMMY_TEMPERATURE} °C (NOOS, {len(OBS_TIMES)} times)", flush=True)

    # ── TODO: replace stub with real Simstrat runner ──────────────────────────
    #
    # ensemble_dir = os.path.join(os.getcwd(), args.ensemble_base, f"ensemble{inst}")
    # results_dir  = os.path.join(ensemble_dir, args.results_subdir)
    # par_path     = os.path.join(ensemble_dir, args.par_file)
    # container    = f"simstrat_{args.container_tag}_{inst}"
    #
    # _overwrite_par_dates(par_path, fixed_start, fixed_end, REF_DATE_DT)
    # _run_simstrat(container, args.par_file)
    # pred = _extract_obs_prediction(results_dir, snap_path, par_path)
    # with open(obs_file, "w") as fh:
    #     fh.write(f"{pred}\n")
    # ─────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    main()
