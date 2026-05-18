import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── CONFIGURE HERE ────────────────────────────────────────────────────────────
LAKE      = "geneva"
YEAR      = 2025
MAX_DEPTH = None

LAKE_CONFIGS = {
    "upperlugano": {
        "label":         "Upper Lugano",
        "folder":        "upperlugano",
        "obs_path":      os.path.join(ROOT, "data", "T_obs_castagnola.csv"),
        "obs2_path":     os.path.join(ROOT, "data", "T_obs_gandria_new_raw.csv"),
        "obs2_label":    "gandria",
        "ref_date":      pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members":     20,
        "pf_mean_subdir": "results_daily_update",
    },
    "murten": {
        "label":         "Murten",
        "folder":        "murten",
        "obs_path":      os.path.join(ROOT, "data", "T_obs_murten.csv"),
        "obs2_path":     None,
        "obs2_label":    None,
        "ref_date":      pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members":     20,
        "pf_mean_subdir": "results_daily_update",
    },
    "geneva": {
        "label":         "Geneva",
        "folder":        "geneva",
        "obs_path":      os.path.join(ROOT, "data", "T_obs_geneva.csv"),
        "obs2_path":     None,
        "obs2_label":    None,
        "ref_date":      pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members":     20,
        "pf_mean_subdir": "old",
    },
}
# ─────────────────────────────────────────────────────────────────────────────

cfg           = LAKE_CONFIGS[LAKE]
LABEL         = cfg["label"]
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", cfg["folder"])
OBS_PATH      = cfg["obs_path"]
OBS2_PATH     = cfg["obs2_path"]
OBS2_LABEL    = cfg["obs2_label"]
REF_DATE      = cfg["ref_date"]
N_MEMBERS     = cfg["n_members"]
PF_MEAN_SUBDIR = cfg["pf_mean_subdir"]


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


def load_obs2_raw(path):
    with open(path, encoding="utf-8") as f:
        lines = [f.readline().rstrip("\n") for _ in range(22)]
    var_row   = lines[16].split(";")
    depth_row = lines[19].split(";")
    temp_col_depths = {}
    for i, (v, d) in enumerate(zip(var_row, depth_row)):
        if "T (Water)" in v:
            m = re.search(r"\((-?\d+\.?\d*)\s*m\)", d)
            if m:
                temp_col_depths[i] = abs(float(m.group(1)))
    selected_cols = [0] + list(temp_col_depths.keys())
    depth_names   = list(temp_col_depths.values())
    df = pd.read_csv(
        path, sep=";",
        skiprows=list(range(20)) + [21],
        header=0,
        usecols=selected_cols,
        na_values=["-", "", "x"],
        low_memory=False,
    )
    df.columns = ["time"] + depth_names
    df["time"] = pd.to_datetime(df["time"], format="%d.%m.%Y %H:%M:%S")
    df["time"] = df["time"].dt.tz_localize("Etc/GMT-1").dt.tz_convert("UTC")
    df = df.melt(id_vars=["time"], var_name="depth", value_name="value")
    df = df.dropna(subset=["value"])
    df["depth"] = df["depth"].astype(float)
    return df


def load_members(n, subpath):
    ms = []
    for i in range(1, n + 1):
        t = load_traj(os.path.join(ENSEMBLE_BASE, f"ensemble{i}", subpath))
        if t is not None:
            ms.append(t)
    return ms


def member_minmax(members, target_depth):
    """Return (common_index, min_series, max_series) across members at target_depth."""
    idx = members[0].index
    for m in members[1:]:
        idx = idx.intersection(m.index)
    stacked = np.column_stack([m.loc[idx, nearest_col(m, target_depth)].values for m in members])
    return idx, stacked.min(axis=1), stacked.max(axis=1)


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

obs2 = None
obs2_depths = None
if OBS2_PATH and os.path.exists(OBS2_PATH):
    obs2 = load_obs2_raw(OBS2_PATH)
    if YEAR is not None:
        obs2 = obs2[obs2["time"].dt.year == YEAR]
    obs2_depths = np.sort(obs2["depth"].unique())

# ── Load trajectories ─────────────────────────────────────────────────────────
# e0        : standard run (no DA)   → ensemble0/Results_PF/T_out_full.dat
# enkf_mean : EnKF assimilation mean → T_out_enkf_mean.dat
# pf_mean   : PF  assimilation mean  → results_daily_update/T_out_ens.dat

e0_traj             = load_traj(os.path.join(ENSEMBLE_BASE, "ensemble0", "Results_PF", "T_out_full.dat"))
enkf_mean_traj      = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_enkf_mean.dat"))
enkf_filt_mean_traj = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_enkf_filtered_mean.dat"))
pf_mean_traj        = load_traj(os.path.join(ENSEMBLE_BASE, PF_MEAN_SUBDIR, "T_out_ens.dat"))
pf_filt_mean_traj   = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_ens_filtered.dat"))

print(f"e0:                {'OK' if e0_traj              is not None else 'MISSING'}")
print(f"EnKF mean:         {'OK' if enkf_mean_traj       is not None else 'MISSING'}")
print(f"EnKF filt mean:    {'OK' if enkf_filt_mean_traj  is not None else 'MISSING'}")
print(f"PF mean:           {'OK' if pf_mean_traj         is not None else 'MISSING'}")
print(f"PF filt mean:      {'OK' if pf_filt_mean_traj    is not None else 'MISSING'}")

enkf_members      = load_members(N_MEMBERS, os.path.join("Results_EnKF",          "T_out_full.dat"))
enkf_filt_members = load_members(N_MEMBERS, os.path.join("Results_EnKF_filtered", "T_out_full.dat"))
pf_members        = load_members(N_MEMBERS, os.path.join("Results_PF",            "T_out_full.dat"))
print(f"EnKF members: {len(enkf_members)}   EnKF filt members: {len(enkf_filt_members)}   PF members: {len(pf_members)}")

_ref_traj = next((t for t in [e0_traj, enkf_mean_traj, enkf_filt_mean_traj, pf_mean_traj, pf_filt_mean_traj] if t is not None), None)
if _ref_traj is None:
    raise RuntimeError("No trajectory files found.")

# ── Plot 1 — time series per depth ───────────────────────────────────────────

_plot_depths = -obs_depths
fig, axes = plt.subplots(len(_plot_depths), 1, figsize=(14, 4 * len(_plot_depths)),
                         sharex=True, squeeze=False)
axes = axes[:, 0]

for ax, target_depth in zip(axes, _plot_depths):
    actual_depth = abs(nearest_col(_ref_traj, target_depth))

    nearest_obs_depth = obs_depths[np.argmin(np.abs(obs_depths - actual_depth))]
    obs_sub = obs[obs["depth"] == nearest_obs_depth]
    ax.scatter(obs_sub["time"], obs_sub["value"], s=1, color="tomato", zorder=5, alpha=0.2,
               label=f"obs ({nearest_obs_depth:.1f} m)")

    if obs2 is not None:
        nearest_obs2_depth = obs2_depths[np.argmin(np.abs(obs2_depths - actual_depth))]
        obs2_sub = obs2[obs2["depth"] == nearest_obs2_depth]
        ax.scatter(obs2_sub["time"], obs2_sub["value"], s=20, color="black", zorder=10, marker="x",
                   label=f"{OBS2_LABEL} ({nearest_obs2_depth:.1f} m)")

    '''if enkf_members:
        idx, mn, mx = member_minmax(enkf_members, target_depth)
        ax.fill_between(idx, mn, mx, color="mediumpurple", alpha=0.15, zorder=2, label="EnKF min–max")'''

    if enkf_filt_members:
        idx, mn, mx = member_minmax(enkf_filt_members, target_depth)
        ax.fill_between(idx, mn, mx, color="darkorchid", alpha=0.12, zorder=2, label="EnKF filt min–max")

    '''if pf_members:
        idx, mn, mx = member_minmax(pf_members, target_depth)
        ax.fill_between(idx, mn, mx, color="steelblue", alpha=0.15, zorder=2, label="PF min–max")'''

    if e0_traj is not None:
        col = nearest_col(e0_traj, target_depth)
        s = e0_traj[col].loc[~e0_traj[col].index.duplicated(keep="first")]
        ax.plot(s.index, s.values, color="dimgrey", lw=1.2, label="e0")

    if enkf_mean_traj is not None:
        col = nearest_col(enkf_mean_traj, target_depth)
        s = enkf_mean_traj[col].loc[~enkf_mean_traj[col].index.duplicated(keep="first")]
        ax.plot(s.index, s.values, color="mediumpurple", lw=1.5, zorder=7, label="EnKF mean")

    if enkf_filt_mean_traj is not None:
        col = nearest_col(enkf_filt_mean_traj, target_depth)
        s = enkf_filt_mean_traj[col].loc[~enkf_filt_mean_traj[col].index.duplicated(keep="first")]
        ax.plot(s.index, s.values, color="darkorchid", lw=1.5, zorder=7, label="EnKF filt mean")

    if pf_mean_traj is not None:
        col = nearest_col(pf_mean_traj, target_depth)
        s = pf_mean_traj[col].loc[~pf_mean_traj[col].index.duplicated(keep="first")]
        ax.plot(s.index, s.values, color="steelblue", lw=1.5, zorder=7, label="PF mean")

    if pf_filt_mean_traj is not None:
        col = nearest_col(pf_filt_mean_traj, target_depth)
        s = pf_filt_mean_traj[col].loc[~pf_filt_mean_traj[col].index.duplicated(keep="first")]
        ax.plot(s.index, s.values, color="teal", lw=1.5, zorder=7, label="PF filt mean")

    ax.set_ylabel("T (°C)")
    ax.set_title(f"T at {actual_depth:.0f} m depth")
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date")
if YEAR is not None:
    axes[0].set_xlim(pd.Timestamp(f"{YEAR}-01-01", tz="UTC"),
                     pd.Timestamp(f"{YEAR}-12-31", tz="UTC"))
fig.autofmt_xdate()
plt.tight_layout(rect=[0, 0, 0.82, 1])
plt.show()

# ── RMSE ──────────────────────────────────────────────────────────────────────

def _common_depths(obs_depths_arr, ref_df):
    col_to_best = {}
    for d in obs_depths_arr:
        col  = nearest_col(ref_df, -d)
        dist = abs(-d - col)
        if col not in col_to_best or dist < col_to_best[col][1]:
            col_to_best[col] = (d, dist)
    return np.array(sorted(v[0] for v in col_to_best.values()))


def compute_rmse_by_depth(traj, obs_df, depths_arr):
    rmses = []
    for d in depths_arr:
        col = nearest_col(traj, -d)
        obs_sub = obs_df[obs_df["depth"] == d].set_index("time")["value"].rename("obs")
        merged = traj[[col]].join(obs_sub, how="inner")
        if len(merged) == 0:
            rmses.append(np.nan)
        else:
            rmses.append(np.sqrt(np.mean((merged[col].values - merged["obs"].values) ** 2)))
    return rmses


_active = [t for t in [e0_traj, enkf_mean_traj, enkf_filt_mean_traj, pf_mean_traj, pf_filt_mean_traj] if t is not None]
common_obs_depths = _common_depths(obs_depths, _active[0])
for _ref in _active[1:]:
    common_obs_depths = np.intersect1d(common_obs_depths, _common_depths(obs_depths, _ref))

e0_rmses             = compute_rmse_by_depth(e0_traj,            obs, common_obs_depths) if e0_traj            is not None else None
enkf_rmses           = compute_rmse_by_depth(enkf_mean_traj,     obs, common_obs_depths) if enkf_mean_traj     is not None else None
enkf_filt_rmses      = compute_rmse_by_depth(enkf_filt_mean_traj, obs, common_obs_depths) if enkf_filt_mean_traj is not None else None
pf_rmses             = compute_rmse_by_depth(pf_mean_traj,       obs, common_obs_depths) if pf_mean_traj       is not None else None
pf_filt_rmses        = compute_rmse_by_depth(pf_filt_mean_traj,  obs, common_obs_depths) if pf_filt_mean_traj  is not None else None

# ── Print RMSE table ──────────────────────────────────────────────────────────

print(f"\nRMSE (°C) — {LABEL} {YEAR}")
header = f"{'depth':>8}" + (f"{'e0':>10}"               if e0_rmses             else "") \
                         + (f"{'EnKF mean':>12}"         if enkf_rmses           else "") \
                         + (f"{'EnKF filt mean':>16}"    if enkf_filt_rmses      else "") \
                         + (f"{'PF mean':>10}"           if pf_rmses             else "") \
                         + (f"{'PF filt mean':>14}"      if pf_filt_rmses        else "")
print(header)
for i, d in enumerate(common_obs_depths):
    row = f"{d:>8.1f} m"
    if e0_rmses:           row += f"  {e0_rmses[i]:>8.4f}"
    if enkf_rmses:         row += f"  {enkf_rmses[i]:>10.4f}"
    if enkf_filt_rmses:    row += f"  {enkf_filt_rmses[i]:>14.4f}"
    if pf_rmses:           row += f"  {pf_rmses[i]:>8.4f}"
    if pf_filt_rmses:      row += f"  {pf_filt_rmses[i]:>12.4f}"
    print(row)
totals_row = f"{'total':>10}"
if e0_rmses:           totals_row += f"  {np.nansum(e0_rmses):>8.4f}"
if enkf_rmses:         totals_row += f"  {np.nansum(enkf_rmses):>10.4f}"
if enkf_filt_rmses:    totals_row += f"  {np.nansum(enkf_filt_rmses):>14.4f}"
if pf_rmses:           totals_row += f"  {np.nansum(pf_rmses):>8.4f}"
if pf_filt_rmses:      totals_row += f"  {np.nansum(pf_filt_rmses):>12.4f}"
print(totals_row)

# ── Plot 2 — RMSE bar chart ───────────────────────────────────────────────────

comp_entries = []
if e0_rmses            is not None: comp_entries.append(("e0",                e0_rmses,           np.nansum(e0_rmses),           "dimgrey"))
if enkf_rmses          is not None: comp_entries.append(("EnKF\nmean",        enkf_rmses,         np.nansum(enkf_rmses),         "mediumpurple"))
if enkf_filt_rmses     is not None: comp_entries.append(("EnKF filt\nmean",   enkf_filt_rmses,    np.nansum(enkf_filt_rmses),    "darkorchid"))
if pf_rmses            is not None: comp_entries.append(("PF\nmean",          pf_rmses,           np.nansum(pf_rmses),           "steelblue"))
if pf_filt_rmses       is not None: comp_entries.append(("PF filt\nmean",     pf_filt_rmses,      np.nansum(pf_filt_rmses),      "teal"))
comp_entries.sort(key=lambda e: e[2], reverse=True)

ref_total  = np.nansum(e0_rmses) if e0_rmses is not None else comp_entries[0][2]
e0_xi      = next((xi for xi, e in enumerate(comp_entries) if e[1] is e0_rmses), None)
depth_cmap = plt.cm.viridis(np.linspace(0.9, 0.1, len(common_obs_depths)))
comp_x     = np.arange(len(comp_entries))
bottoms    = np.zeros(len(comp_entries))
seg_tops   = {}

fig2, ax2 = plt.subplots(figsize=(max(8, 4 * len(comp_entries)), 7))

for d_idx, d in reversed(list(enumerate(common_obs_depths))):
    vals = np.array([e[1][d_idx] if not np.isnan(e[1][d_idx]) else 0 for e in comp_entries])
    ax2.bar(comp_x, vals, bottom=bottoms, color=depth_cmap[d_idx], width=0.5, label=f"{d:.0f} m")
    bottoms += vals
    seg_tops[d_idx] = bottoms.copy()

for d_idx in range(len(common_obs_depths)):
    ax2.plot(comp_x, seg_tops[d_idx], color=depth_cmap[d_idx], lw=1.2, alpha=0.7, zorder=5)

for xi, (lbl, rmses_e, total, edgecolor) in enumerate(comp_entries):
    ax2.bar(xi, total, bottom=0, color="none", edgecolor=edgecolor, lw=2, width=0.5)
    gain = (total - ref_total) / ref_total * 100
    ann  = f"{total:.3f}°C" if xi == e0_xi else f"{total:.3f}°C\n{gain:+.1f}%"
    ax2.text(xi, total + 0.01 * ref_total, ann, ha="center", va="bottom", fontsize=9)

    prev = 0.0
    for d_idx in range(len(common_obs_depths) - 1, -1, -1):
        top = seg_tops[d_idx][xi]
        mid = (prev + top) / 2
        val = rmses_e[d_idx] if not np.isnan(rmses_e[d_idx]) else 0
        if xi == e0_xi or e0_rmses is None or np.isnan(e0_rmses[d_idx]) or e0_rmses[d_idx] == 0:
            ann_seg = f"{val:.3f}"
        else:
            depth_gain = (val - e0_rmses[d_idx]) / e0_rmses[d_idx] * 100
            ann_seg = f"{val:.3f} / {depth_gain:+.1f}%"
        ax2.text(xi, mid, ann_seg, ha="center", va="center", fontsize=7, color="dimgrey")
        prev = top

ax2.set_xticks(comp_x)
ax2.set_xticklabels([e[0] for e in comp_entries], fontsize=10)
ax2.set_ylabel("RMSE (°C)")
ax2.set_title(f"RMSE comparison — {LABEL} {YEAR}")
handles, lbls = ax2.get_legend_handles_labels()
ax2.legend(handles[::-1], lbls[::-1], fontsize=8, loc="upper left",
           bbox_to_anchor=(1.01, 1), borderaxespad=0, title="depth")
ax2.grid(True, axis="y", alpha=0.3)
plt.tight_layout(rect=[0, 0, 0.85, 1])
plt.show()
