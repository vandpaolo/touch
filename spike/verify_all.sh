#!/usr/bin/env bash
# Master T0 spike verification (Days 1-3, headless-testable parts). Writes a
# verdict to spike/VERIFY_RESULT.txt so the result survives a scrambled stdout.
# Does NOT use `set -e` — every step runs and reports its own rc.
#
# NOT covered here (manual, need a display/GPU):
#   - Day 2 visual: three.js render + per-face hover highlight in a browser.
#   - Day 3 windowed: Electron window opens + window<->sidecar supervision.
cd "$(dirname "$0")"
OUT="VERIFY_RESULT.txt"
: > "$OUT"

PY="${PYTHON:-python3.12}"
command -v "$PY" >/dev/null || PY=python3

log() { echo "$@" | tee -a "$OUT"; }

log "=== T0 spike verify @ $(date -u +%FT%TZ) ==="
log "node: $(node --version 2>&1)  python: $($PY --version 2>&1)"

# --- setup -----------------------------------------------------------------
if [ ! -d sidecar/.venv ]; then
  log "[setup] creating sidecar venv"
  ( cd sidecar && "$PY" -m venv .venv && . .venv/bin/activate && pip install -q -e . ) >>"$OUT" 2>&1
fi
if [ ! -d web/node_modules ]; then
  log "[setup] npm install (web)"
  ( cd web && npm install ) >>"$OUT" 2>&1
fi
if [ ! -d shell/node_modules ]; then
  log "[setup] npm install (shell)"
  ( cd shell && npm install ) >>"$OUT" 2>&1
fi

# --- Day 1: sidecar emits a parseable 6-face cube --------------------------
log ""
log "--- DAY 1: sidecar cube frame ---"
D1="$(bash sidecar/verify_day1.sh 2>&1)"; D1_RC=$?
echo "$D1" >> "$OUT"
echo "$D1" | grep -E '^(vertices|triangles|distinct|PASS|FAIL)' | sed 's/^/  /'
log "[day1] rc=$D1_RC"

# --- Day 2a: web build (type-check + bundle) -------------------------------
log ""
log "--- DAY 2a: web build (tsc + vite) ---"
B="$(cd web && npm run build 2>&1)"; B_RC=$?
echo "$B" >> "$OUT"
echo "$B" | grep -iE 'error|built in' | sed 's/^/  /'
log "[build] rc=$B_RC"

# --- Day 2b: FE<->BE wire parity -------------------------------------------
log ""
log "--- DAY 2b: FE<->BE wire parity ---"
D2="$(bash web/verify_day2.sh 2>&1)"; D2_RC=$?
echo "$D2" >> "$OUT"
echo "$D2" | grep -E '^(version|vertices|triangles|distinct|PASS|FAIL|sidecar)' | sed 's/^/  /'
log "[day2] rc=$D2_RC"

# --- Day 3: shell sidecar coupling (spawn + ready + WS) --------------------
log ""
log "--- DAY 3: shell sidecar smoke ---"
D3="$(cd shell && npm run smoke 2>&1)"; D3_RC=$?
echo "$D3" >> "$OUT"
echo "$D3" | grep -E '^(sidecar port|SMOKE_OK|SMOKE_FAIL)' | sed 's/^/  /'
log "[day3] rc=$D3_RC"

# --- verdict ---------------------------------------------------------------
log ""
if [ "$D1_RC" -eq 0 ] && [ "$B_RC" -eq 0 ] && [ "$D2_RC" -eq 0 ] && [ "$D3_RC" -eq 0 ]; then
  log "VERDICT: ALL-PASS (headless parts)"
else
  log "VERDICT: FAIL (day1=$D1_RC build=$B_RC day2=$D2_RC day3=$D3_RC)"
fi
