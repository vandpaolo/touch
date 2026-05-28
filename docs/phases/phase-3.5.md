---
id: phase-3.5
title: Smoke + 3 reference examples (v0 ships)
status: in_progress       # flipped 2026-05-28 via /pm-phase-start
started: 2026-05-28        # ISO date when flipped to in_progress
finished: null            # ISO date when flipped to done
min_goal_met: null        # true | false | null
max_goal_met: null        # true | false | null
blocker: null             # path to blocker doc if status = blocked
depends_on: [phase-3]
audit: audits/2026-05-28-pre-phase-3.5.md
---

# Phase 3.5 — Smoke + 3 reference examples (v0 ships at the end of this phase)

> *Drafted via `/pm-phase-plan` on 2026-05-28. Update via `/pm-phase-plan`
> before `/pm-phase-start`; once `in_progress`, scope is frozen.*

- **Goal:** Verify the **v0 success criterion** (vision § Success
  criteria): all three reference prompts succeed end-to-end via the
  `maquette design` CLI on a clean checkout (only `ANTHROPIC_API_KEY`
  set, plus the documented install), producing STEPs that **open in
  FreeCAD and visually match** the description, each within the latency +
  cost budget. **v0 ships when this phase closes.** This is a
  *verification* phase — almost no new code; the bulk is running the CLI,
  measuring, and a human FreeCAD check.
- **Depends on:** [`phase-3`](phase-3.md) (`status: done`); the v0
  pipeline + CLI complete; requirements F1–F14 delivered; NFRs N1
  (latency) + N2 (cost) + N5 (headless) are what this phase *measures*.
- **Estimated duration:** 1 day min + 1 day max (= 2 units of work).

## Policies locked for this phase

- **The "clean clone" install includes the vtk-osmesa swap.** Per
  carry-forward, a bare `pip install -e ".[dev]"` pulls X11-only `vtk`
  and segfaults on render. The verified install procedure is the README
  steps **including** `pip uninstall -y vtk && pip install
  --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1`. The
  exit-criterion "clean clone … only `ANTHROPIC_API_KEY` set" means
  "following the README install," not a bare pip install.
- **Latency/cost bar = N1/N2 (the tighter numbers).** Each run must be
  **< 20 s wall-clock** (N1) and **< $0.10** API cost (N2), read from
  `status.json` (`duration_s`, `cost_usd_estimate`). (Vision § Success
  says 30 s — see Conflict C1; N1 is the authoritative tighter bar.)
- **Visual correctness is human-judged (the user).** "Opens in FreeCAD
  and visually matches" is not automatable in v0 (the Evaluator is
  v0.1/phase-4). The STEP-opens + non-empty checks are automated; the
  *visual match* is the user's call, recorded in the report.
- **No API key in CI for v0.** Per the phase-2a decision, the
  `ANTHROPIC_API_KEY` secret is **not** added to the push CI. Any CI
  smoke (MAX) is a separate manual/`workflow_dispatch` job, opt-in, not
  on every push (it costs real money). Default CI stays mock-only.
- **`examples/` hygiene.** If reference runs are committed (MAX), they are
  hand-curated and carry **no** timing/cost artefacts (roadmap hygiene);
  `status.json`/`trace.jsonl` timing fields are stripped or excluded. The
  full regression corpus is phase-7b (v0.1), not here.

## Minimum deliverable

Phase-3.5 ships (and v0 ships) when **all** of the following exist:

- **All three reference prompts run end-to-end via the CLI** on a clean
  checkout (README install incl. the vtk-osmesa swap), each producing a
  complete `output/<run-id>/` with a non-empty `part.step` and three
  render PNGs, exit 0:
    1. `a 50 mm cube with a 20 mm hole through the centre`
    2. `a 30 mm diameter, 40 mm tall cylinder with a 2 mm chamfer on the top edge`
    3. `a 60 x 40 x 5 mm L-bracket with a 6 mm hole in the centre of each flange`
- **Per-run latency + cost recorded** from each `status.json`
  (`duration_s`, `cost_usd_estimate`), with a pass/fail against the
  N1 (< 20 s) and N2 (< $0.10) bars.
- **Human FreeCAD verification (user):** each `part.step` opens in
  FreeCAD and the geometry visually matches the description. Pass/fail
  per prompt recorded (the L-bracket is the one to scrutinise — it uses
  the extras path).
- **Results captured in `phase-3.5-report.md`** (a table: prompt →
  latency, cost, STEP-opens, visual-match). If any prompt fails the
  visual or budget bar, that is a v0-ship blocker (file `/pm-blocker` or
  fix before closing).

## Maximum deliverable

If the MIN passes cleanly, also:

- **Live smoke test** `tests/test_smoke.py` (`@pytest.mark.live`, gated
  by `ANTHROPIC_API_KEY`, excluded from default CI): runs all three
  reference prompts through `Loop.run` and asserts a non-empty STEP +
  3 renders + `status.json.cost_usd_estimate < 0.10` per run.
- **Latency p95 script** (e.g. `scripts/measure_latency.py`): runs each
  prompt 10× and reports p50/p95 wall-clock + mean cost. Run manually;
  results pasted into the report. (Costs ~$2-3 in API calls; run once.)
- **Curated `examples/`** — the three reference runs committed under
  `examples/<name>/` (intent.json + code.py + part.step + renders), with
  timing/cost artefacts stripped (hygiene). Seeds the phase-7b corpus.
- **Optional `workflow_dispatch` CI smoke** — a manual-trigger GitHub
  Actions job that runs the live smoke when an `ANTHROPIC_API_KEY` secret
  is present. Not wired to push. (Only if the user wants to add the
  secret; otherwise documented as a future step.)

## Sprint / day breakdown

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Run the 3 reference prompts via the CLI; measure latency + cost; user opens each STEP in FreeCAD | 3 `output/<run-id>/` folders; a results table (prompt → `duration_s`, `cost_usd_estimate`, STEP-opens, visual-match); FreeCAD screenshots optional | All 3 prompts exit 0 with a non-empty STEP + 3 renders; latency < 20 s and cost < $0.10 each; **user confirms each STEP opens in FreeCAD and visually matches** (esp. the L-bracket) |
| 2 (MAX) | Live smoke test + p95 latency script + curated `examples/` (+ optional dispatch CI) | `tests/test_smoke.py` (`@pytest.mark.live`, 3 prompts, STEP + cost assertions); `scripts/measure_latency.py` (10×/prompt, p50/p95 + mean cost); `examples/<name>/` (artefacts, timing stripped) | `pytest -m live` runs the 3-prompt smoke green; p95 script reports per-prompt p50/p95 + cost (pasted into the report); `examples/` holds the 3 curated runs with no timing artefacts |

## Exit criteria

Phase-3.5 is `done` (**and v0 is shipped**) when **all** of the following hold:

1. On a clean checkout (README install incl. the vtk-osmesa swap, only
   `ANTHROPIC_API_KEY` set), `maquette design "<prompt>"` for **each** of
   the three reference prompts exits 0 and produces a complete
   `output/<run-id>/` with a non-empty `part.step` + 3 render PNGs.
2. Each run is **< 20 s** wall-clock (N1) and **< $0.10** API cost (N2),
   per its `status.json`.
3. **Each `part.step` opens in FreeCAD and visually matches** the prompt
   (human-verified by the user; recorded per prompt).
4. Results (latency, cost, STEP-opens, visual-match per prompt) are
   captured in `phase-3.5-report.md`.
5. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing
   (re-verified; N4 holds at ship).
6. Default CI is green on the most recent push to `main` (the live smoke,
   if added, is NOT on the push path).
7. `phases/phase-3.5-report.md` exists (via `/pm-phase-report`) and
   declares **v0 shipped**.

## Known risks for this phase

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| P35-R1 | The **L-bracket visually fails** in FreeCAD — the extras geometry compiles + exports a STEP but the shape is wrong (off-centre holes, wrong flange, etc.) | med | high | This is the headline v0-ship risk. The extras path (ADR-0004 + the phase-2b few-shot fix) was verified to *execute*, not to be *geometrically correct*. If it fails, it is a `/pm-blocker` (planner few-shot or schema gap) — better caught now than post-ship. Inspect the rendered PNGs first (cheap) before FreeCAD. |
| P35-R2 | A reference prompt **exceeds 20 s or $0.10** on a cold run (cache miss on first call inflates `cache_creation` tokens + cost) | med | med | Phase-2b's single run was 10.1 s / $0.0267 — comfortable. Cost is dominated by first-call cache creation; warm runs are cheaper. If a prompt is borderline, record p95 over 10 runs (MAX script) rather than a single cold outlier. If it genuinely exceeds, surface in the report (it is a real N1/N2 finding). |
| P35-R3 | The cylinder-with-chamfer prompt says "chamfer on the **top edge**" but v0 chamfers **all** edges (coarse edge selection, documented limitation) → STEP differs from the description (both rims chamfered) | med | med | This is a *known* v0 limitation (phase-1 surprise #4; data-model § coarse edge selection). Decide at verification time whether "both rims chamfered" is an acceptable v0 visual match or a documented caveat in the report. Not necessarily a ship blocker — record the judgment. |
| P35-R4 | "Clean clone" misses the vtk-osmesa swap → render segfaults on a fresh machine, so the criterion isn't truly reproducible | med | med | The exit criterion explicitly includes the README install (with the swap). The verification run should be done following the README from a fresh venv to actually exercise the documented procedure (P35-R4 closes carry-forward #4 from phase-3). |
| P35-R5 | Visual "match" is subjective and undocumented → no record of *why* a prompt passed/failed | low | low | The report table records pass/fail + a one-line note per prompt; optionally attach the 3 render PNGs or a FreeCAD screenshot. The Evaluator (v0.1) automates this later. |
| P35-R6 | The p95 / smoke MAX work burns real API budget ($2-3) for a one-time number | low | low | MAX-only; run once. The MIN (one run per prompt, ~$0.08 total) is the ship gate. p95 is a nice-to-have measurement, not a ship blocker. |

## Notes for `/pm-phase-start`

When `/pm-phase-start` runs, the Auditor sub-agent should verify:

- This phase delivers no new `src/` modules (verification phase); the
  only code artefacts are the MAX `tests/test_smoke.py` +
  `scripts/measure_latency.py`. The audit should not expect new
  components in `02-classes.md`.
- N1 (latency) + N2 (cost) + N5 (headless) are *measured/verified* here,
  not newly designed.
- **Conflict C1 (flag to user):** vision § Success criteria says 30 s
  wall-clock; N1 + roadmap exit say 20 s. This plan uses 20 s. If the
  user wants the vision aligned, that is a `/pm-vision` (or `/pm-requirements`)
  edit — out of scope for this plan, raised as a Conflict.
- Much of this phase is **manual** (FreeCAD visual check by the user);
  the plan cannot fully automate the exit criterion by design.

After audit passes, `/pm-phase-start` flips this file's `status: planned`
→ `status: in_progress`, sets `started: 2026-MM-DD`, and updates
[`03-roadmap.md`](../03-roadmap.md) frontmatter `active_phase: phase-3.5`.
Scope-freeze applies from that point.
