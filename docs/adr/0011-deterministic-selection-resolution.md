# 0011 — Deterministic selection resolution: captured-id-first, finder-fallback; edge targeting

- **Status:** Accepted
- **Date:** 2026-06-02
- **Deciders:** vandpaolo
- **Refines:** [ADR-0008](./0008-picking-and-face-identity.md) (does not supersede — 0008's combine-the-two-patterns decision stands).

## Context

ADR-0008 chose **geometric finders** as the durable identity for a
selected entity, with the kernel `face_id_at_capture` recorded only as a
"hint for fast match." The T4 implementation took that literally and
resolved the clicked face purely from the finder's `contains_point`
predicate (`resolve_face_containing(solid, point, tol)`), ignoring the
captured id entirely.

Live testing (2026-06-02, `notes/questions.md`) showed this breaks on
ordinary interaction:

- **Edge/corner-adjacent click** → the picked world-point sits on a
  shared boundary → `contains_point` matches **N faces** →
  `FinderError: ambiguous`.
- **Pick lands a hair off the B-rep surface** (the tessellated mesh the
  user clicked is not the exact B-rep; float gap) → **zero** matches →
  `FinderError: no face contains point`.

So a point-only finder is **not a sufficient resolver** for the
within-session, just-clicked case — even though the frontend already
knows *exactly* which face was clicked (the per-face id baked into the
mesh, F20/ADR-0008). The durable finder is the right tool for *replay*;
it is the wrong tool for resolving a click the user just made.

A second, related coarseness: a chamfer resolves the clicked **face** and
chamfers its whole edge loop. The user cannot target one edge, and
overlapping loops cause "chamfer length too big" failures. The mesh
already carries per-edge ids (`edge_tag_per_segment`, ADR-0008) — the
identity machinery for edges exists but is unused.

## Decision

**Resolve a selection in tiers, captured-id first; keep the finder as the
durable fallback. Extend the same model from faces to edges.**

### Resolution order (the refinement of ADR-0008)

A `Selection` resolves to a topological entity on a given solid by:

1. **Captured id (within-session primary).** If
   `entity_id_at_capture` matches a live entity on the current solid, use
   it. Per-face/per-edge ids are **stable within a session** (existing
   assumption, `01-requirements.md`), so the just-clicked case is
   deterministic — no point-containment ambiguity, immune to
   edge/corner adjacency and mesh-vs-B-rep float gaps.
2. **Geometric finder (durable fallback).** On replay / file reopen /
   any case where the captured id no longer matches a live entity, fall
   back to the finder predicates (ADR-0008). The finder must resolve to
   **exactly one** entity.
3. **Clarification (genuine ambiguity only).** If *both* the id misses
   and the finder yields 0 or >1 matches, emit a structured error → the
   clarification conversation (F7). This is now a rare cross-session
   case, not something a normal click hits.

`contains_point` stays in the finder predicate set as a *durability*
predicate, but is no longer the sole within-session resolver.

### Edge targeting (T5b — same model, edges)

- The mesh frame already carries `edge_tag_per_segment` (F20). The
  frontend gains **edge picking** (raycast a wireframe segment → edge id),
  exactly mirroring face picking.
- The finder module gains an **edge resolver** following the same tiered
  order (captured edge id → edge finder predicates → clarify).
- `operation_adapter` applies edge-scoped ops (chamfer, fillet) to the
  **resolved single edge** (`target == "edge"`) instead of the resolved
  face's whole edge loop (F37).

### Phase split

- **T5** — tiers 1–3 for **faces** (F36); plus the clarification loop
  (F7/F22, already designed).
- **T5b** — edge picking + edge resolver + edge-scoped application (F20
  edge channel end-to-end, F37).

## Consequences

- Normal clicks resolve deterministically; "ambiguous" / "no face" stop
  appearing on within-session interaction (F36).
- ADR-0008's durability guarantee is preserved: the finder is unchanged
  as the cross-edit identity; we only changed *which* resolver wins for
  the live case, and *when* clarification triggers.
- **Selection schema gains an explicit captured-id field.** Today's
  `face_id_at_capture: int | None` generalizes to an entity id typed by
  `target` (face|edge). Carried in `protocol/schema.json` → `make
  codegen` regenerates pydantic + TS. (Faces already ship the field; the
  edge case is additive — backward compatible, `None` when absent.)
- `touch_backend.finder` becomes a named module with a documented public
  surface (`resolve_face`, `resolve_edge`) rather than a single helper.
- Edge targeting removes a class of "length too big" failures (a single
  edge has more room than a shared loop) and is the real CAD interaction.

## Alternatives considered

- **Keep finder-only, just widen tolerance.** Rejected: widening helps
  "no face" but worsens "ambiguous"; it cannot fix edge/corner adjacency,
  which is a containment fact, not a tolerance one.
- **Replace finders with raw captured ids.** Rejected: regresses
  ADR-0008 — raw ids are not durable across rebuilds; the finder must
  remain the persisted identity. Ids are the *live* disambiguator only.
- **Clarify on every ambiguous click.** Rejected: ADR-0008 already
  routes genuine ambiguity to clarification, but firing it on ordinary
  edge-adjacent clicks (where we *know* the id) is a bad-UX false
  positive. Clarification is the cross-session safety net, not the
  primary path.

## Carry-forward

- When v0.1 parametric history editing arrives (ADR-0008 carry-forward),
  the captured id stops being reliable across an edited prefix — tier 1
  degrades and tier 2 (finder) carries more weight. The tiered order is
  forward-compatible: it already falls through to the finder.
