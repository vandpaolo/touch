---
id: T5
title: Conversational clarification
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T4]
---

# Phase T5 — Conversational clarification

- **Goal:** When the planner can't answer cleanly, it asks. The prompt panel becomes a chat thread; the conversation resumes the planner until it produces an op (or the user cancels).
- **Min:** Planner returns either an `Operation` or a `ClarifyingQuestion`; FE renders the question; user reply resumes planning with extended conversation context; max-N-turns guard (config); resulting op records the conversation in `Operation.conversation`.
- **Max:** A "show me what you'd do" preview turn (planner describes the proposed op in words before commit); per-turn cost surfaced inline.
- **Exit criterion:** an ambiguous prompt ("hole here") triggers the planner to ask ("what diameter?") → user replies → op applies and the conversation is recorded with the op.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
