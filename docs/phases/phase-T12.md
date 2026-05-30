---
id: T12
title: Schema-v2a — edge selection + oriented hole placement
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T11]
---

# Phase T12 — Schema-v2a

- **Goal:** First-class edge selection (chamfer/fillet a *named* edge) and oriented hole placement (face + axis). Reduces reliance on finders for the harder cases (Maquette's planned phase-4.5, rebuilt for Touch's interactive model).
- **Min:** `Operation` schema gains edge-selection + face+axis hole params; adapter compiles them; finders still cover the fallback.
- **Max:** UI affordances for picking an edge in three.js (currently a facet-pick proxy); per-pick gizmo previews.
- **Exit criterion:** "chamfer the top edge of the cylinder", "a hole through this side of the box" produce correct geometry first try, without ambiguity-triggered clarification.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
