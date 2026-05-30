---
id: T1a
title: Engine rename + salvage + dev infra
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T0]
---

# Phase T1a — Engine rename + salvage + dev infra

- **Goal:** Rename `src/maquette/` → `src/touch_backend/`; carry over the Maquette pipeline modules (planner, intent, intent_validation, adapter, pricing, config) so they pass their existing tests under the new namespace; SOPS-encrypt the dev `.env`; default the dev `out_root` to `/srv/touch/`. No new modules, no new behaviour — just the move.
- **Min:** Renamed package builds; the salvaged modules pass their existing pytest suite under `touch_backend.*`; `ruff check` / `ruff format --check` / `pyright` green; `lint-imports` updated with the new dependency rules and green; SOPS round-trip works (`sops -d` → working `.env`); `out_root` default is `/srv/touch/` on the dev host; the old `src/maquette/` tree is removed.
- **Max:** A CHANGELOG / migration note; CI workflow updated for the new package name; the existing `examples/` regenerated under the new entry point.
- **Exit criterion:** CI green on the renamed package end-to-end; SOPS `secrets.env.sops.yaml` checked into the repo and decrypts to a working dev env; the existing Maquette feature parity holds under the new namespace.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
