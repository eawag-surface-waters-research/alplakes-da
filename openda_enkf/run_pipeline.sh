#!/bin/bash
# Run the full OpenDA EnKF pipeline.
# Usage (from project root):
#   bash openda_enkf/run_pipeline.sh [lake] [n_members] [start] [end]
# Defaults: upperlugano  20  2025-01-01  2025-12-31

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LAKE="${1:-upperlugano}"
N_MEMBERS="${2:-20}"
START="${3:-2025-01-01}"
END="${4:-2025-12-31}"
MODEL_END=$(python3 -c "
from datetime import date, timedelta
d = date.fromisoformat('$END') + timedelta(days=1)
print(d.isoformat())
")

echo "================================================================"
echo " Lake: $LAKE  |  Members: $N_MEMBERS  |  $START → $END"
echo "================================================================"

echo ""
echo "--- Step 1: Init instances ---"
python3 openda_enkf/scripts/init_instances.py \
    --lake "$LAKE" --n-members "$N_MEMBERS" \
    --start "$START" --end "$MODEL_END"

echo ""
echo "--- Step 2: Prepare observations ---"
python3 openda_enkf/scripts/prep_obs.py \
    --lake "$LAKE" --start "$START" --end "$END"

echo ""
echo "--- Step 3: Start Docker containers ---"
python3 openda_enkf/scripts/start_containers.py \
    --lake "$LAKE" --n-members "$N_MEMBERS"

echo ""
echo "--- Step 4: Run OpenDA EnKF ---"
export OPENDADIR="$ROOT/openda_3.4.0/bin"
export PATH="$ROOT/openda_3.4.0/jre/bin:$OPENDADIR:$PATH"
export OPENDA_NATIVE=linux64_gnu
export OPENDALIB="$OPENDADIR/$OPENDA_NATIVE"
export LD_LIBRARY_PATH="$OPENDALIB/lib:$LD_LIBRARY_PATH"

cd "$ROOT/openda_enkf"
oda_run.sh enkf.oda

echo ""
echo "=== Pipeline complete ==="
