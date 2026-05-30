# 0006 — `.touch` JSON as the native document format (operation history, not B-rep snapshot)

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** vandpaolo

## Context

Touch needs a native save format. The obvious candidates would be a
**B-rep snapshot** (STEP, BREP, or a proprietary serialized solid) or a
**mesh** (STL/3MF). All three carry geometry but throw away the
*feature history* — the ordered ops that produced the solid.

Touch's product is the click-and-prompt history itself: each operation
is a user intention, anchored to a selection, paired with a (possibly
clarified) natural-language prompt. Re-execution of that history is what
yields the geometry. Persisting the snapshot but not the history would
lose the work.

Independently, the engine boundary
([ADR-0005](./0005-localhost-websocket-coupling.md)) requires
**kernel-swappability** (any kernel — today Python OCP, tomorrow
something else — must be able to re-execute the saved file) and
**crash-recovery** (a backend crash should replay the same document and
restore the model — N8). Both are free if the file is the history;
neither is free if the file is a snapshot.

## Decision

**The Touch native file format is `.touch` — a JSON document containing
the ordered, append-only operation history (the feature tree).** Schema
is defined in `02-data-model.md` § TouchDocument; structure summarised:

```json
{
  "schema_version": 1,
  "name": "...",
  "description": "...",
  "parameters": [ … ],
  "history": [ { "id": "...", "kind": "box", "params": {...},
                 "selection": { "target": "face", "point_xyz": [..],
                                "finder": [...] },
                 "prompt_text": "...", "conversation": [...] }, … ],
  "created_at": "...", "modified_at": "...", "touch_version": "0.1.0"
}
```

- Saved as **canonical JSON** (sorted keys, fixed whitespace) so files
  diff cleanly in git.
- Carries a `schema_version`; migrations land per minor bump.
- Selections inside operations use **geometric finders** rather than
  brittle topological IDs (see
  [ADR-0008](./0008-picking-and-face-identity.md)), so they survive
  re-execution.

STEP, STL, and 3MF are **exports**, not native formats:

- **STEP** — B-rep handoff to other CAD (FreeCAD, NX, …).
- **STL / 3MF** — mesh handoff to 3D-printing slicers.

## Consequences

- The file *is* the work — kernel-swappable (any v0+ kernel re-executes
  it), undo/redo is free (step through the array), git-diff-friendly,
  human-readable.
- **Crash recovery is automatic** (N8 / F16): Electron main detects the
  sidecar exit, restarts it, sends `rebuild(history)`, the solid +
  tessellation are re-derived. The in-memory state of the sidecar is
  always a *derived cache* of the document.
- **No vendor lock-in to OCP/build123d** — the format is engine-neutral
  data. If Touch ever swaps kernel, the corpus of `.touch` files comes
  with it.
- **Forward compat is structural:** unknown `OperationKind` values or
  unknown `FinderPredicate.kind` values in newer files are handled as a
  named error (or graceful fallback) by older readers; minor-additive
  changes don't break existing files.
- **Cost:** every open re-executes the history → opening a large
  document is slower than loading a snapshot would be. Acceptable for
  the v0 size scale (single parts); cache + incremental replay can be
  added later if it matters.
- **Cost:** an `.touch` file alone doesn't carry the geometry — anyone
  who wants the B-rep needs to open it in Touch (or accept a STEP
  export). This is the intended product shape: Touch owns the
  authoring; STEP/STL are the handoff.

## Alternatives considered

- **B-rep snapshot (STEP/BREP) as native.** Rejected: loses the feature
  history, so re-editing means starting over, and there's no replayable
  audit trail of "what was clicked + said." Useful as an export, not as
  the native.
- **Mesh (STL/3MF) as native.** Rejected: lossy (no faces, no
  precision, no history) — only suitable for printing handoff.
- **Binary serialised operation history** (msgpack, protobuf, etc.).
  Rejected: faster to parse but loses the GitHub-friendly diffability
  that drove the human-readable choice. JSON is plenty fast for a
  single-user file.
- **A proprietary binary "feature tree" format** (à la `.sldprt`).
  Rejected: closed-format trap; defeats the open-source positioning;
  no diff/review story.
- **Embedding both the history AND a snapshot** in the same file.
  Rejected for v0: redundant (snapshot is rebuildable), and risks
  inconsistency. Maybe later if open-without-replay performance becomes
  load-bearing.
