import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.arima_process import ArmaProcess
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

df_obs["time"] = pd.to_datetime(df_obs["time"])
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

print(df.head())

# ----------------------------
# Model comparison:
#   A -- AR(1)
#   B -- Additive AR(1,24):  r_t = phi*r_{t-1} + PHI*r_{t-24} + eps_t
#   C -- AR(1) x SAR(1)_24 (multiplicative, for reference)
#   D -- SARIMA(1,0,1)(1,1,1)_24
#   E -- SARIMA(0,0,1)(0,1,1)_24  [airline-type]
# ----------------------------

N_MEMBERS   = 20
RNG_SEED    = 42
SIGMA_SCALE = 1.0
PHI_SCALE   = 1.0
N_LAGS      = 72

VARIABLES = {
    "U":    ("dU",    "U_obs",    False),
    "V":    ("dV",    "V_obs",    False),
    "GLOB": ("dGLOB", "GLOB_obs", True),
}

DELTA_COLS = {"U": "dU",    "V": "dV",    "GLOB": "dGLOB"}
OBS_COLS   = {"U": "U_obs", "V": "V_obs", "GLOB": "GLOB_obs"}
UNITS      = {"U": "m/s",   "V": "m/s",   "GLOB": "W/m2"}


def fit_ar1(residuals: pd.Series) -> dict:
    r   = residuals.dropna().values
    phi = float(np.corrcoef(r[:-1], r[1:])[0, 1])
    sigma = float(r.std() * np.sqrt(max(1 - phi**2, 0)))
    return {"phi": phi, "sigma": sigma}


def simulate_ar1(phi: float, sigma: float, n: int, n_members: int,
                 rng: np.random.Generator) -> np.ndarray:
    innov = rng.standard_normal((n, n_members)) * sigma
    out   = np.zeros((n, n_members))
    for t in range(1, n):
        out[t] = phi * out[t - 1] + innov[t]
    return out


def fit_additive_ar(residuals: pd.Series) -> dict:
    """Fit AR(1) and AR(24) separately via lag autocorrelations."""
    r   = residuals.dropna().values
    phi = float(np.corrcoef(r[:-1],  r[1:])[0, 1])   # lag-1
    PHI = float(np.corrcoef(r[:-24], r[24:])[0, 1])  # lag-24
    resid = r[24:] - phi * r[23:-1] - PHI * r[:-24]
    sigma = float(resid.std())
    return {"phi": phi, "PHI": PHI, "sigma": sigma}


def simulate_additive_ar(phi: float, PHI: float, sigma: float, n: int, n_members: int,
                         rng: np.random.Generator) -> np.ndarray:
    """r_t = phi*r_{t-1} + PHI*r_{t-24} + eps_t"""
    innov = rng.standard_normal((n, n_members)) * sigma
    out   = np.zeros((n, n_members))
    for t in range(24, n):
        out[t] = phi * out[t - 1] + PHI * out[t - 24] + innov[t]
    return out


def theoretical_acf_ar24(PHI: float, n_lags: int) -> np.ndarray:
    ar     = np.zeros(25)
    ar[0]  =  1.0
    ar[24] = -PHI
    return ArmaProcess(ar=ar, ma=[1]).acf(n_lags + 1)


def theoretical_acf_additive_ar(phi: float, PHI: float, n_lags: int) -> np.ndarray:
    ar      = np.zeros(25)
    ar[0]   =  1.0
    ar[1]   = -phi
    ar[24]  = -PHI
    return ArmaProcess(ar=ar, ma=[1]).acf(n_lags + 1)


def fit_sar1(residuals: pd.Series) -> dict:
    """Fit AR(1) x SAR(1)_24: (1-phi*B)(1-PHI*B^24) r_t = eps_t"""
    r   = residuals.dropna().values
    res = SARIMAX(r, order=(1,0,0), seasonal_order=(1,0,0,24), trend="n").fit(disp=False)
    phi = float(res.params[0])
    PHI = float(res.params[1])
    var_fraction = max(1 - phi**2 - PHI**2 + (phi * PHI)**2, 1e-6)
    sigma = float(r.std() * np.sqrt(var_fraction))
    return {"phi": phi, "PHI": PHI, "sigma": sigma}


def simulate_sar1(phi: float, PHI: float, sigma: float, n: int, n_members: int,
                  rng: np.random.Generator) -> np.ndarray:
    """r_t = phi*r_{t-1} + PHI*r_{t-24} - phi*PHI*r_{t-25} + eps_t"""
    innov = rng.standard_normal((n, n_members)) * sigma
    out   = np.zeros((n, n_members))
    for t in range(25, n):
        out[t] = (phi * out[t-1] + PHI * out[t-24]
                  - phi * PHI * out[t-25] + innov[t])
    return out


def theoretical_acf_sar1(phi: float, PHI: float, n_lags: int) -> np.ndarray:
    ar     = np.zeros(26)
    ar[0]  =  1.0
    ar[1]  = -phi
    ar[24] = -PHI
    ar[25] =  phi * PHI
    return ArmaProcess(ar=ar, ma=[1]).acf(n_lags + 1)


def fit_sarima(residuals: pd.Series, order: tuple, seasonal_order: tuple) -> dict:
    r   = residuals.dropna().values
    res = SARIMAX(r, order=order, seasonal_order=seasonal_order,
                  enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    return {"result": res, "order": order, "seasonal_order": seasonal_order}


def simulate_sarima(fitted: dict, n: int, n_members: int,
                    rng: np.random.Generator) -> np.ndarray:
    sim = np.asarray(fitted["result"].simulate(nsimulations=n, repetitions=n_members,
                                               random_state=rng))
    if sim.ndim == 3:
        sim = sim[:, 0, :]   # drop k_endog=1 axis → (n, n_members)
    return sim


# --- Fit models ---
models_a = {}
models_b = {}
models_c = {}
models_d = {}
models_e = {}

for name, (delta_col, _, _) in VARIABLES.items():
    raw            = df[delta_col]
    models_a[name] = fit_ar1(raw)
    models_b[name] = fit_additive_ar(raw)
    models_c[name] = fit_sar1(raw)
    models_d[name] = fit_sarima(raw, order=(1,0,1), seasonal_order=(1,1,1,24))
    models_e[name] = fit_sarima(raw, order=(0,0,1), seasonal_order=(0,1,1,24))
    ma, mb, mc = models_a[name], models_b[name], models_c[name]
    print(f"{name:4s}  A: phi={ma['phi']:+.3f} sigma={ma['sigma']:.3f}"
          f"  |  B: phi={mb['phi']:+.3f} PHI={mb['PHI']:+.3f} sigma={mb['sigma']:.3f}"
          f"  |  C: phi={mc['phi']:+.3f} PHI={mc['PHI']:+.3f} sigma={mc['sigma']:.3f}"
          f"  |  D/E: fitted")

# --- Simulate ---
rng   = np.random.default_rng(RNG_SEED)
n     = len(df)
ens_a = {}
ens_b = {}
ens_c = {}
ens_d = {}
ens_e = {}

for name, (_, obs_col, clip_zero) in VARIABLES.items():
    obs_vals = df[obs_col].values[:, None]

    pert_a = simulate_ar1(models_a[name]["phi"], models_a[name]["sigma"] * SIGMA_SCALE,
                          n, N_MEMBERS, rng)

    mb     = models_b[name]
    pert_b = simulate_additive_ar(mb["phi"], mb["PHI"], mb["sigma"] * SIGMA_SCALE,
                                  n, N_MEMBERS, rng)

    mc     = models_c[name]
    pert_c = simulate_sar1(mc["phi"], mc["PHI"] * PHI_SCALE, mc["sigma"] * SIGMA_SCALE,
                           n, N_MEMBERS, rng)

    pert_d = simulate_sarima(models_d[name], n, N_MEMBERS, rng) * SIGMA_SCALE
    pert_e = simulate_sarima(models_e[name], n, N_MEMBERS, rng) * SIGMA_SCALE

    for pert, ens in [(pert_a, ens_a), (pert_b, ens_b), (pert_c, ens_c),
                      (pert_d, ens_d), (pert_e, ens_e)]:
        if clip_zero:
            pert[obs_vals[:, 0] == 0] = 0.0
        ens[name] = np.clip(obs_vals + pert, 0.0, None) if clip_zero else obs_vals + pert

print("\nEnsemble spread (std, time-mean):")
for name in VARIABLES:
    print(f"  {name:4s}  A={ens_a[name].std(axis=1).mean():.3f}"
          f"  B={ens_b[name].std(axis=1).mean():.3f}"
          f"  C={ens_c[name].std(axis=1).mean():.3f}"
          f"  D={ens_d[name].std(axis=1).mean():.3f}"
          f"  E={ens_e[name].std(axis=1).mean():.3f}")

# ----------------------------
# Visual diagnostics -- 3 panels per variable
#   col 0: ACF raw + A, B, C theoretical
#   col 1: ensemble fan (first 200 h)
#   col 2: ensemble fan zoomed (first 72 h)
# ----------------------------

fig     = plt.figure(figsize=(18, 4 * len(VARIABLES)))
gs      = gridspec.GridSpec(len(VARIABLES), 3, figure=fig, hspace=0.5, wspace=0.35)
lags_th = np.arange(N_LAGS + 1)

for row, name in enumerate(VARIABLES):
    raw      = df[DELTA_COLS[name]].dropna()
    obs_vals = df[OBS_COLS[name]].values
    unit     = UNITS[name]
    ma       = models_a[name]
    mb       = models_b[name]
    mc       = models_c[name]

    ax0 = fig.add_subplot(gs[row, 0])
    plot_acf(raw, lags=N_LAGS, ax=ax0, alpha=0.05, color="grey")
    ax0.plot(lags_th, ma["phi"] ** lags_th, color="steelblue", lw=1.8, ls="--",
             label=f"AR(1) alone  phi={ma['phi']:.2f}")
    ax0.plot(lags_th, theoretical_acf_ar24(mb["PHI"], N_LAGS), color="tomato", lw=1.8, ls=":",
             label=f"AR(24) alone  PHI={mb['PHI']:.2f}")
    ax0.plot(lags_th, theoretical_acf_additive_ar(mb["phi"], mb["PHI"], N_LAGS),
             color="darkorange", lw=1.8, ls="-.",
             label=f"B: Additive  phi={mb['phi']:.2f}  PHI={mb['PHI']:.2f}")
    ax0.plot(lags_th, theoretical_acf_sar1(mc["phi"], mc["PHI"] * PHI_SCALE, N_LAGS),
             color="seagreen", lw=1.8, ls="-",
             label=f"C: SAR(1)  phi={mc['phi']:.2f}  PHI={mc['PHI'] * PHI_SCALE:.2f} (x{PHI_SCALE})")
    for lag in [24, 48]:
        ax0.axvline(lag, color="black", lw=0.8, ls=":")
    ax0.set_title(f"{name} -- ACF")
    ax0.set_xlabel("lag (h)")
    ax0.legend(fontsize=8)

    for col, hours in [(1, 200), (2, 72)]:
        ax      = fig.add_subplot(gs[row, col])
        t_slice = slice(0, min(hours, n))
        t_plot  = np.arange(t_slice.start, t_slice.stop)
        for ens, color, lbl in [(ens_a[name], "steelblue",  "A: AR(1)"),
                                 (ens_b[name], "darkorange", "B: Additive AR(1,24)"),
                                 (ens_c[name], "seagreen",   "C: SAR(1)_24"),
                                 (ens_d[name], "mediumpurple", "D: SARIMA(1,0,1)(1,1,1)_24"),
                                 (ens_e[name], "crimson",    "E: SARIMA(0,0,1)(0,1,1)_24")]:
            p5, p95 = np.percentile(ens[t_slice], [5, 95], axis=1)
            ax.fill_between(t_plot, p5, p95, alpha=0.18, color=color)
            ax.plot(t_plot, ens[t_slice].mean(axis=1), color=color, lw=1.2, ls="--", label=lbl)
        ax.plot(t_plot, obs_vals[t_slice], "k-", lw=1.0, label="obs")
        ax.set_title(f"{name} -- fan (first {hours} h)")
        ax.set_xlabel("time step (h)")
        ax.set_ylabel(unit)
        ax.legend(fontsize=8)

plt.show()
