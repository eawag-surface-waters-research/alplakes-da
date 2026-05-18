"""
Compare the Geneva initial snapshot (311224 = 31/12/2024) temperature profile
against the closest available LéXPLORE observation and all individual T-chain
profiles for Dec 30, Dec 31 and Jan 01.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "snapshot"))
from snapshot_io import read_snapshot

SNAPSHOT_PATH  = os.path.join(ROOT, "standard_inputs", "geneva", "Results",
                               "simulation-snapshot_31122024.dat")
PAR_PATH       = os.path.join(ROOT, "standard_inputs", "geneva", "Settings.par")
OBS_PATH       = os.path.join(ROOT, "data", "T_obs_geneva.csv")
TCHAIN_GLOB    = [
    os.path.join(ROOT, "data", "geneva", "L2_LexploreTemperatureChain_*.nc"),
    os.path.join(ROOT, "analysis",        "L2_LexploreTemperatureChain_*.nc"),
]
SNAPSHOT_DATE  = pd.Timestamp("2024-12-31", tz="UTC")
TCHAIN_DAYS    = [
    pd.Timestamp("2024-12-30", tz="UTC"),
    pd.Timestamp("2024-12-31", tz="UTC"),
    pd.Timestamp("2025-01-01", tz="UTC"),
]
DAY_COLORS = {
    pd.Timestamp("2024-12-30", tz="UTC"): "#2ca02c",   # green
    pd.Timestamp("2024-12-31", tz="UTC"): "#ff7f0e",   # orange
    pd.Timestamp("2025-01-01", tz="UTC"): "#9467bd",   # purple
}

# ── 1. Load snapshot ───────────────────────────────────────────────────────────
snap       = read_snapshot(SNAPSHOT_PATH, par_path=PAR_PATH)
T          = snap.model["T"]
z_vol      = snap.grid["z_volume"][-len(T):]
lake_lev   = snap.grid["lake_level"]
snap_depth = lake_lev - z_vol
order      = np.argsort(snap_depth)
snap_depth = snap_depth[order]
snap_T     = T[order]

# ── 2. Closest single-point LéXPLORE obs ──────────────────────────────────────
obs          = pd.read_csv(OBS_PATH, parse_dates=["time"])
obs["time"]  = pd.to_datetime(obs["time"], utc=True)
unique_times = obs["time"].sort_values().unique()
closest_time = unique_times[np.argmin(np.abs(unique_times - SNAPSHOT_DATE))]
obs_slice    = obs[obs["time"] == closest_time].sort_values("depth")

# ── 3. Load all T-chain profiles for the target days ─────────────────────────
def load_tchain_profiles(nc_paths, target_days):
    """Return {day: [(timestamp, depths, T_profile), ...]} for each day."""
    results = {day: [] for day in target_days}

    for path in sorted(nc_paths):
        ds     = nc.Dataset(path)
        t_raw  = nc.num2date(ds.variables["time"][:], ds.variables["time"].units,
                             only_use_cftime_datetimes=False)
        t      = pd.to_datetime(t_raw, utc=True)
        T2     = np.ma.filled(ds.variables["temp"][:], np.nan)  # (depth, time)
        depths = ds.variables["depth"][:]
        ds.close()

        for day in target_days:
            mask = (t >= day) & (t < day + pd.Timedelta(days=1))
            for idx in np.where(mask)[0]:
                profile = T2[:, idx]
                valid   = ~np.isnan(profile)
                if valid.sum() == 0:
                    continue
                results[day].append((t[idx], depths[valid], profile[valid]))

    return results

print(f"Snapshot date : {SNAPSHOT_DATE.date()}")
print(f"Closest obs   : {pd.Timestamp(closest_time).isoformat()}")
print()

nc_files      = sorted(f for pattern in TCHAIN_GLOB for f in glob.glob(pattern))
tchain_data   = load_tchain_profiles(nc_files, TCHAIN_DAYS)

for day in TCHAIN_DAYS:
    profiles = tchain_data[day]
    if not profiles:
        print(f"T-chain {day.date()}: no data")
        continue
    hours = sorted({pd.Timestamp(ts).strftime("%H:%M") for ts, _, _ in profiles})
    print(f"T-chain {day.date()}: {len(profiles)} profiles — hours: {', '.join(hours)}")
print()

# ── 4. Plot ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 9))

# T-chain profiles — all timesteps, thin + transparent, one color per day
legend_handles = []
for day in TCHAIN_DAYS:
    profiles = tchain_data[day]
    if not profiles:
        continue
    color = DAY_COLORS[day]
    for ts, depths, temps in profiles:
        ax.plot(temps, depths, color=color, lw=0.4, alpha=0.15)
    label = day.strftime("T-chain %d %b")
    legend_handles.append(mlines.Line2D([], [], color=color, lw=1.5, label=label))

# snapshot
ax.plot(snap_T, snap_depth, color="steelblue", lw=2.5, zorder=5,
        label="Simstrat snapshot 31/12/2024")
legend_handles.insert(0, mlines.Line2D([], [], color="steelblue", lw=2.5,
                                        label="Simstrat snapshot 31/12/2024"))

# single-point obs
obs_label = f"LéXPLORE obs {pd.Timestamp(closest_time).strftime('%d %b %H:%M UTC')}"
ax.scatter(obs_slice["value"], obs_slice["depth"], color="tomato", zorder=6, s=55,
           label=obs_label)
legend_handles.append(mlines.Line2D([], [], color="tomato", marker="o", lw=0,
                                     markersize=6, label=obs_label))

ax.invert_yaxis()
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Depth (m)")
ax.set_title("Geneva – initial snapshot vs LéXPLORE T-chain")
ax.legend(handles=legend_handles, fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "initial_snapshot_check.png")
plt.savefig(out_path, dpi=150)
print(f"Plot saved to: {out_path}")
plt.show()
