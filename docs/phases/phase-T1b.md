---
id: T1b
title: Server + protocol skeleton + new modules
status: in_progress
started: 2026-05-31
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T1a]
---

# Phase T1b — Server + protocol skeleton + new modules

- **Goal:** Stand up the new Touch backend skeleton on top of the salvaged engine: WebSocket `server`, `session`, in-memory `document`, `llm_client` Protocol + both impls stubbed, `tessellate` with per-face IDs, `keychain_bridge`. Define `protocol/schema.json` as the single wire contract + codegen for TS + pydantic. Delete the throwaway `spike/` tree.

- **Depends on:** T1a done ([phase-T1a-report.md](phase-T1a-report.md)); requirements F19/F20/F21/F22/F31 approved; architecture Coupling-Protocol context + [ADR-0005](../adr/0005-localhost-websocket-coupling.md) (WS), [ADR-0007](../adr/0007-pluggable-llm-client.md) (LLMClient), [ADR-0008](../adr/0008-picking-and-face-identity.md) (face IDs); data-model `Operation`/`Selection`/`FinderPredicate`.

- **Min:** `python -m touch_backend` starts the WS server (127.0.0.1, configurable port); a fake-client integration test sends a `plan` message (mocked LLM) and receives a structured op + a tessellated mesh carrying per-face IDs; `protocol/schema.json` exists with TS + pydantic codegen working; `AnthropicAPIClient` + `ClaudeCodeClient` both load behind the `LLMClient` Protocol (smoke-load only — real-call exercise lands in T6); `lint-imports` + `pyright` green; `spike/` removed.

- **Max:** The engine refactored to the new `Operation` / `Selection` / `FinderPredicate` schema (replacing Maquette's `Intent`/`Modifier`/`PrimaryFeature`), with `adapter` emitting build123d from an `Operation` history and the contract test driving a *real* mesh through `adapter → executor → tessellate`; bidirectional contract tests (FE→BE and BE→FE frames) against the generated types.

- **Exit criterion:** a contract test sends `plan` with a mocked LLM and receives a structured op + a tessellated face-id'd mesh; `lint-imports` + `pyright` green; both LLM client impls smoke-load; the protocol codegen is reproducible (`make codegen` is a no-op on a clean tree).

## Sprint / day breakdown

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 1 | **Protocol schema + codegen.** Author `protocol/schema.json` — control envelopes (`plan`, `applyOp`, `cancel`, `rebuild`, `exportStep`, `progress`, `conversationTurn`, `error`, `ready`) + the binary-frame JSON envelope + the `Operation`/`Selection` payload shape (per data-model). Wire pydantic codegen (`datamodel-code-generator` → `protocol/generated/py/`) + TS codegen (`json-schema-to-typescript` via `npx` → `protocol/generated/ts/`); add a `make codegen` target. | `protocol/schema.json`, generated py + ts, `make codegen`. | `make codegen` regenerates both and is a clean-tree no-op; generated pydantic models import; the TS file emits. |
| 2 | **WS server + session + in-memory document.** `server.Server.run()` (websockets/asyncio) binding `127.0.0.1` on a config-driven port; JSON-envelope dispatch → `session.Session`; binary-frame helper; in-memory `document.TouchDocument` (ordered history, no load/save). Emit `ready` on connect; unknown/malformed message → structured `error` (F21, never a traceback). | `server`, `session`, `document` modules. | `python -m touch_backend` starts; a test client connects → gets `ready`; a bad message → typed `error` event, no traceback string. |
| 3 | **`tessellate` with per-face IDs (F20).** New `tessellate(solid) -> Mesh`: OCP tessellation → vertex/normal/index buffers + a per-triangle→face-id map + the `face_id → finder hint` JSON envelope (rebuild fresh from the proven spike pattern, not salvaged). | `tessellate` module + Mesh type. | Tessellating a unit cube yields 6 distinct face ids over the triangle map; the mesh round-trips through the binary frame helper. |
| 4 | **`llm_client` Protocol + both impls + `keychain_bridge`.** `LLMClient` Protocol; `AnthropicAPIClient` (key via `keychain_bridge`/`keyring`); `ClaudeCodeClient` (`claude-agent-sdk`, import-guarded so absence ≠ import error); `make_client(mode)`. | `llm_client` package, `keychain_bridge`. | Both impls satisfy the Protocol (pyright); `make_client` returns each; `keychain_bridge` get/set/clear unit-tested against a fake keyring backend; both smoke-load with no network. |
| 5 | **Wire `plan` end-to-end + contract test (Min exit).** server → session → `planner` (mocked client) → structured op → `tessellate` → stream op + mesh frames. Author the `lint-imports` contracts for the new modules; green the gate. | Wired plan path, contract test, import contracts. | Contract test: `plan` (mocked) → structured op + face-id'd mesh; `lint-imports` + `pyright` green; both clients smoke-load. |
| 6 | **Remove the spike.** Delete `spike/` + `.github/workflows/spike-build.yml`. | Spike gone. | `spike/` absent; CI green; releases/tags still preserve the spike artifacts. |
| Max | **New-schema refactor + bidirectional contracts.** Replace `Intent`/`Modifier`/`PrimaryFeature` with `Operation`/`Selection`/`FinderPredicate`; `adapter` emits build123d from an `Operation` history; contract test drives a *real* mesh through `adapter → executor → tessellate`; FE→BE + BE→FE frame contract tests. | Refactored `intent`/`adapter`; richer contracts. | Real-geometry contract test passes; both frame directions validated against generated types. |

## Known risks for this phase

- **R-T1b-1 — `Operation` vs Maquette `Intent` boundary (the crux; see Probe P1).** The wire contract (`protocol/schema.json`) is `Operation`-based per the data-model, but the engine's `intent.py` is still Maquette's `Intent{features, modifiers}`. Min proves the protocol + plan + mesh round-trip with a *mocked* op and a sample-solid mesh; the real `Operation`→adapter→geometry refactor is Max. Risk: the mocked-op shortcut hides an impedance mismatch the Max refactor then surfaces. Mitigation: make `protocol/schema.json`'s `Operation` the authority on Day 1 so the mock already speaks the target shape.
- **R-T1b-2 — face-id stability in `tessellate` (F20, ADR-0008).** Append-only v0 + kernel face IDs sidestep full topological naming, but OCP tessellation must emit a *stable, complete* triangle→face-id map. Mitigation: assert the expected distinct-face count on a known solid; reuse the spike's proven `face_tag_per_triangle` design (rebuilt, not copied).
- **R-T1b-3 — `claude-agent-sdk` availability.** It may be absent/unauthed on nexus and in headless CI. Mitigation: import-guard `ClaudeCodeClient` so smoke-load never requires the SDK or a live Claude Code; gate any real exercise to T6.
- **R-T1b-4 — TS codegen before `web/` exists (T2).** Generating `protocol/generated/ts/` needs a node tool now. Mitigation: a standalone `npx json-schema-to-typescript` step in `make codegen` — no full `web/` toolchain yet.
- **R-T1b-5 — executor process-model TBD (pre-T1a audit FAIL #7).** `02-classes.md:331` leaves subprocess-vs-in-process open; `session` wires `executor`. Decide and record in `decisions.md` when the adapter→executor path is wired (Max). Running user build123d in-process risks crashing the server → subprocess/worker is the likely call.
- **R-T1b-6 — keep the WS reverse-proxy-ready ([questions.md](../notes/questions.md), 2026-05-31).** For the future always-on Caddy-hosted browser-dev UI: bind `127.0.0.1` only (no app auth in v0), keep host/port config-driven, and have the FE connect via a *relative* ws path so a reverse proxy is trivial in T2. No remote exposure in T1b.
- **R-T1b-7 — new import-linter contracts.** Many new modules + a new layering (`server → session → planner/executor/tessellate`; `llm_client → keychain_bridge`; generated protocol isolated). Author the contracts deliberately and verify they still bite (a deliberate bad import fails).
