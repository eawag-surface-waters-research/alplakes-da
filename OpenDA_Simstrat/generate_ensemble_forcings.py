"""
Generate N perturbed Forcing.dat files for the exercise_simstrat ensemble.

AR(1) noise is applied to u, v (wind components) and sol (solar radiation).
Air temperature is left unperturbed. Sigma is estimated from sub-daily
variability in the base Forcing.dat (residuals from a 24-step rolling mean).

Output: forcings/Forcing_0.dat (unperturbed control)
        forcings/Forcing_1.dat ... Forcing_N.dat (perturbed members)
"""

import os
import shutil
import numpy as np
import pandas as pd

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
FORCING_IN   = os.path.join(SCRIPT_DIR, "stochModel", "template", "Forcing.dat")
FORCINGS_DIR = os.path.join(SCRIPT_DIR, "forcings")

N_MEMBERS = 20
RNG_SEED  = 42

HEADER = "  Time [d]    u [m/s]    v [m/s]  Tair [°C] sol [W/m2] vap [mbar]  cloud [-] rain [m/hr]"
COLS   = ["time", "u", "v", "Tair", "sol", "vap", "cloud", "rain"]

# Variables to perturb and whether to clip negatives to zero
PERTURB_VARS = {
    "u":   False,
    "v":   False,
    "sol": True,   # solar radiation must stay >= 0
}


def fit_ar1(series):
    r = series.dropna().values
    phi = float(np.corrcoef(r[:-1], r[1:])[0, 1])
    sigma = float(r.std() * np.sqrt(max(1 - phi**2, 0)))
    return phi, sigma


def simulate_ar1(phi, sigma, n, n_members, rng):
    noise = rng.standard_normal((n, n_members)) * sigma
    out = np.zeros((n, n_members))
    for t in range(1, n):
        out[t] = phi * out[t - 1] + noise[t]
    return out


df = pd.read_csv(FORCING_IN, sep=r"\s+", names=COLS, skiprows=1)
n  = len(df)
print(f"Loaded {n} rows from {FORCING_IN}")

os.makedirs(FORCINGS_DIR, exist_ok=True)

# Fit AR(1) using sub-daily residuals from a 24-step rolling mean
models = {}
for var in PERTURB_VARS:
    residuals = df[var] - df[var].rolling(24, center=True, min_periods=1).mean()
    phi, sigma = fit_ar1(residuals)
    models[var] = (phi, sigma)
    print(f"{var:4s}  phi={phi:+.3f}  sigma_innov={sigma:.4f}")

rng = np.random.default_rng(RNG_SEED)
perturbed = {}
for var, clip_zero in PERTURB_VARS.items():
    phi, sigma = models[var]
    pert       = simulate_ar1(phi, sigma, n, N_MEMBERS, rng)
    ensemble   = df[var].values[:, None] + pert
    if clip_zero:
        nighttime           = df["sol"].values < 1.0
        ensemble[nighttime] = 0.0
        ensemble            = np.clip(ensemble, 0.0, None)
    perturbed[var] = ensemble

# Forcing_0.dat — unperturbed control (copy of template)
shutil.copy2(FORCING_IN, os.path.join(FORCINGS_DIR, "Forcing_0.dat"))
print("Saved Forcing_0.dat (unperturbed)")

for i in range(N_MEMBERS):
    rows = np.column_stack([
        df["time"].values,
        perturbed["u"][:, i],
        perturbed["v"][:, i],
        df["Tair"].values,
        perturbed["sol"][:, i],
        df["vap"].values,
        df["cloud"].values,
        df["rain"].values,
    ])
    out_path = os.path.join(FORCINGS_DIR, f"Forcing_{i + 1}.dat")
    np.savetxt(out_path, rows, fmt="%10.4f", header=HEADER, comments="")
    print(f"Saved Forcing_{i + 1}.dat")

print(f"\nDone — {N_MEMBERS + 1} files saved to {FORCINGS_DIR}")
