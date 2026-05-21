#!/usr/bin/env python3
"""Build noon-snapshot observation CSVs from T_obs_castagnola.csv.

Reads the high-frequency (10-min) profile observations, selects the single
reading closest to 12:00 UTC from each day at every available depth, and
writes one T_{depth}m_real.csv per depth into stochObserver/.
Time is written as fractional Simstrat days since 1981-01-01.
"""

import csv
import os
from collections import defaultdict
from datetime import date, datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OBS_CSV     = os.path.join(SCRIPT_DIR, 'stochObserver', 'T_obs_castagnola.csv')
OUT_DIR     = os.path.join(SCRIPT_DIR, 'stochObserver')
REF_DATE    = date(1981, 1, 1)
DATE_START  = date(2025, 1, 3)
DATE_END    = date(2025, 12, 31)
TARGET_HOUR = 12  # pick the obs closest to this UTC hour each day

# ---------------------------------------------------------------------------


def noon_simstrat_day(day_str):
    """Simstrat day at noon (integer day + 0.5) for a YYYY-MM-DD string."""
    return (date.fromisoformat(day_str) - REF_DATE).days + 0.5


def utc_minutes_since_midnight(iso_str):
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.hour * 60 + dt.minute + dt.second / 60.0


def depth_label(depth):
    return f"{depth:g}m"


def main():
    # best_obs[depth][day_str] = (abs_minutes_from_target, iso_str, value)
    best_obs = defaultdict(dict)
    target_minutes = TARGET_HOUR * 60

    print("Reading", OBS_CSV)
    with open(OBS_CSV, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['value']:
                continue
            day_str = row['time'][:10]
            if not (DATE_START <= date.fromisoformat(day_str) <= DATE_END):
                continue
            depth = float(row['depth'])
            diff  = abs(utc_minutes_since_midnight(row['time']) - target_minutes)
            current = best_obs[depth].get(day_str)
            if current is None or diff < current[0]:
                best_obs[depth][day_str] = (diff, row['time'], float(row['value']))

    for depth in sorted(best_obs):
        filename = f"T_{depth_label(depth)}_real.csv"
        out_path = os.path.join(OUT_DIR, filename)
        records  = best_obs[depth]
        with open(out_path, 'w', newline='') as f:
            f.write("time,value\n")
            for day_str in sorted(records):
                _, iso_str, value = records[day_str]
                f.write(f"{noon_simstrat_day(day_str):.6f},{value:.6f}\n")
        print(f"Written {filename:30s}  ({len(records)} days, depth {depth} m)")


if __name__ == '__main__':
    main()
