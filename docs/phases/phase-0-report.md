---
phase: phase-0
status: done
min_met: true
max_met: true
duration_planned_days: 4
duration_actual_days: 1
---

# Phase 0 — Foundations — Report

> *Closed out via `/pm-phase-report` on 2026-05-17. Phase ran
> 2026-05-16 → 2026-05-17. Plan: [`phase-0.md`](phase-0.md). Audit:
> [`../audits/2026-05-16-pre-phase-0.md`](../audits/2026-05-16-pre-phase-0.md).*

## What shipped

| Sprint day | Status | Artefacts |
|---|---|---|
| Day 1 — Repo skeleton | done | [`pyproject.toml`](../../pyproject.toml), [`LICENSE`](../../LICENSE), [`.gitignore`](../../.gitignore), [`.env.example`](../../.env.example), [`README.md`](../../README.md), empty `src/maquette/{__init__,agent,adapters,render}` + `tests/__init__.py`. Commit `f932d2a`. |
| Day 2 — Domain model | done | [`src/maquette/intent.py`](../../src/maquette/intent.py), [`src/maquette/intent_validation.py`](../../src/maquette/intent_validation.py), [`tests/test_intent.py`](../../tests/test_intent.py) (14 tests), [`tests/test_intent_validation.py`](../../tests/test_intent_validation.py) (28 tests — positive + negative for each of the 11 kinds). Commit `edf6976`. |
| Day 3 — Pricing + config | done | [`src/maquette/pricing.py`](../../src/maquette/pricing.py) (`Tokens`, `ModelPrice`, three-model `_TABLE` from ADR 0003, `price()`), [`src/maquette/config.py`](../../src/maquette/config.py) (`Config` + `load()` with full precedence), [`tests/test_pricing.py`](../../tests/test_pricing.py) (11 tests), [`tests/test_config.py`](../../tests/test_config.py) (15 tests). Commit `5e7ee63`. |
| Day 4 — CI + tooling | done | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), `[tool.importlinter]` in pyproject (two contracts), `[tool.ruff]` in pyproject, [`pyrightconfig.json`](../../pyrightconfig.json), [`examples/README.md`](../../examples/README.md). Commit `5f8c1e1`. CI green on first push ([run 25995136684](https://github.com/vandpaolo/maquette/actions/runs/25995136684), 55 s). |
| MAX — pre-commit | done | [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) (gitleaks + local NX-grep hook). `pre-commit run --all-files` passes locally. Committed alongside Day 4. |

**Exit criteria** — all ten met:

1. `pip install -e .[dev]` succeeds on fresh Python 3.12 venv — verified.
2. 68 tests pass (target ≥ 20); `coverage` on `intent` + `intent_validation` = **97 %** (target ≥ 80 %).
3. `ruff check src/ tests/` exits 0.
4. `ruff format --check src/ tests/` exits 0.
5. `pyright src/` at `basic` mode exits 0.
6. `lint-imports` — 2 contracts kept, 0 broken.
7. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing.
8. CI on GitHub Actions green on the most recent push to `main` (run 25995136684).
9. `pricing.price(...)` returns a non-zero float for all three documented models.
10. This report exists.

## What slipped

Nothing. Min + Max both met; no exit criterion deferred; no scope dropped.

## Surprises

1. **`git init` was not in the Day 1 spec** but was needed for Day 4's "CI green on first push" criterion. Caught proactively at the start of Day 1; not a blocker.
2. **Speculative `[project.scripts] maquette = "maquette.cli:app"` entry** in the initial pyproject pointed at `cli.py` which is a later-phase module. A dangling entry point installs fine but breaks `maquette` on invocation — removed before commit. The CLI will wire it back when `cli.py` actually lands.
3. **Config defaults were not enumerated** in any design doc. Picked: `out_root=Path("output")`, `max_iterations=1`, `exec_timeout_s=30.0` (per N9), `model="claude-opus-4-7"` (per ADR 0003 default), `verbosity=0`, `sanity_enabled=True` (F6 in v0 scope). Defensible from architecture/NFR context; recorded here for future audit.
4. **`loft.sections` doesn't fit `params: dict[str, float | str]`.** The data model specifies a list of profiles for loft, but the params type is a flat dict of scalars. Resolved inside scope-freeze by storing the section list as a single comma-separated string and having the contract checker validate presence only; adapter (phase-1) will parse. Candidate for a follow-up if it bites in phase-1.
5. **`pyright --pythonpath` flag was needed for CI portability.** Locally `pyrightconfig.json` uses `venvPath: "."` / `venv: ".venv"`; CI has no `.venv` at that path, so the workflow passes `--pythonpath "$(which python)"` explicitly. Two-track configuration (local convenience + CI portability) — minor but unobvious.
6. **GitHub OAuth `workflow` scope was missing** at first push attempt — `gh auth refresh -h github.com -s workflow` resolved it. One-time setup friction; documented here so a future fresh-clone author isn't surprised.
7. **GitHub Actions Node.js 20 deprecation warning** surfaced on the first CI run. `actions/checkout@v4` and `actions/setup-python@v5` are flagged for forced upgrade on **2026-06-02** (~16 days from phase close). Non-blocking, but should be folded into phase-1 work to avoid surprise CI changes later. See *Recommended changes* below.
8. **Plan estimated 4 sprint days; actual = 1 work day** (one concentrated session on 2026-05-17). Phase-0 was lighter-touch than the day-count implied because the four sprint "days" had almost no inter-day dependencies — each was a self-contained file set. By convention this report records `duration_actual_days = 1` (work days, not calendar days); future phase reports should follow the same convention. Worth noting for sizing phase-1, where dependencies between adapter / executor / loop will be richer and a single-session sprint is less plausible.

## Decisions taken mid-phase

No blockers filed. No design pivots required. The only judgment calls were inside-spec implementation choices, captured in *Surprises* above for audit visibility.

## Recommended changes for next phase

1. **Bump GitHub Actions to Node 24-compatible versions.** Update `.github/workflows/ci.yml` early in phase-1 to `actions/checkout@v5` (or `@v6` when out) and `actions/setup-python@v6`. Cheap fix, eliminates the deprecation notice. Add as the first task in phase-1's sprint table.
2. **Watch `loft.sections` representation.** When the build123d adapter starts on phase-1, the comma-separated-string fallback may need rethinking — file a `/pm-blocker` if it forces ambiguity rather than papering over it in the adapter.
3. **Phase-1 entry includes wiring the dangling pieces:** the eventual `cli.py` entry point should re-add `[project.scripts] maquette = "maquette.cli:app"` to `pyproject.toml`. (Phase-1's plan is the Adapter, not CLI — but flag this for whichever phase introduces `cli.py`.)
4. **Coverage filter is currently hand-listed in CI.** As `agent.*` modules land in phase-1+, the `--include=` argument will grow. Consider moving to `[tool.coverage.run] source = ...` in `pyproject.toml` once there are more than two modules to track, so the CI step stays one line.
5. **Pre-commit is not yet `install`-ed by default.** The MAX deliverable shipped the config but didn't run `pre-commit install` (which would be a per-clone action). Worth a single line in the README install steps once the doc grows beyond a skeleton.
6. **No deferred technical debt.** Every shortcut taken in phase-0 is either documented in *Surprises* above or has an explicit follow-up in this list. Nothing carried silently.
