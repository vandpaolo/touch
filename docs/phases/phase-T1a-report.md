---
phase: T1a
title: Engine rename + salvage + dev infra
status: done
min_met: true
max_met: true
duration_planned_days: 5
duration_actual_days: 1
started: 2026-05-30
finished: 2026-05-30
---

# Phase T1a report — Engine rename + salvage + dev infra

Closed 2026-05-30, single session. The Maquette pipeline is resurrected
as Touch's headless backend under `touch_backend`, with SOPS dev secrets
and a `/srv/touch/` dev output root. No behaviour change — pure identity
+ infra. Delivers **F24, F29, F30**.

## What shipped

Against the planned sprint table:

| Day | Task | State | Evidence |
|-----|------|-------|----------|
| 1 | Move the package tree (`src/maquette` → `src/touch_backend`) | ✅ done | `7b1b14c`; `import touch_backend` + `touch-backend --help` OK |
| 2 | Fix the test suite + coverage config | ✅ done | `780b990`; 164 tests pass |
| 3 | Rewrite import-linter contracts + green full CI gate | ✅ done | `780b990`; 10 contracts kept, ruff/pyright/lint-imports green |
| 4 | SOPS-encrypt the dev `.env` + commit guard (F29) | ✅ done | `988268e`; round-trip MATCH, pre-commit + CI guard |
| 5 | `out_root` → `/srv/touch/` dev override + cleanup (F30) | ✅ done | `3fafc82`; resolves + write verified to `/srv/touch/` |
| Max | CHANGELOG / migration note; CI for new name; regen examples | ◑ partial-by-design | `2e824de` CHANGELOG done; other two N/A (see below) |

Concretely:
- **Package + CLI (F24):** `touch_backend` namespace; console script
  `touch-backend`; env prefix `TOUCH_BACKEND_*`; distribution name
  `touch-backend`. Old `src/maquette/` removed (git-mv, history kept).
- **Tooling:** `[tool.coverage]` + all 10 `[tool.importlinter]` contracts
  on `touch_backend`; full local gate green (ruff check + format,
  pyright 0, lint-imports 10/0, pytest 164, coverage 96%, NXOpen + new
  secrets guard).
- **Secrets (F29):** `secrets.env.sops.yaml` (age-encrypted), `.sops.yaml`,
  `.githooks/pre-commit` + CI guard, `Makefile` (`secrets-decrypt` /
  `-encrypt`, `hooks`, `ci`).
- **out_root (F30):** `/srv/touch/` on the dev host via
  `TOUCH_BACKEND_OUT_ROOT` in the gitignored `.env`; portable `./output`
  default preserved for CI + shipped app; `/srv/touch/` created (owned by
  `vandpaolo`) and a write verified.
- **Docs:** `CHANGELOG.md` migration note; plan scope-boundary section.

## What slipped (and why)

- **Two of three Max items were no-ops, not skipped:** "CI workflow
  updated for the new package name" was unnecessary — `ci.yml` is
  package-agnostic (`src/` + `pip install -e .`, no literal `maquette`);
  "regenerate examples" was N/A — `examples/` holds only a README, no
  generated artefacts. The one meaningful Max item (CHANGELOG) shipped.
  Hence `max_met: true`.
- **Repo-identity rename is deferred by design, not slipped:** local dir
  `maquette/` → `touch/`, GitHub repo + remote, `CLAUDE.md`/`README`/
  `HANDOVER`, pyproject `Documentation` URL. Split out as a deliberate
  standalone step before T1b (it needs a venv recreate, Claude Code
  memory-dir migration, and a VSCode reopen). Decision logged in
  `docs/notes/decisions.md` + plan "Scope boundary".

## Surprises

- **CLI name `touch` shadows GNU `/usr/bin/touch`** inside an active venv
  (venv bin precedes `/usr/bin`). Caught by testing on Day 1 → renamed
  the console script to `touch-backend`.
- **`pip install -e .` re-pulls X11 `vtk`** as a pyvista dep, shadowing
  the headless `vtk-osmesa` and hard-crashing the render tests
  (`Fatal Python error: Aborted`). Fixed the way CI does: `uninstall vtk`
  → force-reinstall `vtk-osmesa --no-deps`. A recurring dev-env gotcha.
- **SOPS creation rules match the encryption *input* path**, not the
  output. The first `.sops.yaml` keyed on `secrets.env.sops.yaml$` failed
  ("no matching creation rules"); the rule must match `.env`.
- **The lowercase rename sed missed the uppercase env prefix** `MAQUETTE_`
  in `config.py` + `test_config.py`. Renamed separately on Day 5.
- **`pyproject` is the wrong home for the dev `out_root`** — committed, it
  would leak `/srv/touch` into CI semantics. Used a `.env` env var
  instead (genuinely host-scoped).

## Decisions taken mid-phase

No `/pm-blocker` filed (no design decision proved wrong). In-phase
implementation decisions, all logged in `docs/notes/decisions.md`:
- Console script → `touch-backend` (not `touch`).
- Dev `out_root` via `TOUCH_BACKEND_OUT_ROOT` in `.env` (not pyproject).
- Env prefix `MAQUETTE_` → `TOUCH_BACKEND_`.
- Rename-cascade split: T1a = code/tooling identity; repo identity is a
  separate pre-T1b step; historical Maquette docs never renamed.

## Recommended changes for next phase

1. **Do the repo-identity rename first** (the deferred standalone step),
   before starting T1b — while a clean break is cheap. Includes the venv
   recreate + memory-dir migration + VSCode reopen.
2. **Resolve the executor process-model TBD** (`02-classes.md:331`, flagged
   FAIL #7 in the pre-T1a audit) when T1b plans the server/executor —
   record the T0 spike's outcome in `decisions.md`.
3. **Carry the two unfixed audit FAILs forward:** annotate the Maquette-era
   `constraints.md` "absorbed" marker (#8); standardize phase-report
   frontmatter keys `min_met`/`max_met` vs `min_goal_met`/`max_goal_met`
   (#9). Both are doc hygiene, neither blocks T1b.
