---
id: T5
title: Conversational clarification + robust face resolution
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T4]
---

# Phase T5 — Conversational clarification + robust face resolution

> *Re-scoped 2026-06-02 (ADR-0011): widened from clarification-only to also fix
> the face-selection brittleness surfaced live in T4. Edge targeting is T5b.*

- **Goal:** When the planner can't answer cleanly, it asks; and a clicked face resolves to **exactly** the face the user clicked, deterministically.
- **Min:** (clarify) Planner returns either an `Operation` or a `ClarifyingQuestion`; FE renders the question; user reply resumes planning with extended conversation context; max-N-turns guard (config); resulting op records the conversation in `Operation.conversation`. (resolution, ADR-0011/F36) tiered face resolution — `entity_id_at_capture` first, geometric finder fallback, clarify only on genuine ambiguity; `entity_id_at_capture` rename + `.touch` migration; edge/corner-adjacent and off-surface clicks no longer fail with "ambiguous"/"no face".
- **Max:** A "show me what you'd do" preview turn (planner describes the proposed op in words before commit); per-turn cost surfaced inline.
- **Exit criterion:** an ambiguous prompt ("hole here") triggers the planner to ask ("what diameter?") → user replies → op applies and the conversation is recorded; AND clicking any face (incl. near an edge/corner) then chamfering resolves to that face with no finder error.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
