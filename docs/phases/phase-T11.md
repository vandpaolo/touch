---
id: T11
title: Evaluator (vision-LLM critique of live geometry)
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T10]
---

# Phase T11 — Evaluator

- **Goal:** A vision-LLM critique of the live geometry vs the prompt + selection catches silent semantic failure interactively (Maquette's planned phase-4 idea, rebuilt for the live editor).
- **Min:** `agent/evaluator.py` calling a vision LLM with the streamed renders + the prompt; surfaces a "this might not match" warning in the prompt panel with a one-click rerun.
- **Max:** Optional auto-refine that proposes a corrective op.
- **Exit criterion:** on a representative corpus, the evaluator catches ≥ 70 % of injected silent-semantic mismatches; precision ≥ 80 %.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
