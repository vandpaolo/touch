# 0012 — Layer Stack: free build123d as clickable layers

- **Status:** Accepted
- **Date:** 2026-06-04
- **Deciders:** vandpaolo
- **Relates to:** [ADR-0008](./0008-picking-and-face-identity.md), [ADR-0011](./0011-deterministic-selection-resolution.md); supersedes the "LLM never emits free-form code / Intent schema is the pivot" stance.

## Context

The pivot (`notes/decisions.md` 2026-06-04, `00-vision.md`) makes the user's
own Claude Code the primary author. An LLM writes real build123d (loops, math,
libraries) far better than it fills a bespoke `{kind, params}` DSL, and the DSL
forces us to pre-build an op for every shape the model can imagine (a gearbox is
impossible as a flat op-list). But the editor's value — clickable faces, a
feature tree, instant undo — needs *modular, addressable structure*. The hard
fact: **general build123d → structured ops is decompilation; it cannot be done
reliably.** So we cannot keep "code and ops interchangeable."

A four-lens evaluation (2026-06-04, recorded in `decisions.md`) converged
"sound-with-changes" on the resolution below.

## Decision

**A part is a Layer Stack: an ordered list of layers, each a build123d code
block that transforms the previous solid** (`solid_N = f_N(solid_{N-1})`).

- **Execution** is a fold, re-run from the first dirty layer, with **per-layer
  content-addressed caching** (reuse `mesh_cache`, keyed on the layer's source +
  input hash). Deterministic, clean-state, **no hidden mutable state between
  layers** (the notebook-reproducibility lesson).
- **Clickability comes from computed provenance, not from the kernel.** OCCT has
  no stable cross-op face id, so at each layer Touch **geometrically diffs**
  `solid_N` vs `solid_{N-1}` (finder machinery, ADR-0011) to attribute each
  face/edge: `created_by` + `last_modified_by` (**sets** — booleans fuse faces →
  multi-owner). The result is baked into the per-face/edge ids already in the
  mesh (F20), so click→layer / hover-layer→faces is a zero-round-trip lookup.
- **Recognized templates vs code layers.** A layer whose code matches a *known
  template* (box, cylinder, sphere, chamfer — the v0 vocabulary) renders as an
  **editable parametric card**; everything else renders as a **code card**.
  Recognition matches only known templates — **never general decompilation**.
- **No decompiler.** Code is never reverse-engineered into ops. The structured
  T3–T5 ops survive *as* the recognized-template set; they are one input path,
  not a second source of truth.
- **Append-only in v0** (add / delete-last / undo). Editing or reordering an
  earlier layer is deferred (the topological-naming subsystem — R16).

## Consequences

- Free-code expressiveness **and** feature-tree granularity coexist; the long
  tail (gears, lofts, patterns) is authored as code layers with no new ops.
- Clickability is a property of the **result solid**, so a face from a 200-line
  code layer is as clickable as one from a chamfer — and you can apply
  structured click-edits *on top of* a code layer's geometry.
- **Costs:** provenance is heuristic (booleans/fillets → ambiguous/multi-owner
  faces — mitigate with sets + region-scoped diffs + fail-loud); you cannot
  click *inside* a code layer to parametrically tweak a sub-feature (edit its
  code or re-prompt); the document is now **executable code we run** → the
  executor sandbox (ADR-0016) becomes load-bearing.
- T3–T5 (planner, finder, tessellate, executor, mesh-cache) are **reused**, not
  discarded — they become the recognized-template recognizer + parametric layer.

## Alternatives considered

- **Structured-ops-only (Planner++).** Rejected: caps the model at our op
  vocabulary; we'd perpetually chase its creativity by adding ops.
- **Free code as the document, no structure.** Rejected: loses clickable
  feature granularity, per-feature undo, and the durable selection model.
- **Two synced files (part.py ↔ part.touch).** Rejected: two sources of truth +
  the decompilation problem in full — sync hell.

## Carry-forward

- Re-edit/reorder earlier layers → a later phase (reference re-resolution +
  break detection + disambiguation; ADR-0011's carry-forward applies).
- Keep template recognition *dumb* (exact known call shapes only); the moment it
  tries to understand arbitrary code it becomes the decompiler trap.
