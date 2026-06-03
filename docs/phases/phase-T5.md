---
id: T5
title: Conversational clarification + robust face resolution
status: in_progress
started: 2026-06-03
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

## Depends on

- **T4 done** (folder workspace + `.touch` persistence + chamfer round-trip).
- **ADR-0011** (tiered selection resolution) + **ADR-0008** (finders).
- **Requirements** F7, F22, F36 approved; **F20** (per-face mesh ids, shipped).
- **Architecture**: `finder` module (`resolve_face`); `02-data-model` Selection
  resolution order + `entity_id_at_capture`; planner op-or-question (F22).

## Minimum deliverable

**Robust face resolution (F36):** clicking any face — including near an edge or
corner, or a pick a hair off the surface — resolves to exactly that face when an
op applies; no "ambiguous" / "no face" on a normally-selectable click.

**Conversational clarification (F7, F22):** the planner returns an `Operation`
**or** a `ClarifyingQuestion`; a missing required param (e.g. `chamfer` with no
size) asks instead of guessing; the FE prompt panel becomes a short chat thread;
a reply resumes planning with conversation context; the finalized op records the
turns in `Operation.conversation`; a max-turns guard (config) caps the loop.

## Maximum deliverable

A "show me what you'd do" preview turn (planner describes the op before commit);
per-turn cost surfaced inline in the chat thread.

## Sprint / day breakdown

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 1 | **Protocol rename + migration.** `Selection.face_id_at_capture` → `entity_id_at_capture` (typed by `target`) in `protocol/schema.json`; `make codegen` (pydantic + TS); `TouchDocument._migrate` maps the old field on load. | schema + regenerated types + migration. | Codegen regenerates cleanly; an existing `.touch` (old field) loads + round-trips; protocol tests green. |
| 2 | **Canonical face enumeration + tiered resolver.** Extract the `TopExp_Explorer(FACE)` walk that assigns `face_id` into one shared helper used by **both** `tessellate` and `finder`; add `resolve_face(solid, selection)` — `entity_id_at_capture` first (index into the canonical walk), then the geometric finder, else `FinderError`. | `finder.resolve_face` + shared enumeration. | Unit test: tessellate's `face_id i` ≡ resolver's face `i` on a box + chamfered solid; an edge/corner point that raised `ambiguous` now resolves via id. |
| 3 | **Adapter uses the resolver.** `operation_adapter` chamfer emits `resolve_face(prev, <selection>)` (id-first) instead of `resolve_face_containing(point, tol)`; thread the captured id through the emitted code. | id-first chamfer emission. | Adapter snapshot test updated; a chamfer whose selection sits on an edge-adjacent face builds (no finder error). |
| 4 | **FE carries the captured id.** `web/picking`/`web/selection` populate `entity_id_at_capture` from the mesh face id under the cursor; it reaches the backend in the `plan` selection. | FE selection carries id. | A click sends a selection whose `entity_id_at_capture` is the clicked mesh face id; live chamfer near an edge works end-to-end at nexus/touch. |
| 5 | **Planner: op-or-question (F22).** `plan(...)` returns `Operation \| ClarifyingQuestion`; `ClarifyingQuestion` model + protocol `clarify` message; prompt instructs the planner to ask when a required param (per `intent_validation`) is missing rather than guess. | op-or-question planner + message. | Mocked-client tests assert both branches; `"chamfer"` with no size → a `ClarifyingQuestion`, not a guessed length. |
| 6 | **Session conversation state + resume (F7).** `Session` holds in-flight `ConversationState` (selection + turns + attempts); a reply resumes the planner with context; max-turns guard (config, default 3); finalized op records turns in `Operation.conversation`. | conversation loop (backend). | A 2-turn exchange (question → reply → op) applies, the op's `conversation` holds the turns; exceeding the turn cap returns a graceful structured error. |
| 7 | **FE chat thread (F7).** The prompt panel continues as a chat thread on a `clarify` response: render the question, accept a reply, send it with conversation context; cancel closes; single-shot op path unchanged. | chat-thread prompt panel. | An ambiguous prompt shows the question inline; replying produces the op and updates the viewport; cancelling discards. |
| 8 | **Live exit verification.** Both exit criteria live in a browser tab at nexus/touch. | verified phase. | (a) "chamfer" with no size → asks → reply → applies; (b) click any face incl. near an edge/corner → chamfer → resolves with no finder error. |

## Known risks for this phase

- **R1 — face-id ordering divergence (load-bearing).** The resolver must index
  the **same** face ordering `tessellate` used (its `TopExp_Explorer` walk), not
  build123d's `solid.faces()`. **Mitigation:** Day 2 extracts one shared
  enumeration helper; a test asserts `tessellate` face `i` ≡ resolver face `i`.
- **R2 — id stability across undo/redo within a session.** The captured id must
  still resolve after undo/redo. Append-only history + deterministic emit →
  identical solid → identical enumeration. **Mitigation:** test resolve after an
  undo/redo cycle; the finder fallback covers any miss.
- **R3 — clarify branch regresses the green op-only path** (T3/T4 planner +
  contract tests). **Mitigation:** op-only stays the default branch; both-branch
  mocked tests; keep existing tests green.
- **R4 — LLM over-/under-asks.** **Mitigation:** drive "ask" off the
  `intent_validation` required-params contract, not LLM whim; cap turns.
- **R5 — `.touch` migration.** Existing parts carry the old `face_id_at_capture`.
  **Mitigation:** `_migrate` maps it; Day 1 test loads an old part.
- **R6 — prompt-panel refactor** (single-shot → chat thread) risks the working
  one-shot UX. **Mitigation:** keep the one-shot path when no clarify; layer the
  thread on top incrementally.
