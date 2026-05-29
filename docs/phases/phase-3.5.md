---
id: phase-3.5
title: Smoke + reference examples (v0 ships)
status: done              # flipped 2026-05-29 via /pm-phase-report — v0 SHIPPED
started: 2026-05-28        # ISO date when flipped to in_progress
finished: 2026-05-29       # ISO date when flipped to done
min_goal_met: true        # true | false | null
max_goal_met: false       # true | false | null
blocker: null             # resolved: blockers/2026-05-28-l-bracket-showcase-hole-unreliable.md
depends_on: [phase-3]
audit: audits/2026-05-28-pre-phase-3.5.md
---

# Phase 3.5 — Smoke + reference examples (v0 ships at the end of this phase)

> *Drafted via `/pm-phase-plan` 2026-05-28; **refreshed 2026-05-28** after
> blocker `2026-05-28-v0-references-exceed-schema` restated the v0
> references (vision/requirements/roadmap). Once `in_progress`, scope is
> frozen — this refresh aligns the plan to the just-resolved blocker.*

- **Goal:** Verify the **v0 success criterion** (vision § Success
  criteria, restated): the two **schema-native hard-gate references**
  succeed end-to-end via the `maquette design` CLI on a clean checkout
  and visually match in FreeCAD, within the v0 capability bound; plus the
  **L-bracket best-effort showcase** of the `extras` relief valve. **v0
  ships when this phase closes.** Verification phase — almost no new code.
- **Depends on:** [`phase-3`](phase-3.md) (`status: done`); the v0
  pipeline + CLI complete; the restated references in
  [`00-vision.md`](../00-vision.md) / [`01-requirements.md`](../01-requirements.md)
  / [`03-roadmap.md`](../03-roadmap.md) (blocker resolved); the executor
  relative-path fix (commit `2df4e27`). NFRs N1/N2/N5 are what this phase
  *measures*.
- **Estimated duration:** 1 day min + 1 day max (= 2 units of work).

## Policies locked for this phase

- **Hard ship gate = the two schema-native references** (vision):
    1. `a 50 mm cube with a 20 mm hole through the centre`
    2. `a 30 mm diameter, 40 mm tall cylinder with a 2 mm chamfer`
       (all edges — the schema `chamfer` modifier, *not* "top edge")
  Each must open in FreeCAD, visually match, run **< 20 s** (N1) and
  **< $0.10** (N2). These are reliable (no `extras`).
- **L-bracket is a best-effort showcase, NOT a gate.** `a 60 × 40 × 5 mm
  L-bracket` (bare L-shape — the hole was dropped per blocker
  `2026-05-28-l-bracket-showcase-hole-unreliable`; hole positioning is
  v0.1 phase-4.5) exercises the `extras` relief valve. Because `extras`
  is un-guarded until the v0.1 Evaluator, a bad generation does **not**
  block v0 — v0 ships with one known-good L-shape run captured.
- **Clean-clone install includes the vtk-osmesa swap** (README): a bare
  `pip install -e .` pulls X11-only `vtk` and segfaults on render.
- **Visual correctness is human-judged (the user).** STEP-opens +
  non-empty are automated; the *visual match* is the user's call,
  recorded in the report.
- **No API key in CI** (phase-2a decision). The live smoke (MAX) is a
  gated `pytest -m live`, run manually; default push CI stays mock-only.
- **`examples/` hygiene:** committed reference runs carry no timing/cost
  artefacts (roadmap hygiene); full regression corpus is phase-7b.

## Minimum deliverable

Phase-3.5 ships (and v0 ships) when **all** of the following exist:

- **Both hard-gate references run end-to-end via the CLI** on a clean
  checkout (README install incl. vtk-osmesa swap, only
  `ANTHROPIC_API_KEY` set), each producing a complete `output/<run-id>/`
  with a non-empty `part.step` + 3 render PNGs, exit 0, **< 20 s** and
  **< $0.10**. *(Cube already verified clean this session — DONE_OK,
  9.1 s, $0.007, commit `2df4e27` fixed the path bug that initially
  masked it. Cylinder must be re-run with the restated all-edges prompt.)*
- **Human FreeCAD verification (user):** the cube and cylinder STEPs open
  in FreeCAD and visually match. Pass/fail recorded per reference.
- **L-bracket showcase:** at least one known-good run captured
  (`extras` relief valve demonstrated end-to-end → valid STEP + renders).
- **Results captured in `phase-3.5-report.md`** (table: reference →
  latency, cost, STEP-opens, visual-match). A hard-gate reference failing
  the visual or budget bar blocks v0 (fix or re-blocker before closing).

## Maximum deliverable

If the MIN passes cleanly, also:

- **Live smoke test** `tests/test_smoke.py` (`@pytest.mark.live`, gated by
  `ANTHROPIC_API_KEY`, excluded from default CI): runs the two gate
  references through `Loop.run` and asserts non-empty STEP + 3 renders +
  `status.json.cost_usd_estimate < 0.10` per run.
- **Latency p95 script** (`scripts/measure_latency.py`): runs each gate
  reference 10× and reports p50/p95 wall-clock + mean cost; results pasted
  into the report.
- **Curated `examples/`** — the cube, cylinder, and a known-good L-bracket
  run committed under `examples/<name>/` (artefacts, timing stripped).
  Seeds the phase-7b corpus.

## Sprint / day breakdown

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Run the 2 gate references (cube, cylinder w/ all-edges chamfer) + the L-bracket showcase via the CLI; measure latency + cost; user opens the gate STEPs in FreeCAD | run folders for all three; a results table (reference → `duration_s`, `cost_usd_estimate`, STEP-opens, visual-match); a captured known-good L-bracket run | Both gate references exit 0 with non-empty STEP + 3 renders, < 20 s and < $0.10; **user confirms cube + cylinder open in FreeCAD and visually match**; ≥1 valid L-bracket run captured |
| 2 (MAX) | Live smoke test + p95 latency script + curated `examples/` | `tests/test_smoke.py` (`@pytest.mark.live`, 2 gate refs, STEP + cost asserts); `scripts/measure_latency.py` (10×/gate ref, p50/p95 + mean cost); `examples/<name>/` (cube, cylinder, L-bracket; timing stripped) | `pytest -m live` runs the gate smoke green; p95 script reports per-ref p50/p95 + cost (pasted into the report); `examples/` holds the 3 curated runs with no timing artefacts |

## Exit criteria

Phase-3.5 is `done` (**and v0 is shipped**) when **all** of the following hold:

1. On a clean checkout (README install incl. the vtk-osmesa swap, only
   `ANTHROPIC_API_KEY` set), `maquette design "<prompt>"` for **both
   hard-gate references** exits 0 and produces a complete
   `output/<run-id>/` (non-empty `part.step` + 3 render PNGs).
2. Each gate reference is **< 20 s** wall-clock (N1) and **< $0.10** (N2),
   per its `status.json`.
3. **Both gate STEPs open in FreeCAD and visually match** (human-verified).
4. The **L-bracket showcase** has at least one known-good captured run
   (valid STEP + renders); it is *not* required to pass a strict visual
   bar (best-effort, per the capability bound).
5. Results (latency, cost, STEP-opens, visual-match) captured in
   `phase-3.5-report.md`.
6. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing (N4).
7. Default CI green on the most recent push to `main` (live smoke, if
   added, is NOT on the push path).
8. `phases/phase-3.5-report.md` exists (via `/pm-phase-report`) and
   declares **v0 shipped**.

## Known risks for this phase

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| P35-R1 | The restated cylinder ("a 2 mm chamfer", all edges) still fails or looks wrong — e.g. the planner *re-introduces* the "top edge" extras path, or the all-edges chamfer changes the silhouette unexpectedly | low | med | The all-edges chamfer is the schema `chamfer` modifier, which round-trips (phase-1 test). Confirm the live planner emits the *modifier* (not extras) for "a 2 mm chamfer"; if it reaches for extras, that is a planner-prompt steer fix (prefer schema), not a blocker. |
| P35-R2 | The L-bracket showcase produces a wrong/exec-failing run on a given roll (un-guarded extras) | med | low | Best-effort by design — not a gate. Capture a known-good run (reroll if needed); record the caveat. The proper fix is v0.1 (phase-4 evaluator + phase-4.5 schema). |
| P35-R3 | A gate reference exceeds 20 s or $0.10 on a cold run (first-call cache-creation inflates cost) | low | med | Cube was 9.1 s / $0.007; ample margin. If borderline, use the MAX p95 script over 10 runs rather than a single cold outlier. |
| P35-R4 | "Clean clone" misses the vtk-osmesa swap → render segfaults on a fresh machine | med | med | Exit criterion #1 explicitly follows the README install (incl. the swap); do the verification from a fresh venv to exercise the documented procedure. |
| P35-R5 | Visual "match" is subjective / unrecorded | low | low | Report table records pass/fail + a one-line note per reference; optionally attach the render PNGs. The v0.1 Evaluator automates this later. |
| P35-R6 | MAX p95/smoke burns real API budget (~$1-2) for one-time numbers | low | low | MAX-only; run once. The MIN (one run per gate ref, ~$0.02) is the ship gate. |

## Notes for `/pm-phase-start`

This phase is already `in_progress` (started 2026-05-28, then blocked +
unblocked). No new `/pm-phase-start` is needed — resume directly. The
only code artefacts are the MAX `tests/test_smoke.py` +
`scripts/measure_latency.py`; no new `src/` modules. Much of the phase is
manual (FreeCAD visual check by the user). The blocker that paused this
phase is resolved (`blockers/2026-05-28-v0-references-exceed-schema.md`).
