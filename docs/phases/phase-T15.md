---
id: T15
title: Parametric history editing
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T14]
---

# Phase T15 — Parametric history editing

- **Goal:** Re-open op N, change its parameters, replay forward. Reopens the topological-naming problem in full force; depends on the Evaluator (T11) catching post-replay mismatches and on Schema-v2a (T12) reducing finder fragility.
- **Min:** UI for picking an op in the history → editing its params → replaying; an "op N no longer resolves" failure mode that prompts the user (not silently re-anchored).
- **Max:** Parameter resliders (the Maquette phase-9 idea: tweak a number, see the model rebuild instantly, zero LLM calls).
- **Exit criterion:** for a representative subset of v0 ops, parametric editing works without selection breakage; a stress-test mismatched-finder case is handled with a clear user-driven re-pick UX.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
