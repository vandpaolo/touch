#!/usr/bin/env bash
# Day-1 end-to-end check: build venv, start sidecar, run check_client, tear down.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3.12}"
command -v "$PY" >/dev/null || PY=python3

rm -rf .venv
"$PY" -m venv .venv
. .venv/bin/activate
pip install -q -e .

# Start sidecar, capture the TOUCH_READY line.
LOG="$(mktemp)"
python -m touch_sidecar >"$LOG" 2>&1 &
SIDECAR=$!
trap 'kill "$SIDECAR" 2>/dev/null || true' EXIT

# Wait up to 10s for the ready sentinel.
PORT=""
for _ in $(seq 1 50); do
  if grep -q '^TOUCH_READY ' "$LOG"; then
    PORT="$(awk '/^TOUCH_READY /{print $2; exit}' "$LOG")"
    break
  fi
  sleep 0.2
done

echo "--- sidecar stdout ---"
cat "$LOG"
echo "----------------------"

if [ -z "$PORT" ]; then
  echo "FAIL: no TOUCH_READY line within 10s"
  exit 1
fi
echo "parsed port: $PORT"

python check_client.py "$PORT"
RC=$?
exit $RC
