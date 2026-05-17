---
id: phase-1
title: Adapter
status: planned           # planned | in_progress | blocked | done
started: null             # ISO date when flipped to in_progress
finished: null            # ISO date when flipped to done
min_goal_met: null        # true | false | null
max_goal_met: null        # true | false | null
blocker: null             # path to blocker doc if status = blocked
depends_on: [phase-0]
audit: null               # path to audit doc once /pm-audit (via /pm-phase-start) runs
---

# Phase 1 — Adapter

> *Drafted via `/pm-phase-plan` on 2026-05-17. Update via `/pm-phase-plan`
> before `/pm-phase-start`; once `in_progress`, scope is frozen.*

- **Goal:** The build123d adapter compiles all 11 Intent kinds to runnable
  code; one round-trip works end-to-end (cube-with-hole → STEP file that
  opens in FreeCAD).
- **Depends on:** [`phase-0`](phase-0.md) (`status: done`); requirements
  F3, F4 approved; architecture § Layered responsibilities, classes.md
  § Adapter Protocol + concrete adapters approved; ADR 0001 (Intent as
  pivot).
- **Estimated duration:** 5 days.

## Policies locked for this phase

- **Adapter shape (per [02-classes.md](../02-classes.md) § Module map):**
  `adapters/build123d_target.py` is a **module**, not a class. Its public
  surface is a single module-level `emit(intent: Intent) -> str`. The
  `Adapter` Protocol in `adapters/__init__.py` is defined with a
  `__call__(self, intent: Intent, /) -> str` shape so module-level
  functions satisfy it structurally; conformance is statically asserted
  at the top of each adapter module via `_: Adapter = emit`. Pyright
  basic catches signature drift. (See § Known risks P1-R6 for the
  alternative class-based shape considered.)
- **Purity (per architecture § Layered responsibilities):** adapters are
  pure functions. **No** clock, **no** random, **no** environment reads,
  **no** filesystem I/O in `adapters/*`. Determinism (N3) is enforced
  per-kind via emit-twice diff tests landing in Day 5.
- **`loft.sections` representation (carry-forward from
  [`phase-0-report.md`](phase-0-report.md) surprise #4):** continues to
  be stored as a comma-separated string in `params["sections"]`. If
  parsing this in the adapter produces ambiguity (e.g., spaces, escaped
  commas), **file `/pm-blocker`** to widen `Intent.PrimaryFeature.params`
  to `dict[str, float | str | list[str]]`. Do not paper over with regex
  in the adapter.
- **`extras` handling:** verbatim append after the per-kind emission
  block, separated by `\n\n# --- user extras ---\n`. The `extras` field
  is never parsed, only concatenated. If a user's `extras` references a
  feature id that doesn't exist, the executor (phase-2b) will surface
  the failure — adapter stays out of it.
- **Snapshot fixture format:** each kind gets a folder under
  `tests/fixtures/adapters/build123d/<kind>/` containing `intent.json`
  (input) and `expected.py` (expected emitted code). Tests compare emit
  output to `expected.py` verbatim; CI fails on drift. Re-generating a
  fixture intentionally requires deleting `expected.py` and re-running.

## Minimum deliverable

Phase 1 ships when **all** of the following exist and pass their tests:

- `src/maquette/adapters/__init__.py` — `Adapter` Protocol +
  `AdapterRefusal` exception (carries `reason: str`, `where: str`).
- `src/maquette/adapters/build123d_target.py` — module-level
  `emit(intent: Intent) -> str` covering all 6 PrimaryKinds (box,
  cylinder, sphere, extrude, revolve, loft) and all 5 ModifierKinds
  (hole, fillet, chamfer, shell, pattern). Conformance asserted via
  `_: Adapter = emit` at top of file.
- 11 snapshot fixtures under
  `tests/fixtures/adapters/build123d/<kind>/`, one per kind, with
  `intent.json` + `expected.py`.
- `tests/test_adapters_build123d.py` — 11 snapshot tests (one per
  kind), plus a refusal test (forged unknown kind raises
  `AdapterRefusal`), plus an `extras` round-trip test (verifies the
  raw text gets appended verbatim).
- Round-trip test for the **cube-with-hole reference**: emit code →
  `subprocess.run([sys.executable, "-c", emitted])` in a `tmp_path`
  → assert `part.step` exists and is > 0 bytes. Manual verification
  (FreeCAD opens the STEP and the geometry visibly matches) captured
  in the phase-1 report.
- `[tool.importlinter]` in `pyproject.toml` extended with a new
  contract: `adapters.*` may import only from `maquette.intent` and
  stdlib (excludes `os`, `pathlib`, `subprocess` — adapters are pure).
- CI grep guard (`! grep -rE "^(import NXOpen|from NXOpen)" src/`)
  continues to return nothing after `build123d_target.py` lands.

## Maximum deliverable

If everything above lands cleanly, also:

- Round-trip tests for the two remaining v0 reference prompts:
  cylinder-with-chamfer, L-bracket-with-holes (Intent built in-test,
  emit + subprocess + STEP-exists assertion).
- **Determinism tests per kind (N3)**: `tests/test_adapter_determinism.py`
  emits each of the 11 kinds twice and asserts byte-identical output.
- **GitHub Actions Node-24 bump (carry-forward from
  [`phase-0-report.md`](phase-0-report.md) recommendation #1):** bump
  `actions/checkout@v4` and `actions/setup-python@v5` to versions that
  no longer emit the Node-20 deprecation warning. Verify the warning
  disappears in the resulting CI run. **Deadline: 2026-06-02.**
- **Coverage filter cleanup (carry-forward recommendation #4):** move
  the `coverage run --include=…` line in `.github/workflows/ci.yml` to
  `[tool.coverage.run] source = ["src/maquette/intent", "src/maquette/intent_validation", "src/maquette/adapters"]`
  in `pyproject.toml`; CI step becomes a one-liner.

## Sprint / day breakdown

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Adapter Protocol + scaffolding + import-linter contract | `src/maquette/adapters/__init__.py` (`Adapter` Protocol with `__call__` shape, `AdapterRefusal` exception); `src/maquette/adapters/build123d_target.py` skeleton with `emit(intent)` dispatching to per-kind `_emit_<kind>` placeholders that raise `NotImplementedError`; `_: Adapter = emit` static-conformance assertion at top of module; `[tool.importlinter]` contract added (adapters.* depends only on maquette.intent + stdlib); `tests/test_adapters_protocol.py` with one test that calls `emit` on a forged unknown kind and asserts `AdapterRefusal` | `pyright src/` exits 0 (Protocol conformance); `lint-imports` reports 3 contracts kept, 0 broken; the protocol/refusal test passes; module-level dispatch returns `NotImplementedError` for box (placeholder smoke) |
| 2 | PrimaryKinds (6 emitters) + 6 snapshot fixtures | `_emit_box`, `_emit_cylinder`, `_emit_sphere`, `_emit_extrude`, `_emit_revolve`, `_emit_loft` (pure string-emitting helpers); `_preamble(intent)` (imports + parameter declarations); `tests/fixtures/adapters/build123d/{box,cylinder,sphere,extrude,revolve,loft}/{intent.json,expected.py}`; 6 snapshot tests in `tests/test_adapters_build123d.py` | 6 snapshot tests pass against committed fixtures; emit output for the `box` fixture runs without error under `python -c "<output>"` (no STEP export yet — just BREP construction smoke) |
| 3 | ModifierKinds (5 emitters) + extras escape hatch + refusal path | `_emit_hole`, `_emit_fillet`, `_emit_chamfer`, `_emit_shell`, `_emit_pattern`; `_extras_block(extras)` appending verbatim; AdapterRefusal raised on any unknown kind in dispatch (defensive — pydantic Literal blocks this through normal Intent construction, but the path must exist); 5 snapshot fixtures; 5 snapshot tests; 1 extras test (Intent with `extras="# raw\n"` produces output ending in `# raw\n`); 1 refusal test for `kind=` forged outside the Literal | 11 snapshot tests total pass; extras test asserts verbatim-append behaviour; refusal test asserts `AdapterRefusal.where == "feature:<kind>" \| "modifier:<kind>"` |
| 4 | Round-trip: emit → subprocess → STEP for cube-with-hole | `_export(intent)` appends `Part.export_step(...)` to emitted code; `tests/test_adapter_roundtrip.py` builds the cube-with-hole Intent (per `02-data-model.md` § Example), emits, runs the emitted code via `subprocess.run([sys.executable, "-c", code], cwd=tmp_path, timeout=30)`, asserts `part.step` exists and is > 0 bytes; manual: open the resulting STEP in FreeCAD locally and visually confirm 50 mm cube with through-hole | Round-trip test exits 0; `part.step` size > 0 bytes; manual FreeCAD check passes (recorded in phase-1 report) |
| 5 | (MAX) 3-reference round-trips + determinism + GH Actions Node-24 + coverage cleanup | Round-trip tests for cylinder-with-chamfer + L-bracket-with-holes (both produce valid STEP); `tests/test_adapter_determinism.py` (11 tests — emit twice per kind, assert identical); `.github/workflows/ci.yml` updated: `actions/checkout@v5+`, `actions/setup-python@v6+`, Node-20 deprecation warning gone; `[tool.coverage.run]` section in `pyproject.toml` replacing the `--include=` flag in CI | All 3 round-trip tests pass; 11 determinism tests pass; CI run shows no Node deprecation warning; `coverage report` runs with no `--include` flag on the CLI and still reports on the same modules |

## Exit criteria

Phase 1 is `done` when **all** of the following hold:

1. `pyright src/` exits 0 (Adapter Protocol conformance verified statically).
2. All 11 per-kind snapshot tests pass.
3. `AdapterRefusal` raised on a forged-unknown kind; the refusal test
   asserts `where` and `reason` fields are populated.
4. Cube-with-hole round-trip test passes: emit produces code that runs
   under subprocess and creates a `part.step` > 0 bytes.
5. Manual: the cube-with-hole STEP opens in FreeCAD on nexus and the
   geometry visibly matches the prompt description (50 mm cube with
   20 mm through-hole). Recorded in phase-1 report.
6. `lint-imports` reports zero contract violations (now 3 contracts:
   the two from phase-0 plus the new `adapters.* → maquette.intent +
   stdlib` contract).
7. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing (re-
   verified after `build123d_target.py` lands per N4).
8. `pytest -q` passes; full coverage report ≥ 80 % on
   `maquette.adapters` in addition to the phase-0 modules.
9. CI green on the most recent push to `main`, including the new tests.
10. `phases/phase-1-report.md` exists (written via `/pm-phase-report`)
    capturing what shipped, what slipped, surprises, and decisions.

## Known risks for this phase

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| P1-R1 | build123d API surface for `revolve`, `loft`, and `pattern` requires non-obvious construction (e.g. `revolve` wants a `Sketch`; `loft` wants a sequence of section curves; `pattern` wants a `LocationList`). Emitted code may need iteration before snapshot fixtures stabilise. | med | med | Start with the simpler primitives (Day 2: box, cylinder, sphere) and verify the round-trip subprocess smoke before tackling the more complex three. If a single kind blocks for > 2 hours, file `/pm-blocker` rather than guess at the API. |
| P1-R2 | STEP export via `Part.export_step(...)` (build123d API) may need a different incantation depending on the build123d version pinned in phase-0 (`==0.10.0`). | low | med | Verify on Day 4 against the actual installed build123d. If the API differs, emit `from build123d import export_step` and adjust. Pin survives because adapter only uses public API. |
| P1-R3 | Snapshot test brittleness on whitespace, trailing newlines, or formatter touches (e.g., ruff format auto-fixing committed fixtures). | med | low | Store fixtures with explicit `\n` newlines (no trailing newline drift); exclude `tests/fixtures/**` from ruff via `extend-exclude` in `[tool.ruff]`; one snapshot diff failure should print the diff inline so debugging is one-shot. |
| P1-R4 | Subprocess STEP capture flakes if the subprocess closes before the file is flushed to disk, or working directory confusion between `cwd=tmp_path` and the emitted code's relative paths. | med | med | Emit absolute path for `export_step`: `Part.export_step(Path(__file__).parent / "part.step")` would fail since `__file__` is `None` for `-c`; instead emit `Path.cwd() / "part.step"` and `subprocess.run(..., cwd=tmp_path)`. Round-trip test asserts the file landed in `tmp_path`. |
| P1-R5 | `loft.sections` comma-split representation (carry-forward from phase-0 report surprise #4) forces ugly string-splitting in the adapter and is brittle to user input variation. | med | med | If the adapter ends up with a regex on `params["sections"]`, **file `/pm-blocker`** to widen `Intent.PrimaryFeature.params` to `dict[str, float \| str \| list[str]]` rather than smuggling structure through a string. The "no design edits during phase" rule is exactly what `/pm-blocker` is for. |
| P1-R6 | Pyright Protocol conformance for module-level `emit` is non-obvious — Python's `Protocol` is typically for instance methods, not module functions. A naive `class Adapter(Protocol): def emit(self, intent): ...` won't match a module-level `def emit(intent): ...`. | low | low | Define `Adapter` with `def __call__(self, intent: Intent, /) -> str: ...` and assert `_: Adapter = emit` at top of each adapter module. Pyright treats this as a structural callable check. Verified Day 1. Alternative (class-based wrapper) considered but deviates from classes.md and isn't worth the extra layer. |
| P1-R7 | GitHub Actions Node-20 deprecation hits the **2026-06-02** cutoff; if phase-1 takes longer than expected, Day 5 (MAX) may slip past the deadline and the next CI push fails. | low | med | Day 5 MAX deliverable handles it. If phase-1 looks like it'll slip past the date, promote the Actions bump from MAX to a Day-1 task — it's a 2-line YAML change. Re-evaluate at Day 3 standup. |
| P1-R8 | Adapter purity rule prohibits filesystem I/O — but the cube-with-hole round-trip test on Day 4 *does* I/O (subprocess + STEP write). The I/O lives in the *emitted* code, not the adapter itself; the test verifies behaviour, the test is in `tests/`, the adapter file stays pure. Worth flagging only so the audit doesn't get confused. | low | low | The contract is on `adapters/*` source files, not on what their emitted code does. Test file `tests/test_adapter_roundtrip.py` is allowed to spawn subprocesses; the import-linter rule excludes `tests/` by default. |

## Notes for `/pm-phase-start`

When `/pm-phase-start` runs, the Auditor sub-agent should verify:

- F3 (worker emits build123d via adapter) and F4 (build123d adapter
  supports the full v0 Intent schema) are addressed by at least one task
  in the day breakdown. (F3 partial — worker shim lands in phase-2a;
  phase-1 only delivers the adapter, not the worker. F4 fully delivered
  by Day 2 + Day 3.)
- NFRs N3 (adapter determinism, fixture per kind), N4 (NX hygiene),
  N7 (reproducibility via re-emit) each have at least one task contributing
  to them. (N3 via snapshot tests Day 2 + Day 3 and determinism tests
  Day 5; N4 via the unchanged grep guard; N7 via determinism + snapshot
  re-run on saved `intent.json`.)
- The new import-linter contract (adapters.* depends only on
  maquette.intent + stdlib) is added before Day 2 lands code that
  could violate it.
- The carry-forward items from
  [`phase-0-report.md`](phase-0-report.md) recommendations #1, #2,
  #4 are reflected in the plan: #1 in Day 5 MAX (Node-24 bump), #2 in
  P1-R5 mitigation (loft.sections blocker policy), #4 in Day 5 MAX
  (coverage filter cleanup).
- ADR 0001 (Intent as the pivot) is realised: the adapter is the first
  consumer of the typed Intent that exists outside the schema module
  itself.

After audit passes, `/pm-phase-start` flips this file's
`status: planned` → `status: in_progress`, sets `started: 2026-MM-DD`,
and updates `03-roadmap.md` frontmatter `active_phase: phase-1`. From
that moment, the scope-freeze rule applies: no requirement or
architecture edits without filing `/pm-blocker` first.
