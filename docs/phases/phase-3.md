---
id: phase-3
title: CLI
status: in_progress       # flipped 2026-05-28 via /pm-phase-start
started: 2026-05-28        # ISO date when flipped to in_progress
finished: null            # ISO date when flipped to done
min_goal_met: null        # true | false | null
max_goal_met: null        # true | false | null
blocker: null             # path to blocker doc if status = blocked
depends_on: [phase-2b]
audit: audits/2026-05-28-pre-phase-3.md
---

# Phase 3 — CLI

> *Drafted via `/pm-phase-plan` on 2026-05-28. Update via `/pm-phase-plan`
> before `/pm-phase-start`; once `in_progress`, scope is frozen.*

- **Goal:** `maquette design "<prompt>"` is the only public entry point
  and behaves per requirements **F1**, **F12**, **F13**, **F14** (and
  surfaces F11's run-id). The CLI is a thin shell over `Loop.run` — it
  parses flags into a `Config`, derives a `RunConfig`, constructs the
  Anthropic client + `PromptsBundle`, runs the loop, prints the run dir,
  and maps the run's outcome to a process exit code. **No new domain
  logic** lives here.
- **Depends on:** [`phase-2b`](phase-2b.md) (`status: done`); requirements
  F1, F12, F13, F14 approved; architecture § Layered responsibilities
  (`cli` row) + `02-classes.md` § Module map (`maquette.cli`) approved;
  `config.Config` (phase-0) + `agent.loop.Loop`/`RunConfig` (phase-2b)
  in place.
- **Estimated duration:** 2 days min + 1 day max (= 3 units of work).
  Roadmap gantt shows 2d.

## Policies locked for this phase

- **CLI is a thin shell (no domain logic).** Per `02-classes.md`, `cli`
  owns Typer commands, argument parsing, and glue — nothing else. It
  imports `agent.loop` + `config` + `typer` and calls `Loop.run`.
- **Outcome comes from `status.json`, not a return value.** `Loop.run`
  returns the run dir (a `Path`); the CLI reads `status.json["exit_code"]`
  from it and calls `sys.exit(code)`. The loop already computed the F13
  code; the CLI does not re-derive it.
- **Print the run dir on every exit (F12).** Success or failure, the CLI
  prints the run directory path to stdout as the last line (`-q` still
  prints this — it is the one thing `-q` does not suppress).
- **Exit-code table (F13):** `0` success · `1` generic/unexpected · `2`
  bad CLI args (Typer/Click usage errors already exit 2) · `10` planner ·
  `11` adapter · `12` executor · `13` timeout. `14` is reserved (v0.1).
- **Flag → Config field mapping (F14):** `--out → out_root`,
  `--max-iter → max_iterations`, `--exec-timeout → exec_timeout_s`,
  `--model → model`, `-q/-v → verbosity`. Flags become `cli_overrides`
  passed to `Config.load(...)` (precedence CLI > env > pyproject >
  defaults, already implemented). `RunConfig` is derived from the merged
  `Config`.
- **Secret hygiene (N8).** `ANTHROPIC_API_KEY` is read only by the
  Anthropic client (from env/`.env`); the CLI never logs it. Missing key
  fails fast with a clear message (see P3-R1), not a raw traceback.
- **Testing.** Typer's `CliRunner` drives the command; `Loop` is
  monkeypatched (no real API, no subprocess) so tests assert flag
  parsing, Config precedence, run-dir printing, and exit-code mapping for
  every documented path. No live API in the default suite.

## Minimum deliverable

Phase-3 ships when **all** of the following exist and pass their tests:

- `src/maquette/agent/loop.py` — harden `_plan` (P3-Q1): catch broad
  Anthropic API errors (auth/rate-limit/network), not just
  `PlannerExhausted`, and map them to a `PLANNING_FAILED` / exit 10 with
  `error.json`, so every invocation yields a complete run folder. A
  loop test covers an injected API error → exit 10 + run folder.
- `src/maquette/cli.py` — a Typer app with a `design` subcommand:
    - Signature: `design(prompt: str, out, max_iter, exec_timeout, model,
      quiet, verbose)` with the F14 flags (`--out`, `--max-iter`,
      `--exec-timeout`, `--model`, `-q/--quiet`, `-v/--verbose`).
    - Builds `Config.load(cli_overrides=…)` from the flags, derives a
      `RunConfig`, constructs `Anthropic()` + a `PromptsBundle` loaded
      from `prompts/planner.system.md`, and calls
      `Loop(out_root, cfg, client, prompts).run(prompt)`.
    - Reads `status.json["exit_code"]` from the returned run dir, prints
      the run dir path (F12), and `raise typer.Exit(code)` (F13).
    - Fails fast with a clear message + exit 1 when `ANTHROPIC_API_KEY`
      is absent, and wraps unexpected exceptions → exit 1 (no traceback
      to stdout).
    - A console-script entry point `maquette = "maquette.cli:app"` in
      `pyproject.toml`.
- `[tool.importlinter]` contract: `maquette.cli` may import `agent.loop`,
  `config`, `typer`, stdlib (not `agent.planner`/`sanity`/`worker`/
  `executor`/`adapters`/`render`/`intent*` directly — it goes through
  the loop).
- `[tool.coverage.report] include` extended for `src/maquette/cli.py`.
- `tests/test_cli.py` (Typer `CliRunner`, `Loop` monkeypatched):
    - Happy path: `design "<prompt>"` → exit 0, run dir printed.
    - Exit-code mapping: a monkeypatched loop that writes
      `status.json.exit_code` of 10/11/12/13 → CLI exits with the same
      code, run dir still printed (F12).
    - Flag precedence: `--out`, `--max-iter`, `--exec-timeout`, `--model`
      land in the `Config`/`RunConfig` the loop receives.
    - Missing `ANTHROPIC_API_KEY` → exit 1 with a clear message.
    - Bad args (e.g. `--max-iter abc`) → exit 2 (Typer usage error).
- `README.md` — install (including the **`vtk-osmesa` swap**, carry-forward
  #1 from phase-2b: stock `vtk` segfaults headless), `.env` setup, a
  `maquette design "…"` usage example, the F13 exit-code table, and where
  the run folder lands.

## Maximum deliverable

If everything above lands cleanly, also:

- **`-v` verbose mode** prints a per-LLM-call summary to **stderr**
  (tokens in/out from the `PLANNING` event(s) in `trace.jsonl`), and a
  one-line-per-state-transition human log; **`-q`** suppresses everything
  except the final run-dir line. Covered by `CliRunner` tests asserting
  stdout/stderr content under each verbosity.
- **`--help` completeness** — every flag has help text; a test asserts
  each flag name appears in `design --help` output.
- **Argument-validation edge tests** — empty prompt, negative
  `--max-iter`, non-existent `--out` parent (created vs error), unknown
  `--model` (passes through; cost falls back to 0 per phase-2b loop).

## Sprint / day breakdown

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Harden `loop._plan` for API errors (P3-Q1) + `cli.py` `design` command + flag→Config wiring + exit-code mapping + import-linter contract + entry point | `loop._plan` catches Anthropic API errors → exit 10 + `error.json` (+ a loop test); `src/maquette/cli.py` (Typer `design`; F14 flags → `Config.load` cli_overrides → `RunConfig`; builds `Anthropic()` + `PromptsBundle`; calls `Loop.run`; reads `status.json.exit_code`; prints run dir F12; `typer.Exit` F13; missing-key → exit 1); `[project.scripts] maquette`; `[tool.importlinter]` `cli` contract | injected API error → exit 10 + complete run folder; `maquette design --help` lists all 5 flags; with a monkeypatched `Loop`, `design "x"` exits 0 and prints the run dir; `lint-imports` keeps the new `cli` contract |
| 2 | `tests/test_cli.py` + `README.md` | `tests/test_cli.py` (CliRunner, monkeypatched `Loop`: happy path, exit-code mapping 10/11/12/13 + F12 print, flag precedence into Config/RunConfig, missing-key→1, bad-arg→2); `README.md` (install incl. vtk-osmesa swap, `.env`, usage example, F13 exit-code table, run-folder location) | All CLI tests pass; each documented exit path asserted; README documents the vtk-osmesa swap and a runnable `maquette design "…"` example |
| 3 (MAX) | Verbosity + `--help` coverage + arg-validation edges | `-v` → per-LLM-call tokens + transition log to stderr; `-q` → only the run-dir line on stdout; `--help` text per flag; extra CliRunner tests (empty prompt, negative `--max-iter`, unknown `--model`, `-q`/`-v` output shape) | `-q` run prints exactly the run dir on stdout; `-v` run shows per-call tokens on stderr; `design --help` contains every flag; edge tests pass |

## Exit criteria

Phase-3 is `done` when **all** of the following hold:

1. `pyright src/` exits 0.
2. `maquette design "a 50 mm cube with a 20 mm hole through the centre"`
   from a fresh shell (real `ANTHROPIC_API_KEY`) produces a run folder,
   prints its path (F12), and exits 0 (F1).
3. Each documented failure path returns its F13 code: bad args → 2;
   missing key → 1; an Anthropic API error during planning → 10 with a
   complete run folder (P3-Q1); and the loop-sourced 10/11/12/13 map
   through (verified via monkeypatched `Loop` in tests).
4. `lint-imports` reports all contracts kept, 0 broken (9 from phase-2b +
   `cli` = 10).
5. `pytest -q` passes; coverage on `cli` ≥ 80%.
6. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing.
7. `README.md` documents install (incl. the vtk-osmesa swap), `.env`
   setup, a usage example, and the exit-code table.
8. CI green on the most recent push to `main`.
9. `phases/phase-3-report.md` exists (via `/pm-phase-report`).

## Known risks for this phase

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| P3-R1 | Missing `ANTHROPIC_API_KEY` surfaces as an ugly Anthropic `APIError`/traceback mid-run instead of a clean message | high | med | CLI checks `os.environ.get("ANTHROPIC_API_KEY")` before constructing the client; if absent, print a one-line error to stderr and exit 1. No key value ever logged (N8). |
| P3-R2 | `Loop.run` could raise (auth/network `APIError`) **before** writing `status.json`, leaving the CLI with no run dir + no exit code | med | high | **Resolved (P3-Q1, 2026-05-28): harden the loop.** `loop._plan` catches broad Anthropic API errors (not just `PlannerExhausted`) and maps them to a planner failure (exit 10 + `error.json`) so **every** invocation yields a complete run folder (F8/F12/N10). The CLI then always has a dir to print and a status to read; it still wraps `Loop.run` as a backstop → exit 1 on anything truly unexpected. |
| P3-R3 | Typer/Click default usage-error exit code may not be exactly `2` as F13 requires | low | low | Verify with a `CliRunner` bad-arg test; Click uses `2` for `UsageError` by default. If it differs, set it explicitly. |
| P3-R4 | `-v` needs per-LLM-call tokens, which live in `trace.jsonl` (`PLANNING` events), not the aggregate `status.json` | low | low | `-v` reads `trace.jsonl` after the run and prints the per-`PLANNING` token fields. MAX-only; if fiddly, fall back to printing the aggregate `status.json.tokens`. |
| P3-R5 | README omits the `vtk-osmesa` swap → a fresh `pip install -e .` segfaults on first render and the user is stuck | med | med | The install section leads with the swap (carry-forward #1). A "smoke" usage example notes the renders step needs it. |
| P3-R6 | Flag→Config key mismatch (`--out` vs `out_root`, etc.) silently drops overrides | med | med | The `design` function maps each flag to its exact `Config` field name in `cli_overrides`; a flag-precedence test asserts each value reaches the `RunConfig` the loop receives. |
| P3-R7 | `Config` has `out_root`/`verbosity` but `RunConfig` has `exec_timeout_s`/`sanity_enabled`/token caps — deriving one from the other can drop or misname fields | med | low | Write one explicit `_runconfig_from(config)` mapping with a test; do not rely on field-name coincidence. `out_root` is a `Loop` constructor arg, not a `RunConfig` field. |

## Notes for `/pm-phase-start`

When `/pm-phase-start` runs, the Auditor sub-agent should verify:

- F1 (design command), F12 (prints run dir), F13 (exit codes), F14 (flags)
  each have a task: all on Day 1 (impl) + Day 2 (tests).
- N8 (secret hygiene) — Day 1 missing-key handling; no key logged.
- The CLI is the **only** new `src/` module this phase. The one in-place
  change to an existing module is the P3-Q1 `loop._plan` hardening
  (catch Anthropic API errors → exit 10); the audit should expect this
  edit to `agent/loop.py` and its accompanying test.
- Glossary leaves were closed in phase-2b; no glossary FAIL expected.
- README is a phase-3 MIN deliverable (first time the project ships one
  with real usage content).

After audit passes, `/pm-phase-start` flips this file's `status: planned`
→ `status: in_progress`, sets `started: 2026-MM-DD`, and updates
[`03-roadmap.md`](../03-roadmap.md) frontmatter `active_phase: phase-3`.
Scope-freeze applies from that point.
