# Handover — Maquette, phase-0 day 1

> *Start here in any fresh chat session that opens this project. Once
> phase-0 is `done`, rewrite this file for phase-1. Always keep it short
> enough to read in 60 seconds.*

## You are here

- **Project:** Maquette — natural-language CAD prompt → editable parametric solid + STEP.
- **Active phase:** `phase-0` — Foundations. Status: `in_progress`, started 2026-05-16.
- **Audit:** `docs/audits/2026-05-16-pre-phase-0.md` (PASS, after 4 mechanical fixes).
- **Scope is frozen.** No edits to `docs/00-*`, `docs/01-*`, `docs/02-*`, `docs/03-*`, or `docs/adr/` without filing `/pm-blocker` first. Implementation only.

## Read in this order (under 10 minutes total)

1. `./CLAUDE.md` — project guide, framework reference.
2. `docs/phases/phase-0.md` — your phase plan: policies locked, MIN/MAX, day breakdown, exit criteria. This is your day-by-day spec.
3. `docs/02-data-model.md` — the Intent schema. You're implementing this in Day 2 (`src/maquette/intent.py`).
4. `docs/02-classes.md` § Module map + § Class diagrams — concrete class shapes and signatures you'll write.
5. `docs/adr/0003-prompt-caching-for-cost.md` § Context — the verified Anthropic prices that go into `pricing.py` on Day 3.

## Policies locked for phase-0 (do not deviate without `/pm-blocker`)

- **Python:** `requires-python = ">=3.12,<3.13"`
- **Pinning:** strict (`==`) on `build123d`; compatible (`~=X.Y.0`) on `anthropic`, `pydantic>=2`, `pyvista`, `typer`, `python-dotenv`, and all dev deps
- **Type checker:** pyright (`typeCheckingMode: "basic"`)
- **Coverage:** soft target ≥80% on `maquette.intent` + `maquette.intent_validation` (tracked in CI, not gating)
- **Testing discipline:** pragmatic test-along — *no commit lands a `src/` change without an accompanying test for the new public surface*

## Day 1 — your current task

Repo skeleton, pinned deps, license, gitignore, env example, README skeleton, package layout.

**Outputs:**
- `pyproject.toml` per pinning policy above
- `LICENSE` (MIT)
- `.gitignore` (`output/`, `.env`, `__pycache__/`, `.venv/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`)
- `.env.example` (`ANTHROPIC_API_KEY=sk-...`)
- `README.md` skeleton (install + the v0 usage example from `docs/00-vision.md` § Success criteria + pointer to `docs/`)
- Empty `src/maquette/{__init__.py, agent/__init__.py, adapters/__init__.py, render/__init__.py}` + `tests/__init__.py`

**Done when:**
- `pip install -e .[dev]` succeeds in a fresh Python 3.12 venv
- `python -c "import maquette"` exits 0
- `pytest` collects 0 tests cleanly
- `README.md` renders on GitHub preview

## After Day 1

| Day | Task | Lives in |
|-----|------|----------|
| 2 | Intent schema (types) + intent_validation (per-kind contracts) + tests for both | `src/maquette/intent.py`, `intent_validation.py`, `tests/test_intent.py`, `test_intent_validation.py` |
| 3 | Pricing table (4 token classes, prices from ADR 0003) + Config (CLI > env > pyproject > defaults) + tests | `src/maquette/pricing.py`, `config.py`, `tests/test_pricing.py`, `test_config.py` |
| 4 | GitHub Actions CI + import-linter contracts + pyrightconfig.json + `examples/README.md` + (MAX) pre-commit hooks | `.github/workflows/ci.yml`, `pyproject.toml [tool.importlinter]`, `pyrightconfig.json`, `examples/README.md`, `.pre-commit-config.yaml` |

Full exit criteria are in [docs/phases/phase-0.md § Exit criteria](docs/phases/phase-0.md).

## If you hit a design gap

**Do not modify design docs.** Run `/pm-blocker` and describe the gap. The blocker doc forces a re-design round before implementation continues. The whole point of the framework is that scope is frozen during implementation — design pivots happen explicitly, not silently mid-code.

## Useful commands

```bash
# Current project state
~/.claude/skills/pm-status/status.sh .

# After Day 4: CI should be green
gh run list --limit 1

# Run the audit again if you change anything design-adjacent (you shouldn't)
# (no skill file yet — would run the audit sub-agent manually)
```

## When phase-0 is done

Run `/pm-phase-report` — close out, capture what shipped / what slipped / surprises, flip status to `done`. Then `/pm-phase-plan phase-1` to detail the next phase (Adapter), and `/pm-phase-start phase-1` to greenlight.
