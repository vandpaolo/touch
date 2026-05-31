---
phase: phase-1
status: done
min_met: true
max_met: true
duration_planned_days: 5
duration_actual_days: 1
---

# Phase 1 — Adapter — Report

> *Closed out via `/pm-phase-report` on 2026-05-18. Phase ran
> 2026-05-17 → 2026-05-18. Plan: [`phase-1.md`](phase-1.md). Audit:
> [`../audits/2026-05-17-pre-phase-1-v4.md`](../audits/2026-05-17-pre-phase-1-v4.md)
> (PASS with override on Check 5 — glossary completeness deferred to a
> post-phase-1 `/pm-architecture` pass per audit § Override).*

## What shipped

| Sprint day | Status | Artefacts |
|---|---|---|
| Day 1 — Adapter Protocol + scaffolding + import-linter contract | done | [`src/maquette/adapters/__init__.py`](../../src/touch_backend/adapters/__init__.py) (`Adapter` Protocol, `AdapterRefusal`); [`src/maquette/adapters/build123d_target.py`](../../src/touch_backend/adapters/build123d_target.py) skeleton with dispatch + per-kind placeholders + `_: Adapter = emit` static-conformance assertion; new `[tool.importlinter]` contract (adapters depend only on `maquette.intent` + stdlib minus I/O); [`tests/test_adapters_protocol.py`](../../tests/test_adapters_protocol.py). Commit `1ccf361`. |
| Day 2 — 6 PrimaryKind emitters + fixtures | done | `_emit_{box,cylinder,sphere,extrude,revolve,loft}`; `_preamble` (imports + parameter declarations); 6 fixtures under `tests/fixtures/adapters/build123d/<kind>/` with `intent.json` + `expected.py`; parametrized snapshot test. Commit `77028e5`. |
| Day 3 — 5 ModifierKind emitters + extras escape hatch | done | `_emit_{hole,fillet,chamfer,shell,pattern}`; `_extras_block` (verbatim append with `# --- user extras ---` separator); 5 modifier fixtures (the `hole` fixture is the canonical cube-with-hole reference from `02-data-model.md`); snapshot parametrize extended to all 11 kinds; `test_extras_appended_verbatim`. Commit `3cfbc01`. |
| Day 4 — Cube-with-hole round-trip + STEP export + manual CAD check | done | `_export(intent)` now emits `export_step(<last_feature_id>, "part.step")`; all 11 fixtures' `expected.py` updated; [`tests/test_adapter_roundtrip.py`](../../tests/test_adapter_roundtrip.py) (subprocess round-trips with `cwd=tmp_path`, two tests — box smoke + cube-with-hole); box subprocess smoke moved out of `test_adapters_build123d.py` (now snapshot-only). Manual CAD check passed against Siemens NX Student Edition. Commit `af1d929`. |
| Day 5 (MAX) — 3-reference round-trips + determinism + GH Actions Node-24 + coverage cleanup | done | [`tests/test_adapter_determinism.py`](../../tests/test_adapter_determinism.py) (11 kinds, emit twice, assert byte-identical); two more round-trips (cylinder-with-chamfer, L-bracket-with-holes); `actions/checkout` v4→v6 and `actions/setup-python` v5→v6 (Node-24 compatible); `[tool.coverage.run]` + `[tool.coverage.report]` in pyproject (CI step now one-liner). Commit `4345ee8`. |

**Exit criteria** — all ten met:

1. `pyright src/` exits 0 (Adapter Protocol conformance verified statically).
2. 11 per-kind snapshot tests pass.
3. `AdapterRefusal` raised on forged-unknown kind with `where` + `reason` populated.
4. Cube-with-hole round-trip → `part.step` 19,113 bytes.
5. **Manual CAD verification** — Siemens NX Student Edition opened the STEP cleanly; visible 50 mm centered cube with a 20 mm through-hole along Z, geometry matches the prompt. (Phase plan named FreeCAD as the manual-check target; NX served the same purpose and is a stronger cross-CAD-fidelity signal ahead of phase-5.)
6. `lint-imports` — 3 contracts kept, 0 broken.
7. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing.
8. `pytest -q` → 100 passed (32 net new tests during phase-1). Coverage on `maquette.adapters` = 96% on `build123d_target.py`, 100% on `adapters/__init__.py` — well above the ≥80% bar.
9. CI green on the most recent push to `main` ([run 26031514737](https://github.com/vandpaolo/maquette/actions/runs/26031514737), 1m11s, zero deprecation annotations).
10. This report exists.

## What slipped

Nothing. Min + Max both met. No sprint row deferred or skipped.

## Surprises

1. **Cross-CAD STEP fidelity validated unexpectedly.** The Day-4 manual check was specified against FreeCAD; the user opened the STEP in Siemens NX Student Edition instead and confirmed the geometry. STEP B-rep interop worked cleanly across both the v0 build123d origin and the v0.1 NX target. Concrete positive signal ahead of phase-5 NX adapter work — STEP-as-lingua-franca is a tested assumption now, not a hoped-for one.

2. **Hole positioning is implicit at origin** (highest-impact gap). [`_emit_hole`](../../src/touch_backend/adapters/build123d_target.py) emits the subtractive Cylinder at the origin regardless of any positional intent. Cube-with-hole *works incidentally* because the box is centered at origin and the Cylinder ends up coaxial. The L-bracket case has two holes that overlap at origin instead of sitting at flange centres. Schema slot for hole position (face + 2D offset per `02-data-model.md` text) is not exercised by current emit; carry forward.

3. **L-bracket is not v0-schema-modellable as a single Intent.** No `union` modifier and no L-shape primary in the 11 v0 kinds. The Day-5 round-trip ships a single-plate approximation (60×40×5 box + two overlapping holes) that satisfies "STEP > 0 bytes" but doesn't visually match the prompt. Real L-bracket emission will need either (a) planner using `Intent.extras` to emit a custom L-shape in build123d source, or (b) a schema-v2 addition. Both are post-phase-1.

4. **Coarse fillet/chamfer edge selection is real-prompt-breaking.** Cylinder-with-chamfer's prompt says "2 mm chamfer on the *top* edge"; emit chamfers both top and bottom rims (all-edges selection per [`02-data-model.md`](../02-data-model.md) § Per-kind contracts). v0 schema spec explicitly allows this, but it's a stretch to call the output prompt-faithful. Schema-v2 candidate; not a fix for phase-2a.

5. **`_THROUGH_HOLE_DEPTH = 1000.0 mm` constant** assumes parts < 500 mm. Works for every v0 reference prompt; will quietly produce wrong geometry on a hypothetical 600 mm part. Could compute from target's bounding box but that means the adapter has to introspect intermediate build123d state, which collides with the pure-function rule. Probable resolution: schema-v2 adds optional `clearance` param to hole, defaulting to a generous-but-bounded value.

6. **Cylinder subtraction vs `build123d.Hole` was a real design-integrity check, not a stylistic preference.** Resolved cleanly in conversation mid-Day-3: at the **Intent** layer, `hole` is a distinct kind because the NX adapter (v0.1 phase-5) must render it as `NXOpen.Features.HolePackage` for feature-tree fidelity, while the build123d adapter happens to render it as `body - Cylinder(...)`. STEP B-rep is geometrically identical either way. This is the ADR-0001 pivot doing its job — Intent semantic ≠ implementation detail in each adapter.

7. **`loft.sections` comma-split parsing worked.** The phase-0 surprise #4 (P1-R5 risk) said "file `/pm-blocker` if it gets ambiguous." It didn't — the simple `"sketch_a,sketch_b"` representation parsed cleanly in `_emit_loft`. No blocker filed. Watching whether this still holds when phase-2a planner generates lofts.

8. **Snapshot fixtures matched emit() on first try across all 11 kinds.** No fix-up cycles between writing `expected.py` files and running `pytest`. Suggests the emit format design was well-anchored before code landed (algebra-mode, variable-per-id, predictable f-string formatting). Worth reusing this pattern for the NX adapter's fixtures in phase-5.

9. **`pyright --pythonpath` workaround held up.** Phase-0 surprise #5 noted a two-track pyright config (local `venvPath` vs CI `--pythonpath`); both kept passing through phase-1. Not a problem to fix; just a hygiene tax we're paying.

10. **`build123d.export_step` API worked first-try** (P1-R2 risk mitigated). Called via `from build123d import *` then `export_step(body, "part.step")`. No signature surprises in 0.10.0.

11. **One audit-cycle anomaly carried forward**, recorded in
    [`../audits/2026-05-17-pre-phase-1-v4.md`](../audits/2026-05-17-pre-phase-1-v4.md)
    § Override: four glossary terms (`Build123dTarget`, `NxOpenTarget`,
    `Dimension`, `Refiner`) remain undefined in
    [`02-classes.md`](../02-classes.md) § Ubiquitous language. None
    blocked phase-1 work. Should be closed in a post-phase-1
    `/pm-architecture` glossary polish pass before phase-5 (where the
    NX adapter actually lands `NxOpenTarget`).

## Decisions taken mid-phase

No blockers filed. No design pivots required.

Three substantive choices made inside the locked plan, all in-scope per the policies section of [`phase-1.md`](phase-1.md):

- **Module-level emit, not class-based** (locked at plan time): chose to match `<<module>>` stereotype in `02-classes.md` and shape `Adapter` Protocol with `__call__` so module functions satisfy it structurally. Pyright basic verified cleanly.
- **Cylinder subtraction for build123d `_emit_hole`** (Day 3): documented in this report's surprise #6.
- **Single-plate approximation for L-bracket** (Day 5): documented in this report's surprise #3.

## Recommended changes for next phase

Phase-2a is the Pipeline LLM-facing half: `agent.planner`, `agent.sanity`, `agent.worker`.

1. **The planner system prompt must teach the LLM about v0 schema gaps.** Specifically: hole positioning, no union/L-shape primitives, coarse edge selection for fillet/chamfer. The planner should know to route position info and complex shapes through `Intent.extras` rather than failing or producing misleading geometry. Otherwise the v0 reference prompt #3 (L-bracket) won't ship even with a working pipeline.

2. **`_emit_hole` accepting a `position` param** is a phase-2a worker-side conversation, not a phase-1 fix. When the planner starts emitting positions via `params["position_x"]` (or similar), the adapter needs a slot. Either: (a) add position keys to data-model's per-kind contract for hole; (b) keep emit at origin and have planner use `extras` for off-centre holes. Decision belongs to phase-2a planning, not retro.

3. **Sanity check tolerance is locked** at ±1% or ±0.5 mm whichever is larger (ADR 0002). Phase-2a `agent.sanity` should reference the ADR directly in the module docstring.

4. **F3 (worker shim) is still partial.** Phase-1 delivered the adapter but not the `agent.worker` thin shim that selects between adapters. Phase-2a closes F3 fully.

5. **Coverage filter cleanup landed** (recommendation #4 from phase-0 report). New modules (`agent.*`) added in phase-2a just need to be appended to `[tool.coverage.report] include = [...]` in pyproject.

6. **GH Actions Node-24 bump landed** (recommendation #1 from phase-0 report). Deprecation deadline neutralised; no further action.

7. **Phase pacing pattern is solidifying.** Phase-0 and phase-1 both shipped in 1 work day each despite the plans estimating 4 and 5 days respectively. Two data points isn't a trend, but worth noting: the plans appear to over-estimate calendar effort, possibly because the day rows often have minimal inter-day dependencies. Phase-2a will be a real test — `agent.planner` requires a live Anthropic API key for at least the integration smoke, which adds friction the prior phases didn't have.

8. **Glossary follow-up** (carried from audit-v4 override): a single `/pm-architecture` pass before phase-5 to close the four leaf glossary terms (`Build123dTarget`, `NxOpenTarget`, `Dimension`, `Refiner`) plus any phase-2a-derived terms that surface. Not blocking phase-2a; just don't forget it before phase-5.
