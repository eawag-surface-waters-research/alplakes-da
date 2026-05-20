"""Plot SequentialEnsembleSimulation results: ensemble fan chart vs control vs observations."""
import matplotlib
matplotlib.use("Agg") 

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
WORK_DIR    = os.path.join(SCRIPT_DIR, "work")
OBS_DIR     = os.path.join(SCRIPT_DIR, "stochObserver")
N_MEMBERS   = 5   # must match generate_ensemble_forcings.py

SIMSTRAT_REF = datetime(1981, 1, 1)

TARGET_DEPTHS = [(-0.0, "0 m"), (-10.0, "10 m"), (-20.0, "20 m")]


def simstrat_day_to_dt(day):
    return SIMSTRAT_REF + timedelta(days=float(day))


def read_t_out(path):
    with open(path) as f:
        lines = f.readlines()
    depths = [float(h) for h in lines[0].strip().split(",")[1:]]
    times, rows = [], []
    for line in lines[1:]:
        parts = line.strip().split(",")
        if not parts or not parts[0]:
            continue
        times.append(simstrat_day_to_dt(parts[0]))
        rows.append([float(x) for x in parts[1:]])
    return times, depths, np.array(rows)


def nearest_col(depths, target):
    return min(range(len(depths)), key=lambda i: abs(depths[i] - target))


def read_obs_csv(path):
    times, values = [], []
    with open(path) as f:
        next(f)
        for line in f:
            t, v = line.strip().split(",")
            times.append(simstrat_day_to_dt(t))
            values.append(float(v))
    return times, values


# ── Load control (work0) ──────────────────────────────────────────────────────
ctrl_path = os.path.join(WORK_DIR, "work0", "Results", "T_out.dat")
ctrl_times, ctrl_depths, ctrl_T = read_t_out(ctrl_path)

# ── Load ensemble members (work1…workN) ───────────────────────────────────────
ens_T = []   # list of (n_times, n_depths) arrays, one per member
for i in range(1, N_MEMBERS + 1):
    path = os.path.join(WORK_DIR, f"work{i}", "Results", "T_out.dat")
    if not os.path.exists(path):
        print(f"Warning: {path} not found — skipping member {i}")
        continue
    _, _, T = read_t_out(path)
    ens_T.append(T)

if not ens_T:
    raise RuntimeError("No ensemble member T_out.dat files found — did the run complete?")

ens_T = np.stack(ens_T, axis=0)   # (n_members, n_times, n_depths)

# ── Load observations ─────────────────────────────────────────────────────────
obs_files = {
    0:  (os.path.join(OBS_DIR, "T_0m_real.csv"),  "0 m"),
    10: (os.path.join(OBS_DIR, "T_10m_real.csv"), "10 m"),
    20: (os.path.join(OBS_DIR, "T_20m_real.csv"), "20 m"),
}

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
fig.suptitle("Simstrat – Sequential Ensemble Simulation", fontsize=13)

for ax, (target, label), (depth_key, (obs_path, _)) in zip(
        axes, TARGET_DEPTHS, obs_files.items()):

    col_ctrl = nearest_col(ctrl_depths, target)
    col_ens  = nearest_col(ctrl_depths, target)   # same grid

    ctrl_series = ctrl_T[:, col_ctrl]
    ens_series  = ens_T[:, :, col_ens]            # (n_members, n_times)

    for j in range(ens_series.shape[0]):
        ax.plot(ctrl_times, ens_series[j], color="steelblue", lw=0.8, alpha=0.5,
                label="Ensemble members" if j == 0 else None)
    ax.plot(ctrl_times, ctrl_series, color="navy", lw=1.8, label="Control (work0)")

    if os.path.exists(obs_path):
        ot, ov = read_obs_csv(obs_path)
        ax.scatter(ot, ov, color="tomato", s=30, zorder=6, label="Observations")

    ax.set_ylabel(f"T {label} (°C)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
fig.autofmt_xdate()
plt.tight_layout()

out_path = os.path.join(SCRIPT_DIR, "ensemble_results.png")
plt.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")
plt.show()
