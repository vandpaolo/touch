# Notes — Constraints

Hard limits. "Must not…", "can't…", "blocked by…", "the library only
supports…", "licensing forbids…", "must run on a server without a display".

Constraints feed:
- `01-requirements.md` → Constraints & assumptions section
- `02-architecture.md` → cross-cutting concerns and NFR satisfaction
- `02-classes.md` → dependency rules (e.g. "no module in src/ may import X")

---


## 2026-05-28 — Adapter export contract (CF#1, confirmed live)

> absorbed into docs/02-data-model.md + docs/adr/0004 @ 2026-05-28

Confirmed end-to-end against the live Anthropic API (Opus 4.7) on
2026-05-28: the L-bracket reference prompt ("an L-bracket 100 x 60 x 5 mm
with two 6 mm mounting holes") returns an Intent with `features: []`,
`modifiers: []`, and `extras` containing raw build123d source ending in
`body = bp.part`.

`build123d_target._export` returns `""` when `intent.features` is empty,
so the emitted program defines `body` but **never calls `export_step`** →
no STEP for any extras-only Intent. The planner system prompt already
promises the opposite (few-shot line: "must define a `body` variable so
the adapter's `export_step(body, ...)` works").

Constraint as ratified in ADR-0004 (this supersedes the first-draft
"uniform `body`" idea below — the fixtures showed the final-feature id
varies, so a uniform rule was **rejected**):
- **Feature-based Intent** (`features` non-empty): the adapter exports
  `features[-1].id`, unchanged. The final feature's id is whatever the
  planner named it — the 11 snapshot fixtures use `body`, `cyl`, `slab`,
  `solid`, `ball`, `shell`. No reserved name on this path.
- **Extras-only Intent** (`features` empty, `extras` present): the
  extras block MUST assign `body`; the adapter emits
  `export_step(body, "part.step")`. `body` is the reserved name for the
  escape hatch only.
- **Degenerate Intent** (both empty): `AdapterRefusal(where="export:empty")`.
- The adapter does not parse `extras`; a missing `body` binding surfaces
  as a `NameError` at execution time.

> First-draft note (kept for history, **not** what was adopted): an
> earlier reading proposed a uniform "`body` is always the export
> variable." Rejected in ADR-0004 because it would break 5 of the 11
> snapshot fixtures whose final feature id is not `body`.
