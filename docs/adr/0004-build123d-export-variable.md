# 0004 — build123d export variable convention

- **Status:** Accepted
- **Date:** 2026-05-28
- **Deciders:** vandpaolo

## Context

The build123d adapter (`adapters/build123d_target.py`) emits a single
`export_step(<var>, "part.step")` call as the program's final line.
`_export` currently derives `<var>` from `features[-1].id` and returns
`""` (no export at all) when `features` is empty.

The planner's escape hatch (ADR-0001 / `02-data-model.md` "extras is
forever") lets the planner emit geometry the v0 schema can't express as
raw build123d source in `Intent.extras`, with `features: []`. The
planner system prompt's extras-based few-shots (L-bracket, etc.) end
with `body = bp.part` and promise "the adapter's `export_step(body, ...)`
works." But the adapter never honoured that promise: with `features`
empty, `_export` returned `""`, so an extras-only Intent emitted the
geometry but **no export call** — producing no STEP.

Confirmed end-to-end against the live Anthropic API (Opus 4.7) on
2026-05-28: the L-bracket reference prompt returns `features: []`,
`modifiers: []`, and `extras` ending in `body = bp.part`; the emitted
program contains no `export_step`. Phase-2a never ran the executor, so
this was invisible until phase-2b's round-trip. Carry-forward #1.

## Decision

`body` is the **reserved export variable for the extras-only escape
hatch** — not a global rule for all Intents.

- **Feature-based Intent** (`features` non-empty): the adapter exports
  `features[-1].id`, unchanged. The final feature's id is whatever the
  planner named it (`body`, `cyl`, `slab`, `solid`, `ball`, `shell` in
  the existing fixtures). No reserved name is imposed here — forcing
  `body` would break 5 of the 11 snapshot fixtures for no benefit.
- **Extras-only Intent** (`features` empty, `extras` present): the
  `extras` block must assign `body`, and the adapter emits
  `export_step(body, "part.step")`. This aligns the adapter with the
  promise the planner prompt already makes.

- **Degenerate Intent** (`features` empty **and** `extras` empty/absent):
  the adapter raises `AdapterRefusal(where="export:empty")`. A
  no-geometry Intent is a planner failure surfaced loudly, not a silent
  STEP-less run.
- **Enforcement** of the `body` assignment: the adapter does not parse
  `extras`. It emits `export_step(body, "part.step")` unconditionally on
  the extras-only path; a missing `body` binding surfaces as a
  `NameError` at execution time (executor → `error.json`, phase-2b).
  This preserves the "never parse or rewrite `Intent.extras`" principle
  at the cost of catching the error one layer later.

## Consequences

- Extras-only Intents (the only way v0 expresses L-brackets and other
  non-primitive shapes) now produce a STEP. Unblocks the L-bracket
  reference prompt for phase-2b's round-trip and phase-3.5's v0 ship
  criterion.
- The adapter gains one branch in `_export`; existing feature-based
  fixtures are unaffected (no snapshot churn on the 11 kinds).
- `body` becomes a reserved name in the extras namespace. The planner
  prompt already documents this; no prompt change needed, though the
  few-shot wording can be tightened to say "must" explicitly.
- Trade-off: the convention is split (last-feature-id vs `body`)
  depending on Intent shape, rather than one uniform rule. Accepted
  because a uniform "always `body`" rule would force snapshot churn and
  rename the natural feature ids the planner picks.

## Alternatives considered

- **Always export `body`** (uniform rule). Rejected: breaks 5 snapshot
  fixtures (`cylinder`, `extrude`, `loft`, `revolve`, `sphere`) whose
  final feature id is not `body`, and forces the planner to rename every
  final feature. No upside over the shape-dependent rule.
- **Planner always emits a placeholder feature for extras-only shapes.**
  Rejected: pollutes the Intent with a fake primitive that doesn't model
  the geometry, and the adapter would emit dead code for it. The extras
  block is already the honest representation.
- **Have the worker (not the adapter) append the export.** Rejected:
  the worker is a thin shim (`02-classes.md`); export belongs to the
  adapter that owns code generation.
