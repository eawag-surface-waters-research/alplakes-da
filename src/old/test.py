import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", "upperlugano")
OBS_PATH      = os.path.join(ROOT, "data", "T_obs_castagnola.csv")
N_MEMBERS     = 20
REF_DATE      = pd.Timestamp("1981-01-01", tz="UTC")
PF_RESULTS    = "Results_PF"
DEPTHS        = [-1, -5, -9, -15, -19, -40]
SUMMER_MONTHS = [6, 7, 8]


def load_traj(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df = df[~df.index.duplicated(keep="first")]
    df.columns = df.columns.astype(float)
    return df


def load_traj_split(path):
    """Load T_out_full.dat and split into (daily, weekly) at the first backwards jump."""
    if not os.path.exists(path):
        return None, None
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df.columns = df.columns.astype(float)
    # find first row where time goes backwards
    backwards = df.index.to_series().diff() < pd.Timedelta(0)
    if not backwards.any():
        return df, None
    reset = backwards.idxmax()
    reset_pos = df.index.get_loc(reset)
    if hasattr(reset_pos, '__len__'):  # slice or array from duplicate index
        reset_pos = reset_pos if isinstance(reset_pos, int) else int(np.argmax(reset_pos))
    daily  = df.iloc[:reset_pos]
    weekly = df.iloc[reset_pos:]
    daily  = daily[~daily.index.duplicated(keep="first")]
    weekly = weekly[~weekly.index.duplicated(keep="first")]
    return daily, weekly


def nearest_col(df, target):
    return df.columns[np.argmin(np.abs(df.columns - target))]


def summer(df):
    return df[df.index.month.isin(SUMMER_MONTHS)]


# Load PF full trajectories — split daily vs weekly at the backwards-time jump
members_daily, members_weekly = [], []
for i in range(1, N_MEMBERS + 1):
    path = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "T_out_full.dat")
    d, w = load_traj_split(path)
    if d is not None:
        members_daily.append(summer(d))
    if w is not None:
        members_weekly.append(summer(w))

print(f"Loaded {len(members_daily)} daily / {len(members_weekly)} weekly PF trajectories")
if not members_daily:
    raise FileNotFoundError(f"No T_out_full.dat found under {ENSEMBLE_BASE}/ensemble*/Results_PF/")

# Load obs
obs = pd.read_csv(OBS_PATH, parse_dates=["time"])
obs["time"] = pd.to_datetime(obs["time"], utc=True)
obs = obs[obs["time"].dt.month.isin(SUMMER_MONTHS)]
obs = (obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"]
          .mean().reset_index())
obs_depths = np.sort(obs["depth"].unique())

# Plot
fig, axes = plt.subplots(len(DEPTHS), 1, figsize=(14, 4 * len(DEPTHS)), sharex=True)
fig.suptitle("PF ensemble spread — Upper Lugano (summer: Jun–Aug)", fontsize=13)

for ax, target_depth in zip(axes, DEPTHS):
    actual_depth = abs(nearest_col(members_daily[0], target_depth))

    for j, m in enumerate(members_daily):
        mc = nearest_col(m, target_depth)
        ax.plot(m.index, m[mc].values, color="orange", lw=0.5, alpha=0.5,
                label="daily members" if j == 0 else None)

    for j, m in enumerate(members_weekly):
        mc = nearest_col(m, target_depth)
        ax.plot(m.index, m[mc].values, color="steelblue", lw=0.5, alpha=0.5,
                label="weekly members" if j == 0 else None)

    # ensemble means
    def ens_mean(members):
        aligned = pd.concat(
            [m[[nearest_col(m, target_depth)]].rename(columns={nearest_col(m, target_depth): j})
             for j, m in enumerate(members)], axis=1
        )
        return aligned.index, aligned.mean(axis=1)

    t, mean = ens_mean(members_daily)
    ax.plot(t, mean, color="darkorange", lw=1.5, label="daily mean")
    if members_weekly:
        t, mean = ens_mean(members_weekly)
        ax.plot(t, mean, color="navy", lw=1.5, label="weekly mean")

    # obs
    nearest_obs_depth = obs_depths[np.argmin(np.abs(obs_depths - actual_depth))]
    obs_sub = obs[obs["depth"] == nearest_obs_depth]
    ax.scatter(obs_sub["time"], obs_sub["value"], s=2, color="tomato", zorder=5, alpha=0.4,
               label=f"obs ({nearest_obs_depth:.1f} m)")

    ax.set_ylabel("T (°C)")
    ax.set_title(f"{actual_depth:.0f} m depth")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date")
fig.autofmt_xdate()
plt.tight_layout()
plt.show()
