# Handover — Maquette, between phase-2b (done) and phase-3 (not yet planned)

> *Start here in any fresh chat session that opens this project. Once
> phase-3 is planned + started, rewrite the "You are here" + task
> sections for it. Always keep this short enough to read in 60 seconds.*

## You are here

- **Project:** Maquette — natural-language CAD prompt → editable parametric solid + STEP.
- **Phase-2b is `done`** (closed 2026-05-28 via `/pm-phase-report`, min + max both met). See [`docs/phases/phase-2b-report.md`](docs/phases/phase-2b-report.md).
- **The v0 pipeline runs end-to-end.** A live `Loop.run("a 50 mm cube with a 20 mm hole through the centre")` produced a complete `output/<run-id>/` in 10.1 s for $0.0267 (under the N1 < 20 s / N2 < $0.10 targets).
- **No phase is active.** `docs/03-roadmap.md` frontmatter has `active_phase: null`. Scope freeze is **lifted** — design docs are editable again until the next `/pm-phase-start`.
- **Next move:** `/pm-phase-plan phase-3` (the CLI), then `/pm-phase-start phase-3`. No design-layer blocker is outstanding — carry-forward #1 (extras export) was closed this phase.
- **Last commit:** `08c88c5 style: wrap long _emit call in loop.py (CI ruff E501 fix)` on `main`, pushed. CI green ([run 26569865562](https://github.com/vandpaolo/maquette/actions/runs/26569865562)).
- **Doc-only changes pending commit:** the `/pm-phase-report` frontmatter flips + this handover + the report itself (see `git status`).

## Phases done so far

| Phase | Closed | min/max | Highlights |
|---|---|---|---|
| `phase-0` Foundations | 2026-05-17 | true/true | Intent schema + intent_validation + pricing + config; 68 tests; CI green |
| `phase-1` Adapter | 2026-05-18 | true/true | build123d adapter for all 11 v0 kinds; 3-reference round-trips; cube-with-hole STEP verified in NX |
| `phase-2a` Pipeline (LLM-facing) | 2026-05-28 | true/true | `agent.sanity` + `agent.planner` (prompt caching) + `agent.worker`; planner system prompt + 3 few-shots |
| `phase-2b` Pipeline (runtime) | 2026-05-28 | true/true | `agent.executor` + `render.orthographic` + `agent.loop`; ADR-0004 export fix; trace.jsonl + status.json; live E2E run |

149 tests passing (+ 4 live tests skipped by default). 9 import-linter contracts. CI green on every push to `main`.

## What phase-2b shipped (the runtime / orchestration half)

- [`src/maquette/agent/loop.py`](src/maquette/agent/loop.py) — `Loop.run(prompt) -> Path`. State machine (`PROMPT_RECEIVED → PLANNING → CODE_EMITTING → EXECUTING → DONE_OK | *_FAILED`), run-id (F11), `trace.jsonl` (F10, per-step `duration_s`), `status.json` (F9, cost via `pricing`, `prompts_hash` ADR-0003). The only writer of the `output/<run-id>/` layout. `RunConfig` lives here. Constructor: `Loop(out_root, cfg, client, prompts)`.
- [`src/maquette/agent/executor.py`](src/maquette/agent/executor.py) — `Executor(out_dir, timeout_s).execute(code_path) -> ExecutionResult`. Subprocess (`python -I`, `cwd=run dir`), timeout + SIGTERM→SIGKILL grace (N9), STEP capture, structured `error.json` (N6). Render-free. Exit codes 0/12/13.
- [`src/maquette/render/orthographic.py`](src/maquette/render/orthographic.py) — `orthographic(step_path, out_dir) -> list[Path]`. 3 off-screen PNGs via **vtk-osmesa** (N5). STEP→STL conversion runs in a subprocess (OCP/OSMesa GL isolation).
- [`src/maquette/adapters/build123d_target.py`](src/maquette/adapters/build123d_target.py) `_export` — ADR-0004 export contract (extras-only → `body`).
- [`docs/adr/0004-build123d-export-variable.md`](docs/adr/0004-build123d-export-variable.md) — the export-variable convention.

## Carry-forward — READ BEFORE PLANNING PHASE-3

**1. (env) Headless render requires `vtk-osmesa`, not stock `vtk`.** A
fresh `pip install -e .` pulls X11-only `vtk` and will segfault on
render. The swap (`pip uninstall -y vtk && pip install --extra-index-url
https://wheels.vtk.org vtk-osmesa==9.3.1`) is in CI + a pyproject
comment, **but not yet in the README** — phase-3 ships the README (F-CLI),
so document it there. See `notes/decisions.md` (2026-05-28) + the
[render-backend memory].

**2. (low) `prompts_hash` is sha256 of the bundle text**, not a true
`prompts/` directory roll-up. Fine for one prompt file; revisit
(ADR-0003 open decision #4) when a second prompt file lands (evaluator,
phase-4).

**3. (phase-3) The CLI wraps `Loop.run`.** It builds `config.Config`
(CLI > env > pyproject > defaults), derives `RunConfig`, constructs
`Anthropic()` + the `PromptsBundle` from `prompts/`, calls
`Loop.run(prompt)`, maps `status.json.exit_code` to the process exit
(F13), and prints the run dir on every exit (F12).

## Read in this order (under 10 minutes total)

1. `./CLAUDE.md` — project guide, framework reference, scope-freeze rule.
2. [`docs/phases/phase-2b-report.md`](docs/phases/phase-2b-report.md) — what just shipped, the 6 surprises, the 6 recommended changes feeding phase-3.
3. [`docs/03-roadmap.md`](docs/03-roadmap.md) § Phase 3 — the goal/min/max/exit stub you'll expand with `/pm-phase-plan`.
4. [`docs/02-classes.md`](docs/02-classes.md) § `cli` + § Pricing/Config — the phase-3 surface.
5. [`docs/01-requirements.md`](docs/01-requirements.md) F1, F12–F14 — CLI flags + exit-code table.

## Useful commands

```bash
# Current project state
~/.claude/skills/pm-status/status.sh .

# FULL local CI sequence (run ALL of these before pushing — READ ruff's
# real output; do not mask it behind `>/dev/null && echo OK`)
.venv/bin/ruff check src/ tests/
.venv/bin/ruff format --check src/ tests/
.venv/bin/pyright src/
.venv/bin/lint-imports
grep -rE "^(import NXOpen|from NXOpen)" src/   # must print nothing
.venv/bin/pytest -q                            # 149 passed, 4 deselected
.venv/bin/coverage run -m pytest -q && .venv/bin/coverage report

# Live tests (needs ANTHROPIC_API_KEY; .env at repo root, gitignored)
set -a; . ./.env; set +a; .venv/bin/pytest -m live

# Latest CI status
gh run list --limit 1
```

## When phase-3 is done

Run `/pm-phase-report`. Then `/pm-phase-plan phase-3.5` (smoke + 3
reference prompts verified manually in FreeCAD) and
`/pm-phase-start phase-3.5` — **v0 ships at the end of 3.5.**

## Carry-forward to revisit before phase-3.5

- **L-bracket end-to-end** is now unblocked (carry-forward #1 + the
  few-shot fix this phase). Phase-3.5 should still manually verify the
  L-bracket STEP opens in FreeCAD and visually matches the description.
- **N1 / N2 formal measurement** (p95 latency, cost-per-run) lands in
  phase-3.5; phase-2b's single live run (10.1 s, $0.0267) is indicative,
  not a p95.
