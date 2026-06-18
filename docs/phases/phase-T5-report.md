---
phase: T5
status: done
min_met: true
max_met: false
duration_planned_days: 8
duration_actual_days: 2
---

# Phase T5 report — Conversational clarification + robust face resolution

> Delivered both halves: the F7/F22 clarify loop and the F36 deterministic
> face resolution (ADR-0011). Edge targeting (F37) stays in T5b. Full CI green
> (253 backend + 15 web); both exit criteria verified live on the sidecar.

## What shipped

| Day | Task | Status | Artefact |
|-----|------|--------|----------|
| D1 | `face_id_at_capture` → `entity_id_at_capture` rename + codegen + `.touch` v1→v2 migration | done | `8da8579`; protocol/schema.json, document.py |
| D2 | Canonical face enumeration (`finder.iter_faces`) shared by tessellate + finder; tiered `resolve_face` (id → finder → error) | done | `c8a3502`; finder.py, tessellate.py |
| D3 | Chamfer adapter emits the tiered resolver (id-first, contextful face) | done | `fd4ebce`; operation_adapter.py |
| — | Deflake the OSMesa render test (subprocess isolation) | done | `09fa2f3`; test_render.py |
| D4 | FE carries the captured face id through the selection | done (verified) | wired by D1's rename; selection/index.ts |
| D5 | Planner returns `Operation | ClarifyingQuestion` (contract-driven ask) | done | `948d1a7`; planner.py, session.py |
| D6 | Session conversation state + resume + max-turns; records the thread on the op | done | `4cfb16c`; session.py |
| D7 | Prompt panel becomes a chat thread for clarifications | done | `55b0b41`; App.tsx, PromptPanel.tsx |
| D8 | Live exit verification (both criteria) | done | protocol-verified on the live sidecar |

## What slipped (and why)

- **Max not met.** The stretch items — a "show me what you'd do" preview turn and
  inline per-turn cost — were not built. The min (clarify loop + robust face
  resolution) is fully delivered, so closure is `done` with `max_met: false`.
- **F37 (edge targeting)** was never in T5 — it's T5b by the roadmap split. Not a
  slip.

## Surprises

- **The OSMesa render test was a pre-existing nondeterministic flake**, not a T5
  regression: the same code passed at one run and blanked at another, because
  in-process OCP loaded earlier in the suite poisons the vtk-osmesa GL context
  (auto-memory `render-backend`). Fixed properly by running the render in a fresh
  subprocess and asserting on the written PNGs (`09fa2f3`) — order-independent now.
- **Wire-format alias bug surfaced by D6:** `ConversationTurn.from_` only
  serialises as `from` with `by_alias=True`; the op message, document snapshot,
  and `.touch` file all had to opt in so conversation turns round-trip.
- **`Face(topods_face)` makes a detached face** — build123d then treats chamfer as
  a 2D op ("takes only Vertices"). The resolver must return the *contextful* face
  from `solid.faces()` (matched by `IsSame`).
- **Major post-phase pivot (captured, not acted on):** a direction-setting
  brainstorm landed a pivot toward a Claude-Code/MCP-driven CAD IDE with a
  build123d **Layer Stack** authoring model. Locked decisions are in
  `notes/decisions.md` (2026-06-04); they feed the next vision/architecture pass.

## Decisions taken mid-phase

- No blockers were filed. A glossary FAIL in the pre-T5 audit
  (`docs/audits/2026-06-03-pre-T5.md`) was fixed before greenlight (six domain
  terms added to the 02-classes glossary), recorded in the audit's Resolution.

## Recommended changes for next phase

- **The roadmap is about to be re-scoped** by the pivot (Layer Stack + MCP + agent
  panel). Run `/pm-vision` → `/pm-requirements` → `/pm-architecture` (new ADRs:
  Layer Stack authoring; session coordination; MCP boundary; two-brain; sandboxing)
  → `/pm-roadmap` before planning the next build phase. T5b (edge targeting) may be
  resequenced or folded into the Layer Stack work.
- **Correction to fold in:** F31/ADR-0007 assumed Claude Code via `claude-agent-sdk`
  under the subscription; research shows the Agent SDK now requires a paid API key
  (OAuth restricted to Claude Code + claude.ai). The token-free path is MCP.
- **Carry-forward:** keep the subprocess-isolation pattern for any new in-process
  OCP/GL tests; keep `by_alias=True` on any new aliased protocol fields.
