---
id: 2026-05-28-l-bracket-showcase-hole-unreliable
phase: phase-3.5
severity: soft
status: open
discovered: 2026-05-28
resolved: null
re_entry: vision
---

# Blocker — L-bracket showcase: hole-via-extras silently doesn't cut

## What

During phase-3.5 verification, the best-effort L-bracket showcase
(`"a 60 × 40 × 5 mm L-bracket with a 6 mm mounting hole"`) produced a
valid STEP that **opens but has no hole** — the user caught it in the
visual check. Confirmed empirically: the solid's volume is identical
with and without the hole block (19000.0 mm³ both), so the `extras`
`Hole(...)` subtracts nothing.

The planner's `extras` places the hole as:

```python
with Locations((30, 20, 5)):
    Hole(radius=3, depth=10)
```

build123d drills along the active **workplane normal**; in that
`BuildPart` context the hole does not intersect the flange, so it
silently no-ops. The L-*shape* itself is correct — only the hole fails.

**This does not block v0 ship.** The hard gate (cube + cylinder,
schema-native) both pass and are visually correct; the L-bracket is the
explicitly *best-effort, non-gating* showcase. So severity is **soft**:
a workaround exists (ship on the gate), but the showcase over-promises
and the design should catch up.

## Why the design did not anticipate it

A direct continuation of blocker `2026-05-28-v0-references-exceed-schema`
(R7, silent semantic failure). That blocker narrowed the references and
made the L-bracket a best-effort showcase, but **kept a hole on it**,
assuming a single hole would be reliable enough (or need only a reroll).
Verification shows the hole-via-`extras` is **reliably broken**, not
just occasionally — the LLM mishandles the build123d hole workplane, and
v0 has no correctness guard (Evaluator is v0.1) to catch it. Precise
hole positioning is exactly the capability the v0 schema omits and that
phase-4.5 (schema hole-positioning) is slated to add; expecting it via
un-guarded `extras` in a v0 ship reference was still an over-promise.

## Re-entry point

**Vision** (`00-vision.md` § Success criteria — the showcase reference
is a vision-owned success-criterion item), with mirrors in
`00-pr-faq.md`, `03-roadmap.md` (phase-3.5), and the phase-3.5 plan.
No requirements/architecture change needed (the capability bound +
deferral to phase-4.5 are already recorded from the first blocker).

## Proposed resolution (options)

1. **Narrow the showcase to just the L-shape** (chosen): showcase
   reference → `"a 60 × 40 × 5 mm L-bracket"`. `extras` reliably produces
   the compound L-shape (the thing the schema can't name) — a clean,
   honest demo of the relief valve. The hole is phase-4.5's job
   (first-class schema hole-positioning).
2. Keep the hole, document it as a known best-effort limitation (showcase
   ships holeless). Rejected: a holeless "bracket with a hole" is a poor
   showcase.
3. Reroll hoping the LLM gets the hole workplane right. Rejected: the
   mistake is systematic; un-guarded either way.

## Resolution

<!-- left empty; filled when the vision narrowing locks -->
