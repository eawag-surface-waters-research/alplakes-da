import os
import shutil

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT, "standard_inputs")
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", "upperlugano")
N_MEMBERS = 20

# Files generated per-ensemble — don't overwrite them
SKIP = {"Forcing.dat"}

for i in range(1, N_MEMBERS + 1):
    dest_dir = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    os.makedirs(dest_dir, exist_ok=True)
    for fname in os.listdir(SRC_DIR):
        if fname in SKIP:
            continue
        src = os.path.join(SRC_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dest_dir, fname))
        elif os.path.isdir(src):
            dest_sub = os.path.join(dest_dir, fname)
            if os.path.exists(dest_sub):
                shutil.rmtree(dest_sub)
            shutil.copytree(src, dest_sub)

print(f"Copied standard_inputs to {N_MEMBERS} ensemble directories (skipped: {SKIP})")
