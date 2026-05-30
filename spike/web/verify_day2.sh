#!/usr/bin/env bash
# Day-2 headless parity check: start the sidecar, decode its frame with the
# frontend's TS decoder, assert the cube shape. (Visual render/hover is a
# separate manual browser check — see README.)
set -euo pipefail
cd "$(dirname "$0")"
SIDECAR=../sidecar

PY="${PYTHON:-python3.12}"
command -v "$PY" >/dev/null || PY=python3

if [ ! -d "$SIDECAR/.venv" ]; then
  ( cd "$SIDECAR" && "$PY" -m venv .venv && . .venv/bin/activate && pip install -q -e . )
fi

LOG="$(mktemp)"
( cd "$SIDECAR" && . .venv/bin/activate && exec python -m touch_sidecar ) >"$LOG" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT

PORT=""
for _ in $(seq 1 50); do
  if grep -q '^TOUCH_READY ' "$LOG"; then
    PORT="$(awk '/^TOUCH_READY /{print $2; exit}' "$LOG")"
    break
  fi
  sleep 0.2
done
[ -n "$PORT" ] || { echo "FAIL: no TOUCH_READY line"; cat "$LOG"; exit 1; }
echo "sidecar port: $PORT"

node --experimental-strip-types verify_day2.ts "$PORT"
