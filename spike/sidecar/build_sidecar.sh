#!/usr/bin/env bash
# Day-4 build: PyInstaller the sidecar (--onedir) and verify the standalone
# binary runs with NO Python on PATH (the real R1 test). Writes a verdict to
# spike/sidecar/BUILD_RESULT.txt so it survives a scrambled stdout.
#
# Linux-first by design: confirm the spec collects OCP's native libs here,
# before the Windows variable lands on Day 5.
set -uo pipefail
cd "$(dirname "$0")"
OUT="BUILD_RESULT.txt"
: > "$OUT"
log() { echo "$@" | tee -a "$OUT"; }

VENV="${VENV:-.venv}"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

log "=== Day-4 PyInstaller build @ $(date -u +%FT%TZ) ==="
log "python: $($PY --version 2>&1)"

# --- ensure pyinstaller is present (build extra) ---------------------------
if ! "$PY" -c "import PyInstaller" 2>/dev/null; then
  log "[setup] installing pyinstaller"
  "$PIP" install --progress-bar off "pyinstaller>=6.0" >>"$OUT" 2>&1
fi
log "pyinstaller: $($PY -m PyInstaller --version 2>&1)"

# --- clean + build ---------------------------------------------------------
rm -rf build dist
log "[build] running PyInstaller (this collects ~400 MB of OCCT libs)…"
"$PY" -m PyInstaller build.spec --noconfirm >>"$OUT" 2>&1
BUILD_RC=$?
log "[build] rc=$BUILD_RC"
if [ "$BUILD_RC" -ne 0 ]; then
  log "VERDICT: BUILD-FAIL (see $OUT)"
  exit 1
fi

BIN="dist/touch_sidecar/touch_sidecar"
if [ ! -x "$BIN" ]; then
  log "VERDICT: BUILD-FAIL (no binary at $BIN)"
  exit 1
fi
log "[build] bundle size: $(du -sh dist/touch_sidecar 2>/dev/null | cut -f1)"
log "[build] OCP.libs in bundle: $(find dist/touch_sidecar -name 'libTK*' 2>/dev/null | wc -l) TK libs"

# --- THE R1 TEST: run the standalone binary with NO python on PATH ---------
log ""
log "--- standalone run (PATH scrubbed of python) ---"
# A minimal PATH with no python, and a clean PYTHONPATH/PYTHONHOME so the
# frozen interpreter cannot accidentally borrow the venv.
RUN_LOG="$(mktemp)"
env -i PATH=/usr/bin:/bin HOME="$HOME" "./$BIN" >"$RUN_LOG" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT

PORT=""; SELF=""
for _ in $(seq 1 60); do
  grep -q '^OCP_SELFCHECK ' "$RUN_LOG" && SELF="$(grep -m1 '^OCP_SELFCHECK ' "$RUN_LOG")"
  if grep -q '^TOUCH_READY ' "$RUN_LOG"; then
    PORT="$(awk '/^TOUCH_READY /{print $2; exit}' "$RUN_LOG")"
    break
  fi
  sleep 0.3
done

log "stdout from frozen binary:"
sed 's/^/  /' "$RUN_LOG" | tee -a "$OUT" >/dev/null
sed 's/^/  /' "$RUN_LOG"

if [ -z "$PORT" ]; then
  log "VERDICT: RUN-FAIL (no TOUCH_READY from frozen binary — likely a missing OCCT lib, R1)"
  exit 1
fi
log "[run] frozen binary ready on port $PORT"
log "[run] $SELF"

# --- parse a mesh frame from the frozen binary -----------------------------
"$PY" check_client.py "$PORT" >>"$OUT" 2>&1
CLIENT_RC=$?
log "[run] mesh-frame check rc=$CLIENT_RC"

log ""
if echo "$SELF" | grep -q "volume=1000.0" && [ "$CLIENT_RC" -eq 0 ]; then
  log "VERDICT: ALL-PASS (frozen sidecar imports OCP, computes OCCT volume=1000.0, serves cube mesh with no Python on PATH)"
else
  log "VERDICT: FAIL (selfcheck or mesh-frame check failed)"
  exit 1
fi
