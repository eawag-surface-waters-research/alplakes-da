import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", "upperlugano")
OBS_PATH      = os.path.join(ROOT, "data", "T_obs_castagnola.csv")
N_MEMBERS     = 20
REF_DATE      = pd.Timestamp("1981-01-01", tz="UTC")
PF_RESULTS    = "Results_PF_resampled"
OUTPUT_DIR    = os.path.join(ENSEMBLE_BASE, "results_resampled")
DEPTHS        = [-1, -5, -9, -15, -19, -40]
SUMMER_MONTHS = None  # set to [6, 7, 8] to filter to summer only


def load_traj(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    df.columns = df.columns.astype(float)
    return df


def nearest_col(df, target):
    return df.columns[np.argmin(np.abs(df.columns - target))]


def summer(df):
    if SUMMER_MONTHS is None:
        return df
    return df[df.index.month.isin(SUMMER_MONTHS)]


# ── Load data ─────────────────────────────────────────────────────────────────

members = []
for i in range(1, N_MEMBERS + 1):
    path = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "T_out_full.dat")
    df = load_traj(path)
    if df is not None:
        members.append(summer(df))

print(f"Loaded {len(members)} resampled members")
if not members:
    raise FileNotFoundError(f"No T_out_full.dat found under {ENSEMBLE_BASE}/ensemble*/Results_PF_resampled/")

best_traj    = load_traj(os.path.join(OUTPUT_DIR, "T_out_best.dat"))
ens_traj     = load_traj(os.path.join(OUTPUT_DIR, "T_out_ens.dat"))
persist_traj = load_traj(os.path.join(OUTPUT_DIR, "T_out_persist.dat"))

if best_traj    is not None: best_traj    = summer(best_traj)
if ens_traj     is not None: ens_traj     = summer(ens_traj)
if persist_traj is not None: persist_traj = summer(persist_traj)

obs = pd.read_csv(OBS_PATH, parse_dates=["time"])
obs["time"] = pd.to_datetime(obs["time"], utc=True)
if SUMMER_MONTHS is not None:
    obs = obs[obs["time"].dt.month.isin(SUMMER_MONTHS)]
obs = (obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"]
          .mean().reset_index())
obs_depths = np.sort(obs["depth"].unique())

x_min = min(m.index.min() for m in members)
x_max = max(m.index.max() for m in members)

# ── Plot 1: ensemble spread + trajectories ────────────────────────────────────

fig, axes = plt.subplots(len(DEPTHS), 1, figsize=(14, 4 * len(DEPTHS)), sharex=True)
fig.suptitle("Weighted resampling PF — Upper Lugano (summer: Jun–Aug)", fontsize=13)

for ax, target_depth in zip(axes, DEPTHS):
    actual_depth = abs(nearest_col(members[0], target_depth))

    # ensemble spread
    aligned = pd.concat(
        [m[[nearest_col(m, target_depth)]].rename(columns={nearest_col(m, target_depth): j})
         for j, m in enumerate(members)], axis=1
    )
    p5  = aligned.quantile(0.05, axis=1)
    p95 = aligned.quantile(0.95, axis=1)
    ax.fill_between(aligned.index, p5, p95, color="orange", alpha=0.2, label="5–95th pct")

    for j, m in enumerate(members):
        mc = nearest_col(m, target_depth)
        ax.plot(m.index, m[mc].values, color="orange", lw=0.4, alpha=0.4,
                label="members" if j == 0 else None)

    # trajectories
    for traj, color, ls, lbl in [
        (ens_traj,     "darkorange", "-",  "ens mean"),
        (best_traj,    "crimson",    "--", "best (hindsight)"),
        (persist_traj, "seagreen",   "--", "persistence"),
    ]:
        if traj is not None:
            tc = nearest_col(traj, target_depth)
            ax.plot(traj.index, traj[tc].values, color=color, lw=1.5, ls=ls, zorder=7, label=lbl)

    # obs
    nearest_obs_depth = obs_depths[np.argmin(np.abs(obs_depths - actual_depth))]
    obs_sub = obs[obs["depth"] == nearest_obs_depth]
    ax.scatter(obs_sub["time"], obs_sub["value"], s=2, color="tomato", alpha=0.5,
               zorder=8, label=f"obs ({nearest_obs_depth:.1f} m)")

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(6.8, 8.5)
    ax.set_ylabel("T (°C)")
    ax.set_title(f"{actual_depth:.0f} m depth")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date")
fig.autofmt_xdate()
plt.tight_layout()
plt.show()

# ── Plot 2: ensemble spread width over time (std across members) ──────────────

fig2, axes2 = plt.subplots(len(DEPTHS), 1, figsize=(14, 3 * len(DEPTHS)), sharex=True)
fig2.suptitle("Ensemble spread (std) — weighted resampling (summer: Jun–Aug)", fontsize=13)

for ax, target_depth in zip(axes2, DEPTHS):
    actual_depth = abs(nearest_col(members[0], target_depth))

    aligned = pd.concat(
        [m[[nearest_col(m, target_depth)]].rename(columns={nearest_col(m, target_depth): j})
         for j, m in enumerate(members)], axis=1
    )
    std = aligned.std(axis=1)
    ax.plot(std.index, std.values, color="darkorange", lw=1.2)
    ax.fill_between(std.index, 0, std.values, color="orange", alpha=0.3)
    ax.set_xlim(x_min, x_max)
    ax.set_ylabel("std (°C)")
    ax.set_title(f"{actual_depth:.0f} m depth")
    ax.grid(True, alpha=0.3)

axes2[-1].set_xlabel("Date")
fig2.autofmt_xdate()
plt.tight_layout()
plt.show()
