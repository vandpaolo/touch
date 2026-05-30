# 0009 — Desktop shell: Electron + Python sidecar (with the packaging spike as gating risk)

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** vandpaolo

## Context

Touch's POC distribution target is a **Windows `.exe`** for engineer
friends (vision § Success criteria, requirement F1 / F28 / N4). The
engine is Python (build123d / OCP); the frontend is web tech
(TypeScript + three.js); the coupling is a localhost WebSocket
([ADR-0005](./0005-localhost-websocket-coupling.md)).

The choice of desktop shell decides:

- How the web frontend is hosted in prod (and how that matches
  browser-tab dev mode — N5 / N6).
- How the Python sidecar's lifecycle is managed.
- How everything bundles into a single `.exe` installer (N4).

The shipping author has prior **Electron** experience.

The 2026-05-29 deep-research pass explicitly did **not** benchmark
desktop-shell options (Electron vs Tauri vs Wails vs pywebview vs
Neutralino) — it's an open spike. But it surfaced a working reference
example for **Tauri + Python sidecar** and the broad pattern
(`child_process.spawn` of a PyInstaller'd Python binary) generalises
across shells.

## Decision

**Use Electron as the desktop shell, with the Python backend spawned and
supervised as a sidecar process by Electron main.**

- **Frontend** (three.js + React + Vite output) is loaded into the
  Electron renderer window.
- **Python sidecar** is started by `shell/sidecar` on app launch using
  `child_process.spawn`, with a freshly-allocated localhost port.
- Sidecar **readiness** is signalled by a sentinel line on stdout
  (`READY ws://127.0.0.1:<port>`); Electron main forwards the URL to the
  renderer and dismisses the splash (F15).
- **Crash recovery** (F16 / N8): Electron main listens for the sidecar's
  `exit` event; on unexpected exit, it respawns the process, the
  renderer's `transport` reconnects to the new port, the FE issues
  `rebuild(history)`, and a toast surfaces "engine restarted, work
  restored."
- **Packaging:** `electron-builder` bundles the Electron + frontend
  assets; the Python sidecar is **PyInstaller**'d (with OCP native libs
  + all Python deps) and shipped as a sidecar binary inside the
  installer. The whole thing produces one Windows `.exe` installer.
- **In dev**, Electron is **not used**: the sidecar runs standalone
  (`python -m touch_backend`), the Vite dev server serves the frontend,
  the developer opens a browser tab. Identical FE code path.

### The packaging spike is the gating risk

The single highest-risk unknown of v0 is *whether the
Electron + PyInstaller'd Python sidecar with OCP native libs actually
packages into a `.exe` that installs and runs on a fresh non-technical
Windows box*. The research could not verify this; it must be proved
**before** building features.

**Therefore: phase 0 of the v0 roadmap is an explicit packaging spike** —
trivial round-trip + picked-face + `.exe` on a clean Windows VM. If the
spike fails or proves intractable, the **fallback escape hatch** is
swapping the shell:

- **Tauri (Rust shell, smaller bundle) + same Python sidecar** — same
  architecture, lighter wrapper. Tauri-v2 has a documented sidecar
  pattern (`tauri-plugin-shell`) that mirrors the Electron approach.
- **pywebview / Wails** as further fallbacks.

Because the editor↔engine boundary is a localhost WebSocket
([ADR-0005](./0005-localhost-websocket-coupling.md)), the FE and BE
code don't care which shell wraps them — the swap is contained to
`shell/`.

## Consequences

- Familiar tech for the author (prior Electron experience) — fastest
  path to a working POC if packaging cooperates.
- One stable model across dev and prod: Electron renderer + Python
  sidecar in prod, browser tab + standalone sidecar in dev, identical FE
  code.
- **Cost:** Electron is heavy (~ 100 MB+ wrapper). Acceptable for the
  POC's distribution shape (a `.exe` installer for friends, not a fast
  mobile download), but the installer will be measured in hundreds of
  MB once Python + OCP native libs are added. Document this clearly so
  friends aren't surprised.
- **Cost:** PyInstaller + OCP native libs are non-trivial to bundle
  reliably. This is the **packaging spike** — the load-bearing risk.
- **Cost:** Electron has a real attack-surface footprint vs Tauri's
  Rust shell. For a local-only single-user app this is acceptable; if
  Touch ever exposes a remote surface, revisit.

## Alternatives considered

- **Tauri (Rust shell) + Python sidecar.** Strong alternative — smaller
  bundle, lighter runtime, working sidecar pattern. Rejected as primary
  for v0 because the author has no Rust shell experience and Electron
  is faster to a working POC. **Held in reserve as the explicit
  fallback** if the packaging spike on Electron fails.
- **Wails (Go shell) + Python sidecar.** Same reasoning as Tauri:
  viable, but new ground.
- **pywebview** (pure-Python, native webview embed). Tempting — single
  language, single packaging story — but feature-thin compared to
  Electron for VS-Code-like layouts; less battle-tested for complex
  multi-pane apps. Held as a further fallback.
- **All-Python desktop (PySide6 + pyvistaqt for the viewport, no web FE
  at all).** Rejected because the chosen FE is web tech: PySide forecloses
  the browser-tab dev mode (N6) and removes the path to a hosted-browser
  version later.
- **In-browser WASM kernel, no Python sidecar at all** (full
  opencascade.js / replicad). Rejected in ADR-0005 (forecloses
  Python-ecosystem compute future).
- **Skip the `.exe`; deliver a portable Python + Node project the
  friend runs from a shell.** Rejected: requirement F28 / N4 — friends
  are non-tech-savvy; double-click-to-run is the bar.
