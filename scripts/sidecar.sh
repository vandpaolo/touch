#!/usr/bin/env bash
# Dev-only sidecar toggle: `make up` / `make down`.
#
# Brings the Touch WS sidecar up DETACHED (setsid → survives the launching
# shell), bound on 0.0.0.0 with the demo mesh + the .env Anthropic key, so the
# browser-dev UI at https://nexus/touch goes live. Tracked by a PID file (no
# pkill). This is a dev convenience ONLY — the shipped app uses Electron's
# supervised, localhost-only sidecar (ADR-0005/0009).
set -euo pipefail
cd "$(dirname "$0")/.."

RUN_DIR=.run
PID="$RUN_DIR/sidecar.pid"
LOG="$RUN_DIR/sidecar.log"

is_up() { [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; }

case "${1:-}" in
  up)
    if is_up; then echo "sidecar already up (pid $(cat "$PID"))"; exit 0; fi
    mkdir -p "$RUN_DIR"
    set -a; [ -f .env ] && . ./.env; set +a
    export TOUCH_BACKEND_WS_HOST=0.0.0.0 TOUCH_BACKEND_DEMO_MESH=1
    setsid bash -c "echo \$\$ > $PID; exec .venv/bin/python -m touch_backend" \
      >"$LOG" 2>&1 </dev/null &
    sleep 1
    if is_up; then
      echo "sidecar UP (pid $(cat "$PID")) -> https://nexus/touch  [logs: $LOG]"
    else
      echo "sidecar failed to start; last log lines:"; tail -n 5 "$LOG" 2>/dev/null || true
      exit 1
    fi
    ;;
  down)
    if is_up; then kill "$(cat "$PID")" && echo "sidecar DOWN (pid $(cat "$PID"))"
    else echo "sidecar not running"; fi
    rm -f "$PID"
    ;;
  status)
    if is_up; then echo "UP (pid $(cat "$PID"))"; else echo "DOWN"; fi
    ;;
  *) echo "usage: $0 {up|down|status}"; exit 2 ;;
esac
