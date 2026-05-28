---
id: 2026-05-28-v0-references-exceed-schema
phase: phase-3.5
severity: hard
status: open
discovered: 2026-05-28
resolved: null
re_entry: both
---

# Blocker — v0 reference prompts require geometry the schema omits

## What

Phase-3.5 verification ran all three v0 reference prompts through the
`maquette design` CLI. Results:

- **Cube with through-hole** — ✅ DONE_OK (9.1 s, $0.007). Schema-native
  (`box` + `hole` modifier). Renders look correct.
- **Cylinder with chamfer "on the top edge"** — ❌ EXEC_FAILED (exit 12).
  The planner routed the edge-specific chamfer to `extras` and emitted
  `body.edges().filter_by(Axis.Z)…` (selects Z-*parallel* edges; a
  cylinder's rims are not Z-parallel) → OCC `Standard_Failure: There are
  no suitable edges for chamfer or fillet`. No STEP produced.
- **L-bracket with "a 6 mm hole in the centre of each flange"** — ✅
  runs (10.7 s, $0.012) and the L-profile is correct, but the second
  hole is suspect: both holes drill along **−Z**
  (`Locations((32.5, 20, 5), (5, 20, 22.5))`), so the hole meant for the
  *vertical* flange drills downward through its height rather than
  through the 5 mm wall (−X). Needs FreeCAD confirmation, but the
  emitted code is geometrically wrong for the prompt.

So 1 of 3 references is clean; 1 fails to execute; 1 produces a likely-
wrong solid. The phase-3.5 exit criterion (all three open in FreeCAD and
visually match) **cannot be met as-is**.

## Why the design did not anticipate it

Not a one-off bug — a structural mismatch between the v0 **success
criterion** and the v0 **schema + pipeline**:

1. **The reference prompts demand capabilities the v0 schema
   deliberately omits.** "Chamfer on the top edge" needs edge-specific
   selection; "a hole in each flange" needs multi-face / oriented hole
   positioning. The v0 data model explicitly defers both: chamfer/fillet
   apply to **all** edges (coarse edge selection), and `hole` is centred
   on the target centroid along one axis. Anything finer is "`extras`-
   land" by design (`02-data-model.md` § per-kind contracts +
   architecture decisions deferred).
2. **`extras` offloads correctness to the LLM with no guard.** The
   escape hatch appends raw, LLM-hand-written build123d. For non-trivial
   geometry (edge selection, oriented holes) the LLM gets the build123d
   API subtly wrong, and **v0 has no correctness check** to catch it —
   the dimension sanity check (F6) only compares numeric dimensions, and
   the vision-LLM Evaluator + refine loop is v0.1 (phase-4). So a wrong
   `extras` either crashes (cylinder) or silently ships a wrong solid
   (L-bracket).
3. **Hand-tuning the few-shots to pass these three exact strings would
   be overfitting.** It would game the success criterion (a proxy for
   "v0 reliably turns prompts into correct geometry") without delivering
   the underlying capability — any *other* edge-selection / oriented-hole
   prompt would remain a coin-flip. The honest reading: two of v0's own
   three flagship references reach past what v0 can reliably produce.

The cube (schema-native) working cleanly confirms the core pipeline is
sound; the gap is specifically where the references exceed the schema.

## Re-entry point

**Both layers, requirements first.**

- **Requirements (`/pm-requirements`)** — the primary decision: reconcile
  the v0 success criterion / reference prompts with what v0 can reliably
  deliver. Decide the v0 scope honestly (see Proposed resolution).
- **Architecture (`/pm-architecture`)** — only if the chosen resolution
  adds capability (e.g. pulling edge-selection or hole-positioning into
  the schema, or adding a minimal correctness guard). If the resolution
  is to narrow the references, architecture may not need to change.

## Proposed resolution (options — user decides in the re-design)

1. **Narrow the v0 references to schema-native capability** (honest v0).
   E.g. cylinder → "a 2 mm chamfer" (all edges, via the schema modifier,
   which already round-trips); L-bracket → a hole pattern the centroid/
   axis model supports, or drop the second flange hole. v0 ships doing
   exactly what the schema does well; edge-specific work is explicitly
   v0.1. Cheapest; lowers the promise to match reality.
2. **Pull schema features forward** — add first-class edge selection
   (chamfer/fillet target edges) and/or hole positioning + axis to the
   Intent schema (schema-v2 elements brought into v0). Removes the
   reliance on fragile `extras` for the references. Largest scope; this
   is most of what phase-10 (schema v2) was meant to do.
3. **Accept documented approximations** — keep the references but define
   "visual match" loosely for v0: cylinder = all-edges chamfer (both
   rims), L-bracket = whatever the centroid model yields, caveats listed
   in the ship notes. Ships v0 with known, recorded limitations; no
   schema change. (Note: the cylinder still needs the planner to use the
   *modifier*, not broken extras — a prompt-steering fix, not a few-shot
   overfit.)
4. **Add a minimal correctness guard earlier** — bring a lightweight
   form of the v0.1 Evaluator (or an extras-execution dry-run + retry)
   into v0 so wrong `extras` is caught/retried rather than shipped. Helps
   reliability broadly but is a real scope addition (overlaps phase-4).

## Resolution

<!-- left empty; filled when the re-design locks and the blocker is resolved -->
