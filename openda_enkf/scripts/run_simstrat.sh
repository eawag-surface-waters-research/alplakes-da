#!/bin/bash
# Shell wrapper invoked by OpenDA for each ensemble member.
# Working directory when called: openda_enkf/scripts/  (workingDirectory="%scriptsDir%" = "../scripts" in wrapper XML)
set -e

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
LOG="$SCRIPT_DIR/../run_simstrat_debug.log"

echo "[$(date)] run_simstrat.sh called with args: $*" >> "$LOG"
echo "  PWD=$(pwd)" >> "$LOG"
echo "  python3=$(which python3 2>/dev/null || echo NOT_FOUND)" >> "$LOG"

python3 "$SCRIPT_DIR/run_simstrat.py" "$@" >> "$LOG" 2>&1
STATUS=$?
echo "  exit status: $STATUS" >> "$LOG"
exit $STATUS
