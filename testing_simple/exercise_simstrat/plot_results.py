"""Plot sequential simulation results: model predictions vs observations."""
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SIMSTRAT_REF = datetime(1981, 1, 1)  # Simstrat day 0

def simstrat_day_to_datetime(day):
    return SIMSTRAT_REF + timedelta(days=float(day))

def read_observer_csv(path):
    times, values = [], []
    with open(path) as f:
        next(f)  # header
        for line in f:
            t, v = line.strip().split(',')
            times.append(simstrat_day_to_datetime(t))
            values.append(float(v))
    return times, values

def read_t_out(path):
    with open(path) as f:
        lines = f.readlines()
    depths = [float(h) for h in lines[0].strip().split(',')[1:]]
    times, rows = [], []
    for line in lines[1:]:
        parts = line.strip().split(',')
        if not parts or not parts[0]:
            continue
        times.append(simstrat_day_to_datetime(parts[0]))
        rows.append([float(x) for x in parts[1:]])
    return times, depths, np.array(rows)

# ---------------------------------------------------------------------------
# Load OpenDA results
# ---------------------------------------------------------------------------
results_file = os.path.join(os.path.dirname(__file__), 'sequentialSimulation_results.py')
ns = {}
exec(open(results_file).read(), ns)

analysis_times   = [simstrat_day_to_datetime(t) for t in np.array(ns['analysis_time']).ravel()]
pred_f_central   = np.array(ns['pred_f_central'])   # (n_steps, 3): T_0m, T_10m, T_20m
obs              = np.array(ns['obs'])               # (n_steps, 3)

# ---------------------------------------------------------------------------
# Load full model time series from T_out.dat
# ---------------------------------------------------------------------------
t_out_path = os.path.join(os.path.dirname(__file__), 'work', 'work0', 'Results', 'T_out.dat')
model_times, model_depths, T_matrix = read_t_out(t_out_path)

def nearest_depth_col(depths, target):
    return min(range(len(depths)), key=lambda i: abs(depths[i] - target))

col_0m  = nearest_depth_col(model_depths, -0.0)
col_10m = nearest_depth_col(model_depths, -10.0)
col_20m = nearest_depth_col(model_depths, -20.0)

# ---------------------------------------------------------------------------
# Load observations from stochObserver CSVs
# ---------------------------------------------------------------------------
obs_dir = os.path.join(os.path.dirname(__file__), 'stochObserver')
obs_t_0m,  obs_v_0m  = read_observer_csv(os.path.join(obs_dir, 'T_0m_real.csv'))
obs_t_10m, obs_v_10m = read_observer_csv(os.path.join(obs_dir, 'T_10m_real.csv'))
obs_t_20m, obs_v_20m = read_observer_csv(os.path.join(obs_dir, 'T_20m_real.csv'))

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
fig.suptitle('Simstrat Sequential Simulation: Model vs Observations', fontsize=13)

specs = [
    (axes[0], col_0m,  obs_t_0m,  obs_v_0m,  0,  '0 m'),
    (axes[1], col_10m, obs_t_10m, obs_v_10m, 1, '10 m'),
    (axes[2], col_20m, obs_t_20m, obs_v_20m, 2, '20 m'),
]

for ax, col, ot, ov, pred_col, label in specs:
    ax.plot(model_times, T_matrix[:, col], color='steelblue', lw=1.5, label='Model')
    ax.scatter(ot, ov, color='tomato', zorder=5, s=40, label='Observations')
    ax.scatter(analysis_times, pred_f_central[:, pred_col],
               marker='x', color='steelblue', zorder=6, s=50, label='Model @ obs time')
    ax.set_ylabel(f'T {label} (°C)')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.autofmt_xdate()

plt.tight_layout()
out_path = os.path.join(os.path.dirname(__file__), 'simulation_resultsV3.png')
plt.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")

# ---------------------------------------------------------------------------
# Zoomed figure: January 5
# ---------------------------------------------------------------------------
zoom_year  = analysis_times[0].year
zoom_start = datetime(zoom_year, 1, 4)
zoom_end   = datetime(zoom_year, 1, 7)

fig2, axes2 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
fig2.suptitle('Simstrat Sequential Simulation — Jan 5 zoom', fontsize=13)

specs2 = [
    (axes2[0], col_0m,  obs_t_0m,  obs_v_0m,  0, '0 m'),
    (axes2[1], col_10m, obs_t_10m, obs_v_10m, 1, '10 m'),
    (axes2[2], col_20m, obs_t_20m, obs_v_20m, 2, '20 m'),
]
for ax, col, ot, ov, pred_col, label in specs2:
    ax.plot(model_times, T_matrix[:, col], color='steelblue', lw=1.5, label='Model')
    ax.scatter(ot, ov, color='tomato', zorder=5, s=40, label='Observations')
    ax.scatter(analysis_times, pred_f_central[:, pred_col],
               marker='x', color='steelblue', zorder=6, s=50, label='Model @ obs time')
    ax.set_ylabel(f'T {label} (°C)')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(zoom_start, zoom_end)

axes2[2].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
fig2.autofmt_xdate()
plt.tight_layout()
out_zoom = os.path.join(os.path.dirname(__file__), 'simulation_results_jan5_zoom.png')
fig2.savefig(out_zoom, dpi=150)
print(f"Saved: {out_zoom}")

plt.show()
