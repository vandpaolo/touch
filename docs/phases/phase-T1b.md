---
id: T1b
title: Server + protocol skeleton + new modules
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T1a]
---

# Phase T1b — Server + protocol skeleton + new modules

- **Goal:** Stand up the new Touch backend skeleton on top of the salvaged engine: WebSocket `server`, `session`, `document` (in-memory shape — load/save lands in T4), `llm_client` Protocol + both impls stubbed, `tessellate` with per-face IDs, `keychain_bridge`. Define `protocol/schema.json` + codegen for TS + pydantic.
- **Min:** `python -m touch_backend` starts the WS server; a fake-client integration test sends a `plan` message (mocked LLM) and receives a structured op + a tessellated mesh carrying per-face IDs; `protocol/schema.json` exists with TS + pydantic codegen working; `AnthropicAPIClient` + `ClaudeCodeClient` both load behind the `LLMClient` Protocol (smoke test only — real-call exercise lands in T6).
- **Max:** The adapter refactored for the new `Operation` / `Selection` / `FinderPredicate` schema (extending Maquette's `Intent`); contract tests exercise both protocol directions (FE→BE and BE→FE frames) against the generated types.
- **Exit criterion:** a contract test sends `plan` with a mocked LLM and receives a structured op + a tessellated face-id'd mesh; `lint-imports` + `pyright` green; both LLM client impls smoke-load.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
