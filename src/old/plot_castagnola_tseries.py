import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, filtfilt

df = pd.read_csv("../data/T_obs_castagnola.csv", low_memory=False)
df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
df["time"]  = pd.to_datetime(df["time"], utc=True)
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df = df.dropna(subset=["depth", "time", "value"])
#df = df[(df["time"] >= "2025-06-13") & (df["time"] < "2025-06-18")]

depths = sorted(df["depth"].unique())
colors = cm.viridis_r(np.linspace(0, 1, len(depths)))

CUTOFF_H = 12  # cutoff period in hours

def butter_lp(data, cutoff_h, order=4):
    # fs = 1 sample/h; wn is cutoff in cycles/h normalised to Nyquist
    wn = (1 / cutoff_h) / 0.5
    b, a = butter(order, wn, btype="low")
    return filtfilt(b, a, data)

fig, axes = plt.subplots(len(depths), 1, figsize=(14, 2 * len(depths)), sharex=True)

for ax, depth, color in zip(axes, depths, colors):
    ts = df[df["depth"] == depth].sort_values("time").set_index("time")
    ts_h = ts["value"].resample("1h").mean().interpolate()
    vals = ts_h.values
    idx  = ts_h.index

    ax.plot(idx, vals, lw=0.5, color="lightgray", alpha=0.8, label="raw")

    # rolling mean
    ax.plot(idx, ts_h.rolling(CUTOFF_H, center=True).mean(),
            lw=1.3, color=color, label=f"rolling {CUTOFF_H}h")

    # Gaussian — sigma chosen so -3dB is at the 24h period
    sigma = CUTOFF_H / (2 * np.pi)
    ax.plot(idx, gaussian_filter1d(vals, sigma=sigma),
            lw=1.3, ls="--", color="tab:orange", label=f"Gaussian σ={sigma:.1f}h") 

    # Butterworth low-pass
    if len(vals) > 3 * CUTOFF_H:
        ax.plot(idx, butter_lp(vals, CUTOFF_H),
                lw=1.3, ls=":", color="tab:red", label=f"Butterworth {CUTOFF_H}h")

    ax.set_ylabel(f"{depth:.0f} m", fontsize=8)
    ax.grid(True, alpha=0.3)

axes[0].set_title("Temperature [°C]")
axes[0].legend(fontsize=7, loc="upper right", ncol=4)
axes[-1].set_xlabel("Time")
plt.tight_layout()
plt.show()
