# OpenDA Course 2025 — Summary & Connection to exercise_simstrat

Based on: *OpenDA Course 2025*, Nils van Velzen & Martin Verlaan, February 27 2026.

---

## 1. The OpenDA application structure

Every OpenDA experiment is defined by a `.oda` file (the "main configuration file"). It wires together four components:

| Component | Role | Our file |
|---|---|---|
| `stochObserver` | Provides observations and their uncertainty | `stochObserver/timeSeriesFormatter.xml` |
| `stochModelFactory` | Creates and manages model instances | `stochModel/simstratStochModel.xml` (or via `parallel.xml`) |
| `algorithm` | Defines what to do at each analysis time | `algorithms/SequentialSimulation.xml` or `SequentialEnsembleSimulation.xml` |
| `resultWriter` | Writes results to disk | `sequentialSimulation_results.py` / `sequentialEnsembleSimulation_results.py` |

Our two `.oda` files:
- `SequentialSimulation.oda` — single model run, no ensemble
- `SequentialEnsembleSimulation.oda` — N+1 parallel ensemble runs

---

## 2. The black-box wrapper (three XML files)

The course explains that coupling an external model to OpenDA via the black-box interface requires three XML files. The pollution model example uses `polluteWrapper.xml`, `polluteModel.xml`, and `polluteStochModel.xml`. Our Simstrat setup follows the same pattern:

### 2.1 `simstratWrapper.xml` → *how to run the model*

Specifies:
- **`aliasDefinitions`**: named placeholders (`%templateDir%`, `%instanceDir%`, `%instanceNumber%`, `%binDir%`, `%configFile%`, `%stateFile%`) that make the config reusable across instances.
- **`initializeActionsUsingDirClone`**: clones `stochModel/template/` into `work/work<N>/` for each instance before the first run.
- **`computeActions`**: what to execute at each time step — our `simstrat_wrapper.py` (Linux) or `simstrat_wrapper.bat` (Windows), with `--config Settings.par`.
- **`checkOutput`**: verifies that `T_0m.csv`, `T_10m.csv`, `T_20m.csv` exist after each run.
- **`inputOutput`**: three data objects — `time_control.yaml` (AsciiKeywordDataObject), `temperature_state.txt` (AsciiVectorDataObject), `timeSeriesFormatter.xml` (TimeSeriesFormatterDataObject).

### 2.2 `simstratModel.xml` → *the deterministic model*

Specifies:
- **`wrapperConfig`**: reference to `simstratWrapper.xml`.
- **`aliasValues`**: concrete values for the aliases (`templateDir=template`, `instanceDir=../work/work`, `binDir=bin`, `configFile=Settings.par`, `stateFile=temperature_state.txt`).
- **`timeInfoExchangeItems`**: maps `start_time`, `time_step`, `end_time` to entries in `time_control.yaml`. OpenDA writes these before each call; `simstrat_wrapper.py` reads them to set the Simstrat simulation window.
- **`exchangeItems`**: all model variables OpenDA can read/write — `temperature.state`, `T_0m`, `T_10m`, `T_20m`.

### 2.3 `simstratStochModel.xml` → *the stochastic model*

Specifies:
- **`modelConfig`**: reference to `simstratModel.xml`.
- **`vectorSpecification`**:
  - `<state>`: `temperature.state` — the vector OpenDA can perturb and update.
  - `<predictor>`: `T_0m`, `T_10m`, `T_20m` — model output at observation locations, compared against the stochObserver.

No noise models are declared here because our ensemble spread comes from pre-generated perturbed `Forcing.dat` files, not from OpenDA's built-in stochastic perturbation.

---

## 3. Exchange items and the state vector

The course explains that exchange items come in three categories:

| Category | Purpose | Our items |
|---|---|---|
| **State** | Vector manipulated by the filter | `temperature.state` (7 depth levels) |
| **Predictor** | Model output at observation locations | `T_0m`, `T_10m`, `T_20m` |
| **Parameters** | Model parameters (for calibration) | Not used in this experiment |

The `temperature.state` vector holds temperatures at the 7 IC depth levels `[0, -10, -20, -30, -40, -50, -95 m]`. It is declared as the state vector and maintained by `simstrat_wrapper.py` (read at the start of each window, updated from `T_out.dat` at the end), but it is **not the actual restart mechanism**.

The real restart is driven by the binary `simulation-snapshot.dat` because the wrapper always sets `Continue from last snapshot = True` in `Settings.par`. Simstrat therefore ignores `InitialConditions.dat` (which is rebuilt from `temperature_state.txt`) and restarts from the snapshot. The `temperature_state.txt` round-trip is effectively a no-op in the current setup.

This has an important implication for EnKF: if OpenDA were to update `temperature.state` (writing corrected temperatures to `temperature_state.txt`), the model would still restart from the unmodified binary snapshot and ignore the correction. Two options to fix this when moving to EnKF:

- **Option A** — switch to text restart (`Use text restart = True` in `Settings.par`), so `InitialConditions.dat` drives the restart and the OpenDA correction propagates.
- **Option B** — have the wrapper inject the corrected state directly into the binary snapshot (requires knowledge of the Simstrat snapshot format).

---

## 4. Analysis times and the sequential loop

The course explains that OpenDA steps through time between analysis times, running the model for each window. Analysis times can be fixed or derived from observation times:

```xml
<analysisTimes type="fromObservationTimes" />
```

In our setup, the observations are daily (one value per day per depth). OpenDA therefore calls `simstrat_wrapper.py` once per day, each time advancing Simstrat by one day using Docker.

The sequential loop is:
1. OpenDA writes `time_control.yaml` with the next window's start/end times.
2. `simstrat_wrapper.py` reads `time_control.yaml`, sets Simstrat dates in `Settings.par`, and launches Docker.
3. Simstrat runs, writes `Results/T_out.dat` and `Results/simulation-snapshot.dat`.
4. Wrapper extracts `T_0m.csv`, `T_10m.csv`, `T_20m.csv` and updates `temperature_state.txt`.
5. OpenDA reads the predictor CSVs via `timeSeriesFormatter.xml`, compares them to observations.

---

## 5. Sequential simulation vs sequential ensemble simulation

The course introduces both in section 5 of the black-box exercise:

| | `SequentialSimulation` | `SequentialEnsembleSimulation` |
|---|---|---|
| Instances | 1 (`work0`) | N+1 (`work0` … `workN`) |
| Purpose | Verify model-obs alignment, no update | Quantify ensemble spread |
| Update step | None | None (spread only; no EnKF correction) |
| Noise on forcing | N/A | Pre-generated perturbed `Forcing.dat` |
| Noise on state | N/A | `stochInit=false` (no OpenDA perturbation) |

In the course, the ensemble members get stochastic forcing from OpenDA's noise models (`stochForcing=true`). In our setup we use `stochForcing=false` because the forcing uncertainty is already encoded in `forcings/Forcing_1.dat`…`Forcing_N.dat`, generated by `generate_ensemble_forcings.py` using AR(1) models fitted to ICON reanalysis − Forcing.dat residuals (equivalent to `src/ensembles_fromstandard.py`).

Our `SequentialEnsembleSimulation.xml`:
```xml
<ensembleSize>5</ensembleSize>
<mainModel  stochParameter="false" stochForcing="false" stochInit="false" />
<ensembleModel stochParameter="false" stochForcing="false" stochInit="false" />
```

`work0` = unperturbed control; `work1`–`work5` each get their own `Forcing_i.dat` injected by the wrapper based on the instance number parsed from the working directory name.

---

## 6. Parallel computing with `ThreadStochModelFactory`

The course (section 5.3) explains that running N ensemble members sequentially is slow because each Docker/model startup has overhead. The fix is wrapping the factory with `org.openda.models.threadModel.ThreadStochModelFactory`, configured via `parallel.xml`:

```xml
<threadConfigstoch>
    <maxThreads>6</maxThreads>
    <stochModelFactory className="org.openda.blackbox.wrapper.BBStochModelFactory">
        ...
    </stochModelFactory>
</threadConfigstoch>
```

The course recommendation is to set `maxThreads` to the number of available CPU cores. In our `SequentialEnsembleSimulation.oda`, the `stochModelFactory` entry points to `parallel.xml` rather than directly to `simstratStochModel.xml`. This makes all 6 instances (1 main + 5 ensemble) launch their Docker containers concurrently at each time step.

---

## 7. The stochObserver

The course explains that the `StochObserver` provides both observation values and their uncertainty (standard deviation). In our setup:

- **Source**: `stochObserver/T_1m_real.csv` … `T_40m_real.csv` — 15 files, daily temperature observations at 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 25, 30, 35, 40 m from Castagnola.
- **Format**: `time,value` CSV with Simstrat days since 1981-01-01.
- **Class**: `org.openda.observers.TimeSeriesFormatterStochObserver`, configured by `stochObserver/timeSeriesFormatter.xml`.
- **Observation uncertainty**: `standardDeviation="0.5"` °C uniformly across all depths in `timeSeriesFormatter.xml`.

These observations drive the analysis time schedule (one step per obs time). They are compared against predictors `T_1m`…`T_40m` during the analysis step.

---

## 8. Result writers and output format

The course uses `PythonResultWriter`, which writes results as executable Python that populates named lists:

```python
analysis_time.append(16073.0)
pred_f_central.append([8.07, 8.09, 8.10])   # model at obs locations
obs.append([7.94, 7.92, 7.90])              # observed values
x_f_central.append([8.07, 8.09, ...])       # full state vector
```

At the end, all lists are `np.vstack`-ed into arrays. Our `plot_results.py` loads `sequentialSimulation_results.py` via `exec()` and plots `pred_f_central` vs `obs` at each depth.

For the ensemble, our `plot_ensemble_results.py` bypasses the results file entirely and reads `work/work{i}/Results/T_out.dat` directly — this gives the full time series for each member, not just the values at analysis times.

---

## 9. The Simstrat-specific state update mechanism

This is the central design challenge of the OpenDA–Simstrat EnKF and the reason a dedicated EnKF wrapper (`simstrat_wrapper_enkf.py`) exists.

### Why a naive coupling fails

Simstrat restarts from a binary snapshot (`simulation-snapshot.dat`) rather than from `InitialConditions.dat`. If OpenDA writes a corrected temperature profile to `temperature_state.txt` after the Kalman update, Simstrat would simply ignore it at the next call — it reads the snapshot, which was written at the end of the previous run and carries the *uncorrected* state.

### The solution: full-grid state injection via snapshot_io

The EnKF wrapper closes the loop by using `snapshot_io` (from `snapshot/snapshot_io.py`) to directly overwrite the temperature array inside the binary snapshot before each Simstrat call. The full cycle per analysis step is:

**End of call `t` (post-run):**
1. Simstrat finishes, writes `Results/simulation-snapshot.dat` and `Results/T_out.dat`.
2. Wrapper reads the full T profile (all N grid cells, e.g. 576) from the snapshot via `read_snapshot`.
3. Wrapper writes those N values to `temperature_state.txt`.

**OpenDA analysis step (between calls):**
4. OpenDA reads `temperature.state` (= `temperature_state.txt`, N values).
5. OpenDA computes the Kalman gain and writes the corrected profile back to `temperature_state.txt`.

**Start of call `t+1` (pre-run):**
6. Wrapper reads `temperature_state.txt` (now N corrected values).
7. Wrapper calls `read_snapshot` on the existing snapshot, overwrites `snap.model['T']` with the corrected values, and calls `write_snapshot` — all other state (turbulence, mixing, velocities) is preserved.
8. Simstrat runs with `Continue from last snapshot = True` and picks up the corrected temperature field.

### First-run bootstrap

On the very first call, `temperature_state.txt` contains only 7 values (the IC depth levels from the template). The wrapper detects this via a size guard (`len(T_state) > len(IC_DEPTHS)`), skips the injection, and lets Simstrat start from the warmup snapshot as-is. After that first run the state file is upgraded to the full N-cell profile, and injection is active for every subsequent call.

### Why this preserves physical consistency

Injecting only the T field into the snapshot — while leaving turbulent kinetic energy, dissipation rate, and velocities unchanged — is a deliberate choice. It avoids reinitialising the turbulence closure at every analysis step, which would cause unphysical transients. The EnKF correction is applied purely to temperature, consistent with what the observation operator and Kalman gain operate on.

---

## 10. Ensemble Kalman Filter (EnKF)

### 10.1 Algorithm

The EnKF approximates the Kalman filter by representing the error covariance with an ensemble of N model runs. At each analysis time the algorithm follows three stages:

**Forecast step** — each ensemble member $i$ is advanced from $t_{k-1}$ to $t_k$ independently:

$$x_f^i = M(x_a^i), \quad i = 1, \ldots, N$$

The ensemble mean and spread estimate the prior state and its uncertainty:

$$x_f = \frac{1}{N} \sum_{i=1}^{N} x_f^i$$

$$P_f \approx \frac{1}{N-1} \sum_{i=1}^{N} (x_f^i - x_f)(x_f^i - x_f)^\top$$

**Analysis step** — observations $y$ are assimilated via the Kalman update:

$$K = P_f H^\top (H P_f H^\top + R)^{-1} \quad \text{(Kalman gain)}$$

$$x_a^i = x_f^i + K(y^i - H x_f^i) \quad \text{(member update)}$$

where $H$ maps the state to observation space, $R$ is the observation error covariance, and $y^i = y + \varepsilon^i$ are perturbed observations ($\varepsilon^i \sim \mathcal{N}(0, R)$) added to keep the ensemble spread consistent.

**Key property** — the Kalman gain weights the correction:
- If $H P_f H^\top \gg R$ (model uncertain, obs precise): $K \approx H^{-1}$, analysis is pulled strongly toward obs.
- If $H P_f H^\top \ll R$ (model confident, obs noisy): $K \approx 0$, state barely changes.
- If spread is zero everywhere: $K = 0$, no correction is ever applied.

### 10.2 Configuration in this exercise

| File | Role |
|---|---|
| `EnKF.oda` / `parallel_enkf.xml` | Top-level experiment, points to EnKF algorithm |
| `algorithms/EnKF.xml` | Algorithm class `org.openda.algorithms.kalmanFilter.EnKF`, ensemble size 20, analysis times from observations |
| `stochModel/simstratModelEnKF.xml` | Deterministic model config (same wrapper as ensemble simulation) |
| `stochModel/simstratStochModelEnKF.xml` | Stochastic model — state vector `temperature.state`, predictors `T_1m`…`T_40m` (15 depths) |
| `stochModel/simstratWrapperEnKF.xml` | Black-box wrapper, clones template into `work_enkf/work<N>/` |
| `work_enkf/work0/` | Main (central) model — unperturbed control |
| `work_enkf/work1/`–`work_enkf/work20/` | Ensemble members — each uses a different pre-perturbed `Forcing.dat` |

The stochastic flags in `EnKF.xml`:
```xml
<mainModel   stochParameter="false" stochForcing="false" stochInit="false" />
<ensembleModel stochParameter="false" stochForcing="false" stochInit="false" />
```

These are `false` because forcing uncertainty is pre-baked in `Forcing_1.dat`…`Forcing_20.dat`, not injected by OpenDA at runtime. The ensemble spread therefore comes entirely from meteorological forcing differences between members.

### 10.3 Ensemble spread and Kalman gain in our run

Reading `std_x_f` from `enkf_results.py` (standard deviation of ensemble at forecast step):

- **Deep layers (z ≈ −287 m)**: std ≈ 0 — the 20 members have identical deep temperatures because the initial conditions are the same.
- **Intermediate depths**: std increases gradually as diverging surface forcing propagates downward.
- **Surface layers (z ≈ 0 m)**: std ≈ 0.15 °C — largest spread, driven directly by different wind/solar forcings.

At the observation depths (1–40 m, 15 levels) the spread is large enough that the Kalman gain is non-negligible. The analysis correction `x_a − x_f` is largest near the surface where ensemble spread is greatest.

### 10.4 A subtlety in OpenDA's Python output

Inspecting `enkf_results.py` reveals an important output convention:

| Variable | What it actually contains |
|---|---|
| `pred_f_central` | `H · x_f` — forecast prediction at obs locations (correct) |
| `pred_a_central` | `H · x_f` — **same as forecast**, computed before the Kalman update |
| `x_f_central` | Full state vector before update (correct) |
| `x_a_central` | Full state vector **after** Kalman update (correct) |

`pred_a_central` is NOT `H · x_a`. OpenDA computes it at the analysis step for the purpose of logging the innovation (`y − pred_f`), before the state is updated. This means:

- **Depth profiles** (plotting `x_f_central` vs `x_a_central` directly) correctly show the EnKF correction along the full water column.
- **Time series** using `pred_a_central` would show zero correction everywhere — misleading.

The fix is to extract the analysis state at observation depths directly from `x_a_central`:

```python
_obs_cols = [int(np.argmin(np.abs(lake_lev - z_vol - d))) for d in OBS_DEPTHS]
x_a_at_obs = np.column_stack([x_a_central[:, c] for c in _obs_cols])  # (n_steps, n_obs)
```

This gives the true post-analysis temperature at the 15 observation depths (1–40 m) for plotting against observations.

---

## 11. Extending the setup to compare multiple assimilation algorithms

### 11.1 Why the architecture makes this mostly cheap

Every OpenDA experiment is defined by a `.oda` file that wires together four independent components (stochObserver, stochModelFactory, algorithm, resultWriter). The stochModel coupling — including the `simstrat_wrapper_enkf.py` state injection via `snapshot_io` — is algorithm-agnostic: OpenDA writes a corrected `temperature_state.txt` per member, and the wrapper injects it into the binary snapshot before the next call regardless of how the correction was computed. Swapping algorithms therefore only requires:

1. A new `.oda` file with a different `<algorithm className="...">`.
2. A new algorithm config XML in `algorithms/`.
3. A distinct `resultWriter` output filename to avoid collisions.

The stochObserver, parallel model factory (`parallel_enkf.xml`), stochModel XML stack, and wrapper scripts are shared verbatim across all experiments.

### 11.2 Algorithms available in OpenDA 3.4.0

The following sequential ensemble algorithms exist in `openda_3.4.0/xmlSchemas/algorithm/` and are bundled in `algorithms.jar`:

| Algorithm | OpenDA class | XSD schema | Config effort |
|---|---|---|---|
| **EnKF** | `kalmanFilter.EnKF` | `enkf.xsd` | Already implemented |
| **EnSR** (Ensemble Square Root) | `kalmanFilter.EnSR` | `ensr.xsd` | Rename `EnKFConfig` → `EnsrConfig`, update className — same fields |
| **EWPF** (Ensemble Weighted Particle Filter) | `kalmanFilter.EWPF` | `ewpf.xsd` | Rename `EnKFConfig` → `EWPFConfig`, update className — same fields |
| **Particle Filter** | `particleFilter.ParticleFilter` | `particleFilter.xsd` | Same fields + optional `<samplingMethod>` — see §11.4 |
| **Steady State Filter** | `kalmanFilter.SteadyStateKalmanFilter` | `steadyStateFilter.xsd` | Requires a pre-computed Kalman gain from a prior EnKF run |

### 11.3 Minimal-effort additions: EnSR and EWPF

EnSR and EWPF share the `SequentialEnsembleAlgorithmConfigType` with EnKF — identical elements (`analysisTimes`, `mainModel`, `ensembleSize`, `ensembleModel`). Adding either is a pure XML operation:

**`algorithms/EnSR.xml`**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<EnsrConfig xmlns="http://www.openda.org"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openda.org http://schemas.openda.org/algorithm/ensr.xsd">

    <analysisTimes type="fromObservationTimes" />
    <mainModel   stochParameter="false" stochForcing="false" stochInit="false" />
    <ensembleSize>20</ensembleSize>
    <ensembleModel stochParameter="false" stochForcing="false" stochInit="false" />
</EnsrConfig>
```

**`EnSR.oda`** — copy `EnKF.oda`, change:
```xml
<algorithm className="org.openda.algorithms.kalmanFilter.EnSR">
    <workingDirectory>./algorithms</workingDirectory>
    <configString>EnSR.xml</configString>
</algorithm>
...
<configFile>ensr_results.py</configFile>
```

The `work_enkf/` directory, both stochModel XML stacks, and `simstrat_wrapper_enkf.py` are unchanged. EWPF follows the identical pattern with `EWPFConfig` / `EWPF` / `ewpf_results.py`.

### 11.4 The Particle Filter — what needs care

The Particle Filter does not compute a linear Kalman update. Instead it:
1. Weights each ensemble member by its likelihood given the observations.
2. Resamples: clones high-weight members, drops low-weight ones.

The `simstrat_wrapper_enkf.py` state injection (read `temperature_state.txt` → overwrite snapshot T field) survives resampling unchanged — OpenDA still writes each member's state to its own instance directory, and the wrapper reads it before the next model call.

**The real problem is the pre-baked forcing.** After resampling, two members may share the same corrected snapshot state but continue advancing with *different* `Forcing.dat` files (because forcing files are tied to directory index `work_enkf/work{i}/`). The forcing diversity is no longer aligned with the resampled state diversity. For a rigorous PF experiment, one of two approaches is needed:

- **Option A — live resampling of forcing**: When the wrapper detects it has been cloned (e.g., by comparing snapshot state with the prior step's unperturbed state), it resamples a new forcing perturbation on the fly. Requires some bookkeeping.
- **Option B — accept the mismatch as a known limitation**: The forcing perturbations are small (~AR(1) residuals) and the resampling step is rare enough that the mismatch has limited impact over a short experiment window. Document it explicitly.

For an initial comparison this limitation can be accepted; for publication-quality results Option A is needed.

### 11.5 Suggested comparison setup

Run three `.oda` files sequentially (or in separate directories) against the same observation dataset:

```
EnKF.oda          → enkf_results.py       (already working)
EnSR.oda          → ensr_results.py       (one new .oda + one algorithm XML)
EWPF.oda          → ewpf_results.py       (one new .oda + one algorithm XML)
```

Each run populates its own result file. A single comparison script loads all three via `exec()` and overlays RMSE, bias, and ensemble spread at the 15 observation depths.

Note: each run needs its own `work_enkf/` directory tree (or the directory must be cleaned between runs), because the binary snapshots from one run's analysis step must not contaminate the next.

---

## 12. Full-year run: results and new considerations

The EnKF completed a full calendar year of daily analysis steps (Simstrat days 16073.5–16435.5, i.e., 2025-01-03 → 2025-12-31, 363 steps) with 20 ensemble members in approximately **4.6 hours** (16 657 s) on 21 threads (`maxThreads=21`). This is the first run long enough to reveal effects that are invisible over short windows.

### 12.1 Seasonal variation in ensemble spread and Kalman gain

The AR(1) forcing perturbations (wind speed and shortwave radiation residuals) drive ensemble divergence from the surface downward. Over a full year the divergence is not stationary:

- **Winter (weak stratification, Jan–Mar)**: The water column is nearly isothermal; surface forcing differences mix quickly through the column. Ensemble spread is low everywhere, so the Kalman gain `K ≈ 0` and the filter barely corrects.
- **Late spring / summer (strong stratification, May–Sep)**: Surface spread peaks (σ ≈ 0.15–0.3 °C) as solar perturbations amplify. The thermocline acts as a barrier: spread is large above it and near-zero below ~40 m. Corrections are largest at the 1–15 m depths where both spread and innovation are large.
- **Autumn mixing (Oct–Nov)**: As stratification breaks down the surface-corrected state mixes downward, propagating the accumulated analysis corrections into the seasonal thermocline for the first time.

**Implication**: RMSE reduction from EnKF is largest during stratified periods and near-zero in winter. Reporting a single annual mean RMSE therefore understates summer performance improvement and may overstate annual skill.

### 12.2 Deep-layer temperature drift over a year

Depths below ~40 m have ensemble spread ≈ 0 (identical initial conditions, negligible forcing-driven divergence). The Kalman gain for those cells is therefore always zero — no correction is ever applied. Any model bias in the deep water (hypolimnion) accumulates entirely unchecked over the 365-day run.

This is not a bug in the OpenDA setup: it is a fundamental limitation of using forcing-only ensemble perturbations. Fixing it requires either:
- Adding a small model-error noise term to the state (state-space noise, `stochForcing=true` in OpenDA or a manual additive inflation),
- Or inflating the ensemble covariance (multiplicative inflation) so that deep cells get a non-zero gain even when member spread is negligible.

The custom `main_EnKF.py` uses `INFLATION = 1.05` (multiplicative) for this reason. The OpenDA run currently has no inflation, which makes it a clean reference but a less robust operational filter.

### 12.3 `pred_a_central` over a full year: cumulative misleading signal

The convention described in §10.4 — that `pred_a_central` equals `H·x_f` (pre-analysis), not `H·x_a` — means any **annual summary statistic computed from `pred_a_central` shows zero net correction**. Over 363 steps this appears as a perfectly flat bias between the "analysis" prediction and the observations, which looks like filter divergence. Always use `x_a_central` columns projected to observation depths when computing annual RMSE or bias for the EnKF analysis state.

### 12.4 Observation gaps and their effect on the filter

The Castagnola daily observations may have multi-day gaps (sensor maintenance, ice cover, data quality). When a day has no observation, OpenDA still runs all 21 model instances forward but skips the analysis step — the ensemble continues diverging with no correction. After a long gap the spread can widen significantly, and the next available observation triggers a large correction that may be physically implausible.

Over a full year this happened at several points and is visible in the `enkf_results.py` as steps where `obs` contains `NaN` but `x_f_central` and `x_a_central` are identical. Monitoring gap frequency is therefore important when interpreting annual RMSE: a year with many gaps naturally yields worse filter performance even if the filter is correctly configured.

### 12.5 Cross-validation against main_EnKF.py is now meaningful

With a full year of results from both OpenDA EnKF (in `work_enkf/`) and the custom Python EnKF (`assimilation/upperlugano/`), the `analyze_results_general_v2.py` script can compute side-by-side RMSE profiles at the 15 observation depths. Differences between the two should be attributable to:

| Source of difference | Expected effect |
|---|---|
| OpenDA has no multiplicative inflation; `main_EnKF.py` uses 1.05 | OpenDA analysis state drifts slightly more at depth |
| `main_EnKF.py` applies obs at 0.5 m only; OpenDA uses 15 depths | OpenDA should outperform at mid-depth (5–30 m) |
| Perturbed forcing differs slightly in generation (same AR(1) method, different random seed) | Small, random RMSE differences |

If the annual RMSE profiles are qualitatively consistent (same depth ordering, same seasonal pattern), the two implementations are cross-validated. Large systematic differences at specific depths would indicate a configuration mismatch worth diagnosing.

### 12.6 Computational budget and planning

The full-year run (363 steps × 21 instances) took 16 657 s ≈ **4.6 h**. This implies roughly **46 s per analysis step** across all threads (21 × ~20 s Docker startup + run per step). Key takeaways:

- A second full-year run with a different algorithm (EnSR, EWPF) costs the same ~4.6 h. Plan accordingly when comparing algorithms.
- Doubling the ensemble to 40 members increases wall-clock time only if thread count is not also increased (the bottleneck is `maxThreads`, not ensemble size, up to the available CPU count).
- Extending the simulation period beyond one year does not require regenerating forcings if new `Forcing_i.dat` files are appended; the AR(1) perturbation method is stationary.
