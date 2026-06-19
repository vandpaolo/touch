---
id: TP1
title: Layer Stack backend
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T5]
---

# Phase TP1 — Layer Stack backend

- **Goal:** Refactor authoring to the **Layer Stack** (ADR-0012/0013) — a part is an ordered list of build123d layers, clickable via computed provenance, held as one shared versioned live document.
- **Min:** layers + deterministic fold + per-layer content cache; provenance → clickable layers (F39); recognized templates vs code cards (F40); one shared live document + versioned stack + compare-and-swap (F44/N16); workspace-confined executor (F46); selection as finder references (F45); append-only.
- **Max:** robust provenance through booleans/fillets; richer recognized-template set; FE Layer Stack panel polish.
- **Exit criterion:** build a part as a stack including a freeform code layer; click a face → its owning layer highlights (and vice-versa); undo/redo per layer; reopen → identical; a stale-revision mutation is rejected.
- **Delivers:** F38, F39, F40, F44, F45, F46, N16.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
