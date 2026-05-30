# touch-shell-spike (T0 spike, Day 3)

Throwaway Electron shell for the packaging spike. Spawns the Python sidecar,
waits for `TOUCH_READY <port>` on its stdout, opens a `BrowserWindow` loading
the Vite-built viewport with `?port=<port>` injected, and supervises the
lifecycle in both directions. Deleted in T1a/T1b.

See [`docs/phases/phase-T0.md`](../../docs/phases/phase-T0.md) (Day 3).

## Prerequisites

- Sidecar venv built: `cd ../sidecar && python3.12 -m venv .venv && . .venv/bin/activate && pip install -e .`
- Web built: `cd ../web && npm install && npm run build` (the shell loads
  `../web/dist/index.html`).
- `npm install` here (electron + typescript).

## Run (manual desktop check — needs a display)

```bash
npm start          # tsc + electron .
```

**Done when (visual, manual):** a window opens within ~3 s showing the cube +
hover-highlight, with the sidecar auto-spawned; quitting the window kills the
sidecar; killing the sidecar closes the window. This requires a real
display + WebGL — it cannot run on a headless box (Electron aborts with
"Missing X server or $DISPLAY").

## Headless smoke (CI-able, no display)

```bash
npm run smoke      # tsc + node dist/smoke.js
```

Exercises the load-bearing coupling the Electron main depends on — the exact
`spawnSidecar` + `TOUCH_READY` parsing (R2/R3/R4) in
[`src/sidecar.ts`](src/sidecar.ts) — then opens a WebSocket and asserts a
valid mesh frame arrives. Prints `SMOKE_OK` / exits 0 on success.

What the smoke does **not** cover (manual, needs a display): the
`BrowserWindow` open, the WebGL render, and the window↔sidecar supervision
glue in [`src/main.ts`](src/main.ts).

## Design notes

- `src/sidecar.ts` is intentionally **Electron-free** so the spawn/ready
  logic is unit-testable from plain node (the smoke) and reused unchanged by
  the Electron main.
- Dev resolves the sidecar to `../sidecar/.venv/bin/python -m touch_sidecar`.
  Packaged (Day 5) resolves it to `process.resourcesPath/sidecar/touch_sidecar`
  (the PyInstaller `--onedir` output, asarUnpack'd) — R2.
- Main waits for `TOUCH_READY` before creating the window, so the WS-connect
  race (R3) is closed at the process level, not papered over with a timeout.
