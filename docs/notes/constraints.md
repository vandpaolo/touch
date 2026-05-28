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

Constraint to ratify in architecture:
- `body` is the **conventional export variable** for the build123d
  adapter. The final solid is always bound to `body`.
- `_export` emits `export_step(body, "part.step")`. When `features` is
  non-empty, the last feature's id is `body` by convention (every
  fixture/example already uses it); when `features` is empty but
  `extras` is present, the extras block MUST assign `body`, and the
  adapter still exports it.
- This is a `02-data-model.md` adapter-contract change (was silent on
  which variable gets exported). Freeze is lifted (no active phase) so
  it's editable now, ahead of phase-2b.
