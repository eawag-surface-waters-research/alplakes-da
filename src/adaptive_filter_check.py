"""
Causal gradient- and depth-dependent low-pass filter for lake observations.

The filter window at each depth and timestep is the sum of two components:

  1. Temperature gradient-driven (thermocline signal):
       W_grad(z,t) = clip(W_MAX * |dT/dz(z,t)| / G_MAX,  W_MIN, W_MAX)
     - |dT/dz| is computed from a causal 72-h trailing mean of the local gradient
     - Depths shallower than THERMO_DEPTH_MIN are excluded (surface heating dominant, not thermocline internal waves)

  2. Depth floor (stability below thermocline):
       W_floor(z,t) = clip((z - z_tc(t)) / (DEEP_REF - z_tc(t)), 0, 1) * (W_DEEP - W_MIN)
     where z_tc(t) = depth of maximum |dT/dz| at time t (time-varying thermocline depth)
     - Zero everywhere when peak gradient < THERMO_GRAD_MIN (no thermocline, e.g. winter)
     - Zero at and above z_tc; ramps linearly to W_DEEP at DEEP_REF when active

  Final window:
       W(z,t) = clip(W_grad(z,t) + W_floor(z),  W_MIN, W_MAX)

  Zone summary:
    surface  (z < THERMO_DEPTH_MIN)  → W_MIN only  (solar heating, not internal waves)
    thermocline                       → dominated by W_grad, up to W_MAX
    below thermocline                 → W_floor increases with depth, W_grad small

  Applied as a causal trailing box filter (no lookahead, online-compatible).
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings("ignore")

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "analysis", "oscillations_geneva", "filter_check")
os.makedirs(OUT_DIR, exist_ok=True)
OBS_PATH = os.path.join(ROOT, "data", "T_obs_geneva.csv")

# ── PARAMETERS ────────────────────────────────────────────────────────────────
DEPTH_MAX       = 50.0   # m  – discard observations deeper than this
OUT_OBS         = os.path.join(ROOT, "data", "filtered_geneva.csv")

W_MIN  = 1.0    # h  – minimum window (surface / no stratification)
W_MAX  = 72     # h  – maximum window (peak thermocline gradient)
W_DEEP = 72.0   # h  – depth-floor window at DEEP_REF (linear ramp below thermocline)
DEEP_REF         = 50.0  # m  – depth at which depth-floor reaches W_DEEP
G_MAX  = None   # °C/m – gradient at which W = W_MAX; None = auto (95th pct of thermocline depths)
GRAD_SMOOTH_H    = 72  # h  – rolling window to smooth gradient before computing filter window
THERMO_DEPTH_MIN  = 4.0   # m  – gradient shallower than this is surface heating, not thermocline → W_MIN
THERMO_GRAD_MIN   = 0.1   # °C/m – min peak gradient to consider thermocline active; below → no depth floor
DT_MIN  = 10    # minutes – raw resolution
DT_FILT = 60   # minutes – resolution used for filtering

PLOT_DEPTHS = [0.25, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 12.0, 18.0, 27.0, 30.0, 35.0, 39.0]

ZOOM_PERIODS = [
    ("june_w1", "2025-06-01", "2025-06-08"),
    ("june_w2", "2025-06-08", "2025-06-15"),
    ("june_w3", "2025-06-15", "2025-06-22"),
    ("june_w4", "2025-06-22", "2025-06-30"),
    ("july_w1", "2025-07-01", "2025-07-08"),
    ("july_w2", "2025-07-08", "2025-07-15"),
    ("july_w3", "2025-07-15", "2025-07-22"),
    ("july_w4", "2025-07-22", "2025-07-30"),
]

# ── LOAD ──────────────────────────────────────────────────────────────────────
print("Loading …")
df = pd.read_csv(OBS_PATH, parse_dates=["time"])
df["time"] = pd.to_datetime(df["time"], utc=True)

pivot = (
    df[df["depth"] <= DEPTH_MAX]
    .pivot_table(index="time", columns="depth", values="value", aggfunc="mean")
    .sort_index()
    .resample(f"{DT_FILT}min").mean()   # resample to hourly
    .interpolate(method="time", limit=2)  # fill gaps up to 2 h
)
# drop depths with > 30 % NaN after resampling
nan_frac_col = pivot.isna().mean()
keep = nan_frac_col[nan_frac_col <= 0.30].index
dropped = nan_frac_col[nan_frac_col > 0.30].index.tolist()
if dropped:
    print(f"  Dropping depths with >30% NaN: {dropped}")
pivot      = pivot[keep]
depths_arr = np.array(pivot.columns, dtype=float)
PLOT_DEPTHS = [d for d in PLOT_DEPTHS if d in pivot.columns]
print(f"  {len(pivot)} timesteps × {len(depths_arr)} depths kept")

# ── LOCAL GRADIENT (centred finite difference, thermocline depths only) ────────
# Neighbors shallower than THERMO_DEPTH_MIN are excluded to avoid surface
# heating contaminating the gradient at the top of the thermocline.
T = pivot.values                         # (N, D)
G = np.full_like(T, np.nan)
for i in range(len(depths_arr)):
    d      = depths_arr[i]
    # find nearest valid neighbour above (>= THERMO_DEPTH_MIN)
    i_lo   = next((j for j in range(i-1, -1, -1) if depths_arr[j] >= THERMO_DEPTH_MIN), None)
    i_hi   = i + 1 if i + 1 < len(depths_arr) else None
    if i_lo is not None and i_hi is not None:
        dz = depths_arr[i_hi] - depths_arr[i_lo]
        G[:, i] = np.abs(T[:, i_hi] - T[:, i_lo]) / dz
    elif i_hi is not None:
        dz = depths_arr[i_hi] - d
        G[:, i] = np.abs(T[:, i_hi] - T[:, i]) / dz
    elif i_lo is not None:
        dz = d - depths_arr[i_lo]
        G[:, i] = np.abs(T[:, i] - T[:, i_lo]) / dz

grad_df = pd.DataFrame(G, index=pivot.index, columns=pivot.columns)

# surface depths get zero gradient (solar heating, not internal waves)
shallow_cols = [d for d in grad_df.columns if d < THERMO_DEPTH_MIN]
grad_df[shallow_cols] = 0.0

# trailing rolling mean of gradient (causal — no lookahead)
gs = int(GRAD_SMOOTH_H * 60 / DT_FILT)
grad_smooth = grad_df.rolling(gs, center=False, min_periods=gs // 2).mean()
grad_smooth = grad_smooth.ffill().bfill().fillna(0.0)

# G_MAX: 95th percentile of thermocline-depth gradients (auto-calibrated, no surface)
thermo_cols = [d for d in grad_smooth.columns if d >= THERMO_DEPTH_MIN]
G_MAX_auto  = np.nanpercentile(grad_smooth[thermo_cols].values, 95)
print(f"  G_MAX auto (95th pct of thermocline gradients): {G_MAX_auto:.3f} °C/m  "
      f"({'using auto' if G_MAX is None else f'overridden with G_MAX={G_MAX:.2f}'})")
G_MAX_use = G_MAX if G_MAX is not None else G_MAX_auto

# gradient-driven window
W_df = (grad_smooth / G_MAX_use * W_MAX).clip(W_MIN, W_MAX)

# depth floor: ramps from 0 at the actual thermocline depth to W_DEEP at DEEP_REF
# thermocline depth = depth of max gradient at each timestep (time-varying)
thermo_depth_t  = grad_smooth[thermo_cols].idxmax(axis=1)   # series (time,)
thermo_active_t = grad_smooth[thermo_cols].max(axis=1) >= THERMO_GRAD_MIN  # bool series

depth_floor_arr = np.zeros((len(W_df), len(depths_arr)))
for i, (z_tc, active) in enumerate(zip(thermo_depth_t.values, thermo_active_t.values)):
    if not active:
        continue                                            # no thermocline → floor stays 0
    span = max(DEEP_REF - z_tc, 1.0)                       # avoid division by zero
    depth_floor_arr[i] = np.clip(
        (depths_arr - z_tc) / span, 0.0, 1.0
    ) * (W_DEEP - W_MIN)

depth_floor_df = pd.DataFrame(depth_floor_arr, index=W_df.index, columns=W_df.columns)

# final window: gradient-driven + depth-floor, capped at W_MAX
W_df = (W_df + depth_floor_df).clip(W_MIN, W_MAX)

# ── CAUSAL TRAILING BOX FILTER (variable-width, online-compatible) ────────────
def variable_box_filter(x, widths):
    """
    Trailing rolling mean: at sample i, averages [i-widths[i]+1 … i].
    Causal — uses only past and current data, never future.
    Uses cumsum trick: O(N), handles NaN via separate valid-count accumulator.
    """
    x_fill = np.where(np.isnan(x), 0.0, x)
    valid  = (~np.isnan(x)).astype(float)
    cs     = np.concatenate([[0.0], np.cumsum(x_fill)])
    cv     = np.concatenate([[0.0], np.cumsum(valid)])
    result = np.empty(len(x))
    for i in range(len(x)):
        lo = max(0, i - widths[i] + 1)
        hi = i + 1                          # inclusive current sample only
        n  = cv[hi] - cv[lo]
        result[i] = (cs[hi] - cs[lo]) / n if n > 0 else np.nan
    return result

print("Filtering …")
filtered = pd.DataFrame(index=pivot.index, columns=pivot.columns, dtype=float)
for d in depths_arr:
    widths = np.maximum(1, np.round(W_df[d].values * 60 / DT_FILT).astype(int))
    filtered[d] = variable_box_filter(pivot[d].values, widths)

nan_frac = filtered.isna().mean().mean()
print(f"  Done. NaN fraction in filtered output: {nan_frac:.4f}")
if nan_frac > 0.01:
    print("  WARNING: high NaN fraction — check gaps in input data")
    for d in PLOT_DEPTHS:
        print(f"    depth {d:.0f} m: {filtered[d].isna().mean():.4f} NaN fraction")


############################# PLOTTING ############################################################
# ── PLOT 1: YEAR OVERVIEW ─────────────────────────────────────────────────────
print("Plotting year overview …")
fig, axes = plt.subplots(len(PLOT_DEPTHS) + 1, 1,
                          figsize=(16, 3.5 * (len(PLOT_DEPTHS) + 1)), sharex=True)

for ax, d in zip(axes[:-1], PLOT_DEPTHS):
    ax.plot(pivot[d].index,    pivot[d].values,    lw=0.4, alpha=0.6, color="steelblue", label="raw")
    ax.plot(filtered[d].index, filtered[d].values, lw=1.0, color="C3", label="filtered")
    ax.set_ylabel("T (°C)")
    ax.set_title(f"Depth {d:.0f} m")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    for _, t0, t1 in ZOOM_PERIODS:
        ax.axvspan(pd.Timestamp(t0, tz="UTC"), pd.Timestamp(t1, tz="UTC"),
                   alpha=0.12, color="gold")

ax = axes[-1]
for d in PLOT_DEPTHS:
    wh = W_df[d].resample("6h").median()
    ax.plot(wh.index, wh.values, lw=0.8, label=f"{d:.0f} m")
ax.set_ylabel("Window (h)")
ax.set_title("Filter window size (shaded = zoom periods)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
for _, t0, t1 in ZOOM_PERIODS:
    ax.axvspan(pd.Timestamp(t0, tz="UTC"), pd.Timestamp(t1, tz="UTC"),
               alpha=0.12, color="gold")

fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "overview_year.png"), dpi=150)
plt.close(fig)
print("  → overview_year.png")

# ── PLOT 2: ZOOM WINDOWS ──────────────────────────────────────────────────────
for name, t0_str, t1_str in ZOOM_PERIODS:
    t0  = pd.Timestamp(t0_str, tz="UTC")
    t1  = pd.Timestamp(t1_str, tz="UTC")
    msk = (pivot.index >= t0) & (pivot.index <= t1)
    t_msk = pivot.index[msk]

    # rows: temp panels + window lines + gradient heatmap + window heatmap
    n_rows = len(PLOT_DEPTHS) + 3
    fig, axes = plt.subplots(n_rows, 1,
                              figsize=(14, 3.0 * n_rows), sharex=True,
                              gridspec_kw={"height_ratios": [2.5]*len(PLOT_DEPTHS) + [1.5, 1.5, 1.5]})

    # ── temperature panels ──
    for ax, d in zip(axes[:len(PLOT_DEPTHS)], PLOT_DEPTHS):
        raw_z  = pivot[d][msk]
        filt_z = filtered[d][msk]
        W_med  = W_df[d][msk].median()
        rms    = np.sqrt(np.nanmean((raw_z - filt_z).values ** 2))
        ax.plot(raw_z.index,  raw_z.values,  lw=0.6, alpha=0.7, color="steelblue", label="raw")
        ax.plot(filt_z.index, filt_z.values, lw=1.8, color="C3", label="filtered")
        ax.fill_between(raw_z.index, raw_z.values, filt_z.values,
                        alpha=0.2, color="C0")
        ax.set_title(f"{d:.0f} m  |  removed RMS = {rms:.3f} °C  |  median W = {W_med:.1f} h",
                     fontsize=9)
        ax.set_ylabel("T (°C)")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)

    # ── window size time series (one line per depth) ──
    ax_w = axes[-3]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(PLOT_DEPTHS)))
    for c, d in zip(colors, PLOT_DEPTHS):
        ax_w.plot(t_msk, W_df[d][msk].values, lw=1.2, color=c, label=f"{d:.0f} m")
    ax_w.set_ylabel("Window (h)")
    ax_w.set_ylim(0, W_MAX * 1.05)
    ax_w.axhline(W_MIN, color="gray", lw=0.8, ls=":")
    ax_w.axhline(W_MAX, color="gray", lw=0.8, ls=":")
    ax_w.set_title("Applied filter window per depth", fontsize=9)
    ax_w.legend(fontsize=7, ncol=len(PLOT_DEPTHS), loc="upper right")
    ax_w.grid(True, alpha=0.3)

    # ── gradient Hovmöller ──
    ax_g = axes[-2]
    G_sub  = grad_smooth[msk]
    t_num  = mdates.date2num(t_msk.to_pydatetime())
    d_vals = np.array(G_sub.columns, dtype=float)
    g_max_plot = np.nanpercentile(G_sub.values, 99)
    im_g = ax_g.contourf(t_num, d_vals, G_sub.values.T,
                          levels=np.linspace(0, g_max_plot, 20), cmap="Blues")
    fig.colorbar(im_g, ax=ax_g, label="|dT/dz| (°C/m)", pad=0.01)
    ax_g.set_ylabel("Depth (m)")
    ax_g.invert_yaxis()
    ax_g.set_title("Temperature gradient |dT/dz| (Hovmöller)", fontsize=9)

    # ── window heatmap across ALL depths ──
    ax_h = axes[-1]
    W_sub  = W_df[msk]
    im_w = ax_h.contourf(t_num, d_vals, W_sub.values.T,
                          levels=np.linspace(W_MIN, W_MAX, 20), cmap="YlOrRd")
    fig.colorbar(im_w, ax=ax_h, label="W (h)", pad=0.01)
    ax_h.set_ylabel("Depth (m)")
    ax_h.invert_yaxis()
    ax_h.set_title("Applied filter window (Hovmöller)", fontsize=9)
    ax_h.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax_h.xaxis.set_major_locator(mdates.DayLocator())

    fig.suptitle(f"June {t0_str[8:10]}–{t1_str[8:10]}  ({t0_str[:7]})", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, f"zoom_{name}.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → zoom_{name}.png")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("\n=== removed RMS (°C) per depth × period ===")
print(f"{'depth':>7}", end="")
for name, *_ in ZOOM_PERIODS:
    print(f"  {name:>12}", end="")
print()
for d in PLOT_DEPTHS:
    print(f"{d:>7.0f}", end="")
    for _, t0_str, t1_str in ZOOM_PERIODS:
        t0  = pd.Timestamp(t0_str, tz="UTC")
        t1  = pd.Timestamp(t1_str, tz="UTC")
        msk = (pivot.index >= t0) & (pivot.index <= t1)
        rms = np.sqrt(np.nanmean((pivot[d][msk] - filtered[d][msk]).values ** 2))
        print(f"  {rms:>12.4f}", end="")
    print()
print(f"\nOutputs → {OUT_DIR}")

# ── SAVE FILTERED OBSERVATIONS ────────────────────────────────────────────────
print("\nSaving filtered observations …")

# get lat/lon from original file (take first occurrence per depth)
meta = (
    df[df["depth"].isin(depths_arr)]
    .groupby("depth")[["latitude", "longitude"]]
    .first()
)

records = []
for d in depths_arr:
    lat = meta.loc[d, "latitude"] if d in meta.index else np.nan
    lon = meta.loc[d, "longitude"] if d in meta.index else np.nan
    col = filtered[d].dropna()
    for t, v in col.items():
        records.append({
            "time":      t.isoformat(),
            "depth":     d,
            "latitude":  lat,
            "longitude": lon,
            "value":     round(v, 6),
            "weight":    1,
        })

out_df = pd.DataFrame(records).sort_values(["time", "depth"])
out_df.to_csv(OUT_OBS, index=False)
print(f"  {len(out_df):,} rows → {OUT_OBS}")
