---
id: TP1
title: Layer Stack backend
status: done
started: 2026-06-19
finished: 2026-06-22
min_goal_met: true
max_goal_met: false
blocker: null
depends_on: [T5]
---

# Phase TP1 — Layer Stack backend

- **Goal:** Refactor authoring to the **Layer Stack** (ADR-0012/0013) — a part is an ordered list of build123d layers, clickable via computed provenance, held as one shared versioned live document.
- **Min:** layers + deterministic fold + per-layer content cache; provenance → clickable layers (F39); recognized templates vs code cards (F40); one shared live document + versioned stack + compare-and-swap (F44/N16); workspace-confined executor (F46); selection as finder references (F45); append-only.
- **Max:** robust provenance through booleans/fillets; richer recognized-template set; FE Layer Stack panel polish.
- **Exit criterion:** build a part as a stack including a freeform code layer; click a face → its owning layer highlights (and vice-versa); undo/redo per layer; reopen → identical; a stale-revision mutation is rejected.
- **Delivers:** F38, F39, F40, F44, F45, F46, N16.

## Depends on

- **T5 done** (finder, `resolve_face`, `iter_faces`, tessellate face/edge ids,
  mesh_cache, executor, planner/adapter — all reused).
- **ADR-0012** (Layer Stack), **ADR-0013** (shared doc + CAS), **ADR-0016**
  (executor sandbox); requirements **F38, F39, F40, F44, F45, F46, N16**;
  architecture pivot-components (`layer_stack`, `provenance`, `templates`,
  `executor`, `context_packets`).

## Minimum deliverable

The backend Layer Stack end-to-end: a part is an ordered list of build123d
layers; deterministic fold + per-layer cache; provenance makes layers clickable;
recognized templates vs code layers; one shared versioned live document with
compare-and-swap; `.touch` persists the stack; the executor is
workspace-confined; the existing click-to-prompt path now appends
recognized-template layers (selection as finder references); append-only
(add / delete-last / undo / redo). **T0–T5 stay green.**

## Maximum deliverable

Robust provenance through booleans/fillets; a richer recognized-template set;
edge provenance; a minimal read-only FE Layer Stack list (full panel is TP3).

## Sprint / day breakdown

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 1 | **Layer + LayerStack model + emit.** Define `Layer` (id, source, kind, params, selection, input/output hash) + `LayerStack` (layers, revision); emit the stack as one build123d script (template → snippet, code layer → inlined verbatim). | `layer_stack` types + `emit(stack)`. | A `[box-template, code-layer]` stack emits a runnable script; unit tests on the model + deterministic emit (byte-identical twice). |
| 2 | **Deterministic fold + per-layer cache.** Execute the stack as a fold (`solid_N = f_N(solid_{N-1})`) reusing `mesh_cache`, keyed per layer on `(input_hash, source)`; rebuild from the first dirty layer. | `LayerStack.rebuild()`. | Building a stack runs each layer once; an unchanged prefix is cache-served (no re-exec); two rebuilds are byte-identical. |
| 3 | **Provenance → clickable layers.** `provenance.attribute(prev, next)` (geometric diff via `iter_faces`/finder) → `created_by`/`last_modified_by` **sets**; bake into the mesh face/edge ids (F39). | `provenance` module + mesh tags. | On a `[box, chamfer]` stack, each face resolves to its owning layer (chamfer faces → chamfer; trimmed box faces carry `last_modified_by` chamfer); test asserts attribution. |
| 4 | **Recognized templates.** `templates.recognize(layer)` for box/cylinder/sphere/chamfer → `kind=template` + extracted params; else `kind=code` (F40). | `templates` module. | The four known kinds recognise with params; an arbitrary code layer → `code`; tests cover both. |
| 5 | **Shared live document + versioned stack + CAS.** Backend holds one active `LayerStack`; `revision` bumps per mutation; `add_layer(code, expect_rev)` / `delete_last(expect_rev)` reject on stale revision (F44/N16). | shared-doc + mutation API. | A stale-revision mutation is rejected; a race test (two edits, same rev) → one applied, one rejected-and-replanned; the stack never corrupts. |
| 6 | **Session → shared-doc refactor.** Evolve `Session` from owning a per-connection document to **attaching to the one shared active document**; route undo/redo + snapshots through the versioned stack. | refactored `session`. | Existing `session`/`server`/`document` tests pass against the shared-doc model; undo/redo work; **T0–T5 green**. |
| 7 | **`.touch` persistence for the Layer Stack.** Save/load the stack (layers + source + selection) as `.touch` (schema bump + migration from the op-history format). | document save/load. | Save → reopen → identical stack (incl. a code layer); an old op-history `.touch` migrates to a layer stack; round-trip test. |
| 8 | **Workspace-confined executor.** `Executor` runs cwd=workspace, no secrets in env, network off by default, soft import-lint (warn on `os`/`socket`/`subprocess`); single chokepoint (F46). | hardened `executor`. | The executor can't write outside the workspace or reach the network in a test; the import-lint warns; existing executor tests pass. |
| 9 | **Wire click-to-prompt → layers.** The T5 planner/adapter path now **appends a recognized-template layer** (selection as a **finder reference**, F45) instead of an op-history entry; the built-in click→chamfer still works. | click path emits layers. | A click → "chamfer 2 mm" appends a chamfer layer that is clickable (provenance) and undoable; the live flow works end-to-end. |
| 10 | **Exit verification + CI.** Append-only undo/redo on the stack; run the exit criteria live; full CI (backend + web). | verified phase. | The exit criteria below hold live; `make ci` + web tests green. |

## Exit criteria

- Build a part as a **stack including a freeform code layer**; **click a face →
  its owning layer highlights** (and hover-layer → its faces).
- **Undo/redo** per layer (append-only: add / delete-last); reopen the `.touch`
  → **identical** stack.
- A **stale-revision mutation is rejected** (N16); the existing click-to-prompt
  chamfer still works, now as a recognized-template layer.
- **T0–T5 remain green**; full CI passes.

## Known risks for this phase

- **R-A — Session→shared-doc refactor regresses the green path** (Day 6 touches
  T3–T5's working undo/redo + protocol). *Mitigation:* keep all existing tests
  green as the gate; land the shared-doc model behind the same protocol surface;
  do Day 6 after the model/fold (Days 1–2) are solid.
- **R-B — Provenance is heuristic** (booleans/fillets → ambiguous / multi-owner
  faces). *Mitigation:* owner **sets** (not scalars); region-scoped diff for
  local ops, full diff only on booleans; fail-loud on no-match; v0 parts are
  simple. (Robustness-through-booleans is a Max item.)
- **R-C — `.touch` format change + migration** (op-history → layer stack).
  *Mitigation:* schema bump + a migration that wraps existing ops as
  recognized-template layers; round-trip test on the T4/T5 corpus.
- **R-D — Toponaming is deferred** (append-only v0); re-edit/reorder of earlier
  layers is out of scope (T15). Don't let Day 9's finder-ref selection creep
  into re-edit.
- **R-E — FE is intentionally minimal here** (read-only list at most); the full
  Layer Stack + agent panel is TP3 — don't gold-plate the UI in TP1.
