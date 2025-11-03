#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

source tools/ust_curve/venv/bin/activate
export PYTHONPATH="$ROOT/tools/ust_curve:$ROOT:$PYTHONPATH"

DATE="${1:-$(date +%F)}"

python tools/ust_curve/llm/build_snapshots.py --core-module tools.ust_curve.curves "$DATE"
python tools/ust_curve/llm/make_summary.py --date "$DATE"

# Normalize any stray outputs written under tools/tools → move into tools/ust_curve
if [ -d tools/tools/ust_curve/llm/snapshots ]; then
  mkdir -p tools/ust_curve/llm/snapshots
  mv -f tools/tools/ust_curve/llm/snapshots/* tools/ust_curve/llm/snapshots/ 2>/dev/null || true
fi
if [ -d tools/tools/ust_curve/llm/summaries ]; then
  mkdir -p tools/ust_curve/llm/summaries
  mv -f tools/tools/ust_curve/llm/summaries/* tools/ust_curve/llm/summaries/ 2>/dev/null || true
fi
# optional clean-up
[ -d tools/tools ] && rm -rf tools/tools

SNAP="tools/ust_curve/llm/snapshots/curve_snapshot_${DATE}.json"
LOG="tools/ust_curve/llm/curve_daily_log.md"

if [ -f "$SNAP" ]; then
  # NEW: make plots
  python tools/ust_curve/llm/plot_snapshot.py "$DATE"

  # Append short analysis to rolling log
  python tools/ust_curve/llm/analyze_snapshot.py "$SNAP" >> "$LOG"
  echo -e "\n---\n" >> "$LOG"
  echo "Done for $DATE"
else
  echo "ERROR: Snapshot not found at $SNAP"
  exit 1
fi
