"""
Compare the exercise_simstrat initial snapshot (2024-12-31, Simstrat day 16070)
temperature profile against the closest single-point observations at 0 m, 10 m,
and 20 m from the stochObserver real-obs files.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

# Resolve project root robustly — works both as a script and in a Jupyter cell
_here = globals().get("__file__", None)
if _here is not None:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(_here))
    ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
else:
    # Running in a notebook: walk up from cwd until we find the snapshot/ folder
    _cwd = os.getcwd()
    ROOT = _cwd
    while ROOT and not os.path.isdir(os.path.join(ROOT, "snapshot")):
        _parent = os.path.dirname(ROOT)
        if _parent == ROOT:
            raise RuntimeError("Cannot locate project root (snapshot/ not found)")
        ROOT = _parent
    SCRIPT_DIR = os.path.join(ROOT, "testing_simple", "exercise_simstrat")

sys.path.insert(0, os.path.join(ROOT, "snapshot"))
from snapshot_io import read_snapshot
SNAPSHOT_PATH = os.path.join(SCRIPT_DIR, "stochModel", "template", "Results",
                              "simulation-snapshot.dat")
SNAPSHOT_REF_PATH = os.path.join(SCRIPT_DIR, "stochModel", "template",
                                  "simulation-snapshot_20241231.dat")
PAR_PATH      = os.path.join(SCRIPT_DIR, "stochModel", "template", "Settings.par")
OBS_DIR       = os.path.join(SCRIPT_DIR, "stochObserver")

# Reference date and snapshot day (Simstrat days since 1981-01-01)
REF_DATE      = pd.Timestamp("1981-01-01", tz="UTC")
SNAPSHOT_DAY  = 16070.0   # 2024-12-31

OBS_FILES = {
    0:  os.path.join(OBS_DIR, "T_0m_real.csv"),
    10: os.path.join(OBS_DIR, "T_10m_real.csv"),
    20: os.path.join(OBS_DIR, "T_20m_real.csv"),
}
OBS_COLORS = {0: "#e41a1c", 10: "#ff7f00", 20: "#984ea3"}

snapshot_date = REF_DATE + pd.to_timedelta(SNAPSHOT_DAY, unit="D")
print(f"Snapshot date : {snapshot_date.date()}  (day {SNAPSHOT_DAY})")

# ── 1. Load snapshot ─────────────────────────────────────────────────────────
snap      = read_snapshot(SNAPSHOT_PATH, par_path=PAR_PATH)
T         = snap.model["T"]
z_vol     = snap.grid["z_volume"][-len(T):]
lake_lev  = snap.grid["lake_level"]
snap_depth = lake_lev - z_vol
order     = np.argsort(snap_depth)
snap_depth = snap_depth[order]
snap_T    = T[order]

snap_ref   = read_snapshot(SNAPSHOT_REF_PATH, par_path=PAR_PATH)
T_ref      = snap_ref.model["T"]
z_vol_ref  = snap_ref.grid["z_volume"][-len(T_ref):]
lev_ref    = snap_ref.grid["lake_level"]
ref_depth  = lev_ref - z_vol_ref
order_ref  = np.argsort(ref_depth)
ref_depth  = ref_depth[order_ref]
ref_T      = T_ref[order_ref]

# ── 2. Load obs – pick value closest in time to the snapshot ─────────────────
obs_points = {}   # depth -> (day, value, date)
for depth, path in OBS_FILES.items():
    df = pd.read_csv(path)
    idx = (df["time"] - SNAPSHOT_DAY).abs().idxmin()
    row = df.loc[idx]
    obs_date = REF_DATE + pd.to_timedelta(row["time"], unit="D")
    obs_points[depth] = (row["time"], row["value"], obs_date)
    print(f"  obs {depth:2d} m  : day {row['time']:.0f}  ({obs_date.date()})  T = {row['value']:.3f} °C")

print()

# ── 3. Plot ──────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5, 8))

ax.plot(snap_T, snap_depth, color="steelblue", lw=2.5, zorder=5)
ax.plot(ref_T, ref_depth, color="gray", lw=2, ls="--", zorder=4)
legend_handles = [
    mlines.Line2D([], [], color="steelblue", lw=2.5,
                  label=f"Simstrat snapshot {snapshot_date.strftime('%d/%m/%Y')}"),
    mlines.Line2D([], [], color="gray", lw=2, ls="--",
                  label="reference snapshot_20241231"),
]

for depth, (day, value, obs_date) in obs_points.items():
    color = OBS_COLORS[depth]
    ax.scatter([value], [depth], color=color, s=80, zorder=6)
    legend_handles.append(
        mlines.Line2D([], [], color=color, marker="o", lw=0, markersize=7,
                      label=f"obs {depth} m  ({obs_date.strftime('%d %b')})")
    )

ax.invert_yaxis()
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Depth (m)")
ax.set_title("exercise_simstrat – initial snapshot vs observations")
ax.legend(handles=legend_handles, fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
out_path = os.path.join(SCRIPT_DIR, "initial_snapshot_check.png")
plt.savefig(out_path, dpi=150)
print(f"Plot saved to: {out_path}")
plt.show()
