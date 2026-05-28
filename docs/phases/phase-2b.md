---
id: phase-2b
title: Pipeline (runtime + orchestration half)
status: planned           # flips via /pm-phase-start (after audit)
started: null             # ISO date when flipped to in_progress
finished: null            # ISO date when flipped to done
min_goal_met: null        # true | false | null
max_goal_met: null        # true | false | null
blocker: null             # path to blocker doc if status = blocked
depends_on: [phase-2a]
audit: null               # path to pre-phase audit when /pm-phase-start runs
---

# Phase 2b — Pipeline (runtime + orchestration half)

> *Drafted via `/pm-phase-plan` on 2026-05-28. Update via `/pm-phase-plan`
> before `/pm-phase-start`; once `in_progress`, scope is frozen.*

- **Goal:** The worker's emitted code runs in a sandboxed subprocess, the
  STEP is captured, orthographic renders are produced, and the `Loop`
  ties planner → sanity → worker → executor together with `trace.jsonl`
  + `status.json`. Closes **F5** (Executor → STEP), **F7** (Renderer →
  3 PNGs), **F8** (run-folder artefact set), **F9** (`status.json` +
  cost accounting), **F10** (`trace.jsonl`), **F11** (run-id format).
  Satisfies **N5** (headless), **N6** (graceful failure / `error.json`),
  **N9** (subprocess timeout + SIGKILL), **N10** (self-contained run
  folder); partial **N1** (per-step duration) + **N2** (cost estimate in
  `status.json`). Also lands the **ADR-0004** adapter export fix
  (carry-forward #1) so extras-only Intents export a STEP. **Out of
  scope:** the CLI (F1, F12, F13-as-process-exit, F14) — phase-3. In v0
  the `Loop` is callable from a Python REPL; the CLI wraps it next phase.
- **Depends on:** [`phase-2a`](phase-2a.md) (`status: done`);
  requirements F5, F7, F8, F9, F10, F11 + N5, N6, N9, N10 approved;
  architecture § Layered responsibilities (`agent.executor`,
  `agent.loop`, `render` rows) + § Cross-cutting (State, Sandboxing,
  Reproducibility, Logging) approved; [ADR 0002](../adr/0002-dimension-sanity-check.md)
  § Loop integration, [ADR 0003](../adr/0003-prompt-caching-for-cost.md)
  § prompts_hash, [ADR 0004](../adr/0004-build123d-export-variable.md)
  accepted.
- **Estimated duration:** 4 days min + 1 day max (= 5 units of work).
  Roadmap gantt shows 3d (ordering only). Prior phases ran ~1 active day
  each; pace is not the constraint — PyVista-headless friction on nexus
  is the likely time sink (see P2b-R3).

## Policies locked for this phase

- **ADR-0004 export contract (carry-forward #1).** The build123d adapter
  exports `features[-1].id` for feature-based Intents (unchanged) and
  `body` for extras-only Intents (`features == []`, `extras` present).
  Degenerate Intents (`features == []` and no `extras`) raise
  `AdapterRefusal(where="export:empty")`. The adapter does **not** parse
  `extras` to verify it binds `body`; a missing binding surfaces as a
  `NameError` at execution → `error.json` (exit 12). Day 1 implements
  this; `02-data-model.md` § Adapter export contract is the spec.
- **Loop owns rendering** (resolved in the 2026-05-28 `/pm-architecture`
  touch — aligns `02-classes.md` with the C4 container view, which
  already drew `Loop --> Render`). The `Executor` is a pure subprocess
  manager (N6, N9) and does **not** import `render`; `ExecutionResult`
  carries no `renders` field. After `Executor.execute()` returns a valid
  `step_path`, the `Loop` calls `render.orthographic(step_path, run_dir)`
  as a separate step. No `RENDERING` state in the machine — rendering is
  a post-`EXECUTING` action inside the loop, not a transition.
- **Render failure is non-fatal (F7).** The loop wraps the
  `render.orthographic` call in a try/except; on failure the missing
  renders are marked in `status.json.artefacts` and the run still exits 0
  if the STEP is valid. STEP is the primary artefact; PNGs are a "should".
  Render failure never changes `ExecutionResult.exit_code` (which is
  execution-only) — the exit code stays 0.
- **Sanity is a visibility signal, never a gate** (ADR-0002 § Loop
  integration). The loop calls `sanity.check(...)` after the planner
  returns, logs one `DIMENSION_WARNING` per mismatch to `trace.jsonl`,
  appends to `status.json.warnings[]`, and **continues**. No `--no-sanity`
  flag in v0 (R11).
- **Single-pass loop in v0.** `RunConfig.max_iterations` defaults to 1.
  No `REFINING` state, no evaluator — that is phase-4 (v0.1). The v0
  state machine is linear: `PROMPT_RECEIVED → PLANNING → CODE_EMITTING →
  EXECUTING → DONE_OK | PLANNING_FAILED | ADAPTER_REFUSED | EXEC_FAILED |
  EXEC_TIMEOUT`.
- **Exit codes are recorded, not raised, in phase-2b.** The loop computes
  the F13 exit code (10 planner, 11 adapter, 12 executor, 13 timeout, 1
  generic, 0 success) and stamps it into `status.json.exit_code`. The
  process-level `sys.exit(code)` belongs to the CLI (phase-3). v0
  callers read the code from the returned run dir's `status.json`.
- **`Loop` is the only writer to `output/`** (N10). Executor and render
  write only *within* the run dir the loop hands them. Verified by the
  dependency-rule test.
- **Subprocess timeout + SIGKILL** (N9). `Executor` uses `subprocess.Popen`
  + `wait(timeout=timeout_s)`; on `TimeoutExpired` it sends `terminate()`,
  waits a 2 s grace, then `kill()` (SIGKILL). No zombie left behind.
- **prompts_hash** (ADR-0003). The loop computes the single rolled-up
  SHA-256 of `prompts/` contents and stamps `status.json.prompts_hash`.
  `PromptsBundle.hash` (empty since phase-2a) is filled here.
- **Testing strategy.** Loop + executor tested with a **mocked planner**
  (no live API in the default suite). The phase-2a `@pytest.mark.live`
  tests stay gated. Executor tests use real subprocesses against tiny
  hand-written build123d snippets (no LLM). Render tested against a
  committed fixture STEP. Headless assertion runs with `DISPLAY` unset.

## Minimum deliverable

Phase-2b ships when **all** of the following exist and pass their tests:

- **ADR-0004 export fix** in `src/maquette/adapters/build123d_target.py`:
  `_export(intent)` returns `export_step(features[-1].id, "part.step")`
  when `features` is non-empty; `export_step(body, "part.step")` when
  `features == []` and `extras` is present; raises
  `AdapterRefusal(where="export:empty")` when both are empty. A new
  snapshot fixture pair for an extras-only Intent (the L-bracket) under
  `tests/fixtures/adapters/build123d/l_bracket_extras/`; the 11 existing
  per-kind fixtures are unchanged (no snapshot churn).
- `src/maquette/render/orthographic.py` — `orthographic(step_path: Path,
  out_dir: Path) -> list[Path]`. Loads the STEP via OCP, renders three
  off-screen PyVista views (front/side/top) to `out_dir/renders/{front,
  side,top}.png`. Off-screen / headless (no `DISPLAY`). Raises on hard
  failure; the caller (the `Loop`) decides fatality. Pure w.r.t. inputs;
  the only side effect is writing PNGs into the given `out_dir`.
- `src/maquette/agent/executor.py` — `ExecutionResult` dataclass
  (`step_path: Path | None`, `error: str | None`, `exit_code: int`,
  `duration_s: float` — **no** `renders` field); `Executor`
  (`out_dir: Path`, `timeout_s: float`) with `execute(code_path: Path) ->
  ExecutionResult`. Spawns `python <code_path>` with `cwd=out_dir`,
  captures stdout/stderr, enforces the timeout + SIGKILL grace (N9),
  checks `part.step` exists and is > 0 bytes, and writes `error.json` on
  crash/timeout (N6) with a structured `{reason, stderr_tail, exit_code}`
  — never a raw traceback. Does **not** import `render`.
- `src/maquette/agent/loop.py` — `RunConfig` dataclass (`max_iterations=1`,
  `max_tokens_in`, `max_tokens_out`, `exec_timeout_s=30`, `model`,
  `sanity_enabled=True`); `Loop` (`out_root: Path`, `cfg: RunConfig`)
  with `run(prompt: str) -> Path`. Responsibilities:
    - Mints the run-id (`<UTC-ISO with - separators>__<intent.name
      slugified>`, F11) and creates `output/<run-id>/`.
    - Drives the linear state machine; writes `prompt.txt`, `intent.json`,
      `code.py`, `part.step`, `renders/`, `trace.jsonl`, `status.json`,
      and `error.json` (on failure) — the full F8 artefact set.
    - Calls `planner.plan` → `sanity.check` → `worker.emit_code` →
      `executor.execute`, mapping each failure to its F13 exit code
      recorded in `status.json.exit_code`. On a valid `step_path`, calls
      `render.orthographic(step_path, run_dir)` in a try/except (F7
      non-fatal); missing renders are marked in `artefacts`.
    - `trace.jsonl` (F10): one JSON object per line, one per state
      transition; per-LLM-call lines carry `tokens_in`, `tokens_out`,
      `cache_read_tokens`, `cache_creation_tokens`; sanity mismatches
      logged as `DIMENSION_WARNING`.
    - `status.json` (F9): `status`, `exit_code`, `started_at`,
      `finished_at`, `duration_s`, `iterations`, `tokens.{...}`,
      `cost_usd_estimate` (via `maquette.pricing.price`), `warnings[]`,
      `artefacts.{...}`, `prompts_hash` (ADR-0003).
- `[tool.importlinter]` extended with three new contracts:
    - `render` may import only `pyvista`, `ocp`/build123d STEP-load deps,
      `pathlib`, stdlib (no `maquette.*` except types it does not need).
    - `agent.executor` may import `subprocess`, `pathlib`, `json`, stdlib
      (no `render`, no planner/loop/adapters/intent_validation) — the
      executor is render-free per the 2026-05-28 architecture touch.
    - `agent.loop` may import `agent.planner`, `agent.sanity`,
      `agent.worker`, `agent.executor`, `maquette.intent`,
      `maquette.intent_validation`, `maquette.pricing`, `maquette.config`,
      `render`, stdlib.
- `[tool.coverage.report] include` extended for `render.orthographic`,
  `agent.executor`, `agent.loop`.
- Tests:
    - `tests/test_adapter_export.py` (ADR-0004): feature-based export
      unchanged; extras-only → `export_step(body`; degenerate →
      `AdapterRefusal(where="export:empty")`; L-bracket round-trip
      (emit → subprocess → `part.step` > 0 bytes).
    - `tests/test_render.py`: load the fixture STEP, render 3 views,
      assert 3 PNGs > 0 bytes; headless (no `DISPLAY`).
    - `tests/test_executor.py`: success (tiny box snippet → STEP > 0
      bytes, exit 0); crash (broken snippet → `error.json`, exit 12, no
      traceback on stdout); STEP-not-produced → exit 12. No render
      assertions — the executor is render-free.
    - `tests/test_loop.py` (mocked planner): full single-pass run on the
      cube-with-hole prompt produces the F8 artefact set *including* the
      three render PNGs (the loop drives `render.orthographic`);
      `status.json` validates the F9 field set; `trace.jsonl` has the
      expected transition sequence; a sanity mismatch surfaces as
      `DIMENSION_WARNING` + a `warnings[]` entry without changing
      `exit_code`; a forced render failure leaves the STEP intact, marks
      renders missing in `artefacts`, and still exits 0 (F7).

## Maximum deliverable

If everything above lands cleanly, also:

- **End-to-end integration test (mocked LLM)** — `tests/test_loop.py`
  asserts the *complete* artefact set and the full `trace.jsonl`
  transition sequence for one happy-path run, plus a planner-failure run
  (exit 10) and an adapter-refusal run (exit 11), each producing the
  right `status.json.exit_code` + `error.json`.
- **Per-step duration in `trace.jsonl`** — every transition event carries
  `duration_s` (planner from `PlanResult.duration_s`, executor from
  `ExecutionResult.duration_s`, render measured), feeding N1.
- **SIGKILL / N9 test** — an infinite-loop generated snippet is killed
  within `timeout_s` + 2 s grace; assert exit 13, `error.json` reason
  `"timeout"`, and no orphaned child process.
- **Live REPL exit-criterion run** — with a real `ANTHROPIC_API_KEY`,
  `Loop.run("a 50 mm cube with a 20 mm hole through the centre")`
  produces a complete `output/<run-id>/` from a Python REPL. Captured in
  the phase report (latency + cost noted, feeding N1/N2).

## Sprint / day breakdown

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | ADR-0004 export fix (carry-forward #1) | `_export` branches on `features`/`extras` per ADR-0004; `AdapterRefusal(where="export:empty")` on degenerate; new `l_bracket_extras` fixture pair; `tests/test_adapter_export.py` (feature-based unchanged, extras-only → `export_step(body`, degenerate → refusal, L-bracket round-trip emit→subprocess→STEP) | All 11 existing snapshot fixtures still pass byte-identical; extras-only L-bracket emits `export_step(body, "part.step")`; L-bracket round-trip produces `part.step` > 0 bytes; degenerate Intent raises `AdapterRefusal(where="export:empty")` |
| 2 | `render/orthographic.py` + import-linter contract | `orthographic(step_path, out_dir) -> list[Path]` (OCP STEP load → 3 off-screen PyVista views → `renders/{front,side,top}.png`); committed fixture STEP; `[tool.importlinter]` `render` contract; `tests/test_render.py` | 3 PNGs > 0 bytes from the fixture STEP with `DISPLAY` unset; `lint-imports` reports the new `render` contract kept |
| 3 | `agent/executor.py` + import-linter contract (N6, N9) | `ExecutionResult` dataclass (no `renders`); `Executor.execute(code_path)` (Popen + `cwd=out_dir`, timeout + 2 s SIGKILL grace, STEP > 0-byte check, `error.json` on crash/timeout); render-free; `[tool.importlinter]` `agent.executor` contract; `tests/test_executor.py` (success / crash→exit 12 / no-STEP→exit 12) | Tiny box snippet → STEP > 0 bytes, exit 0; broken snippet → `error.json` (structured, no traceback on stdout), exit 12; executor imports no PyVista; `lint-imports` keeps the executor contract |
| 4 | `agent/loop.py`: state machine + wiring + run-id + render + observability (F8, F9, F10, F11) + import-linter contract | `RunConfig`; `Loop.run(prompt)` mints run-id (F11), creates `output/<run-id>/`, drives planner→sanity→worker→executor, calls `render.orthographic` on a valid STEP (F7 non-fatal try/except), maps failures to F13 exit codes; `_write_trace` (one event/transition; per-LLM-call token fields; `DIMENSION_WARNING` on sanity mismatch), `_write_status` (full F9 set incl. `cost_usd_estimate` via `pricing`, `warnings[]`, `artefacts`, `prompts_hash` via ADR-0003 rolled-up SHA-256), `_write_error`; `[tool.importlinter]` `agent.loop` contract; `tests/test_loop.py` | A mocked-planner cube-with-hole run produces `output/<run-id>/` with the full F8 set incl. 3 render PNGs; run-id matches F11; `trace.jsonl` has the linear transition sequence with token counts; `status.json` validates the F9 fields with a non-zero `cost_usd_estimate` and the `prompts/` SHA-256; a sanity mismatch → `DIMENSION_WARNING` + `warnings[]` without changing `exit_code`; a forced planner failure → exit 10 + `error.json`; a forced render failure → STEP intact, renders marked missing, exit 0; `lint-imports` keeps the loop contract |
| 5 (MAX) | Integration test + per-step duration + SIGKILL (N9) + live REPL run | End-to-end mocked-LLM test asserting the full artefact set + happy/planner-fail/adapter-refuse exit codes; `duration_s` on every `trace.jsonl` event; infinite-loop SIGKILL test (exit 13, reason `timeout`, no orphan); one live `Loop.run(...)` from a REPL with a real key, results noted for the report | Integration test asserts the complete F8 artefact set + correct exit codes for the 3 paths; SIGKILL test kills within `timeout + 2 s`; live REPL run produces a complete `output/<run-id>/`; latency + cost recorded |

## Exit criteria

Phase-2b is `done` when **all** of the following hold:

1. `pyright src/` exits 0.
2. ADR-0004 fix verified: `worker.emit_code(<extras-only L-bracket Intent>)`
   contains `export_step(body, "part.step")`; the 11 per-kind snapshot
   fixtures remain byte-identical; a degenerate Intent raises
   `AdapterRefusal(where="export:empty")`.
3. `render.orthographic(<fixture STEP>, <tmp>)` writes three PNGs > 0
   bytes with `DISPLAY` unset (N5).
4. `Executor.execute(<crashing snippet>)` returns `exit_code == 12` with
   a structured `error.json` and no traceback on stdout (N6); a runaway
   snippet is killed within `timeout + 2 s` and returns `exit_code == 13`
   (N9).
5. `Loop.run("a 50 mm cube with a 20 mm hole through the centre")` with a
   real `ANTHROPIC_API_KEY` (from a REPL) produces a complete
   `output/<run-id>/` containing `prompt.txt`, `intent.json`, `code.py`,
   `part.step`, `renders/{front,side,top}.png`, `trace.jsonl`,
   `status.json` (F8); `status.json` carries the full F9 field set with a
   non-zero `cost_usd_estimate`; the run-id matches the F11 format.
6. `lint-imports` reports all contracts kept, 0 broken (6 from phase-2a +
   render + executor + loop = 9).
7. `pytest -q` passes; coverage on `render`, `agent.executor`,
   `agent.loop` ≥ 80% each.
8. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing
   (re-verified).
9. CI green on the most recent push to `main`.
10. `phases/phase-2b-report.md` exists (written via `/pm-phase-report`)
    capturing surprises, the live latency/cost numbers, and decisions.

## Known risks for this phase

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| P2b-R1 | The ADR-0004 fix changes `_export` and could perturb the 11 existing snapshot fixtures (e.g. trailing-newline diffs) | low | med | Day 1 first step: run the existing snapshot suite *before* touching `_export`; the branch for non-empty `features` must reproduce the current output byte-for-byte. Add the extras-only fixture as a *new* file, never edit the 11. |
| P2b-R2 | Extras-only generated code raises at execution because the LLM's `extras` build123d source doesn't compile (P2a-R9 carried forward) — the L-bracket geometry is non-trivial | med | med | This is exactly the `error.json` path (exit 12). Day 1's L-bracket round-trip uses the *known-good* extras from the phase-2a few-shot (verified live 2026-05-28), not a fresh LLM emission, so the adapter fix is tested deterministically. Real-LLM extras quality is a phase-3.5 concern. |
| P2b-R3 | PyVista headless / off-screen on nexus fails or needs system libs (VTK, OSMesa, Xvfb) — the classic "works locally, not on a server without a display" trap (N5) | high | med | Day 2 is isolated and first among the runtime modules so the friction surfaces early. If off-screen needs `pyvista.start_xvfb()` or `OSMesa`, document the system dep in README + `.env.example` notes. Render failure is non-fatal (F7), so worst case v0 ships STEP-only renders missing — but N5 is a hard requirement, so resolve it, don't skip it. |
| P2b-R4 | Subprocess timeout + SIGKILL leaves a zombie or the grace logic races (process exits during the 2 s grace) (N9) | med | med | Use `Popen` + `wait(timeout)`; on `TimeoutExpired` call `terminate()`, `wait(2)`, then `kill()` inside a `try/except`. The MAX SIGKILL test asserts no orphan via `psutil`/`os.waitpid`. Guard against the race by treating "already exited" as success in the grace window. |
| P2b-R5 | STEP capture path mismatch — generated code writes `part.step` to its CWD; if the subprocess CWD isn't the run dir, the loop can't find it | med | low | `Executor` sets `cwd=out_dir` on the subprocess. Test asserts `part.step` lands in `out_dir`, not the repo root. Document the convention (the adapter emits a bare `"part.step"` filename, relative to CWD). |
| P2b-R6 | `cost_usd_estimate` drifts from real cost if `status.json` sums token classes wrong, or if the SDK exposes a direct cost field that F9 says to prefer | low | low | Reuse `maquette.pricing.price(model, Tokens(...))` (phase-0, tested). F9 says "when the SDK exposes a cost field, use it as authoritative and fall back to local calc" — check `response.usage` for a cost field; if absent (current SDK), use `pricing`. One test asserts the calc against known token counts. |
| P2b-R7 | `trace.jsonl` / `status.json` schema invented here will be consumed by phase-3 CLI (`-v`), phase-6 `inspect`/`list`, phase-7c cost caps — a sloppy schema now is churn later | med | low | Field names come straight from F9/F10 (already specified). Keep the writers in one place (`Loop`), one helper per file, so a later schema bump is localized. Don't add speculative fields. |
| P2b-R8 | `Loop` accretes responsibility (state machine + 3 writers + run-id + cost + wiring) and becomes a god-object | med | low | The writers are private methods (`_write_trace`, `_write_status`, `_write_error`, `_new_run_dir`) per `02-classes.md`. State transitions are explicit. If `run()` exceeds ~80 lines, extract a `_RunState` helper — but don't pre-abstract (single-pass v0 is small). |
| P2b-R9 | The `Loop` success-path test (`test_loop.py`) drives real rendering, pulling PyVista/VTK into the loop test — heavy + potentially flaky if headless render is unavailable in CI | med | low | The render-in-executor coupling was removed (2026-05-28 architecture touch), so executor tests are now PyVista-free. The loop's render call is wrapped to monkeypatch `render.orthographic` for the failure-path + exit-code tests; only one loop test exercises real rendering and may be skipped where headless render is unavailable (N5 is verified by the dedicated `test_render.py` + the nexus smoke). |

## Notes for `/pm-phase-start`

When `/pm-phase-start` runs, the Auditor sub-agent should verify:

- Each delivered requirement has at least one task in the day breakdown:
  - F5 (Executor → STEP): Day 3.
  - F7 (Renderer → 3 PNGs): Day 2 (render module) + Day 4 (loop drives it, non-fatal).
  - F8 (run-folder artefact set): Day 4.
  - F9 (`status.json` + cost): Day 4.
  - F10 (`trace.jsonl`): Day 4.
  - F11 (run-id format): Day 4.
  - N6 (graceful failure): Day 3.
  - N9 (timeout + SIGKILL): Day 3 (enforcement) + Day 5 (MAX test).
  - N5 (headless): Day 2.
  - N10 (only-writer): Day 4 (dependency-rule test).
- The 2026-05-28 `/pm-architecture` touch moved rendering ownership from
  the `Executor` to the `Loop` (resolving a pre-existing contradiction
  between the C4 container view and `02-classes.md`). Audit should find
  `02-classes.md` module map, `ExecutionResult`, and the Loop class
  diagram all consistent on this (loop → render; executor render-free).
- ADR-0004 (export contract) is referenced from `_export`'s docstring and
  implemented Day 1; carry-forward #1 from `phase-2a-report.md` is closed.
- Carry-forward #2 (live API path) is **already discharged** — the live
  smoke ran 3/3 on 2026-05-28 (~12 s); no longer a phase-start blocker.
- Carry-forward #3 (`PromptsBundle.hash`) + #4 (`PlanResult.duration_s`)
  are consumed Day 5 / Day 6 respectively.
- N1 (latency) + N2 (cost) are *partially* delivered (per-step duration +
  `cost_usd_estimate`); the p95 / <$0.10 assertions land in phase-3.5.
- Glossary follow-up (`Build123dTarget`, `NxOpenTarget` leaves) remains a
  pre-phase-5 `/pm-architecture` pass; audit should **not** block on it
  (documented override pattern from phase-2a).
- The CLI (F1, F12, F13 process-exit, F14) is **out of scope** — phase-3.
  Audit should not expect a `cli.py` task here.

After audit passes, `/pm-phase-start` flips this file's `status: planned`
→ `status: in_progress`, sets `started: 2026-MM-DD`, and updates
[`03-roadmap.md`](../03-roadmap.md) frontmatter `active_phase: phase-2b`.
Scope-freeze applies from that point.
