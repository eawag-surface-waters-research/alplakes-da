import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.statespace.sarimax import SARIMAX

# ----------------------------
# Data preprocessing
# ----------------------------

df_obs = pd.read_csv("../data/obs_2025.csv")
df_obs["time"] = pd.to_datetime(df_obs["time"])
df_obs = df_obs.drop_duplicates(subset="time").reset_index(drop=True)

theta = np.deg2rad(df_obs["wind_direction"])
df_obs["u"] = -df_obs["wind_speed"] * np.sin(theta)
df_obs["v"] = -df_obs["wind_speed"] * np.cos(theta)

lake_mean = pd.read_csv("../data/lake_mean_ICON_2025.csv")
lake_mean["time"] = pd.to_datetime(lake_mean["time"])

icon = lake_mean.rename(columns={"T_2M": "T", "U": "U", "V": "V", "GLOB": "GLOB"})
icon["T"] = icon["T"] - 273.15

obs = df_obs.rename(columns={
    "air_temperature": "T_obs",
    "u": "U_obs",
    "v": "V_obs",
    "global_radiation": "GLOB_obs"
})[["time", "T_obs", "U_obs", "V_obs", "GLOB_obs", "vapour_pressure", "cloud_cover", "precipitation"]]

df = pd.merge(icon, obs, on="time", how="inner")

df["dT"]    = df["T"]    - df["T_obs"]
df["dU"]    = df["U"]    - df["U_obs"]
df["dV"]    = df["V"]    - df["V_obs"]
df["dGLOB"] = df["GLOB"] - df["GLOB_obs"]

# ----------------------------
# Model comparison:
#   D -- SARIMA(1,0,1)(1,1,1)_24
#   E -- SARIMA(0,0,1)(0,1,1)_24  [airline-type]
# ----------------------------

N_MEMBERS = 20
RNG_SEED  = 42
N_LAGS    = 72

VARIABLES = {
    "U":    ("dU",    "U_obs",    False),
    "V":    ("dV",    "V_obs",    False),
    "GLOB": ("dGLOB", "GLOB_obs", True),
}

DELTA_COLS = {"U": "dU",    "V": "dV",    "GLOB": "dGLOB"}
OBS_COLS   = {"U": "U_obs", "V": "V_obs", "GLOB": "GLOB_obs"}
UNITS      = {"U": "m/s",   "V": "m/s",   "GLOB": "W/m2"}

MODELS = {
    "D": {"order": (1, 0, 1), "seasonal_order": (1, 1, 1, 24)},
    "E": {"order": (0, 0, 1), "seasonal_order": (0, 1, 1, 24)},
}


def fit_sarima(residuals: pd.Series, order: tuple, seasonal_order: tuple) -> object:
    r = residuals.dropna().values
    return SARIMAX(r, order=order, seasonal_order=seasonal_order,
                   enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def simulate_sarima(result, n: int, n_members: int, rng: np.random.Generator) -> np.ndarray:
    sim = np.asarray(result.simulate(nsimulations=n, repetitions=n_members, random_state=rng))
    if sim.ndim == 3:
        sim = sim[:, 0, :]   # drop k_endog axis → (n, n_members)
    return sim


# --- Fit ---
fitted = {m: {} for m in MODELS}

for name, (delta_col, _, _) in VARIABLES.items():
    for m, cfg in MODELS.items():
        print(f"Fitting {m} for {name}...")
        fitted[m][name] = fit_sarima(df[delta_col], cfg["order"], cfg["seasonal_order"])
        print(fitted[m][name].summary())

# --- Simulate ---
rng = np.random.default_rng(RNG_SEED)
n   = len(df)
ens = {m: {} for m in MODELS}

for name, (_, obs_col, clip_zero) in VARIABLES.items():
    obs_vals = df[obs_col].values[:, None]
    for m in MODELS:
        pert = simulate_sarima(fitted[m][name], n, N_MEMBERS, rng)
        if clip_zero:
            pert[obs_vals[:, 0] == 0] = 0.0
        ens[m][name] = np.clip(obs_vals + pert, 0.0, None) if clip_zero else obs_vals + pert

print("\nEnsemble spread (std, time-mean):")
for name in VARIABLES:
    row = f"  {name:4s}"
    for m in MODELS:
        row += f"  {m}={ens[m][name].std(axis=1).mean():.3f}"
    print(row)

# ----------------------------
# Visual diagnostics -- 3 panels per variable
#   col 0: ACF of raw residuals
#   col 1: ensemble fan (first 200 h)
#   col 2: ensemble fan zoomed (first 72 h)
# ----------------------------

COLORS = {"D": "mediumpurple", "E": "crimson"}
LABELS = {
    "D": "D: SARIMA(1,0,1)(1,1,1)_24",
    "E": "E: SARIMA(0,0,1)(0,1,1)_24",
}

fig = plt.figure(figsize=(18, 4 * len(VARIABLES)))
gs  = gridspec.GridSpec(len(VARIABLES), 3, figure=fig, hspace=0.5, wspace=0.35)

for row, name in enumerate(VARIABLES):
    raw      = df[DELTA_COLS[name]].dropna()
    obs_vals = df[OBS_COLS[name]].values
    unit     = UNITS[name]

    ax0 = fig.add_subplot(gs[row, 0])
    plot_acf(raw, lags=N_LAGS, ax=ax0, alpha=0.05, color="grey")
    for lag in [24, 48]:
        ax0.axvline(lag, color="black", lw=0.8, ls=":")
    ax0.set_title(f"{name} -- ACF")
    ax0.set_xlabel("lag (h)")

    for col, hours in [(1, 200), (2, 72)]:
        ax      = fig.add_subplot(gs[row, col])
        t_slice = slice(0, min(hours, n))
        t_plot  = np.arange(t_slice.start, t_slice.stop)
        for m in MODELS:
            p5, p95 = np.percentile(ens[m][name][t_slice], [5, 95], axis=1)
            ax.fill_between(t_plot, p5, p95, alpha=0.2, color=COLORS[m])
            ax.plot(t_plot, ens[m][name][t_slice].mean(axis=1),
                    color=COLORS[m], lw=1.2, ls="--", label=LABELS[m])
        ax.plot(t_plot, obs_vals[t_slice], "k-", lw=1.0, label="obs")
        ax.set_title(f"{name} -- fan (first {hours} h)")
        ax.set_xlabel("time step (h)")
        ax.set_ylabel(unit)
        ax.legend(fontsize=8)

plt.show()
