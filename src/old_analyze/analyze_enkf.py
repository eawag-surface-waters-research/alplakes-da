import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── CONFIGURE HERE ────────────────────────────────────────────────────────────
LAKE      = "upperlugano"
YEAR      = 2025       # None = all years
MAX_DEPTH = None       # restrict to depths <= this (m); None = all depths

LAKE_CONFIGS = {
    "upperlugano": {
        "label":    "Upper Lugano",
        "folder":   "upperlugano",
        "obs_path": os.path.join(ROOT, "data", "T_obs_castagnola.csv"),
        "ref_date": pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members": 20,
        "depths":   [-1, -5, -9, -15, -19, -40],
    },
    "murten": {
        "label":    "Murten",
        "folder":   "murten",
        "obs_path": os.path.join(ROOT, "data", "T_obs_murten.csv"),
        "ref_date": pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members": 20,
        "depths":   [-1, -5, -10, -20, -40],
    },
    "geneva": {
        "label":    "Geneva",
        "folder":   "geneva",
        "obs_path": os.path.join(ROOT, "data", "T_obs_geneva.csv"),
        "ref_date": pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members": 20,
        "depths":   [-1, -5, -10, -21, -24, -25, -30],
    },
}
# ─────────────────────────────────────────────────────────────────────────────

cfg           = LAKE_CONFIGS[LAKE]
LABEL         = cfg["label"]
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", cfg["folder"])
OBS_PATH      = cfg["obs_path"]
REF_DATE      = cfg["ref_date"]
N_MEMBERS     = cfg["n_members"]
DEPTHS        = [d for d in cfg["depths"] if MAX_DEPTH is None or abs(d) <= MAX_DEPTH]


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_traj(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = (REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")).dt.round("1h")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df = df[~df.index.duplicated(keep="first")]
    df.columns = df.columns.astype(float)
    return df


def nearest_col(df, target):
    return df.columns[np.argmin(np.abs(df.columns - target))]


# ── Load observations ─────────────────────────────────────────────────────────

obs = pd.read_csv(OBS_PATH, parse_dates=["time"])
obs["time"] = pd.to_datetime(obs["time"], utc=True)
obs["depth"] = pd.to_numeric(obs["depth"])
obs = obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"].mean().reset_index()
obs["depth"] = obs["depth"].replace(0.5, 0.0)
if YEAR is not None:
    obs = obs[obs["time"].dt.year == YEAR]
obs_depths = np.sort(obs["depth"].unique())
if MAX_DEPTH is not None:
    obs_depths = obs_depths[obs_depths <= MAX_DEPTH]

# ── Load trajectories ─────────────────────────────────────────────────────────

enkf_ctrl = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_enkf_ctrl.dat"))
enkf_mean = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_enkf_mean.dat"))

members = []
for i in range(1, N_MEMBERS + 1):
    t = load_traj(os.path.join(ENSEMBLE_BASE, f"ensemble{i}", "Results_EnKF", "T_out_full.dat"))
    if t is not None:
        members.append(t)
print(f"Loaded enkf_ctrl: {enkf_ctrl.index[0].date()} → {enkf_ctrl.index[-1].date()}" if enkf_ctrl is not None else "Missing enkf_ctrl")
print(f"Loaded enkf_mean: {enkf_mean.index[0].date()} → {enkf_mean.index[-1].date()}" if enkf_mean is not None else "Missing enkf_mean")
print(f"Loaded {len(members)} member full trajectories")

# ── RMSE helpers ──────────────────────────────────────────────────────────────

def _common_depths(obs_depths_arr, ref_df):
    col_to_best = {}
    for d in obs_depths_arr:
        col  = nearest_col(ref_df, -d)
        dist = abs(-d - col)
        if col not in col_to_best or dist < col_to_best[col][1]:
            col_to_best[col] = (d, dist)
    return np.array(sorted(v[0] for v in col_to_best.values()))


def rmse_by_depth(traj, obs_df, depths_arr):
    rmses = []
    for d in depths_arr:
        col     = nearest_col(traj, -d)
        obs_sub = obs_df[obs_df["depth"] == d].set_index("time")["value"].rename("obs")
        merged  = traj[[col]].join(obs_sub, how="inner")
        if len(merged) == 0:
            rmses.append(np.nan)
        else:
            rmses.append(np.sqrt(np.mean((merged[col].values - merged["obs"].values) ** 2)))
    return rmses


_ref_dfs = [t for t in [enkf_ctrl, enkf_mean] if t is not None]
if not _ref_dfs:
    raise RuntimeError("No trajectory files found.")

common_depths = _common_depths(obs_depths, _ref_dfs[0])
for _ref in _ref_dfs[1:]:
    common_depths = np.intersect1d(common_depths, _common_depths(obs_depths, _ref))

depth_cmap = plt.cm.viridis(np.linspace(0.9, 0.1, len(common_depths)))

ctrl_rmses = rmse_by_depth(enkf_ctrl, obs, common_depths) if enkf_ctrl is not None else None
mean_rmses = rmse_by_depth(enkf_mean, obs, common_depths) if enkf_mean is not None else None

member_rmses_arr  = None
member_rmses_mean = None
if members:
    _all_mr           = np.array([rmse_by_depth(m, obs, common_depths) for m in members])
    member_rmses_arr  = _all_mr
    member_rmses_mean = np.nanmean(_all_mr, axis=0).tolist()

# ── Print RMSE table ──────────────────────────────────────────────────────────

print(f"\nRMSE (°C) — {LABEL} {YEAR}")
header = f"{'depth':>8}" + (f"{'ctrl':>10}" if ctrl_rmses else "") \
                         + (f"{'EnKF mean':>12}" if mean_rmses else "") \
                         + (f"{'EnKF mbrs':>12}" if member_rmses_mean else "")
print(header)
for i, d in enumerate(common_depths):
    row = f"{d:>8.1f} m"
    if ctrl_rmses:        row += f"  {ctrl_rmses[i]:>8.4f}"
    if mean_rmses:        row += f"  {mean_rmses[i]:>10.4f}"
    if member_rmses_mean: row += f"  {member_rmses_mean[i]:>10.4f}"
    print(row)
totals_row = f"{'total':>10}"
if ctrl_rmses:        totals_row += f"  {np.nansum(ctrl_rmses):>8.4f}"
if mean_rmses:        totals_row += f"  {np.nansum(mean_rmses):>10.4f}"
if member_rmses_mean: totals_row += f"  {np.nansum(member_rmses_mean):>10.4f}"
print(totals_row)

# ── Plot 1 — time series per depth with ensemble spread ──────────────────────

_plot_depths = -obs_depths
fig, axes = plt.subplots(len(_plot_depths), 1, figsize=(14, 4 * len(_plot_depths)),
                         sharex=True, squeeze=False)
axes = axes[:, 0]

for ax, target in zip(axes, _plot_depths):
    actual = abs(target)
    nearest_obs_d = obs_depths[np.argmin(np.abs(obs_depths - actual))]
    obs_sub = obs[obs["depth"] == nearest_obs_d]
    ax.scatter(obs_sub["time"], obs_sub["value"], s=1, color="tomato", alpha=0.25, zorder=5,
               label=f"obs ({nearest_obs_d:.1f} m)")

    if enkf_ctrl is not None:
        col = nearest_col(enkf_ctrl, target)
        s   = enkf_ctrl[col]
        ax.plot(s.index, s.values, color="dimgrey", lw=1.3, label="ctrl (no DA)")

    if members:
        col    = nearest_col(members[0], target)
        stacks = np.column_stack([m[nearest_col(m, target)].values for m in members])
        idx    = members[0].index
        mu     = stacks.mean(axis=1)
        sigma  = stacks.std(axis=1, ddof=1)
        ax.fill_between(idx, mu - sigma, mu + sigma,
                        color="darkorange", alpha=0.20, zorder=3, label="±1σ spread")

    if enkf_mean is not None:
        col = nearest_col(enkf_mean, target)
        s   = enkf_mean[col]
        ax.plot(s.index, s.values, color="darkorange", lw=1.6, zorder=7, label="EnKF mean")

    ax.set_ylabel("T (°C)")
    ax.set_title(f"{actual:.0f} m depth")
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date")
if YEAR is not None:
    axes[0].set_xlim(pd.Timestamp(f"{YEAR}-01-01", tz="UTC"),
                     pd.Timestamp(f"{YEAR}-12-31", tz="UTC"))
fig.suptitle(f"Temperature — {LABEL} {YEAR}", y=1.002)
fig.autofmt_xdate()
plt.tight_layout(rect=[0, 0, 0.82, 1])
plt.show()

# ── Plot 2 — RMSE comparison (stacked bar) ───────────────────────────────────

entries = []
if ctrl_rmses is not None:        entries.append(("ctrl\n(no DA)",    ctrl_rmses,        np.nansum(ctrl_rmses),        "dimgrey"))
if mean_rmses is not None:        entries.append(("EnKF\nmean",       mean_rmses,        np.nansum(mean_rmses),        "darkorange"))
if member_rmses_mean is not None: entries.append(("EnKF\nmembers",    member_rmses_mean, np.nansum(member_rmses_mean), "steelblue"))
entries.sort(key=lambda e: e[2], reverse=True)

ref_total = entries[0][2]
comp_x    = np.arange(len(entries))
bottoms   = np.zeros(len(entries))
seg_tops  = {}

fig2, ax2 = plt.subplots(figsize=(max(8, 4 * len(entries)), 7))

for d_idx, d in reversed(list(enumerate(common_depths))):
    vals = np.array([e[1][d_idx] if not np.isnan(e[1][d_idx]) else 0 for e in entries])
    ax2.bar(comp_x, vals, bottom=bottoms, color=depth_cmap[d_idx], width=0.5, label=f"{d:.0f} m")
    bottoms          += vals
    seg_tops[d_idx]   = bottoms.copy()

for d_idx in range(len(common_depths)):
    ax2.plot(comp_x, seg_tops[d_idx], color=depth_cmap[d_idx], lw=1.2, alpha=0.7, zorder=5)

for xi, (lbl, rmses, total, edgecolor) in enumerate(entries):
    ax2.bar(xi, total, bottom=0, color="none", edgecolor=edgecolor, lw=2, width=0.5)
    if lbl == "EnKF\nmembers" and member_rmses_arr is not None:
        member_totals = np.nansum(member_rmses_arr, axis=1)
        ax2.errorbar(xi, total, yerr=member_totals.std(), fmt="none",
                     color=edgecolor, capsize=6, lw=2, zorder=10)
    gain  = (total - ref_total) / ref_total * 100
    ann   = f"{total:.3f}°C" if xi == 0 else f"{total:.3f}°C\n{gain:+.1f}%"
    ax2.text(xi, total + 0.01 * ref_total, ann, ha="center", va="bottom", fontsize=9)

    prev = 0.0
    for d_idx in range(len(common_depths) - 1, -1, -1):
        top = seg_tops[d_idx][xi]
        mid = (prev + top) / 2
        val = rmses[d_idx] if not np.isnan(rmses[d_idx]) else 0
        ax2.text(xi, mid, f"{val:.3f}", ha="center", va="center", fontsize=7, color="dimgrey")
        prev = top

ax2.set_xticks(comp_x)
ax2.set_xticklabels([e[0] for e in entries], fontsize=10)
ax2.set_ylabel("RMSE (°C)")
ax2.set_title(f"RMSE comparison — {LABEL} {YEAR}")
handles, lbls = ax2.get_legend_handles_labels()
ax2.legend(handles[::-1], lbls[::-1], fontsize=8, loc="upper left",
           bbox_to_anchor=(1.01, 1), borderaxespad=0, title="depth")
ax2.grid(True, axis="y", alpha=0.3)
plt.tight_layout(rect=[0, 0, 0.85, 1])
plt.show()
