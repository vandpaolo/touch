---
id: T8
title: Cost indicator + cold-start splash + crash recovery
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T7]
---

# Phase T8 — Cost / splash / crash UX

- **Goal:** Production-grade lifecycle UX. The app handles its own boots and crashes with grace.
- **Min:** Cold-start splash until backend `ready` (F15); session cost indicator from `pricing` (F14); Electron main `shell/sidecar` spawns + supervises + restarts the Python sidecar on unexpected exit (F16); FE `transport` reconnects and issues `rebuild(history)`; toast: "engine restarted, work restored"; cancel button completes for in-flight prompts (F17 done end-to-end).
- **Max:** Per-LLM-call token breakdown view; sidecar log surface in dev only (off in prod).
- **Exit criterion:** chaos test: kill the sidecar mid-session → app recovers in < 10 s with a single toast and identical model; running cost displayed in the UI matches the sum of per-prompt costs.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
