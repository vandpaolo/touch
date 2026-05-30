---
id: T1a
title: Engine rename + salvage + dev infra
status: in_progress
started: 2026-05-30
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T0]
---

# Phase T1a — Engine rename + salvage + dev infra

- **Goal:** Rename `src/maquette/` → `src/touch_backend/`; carry over the Maquette pipeline modules (planner, intent, intent_validation, adapter, pricing, config) so they pass their existing tests under the new namespace; SOPS-encrypt the dev `.env`; default the dev `out_root` to `/srv/touch/`. No new modules, no new behaviour — just the move.

- **Depends on:** T0 done ([phase-T0-report.md](phase-T0-report.md)); requirements F24 / F29 / F30 approved; architecture "engine reuse" decision (`03-roadmap.md` locked decision 2) + ADR import-contract layering.

- **Min:** Renamed package builds; the salvaged modules pass their existing pytest suite under `touch_backend.*`; `ruff check` / `ruff format --check` / `pyright` green; `lint-imports` updated with the new dependency rules and green; SOPS round-trip works (`sops -d` → working `.env`); `out_root` default is `/srv/touch/` on the dev host; the old `src/maquette/` tree is removed.

- **Max:** A CHANGELOG / migration note; CI workflow updated for the new package name; the existing `examples/` regenerated under the new entry point.

- **Exit criterion:** CI green on the renamed package end-to-end; SOPS `secrets.env.sops.yaml` checked into the repo and decrypts to a working dev env; the existing Maquette feature parity holds under the new namespace (the existing `maquette design` smoke tests pass as `touch_backend.cli design` or equivalent).

## Sprint / day breakdown

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 1 | **Move the package tree.** `git mv src/maquette → src/touch_backend`; rewrite all intra-package `import maquette` / `from maquette` references to `touch_backend`; update `pyproject.toml` (`name`, `packages = ["src/touch_backend"]`, and rename the `[project.scripts]` binary to `touch = "touch_backend.cli:app"`). | Renamed source tree; updated `pyproject.toml`. | `pip install -e .` succeeds; `python -c "import touch_backend"` works; the `touch` console script runs; `grep -r "maquette" src/` returns nothing (outside `spike/`). |
| 2 | **Fix the test suite + coverage config.** Rewrite all `tests/*` imports to `touch_backend`; update `[tool.coverage] source` + per-file `omit` paths. | Updated `tests/`, coverage config. | `pytest` (non-live) green; coverage runs against `touch_backend`. |
| 3 | **Rewrite import-linter contracts + green the full CI sequence.** Update `[tool.importlinter] root_package` and every contract from `maquette.*` → `touch_backend.*`. Run the full local CI gate. | Updated contracts. | `ruff check` + `ruff format --check` + `pyright` + `lint-imports` all green (see auto-memory `feedback_ci-checks`). |
| 4 | **SOPS-encrypt the dev `.env` (F29).** Create `.sops.yaml` keyed to the host age key; encrypt the current plaintext `.env` → `secrets.env.sops.yaml`; `.gitignore` the plaintext `.env`; add a pre-commit (or CI) guard that blocks a plaintext `.env` from being committed. | `secrets.env.sops.yaml`, `.sops.yaml`, `.gitignore` entry, commit guard. | `sops -d secrets.env.sops.yaml > .env` yields a working dev `.env`; no plaintext key in any committed file; guard rejects a staged plaintext `.env`. |
| 5 | **`out_root` → `/srv/touch/` on the dev host (F30) + final cleanup.** Keep the portable global default (`Path("output")` — the shipped app needs a per-user dir); set `/srv/touch/` as a **dev-host-only override** via `pyproject [tool.touch_backend]` (consumed by `_from_pyproject`) or env. Confirm `src/maquette/` is fully gone; verify exit criteria end-to-end. | Dev-host override; clean tree. | Running the backend locally writes under `/srv/touch/`; the dataclass default is unchanged; `src/maquette/` absent; exit criteria met. |
| Max | **Stretch.** Update the CI workflow for the new package name; write a CHANGELOG / migration note; regenerate `examples/` under the new entry point. | CI workflow, CHANGELOG, regenerated examples. | CI workflow references `touch_backend`; examples regenerate byte-clean. |

## Known risks for this phase

- **R-T1a-1 — `out_root` default vs. portability (F30).** Hardcoding `/srv/touch/` as the global dataclass default ([config.py:13,57](../../src/maquette/config.py)) would break the eventual shipped desktop app, which must write to a per-user dir. F30 scopes the requirement to *the dev host*. **Decided:** keep the portable default; set `/srv/touch/` via a dev-only override (pyproject `[tool.touch_backend]` or env).
- **R-T1a-2 — import-linter contract drift.** The contracts encode the intended module layering (`intent` → nothing, `intent_validation` → only `intent`, etc.). A mechanical find/replace can silently relax a contract if a module path is missed. Mitigation: diff the contract block before/after; confirm `lint-imports` still *fails* on a deliberately-introduced bad import, then revert the probe.
- **R-T1a-3 — stale entry-point / script name.** `[project.scripts] maquette = "maquette.cli:app"` and the `Documentation` URL reference the old name; CI and any docs that call `maquette design` will break. **Decided:** rename the console script to `touch` (`touch = "touch_backend.cli:app"`); the exit-criterion smoke flow runs as `touch design` / `python -m touch_backend.cli design`.
- **R-T1a-4 — coverage `omit`/`source` path rot.** `[tool.coverage]` hardcodes `src/maquette/...` file paths ([pyproject.toml:63–79]); missing one silently drops a file from coverage rather than erroring. Mitigation: run coverage and confirm the expected file count.
- **R-T1a-5 — SOPS host-key assumption.** F29's round-trip depends on the host age key (`~/.config/sops/age/keys.txt`, present). A fresh clone on another host can't decrypt. Acceptable for v0 (single dev host); note it in the migration doc.
