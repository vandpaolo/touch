---
phase: phase-2b
status: done
min_met: true
max_met: true
duration_planned_days: 5
duration_actual_days: 1
---

# Phase 2b — Pipeline (runtime + orchestration half) — Report

> *Closed out via `/pm-phase-report` on 2026-05-28. Phase started
> 2026-05-28, implementation landed in a single working session the same
> day. Plan: [`phase-2b.md`](phase-2b.md). Audit:
> [`../audits/2026-05-28-pre-phase-2b.md`](../audits/2026-05-28-pre-phase-2b.md)
> (9 PASS, 0 FAIL after clearing two FAILs pre-start — no override).*

## What shipped

| Sprint day | Status | Artefacts |
|---|---|---|
| 1 — ADR-0004 export fix | done | [`build123d_target._export`](../../src/touch_backend/adapters/build123d_target.py) branches on Intent shape (feature-based → `features[-1].id`; extras-only → `body`; degenerate → `AdapterRefusal(where="export:empty")`); new [`l_bracket_extras`](../../tests/fixtures/adapters/build123d/l_bracket_extras/) fixture pair; [`test_adapter_export.py`](../../tests/test_adapter_export.py) (6 tests incl. round-trip). 11 per-kind snapshots byte-identical. Commit `5dc206a`. Carry-forward #1 closed. |
| (mid-day-1) — planner few-shot fix | done | [`prompts/planner.system.md`](../../prompts/planner.system.md): wrapped `Polyline` in `BuildLine` (the few-shot taught non-runnable build123d) + added a "extras must be runnable" guidance note. Verified live. Commit `ba7bdb8`. |
| 2 — `render/orthographic.py` | done | [`render.orthographic`](../../src/touch_backend/render/orthographic.py) → 3 off-screen PNGs (front/side/top) via vtk-osmesa (N5); committed fixture STEP; [`test_render.py`](../../tests/test_render.py) (incl. geometry-not-blank guard); pyproject + CI swap to `vtk-osmesa`. Commits `94c10ce`, `da63d0e`. |
| 3 — `agent/executor.py` | done | [`Executor.execute`](../../src/touch_backend/agent/executor.py) (subprocess `cwd=run dir`, timeout + SIGTERM→SIGKILL grace N9, STEP capture, structured `error.json` N6, run with `python -I`); `ExecutionResult` (no `renders`); [`test_executor.py`](../../tests/test_executor.py). Exit codes 0/12/13. Commit `71f6d12`. |
| 4 — `agent/loop.py` | done | [`Loop.run`](../../src/touch_backend/agent/loop.py) + `RunConfig`: state machine, run-id (F11), planner→contract-validation→sanity→worker→executor→render wiring, `trace.jsonl` (F10), `status.json` (F9, cost via `pricing`, `prompts_hash` ADR-0003), error.json routing; [`test_loop.py`](../../tests/test_loop.py) (6 paths, real worker/executor/render). Commit `1ed938c`. |
| 5 (MAX) — integration + duration + SIGKILL + live | done | Per-step `duration_s` on every trace event (N1); N9 SIGKILL-no-orphan test (executor 100%); live-gated end-to-end test (exit criterion #5). Commits `9be439f`, `08c88c5` (CI fix). |

**Exit criteria — all ten met:**

1. `pyright src/` exits 0.
2. ADR-0004 verified: extras-only L-bracket emits `export_step(body, …)`; 11 snapshots byte-identical; degenerate → `AdapterRefusal(where="export:empty")`.
3. `render.orthographic` writes 3 PNGs > 0 bytes with `DISPLAY` unset (N5).
4. Crash → exit 12 + structured `error.json`, no raw traceback (N6); runaway (SIGTERM-ignoring) killed within timeout + 2 s → exit 13 (N9).
5. **Live** `Loop.run("a 50 mm cube with a 20 mm hole through the centre")` produced a complete `output/2026-05-28T10-31-52__cube_with_hole/` (full F8 set, F9 fields) in **10.1 s** for **$0.0267** — both under the v0 N1 (< 20 s) and N2 (< $0.10) targets.
6. `lint-imports` — 9 contracts kept, 0 broken (6 from phase-2a + render + executor + loop).
7. `pytest -q` → 149 passed, 4 deselected (live). Coverage: render 97%, executor 100%, loop 96% — all above the ≥80% bar.
8. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing.
9. CI green on the most recent push to `main` ([run 26569865562](https://github.com/vandpaolo/maquette/actions/runs/26569865562)).
10. This report exists.

## What slipped

Nothing functional. Min + Max both met; no sprint row deferred or skipped.

One process hiccup (not a scope slip): the day-5 push failed CI on a
single `ruff check` E501 (a 89-char line in `loop.py`) — I had masked the
local `ruff check` output behind `>/dev/null && echo OK` and trusted the
echo instead of reading ruff's real output. Fixed in `08c88c5`; CI green
on re-push. This is the *second* CI-cycle burned on ruff (phase-2a was
`ruff format --check`); both are now captured in the CI-checks memory.

## Surprises

1. **OpenCascade (OCP) and VTK-OSMesa fight over the Mesa GL context.**
   Loading OCP (via build123d) before rendering poisons OSMesa →
   completely blank PNGs. Non-deterministic-looking until isolated. Fix:
   the renderer converts STEP→STL in a **subprocess**, so the render
   process never imports build123d. Also: OSMesa needs an explicit
   `plotter.render()` before `screenshot()` or the frame is blank.
2. **The run artefact `code.py` shadows the stdlib `code` module.**
   Running `code.py` as a script prepends the run dir to `sys.path`;
   build123d's import chain (IPython→pdb→`import code`) then resolves the
   run's `code.py` and fails with a circular import. This is a real
   pipeline bug (the F8 artefact name is fixed). Fix: run with
   `python -I` (isolated) — also a small sandboxing win.
3. **The planner's L-bracket few-shot emitted non-runnable build123d.**
   `Polyline` was placed directly in `BuildSketch`, but build123d
   requires it inside a `BuildLine` context → `RuntimeError`, no STEP.
   This was the *planner prompt's* bug (separate from the ADR-0004 export
   gap). Found while building the day-1 fixture (P2b-R2 materialised).
   Fixed the few-shot + added general guidance; verified live.
4. **Headless rendering needed an environment change (P2b-R3 hit).** The
   stock `vtk` wheel is X11-only and segfaults off-screen; no Xvfb/OSMesa
   on the box. A research sub-agent compared Xvfb vs vtk-osmesa vs EGL;
   chose `vtk-osmesa==9.3.1` (bundled CPU OSMesa, no X/Xvfb/sudo, works on
   bare-ubuntu CI). It coexists with `pyvista` via a post-install swap
   (pyproject comment + dedicated CI step). Verified green in CI.
5. **The architecture was internally inconsistent on render ownership.**
   The C4 container view drew `Loop --> Render` while `02-classes.md` had
   the Executor own it (`ExecutionResult.renders` + an `executor→render`
   dep). Resolving carry-forward / B1 in favour of *Loop owns render*
   (during the pre-phase `/pm-architecture` touch) aligned the docs and
   gave a cleaner N5/N6 separation and natural F7 non-fatal semantics.
6. **Live latency/cost beat the v0 targets on the first real run.** 10.1 s
   and $0.0267 vs N1 < 20 s / N2 < $0.10. First-call `cache_creation` was
   3138 tokens; a warm cache should be cheaper. Formal p95 / cost
   measurement is still phase-3.5's job.

## Decisions taken mid-phase

No `/pm-blocker` filed. The one design-layer decision (render ownership,
plus the ADR-0004 export contract) was handled in a `/pm-architecture`
touch **before** `/pm-phase-start` (freeze was lifted), so no blocker was
needed mid-phase. Key in-phase implementation choices:

- **`python -I` for execution** (surprise #2) — fixes the `code.py`
  shadowing and isolates env/user-site.
- **Subprocess STEP→STL in the renderer** (surprise #1) — isolates OCP
  from OSMesa.
- **`vtk-osmesa` over Xvfb** (surprise #4) — research-backed; recorded in
  `notes/decisions.md`.
- **error.json split** — the executor writes it for exec failures (12/13);
  the loop writes it for planner/adapter failures (10/11); never both.

## Recommended changes for next phase

Phase-3 is the CLI (`maquette design`, F1, F11–F14): the public entry
point wrapping `Loop.run`.

1. **The CLI calls `Loop.run` and maps `status.json.exit_code` to the
   process exit code (F13).** The loop already computes the code and
   records it; the CLI does `sys.exit(code)` and prints the run dir on
   every exit (F12). `Loop.__init__` currently takes
   `(out_root, cfg, client, prompts)` — the CLI constructs the
   `Anthropic()` client and loads the `PromptsBundle` from `prompts/`.
2. **`prompts_hash` is sha256 of the bundle's `planner_system` text**, not
   a true directory roll-up. Fine while `prompts/` holds one file; revisit
   (ADR-0003 open decision #4) when a second prompt file lands (evaluator,
   v0.1 phase-4).
3. **`RunConfig` ↔ `Config` mapping.** Phase-3 builds the `config.Config`
   (CLI > env > pyproject > defaults) and derives the run-scoped
   `RunConfig` from it. The CLI flags (`--out`, `--max-iter`,
   `--exec-timeout`, `--model`, `-q`/`-v`) map onto these fields.
4. **Document the `vtk-osmesa` install step in the README** (phase-3 ships
   the README per F-CLI). The swap is currently only in CI + a pyproject
   comment; a fresh `pip install -e .` won't render until the swap runs.
5. **Glossary follow-up still pending** for `Build123dTarget` /
   `NxOpenTarget` was *resolved this phase* (all four flagged leaves added
   to `02-classes.md`). The recurring pre-phase glossary FAIL should not
   recur.
6. **L-bracket end-to-end is now unblocked** for phase-3.5 (carry-forward
   #1 + the few-shot fix). Phase-3.5 should still manually verify the
   L-bracket STEP opens in FreeCAD and visually matches.
