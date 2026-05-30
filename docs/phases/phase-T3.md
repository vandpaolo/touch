---
id: T3
title: Picking + click-to-prompt (first end-to-end round-trip)
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T2]
---

# Phase T3 — Picking + click-to-prompt

- **Goal:** The first end-to-end click→prompt→geometry round-trip. The first time the user can actually drive Touch.
- **Min:** FE picking (raycaster + face-id lookup → instant local highlight, N1); selection store; prompt panel opens on click; submit sends `{selection, point, prompt}` to BE; planner returns an op (no clarification yet); BE executes + re-tessellates; mesh delta back; viewport updates. The op is held in memory (history persistence comes in T4).
- **Max:** Distinct hover vs click highlight styles; spatial click point displayed in the prompt panel for transparency; manually-typed prompt without a selection (BE accepts `None` selection for the initial primary feature on a base plane).
- **Exit criterion:** in a browser tab, click a face of a backend-built cube, type "add a 5 mm chamfer here", see the chamfered cube within the N2 latency budget.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
