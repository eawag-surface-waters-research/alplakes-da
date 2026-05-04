import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

df = pd.read_csv("../data/T_obs_castagnola.csv", low_memory=False)
df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
df["time"]  = pd.to_datetime(df["time"], utc=True)
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df = df.dropna(subset=["depth", "time", "value"])

depths = sorted(df["depth"].unique())
colors = cm.viridis_r(np.linspace(0, 1, len(depths)))

fig, axes = plt.subplots(len(depths), 1, figsize=(14, 2 * len(depths)), sharex=True)

for ax, depth, color in zip(axes, depths, colors):
    ts = df[df["depth"] == depth].sort_values("time")
    ax.plot(ts["time"], ts["value"], lw=0.7, color=color)
    ax.set_ylabel(f"{depth:.0f} m", fontsize=8)
    ax.grid(True, alpha=0.3)

axes[0].set_title("Castagnola — water temperature by depth")
axes[-1].set_xlabel("time")
plt.tight_layout()
plt.show()
