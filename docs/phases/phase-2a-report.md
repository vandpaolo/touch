---
phase: phase-2a
status: done
min_met: true
max_met: true
duration_planned_days: 3
duration_actual_days: 1
---

# Phase 2a — Pipeline (LLM-facing half) — Report

> *Closed out via `/pm-phase-report` on 2026-05-28. Phase started
> 2026-05-18, implementation landed in a single working session on
> 2026-05-28. Plan: [`phase-2a.md`](phase-2a.md). Audit:
> [`../audits/2026-05-18-pre-phase-2a-v2.md`](../audits/2026-05-18-pre-phase-2a-v2.md)
> (PASS with documented override on out-of-phase glossary leaves +
> README-frontmatter strict-reading).*

## What shipped

| Sprint day | Status | Artefacts |
|---|---|---|
| Day 1 — `agent.sanity` + import-linter contract | done | [`src/maquette/agent/sanity.py`](../../src/maquette/agent/sanity.py) (`Dimension`, `DimensionMismatch`, `SanityResult` frozen dataclasses; `check(prompt, intent) -> SanityResult`; single + delimited `×` regex extraction; unit-normalised comparison; ±1%/±0.5 mm tolerance; docstring links ADR-0002); `[tool.importlinter]` contract `agent.sanity → maquette.intent + stdlib`; [`tests/test_sanity.py`](../../tests/test_sanity.py) (16 tests). Commit `763953b`. |
| Day 2 — `agent.planner` + `prompts/planner.system.md` + caching | done | [`src/maquette/agent/planner.py`](../../src/maquette/agent/planner.py) (`PlanResult`, `PromptsBundle`, `PlannerExhausted`; `plan(client, prompt, model, prompts)` with `cache_control` ephemeral system prompt per ADR-0003; 3-tier JSON extraction; one retry on JSON-extraction OR schema-validation failure within a 2-call budget; defensive `getattr` token mapping per P2a-R5); [`prompts/planner.system.md`](../../prompts/planner.system.md) (Intent schema, 11-kind contract tables, cube-with-hole few-shot, v0-gap → extras guidance); `[tool.importlinter]` contract `agent.planner → intent + intent_validation + pricing + anthropic + stdlib`; [`tests/test_planner.py`](../../tests/test_planner.py) (10 tests, mocked client). Commit `737ca70`. |
| Day 3 — `agent.worker` shim + import-linter contract | done | [`src/maquette/agent/worker.py`](../../src/maquette/agent/worker.py) (`emit_code` delegates to `build123d_target.emit`; `emit_journal` stubs `NotImplementedError("v0.1: …")`); `[tool.importlinter]` contract `agent.worker → intent + adapters + stdlib`; [`tests/test_worker.py`](../../tests/test_worker.py) (3 tests). Commit `5482e36`. |
| Day 3 (MAX) — duration + centred sanity + 2 few-shots + live gate | done | `PlanResult.duration_s` (perf_counter wrap, N1 plumbing); 3 centred-keyword sanity tests; cylinder-with-chamfer + L-bracket-with-extras few-shots in `prompts/planner.system.md`; `@pytest.mark.live` [`tests/test_planner_live.py`](../../tests/test_planner_live.py) (3 tests, gated by `ANTHROPIC_API_KEY`, `addopts = "-m 'not live'"`). Commit `5482e36`. |

**Exit criteria** — all nine met:

1. `pyright src/` exits 0.
2. `agent.sanity.check("a 50 mm cube with a 20 mm hole through the centre", <cube-with-hole Intent>)` → `SanityResult(ok=True, …)` (test `test_cube_with_hole_reference_prompt_matches`).
3. `agent.planner.plan(<mocked>, …)` → `PlanResult` whose `.intent` has one `box` feature + one `hole` modifier (test `test_plain_json_response_validates_and_maps_tokens`).
4. `agent.worker.emit_code(<cube-with-hole>)` → non-empty string containing `export_step(body` (test `test_emit_code_delegates_to_build123d_adapter`).
5. `lint-imports` — 6 contracts kept, 0 broken (3 phase-0/1 + sanity + planner + worker).
6. `pytest -q` → 129 passed, 3 deselected (live). Coverage: `agent.sanity` 96%, `agent.planner` 90%, `agent.worker` 100% — all above the ≥80% bar.
7. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing.
8. CI green on the most recent push to `main` ([run 26561976828](https://github.com/vandpaolo/maquette/actions/runs/26561976828), 1m14s).
9. This report exists.

## What slipped

Nothing functional. Min + Max both met; no sprint row deferred or skipped.

One process hiccup (not a scope slip): the first day-3 push failed CI on
`ruff format --check` — local pre-push verification had run `ruff check`
but not `ruff format --check`, which is a separate gate. Fixed in commit
`42fdea3`; CI green on re-push. Captured as surprise #2.

## Surprises

1. **Extras-only Intents produce no STEP export (highest-impact
   carry-forward).** The MAX L-bracket few-shot instructs the planner
   to emit the full L-geometry in `Intent.extras` with **empty**
   `features` (the v0 schema has no L-primary / no `union`, per
   phase-1 surprise #3). But [`_export`](../../src/maquette/adapters/build123d_target.py)
   returns `""` when `intent.features` is empty — so an extras-only
   Intent emits the extras block verbatim (defining `body = bp.part`)
   but **no `export_step(...)` call**. Phase-2a never runs the executor
   (planner/worker only emit strings; mocked tests don't round-trip),
   so this is not a phase-2a failure — but it means the L-bracket
   reference prompt will not produce a STEP in phase-2b's round-trip
   without an adapter/worker fix. There is also no contract forcing
   extras to define a variable named `body`. **This is the #1
   phase-2b/phase-3.5 risk** — see Recommended changes #1.

2. **CI `ruff format --check` is a distinct gate from `ruff check`.**
   The day-3 commit passed `ruff check` locally but `test_sanity.py`
   carried formatting drift that only `ruff format --check` catches.
   Burned one CI cycle + a follow-up commit (`42fdea3`). Lesson: run
   the *full* CI sequence (`ruff check` **and** `ruff format --check`,
   pyright, lint-imports, NX-grep, pytest, coverage) before every push.

3. **P2a-R3 (sanity false positives) is structurally near-impossible,
   not just mitigated.** The risk imagined a `pattern count=4` being
   extracted as a "4 mm" dimension. But the extraction regex
   *requires* a unit token (`mm|cm|m|in`); bare numbers are never
   extracted. The 3 centred-keyword tests pass trivially because
   "centred" carries no numeric+unit token to flag. The only way to
   get a false positive is a genuine numeric+unit substring in the
   prompt that has no matching Intent value — which is the *intended*
   behaviour, not a false positive. Risk is lower than the plan rated it.

4. **Empty `features` validates at the schema level.** `Intent.features`
   has no `min_length`, so `"features": []` passes pydantic validation.
   This is what *enables* the extras-only L-bracket pattern at the
   schema layer — but combined with surprise #1, it's a footgun: a
   schema-valid Intent can still produce a non-exporting build123d
   program. Phase-2b should decide whether extras-only Intents are a
   supported shape (and if so, fix the export path) or whether the
   planner should always emit at least a placeholder feature.

5. **Planner retries on JSON-extraction failure, not only pydantic
   `ValidationError`.** The plan text said "one retry on `ValidationError`."
   In implementation both failure classes (couldn't extract a JSON
   object, OR extracted JSON failed `Intent.model_validate`) consume
   one of the 2 call-budget attempts and feed a stricter addendum to
   the retry prompt. This is a strictly-more-robust reading of the
   intent ("retry on schema fail"), within the same 2-call ceiling.
   Covered by `test_non_json_response_triggers_retry_and_exhausts`.

6. **ADR-0003 SDK shape held through implementation.** P2a-R1 + P2a-R5
   were closed by the pre-phase verification (2026-05-18); no further
   drift surfaced while writing `plan()`. `cache_control` on the
   system block and the four `usage` token fields mapped exactly as
   documented. **Caveat:** this is verified against the *mocked* client
   only — the live path (`pytest -m live`) was written but not run this
   phase (no key exercised in-session). Real-API shape + retry rate
   (P2a-R2) remain unexercised until someone runs the live suite.

7. **Phase pacing held at ~1 active day vs 3 planned** — third data
   point after phase-0 (4→1) and phase-1 (5→1). The Anthropic-key
   friction phase-1's report worried about did not materialise, because
   the live tests are gated/skipped and the MIN is entirely mock-driven.
   The friction is deferred, not absent: it lands the first time someone
   runs `pytest -m live` or wires the loop in phase-2b.

## Decisions taken mid-phase

No blockers filed. No design pivots required. Three in-scope choices
made inside the locked plan:

- **`PromptsBundle` lives in `agent/planner.py`** (not a separate
  `prompts` module). The architecture's module map has no `prompts`
  module; the planner is its only consumer this phase. `agent.loop`
  will import it from here in phase-2b; relocate then if the loop
  wants it elsewhere.
- **Retry covers JSON-extraction failures too** (surprise #5) — broader
  than the literal plan wording, same 2-call budget.
- **L-bracket few-shot uses empty `features` + extras** — the cleanest
  expression of "v0 can't model this primitive," but it exposed the
  export gap (surprise #1). The few-shot content is correct as
  *planner guidance*; the *adapter* is what needs the phase-2b fix.

## Recommended changes for next phase

Phase-2b is the Pipeline runtime / orchestration half: `agent.executor`,
`render.orthographic`, `agent.loop` (with `trace.jsonl` + `status.json`).

1. **Fix the extras-only export gap (surprise #1) before the L-bracket
   reference prompt is exercised.** Options: (a) `_export` falls back to
   exporting a conventional `body` variable when `features` is empty
   and `extras` is present; (b) establish a documented contract that
   extras must assign `body` and have the worker/adapter export it;
   (c) planner always emits a placeholder feature. This is a
   `02-data-model.md` / adapter-contract question — likely a
   `/pm-blocker` or a `/pm-architecture` touch, since it crosses the
   frozen design layer. **Decide this early in phase-2b planning.**

2. **Run `pytest -m live` before wiring the loop.** The system prompt
   (P2a-R2) and real SDK shape are untested against the live API. One
   run surfaces retry rate, JSON-fence behaviour, and whether the
   L-bracket few-shot actually elicits valid extras. Needs
   `ANTHROPIC_API_KEY` in the environment (phase-2a never exercised it).

3. **`PromptsBundle.hash` is currently empty.** Phase-2b's `agent.loop`
   computes the rolled-up SHA-256 of `prompts/` per ADR-0003 and stamps
   it into `status.json.prompts_hash`. The field exists; the loop fills it.

4. **`PlanResult.duration_s` plumbing is ready** for `trace.jsonl`. The
   loop should record it per planner call alongside `tokens`.

5. **Add a full-CI-sequence pre-push habit** (surprise #2). Consider a
   `make check` / pre-commit hook running `ruff format --check` so the
   gate isn't missed manually. Optional ergonomics, not blocking.

6. **Glossary follow-up still pending** (carried from phase-1 audit-v4
   override + phase-1 report #8): a `/pm-architecture` pass before
   phase-5 to close the four leaf glossary terms. `Dimension` and
   `DimensionMismatch` are now *implemented* (phase-2a) and *defined*
   in `02-classes.md` glossary, so two of the four leaves are de-facto
   closed; `Build123dTarget` and `NxOpenTarget` remain. Not blocking
   phase-2b.
