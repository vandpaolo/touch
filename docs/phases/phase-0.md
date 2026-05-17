---
id: phase-0
title: Foundations
status: in_progress        # planned | in_progress | blocked | done — flipped 2026-05-16 via /pm-phase-start
started: 2026-05-16        # ISO date when flipped to in_progress
finished: null             # ISO date when flipped to done
min_goal_met: null         # true | false | null
max_goal_met: null         # true | false | null
blocker: null              # path to blocker doc if status = blocked
depends_on: []             # phase-0 has no prerequisites
audit: audits/2026-05-16-pre-phase-0.md
---

# Phase 0 — Foundations

> *Drafted via `/pm-phase-plan` on 2026-05-16. Update via `/pm-phase-plan`
> before `/pm-phase-start`; once `in_progress`, scope is frozen.*

- **Goal:** Project scaffolded; the domain model (`intent` +
  `intent_validation`), pricing table, and config layer exist and are
  tested; CI runs ruff + pytest + import-linter + NX-grep guard on
  every push.
- **Depends on:** nothing (this is the first phase).
- **Estimated duration:** 4 days.

## Policies locked for this phase

- **Python version pin:** `requires-python = ">=3.12,<3.13"` (per gap G1).
- **Dependency pinning strategy (per gap G2):** *hybrid*.
  - **Strict** (`==X.Y.Z`) on snapshot-sensitive runtime deps: `build123d`.
  - **Compatible** (`~=X.Y.0`) on the rest: `anthropic`, `pydantic>=2`,
    `pyvista`, `typer`, `python-dotenv`.
  - **Compatible** on all dev deps: `pytest`, `ruff`, `import-linter`,
    `pyright`, `coverage`.
- **Type checker (per probe P3):** *pyright*. Phase 0 ships the dep +
  a minimal `pyrightconfig.json`; first real Protocol-conformance check
  runs against Phase 1's adapter.
- **Coverage baseline (per push-back B1):** *soft* target ≥80% on
  `maquette.intent` + `maquette.intent_validation`. Tracked in CI via
  `coverage` + reported; **not gating** (a drop doesn't fail the build).
- **Testing discipline (per push-back B2):** *pragmatic test-along*, not
  strict TDD. Working rule: no commit lands `src/` changes without an
  accompanying test in `tests/` covering the new public surface. The
  ≥80% coverage gate is the long-term backstop; the per-commit rule is
  the immediate discipline. Strict red→green→refactor isn't enforced —
  solo + multi-month projects tend to slip out of it, which the user
  flagged. Test-along is more sustainable.

## Minimum deliverable

Phase 0 ships when **all** of the following exist and pass their tests:

- `pyproject.toml` per the pinning policy above (runtime + dev deps;
  `requires-python = ">=3.12,<3.13"`).
- `src/maquette/intent.py` — full Intent schema (pure declarative
  pydantic types + the `validate_references` `@model_validator` per
  decision B3).
- `src/maquette/intent_validation.py` — `validate_kind_contracts(intent)`
  + `ContractViolation` (per-kind param checks, per ADR 0001 and the v0
  schema in 02-data-model.md).
- `src/maquette/pricing.py` — `Tokens`, `ModelPrice` dataclasses, the
  three-model price table with the verified Anthropic values from
  ADR 0003, and `price(model, tokens) → float`.
- `src/maquette/config.py` — `Config` dataclass + `load(cli_overrides)`
  enforcing the CLI > env > pyproject > defaults precedence (per the
  architecture doc § Cross-cutting / Configuration).
- `tests/test_intent.py`, `tests/test_intent_validation.py`,
  `tests/test_pricing.py`, `tests/test_config.py` — ≥20 tests total,
  all passing, with `coverage` reporting ≥80% on `intent` +
  `intent_validation`.
- `LICENSE` (MIT, per gap G3 decision).
- `README.md` (skeleton) with install steps, the v0 usage example, and
  a pointer to `docs/`. (Promoted from MAX per probe P1.)
- `.env.example` (`ANTHROPIC_API_KEY=sk-...`). (Promoted from MAX per
  probe P1.)
- `examples/README.md` placeholder noting "regression cases land in
  Phase 4 / Phase 7b; format = `output/<run-id>/` minus `trace.jsonl`
  + `status.json`". (Promoted from MAX per probe P2.)
- `pyrightconfig.json` (minimal: `include: ["src"]`,
  `pythonVersion: "3.12"`, `typeCheckingMode: "basic"`).
- `.github/workflows/ci.yml` running on every push: `ruff check`,
  `ruff format --check`, `pytest`, `coverage report`, `pyright`,
  `lint-imports`, and the NX-grep guard
  `! grep -rE "^(import NXOpen|from NXOpen)" src/`.
- `.gitignore` covering `output/`, `.env`, `__pycache__/`, `.venv/`,
  `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`.

## Maximum deliverable

If everything above lands cleanly, also:

- `.pre-commit-config.yaml` with `gitleaks` (secret scan) and a local
  hook running the same NX-grep guard (local-side reinforcement of the
  CI rule per probe P5).

## Sprint / day breakdown

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Repo skeleton, dep pinning, license, gitignore, env example, README skeleton, package layout | `pyproject.toml` (`requires-python=">=3.12,<3.13"`, hybrid-pinned runtime + dev deps including `pyright` and `coverage`); `LICENSE` (MIT); `.gitignore`; `.env.example`; `README.md` (skeleton: install + v0 usage example + pointer to `docs/`); empty `src/maquette/{__init__.py, agent/__init__.py, adapters/__init__.py, render/__init__.py}`; `tests/__init__.py` | `pip install -e .[dev]` succeeds in a fresh Python 3.12 venv; `python -c "import maquette"` exits 0; `pytest` collects 0 tests cleanly; `README.md` renders on GitHub preview |
| 2 | Domain model — types + cross-reference + per-kind contracts | `src/maquette/intent.py` (Unit, PrimaryKind, ModifierKind enums; Parameter, PrimaryFeature, Modifier, Intent classes; `validate_references` @model_validator); `src/maquette/intent_validation.py` (`ContractViolation` + `validate_kind_contracts(intent) → list[ContractViolation]`); `tests/test_intent.py`; `tests/test_intent_validation.py` | ≥15 tests pass; pydantic edge cases covered (invalid unit, duplicate feature/modifier ids, dangling modifier target); per-kind contract tests cover all 11 kinds (positive + at least one negative per kind) |
| 3 | Pricing + config | `src/maquette/pricing.py` (`Tokens`, `ModelPrice` dataclasses; `_TABLE` with Opus 4.7 / Sonnet 4.6 / Haiku 4.5 four-class prices from ADR 0003; `price(model, tokens) → float`); `src/maquette/config.py` (`Config` dataclass + `load(cli_overrides: dict) → Config`); `tests/test_pricing.py`; `tests/test_config.py` | `pricing.price("claude-opus-4-7", Tokens(input=1000, output=500, cache_read=0, cache_creation=0))` returns ≈ $0.0175; `pricing.price` per-model rounding/precision tests pass; `config.load({})` returns defaults; precedence verified (CLI override beats env beats pyproject beats default) |
| 4 | CI workflow + import-linter + pyright config + examples stub + (MAX) pre-commit | `.github/workflows/ci.yml` (ruff + pytest + coverage + pyright + import-linter + NX-grep guard); `pyproject.toml [tool.importlinter]` contracts (intent has no project deps; intent_validation depends only on intent); `pyrightconfig.json` (minimal); `examples/README.md` (placeholder); (MAX) `.pre-commit-config.yaml`; first push → verify CI green | CI workflow runs and is green on the first push to `main`; `lint-imports` exits 0; `pyright src/` exits 0 (no errors); `coverage report` shows ≥80% on `intent` + `intent_validation`; `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing; pytest, ruff check, ruff format-check all exit 0 in CI; (MAX) `pre-commit run --all-files` passes locally |

## Exit criteria

Phase 0 is `done` when **all** of the following hold:

1. `pip install -e .[dev]` succeeds on a fresh Python 3.12 venv.
2. ≥20 tests pass across `tests/test_intent.py`,
   `tests/test_intent_validation.py`, `tests/test_pricing.py`,
   `tests/test_config.py`; `coverage report --include="src/maquette/intent*.py"`
   shows ≥80% (soft target — drop does not fail CI but is visible).
3. `ruff check src/ tests/` exits 0.
4. `ruff format --check src/ tests/` exits 0.
5. `pyright src/` exits 0 (no type errors at `basic` mode).
6. `lint-imports` (import-linter) reports zero contract violations.
7. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing.
8. CI workflow on GitHub runs green on the most recent push to `main`.
9. `pricing.price(model, Tokens(...))` returns a non-zero float for all
   three documented models.
10. `phases/phase-0-report.md` exists (written via `/pm-phase-report`)
    capturing what shipped, what slipped, and any surprises.

## Known risks for this phase

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| P0-R1 | build123d / OCP / PyVista install on Linux is heavy (large OCP wheel) and can fail on certain Python versions | med | med | Pin to a verified-working version in `pyproject.toml`; document any install issues in `README.md` install section; nexus has all three working — pin the same versions |
| P0-R2 | import-linter contract syntax may take iteration (rules sometimes catch the wrong thing) | med | low | Start with the load-bearing contract only (`intent` has zero project deps); add `intent_validation` and other rules incrementally in later phases as modules land |
| P0-R3 | GitHub Actions workflow can be finicky on first attempt (cache config, Python version pin, dep install on CI's Ubuntu) | med | low | Keep workflow minimal (install + 4 commands, no matrix, no cache initially); iterate if first push is red |
| P0-R4 | Pydantic v2 has different `model_validator` semantics than v1 | low | med | Pin `pydantic>=2` in `pyproject.toml`; reference pydantic v2 docs in `intent.py` comments where the validator is defined |
| P0-R5 | The verified Anthropic prices (ADR 0003) may have changed between roadmap-time (2026-05-16) and code-time | low | low | First run with real API: compare `status.json.cost_usd_estimate` against the actual invoice line item; update `pricing._TABLE` if drift detected; file a "prices verified" note in the phase-0 report |

## Notes for `/pm-phase-start`

When `/pm-phase-start` runs, the Auditor sub-agent should verify:

- Every functional requirement covered by Phase 0 (F-prefixed) maps to
  at least one task above. **Phase 0 implements no F-numbered functional
  requirements directly** — Phase 0 is foundation work; F1 onwards land
  starting in Phase 1 (Adapter) and Phase 2a/2b (Pipeline). The audit
  should flag this and confirm it's expected.
- NFRs N3 (adapter determinism), N4 (NX hygiene), N8 (secret hygiene)
  have at least one task contributing to them in Phase 0. (N4 via CI
  grep guard + import-linter; N8 via `.gitignore` + `.env.example`; N3
  has no implementation yet — that lands in Phase 1.)
- ADRs 0001, 0002, 0003 are linked from `02-architecture.md` and
  exist as files (they do).
- The `LICENSE` file appears in the Min deliverable.
- The `.github/workflows/ci.yml` task appears in the Min deliverable.

After audit passes, `/pm-phase-start` flips this file's
`status: planned` → `status: in_progress`, sets `started: 2026-MM-DD`,
and updates `03-roadmap.md` frontmatter `active_phase: phase-0` (already
set). From that moment, the scope-freeze rule applies: no requirement
or architecture edits without filing `/pm-blocker` first.
