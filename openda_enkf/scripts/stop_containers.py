"""Stop and remove all OpenDA Simstrat containers."""

import sys, argparse, subprocess, concurrent.futures

CONTAINER_TAG = "enkf_openda"


def stop_one(member_id):
    name = f"simstrat_{CONTAINER_TAG}_{member_id}"
    subprocess.run(f"docker stop {name}", shell=True, capture_output=True)
    subprocess.run(f"docker rm   {name}", shell=True, capture_output=True)
    print(f"  Removed  {name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-members", type=int, default=20)
    args = ap.parse_args()

    print(f"Stopping {args.n_members} containers ...")
    with concurrent.futures.ThreadPoolExecutor() as pool:
        list(pool.map(stop_one, range(1, args.n_members + 1)))
    print("Done.")


if __name__ == "__main__":
    main()
