"""
Start persistent Docker containers for the OpenDA Simstrat ensemble.
Run BEFORE launching OpenDA; stop with stop_containers.py.

Usage:
    python start_containers.py [--lake upperlugano] [--n-members 20]
"""

import os, sys, argparse, subprocess, concurrent.futures

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SIMSTRAT_VERSION = "3.0.4"
CONTAINER_TAG    = "enkf_openda"
SIMSTRAT_WORKDIR = "/simstrat/run"


def start_one(member_id, ensemble_base):
    name  = f"simstrat_{CONTAINER_TAG}_{member_id}"
    mount = os.path.join(ensemble_base, f"ensemble{member_id}").replace("\\", "/")
    subprocess.run(f"docker rm -f {name}", shell=True, capture_output=True)
    cmd = (
        f"docker run -d --name {name} "
        f"-v {mount}:{SIMSTRAT_WORKDIR} "
        f"--entrypoint sleep "
        f"eawag/simstrat:{SIMSTRAT_VERSION} infinity"
    )
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    ok  = res.returncode == 0
    print(f"  {'OK' if ok else 'FAILED'}  {name}")
    if not ok:
        print(f"       {res.stderr.strip()}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lake",      default="upperlugano")
    ap.add_argument("--n-members", type=int, default=20)
    args = ap.parse_args()

    ensemble_base = os.path.join(ROOT, "assimilation", args.lake)
    print(f"Starting {args.n_members} containers  (lake={args.lake}) ...")

    members = list(range(0, args.n_members + 1))
    with concurrent.futures.ThreadPoolExecutor() as pool:
        results = list(pool.map(
            lambda i: start_one(i, ensemble_base),
            members,
        ))

    failed = [members[i] for i, ok in enumerate(results) if not ok]
    if failed:
        sys.exit(f"FAILED members: {failed}")
    print("All containers started.")


if __name__ == "__main__":
    main()
