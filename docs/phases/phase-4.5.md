---
id: phase-4.5
title: Schema v2a — edge selection + hole positioning
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [phase-4]
---

# Phase 4.5 — Schema v2a: edge selection + hole positioning

- **Goal:** Make the highest-value `extras` use-cases the phase-3.5
  blocker exposed (chamfer/fillet a named edge; a hole on a chosen
  face/axis) into first-class `Intent` schema, so they no longer depend
  on fragile un-guarded LLM-written `extras`. Pulled forward from
  phase-10 per the 2026-05-28 blocker re-design.
- **Min:** schema additions (edge-selection qualifier on `fillet`/
  `chamfer`; hole positioning + axis on `hole`); adapter support; per-kind
  fixtures; planner prompt updated to prefer schema over `extras`;
  migration for old payloads.
- **Max:** cylinder + L-bracket references expressible without `extras`;
  the L-bracket showcase re-runs schema-native and passes the phase-4
  evaluator.
- **Exit criterion:** "cylinder with a 2 mm chamfer on the top edge" and
  "L-bracket with a hole in each flange" produce correct geometry via the
  schema (no `extras`), verified by the phase-4 evaluator + snapshots.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
