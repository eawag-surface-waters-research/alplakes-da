import pandas as pd
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(14, 4))


for name, label, color in [
    ("T_obs_geneva", "Geneva", "steelblue"),
    ("T_obs_murten", "Murten", "darkorange"),
    ("T_obs_Castagnola", "Lugano", "seagreen"),
]:
    df = pd.read_csv(f"../data/{name}.csv")
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    shallowest = 1
    ts = df[df["depth"] == shallowest].sort_values("time")
    ax.plot(ts["time"], ts["value"], lw=0.8, label=f"{label} ({shallowest:.1f} m)", color=color)

ax.set_title("Geneva & Murten — surface water temperature")
ax.set_ylabel("Temperature (°C)")
ax.set_xlabel("Time")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

fig2, ax2 = plt.subplots(figsize=(14, 4))

for name, label, color in [
    ("lake_mean_geneva_2025", "Geneva", "steelblue"),
    ("lake_mean_murten_2025", "Murten", "darkorange"),
    ("lake_mean_lugano_2025", "Lugano", "seagreen"),
]:
    df = pd.read_csv(f"../data/{name}.csv")
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df["T_2M"] = pd.to_numeric(df["T_2M"], errors="coerce")
    ax2.plot(df["time"], df["T_2M"] - 273.15, lw=0.8, label=label, color=color)

ax2.set_title("2m air temperature — lake mean files 2025")
ax2.set_ylabel("T_2M (°C)")
ax2.set_xlabel("Time")
ax2.legend()
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
