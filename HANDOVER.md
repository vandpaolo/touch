# Handover — Maquette, phase-2a day 1

> *Start here in any fresh chat session that opens this project. Once
> phase-2a is `done`, rewrite this file for phase-2b. Always keep it
> short enough to read in 60 seconds.*

## You are here

- **Project:** Maquette — natural-language CAD prompt → editable parametric solid + STEP.
- **Active phase:** `phase-2a` — Pipeline (LLM-facing half). Status: `in_progress`, started 2026-05-18.
- **Audit:** [`docs/audits/2026-05-18-pre-phase-2a-v2.md`](docs/audits/2026-05-18-pre-phase-2a-v2.md) (PASS with documented override on out-of-phase glossary leaves + README-frontmatter strict-reading).
- **Last commit:** `607e74f docs: phase-2a audit cycle + start (via /pm-phase-start)` on `main`, pushed.
- **Scope is frozen.** No edits to `docs/00-*`, `docs/01-*`, `docs/02-*`, `docs/03-*`, or `docs/adr/` without filing `/pm-blocker` first. Implementation only.

## Phases done so far

| Phase | Closed | min/max | Highlights |
|---|---|---|---|
| `phase-0` Foundations | 2026-05-17 | true/true | Intent schema + intent_validation + pricing + config; 68 tests; CI green |
| `phase-1` Adapter | 2026-05-18 | true/true | build123d adapter for all 11 v0 kinds; 3-reference round-trips; cube-with-hole STEP verified visually in NX |

100 tests across the project at end of phase-1. CI green on every push to `main`.

## Read in this order (under 10 minutes total)

1. `./CLAUDE.md` — project guide, framework reference.
2. [`docs/phases/phase-2a.md`](docs/phases/phase-2a.md) — your phase plan: policies locked, MIN/MAX, day breakdown, exit criteria. **This is your day-by-day spec.**
3. [`docs/phases/phase-1-report.md`](docs/phases/phase-1-report.md) § Recommended changes for next phase — eight items feeding phase-2a's choices (hole-positioning via extras, sanity tolerance locked, etc.). Plus § Surprises (which limitations of the v0 schema the planner system prompt must teach the LLM about).
4. [`docs/adr/0002-dimension-sanity-check.md`](docs/adr/0002-dimension-sanity-check.md) — the implementation spec for Day 1's `agent.sanity`. Tolerance ±1% or ±0.5 mm whichever larger; visibility-signal-not-gate.
5. [`docs/adr/0003-prompt-caching-for-cost.md`](docs/adr/0003-prompt-caching-for-cost.md) — the Anthropic call shape for Day 2's `agent.planner`. **Pre-phase verified against `anthropic==0.102.0` SDK on 2026-05-18; ADR shape valid as documented.** See phase-2a.md § Policies locked for the verification note.
6. [`docs/02-classes.md`](docs/02-classes.md) § Module map + § Agent module class diagrams — concrete class shapes for `PlanResult`, `SanityResult`, `DimensionMismatch`, `Dimension`.

## Policies locked for phase-2a (do not deviate without `/pm-blocker`)

- **Hole-positioning carry-forward:** planner system prompt instructs LLM to route off-centre hole positions through `Intent.extras` (not ad-hoc `params` keys). v0 schema stays stable through v0 ship. No `/pm-blocker` needed.
- **L-bracket / non-primitive shapes:** planner emits raw build123d source in `extras` for shapes the 11-kind schema can't express.
- **Coarse edge selection:** fillet/chamfer modifiers chamfer/fillet *all* edges of the target. If a prompt says "top edge only," planner emits explicit edge selection in `extras`. Schema-v2 candidate.
- **Sanity tolerance:** ±1% or ±0.5 mm, whichever is larger (ADR 0002). Referenced from the module docstring.
- **Testing strategy:** unit tests use `unittest.mock` patched Anthropic client (no key, no network, fast). Live integration tests use `@pytest.mark.live` + `pytest.skipif(os.environ.get("ANTHROPIC_API_KEY") is None)` and are excluded from default CI matrix until phase-3.5.
- **Anthropic call shape:** `system=[{"type": "text", "text": ..., "cache_control": {"type": "ephemeral"}}]` per ADR 0003 (verified against SDK).

## Day 1 — your current task

`agent.sanity` + import-linter contract.

**Outputs:**
- `src/maquette/agent/sanity.py` — `Dimension`, `DimensionMismatch`, `SanityResult` frozen dataclasses; module-level `check(prompt: str, intent: Intent) -> SanityResult` with regex extraction `(\d+(?:\.\d+)?)\s*(mm|cm|m|in)` plus delimited `<n>×<n>×<n> mm`; unit-normalised comparison to all Intent numeric values; ±1% or ±0.5 mm tolerance; module docstring links ADR 0002.
- `[tool.importlinter]` contract added to `pyproject.toml`: `agent.sanity → maquette.intent + stdlib only` (no other maquette modules, no I/O modules).
- `tests/test_sanity.py` — ≥ 8 tests covering tolerance edges (just-inside vs just-outside ±0.5 mm and ±1%), multi-axis prompts (`60 × 40 × 5 mm`), unit-aware comparison (50 mm vs 5 cm), empty-prompt and empty-intent edge cases.

**Done when:**
- All sanity tests pass.
- `check("a 50 mm cube with a 20 mm hole through the centre", <cube-with-hole Intent>)` returns `SanityResult(ok=True, ...)`.
- `lint-imports` reports **4 contracts kept** (3 from phase-0/1 + the new sanity contract).
- `pyright src/` exits 0.
- `pytest -q` passes (current baseline: 100 tests).

## After Day 1

| Day | Task | Lives in |
|-----|------|----------|
| 2 | `agent.planner` (Anthropic prompt caching + JSON extraction + retry-on-schema-fail + PlannerExhausted exception + Tokens mapping) + initial `prompts/planner.system.md` (Intent schema + 11-kind contracts + cube-with-hole few-shot + v0-gap guidance) | `src/maquette/agent/planner.py`, `prompts/planner.system.md`, `tests/test_planner.py` (mocked client) |
| 3 | `agent.worker` (thin shim delegating to phase-1's build123d adapter) + (MAX) `PlanResult.duration_s` + centred-keyword sanity false-positive tests + cylinder-with-chamfer + L-bracket-with-extras few-shots + `@pytest.mark.live` integration smoke gated on `ANTHROPIC_API_KEY` | `src/maquette/agent/worker.py`, `tests/test_worker.py`, `tests/test_planner_live.py` (MAX) |

Full exit criteria are in [docs/phases/phase-2a.md § Exit criteria](docs/phases/phase-2a.md).

## If you hit a design gap

**Do not modify design docs.** Run `/pm-blocker` and describe the gap. Phase-1 surfaced two real ones (hole positioning, L-bracket) that were absorbed into phase-2a's locked policies above — that's how the framework wants design pivots to surface, explicit and visible, not via silent mid-code edits.

Likely candidates this phase:
- **SDK API drift mid-implementation** beyond the pre-phase verification. Possible if upstream releases a new `anthropic` version between commits. (Pinned `~=0.102.0`, so minor releases only; should be stable.)
- **System prompt under-specification** (P2a-R2) — only surfaces under real LLM calls. If MAX live tests show high retry rates, that's prompt-design iteration inside phase-2a, not a blocker.

## Useful commands

```bash
# Current project state
~/.claude/skills/pm-status/status.sh .

# Latest CI status (last green run was on phase-1 day 5 MAX)
gh run list --limit 1

# Run all tests (currently 100 passing)
.venv/bin/pytest -q

# Run only unit tests, skipping any future live tests
.venv/bin/pytest -q -m "not live"

# Coverage on tracked modules (config in pyproject)
.venv/bin/coverage run -m pytest -q && .venv/bin/coverage report
```

## When phase-2a is done

Run `/pm-phase-report` — close out, capture what shipped / what slipped / surprises, flip status to `done`. Then `/pm-phase-plan phase-2b` to detail the next phase (Pipeline runtime + orchestration half: `agent.executor`, `render.orthographic`, `agent.loop` with `trace.jsonl` + `status.json`), and `/pm-phase-start phase-2b` to greenlight.

Phase-2b lands the loop that ties everything together; phase-3 wires the CLI; phase-3.5 verifies the 3 v0 reference prompts manually and **v0 ships**.

## Carry-forward to revisit before phase-5

- **Glossary close-out** — phase-1-report recommendation #8 + phase-2a audit-v2 override. Run a `/pm-architecture` pass to add the remaining leaf terms (`PrimaryKind`, `ModifierKind`, `Unit`, `Mesh`, `Pricing`, `Config`, `Refiner`) plus any phase-2a-introduced terms not already added. Eliminates the audit-loop pattern that's hit every `/pm-phase-start` so far.
