"""
Convert observation CSV to OpenDA NOOS format.

Input:  data/T_obs_castagnola.csv  (lake=upperlugano)
Output: openda_enkf/stochObserver/obs_depth_0.5m.noo

Output NOOS format:
    #------------------------------------------------------
    # Location    : depth_0.5
    # Unit        : temperature
    # Timezone    : GMT
    #------------------------------------------------------
    202501020000   14.234567
    202501030000   14.187432
    ...

Timestamps are YYYYMMDDHHmm at 00:00:00 of day+1, so 202501020000
represents the daily mean over 2025-01-01. The NOOS Location+Unit headers
produce the id "depth_0.5.temperature" which must match predictorVector
id in stochModel/simstratStochModel.xml.

Usage:
    python prep_obs.py [--lake upperlugano] [--depth 0.5]
                       [--start 2025-01-01] [--end 2025-12-31]
"""

import os, sys, argparse
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAKE_OBS = {
    "upperlugano": os.path.join(ROOT, "data", "T_obs_castagnola.csv"),
    "murten":      os.path.join(ROOT, "data", "T_obs_murten.csv"),
    "geneva":      os.path.join(ROOT, "data", "T_obs_geneva.csv"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lake",  default="upperlugano")
    ap.add_argument("--depth", type=float, default=0.5)
    ap.add_argument("--start", default="2025-01-01")
    ap.add_argument("--end",   default="2025-12-31")
    args = ap.parse_args()

    obs = pd.read_csv(LAKE_OBS[args.lake], parse_dates=["time"])
    obs["time"] = pd.to_datetime(obs["time"], utc=True)

    mask = (
        (obs["depth"] == args.depth) &
        (obs["time"] >= pd.Timestamp(args.start, tz="UTC")) &
        (obs["time"] <= pd.Timestamp(args.end,   tz="UTC"))
    )
    obs = obs[mask].set_index("time")

    # Daily mean over each calendar day
    daily = obs["value"].resample("1D").mean().dropna()

    openda_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(openda_dir, "stochObserver", "obs_depth_0.5m.noo")

    location = f"depth_{args.depth}"
    with open(output_path, "w") as fh:
        fh.write("#------------------------------------------------------\n")
        fh.write(f"# Location    : {location}\n")
        fh.write("# Unit        : temperature\n")
        fh.write("# Timezone    : GMT\n")
        fh.write("#------------------------------------------------------\n")
        for ts, val in daily.items():
            end_of_window = (ts + pd.Timedelta("1D")).strftime("%Y%m%d%H%M")
            fh.write(f"{end_of_window}   {val:.6f}\n")

    print(f"Written {len(daily)} daily observations → {output_path}")
    print(f"  Depth: {args.depth} m,  Period: {args.start} – {args.end}")


if __name__ == "__main__":
    main()
