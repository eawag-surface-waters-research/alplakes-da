"""
Oscillation analysis of thermocline-depth temperatures in Lake Geneva.

Goals:
  1. Characterise subdaily oscillatory signals (internal waves / seiches) at
     thermocline depths (7–20 m).
  2. Quantify how oscillation amplitude correlates with the vertical temperature
     gradient (thermocline strength) – the basis for a gradient-dependent
     moving-average filter.

Outputs (saved to analysis/oscillations_geneva/):
  • heatmap_thermocline.png   – hovmöller of raw T at 8–18 m
  • gradient_timeseries.png   – max |dT/dz| and thermocline depth vs time
  • spectral_summary.png      – power spectra per depth (summer vs winter)
  • wavelet_*.png             – wavelet scalograms per depth
  • amplitude_vs_gradient.png – scatter: oscillation amplitude vs gradient
  • filter_response.png       – candidate window sizes vs gradient strength
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
from scipy import signal
from scipy.interpolate import interp1d

warnings.filterwarnings("ignore")

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "analysis", "oscillations_geneva")
os.makedirs(OUT_DIR, exist_ok=True)

OBS_PATH   = os.path.join(ROOT, "data", "T_obs_geneva.csv")
THERMO_MIN = 7.0    # m  – shallowest depth of interest
THERMO_MAX = 30.0   # m  – deepest depth of interest
DT_MIN     = 10     # minutes – expected sample interval

# ── 1.  LOAD & PIVOT ──────────────────────────────────────────────────────────
print("Loading data …")
df = pd.read_csv(OBS_PATH, parse_dates=["time"])
df["time"] = pd.to_datetime(df["time"], utc=True)

# keep thermocline band plus one depth above and one below for gradient calc
thermo_depths = sorted(df["depth"].unique())
grad_depths   = [d for d in thermo_depths if THERMO_MIN - 5 <= d <= THERMO_MAX + 5]
thermo_only   = [d for d in thermo_depths if THERMO_MIN <= d <= THERMO_MAX]

pivot = (
    df[df["depth"].isin(grad_depths)]
    .pivot_table(index="time", columns="depth", values="value", aggfunc="mean")
    .sort_index()
)

# Resample to regular 10-min grid, linear interpolation across small gaps (<= 2 h)
pivot = pivot.resample("10min").mean()
pivot = pivot.interpolate(method="time", limit=12)   # 12 × 10 min = 2 h

print(f"  Grid: {len(pivot)} timesteps, depths: {list(pivot.columns.values)}")

# ── 2.  THERMOCLINE CHARACTERISATION ─────────────────────────────────────────
print("Computing temperature gradients …")

depths_arr = np.array(pivot.columns, dtype=float)   # positive downward

def vertical_gradient(row):
    """Return max |dT/dz| and the depth at which it occurs."""
    T    = row.values
    mask = ~np.isnan(T)
    if mask.sum() < 2:
        return np.nan, np.nan
    z  = depths_arr[mask]
    T  = T[mask]
    dz = np.diff(z)
    dT = np.diff(T)
    # dT/dz – positive = temperature increasing with depth (unstable / heating from above)
    # In summer the lake warms from above so dT/dz > 0 in the thermocline
    grad   = dT / dz           # °C / m
    abs_g  = np.abs(grad)
    imax   = np.argmax(abs_g)
    z_mid  = 0.5 * (z[imax] + z[imax + 1])
    return abs_g[imax], z_mid

grad_series = pivot.apply(vertical_gradient, axis=1, result_type="expand")
grad_series.columns = ["max_grad", "thermo_depth"]

# Daily smoothed versions for plotting
daily_grad        = grad_series["max_grad"].resample("D").median()
daily_thermo_depth = grad_series["thermo_depth"].resample("D").median()

# ── 3.  ANOMALIES  (remove 25-h low-pass to isolate subdaily signal) ──────────
print("Extracting subdaily anomalies …")

# 25-h Hanning low-pass (keeps diel and longer)
LP_HOURS   = 25
lp_samples = int(LP_HOURS * 60 / DT_MIN)
lp_win     = signal.windows.hann(lp_samples if lp_samples % 2 == 1
                                  else lp_samples + 1)
lp_win     /= lp_win.sum()

thermo_pivot = pivot[thermo_only].copy()
low_pass     = thermo_pivot.apply(
    lambda col: pd.Series(
        np.convolve(col.fillna(col.median()), lp_win, mode="same"),
        index=col.index
    ),
    axis=0,
)
anomaly = thermo_pivot - low_pass   # subdaily oscillatory component

# ── 4.  RUNNING OSCILLATION AMPLITUDE  (6-h RMS) ─────────────────────────────
print("Computing running oscillation amplitude …")

rms_window = int(6 * 60 / DT_MIN)   # 6 h
osc_amp    = anomaly.rolling(rms_window, center=True, min_periods=rms_window // 2) \
                    .apply(lambda x: np.sqrt(np.nanmean(x**2)), raw=True)

# Also compute median depth amplitude (across all thermo depths)
osc_amp_median = osc_amp.median(axis=1)

# ── 5.  SPECTRAL ANALYSIS ─────────────────────────────────────────────────────
print("Running spectral analysis …")

# Split into summer (Jun–Sep, strong thermocline) and winter (Dec–Mar, no thermo)
pivot_time = pivot.index

def season_mask(idx, months):
    return idx.month.isin(months)

summer_mask = season_mask(anomaly.index, [6, 7, 8, 9])
winter_mask = season_mask(anomaly.index, [12, 1, 2, 3])

fs = 1 / (DT_MIN * 60)   # Hz  (samples per second)


def welch_spectrum(series, fs, nperseg_hours=24):
    """Return (freq_cpd, psd) using Welch method."""
    x = series.dropna().values
    if len(x) < 144:   # need at least 1 day
        return None, None
    nperseg = int(nperseg_hours * 3600 * fs)
    f, p = signal.welch(x, fs=fs, nperseg=nperseg, window="hann",
                        detrend="linear", scaling="density")
    f_cpd = f * 86400   # convert Hz to cycles per day
    return f_cpd, p


# ── 6.  WAVELET ANALYSIS  (Morlet, manual implementation) ────────────────────

def morlet_cwt(x, dt_min, periods_h):
    """
    Continuous wavelet transform using complex Morlet wavelet.
    Returns (power, coi) where power.shape = (len(periods_h), len(x)),
    and coi is the cone-of-influence in the same period units.
    """
    N     = len(x)
    dt    = dt_min * 60          # seconds
    omega0 = 6.0                 # Morlet parameter

    # Pad to next power of 2 for FFT efficiency
    N2  = int(2 ** np.ceil(np.log2(N)))
    xp  = np.concatenate([x - np.nanmean(x), np.zeros(N2 - N)])

    # Angular frequency array
    k    = np.fft.fftfreq(N2, d=dt) * 2 * np.pi
    xhat = np.fft.fft(xp)

    scales  = np.array(periods_h) * 3600 / (4 * np.pi / (omega0 + np.sqrt(2 + omega0**2)))
    power   = np.zeros((len(scales), N))

    for i, s in enumerate(scales):
        psi_hat     = (np.pi ** -0.25) * np.sqrt(2 * np.pi * s / dt) * \
                      np.exp(-0.5 * (s * k - omega0) ** 2) * \
                      np.heaviside(k, 1.0)
        W           = np.fft.ifft(xhat * psi_hat)[:N]
        power[i, :] = np.abs(W) ** 2

    coi = np.sqrt(2) * scales / 3600   # cone of influence in hours
    return power, coi


# ── 7.  PLOT: HEATMAP THERMOCLINE ────────────────────────────────────────────
print("Plotting heatmap …")

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

ax = axes[0]
T_plot = thermo_pivot.resample("1h").mean()
im = ax.contourf(T_plot.index, T_plot.columns, T_plot.values.T,
                 levels=20, cmap="RdYlBu_r")
fig.colorbar(im, ax=ax, label="T (°C)")
ax.set_ylabel("Depth (m)")
ax.set_title("Raw temperature — thermocline depths (8–18 m)")
ax.invert_yaxis()

ax = axes[1]
anom_plot = anomaly.resample("1h").mean()
vlim = np.nanpercentile(np.abs(anom_plot.values), 99)
im2 = ax.contourf(anom_plot.index, anom_plot.columns, anom_plot.values.T,
                  levels=np.linspace(-vlim, vlim, 21), cmap="RdBu_r")
fig.colorbar(im2, ax=ax, label="ΔT (°C)")
ax.set_ylabel("Depth (m)")
ax.set_title("Subdaily anomaly (T minus 25-h low-pass)")
ax.invert_yaxis()

ax = axes[2]
ax.plot(grad_series.index, grad_series["max_grad"], color="gray", lw=0.3, alpha=0.5)
ax.plot(daily_grad.index, daily_grad.values, color="C1", lw=1.5, label="max |dT/dz|")
ax2 = ax.twinx()
ax2.plot(daily_thermo_depth.index, daily_thermo_depth.values,
         color="C0", lw=1.5, ls="--", label="thermocline depth")
ax2.invert_yaxis()
ax.set_ylabel("max |dT/dz|  (°C m⁻¹)", color="C1")
ax2.set_ylabel("Thermocline depth (m)", color="C0")
ax.set_title("Thermocline strength and depth")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_xlabel("2025")

fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "heatmap_thermocline.png"), dpi=150)
plt.close(fig)
print("  → heatmap_thermocline.png")

# ── 8.  PLOT: POWER SPECTRA ───────────────────────────────────────────────────
print("Plotting spectra …")

depths_to_plot = thermo_only
n_d            = len(depths_to_plot)

fig, axes = plt.subplots(1, n_d, figsize=(3 * n_d, 5), sharey=True)

# Period ticks to annotate
period_labels = {0.5: "12 h", 1: "1 d", 2: "2 d", 3: "3 d"}

for ax, d in zip(axes, depths_to_plot):
    col  = anomaly[d]
    fs_h = fs * 3600   # cycles per hour

    f_s, p_s = welch_spectrum(col[summer_mask], fs, nperseg_hours=48)
    f_w, p_w = welch_spectrum(col[winter_mask], fs, nperseg_hours=48)

    if f_s is not None:
        ax.semilogy(f_s, p_s, color="C3", lw=1.2, label="summer")
    if f_w is not None:
        ax.semilogy(f_w, p_w, color="C0", lw=1.2, label="winter")

    ax.set_title(f"{d:.0f} m")
    ax.set_xlabel("Freq. (cpd)")
    ax.grid(True, which="both", alpha=0.3)

    # Mark periods of interest
    for f_cpd, lbl in [(2, "12 h"), (1, "1 d"), (0.5, "2 d"), (0.333, "3 d")]:
        ax.axvline(f_cpd, color="k", lw=0.7, ls=":")
        ax.text(f_cpd, ax.get_ylim()[0] * 2, lbl, fontsize=6,
                rotation=90, va="bottom", ha="right")

axes[0].set_ylabel("PSD (°C² / cpd)")
axes[-1].legend(fontsize=8)
fig.suptitle("Power spectra of subdaily anomaly — thermocline depths\n"
             "Summer (Jun–Sep) vs Winter (Dec–Mar)", fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "spectral_summary.png"), dpi=150)
plt.close(fig)
print("  → spectral_summary.png")

# ── 9.  PLOT: WAVELET for representative depths ───────────────────────────────
print("Computing wavelets …")

periods_h = np.logspace(np.log10(0.5), np.log10(96), 60)   # 30 min → 4 days

rep_depths = [d for d in [9.0, 12.0, 18.0] if d in thermo_only]

for d in rep_depths:
    col = anomaly[d].fillna(0).values
    if len(col) == 0:
        continue

    power, coi = morlet_cwt(col, DT_MIN, periods_h)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})

    t_arr   = anomaly.index
    t_num   = mdates.date2num(t_arr.to_pydatetime())
    P_grid, T_grid = np.meshgrid(t_num, periods_h)

    vmax = np.nanpercentile(power, 99)
    cf   = ax1.contourf(T_grid, P_grid, power,
                        levels=np.linspace(0, vmax, 20), cmap="hot_r")
    fig.colorbar(cf, ax=ax1, label="Wavelet power (°C²)")

    # Cone of influence
    dt_h   = DT_MIN / 60
    t_idx  = np.arange(len(t_arr))
    coi_l  = np.minimum(t_idx, len(t_arr) - 1 - t_idx) * dt_h * np.sqrt(2)
    ax1.fill_between(t_num,
                     np.full(len(t_num), periods_h.max()),
                     np.clip(coi_l, periods_h.min(), periods_h.max()),
                     alpha=0.35, color="lightgray", label="COI")

    ax1.set_yscale("log")
    ax1.set_ylim(periods_h.min(), periods_h.max())
    ax1.set_yticks([0.5, 1, 2, 3, 6, 12, 24, 48, 96])
    ax1.set_yticklabels(["30 m", "1 h", "2 h", "3 h", "6 h", "12 h",
                         "1 d", "2 d", "4 d"])
    ax1.set_ylabel("Period")
    ax1.set_title(f"Morlet wavelet scalogram — depth {d:.0f} m")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    ax2.plot(t_arr, anomaly[d].values, lw=0.4, color="C0")
    ax2.set_ylabel("ΔT (°C)")
    ax2.set_xlabel("2025")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fname = os.path.join(OUT_DIR, f"wavelet_depth{int(d)}m.png")
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"  → wavelet_depth{int(d)}m.png")

# ── 10.  AMPLITUDE vs GRADIENT SCATTER ───────────────────────────────────────
print("Plotting amplitude vs gradient …")

# Resample gradient and amplitude to the same hourly grid
grad_h = grad_series["max_grad"].resample("1h").median()
amp_h  = osc_amp_median.resample("1h").median()

common = grad_h.index.intersection(amp_h.index)
G = grad_h[common].values
A = amp_h[common].values
mask = np.isfinite(G) & np.isfinite(A)
G, A = G[mask], A[mask]

# Month for colour
months = common[mask].month

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

ax = axes[0]
sc = ax.scatter(G, A, c=months, cmap="hsv", s=2, alpha=0.4, vmin=1, vmax=12)
fig.colorbar(sc, ax=ax, label="Month")
ax.set_xlabel("max |dT/dz|  (°C m⁻¹)")
ax.set_ylabel("6-h RMS oscillation amplitude (°C)")
ax.set_title("Oscillation amplitude vs thermocline gradient")

# Bin statistics
bins  = np.percentile(G[G > 0], np.linspace(5, 95, 20))
bin_i = np.digitize(G, bins)
b_med = [np.nanmedian(A[bin_i == i]) for i in range(len(bins) + 1)]
b_p75 = [np.nanpercentile(A[bin_i == i], 75) if (bin_i == i).sum() > 5 else np.nan
         for i in range(len(bins) + 1)]
b_p25 = [np.nanpercentile(A[bin_i == i], 25) if (bin_i == i).sum() > 5 else np.nan
         for i in range(len(bins) + 1)]
b_x   = np.concatenate([[G.min()], bins])
ax.plot(b_x, b_med, "k-", lw=2, label="median")
ax.fill_between(b_x, b_p25, b_p75, alpha=0.3, color="k", label="IQR")
ax.legend()

# ── 11.  FILTER RESPONSE: ADAPTIVE WINDOW SIZE ───────────────────────────────
ax = axes[1]

# Design: window size (hours) = W_min + (W_max - W_min) * exp(-k * grad)
# This gives large window (more smoothing) when gradient is small,
# and small window (less smoothing) when gradient is large.
W_MIN, W_MAX = 1.0, 24.0    # hours
k_values     = [2, 5, 10]   # controls sharpness of transition

grad_range = np.linspace(0, max(G.max(), 1.0), 200)

for k in k_values:
    W = W_MIN + (W_MAX - W_MIN) * np.exp(-k * grad_range)
    ax.plot(grad_range, W, lw=1.8, label=f"k = {k}")

# Overlay the scatter as background density
hist, xedge, yedge = np.histogram2d(G, A, bins=(50, 50))
ax.set_xlabel("max |dT/dz|  (°C m⁻¹)")
ax.set_ylabel("Adaptive window size (h)")
ax.set_title("Candidate adaptive filter windows\n"
             "W = W_min + (W_max - W_min)·exp(−k·|dT/dz|)")
ax.legend()
ax.axhline(W_MIN, color="gray", ls=":", lw=0.8)
ax.axhline(W_MAX, color="gray", ls=":", lw=0.8)
ax.text(0.01, W_MIN + 0.3, f"W_min = {W_MIN} h", fontsize=8, color="gray")
ax.text(0.01, W_MAX - 1.0, f"W_max = {W_MAX} h", fontsize=8, color="gray")

fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "amplitude_vs_gradient.png"), dpi=150)
plt.close(fig)
print("  → amplitude_vs_gradient.png")

# ── 12.  SUMMARY STATISTICS ───────────────────────────────────────────────────
print("\n=== SUMMARY ===")
print(f"Depths analysed:   {thermo_only}")
print(f"Period:            {pivot.index.min().date()} → {pivot.index.max().date()}")

print("\nOscillation amplitude (6-h RMS) by season:")
for season, msk in [("summer (JJA+Sep)", summer_mask), ("winter (DJF+Mar)", winter_mask)]:
    amp_s = osc_amp_median[msk]
    print(f"  {season:25s}  median={amp_s.median():.4f} °C  p95={amp_s.quantile(0.95):.4f} °C")

print("\nThermocline gradient statistics:")
print(f"  Annual median : {grad_series['max_grad'].median():.4f} °C/m")
print(f"  Summer median : {grad_series['max_grad'][summer_mask].median():.4f} °C/m")
print(f"  Winter median : {grad_series['max_grad'][winter_mask].median():.4f} °C/m")

print(f"\nAll outputs saved to: {OUT_DIR}")
