---
id: TP2
title: MCP server + agent loop (MCP-first)
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [TP1]
---

# Phase TP2 — MCP server + agent loop (MCP-first)

- **Goal:** Expose Touch's geometry over an **MCP server** the user's **own Claude Code** drives — validate the full agent loop on the subscription, no API tokens, before embedding (ADR-0014).
- **Min:** MCP server with the geometry tools (query/select/render-to-image/list/get/add/edit/reorder/delete layer) + the structured mutating envelope, forwarding to the live backend (F41); positional + macro context packets (F45/N15); driven from the user's existing Claude Code (F42); the agent sees renders and self-corrects.
- **Max:** downstream-delta / finder-rebind warnings; thumbnail + context tuning; multi-edit batching; usage/quota surfacing.
- **Exit criterion (agent-path benchmark):** point your own Claude Code at Touch → "build a part with an extrusion, a hole, and a chamfer" (positional + macro) → it builds via MCP, sees renders, appears live — entirely on the subscription, zero API tokens (N14).
- **Delivers:** F41, F42, F43 (agent loop), N14, N15.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
