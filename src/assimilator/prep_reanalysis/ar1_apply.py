"""Part 2 — apply AR(1) forcing perturbations from perturbations/<lake>.json.

Reads the fitted (phi, sigma) per variable, simulates fresh AR(1) noise for each
ensemble member, adds it to the control Forcing.dat, and writes the perturbed
Forcing.dat into ensemble1..N. Needs only numpy/pandas + the committed JSON + the
control forcing — no ICON, no residual fitting (that is fit_perturbations.py).
"""
import json
import logging
import os
import numpy as np
import pandas as pd

from ..functions import ROOT, FORCING_HEADER, SIMSTRAT_REF_YEAR

logger = logging.getLogger(__name__)

# variable -> (control column, clip-to-zero at night?)
PERTURB_VARS = {"U": ("U_std", False), "V": ("V_std", False), "GLOB": ("GLOB_std", True)}


# Note: AR(1) cold-start. out[0]=0 for all members -> zero forcing spread at t=0,
# suppressed for the first ~1/(1-phi) steps (and noise[0] is generated but unused). Negligible
# in practice. Intended.
def _simulate_ar1(phi: float, sigma: float, n: int, n_members: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal((n, n_members)) * sigma
    out   = np.zeros((n, n_members))
    for t in range(1, n):
        out[t] = phi * out[t - 1] + noise[t]
    return out


def _load_params(lake: str, perturb_dir: str) -> dict:
    json_path = os.path.join(perturb_dir, f"{lake}.json")
    if not os.path.isfile(json_path):
        raise FileNotFoundError(
            f"{json_path} not found — run fit_perturbations.py (needs the ICON API / EAWAG VPN) "
            f"or provide perturbations/{lake}.json")
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def perturbate(args: dict, params: dict = None) -> None:
    lake                 = args["lake"]
    standard_inputs_path = args["standard_inputs_path"]
    ensemble_base        = args["ensemble_base"]
    n_members            = args["n_members"]
    rng_seed             = args.get("rng_seed", 42)
    sigma_scale          = args.get("sigma_scale", 1.0)
    ref_year             = args.get("ref_year", SIMSTRAT_REF_YEAR)
    perturb_dir          = args.get("perturbations_dir", os.path.join(ROOT, "perturbations"))

    if params is None:
        params = _load_params(lake, perturb_dir)
    variables = params["variables"]

    # Control Forcing.dat as the base signal, over the assimilation window
    t0  = pd.Timestamp(f"{ref_year}-01-01")
    std = pd.read_csv(
        os.path.join(standard_inputs_path, "Forcing.dat"),
        sep=r"\s+",
        names=["time_days", "U_std", "V_std", "T_std", "GLOB_std", "vap_std", "cloud_std", "rain_std"],
        skiprows=1,
    )
    # Forcing.dat time_days is 0-based (day 0 = ref_year Jan 1), the SAME axis as the par's
    # "Start d" and T_out's "Datetime" (load_T). Verified: file spans time_days 0..16435 =
    # 1981-01-01..2025-12-31. (Was off by one — a `- 1` here treated it as 1-based, shifting the
    # perturbation window +1 day and dropping the first assimilation day.)
    std["time"] = (t0 + pd.to_timedelta(std["time_days"], unit="D")).dt.round("h").dt.tz_localize("UTC")
    start = pd.Timestamp(args["start_date"]).tz_convert("UTC")
    end   = pd.Timestamp(args["end_date"]).tz_convert("UTC")
    df    = std[(std["time"] >= start) & (std["time"] <= end)].reset_index(drop=True)
    if df.empty:
        raise ValueError(f"Control Forcing.dat has no rows in [{start}, {end}] for {lake}")
    n = len(df)

    # Note: forcing perturbation is seeded (rng_seed) -> identical ensemble forcing every
    # run, while the EnKF obs-perturbation rng (enkf.py) is unseeded. Mixed reproducibility... 
    # need to choose but for now not essential. Acknowledged.
    rng   = np.random.default_rng(rng_seed)
    night = df["GLOB_std"].values < 1.0   # night mask from the control's solar (no ICON at apply time)

    # Note: U and V are perturbed with independent AR(1) draws (separate phi/sigma), so
    # their cross-correlation is ignored. Intended.
    perturbed = {}
    for name, (std_col, clip_zero) in PERTURB_VARS.items():
        p    = variables[name]
        pert = _simulate_ar1(p["phi"], p["sigma"] * sigma_scale, n, n_members, rng)
        if clip_zero:
            pert[night] = 0.0
        ensemble = df[std_col].values[:, None] + pert
        if clip_zero:
            ensemble[night, :] = 0.0
            # Note: GLOB clipped at 0 only (no upper bound) -> a member's solar can be
            # perturbed above the physical clear-sky maximum. Acknowledged.
            ensemble = np.clip(ensemble, 0.0, None)
        perturbed[name] = ensemble

    spreads = {name: arr.std(axis=1).mean() for name, arr in perturbed.items()}
    logger.info(f"{lake}: mean ensemble spread — " + ", ".join(f"{k}={v:.3f}" for k, v in spreads.items()))

    # Overwrite Forcing.dat in each member (ensemble1..N); ensemble0 is the unperturbed control.
    for i in range(n_members):
        member_dir = os.path.join(ensemble_base, f"ensemble{i + 1}")
        if not os.path.isdir(member_dir):
            raise FileNotFoundError(
                f"{member_dir} missing — run the copy step (main.py) before perturbate")
        rows = np.column_stack([
            df["time_days"].values,
            perturbed["U"][:, i],
            perturbed["V"][:, i],
            df["T_std"].values,            # temperature: unperturbed
            perturbed["GLOB"][:, i],
            df["vap_std"].fillna(0).values,
            df["cloud_std"].fillna(0).values,
            df["rain_std"].fillna(0).values,
        ])
        np.savetxt(
            os.path.join(member_dir, "Forcing.dat"),
            rows, fmt="%10.4f", header=FORCING_HEADER, comments="",
        )

    logger.info(f"{lake}: perturbed Forcing.dat written to ensemble1..{n_members} -> {ensemble_base}")
