---
id: T0
title: Packaging spike (Electron + Python sidecar + OCP → Windows .exe)
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: []
---

# Phase T0 — Packaging spike

- **Goal:** Prove Electron + a PyInstaller'd Python sidecar with OCP native libs packages into a Windows `.exe` that installs and runs on a fresh non-technical Windows VM — *before* any feature work (ADR-0009 gating risk).
- **Min:** A `Touch-spike-0.1.0.exe` installs on a clean Windows VM, launches the sidecar, the Electron renderer connects to it over WebSocket, the sidecar emits a known-good face-id'd mesh (hardcoded cube), three.js renders it, hovering a face highlights it locally. No LLM, no real planner, no `.touch` save.
- **Max:** Builds via GitHub Actions on a tag push; a smoke check launches the `.exe` headlessly and asserts the WS handshake; identical bare-frontend served as a browser tab on the dev box.
- **Exit criterion:** the Min holds, *or* the spike is filed as `/pm-blocker` and the desktop shell pivots to Tauri (ADR-0009 escape hatch).

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
