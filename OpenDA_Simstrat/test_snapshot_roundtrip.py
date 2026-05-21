"""Round-trip test for snapshot_io + full-state temperature_state.txt.

Three tests:
  1. Unmodified round-trip  — write_snapshot → read_snapshot, T must be bit-exact.
  2. Perturbed round-trip   — modify T in memory, write, read back, verify preserved.
  3. State-file round-trip  — write full T to temperature_state.txt, read back,
                               inject into snapshot, verify the snapshot T matches.

Inspired by check_initial_snapshot.py; uses the same path resolution.
"""

import os
import sys
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

# ── path resolution (works as script or notebook cell) ────────────────────────
_here = globals().get("__file__", None)
if _here is not None:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(_here))
    ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
else:
    _cwd = os.getcwd()
    ROOT = _cwd
    while ROOT and not os.path.isdir(os.path.join(ROOT, "snapshot")):
        _parent = os.path.dirname(ROOT)
        if _parent == ROOT:
            raise RuntimeError("Cannot locate project root (snapshot/ not found)")
        ROOT = _parent
    SCRIPT_DIR = os.path.join(ROOT, "testing_simple", "exercise_simstrat")

sys.path.insert(0, os.path.join(ROOT, "snapshot"))
from snapshot_io import read_snapshot, write_snapshot

SNAPSHOT_PATH = os.path.join(
    SCRIPT_DIR, "stochModel", "template", "Results", "simulation-snapshot.dat"
)
PAR_PATH = os.path.join(SCRIPT_DIR, "stochModel", "template", "Settings.par")

PERTURBATION = 1.0  # °C added to every cell in the perturbed test


# ── helpers ───────────────────────────────────────────────────────────────────

def snap_depths(snap):
    """Return depth array (m, positive downward) matching snap.model['T']."""
    T = snap.model["T"]
    z_vol = snap.grid["z_volume"][-len(T):]
    lake_lev = snap.grid["lake_level"]
    depths = lake_lev - z_vol
    return depths


def write_state_file(path, T_array):
    """Write full temperature profile to an ASCII state file (one value per line)."""
    with open(path, "w") as f:
        for t in T_array:
            f.write(f"{t:.6f}\n")


def read_state_file(path):
    """Read full temperature profile from ASCII state file."""
    with open(path) as f:
        return np.array([float(line.strip()) for line in f if line.strip()])


# ── test 1: unmodified round-trip ─────────────────────────────────────────────

print("=" * 60)
print("Test 1 — unmodified round-trip")
print("=" * 60)

snap_orig = read_snapshot(SNAPSHOT_PATH, par_path=PAR_PATH)
T_orig = snap_orig.model["T"].copy()
depths = snap_depths(snap_orig)

print(f"  Grid cells (T):  {len(T_orig)}")
print(f"  Depth range:     {depths.min():.1f} – {depths.max():.1f} m")
print(f"  T range:         {T_orig.min():.4f} – {T_orig.max():.4f} °C")

with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as tmp:
    tmp_path = tmp.name

write_snapshot(tmp_path, snap_orig)
snap_back = read_snapshot(tmp_path, par_path=PAR_PATH)
T_back = snap_back.model["T"]

max_diff = np.max(np.abs(T_back - T_orig))
print(f"  Max |T_back - T_orig|: {max_diff:.2e}  (should be 0.0)")
assert max_diff == 0.0, f"FAIL: unmodified round-trip not bit-exact (max diff {max_diff})"
print("  PASS")

os.unlink(tmp_path)


# ── test 2: perturbed round-trip ──────────────────────────────────────────────

print()
print("=" * 60)
print(f"Test 2 — perturbed round-trip (+{PERTURBATION} °C to all cells)")
print("=" * 60)

snap_pert = read_snapshot(SNAPSHOT_PATH, par_path=PAR_PATH)
snap_pert.model["T"] = snap_pert.model["T"] + PERTURBATION

with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as tmp:
    tmp_path = tmp.name

write_snapshot(tmp_path, snap_pert)
snap_pert_back = read_snapshot(tmp_path, par_path=PAR_PATH)
T_pert_back = snap_pert_back.model["T"]
T_pert_expected = T_orig + PERTURBATION

max_diff = np.max(np.abs(T_pert_back - T_pert_expected))
print(f"  Max |T_pert_back - (T_orig + {PERTURBATION})|: {max_diff:.2e}  (should be 0.0)")
assert max_diff == 0.0, f"FAIL: perturbed round-trip not exact (max diff {max_diff})"
print("  PASS")

os.unlink(tmp_path)


# ── test 3: state-file round-trip ─────────────────────────────────────────────

print()
print("=" * 60)
print("Test 3 — state-file round-trip (snapshot -> txt -> snapshot)")
print("=" * 60)

# Simulate what the wrapper will do at end-of-run: dump full T to state file
with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp:
    state_path = tmp.name

write_state_file(state_path, T_orig)
T_from_file = read_state_file(state_path)

print(f"  Values written:  {len(T_orig)}")
print(f"  Values read back:{len(T_from_file)}")
assert len(T_from_file) == len(T_orig), "FAIL: length mismatch after state-file round-trip"

max_diff = np.max(np.abs(T_from_file - T_orig))
print(f"  Max |T_file - T_orig|: {max_diff:.2e}  (expect < 1e-5, limited by %.6f precision)")

# Simulate what the wrapper will do at start-of-run: inject state into snapshot
with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as tmp:
    injected_path = tmp.name

snap_inject = read_snapshot(SNAPSHOT_PATH, par_path=PAR_PATH)
snap_inject.model["T"] = T_from_file          # direct 1:1 assignment — no interpolation
write_snapshot(injected_path, snap_inject)

snap_inject_back = read_snapshot(injected_path, par_path=PAR_PATH)
T_inject_back = snap_inject_back.model["T"]
max_diff2 = np.max(np.abs(T_inject_back - T_orig))
print(f"  Max |T_inject_back - T_orig|: {max_diff2:.2e}  (expect < 1e-5)")
assert max_diff2 < 1e-4, f"FAIL: injected snapshot T does not match original (max diff {max_diff2})"
print("  PASS")

os.unlink(state_path)
os.unlink(injected_path)


# ── plot ──────────────────────────────────────────────────────────────────────

print()
print("Generating plot...")

fig, axes = plt.subplots(1, 2, figsize=(10, 7))

# Left: full profile
ax = axes[0]
ax.plot(T_orig, depths, color="steelblue", lw=2, label="original T")
ax.plot(T_orig + PERTURBATION, depths, color="tomato", lw=2, ls="--",
        label=f"original + {PERTURBATION} °C")
ax.invert_yaxis()
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Depth (m)")
ax.set_title("Full-grid T profile")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Right: difference after state-file round-trip (shows ASCII precision floor)
ax2 = axes[1]
diff = T_from_file - T_orig
ax2.plot(diff, depths, color="darkorange", lw=1.5)
ax2.axvline(0, color="gray", lw=0.8, ls="--")
ax2.invert_yaxis()
ax2.set_xlabel("T_file − T_orig (°C)")
ax2.set_ylabel("Depth (m)")
ax2.set_title("State-file round-trip error\n(ASCII %.6f precision)")
ax2.grid(True, alpha=0.3)

plt.suptitle("test_snapshot_roundtrip.py — all 3 tests passed", fontsize=11)
plt.tight_layout()

out_path = os.path.join(SCRIPT_DIR, "snapshot_roundtrip_check.png")
plt.savefig(out_path, dpi=150)
print(f"Plot saved to: {out_path}")
plt.show()

print()
print("All tests passed.")
