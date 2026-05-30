# 0008 — Picking and face-identity: kernel IDs in mesh + geometric finders + append-only v0

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** vandpaolo

## Context

Touch's core interaction is **click a face → prompt**. The "click" must
feel native-CAD instant (no backend round-trip, requirement N1). The
"prompt" needs to attach the click context to a structured operation
that the system can later replay and have it mean the same thing.

Two hard problems:

1. **Make clicks instant** — the frontend has a tessellated mesh, three.js
   raycasts a triangle; how does it know which CAD *face* that triangle
   belongs to *without* asking the kernel?
2. **Make clicks survive edits** — when an operation in history is
   replayed (after a crash, or on re-opening the file, or potentially
   after re-editing earlier ops), "the face I clicked" must still refer
   to the same face on the rebuilt solid. CAD's classic
   **topological / persistent naming** problem — famously hard, with no
   universal solution (FreeCAD has wrestled with it for years).

The 2026-05-29 deep-research pass surfaced two patterns from real
products:

- **Onshape** carries kernel-owned IDs per face/edge in the streamed
  tessellation; selection is local; cross-edit identity is resolved via a
  server-side `idtranslations` endpoint (no persistent client IDs).
- **Replicad** uses **stateless "finders"** — predicates against the
  current shape (`inPlane`, `containsPoint`, `ofSurfaceType`, chained
  AND) — re-evaluated per model state.

Both patterns have merit; both can compose.

## Decision

**Combine the two patterns. Sidestep the worst of persistent naming for
v0 by making the operation history append-only.**

### For instant local picking (problem 1)

- The backend's tessellator (`touch_backend.tessellate`, wrapping OCP /
  `ocp_tessellate`) **bakes per-face and per-edge IDs into the streamed
  mesh** (`face_tag_per_triangle`, `edge_tag_per_segment` buffers, see
  `02-data-model.md` § Mesh).
- three.js raycaster returns the triangle index; the frontend looks up
  the face ID locally in O(1). **Zero backend calls on hover / click /
  select.**

### For edit-surviving operation references (problem 2)

- The kernel ID at click time is a **hint**, not the source of truth.
- The `Selection` value object in the persisted operation carries a
  **`finder: list[FinderPredicate]`** — re-derivable geometric
  predicates (plane-normal, contains-point, surface-type, centroid-near,
  of-feature, area-near, edges-count). See `02-data-model.md` §
  FinderPredicate.
- On replay, the kernel re-evaluates the finder against the rebuilt
  solid. If exactly one entity matches, the operation applies. If zero
  or multiple match, it's a structured error → triggers a clarification
  conversation (F7 / F21).

### For v0 scope discipline

- **The operation history is append-only.** Re-editing an earlier op is
  *not* a v0 feature. This eliminates the *worst* case of persistent
  naming — the one where editing op #3 changes which faces exist when
  op #5 replays. With append-only, finders only need to be stable across
  *crash recovery / file reopen / undo back-and-forth on a linear
  history* — much easier than full parametric edit.

## Consequences

- Selection feels instant (N1) — picking is purely local mesh lookup.
- Operations recorded in `.touch` files remain valid across crash
  recovery, file re-opens, undo/redo, and Touch version bumps (as long
  as the kernel's predicate semantics are stable).
- The system has a **principled fallback to clarification** when
  geometry is ambiguous — instead of guessing the wrong face, it asks
  (F7). Visible failure mode > silent semantic failure.
- A `.touch` file is portable to any future kernel that can re-execute
  it (finders are kernel-neutral geometric predicates).
- **Cost:** authoring the right finder per click requires the backend
  to inspect the picked face's geometric features at capture time
  (plane normal, surface type, containing-feature provenance, etc.) and
  emit a set of predicates that uniquely identify it. That's
  non-trivial backend logic, but it's the load-bearing innovation that
  makes click-and-prompt CAD durable.
- **Cost (deferred):** v0.1+ parametric editing of history (re-open
  op #3, change its parameter, replay forward) re-opens the full
  topological-naming problem. That's a known, deep CAD problem and is
  explicitly out of v0; finders + per-op clarification get us most of
  the way; the rest is a real engineering project.
- **Cost:** ambiguity in finder resolution (0 or > 1 match on replay)
  surfaces as a user-facing question on file open in some cases. v0
  must make that UX clear and recoverable (the user picks the right
  face from a candidate list).

## Alternatives considered

- **Kernel persistent IDs only.** Rejected: OCP IDs are not stable
  across rebuilds; even Onshape doesn't expose persistent client IDs
  and falls back to server-side translation. We'd be building the
  hardest part of CAD with the wrong tool.
- **Finders only, no kernel IDs in the mesh.** Rejected: the click→
  select interaction would have to round-trip the backend to ask "what
  did I click?" — losing N1 (instant selection).
- **Full topological / persistent naming (à la SolidWorks / Onshape's
  server logic).** Rejected for v0: real engineering project, multi-
  year for full robustness, and not needed if v0 is append-only.
- **Defer everything to v0.1 and ship without robust selection.**
  Rejected: the whole product is click-and-prompt. Picking is core.

## Carry-forward

- **Append-only is a v0 constraint, not a forever constraint.** When v0
  earns its place, the next big design pass is parametric editing of
  history → real persistent-naming engine. That's roadmap, not v0.
- **`face_id_at_capture` is a hint, not a source of truth.** It speeds
  up the common-case match on replay (when IDs happen to be stable);
  the finder is the durable identity.
