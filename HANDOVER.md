# Handover — Maquette, between phase-2a (done) and phase-2b (not yet planned)

> *Start here in any fresh chat session that opens this project. Once
> phase-2b is planned + started, rewrite the "You are here" + task
> sections for it. Always keep this short enough to read in 60 seconds.*

## You are here

- **Project:** Maquette — natural-language CAD prompt → editable parametric solid + STEP.
- **Phase-2a is `done`** (closed 2026-05-28 via `/pm-phase-report`, min + max both met). See [`docs/phases/phase-2a-report.md`](docs/phases/phase-2a-report.md).
- **No phase is active.** `docs/03-roadmap.md` frontmatter has `active_phase: null`. Scope freeze is **lifted** — design docs are editable again until the next `/pm-phase-start`.
- **Next move:** `/pm-phase-plan phase-2b` to detail the runtime/orchestration half, then `/pm-phase-start phase-2b`. But **read carry-forward #1 below first** — there's a design-layer decision that may want a `/pm-architecture` touch or a `/pm-blocker` before phase-2b coding.
- **Last commit:** `42fdea3 style: ruff format test_sanity.py (CI fix)` on `main`, pushed. CI green ([run 26561976828](https://github.com/vandpaolo/maquette/actions/runs/26561976828)).
- **Doc-only changes pending commit:** the `/pm-phase-report` frontmatter flips + this handover + the report itself are unstaged at handover time (see `git status`).

## Phases done so far

| Phase | Closed | min/max | Highlights |
|---|---|---|---|
| `phase-0` Foundations | 2026-05-17 | true/true | Intent schema + intent_validation + pricing + config; 68 tests; CI green |
| `phase-1` Adapter | 2026-05-18 | true/true | build123d adapter for all 11 v0 kinds; 3-reference round-trips; cube-with-hole STEP verified in NX |
| `phase-2a` Pipeline (LLM-facing) | 2026-05-28 | true/true | `agent.sanity` + `agent.planner` (Anthropic prompt caching) + `agent.worker` shim; planner system prompt with 3 few-shots; 129 tests, 6 import-linter contracts |

129 tests passing (+ 3 live tests skipped by default). CI green on every push to `main`.

## What phase-2a shipped (the LLM-facing pipeline)

- [`src/maquette/agent/sanity.py`](src/maquette/agent/sanity.py) — F6 dimension check. `check(prompt, intent) -> SanityResult`. Pure, regex-based, ±1%/±0.5 mm tolerance (ADR-0002).
- [`src/maquette/agent/planner.py`](src/maquette/agent/planner.py) — F2. `plan(client, prompt, model, prompts) -> PlanResult`. Anthropic call with `cache_control` ephemeral system prompt (ADR-0003), 3-tier JSON extraction, one retry (on JSON-extraction OR schema fail) within a 2-call budget, `PlannerExhausted` on exhaustion. Carries `Tokens` + `retries` + `duration_s`. `PromptsBundle` (with `.hash`, currently empty) lives here.
- [`src/maquette/agent/worker.py`](src/maquette/agent/worker.py) — F3 shim. `emit_code` delegates to the phase-1 build123d adapter; `emit_journal` stubs v0.1.
- [`prompts/planner.system.md`](prompts/planner.system.md) — Intent schema + 11-kind contract tables + 3 few-shots (cube-with-hole, cylinder-with-chamfer, L-bracket-with-extras) + v0-gap → extras guidance.
- [`tests/test_planner_live.py`](tests/test_planner_live.py) — `@pytest.mark.live` smoke, gated by `ANTHROPIC_API_KEY`, excluded from default `pytest` via `addopts = "-m 'not live'"`.

## Carry-forward — READ BEFORE PLANNING PHASE-2B

**1. (HIGH) Extras-only Intents produce no STEP export.** The L-bracket
few-shot tells the planner to emit geometry in `Intent.extras` with
*empty* `features`. But [`_export`](src/maquette/adapters/build123d_target.py)
returns `""` when `features` is empty → the emitted program defines
`body = bp.part` (by convention) but never calls `export_step(...)`.
Phase-2a never ran the executor so this didn't surface in tests, but
phase-2b's round-trip will hit it on the L-bracket reference prompt.
There's also no contract forcing extras to define `body`. **This crosses
the frozen design layer** (`02-data-model.md` adapter contract), so the
fix is likely a `/pm-architecture` touch or `/pm-blocker`, not a silent
code edit. Decide early. Full detail: phase-2a-report § Surprises #1 +
Recommended changes #1.

**2. (MED) Live API path is untested.** Everything in phase-2a is
mock-driven. Run `pytest -m live` (needs `ANTHROPIC_API_KEY` in env)
before wiring the loop — it surfaces real retry rate (P2a-R2), JSON-fence
behaviour, and whether the L-bracket few-shot actually elicits valid
extras. No key was exercised this phase.

**3. (LOW) `PromptsBundle.hash` is empty** — phase-2b's `agent.loop`
computes the rolled-up SHA-256 of `prompts/` per ADR-0003 and stamps
`status.json.prompts_hash`. Field exists; loop fills it.

**4. (LOW) `PlanResult.duration_s` is ready** for `trace.jsonl` — loop
should record it per planner call.

**5. (process) Run the FULL CI sequence before pushing.** `ruff check`
and `ruff format --check` are *separate* gates; phase-2a burned a CI
cycle missing the latter. See "Useful commands" for the full list.

## Read in this order (under 10 minutes total)

1. `./CLAUDE.md` — project guide, framework reference, scope-freeze rule.
2. [`docs/phases/phase-2a-report.md`](docs/phases/phase-2a-report.md) — what just shipped, the 7 surprises, and the 6 recommended changes feeding phase-2b.
3. [`docs/03-roadmap.md`](docs/03-roadmap.md) § Phase 2b — the goal/min/max/exit-criterion stub you'll expand with `/pm-phase-plan`.
4. [`docs/02-classes.md`](docs/02-classes.md) § Agent module — class shapes for `Executor`, `ExecutionResult`, `Loop`, `RunConfig` (the phase-2b surface).
5. [`docs/adr/0002`](docs/adr/0002-dimension-sanity-check.md) § Loop integration — how the loop consumes `SanityResult` (logs `DIMENSION_WARNING`, continues, never gates).

## Phase-2b at a glance (from roadmap; not yet a detailed plan)

- **Goal:** Worker code runs in a sandboxed subprocess, STEP captured, renders produced, Loop ties it together with `trace.jsonl` + `status.json`.
- **Min:** `agent/executor.py` (subprocess + 30 s timeout + STEP capture + `error.json`); `render/orthographic.py` (PyVista headless, 3 PNGs); `agent/loop.py` (state machine `PROMPT_RECEIVED → PLANNING → CODE_EMITTING → EXECUTING → DONE_OK | *_FAILED`, `trace.jsonl`, `status.json` with `cost_usd_estimate` via `pricing.py`).
- **Max:** end-to-end integration test with mocked LLM; per-step duration in `trace.jsonl`; SIGKILL test (infinite-loop code killed within timeout + 2 s grace, N9).
- **Exit:** `Loop.run("a 50 mm cube with a 20 mm hole through the centre")` produces a complete `output/<run-id>/` folder from a REPL with a real `ANTHROPIC_API_KEY`.

## If you hit a design gap

**Do not modify design docs while a phase is `in_progress`.** Run
`/pm-blocker`. Right now no phase is active, so design docs are editable —
but once you `/pm-phase-start phase-2b`, the freeze re-applies. Carry-forward
#1 above is the most likely blocker/architecture trigger.

## Useful commands

```bash
# Current project state
~/.claude/skills/pm-status/status.sh .

# FULL local CI sequence (run ALL of these before pushing — see carry-forward #5)
.venv/bin/ruff check src/ tests/
.venv/bin/ruff format --check src/ tests/
.venv/bin/pyright src/
.venv/bin/lint-imports
grep -rE "^(import NXOpen|from NXOpen)" src/   # must print nothing
.venv/bin/pytest -q                            # 129 passed, 3 deselected
.venv/bin/coverage run -m pytest -q && .venv/bin/coverage report

# Live planner smoke (needs ANTHROPIC_API_KEY; skipped by default)
.venv/bin/pytest -m live

# Latest CI status
gh run list --limit 1
```

## When phase-2b is done

Run `/pm-phase-report`. Then `/pm-phase-plan phase-3` (CLI) and
`/pm-phase-start phase-3`. After phase-3 comes phase-3.5 (smoke + 3
reference prompts verified manually) — **v0 ships at the end of 3.5.**

## Carry-forward to revisit before phase-5

- **Glossary close-out** — phase-1-report rec #8 + phase-2a audit-v2 override. A `/pm-architecture` pass to close remaining leaf glossary terms. Phase-2a closed `Dimension` + `DimensionMismatch` (now implemented + defined); `Build123dTarget` + `NxOpenTarget` remain. Eliminates the audit-loop pattern hit every `/pm-phase-start` so far. Not blocking phase-2b/3.
- **Extras-only export contract** (carry-forward #1) — if not resolved in phase-2b, it blocks the L-bracket reference prompt in phase-3.5.
