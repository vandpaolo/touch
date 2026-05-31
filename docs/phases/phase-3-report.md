---
phase: phase-3
status: done
min_met: true
max_met: true
duration_planned_days: 3
duration_actual_days: 1
---

# Phase 3 — CLI — Report

> *Closed out via `/pm-phase-report` on 2026-05-28. Phase started
> 2026-05-28, implementation landed the same session. Plan:
> [`phase-3.md`](phase-3.md). Audit:
> [`../audits/2026-05-28-pre-phase-3.md`](../audits/2026-05-28-pre-phase-3.md)
> (9 PASS, 0 FAIL after fixing one broken link pre-start — no override).*

## What shipped

| Sprint day | Status | Artefacts |
|---|---|---|
| 1 — loop API-error hardening (P3-Q1) + `cli.py` + contract + entry point | done | [`loop._plan`](../../src/touch_backend/agent/loop.py) catches `anthropic.AnthropicError` → `PLANNING_FAILED` / exit 10 + complete run folder; [`src/maquette/cli.py`](../../src/touch_backend/cli.py) (`design` command; F14 flags → `Config.load` → `RunConfig`; `Anthropic()` + `PromptsBundle`; `Loop.run`; reads `status.json.exit_code`; prints run dir F12; missing-key → exit 1); `[project.scripts] maquette`; `[tool.importlinter]` `cli` contract (`allow_indirect_imports`). Commit `5fcc588`. |
| 2 — `tests/test_cli.py` + `README.md` | done | [`tests/test_cli.py`](../../tests/test_cli.py) (CliRunner, monkeypatched `Loop`: happy path, exit-code mapping 10/11/12/13 + F12, flag precedence into Config/RunConfig, missing-key→1, bad-arg→2); [`README.md`](../../README.md) (install incl. **vtk-osmesa swap**, `.env`, usage + flag table, F13 exit-code table, run-folder layout). Commit `5fcc588`. |
| 3 (MAX) — verbosity + prompt guard + `--help` + edge tests | done | `-v` per-step/per-LLM-call token log to stderr; default one-line status summary; `-q` prints only the run dir (F12); empty/whitespace prompt → exit 2; `--help` flag-registration test; `-q`/`-v` output tests. Commits `0343f95`, `3779b1a`, `614a363`. |

**Exit criteria — all nine met:**

1. `pyright src/` exits 0.
2. **Live:** `maquette design "a 50 mm cube with a 20 mm hole through the centre" --out …` from a shell produced a complete run folder, printed its path (F12), and exited 0 (F1).
3. F13 codes verified: bad args → 2; missing key → 1; Anthropic API error during planning → 10 with a complete folder (P3-Q1); loop-sourced 10/11/12/13 map through (monkeypatched `Loop` tests).
4. `lint-imports` — 10 contracts kept, 0 broken (9 from phase-2b + `cli`).
5. `pytest -q` → 162 passed, 4 deselected (live). `cli` coverage 90% (≥ 80% bar).
6. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing.
7. `README.md` documents install (incl. the vtk-osmesa swap), `.env`, usage + flags, and the exit-code table.
8. CI green on the most recent push to `main` ([run 26574404378](https://github.com/vandpaolo/maquette/actions/runs/26574404378)).
9. This report exists.

## What slipped

Nothing functional. Min + Max both met; no sprint row deferred or skipped.

Process: **three CI cycles burned**, all on lint/test-environment issues
(not logic). (1) An E501 long line in `loop.py` reached CI after I masked
local `ruff check` output behind `>/dev/null && echo OK`. (2)+(3) A
`--help` test asserted flag names in Typer/Rich-rendered output, which
passed on a wide local terminal but wrapped/truncated at CI's 80 cols;
patching `COLUMNS` didn't fix it (rich version differences), so the test
was rewritten to introspect the Click command's registered options
(render-independent). All captured in the CI-checks memory.

## Surprises

1. **A single-command Typer app collapses the command name.** With only
   `@app.command() design`, Typer drops the subcommand name, so
   `maquette design "…"` parsed "design" as the prompt. Adding a no-op
   `@app.callback()` forces multi-command mode and restores
   `maquette design "…"`.
2. **Rich-rendered `--help` is not a stable test target.** Terminal width
   *and* the (unpinned) `rich` version change wrapping/truncation, so
   asserting flag substrings in `--help` output is flaky across
   environments. The robust test introspects
   `typer.main.get_command(app).commands["design"].params`.
3. **`ruff format` does not always wrap an over-length expression**, so an
   E501 can survive a format pass — `ruff check` is the gate that catches
   it. (Reinforced the phase-2a lesson; both now in the CI memory.)
4. **import-linter `forbidden` contracts catch *transitive* imports.** The
   `cli` contract forbids `render`/`adapters`/etc., but the cli reaches
   them through the loop (its entire job). `allow_indirect_imports = "true"`
   restricts the contract to *direct* cli imports — the actual intent.
5. **`.env` had no loader in `src/`.** The architecture said ".env loaded
   at startup," but nothing did it until now. The CLI calls
   `dotenv.load_dotenv()` at startup — the natural composition-root home.

## Decisions taken mid-phase

No `/pm-blocker` filed. The one design-adjacent decision (P3-Q1: how to
handle Anthropic API errors during planning) was settled in
`/pm-phase-plan` *before* start — harden `loop._plan` to map them to exit
10 + a complete run folder, so every invocation is self-contained
(recorded in `notes/decisions.md`, 2026-05-28). In-phase implementation
choices:

- **`@app.callback()`** to keep `maquette design` as a real subcommand
  (surprise #1).
- **`allow_indirect_imports`** on the `cli` import contract (surprise #4).
- **Render-independent `--help` test** via Click introspection
  (surprise #2).

## Recommended changes for next phase

Phase-3.5 is **smoke + 3 reference examples** — manual FreeCAD
verification; **v0 ships at the end of it**.

1. **Run all 3 reference prompts via the CLI end-to-end** and open each
   STEP in FreeCAD: cube-with-hole, cylinder-with-chamfer, L-bracket.
   The L-bracket is the one to watch — it exercises the extras path
   (ADR-0004 export fix + the few-shot fix from phase-2b). Confirm the
   geometry *visually matches*, not just that a STEP is produced.
2. **Measure N1 (latency p95) and N2 (cost/run) formally.** Phase-2b's
   single live run was 10.1 s / $0.0267 — indicative, not a p95. Phase-3.5
   should record latency + cost per prompt (the MAX in the roadmap
   suggests ~10 runs per prompt for p95).
3. **Packaging note for prompts/.** The CLI loads `prompts/planner.system.md`
   via `parents[2]` (repo-relative) — works for an editable install /
   clone, which is the v0 distribution. A non-editable install would not
   bundle `prompts/`; revisit if/when v0 is packaged for PyPI (out of v0
   scope).
4. **Optional: pin `rich`** if `--help`/console rendering is ever tested
   on output again — but the current introspection test sidesteps it.
5. **`--max-iter` is recorded but inert in v0** (single-pass). It becomes
   live in phase-4 (v0.1 evaluator/refine loop); no action for 3.5.
