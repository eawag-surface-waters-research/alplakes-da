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

In the course, the ensemble members get stochastic forcing from OpenDA's noise models (`stochForcing=true`). In our setup we use `stochForcing=false` because the forcing uncertainty is already encoded in `forcings/Forcing_1.dat`…`Forcing_N.dat`, generated by `generate_ensemble_forcings.py` using AR(1) models fitted to sub-daily variability.

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

- **Source**: `stochObserver/T_0m_real.csv`, `T_10m_real.csv`, `T_20m_real.csv` — daily temperature observations at 0, 10, 20 m from Castagnola.
- **Format**: `time,value` CSV with Simstrat days since 1981-01-01.
- **Class**: `org.openda.observers.TimeSeriesFormatterStochObserver`, configured by `stochObserver/timeSeriesFormatter.xml`.
- **Observation uncertainty**: defined in `timeSeriesFormatter.xml` — determines how much weight the filter places on observations vs model in an EnKF step.

These observations currently drive the analysis time schedule (one step per obs time). They are compared against predictors `T_0m`, `T_10m`, `T_20m` during the analysis step.

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

## 9. Towards EnKF (next step)

The course shows that moving from `SequentialEnsembleSimulation` to `EnKF` requires:

1. Switching `className` in the `.oda` to `org.openda.algorithms.kalmanFilter.EnKF`.
2. Adding a noise model in `simstratStochModel.xml` — either `stochInit=true` (perturb initial state) or `stochForcing=true` (perturb forcing). In our case, forcing perturbations are pre-baked, so `stochInit=true` on `temperature.state` is the natural choice for additional spread.
3. Setting observation uncertainty correctly in `timeSeriesFormatter.xml` — the balance between obs error and ensemble spread determines how aggressively the filter corrects the model.

The EnKF would then compute a Kalman gain from the ensemble covariance and update `temperature.state` in each member at every analysis time — closing the loop from open-loop ensemble simulation to full data assimilation.

**Fixing the restart mechanism for EnKF** — since the model currently restarts from the binary snapshot, OpenDA's corrections to `temperature.state` would be ignored. The preferred fix is to have the wrapper inject the corrected temperatures directly into the binary snapshot after the EnKF update step, using the `snapshot_io` module already available in the project (`snapshot/snapshot_io.py`). This preserves the full Simstrat internal state (turbulence, mixing) while applying the temperature correction.

---

## 10. Ensemble Kalman Filter (EnKF)

### 10.1 Algorithm

The EnKF approximates the Kalman filter by representing the error covariance with an ensemble of N model runs. At each analysis time the algorithm follows three stages:

**Forecast step** — each ensemble member `i` is advanced from `t_{k-1}` to `t_k` independently:

```
x_f^i = M(x_a^i)     (i = 1 … N)
```

The ensemble mean and spread estimate the prior state and its uncertainty:

```
x_f = (1/N) Σ x_f^i
P_f ≈ (1/(N-1)) Σ (x_f^i - x_f)(x_f^i - x_f)^T
```

**Analysis step** — observations `y` are assimilated via the Kalman update:

```
K   = P_f H^T (H P_f H^T + R)^{-1}     (Kalman gain)
x_a^i = x_f^i + K (y^i - H x_f^i)     (member update)
```

where `H` maps the state to observation space, `R` is the observation error covariance, and `y^i = y + ε^i` are perturbed observations (ε^i ~ N(0, R)) added to keep the ensemble spread consistent.

**Key property** — the Kalman gain weights the correction:
- If `H P_f H^T >> R` (model uncertain, obs precise): `K ≈ H^{-1}`, analysis is pulled strongly toward obs.
- If `H P_f H^T << R` (model confident, obs noisy): `K ≈ 0`, state barely changes.
- If spread is zero everywhere: `K = 0`, no correction is ever applied.

### 10.2 Configuration in this exercise

| File | Role |
|---|---|
| `EnKF.oda` / `parallel_enkf.xml` | Top-level experiment, points to EnKF algorithm |
| `algorithms/EnKF.xml` | Algorithm class `org.openda.algorithms.kalmanFilter.EnKF`, ensemble size 5, analysis times from observations |
| `stochModel/simstratModelEnKF.xml` | Deterministic model config (same wrapper as ensemble simulation) |
| `stochModel/simstratStochModelEnKF.xml` | Stochastic model — state vector `temperature.state`, predictors `T_0m/10m/20m` |
| `stochModel/simstratWrapperEnKF.xml` | Black-box wrapper, clones template into `work_enkf/work<N>/` |
| `work_enkf/work0/` | Main (central) model — unperturbed control |
| `work_enkf/work1/`–`work5/` | Ensemble members — each uses a different pre-perturbed `Forcing.dat` |

The stochastic flags in `EnKF.xml`:
```xml
<mainModel   stochParameter="false" stochForcing="false" stochInit="false" />
<ensembleModel stochParameter="false" stochForcing="false" stochInit="false" />
```

These are `false` because forcing uncertainty is pre-baked in `Forcing_1.dat`…`Forcing_5.dat`, not injected by OpenDA at runtime. The ensemble spread therefore comes entirely from meteorological forcing differences between members.

### 10.3 Ensemble spread and Kalman gain in our run

Reading `std_x_f` from `enkf_results.py` (standard deviation of ensemble at forecast step):

- **Deep layers (z ≈ −287 m)**: std ≈ 0 — the 5 members have identical deep temperatures because the initial conditions are the same.
- **Intermediate depths**: std increases gradually as diverging surface forcing propagates downward.
- **Surface layers (z ≈ 0 m)**: std ≈ 0.15 °C — largest spread, driven directly by different wind/air-temperature forcings.

At the observation depths (0 m, 10 m, 20 m) the spread is large enough that the Kalman gain is non-negligible. The analysis correction `x_a − x_f` reaches **~0.11 °C** at the surface.

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
x_a_at_obs = np.column_stack([x_a_central[:, c] for c in _obs_cols])  # (n_steps, 3)
```

This gives the true post-analysis temperature at 0 m, 10 m, 20 m for plotting against observations.
