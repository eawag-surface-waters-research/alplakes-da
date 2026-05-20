#!/usr/bin/env python3
"""Build daily-mean observation CSVs from T_obs_castagnola.csv.

Reads the high-frequency (10-min) profile observations, computes a daily
mean at each target depth, and writes T_0m_real.csv / T_10m_real.csv /
T_20m_real.csv into stochObserver/ using the same time,value format as the
existing synthetic CSVs (time in Simstrat days since 1981-01-01).
"""

import csv
import os
from collections import defaultdict
from datetime import date

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
OBS_CSV      = os.path.join(SCRIPT_DIR, 'stochObserver', 'T_obs_castagnola.csv')
OUT_DIR      = os.path.join(SCRIPT_DIR, 'stochObserver')
REF_DATE     = date(1981, 1, 1)
DATE_START   = date(2025, 1, 3)
DATE_END     = date(2025, 1, 31)

# target depth (m) -> label -> file name
TARGET_DEPTHS = {
    0.0:  ('T_0m_real.csv',  0.5),   # closest available depth
    10.0: ('T_10m_real.csv', 9.0),
    20.0: ('T_20m_real.csv', 19.0),
}

# ---------------------------------------------------------------------------

def to_simstrat_day(iso_str):
    """Convert ISO date string (YYYY-MM-DD...) to integer Simstrat day."""
    d = date.fromisoformat(iso_str[:10])
    return (d - REF_DATE).days


def main():
    # daily_data[obs_depth][date_str] = [values...]
    daily_data = defaultdict(lambda: defaultdict(list))

    needed_depths = {v[1] for v in TARGET_DEPTHS.values()}

    print("Reading", OBS_CSV)
    with open(OBS_CSV, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            depth = float(row['depth'])
            if depth not in needed_depths:
                continue
            if not row['value']:
                continue
            day_str = row['time'][:10]
            if not (DATE_START <= date.fromisoformat(day_str) <= DATE_END):
                continue
            daily_data[depth][day_str].append(float(row['value']))

    for target, (filename, obs_depth) in TARGET_DEPTHS.items():
        out_path = os.path.join(OUT_DIR, filename)
        records  = daily_data[obs_depth]
        with open(out_path, 'w', newline='') as f:
            f.write("time,value\n")
            for day_str in sorted(records):
                sim_day  = to_simstrat_day(day_str)
                mean_val = sum(records[day_str]) / len(records[day_str])
                f.write("{},{:.6f}\n".format(sim_day, mean_val))
        print("Written {:25s}  ({} days, obs depth {:.1f} m)".format(
            filename, len(records), obs_depth))


if __name__ == '__main__':
    main()
