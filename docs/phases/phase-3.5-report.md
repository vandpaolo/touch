---
phase: phase-3.5
status: done
min_met: true
max_met: false
duration_planned_days: 2
duration_actual_days: 2
---

# Phase 3.5 — Smoke + reference examples — Report (v0 SHIPPED)

> *Closed out via `/pm-phase-report` on 2026-05-29. Phase started
> 2026-05-28; verification surfaced two design over-promises (both
> blockered + resolved) and three implementation bugs (all fixed) before
> the gate passed on 2026-05-29. Plan: [`phase-3.5.md`](phase-3.5.md).
> Audit: [`../audits/2026-05-28-pre-phase-3.5.md`](../audits/2026-05-28-pre-phase-3.5.md)
> (9 PASS, 0 FAIL).*

## What shipped — v0

The v0 success criterion holds: the two **hard-gate references** run
end-to-end via the `maquette design` CLI, open in FreeCAD, and visually
match (user-verified), within the 20 s / $0.10 budget.

| Reference | Role | Result | Latency | Cost | FreeCAD |
|---|---|---|---|---|---|
| `a 50 mm cube with a 20 mm hole through the centre` | gate | DONE_OK | 9.5 s | $0.025 | ✓ matches |
| `a 30 mm diameter, 40 mm tall cylinder with a 2 mm chamfer` | gate | DONE_OK | 10.1 s | $0.027 | ✓ matches (all-edges) |
| `a 60 × 40 × 5 mm L-bracket` | showcase | DONE_OK | 11.8 s | $0.028 | ✓ clean L-shape (extras relief valve) |

Sprint rows:

- **Day 1 (MIN) — run references + measure + FreeCAD check:** done. All
  three run; both gate STEPs human-verified in FreeCAD; the bare L-shape
  showcase captured (`output/v0ship/2026-05-29T14-50-06__l_bracket_60x40x5`).
- **Day 2 (MAX) — live smoke test + p95 script + curated `examples/`:**
  **not done** (see What slipped). Optional; not required for ship.

**Exit criteria:** the two hard-gate references pass FreeCAD + budget on
the CLI; the L-bracket showcase has a known-good captured run; NX grep
clean; default CI green; this report exists. **v0 is shipped.**

## What slipped (and why)

- **MAX deliverables deferred** (`max_met: false`): the live smoke test
  (`tests/test_smoke.py`), the p95 latency script, and the curated
  `examples/` corpus were not built. They are polish/automation, not
  ship-gating — the MIN (manual gate verification) is the v0 ship bar.
  Natural to fold into v0.1 (the `examples/` corpus is already the
  phase-4 / phase-7b deliverable).
- **Scope grew well beyond "verify and ship":** verification turned into
  two design re-scopes + three bug fixes. That's the verification phase
  doing its job, but it's why actual ≈ 2 days vs 2 planned (the planned
  days assumed clean references).

## Surprises

1. **Verification was where the real bugs lived.** A phase that looked
   like "run three prompts and eyeball them" surfaced **three
   implementation bugs** the earlier phases' mocked tests never hit:
   the executor doubled the code path with a relative `out_dir` (commit
   `2df4e27` — would have broken the *default* `output/`); the adapter
   emitted a parameter that shadowed a build123d function (`chamfer`,
   commit `0971b96`); and (earlier) the planner few-shot emitted
   non-runnable build123d. Mock-driven tests pass on shapes; only real
   end-to-end runs expose these.
2. **Two reference prompts over-promised vs the v0 schema** — caught
   only by running them. "chamfer on the top edge" + "a hole in each
   flange" need edge-selection / oriented holes the schema omits;
   routed to fragile `extras` with no guard (R7). Led to blocker #1.
3. **Even a *single* hole via `extras` is reliably broken**, not just
   occasionally — the LLM mishandles the build123d hole workplane and it
   silently no-ops (valid STEP, no hole). The user's FreeCAD eye caught
   it. Led to blocker #2. This is the strongest possible justification
   for front-loading the v0.1 Evaluator (phase-4) + schema
   hole-positioning (phase-4.5).
4. **Human-in-the-loop earned its place.** Every geometry bug here was
   caught by a human looking at the result, exactly the v0 design
   (Evaluator is v0.1). v0 ships honest about this: the gate is
   schema-native + human-verified.
5. **The hard gate held throughout.** Cube + cylinder (schema-native)
   were correct once the executor/adapter bugs were fixed; the churn was
   all in the `extras`-dependent showcase. Schema-native is the reliable
   core; `extras` is the best-effort relief valve. v0's scope now says
   so explicitly.

## Decisions taken mid-phase (blockers)

Two blockers, both filed and resolved within the phase:

- **[`2026-05-28-v0-references-exceed-schema`](../blockers/2026-05-28-v0-references-exceed-schema.md)**
  (hard → resolved): the cylinder/L-bracket references demanded geometry
  past the v0 capability bound. Resolved "do all four, sequenced" —
  restated the references honestly + added a v0 capability bound (vision/
  requirements/roadmap), and front-loaded the Evaluator (phase-4) +
  schema edge-selection/hole-positioning (new phase-4.5) into early v0.1.
- **[`2026-05-28-l-bracket-showcase-hole-unreliable`](../blockers/2026-05-28-l-bracket-showcase-hole-unreliable.md)**
  (soft → resolved): the single-hole L-bracket showcase shipped holeless
  (extras hole silently no-ops). Resolved by narrowing the showcase to
  the bare L-shape; hole positioning deferred to phase-4.5.

Three implementation bugs fixed in-phase (not blockers — code fixes):
executor relative-path doubling (`2df4e27`), adapter parameter shadowing
(`0971b96`), planner L-bracket few-shot (`ba7bdb8`, earlier).

## Recommended changes for next phase (v0.1, phase 4)

1. **Pick up the deferred MAX work in v0.1:** the `examples/` corpus is
   already the phase-4 (≥10 sessions) + phase-7b (regression CI)
   deliverable; the cube/cylinder/L-shape runs captured here seed it. The
   live smoke + p95 script are cheap to add alongside.
2. **Phase-4 (Evaluator) is now doubly justified** — it auto-catches the
   silent-no-op class (blocker #2) that a human caught here. It is
   correctly first in v0.1.
3. **Phase-4.5 (schema edge-selection + hole-positioning)** removes the
   `extras` reliance that caused both blockers — confirm it makes the
   "chamfer the top edge" + "hole in each flange" prompts work natively.
4. **Verify on a genuinely fresh clone** for the next ship milestone:
   this phase's runs used the dev venv; the README install path (incl.
   the vtk-osmesa swap) should be exercised from scratch once before a
   public-facing release.
