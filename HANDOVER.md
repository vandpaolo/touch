# Handover — Maquette, v0 SHIPPED (between phase-3.5 done and phase-4 / v0.1)

> *Start here in any fresh chat session that opens this project. Once
> phase-4 is planned + started, rewrite the "You are here" + task
> sections for it. Keep this short enough to read in 60 seconds.*

## You are here

- **Project:** Maquette — natural-language CAD prompt → editable parametric solid + STEP.
- **🎉 v0 is SHIPPED** (phase-3.5 closed 2026-05-29 via `/pm-phase-report`, min met / max deferred). See [`docs/phases/phase-3.5-report.md`](docs/phases/phase-3.5-report.md).
- **The v0 success criterion holds:** the two hard-gate references run end-to-end via `maquette design`, open in FreeCAD, and visually match, within 20 s / $0.10 — human-verified. The L-bracket (bare L-shape) showcases the `extras` relief valve.
- **No phase is active.** `docs/03-roadmap.md`: `active_phase: null`, `project_status: building` (v0 milestone shipped; v0.1/v0.2 remain).
- **Next move:** v0.1 begins at **phase-4 (Evaluator + refinement loop)** — `/pm-phase-plan phase-4`, then `/pm-phase-start phase-4`. **Read carry-forward below first.**
- **Last commit:** `350ee81` (blocker resolution) pushed; the phase-3.5 close-out commit is local until pushed. CI green.

## Phases done so far (v0 complete)

| Phase | Closed | min/max | Highlights |
|---|---|---|---|
| `phase-0` Foundations | 2026-05-17 | true/true | Intent schema + intent_validation + pricing + config |
| `phase-1` Adapter | 2026-05-18 | true/true | build123d adapter for all 11 v0 kinds |
| `phase-2a` Pipeline (LLM-facing) | 2026-05-28 | true/true | planner + sanity + worker; prompt + few-shots |
| `phase-2b` Pipeline (runtime) | 2026-05-28 | true/true | executor + render + loop; ADR-0004; trace/status |
| `phase-3` CLI | 2026-05-28 | true/true | `maquette design`; loop API-error hardening |
| `phase-3.5` Smoke + examples | 2026-05-29 | true/false | **v0 shipped** — gate refs FreeCAD-verified; 2 blockers + 3 bugs caught & fixed |

~165 tests passing (+ 4 live, skipped by default). 10 import-linter contracts. CI green on every push to `main`.

## Carry-forward — READ BEFORE PLANNING PHASE-4 / v0.1

**1. v0.1 ordering was re-sequenced (phase-3.5 blocker re-design).** v0.1
now leads with **phase-4 (Evaluator + refine loop)** — the correctness
guard that auto-catches silent-wrong geometry (R7) — then **phase-4.5
(Schema v2a: edge selection + hole positioning)**, pulled forward from
phase-10 to make "chamfer the top edge" / "hole in each flange" work
natively instead of via fragile `extras`. See `docs/03-roadmap.md`.

**2. Deferred MAX work from phase-3.5** (cheap, fold into v0.1): a live
smoke test (`pytest -m live`, 2 gate refs), a p95 latency script, and the
curated `examples/` corpus (cube/cylinder/L-shape runs captured under
`output/v0ship/` seed it — the corpus is the phase-4 / phase-7b deliverable).

**3. `extras` is best-effort and un-guarded in v0** — it reliably makes
compound *shapes* (the L) but not precise *features* (holes, edge-specific
chamfers). The Evaluator (phase-4) + schema (phase-4.5) are the fixes.

**4. Fresh-clone verification** — phase-3.5 used the dev venv; before any
public release, exercise the README install from scratch (incl. the
`vtk-osmesa` swap).

## v0 architecture in one breath

`maquette design "<prompt>"` → `cli` → `agent.loop` (state machine, the
only writer of `output/<run-id>/`) → `planner` (LLM→Intent) → `sanity`
(F6) → `worker`→`adapters.build123d_target` (Intent→code) → `executor`
(subprocess + timeout + STEP) → `render` (vtk-osmesa, 3 PNGs). Outputs:
`prompt.txt, intent.json, code.py, part.step, renders/, trace.jsonl,
status.json` (+ `error.json` on failure). Exit codes per F13.

## Read in this order (under 10 minutes)

1. `./CLAUDE.md` — project guide, framework, scope-freeze rule.
2. [`docs/phases/phase-3.5-report.md`](docs/phases/phase-3.5-report.md) — v0 ship report, the 5 surprises, v0.1 recommendations.
3. [`docs/03-roadmap.md`](docs/03-roadmap.md) § Phase 4 + 4.5 — the v0.1 stubs to expand with `/pm-phase-plan`.
4. [`docs/blockers/`](docs/blockers/) — the two phase-3.5 blockers (both resolved) explain the v0 scope as it stands.

## Useful commands

```bash
~/.claude/skills/pm-status/status.sh .                 # project state

# Run v0 (needs the vtk-osmesa swap + a key; .env at repo root)
set -a; . ./.env; set +a
maquette design "a 50 mm cube with a 20 mm hole through the centre" --out /tmp/m

# FULL local CI — READ ruff's real output; run CLI tests under COLUMNS=80
.venv/bin/ruff check src/ tests/ && .venv/bin/ruff format --check src/ tests/
.venv/bin/pyright src/ && .venv/bin/lint-imports
grep -rE "^(import NXOpen|from NXOpen)" src/          # must print nothing
COLUMNS=80 .venv/bin/pytest -q
set -a; . ./.env; set +a; .venv/bin/pytest -m live    # gated live tests
gh run list --limit 1
```

## When phase-4 / v0.1 work continues

v0.1 = phase-4 (Evaluator) → phase-4.5 (schema edge/hole) → phase-5 (NX
adapter) → phase-6 (supporting commands) → phase-7a/b/c (sandboxing,
regression CI, cost caps). v0.2 = phase-8/9/10. Consider a short v0
retrospective (read phase-0…3.5 reports together) before diving into v0.1.
