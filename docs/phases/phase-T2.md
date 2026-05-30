---
id: T2
title: Frontend skeleton (Vite + React + TS + three.js)
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T1b]
---

# Phase T2 — Frontend skeleton

- **Goal:** Stand up the Vite + React + TypeScript frontend with the three.js viewport, NX camera, transport layer, and the layout shell. Not yet interactive beyond camera control.
- **Min:** `web/` builds via Vite; opening it in a browser tab shows three panels (file-tree placeholder left, viewport centre, settings menu); the viewport renders a static mesh sent by the backend; NX-style camera controls work; `web/transport` connects to `ws://localhost:<port>`; `web/protocol-types` is generated from `protocol/schema.json`.
- **Max:** Hot-reload polished; basic styling matches a VS-Code-lite look (dark theme, the three-panel layout).
- **Exit criterion:** in a browser tab in dev → connect to BE → camera orbits a backend-served mesh.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
