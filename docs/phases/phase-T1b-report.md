---
phase: T1b
title: Server + protocol skeleton + new modules
status: done
min_met: true
max_met: false
duration_planned_days: 7
duration_actual_days: 1
started: 2026-05-31
finished: 2026-05-31
---

# Phase T1b report — Server + protocol skeleton + new modules

Closed 2026-05-31, single session. The Touch backend skeleton stands up on the
salvaged engine: a localhost WS server speaks a generated protocol, plans an
operation via a pluggable LLM client, builds **real geometry** from it, and
streams a face-id'd mesh. Delivers **F19, F20, F21, F22, F31**. No blockers.

## What shipped

Against the planned sprint table:

| Day | Task | State | Evidence |
|-----|------|-------|----------|
| 1 | Protocol schema + codegen | ✅ done | `a4b305b`; `protocol/schema.json` + `make codegen` (deterministic) → pydantic + TS |
| 2 | WS server + session + in-memory document | ✅ done | `6ccf0cc`; `python -m touch_backend` serves; `ready` on connect; structured errors |
| 3 | `tessellate` with per-face IDs (F20) | ✅ done | `eeea23f`; cube → 6 face ids, binary frame round-trip |
| 4 | `llm_client` Protocol + both impls + `keychain_bridge` (F31) | ✅ done | `b6963c9`; both smoke-load; keychain round-trip |
| 5 | Wire `plan` end-to-end + contract test + import contracts | ✅ done | `d628160`; Min contract test passes; 14 import contracts |
| 6 | Delete the spike | ✅ done | `43d8eb5`; `spike/` + `spike-build.yml` gone (2.2 GB), tags preserve it |
| Max | New-schema refactor + bidirectional contracts | ◑ partial | `eaae8bf`; real Operation geometry shipped; full Intent removal + bidirectional deferred (below) |

Concretely:
- **Protocol (ADR-0005):** `protocol/schema.json` is the single wire contract
  (`Operation`/`Selection`/7 `FinderPredicate` variants/control + mesh
  envelopes); `make codegen` emits pydantic (`src/touch_backend/_generated/`)
  + TS (`protocol/generated/ts/`), reproducibly.
- **Server/session/document:** `Server` (websockets/asyncio, `127.0.0.1` +
  configurable port, F19), `Session` (parse → dispatch, structured errors F21),
  in-memory `TouchDocument` (F8).
- **tessellate (F20):** OCP solid → mesh + per-triangle face-id map + binary
  frame pack/unpack + the `face_id → finder hint` envelope.
- **LLM clients (F31):** `LLMClient` Protocol + `AnthropicAPIClient` (key via
  `keychain_bridge`) + `ClaudeCodeClient` (import-guarded) + `make_client`.
- **plan, end-to-end (F22):** server → session → `planner` → `Operation` →
  `operation_adapter.emit` → subprocess `Executor` → `import_step` →
  `tessellate` → stream op + mesh. **Real geometry** (contract test: a
  30×20×10 box op yields a mesh whose bounding box is 30×20×10).
- **Quality:** 196 tests; `ruff`/`pyright` (0)/`lint-imports` (14 kept, 0
  broken, incl. 4 new layering contracts) green; resolved the carried-over
  executor TBD (subprocess model, decisions.md P3) in `02-classes.md`.

## What slipped (and why)

`max_met: false` — the Max was partially delivered. **Shipped:** the
`operation_adapter` (Operation history → deterministic build123d source for the
param-only primary kinds) and the real `adapter → executor → tessellate` path —
the substantive Max value. **Deferred (own focused effort, none blocking):**
1. Fully replacing Maquette's `Intent`/`Modifier`/`PrimaryFeature` across the
   legacy `agent/*` pipeline and its ~10 tests — a large mechanical refactor;
   the legacy pipeline stays green and off Touch's critical path.
2. Modifier geometry (hole/fillet/chamfer/shell/pattern) — needs finder-resolved
   selections (ADR-0008); `operation_adapter` refuses them for now.
3. Bidirectional FE→BE / BE→FE frame contract tests — best written once the
   frontend exists (T2).

Min was fully met, so closure is `done`.

## Surprises

- **OSMesa collection-poisoning.** Importing `build123d`/`OCP` at a test
  module's top level loads the OCP GL layer at pytest *collection*, which
  poisons VTK-OSMesa for the legacy orthographic render test (blank frame) —
  independent of execution order. Fix: import them lazily inside functions.
  Cost a real Day-3 bisect; now in auto-memory `render-backend`.
- **`pip install -e .` keeps re-pulling stock `vtk`** (pyvista dep), re-shadowing
  `vtk-osmesa` and crashing render tests — happened 3×. Direct `pip install`
  of a single dep avoids it; full reinstalls need the osmesa swap again.
- **The subprocess `Executor` is a feature, not just safety.** Running the
  emitted build123d in a subprocess isolates the heavy OCP build from the main
  process, so the Max real-geometry path doesn't poison the in-process render
  test. The P3 subprocess decision paid off twice.
- **Generated-model shape:** the `Message` union is a pydantic `RootModel`
  (`.message.root`), and per-message `type` Literals have no default (must be
  passed explicitly when constructing).

## Decisions taken mid-phase

No `/pm-blocker` filed. In-phase decisions (logged in `docs/notes/decisions.md`):
- **P1** — the wire/protocol shape is `Operation` from day 1; Min used a mocked
  op (sample box), the Max upgraded to real Operation geometry.
- **P2** — added `websockets`/`numpy`/`keyring`/`datamodel-code-generator`;
  `claude-agent-sdk` import-guarded (hard dep deferred to T6).
- **P3** — executor process model = subprocess/worker; resolved the
  `02-classes.md:331` TBD (pre-T1a audit FAIL #7).
- Generated pydantic lands in `src/touch_backend/_generated/` (importable);
  schema + TS stay under `protocol/`.
- Pre-T1b audit overridden: 2 blocking FAILs fixed before start, 3 doc-quality
  FAILs deferred.

## Recommended changes for next phase

1. **Schedule the full `Intent → Operation` engine completion** as its own
   phase/effort: retire the legacy `agent/*` Intent pipeline + tests, and add
   modifier geometry with finder resolution (ADR-0008). It's mechanical but
   large; doing it piecemeal risks half-migrated state.
2. **Run-folder + `.touch` persistence (T4):** the Max rebuild uses a tempdir
   per plan; persistent run dirs under `/srv/touch` + load/save land in T4.
3. **Before T2 (frontend):** add the `web/main` app-shell owner for F2
   (pre-T1b audit FAIL #1) via `/pm-architecture`; write the bidirectional
   frame contract tests against the real FE; the always-on Caddy-hosted
   browser-dev UI (notes/questions.md) is a T2-era ops task.
4. **CI hardening:** add a codegen-drift guard (`make codegen` + `git diff
   --exit-code`); the recurring `vtk-osmesa` swap is in `ci.yml` but bites dev
   reinstalls — consider a `make dev-install` that bundles the swap.
