---
id: T4
title: Operation history + .touch document
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T3]
---

# Phase T4 — Operation history + .touch document

- **Goal:** The document *is* the operation history. Save/load + undo/redo from the history.
- **Min:** `touch_backend.document` load/save `.touch` JSON; FE `doc-store` mirrors; undo pops + replays; redo re-applies; round-trip a `.touch` file from disk → identical model; `schema_version` field + a minimal migration helper.
- **Max:** Viewport feedback at each undo step; replay-from-history is the recovery path (foreshadowing T8 crash recovery).
- **Exit criterion:** model a cube + chamfer in dev → save → close → open → identical model. Undo back to empty → redo to full → unchanged.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
