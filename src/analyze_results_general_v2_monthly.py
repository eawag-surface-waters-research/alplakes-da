import os
import re
import calendar
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── CONFIGURE HERE ────────────────────────────────────────────────────────────
LAKE            = "upperlugano"
YEAR            = 2025
MAX_DEPTH       = None
PLOT_TIMESERIES = True   # True → one time-series figure per month (can be many)

LAKE_CONFIGS = {
    "upperlugano": {
        "label":          "Upper Lugano",
        "folder":         "upperlugano",
        "obs_path":       os.path.join(ROOT, "data", "T_obs_castagnola.csv"),
        "obs2_path":      os.path.join(ROOT, "data", "T_obs_gandria_new_raw.csv"),
        "obs2_label":     "gandria",
        "ref_date":       pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members":      20,
        "pf_mean_subdir": "results_daily_update",
        "openda_enkf_dir":   os.path.join(ROOT, "OpenDA_Simstrat", "work_enkf"),
        "openda_ensr_dir":   os.path.join(ROOT, "OpenDA_Simstrat", "work_ensr"),
        "n_openda_members":  20,
    },
    "murten": {
        "label":          "Murten",
        "folder":         "murten",
        "obs_path":       os.path.join(ROOT, "data", "T_obs_murten.csv"),
        "obs2_path":      None,
        "obs2_label":     None,
        "ref_date":       pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members":      20,
        "pf_mean_subdir": "results_daily_update",
    },
    "geneva": {
        "label":          "Geneva",
        "folder":         "geneva",
        "obs_path":       os.path.join(ROOT, "data", "T_obs_geneva.csv"),
        "obs2_path":      None,
        "obs2_label":     None,
        "ref_date":       pd.Timestamp("1981-01-01", tz="UTC"),
        "n_members":      20,
        "pf_mean_subdir": "old",
    },
}
# ─────────────────────────────────────────────────────────────────────────────

cfg            = LAKE_CONFIGS[LAKE]
LABEL          = cfg["label"]
ENSEMBLE_BASE  = os.path.join(ROOT, "assimilation", cfg["folder"])
OBS_PATH       = cfg["obs_path"]
OBS2_PATH      = cfg["obs2_path"]
OBS2_LABEL     = cfg["obs2_label"]
REF_DATE       = cfg["ref_date"]
N_MEMBERS      = cfg["n_members"]
PF_MEAN_SUBDIR = cfg["pf_mean_subdir"]
OPENDA_DIR     = cfg.get("openda_enkf_dir")
OPENDA_ENSR_DIR = cfg.get("openda_ensr_dir")
N_OPENDA       = cfg.get("n_openda_members", 20)

MONTH_NAMES = [calendar.month_abbr[m] for m in range(1, 13)]


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
    idx = members[0].index
    for m in members[1:]:
        idx = idx.intersection(m.index)
    stacked = np.column_stack([m.loc[idx, nearest_col(m, target_depth)].values for m in members])
    return idx, stacked.min(axis=1), stacked.max(axis=1)


def load_openda_members(work_dir, n):
    members = []
    for i in range(1, n + 1):
        path = os.path.join(work_dir, f"work{i}", "Results", "T_out.dat")
        t = load_traj(path)
        if t is not None:
            members.append(t)
    return members


def openda_ensemble_stats(members):
    if not members:
        return None, None, None
    idx = members[0].index
    for m in members[1:]:
        idx = idx.intersection(m.index)
    cols = members[0].columns
    stacked = np.stack([m.loc[idx].values for m in members], axis=0)
    return (
        pd.DataFrame(stacked.mean(axis=0), index=idx, columns=cols),
        pd.DataFrame(stacked.min(axis=0),  index=idx, columns=cols),
        pd.DataFrame(stacked.max(axis=0),  index=idx, columns=cols),
    )


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

openda_members = load_openda_members(OPENDA_DIR, N_OPENDA) if OPENDA_DIR else []
openda_mean_traj, openda_min_traj, openda_max_traj = openda_ensemble_stats(openda_members)
print(f"OpenDA EnKF members: {len(openda_members)}   mean: {'OK' if openda_mean_traj is not None else 'MISSING'}")

openda_ensr_members = load_openda_members(OPENDA_ENSR_DIR, N_OPENDA) if OPENDA_ENSR_DIR else []
openda_ensr_mean_traj, openda_ensr_min_traj, openda_ensr_max_traj = openda_ensemble_stats(openda_ensr_members)
print(f"OpenDA EnSR members: {len(openda_ensr_members)}   mean: {'OK' if openda_ensr_mean_traj is not None else 'MISSING'}")

enkf_members      = load_members(N_MEMBERS, os.path.join("Results_EnKF",          "T_out_full.dat"))
enkf_filt_members = load_members(N_MEMBERS, os.path.join("Results_EnKF_filtered", "T_out_full.dat"))
pf_members        = load_members(N_MEMBERS, os.path.join("Results_PF",            "T_out_full.dat"))
print(f"EnKF members: {len(enkf_members)}   EnKF filt: {len(enkf_filt_members)}   PF members: {len(pf_members)}")

_ref_traj = next((t for t in [e0_traj, enkf_mean_traj, enkf_filt_mean_traj,
                               pf_mean_traj, pf_filt_mean_traj, openda_mean_traj,
                               openda_ensr_mean_traj]
                  if t is not None), None)
if _ref_traj is None:
    raise RuntimeError("No trajectory files found.")


# ── RMSE helpers ──────────────────────────────────────────────────────────────

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
        merged  = traj[[col]].join(obs_sub, how="inner")
        if len(merged) == 0:
            rmses.append(np.nan)
        else:
            rmses.append(np.sqrt(np.mean((merged[col].values - merged["obs"].values) ** 2)))
    return rmses


def monthly_rmse(traj, obs_df, depths_arr):
    """Return {month: [rmse_per_depth]} for months 1-12. None if traj is None."""
    if traj is None:
        return None
    result = {}
    for m in range(1, 13):
        traj_m = traj[traj.index.month == m]
        obs_m  = obs_df[obs_df["time"].dt.month == m]
        if len(traj_m) == 0 or len(obs_m) == 0:
            result[m] = [np.nan] * len(depths_arr)
        else:
            result[m] = compute_rmse_by_depth(traj_m, obs_m, depths_arr)
    return result


def to_matrix(monthly_dict):
    """Convert {month: [rmse]} → ndarray (n_depths, 12)."""
    return np.column_stack([monthly_dict[m] for m in range(1, 13)])


# ── Compute common depths and monthly RMSE ────────────────────────────────────

_active = [t for t in [e0_traj, enkf_mean_traj, enkf_filt_mean_traj,
                        pf_mean_traj, pf_filt_mean_traj, openda_mean_traj,
                        openda_ensr_mean_traj]
           if t is not None]
common_obs_depths = _common_depths(obs_depths, _active[0])
for _ref in _active[1:]:
    common_obs_depths = np.intersect1d(common_obs_depths, _common_depths(obs_depths, _ref))

e0_mo          = monthly_rmse(e0_traj,            obs, common_obs_depths)
enkf_mo        = monthly_rmse(enkf_mean_traj,     obs, common_obs_depths)
enkf_filt_mo   = monthly_rmse(enkf_filt_mean_traj, obs, common_obs_depths)
pf_mo          = monthly_rmse(pf_mean_traj,       obs, common_obs_depths)
pf_filt_mo     = monthly_rmse(pf_filt_mean_traj,  obs, common_obs_depths)
openda_mo      = monthly_rmse(openda_mean_traj,      obs, common_obs_depths)
openda_ensr_mo = monthly_rmse(openda_ensr_mean_traj, obs, common_obs_depths)

# Collect active entries: (label, monthly_dict, color)
entries = []
if e0_mo          is not None: entries.append(("e0",               e0_mo,          "dimgrey"))
if enkf_mo        is not None: entries.append(("EnKF mean",        enkf_mo,        "mediumpurple"))
if enkf_filt_mo   is not None: entries.append(("EnKF filt mean",   enkf_filt_mo,   "darkorchid"))
if pf_mo          is not None: entries.append(("PF mean",          pf_mo,          "steelblue"))
if pf_filt_mo     is not None: entries.append(("PF filt mean",     pf_filt_mo,     "teal"))
if openda_mo      is not None: entries.append(("OpenDA EnKF",      openda_mo,      "darkorange"))
if openda_ensr_mo is not None: entries.append(("OpenDA EnSR",      openda_ensr_mo, "forestgreen"))


# ── Print monthly RMSE tables ─────────────────────────────────────────────────

for lbl, mo, _ in entries:
    print(f"\nMonthly RMSE (°C) — {lbl} — {LABEL} {YEAR}")
    header = f"{'depth':>8}  " + "  ".join(f"{mn:>6}" for mn in MONTH_NAMES) + "  {'total':>7}"
    print(header)
    mat = to_matrix(mo)
    for i, d in enumerate(common_obs_depths):
        row_vals = mat[i, :]
        row = f"{d:>8.1f} m  " + "  ".join(f"{v:>6.3f}" if not np.isnan(v) else f"{'--':>6}" for v in row_vals)
        row += f"  {np.nansum(row_vals):>7.3f}"
        print(row)
    col_totals = np.nansum(mat, axis=0)
    print(f"{'total':>10}  " + "  ".join(f"{v:>6.3f}" for v in col_totals) +
          f"  {np.nansum(col_totals):>7.3f}")


# ── Plot 0 — Full-year time series per depth ─────────────────────────────────

_ts_depths = -obs_depths
fig0, axes0 = plt.subplots(len(_ts_depths), 1,
                            figsize=(14, 4 * len(_ts_depths)),
                            sharex=True, squeeze=False)
axes0 = axes0[:, 0]
fig0.suptitle(f"Temperature time series — {LABEL} {YEAR}", fontsize=12)

for _ax0, _td in zip(axes0, _ts_depths):
    _actual_d = abs(nearest_col(_ref_traj, _td))
    _nearest_obs_d = obs_depths[np.argmin(np.abs(obs_depths - _actual_d))]
    _obs_sub = obs[obs["depth"] == _nearest_obs_d]
    _ax0.scatter(_obs_sub["time"], _obs_sub["value"], s=1, color="tomato",
                 zorder=5, alpha=0.3, label=f"obs ({_nearest_obs_d:.1f} m)")

    for _traj0, _color0, _lbl0 in [
        (e0_traj,               "dimgrey",      "e0"),
        (enkf_mean_traj,        "mediumpurple", "EnKF mean"),
        (enkf_filt_mean_traj,   "darkorchid",   "EnKF filt mean"),
        (pf_mean_traj,          "steelblue",    "PF mean"),
        (pf_filt_mean_traj,     "teal",         "PF filt mean"),
        (openda_mean_traj,      "darkorange",   "OpenDA EnKF mean"),
        (openda_ensr_mean_traj, "forestgreen",  "OpenDA EnSR mean"),
    ]:
        if _traj0 is not None:
            _col0 = nearest_col(_traj0, _td)
            _s0 = _traj0[_col0].loc[~_traj0[_col0].index.duplicated(keep="first")]
            _ax0.plot(_s0.index, _s0.values, lw=1.5, color=_color0, label=_lbl0)

    if openda_mean_traj is not None:
        _col0 = nearest_col(openda_min_traj, _td)
        _ax0.fill_between(openda_min_traj.index,
                          openda_min_traj[_col0], openda_max_traj[_col0],
                          color="darkorange", alpha=0.12, zorder=2)
    if openda_ensr_mean_traj is not None:
        _col0 = nearest_col(openda_ensr_min_traj, _td)
        _ax0.fill_between(openda_ensr_min_traj.index,
                          openda_ensr_min_traj[_col0], openda_ensr_max_traj[_col0],
                          color="forestgreen", alpha=0.12, zorder=2)

    _ax0.set_ylabel("T (°C)")
    _ax0.set_title(f"{_actual_d:.0f} m")
    _ax0.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    _ax0.grid(True, alpha=0.3)

axes0[-1].set_xlabel("Date")
if YEAR is not None:
    axes0[0].set_xlim(pd.Timestamp(f"{YEAR}-01-01", tz="UTC"),
                      pd.Timestamp(f"{YEAR}-12-31", tz="UTC"))
fig0.autofmt_xdate()
plt.tight_layout(rect=[0, 0, 0.82, 1])
plt.show()


# ── Plot 1 — RMSE heatmaps (depth × month) ───────────────────────────────────
# One subplot per algorithm; shared colour scale so algorithms are comparable.

n_entries = len(entries)
all_matrices = [to_matrix(mo) for _, mo, _ in entries]
vmax = np.nanpercentile(np.concatenate([m.ravel() for m in all_matrices]), 95)

ncols = min(n_entries, 3)
nrows = (n_entries + ncols - 1) // ncols
fig1, axes1 = plt.subplots(nrows, ncols,
                            figsize=(5 * ncols, 4 * nrows),
                            squeeze=False)
fig1.suptitle(f"Monthly RMSE (°C) — {LABEL} {YEAR}", fontsize=12)

for idx, ((lbl, mo, color), mat) in enumerate(zip(entries, all_matrices)):
    ax = axes1[idx // ncols][idx % ncols]
    im = ax.imshow(mat, aspect="auto", origin="upper",
                   cmap="YlOrRd", vmin=0, vmax=vmax,
                   extent=[-0.5, 11.5, len(common_obs_depths) - 0.5, -0.5])
    ax.set_xticks(range(12))
    ax.set_xticklabels(MONTH_NAMES, fontsize=8)
    ax.set_yticks(range(len(common_obs_depths)))
    ax.set_yticklabels([f"{d:.0f} m" for d in common_obs_depths], fontsize=7)
    ax.set_title(lbl, color=color, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Depth")
    for i in range(len(common_obs_depths)):
        for j in range(12):
            val = mat[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=5.5, color="black" if val < 0.6 * vmax else "white")
    plt.colorbar(im, ax=ax, label="RMSE (°C)", fraction=0.03, pad=0.04)

# Hide unused subplots
for idx in range(n_entries, nrows * ncols):
    axes1[idx // ncols][idx % ncols].set_visible(False)

plt.tight_layout()
plt.show()


# ── Plot 2 — Monthly total RMSE line chart ────────────────────────────────────

fig2, ax2 = plt.subplots(figsize=(10, 5))
for lbl, mo, color in entries:
    totals = [np.nansum(mo[m]) for m in range(1, 13)]
    ax2.plot(range(1, 13), totals, marker="o", lw=2, color=color, label=lbl)

ax2.set_xticks(range(1, 13))
ax2.set_xticklabels(MONTH_NAMES)
ax2.set_ylabel("Total RMSE over all depths (°C)")
ax2.set_title(f"Monthly total RMSE — {LABEL} {YEAR}")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


# ── Plot 2b — Monthly RMSE per depth (line charts) ───────────────────────────

_nd = len(common_obs_depths)
_ncols2b = min(_nd, 4)
_nrows2b = (_nd + _ncols2b - 1) // _ncols2b
fig2b, axes2b = plt.subplots(_nrows2b, _ncols2b,
                              figsize=(5 * _ncols2b, 3.5 * _nrows2b),
                              sharex=True, squeeze=False)
fig2b.suptitle(f"Monthly RMSE per depth — {LABEL} {YEAR}", fontsize=12)

for _di, _d in enumerate(common_obs_depths):
    _ax = axes2b[_di // _ncols2b][_di % _ncols2b]
    for lbl, mo, color in entries:
        _vals = [mo[m][_di] for m in range(1, 13)]
        _ax.plot(range(1, 13), _vals, marker="o", lw=1.8, color=color, label=lbl)
    _ax.set_title(f"{_d:.0f} m", fontsize=9)
    _ax.set_xticks(range(1, 13))
    _ax.set_xticklabels(MONTH_NAMES, fontsize=7, rotation=45)
    _ax.set_ylabel("RMSE (°C)", fontsize=8)
    _ax.grid(True, alpha=0.3)

for _di in range(_nd, _nrows2b * _ncols2b):
    axes2b[_di // _ncols2b][_di % _ncols2b].set_visible(False)

_handles2b, _lbls2b = axes2b[0][0].get_legend_handles_labels()
fig2b.legend(_handles2b, _lbls2b, fontsize=8, loc="lower center",
             ncol=len(entries), bbox_to_anchor=(0.5, -0.02))
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.show()


# ── Plot 3 — Monthly RMSE bar charts (one per month) ─────────────────────────
# One figure with 12 subplots arranged in a 3×4 grid; each subplot is a
# stacked bar chart (same style as V2) for that month.

depth_cmap = plt.cm.viridis(np.linspace(0.9, 0.1, len(common_obs_depths)))
ref_mo = e0_mo  # use e0 as reference for gain annotation; may be None

fig3, axes3 = plt.subplots(3, 4, figsize=(20, 14), sharey=True)
fig3.suptitle(f"RMSE by month — {LABEL} {YEAR}", fontsize=13)

for m_idx, m in enumerate(range(1, 13)):
    ax = axes3[m_idx // 4][m_idx % 4]
    ax.set_title(MONTH_NAMES[m - 1], fontsize=10)

    month_entries = [(lbl, mo[m], np.nansum(mo[m]), color)
                     for lbl, mo, color in entries]
    month_entries.sort(key=lambda e: e[2], reverse=True)

    comp_x  = np.arange(len(month_entries))
    bottoms = np.zeros(len(month_entries))
    seg_tops = {}

    for d_idx, d in reversed(list(enumerate(common_obs_depths))):
        vals = np.array([e[1][d_idx] if not np.isnan(e[1][d_idx]) else 0
                         for e in month_entries])
        ax.bar(comp_x, vals, bottom=bottoms, color=depth_cmap[d_idx],
               width=0.6, label=f"{d:.0f} m" if m_idx == 0 else "")
        bottoms += vals
        seg_tops[d_idx] = bottoms.copy()

    ref_total_m = np.nansum(ref_mo[m]) if ref_mo is not None else month_entries[0][2]
    ref_xi      = next((xi for xi, e in enumerate(month_entries)
                        if e[0] == "e0"), None)

    for xi, (lbl, rmses_e, total, edgecolor) in enumerate(month_entries):
        ax.bar(xi, total, bottom=0, color="none", edgecolor=edgecolor, lw=1.5, width=0.6)
        gain = (total - ref_total_m) / ref_total_m * 100 if ref_total_m else 0
        ann  = f"{total:.2f}" if xi == ref_xi else f"{total:.2f}\n{gain:+.0f}%"
        ax.text(xi, total + 0.005 * ref_total_m, ann,
                ha="center", va="bottom", fontsize=6)

    ax.set_xticks(comp_x)
    ax.set_xticklabels([e[0].replace(" ", "\n") for e in month_entries], fontsize=6)
    ax.set_ylabel("RMSE (°C)" if m_idx % 4 == 0 else "")
    ax.grid(True, axis="y", alpha=0.3)

# Shared depth legend from first subplot
handles, lbls = axes3[0][0].get_legend_handles_labels()
fig3.legend(handles[::-1], lbls[::-1], fontsize=8, loc="lower center",
            ncol=len(common_obs_depths), title="depth", bbox_to_anchor=(0.5, -0.02))
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.show()


# ── Plot 4 — Annual RMSE bar chart (parplot) ─────────────────────────────────
# Annual RMSE computed over the full year (all months combined), depth-coloured
# stacked bars sorted worst → best, with gain% vs e0 annotations.

_annual_traj_list = [
    ("e0",              e0_traj,               "dimgrey"),
    ("EnKF\nmean",      enkf_mean_traj,        "mediumpurple"),
    ("EnKF filt\nmean", enkf_filt_mean_traj,   "darkorchid"),
    ("PF\nmean",        pf_mean_traj,          "steelblue"),
    ("PF filt\nmean",   pf_filt_mean_traj,     "teal"),
    ("OpenDA\nEnKF",    openda_mean_traj,       "darkorange"),
    ("OpenDA\nEnSR",    openda_ensr_mean_traj,  "forestgreen"),
]

annual_comp = []
e0_rmses_annual = None
for _lbl, _traj, _color in _annual_traj_list:
    if _traj is None:
        continue
    _rmses = compute_rmse_by_depth(_traj, obs, common_obs_depths)
    _total = np.nansum(_rmses)
    annual_comp.append((_lbl, _rmses, _total, _color))
    if _lbl == "e0":
        e0_rmses_annual = _rmses

annual_comp.sort(key=lambda e: e[2], reverse=True)

_ref_total = np.nansum(e0_rmses_annual) if e0_rmses_annual is not None else annual_comp[0][2]
_e0_xi     = next((xi for xi, e in enumerate(annual_comp) if e[0] == "e0"), None)
_depth_cmap = plt.cm.viridis(np.linspace(0.9, 0.1, len(common_obs_depths)))
_comp_x    = np.arange(len(annual_comp))
_bottoms   = np.zeros(len(annual_comp))
_seg_tops  = {}

fig4, ax4 = plt.subplots(figsize=(max(8, 4 * len(annual_comp)), 7))

for _d_idx, _d in reversed(list(enumerate(common_obs_depths))):
    _vals = np.array([e[1][_d_idx] if not np.isnan(e[1][_d_idx]) else 0 for e in annual_comp])
    ax4.bar(_comp_x, _vals, bottom=_bottoms, color=_depth_cmap[_d_idx], width=0.5, label=f"{_d:.0f} m")
    _bottoms += _vals
    _seg_tops[_d_idx] = _bottoms.copy()

for _d_idx in range(len(common_obs_depths)):
    ax4.plot(_comp_x, _seg_tops[_d_idx], color=_depth_cmap[_d_idx], lw=1.2, alpha=0.7, zorder=5)

for _xi, (_lbl, _rmses_e, _total, _edgecolor) in enumerate(annual_comp):
    ax4.bar(_xi, _total, bottom=0, color="none", edgecolor=_edgecolor, lw=2, width=0.5)
    _gain = (_total - _ref_total) / _ref_total * 100
    _ann  = f"{_total:.3f}°C" if _xi == _e0_xi else f"{_total:.3f}°C\n{_gain:+.1f}%"
    ax4.text(_xi, _total + 0.01 * _ref_total, _ann, ha="center", va="bottom", fontsize=9)

    _prev = 0.0
    for _d_idx in range(len(common_obs_depths) - 1, -1, -1):
        _top = _seg_tops[_d_idx][_xi]
        _mid = (_prev + _top) / 2
        _val = _rmses_e[_d_idx] if not np.isnan(_rmses_e[_d_idx]) else 0
        if _xi == _e0_xi or e0_rmses_annual is None or np.isnan(e0_rmses_annual[_d_idx]) or e0_rmses_annual[_d_idx] == 0:
            _ann_seg = f"{_val:.3f}"
        else:
            _depth_gain = (_val - e0_rmses_annual[_d_idx]) / e0_rmses_annual[_d_idx] * 100
            _ann_seg = f"{_val:.3f} / {_depth_gain:+.1f}%"
        ax4.text(_xi, _mid, _ann_seg, ha="center", va="center", fontsize=7, color="dimgrey")
        _prev = _top

ax4.set_xticks(_comp_x)
ax4.set_xticklabels([e[0] for e in annual_comp], fontsize=10)
ax4.set_ylabel("RMSE (°C)")
ax4.set_title(f"Annual RMSE comparison — {LABEL} {YEAR}")
_handles, _lbls = ax4.get_legend_handles_labels()
ax4.legend(_handles[::-1], _lbls[::-1], fontsize=8, loc="upper left",
           bbox_to_anchor=(1.01, 1), borderaxespad=0, title="depth")
ax4.grid(True, axis="y", alpha=0.3)
plt.tight_layout(rect=[0, 0, 0.85, 1])
plt.show()


# ── Plot 5 (optional) — Monthly time series ───────────────────────────────────

if PLOT_TIMESERIES:
    _plot_depths = -obs_depths
    for m in range(1, 13):
        fig_ts, axes_ts = plt.subplots(len(_plot_depths), 1,
                                       figsize=(12, 3 * len(_plot_depths)),
                                       sharex=True, squeeze=False)
        axes_ts = axes_ts[:, 0]
        fig_ts.suptitle(f"{MONTH_NAMES[m-1]} {YEAR} — {LABEL}", fontsize=11)

        t_start = pd.Timestamp(f"{YEAR}-{m:02d}-01", tz="UTC")
        t_end   = (t_start + pd.offsets.MonthEnd(1)).replace(hour=23, minute=59)

        for ax, target_depth in zip(axes_ts, _plot_depths):
            actual_depth = abs(nearest_col(_ref_traj, target_depth))
            nearest_obs_depth = obs_depths[np.argmin(np.abs(obs_depths - actual_depth))]
            obs_m = obs[(obs["depth"] == nearest_obs_depth) & (obs["time"].dt.month == m)]
            ax.scatter(obs_m["time"], obs_m["value"], s=4, color="tomato",
                       zorder=5, label=f"obs ({nearest_obs_depth:.1f} m)")

            if enkf_filt_members:
                _idx_sp, _mn_sp, _mx_sp = member_minmax(enkf_filt_members, target_depth)
                _mask = _idx_sp.month == m
                ax.fill_between(_idx_sp[_mask], _mn_sp[_mask], _mx_sp[_mask],
                                color="darkorchid", alpha=0.12, zorder=2,
                                label="EnKF filt min–max")

            if openda_mean_traj is not None:
                _col_sp = nearest_col(openda_min_traj, target_depth)
                _omn = openda_min_traj[_col_sp]
                _omx = openda_max_traj[_col_sp]
                _mask = _omn.index.month == m
                ax.fill_between(_omn.index[_mask], _omn.values[_mask], _omx.values[_mask],
                                color="darkorange", alpha=0.12, zorder=2,
                                label="OpenDA EnKF min–max")

            if openda_ensr_mean_traj is not None:
                _col_sp = nearest_col(openda_ensr_min_traj, target_depth)
                _emn = openda_ensr_min_traj[_col_sp]
                _emx = openda_ensr_max_traj[_col_sp]
                _mask = _emn.index.month == m
                ax.fill_between(_emn.index[_mask], _emn.values[_mask], _emx.values[_mask],
                                color="forestgreen", alpha=0.12, zorder=2,
                                label="OpenDA EnSR min–max")

            for traj, color, lbl in [
                (e0_traj,               "dimgrey",     "e0"),
                (enkf_mean_traj,        "mediumpurple","EnKF mean"),
                (enkf_filt_mean_traj,   "darkorchid",  "EnKF filt mean"),
                (pf_mean_traj,          "steelblue",   "PF mean"),
                (pf_filt_mean_traj,     "teal",        "PF filt mean"),
                (openda_mean_traj,      "darkorange",  "OpenDA EnKF mean"),
                (openda_ensr_mean_traj, "forestgreen", "OpenDA EnSR mean"),
            ]:
                if traj is not None:
                    col = nearest_col(traj, target_depth)
                    s = traj[col]
                    s = s[s.index.month == m]
                    ax.plot(s.index, s.values, color=color, lw=1.5, label=lbl)

            ax.set_ylabel("T (°C)")
            ax.set_title(f"{actual_depth:.0f} m")
            ax.set_xlim(t_start, t_end)
            ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1),
                      borderaxespad=0)
            ax.grid(True, alpha=0.3)

        axes_ts[-1].set_xlabel("Date")
        fig_ts.autofmt_xdate()
        plt.tight_layout(rect=[0, 0, 0.82, 1])
        plt.show()
