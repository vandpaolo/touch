---
id: T5b
title: Edge identity + edge targeting
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T5]
---

# Phase T5b — Edge identity + edge targeting

- **Goal:** Select a single **edge** and chamfer/fillet exactly that edge, not the whole face's edge loop.
- **Min:** The mesh frame carries per-edge ids (`edge_tag_per_segment`, F20 end-to-end); FE edge picking (raycast a wireframe segment → edge id); an **edge resolver** in `finder` (same tiered model as faces, ADR-0011); `operation_adapter` applies edge-scoped ops to the resolved single edge.
- **Max:** Edge hover affordance/highlight parity with faces; multi-edge selection for a batched chamfer.
- **Exit criterion:** click one edge of a box → chamfer → only that edge is chamfered (not the loop); face selection still applies face-scoped ops.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
