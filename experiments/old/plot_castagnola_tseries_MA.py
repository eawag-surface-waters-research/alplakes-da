import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

df = pd.read_csv("../data/T_obs_castagnola.csv", low_memory=False)
df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
df["time"]  = pd.to_datetime(df["time"], utc=True)
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df = df.dropna(subset=["depth", "time", "value"])
TMIN, TMAX = pd.Timestamp("2025-07-23", tz="UTC"), pd.Timestamp("2025-07-31", tz="UTC")

depths = [1, 9, 40]
ylims  = [(20, 29), (16, 25), (2, 11)]
windows = [6, 12, 24, 48]
ma_colors = cm.cool(np.linspace(0.1, 0.9, len(windows)))

fig, axes = plt.subplots(len(depths), 1, figsize=(10, 2.5 * len(depths)), sharex=True)

for ax, depth, ylim in zip(axes, depths, ylims):
    ts = df[df["depth"] == depth].sort_values("time").set_index("time")
    ts_h = ts["value"].resample("1h").mean().interpolate()

    ax.plot(ts_h.index, ts_h.values, lw=1.2, color="black", alpha = 1, label="raw")

    for w, c in zip(windows, ma_colors):
        ax.plot(ts_h.index, ts_h.rolling(w, center=True).mean(),
                lw=1.2, color=c, label=f"MA {w}h", alpha = 0.5)

    ax.set_ylim(ylim)
    ax.set_ylabel(f"{depth:.0f} m", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(TMIN, TMAX)

axes[0].set_title("Temperature [°C]")
axes[0].legend(fontsize=7, loc="upper right", ncol=len(windows) + 1)
axes[-1].set_xlabel("")
plt.tight_layout()
plt.show()
