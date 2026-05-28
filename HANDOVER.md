# Handover — Maquette, between phase-3 (done) and phase-3.5 (not yet planned)

> *Start here in any fresh chat session that opens this project. Once
> phase-3.5 is planned + started, rewrite the "You are here" + task
> sections for it. Always keep this short enough to read in 60 seconds.*

## You are here

- **Project:** Maquette — natural-language CAD prompt → editable parametric solid + STEP.
- **Phase-3 is `done`** (closed 2026-05-28 via `/pm-phase-report`, min + max both met). See [`docs/phases/phase-3-report.md`](docs/phases/phase-3-report.md).
- **v0 is feature-complete.** The public CLI works end-to-end: `maquette design "a 50 mm cube with a 20 mm hole through the centre"` produces a complete `output/<run-id>/` and exits 0.
- **No phase is active.** `docs/03-roadmap.md` frontmatter has `active_phase: null`. Scope freeze is **lifted**.
- **Next move:** `/pm-phase-plan phase-3.5`, then `/pm-phase-start phase-3.5`. **Phase-3.5 is the last v0 phase — v0 ships at the end of it.** It is mostly *manual verification* (run the 3 reference prompts, open the STEPs in FreeCAD, confirm they match), plus latency/cost measurement.
- **Last commit:** see `git log -1` on `main` (pushed). CI green ([latest run](https://github.com/vandpaolo/maquette/actions)).
- **Doc-only changes pending commit:** the `/pm-phase-report` frontmatter flips + this handover + the report (see `git status`).

## Phases done so far

| Phase | Closed | min/max | Highlights |
|---|---|---|---|
| `phase-0` Foundations | 2026-05-17 | true/true | Intent schema + intent_validation + pricing + config; CI green |
| `phase-1` Adapter | 2026-05-18 | true/true | build123d adapter for all 11 v0 kinds; cube-with-hole STEP verified in NX |
| `phase-2a` Pipeline (LLM-facing) | 2026-05-28 | true/true | `agent.sanity` + `agent.planner` + `agent.worker`; planner prompt + few-shots |
| `phase-2b` Pipeline (runtime) | 2026-05-28 | true/true | `agent.executor` + `render.orthographic` + `agent.loop`; ADR-0004; trace/status; live E2E |
| `phase-3` CLI | 2026-05-28 | true/true | `maquette design` (Typer); loop API-error hardening; README; live E2E |

162 tests passing (+ 4 live, skipped by default). 10 import-linter contracts. CI green on every push to `main`.

## What phase-3 shipped (the CLI)

- [`src/maquette/cli.py`](src/maquette/cli.py) — `maquette design "<prompt>"`. Thin Typer shell over `Loop.run`: loads `.env`, maps flags (`--out`, `--max-iter`, `--exec-timeout`, `--model`, `-q`, `-v`) → `Config.load` → `RunConfig`, runs the loop, prints the run dir (F12), exits with the F13 code. `-v` logs per-LLM-call tokens to stderr; `-q` prints only the run dir.
- [`src/maquette/agent/loop.py`](src/maquette/agent/loop.py) `_plan` — now also catches `anthropic.AnthropicError` → exit 10 + complete run folder (P3-Q1).
- [`README.md`](README.md) — install (incl. the vtk-osmesa swap), `.env`, usage + flag table, exit-code table.
- `[project.scripts] maquette = "maquette.cli:app"`.

## Carry-forward — READ BEFORE PLANNING PHASE-3.5

**1. (verify) Run all 3 reference prompts via the CLI + open in FreeCAD.**
The v0 ship bar is *visual* correctness, not just a non-empty STEP. The
**L-bracket** is the one to watch — it exercises the extras path
(ADR-0004 export fix + the phase-2b few-shot fix). Confirm geometry
matches the description.

**2. (measure) N1 latency p95 + N2 cost/run.** Phase-2b's single live run
was 10.1 s / $0.0267 — indicative, not a p95. Phase-3.5 should record
latency + cost per prompt (roadmap MAX suggests ~10 runs/prompt).

**3. (env) Headless render still needs the `vtk-osmesa` swap** (carry from
phase-2b): a fresh `pip install -e .` pulls X11-only `vtk` and segfaults
on render. Documented in the README + CI; do the swap in any fresh env:
`pip uninstall -y vtk && pip install --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1`.

**4. (low) prompts/ packaging.** The CLI loads `prompts/planner.system.md`
via a repo-relative path (`parents[2]`) — fine for an editable clone (the
v0 distribution), not for a packaged install. Out of v0 scope.

## Read in this order (under 10 minutes total)

1. `./CLAUDE.md` — project guide, framework reference, scope-freeze rule.
2. [`docs/phases/phase-3-report.md`](docs/phases/phase-3-report.md) — what shipped, 5 surprises, 5 recommendations.
3. [`docs/03-roadmap.md`](docs/03-roadmap.md) § Phase 3.5 — the goal/min/max/exit stub to expand with `/pm-phase-plan`.
4. [`docs/00-vision.md`](docs/00-vision.md) § Success criteria — the v0 ship bar phase-3.5 verifies.

## Useful commands

```bash
# Current project state
~/.claude/skills/pm-status/status.sh .

# Run the CLI (needs the vtk-osmesa swap + a key; .env at repo root)
set -a; . ./.env; set +a
maquette design "a 50 mm cube with a 20 mm hole through the centre" --out /tmp/m

# FULL local CI sequence — READ ruff's real output (don't mask it);
# run CLI tests under COLUMNS=80 to mimic CI before pushing
.venv/bin/ruff check src/ tests/
.venv/bin/ruff format --check src/ tests/
.venv/bin/pyright src/
.venv/bin/lint-imports
grep -rE "^(import NXOpen|from NXOpen)" src/   # must print nothing
COLUMNS=80 .venv/bin/pytest -q                 # 162 passed, 4 deselected
.venv/bin/coverage run -m pytest -q && .venv/bin/coverage report

# Live tests (gated)
set -a; . ./.env; set +a; .venv/bin/pytest -m live

gh run list --limit 1
```

## When phase-3.5 is done

**v0 ships.** Run `/pm-phase-report`, then consider a v0 retrospective
(read all phase reports together). v0.1 begins at phase-4 (evaluator +
refinement loop).
