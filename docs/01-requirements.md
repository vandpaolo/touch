# 01 — Requirements

> *Synthesized from `notes/inbox.md` (migrated vault content: 05-cli-and-io.md,
> 01-architecture.md NFR section, 03-agent-loop.md failure modes) and
> `docs/00-vision.md` on 2026-05-16. Revised same day per `/pm-requirements`
> answers (see `notes/decisions.md` 2026-05-16). Update via `/pm-requirements`.*

This document covers **v0 only**. v0.1 and v0.2 requirements live in
`03-roadmap.md` (per decision P5). Priority field uses must / should / could.

## Functional requirements

### Core flow

| ID | Requirement | Acceptance criterion | Priority |
|----|-------------|---------------------|----------|
| F1 | The CLI accepts a natural-language prompt via `maquette design "<prompt>"` | Running with a valid prompt and `ANTHROPIC_API_KEY` set creates a run directory and exits 0 on success | must |
| F2 | A Planner call converts the prompt to a validated `Intent` (pydantic) | The resulting `intent.json` parses cleanly against the `Intent` schema; invalid LLM output triggers one retry before failing exit 10 | must |
| F3 | A Worker emits build123d Python from the `Intent` via the build123d adapter | The adapter is a pure function `Intent → str`; emits byte-identical code for the same Intent across runs | must |
| F4 | The build123d adapter supports the full v0 Intent schema | All 6 PrimaryKinds (box, cylinder, sphere, extrude, revolve, loft) and all 5 ModifierKinds (hole, fillet, chamfer, shell, pattern) compile to valid build123d code with snapshot fixtures per kind | must |
| F5 | An Executor runs the worker's code in a subprocess and produces a STEP file | `output/<run-id>/part.step` exists, is > 0 bytes, and (per the v0 success criterion) **a human reviewer confirms the geometry matches the prompt description — within the v0 capability bound** (vision § capability bound: schema-native geometry + the `extras` relief valve; *not* edge-specific selection or oriented multi-face holes). STEP non-emptiness is the automatable bar; geometric correctness is human-verified in v0 (Evaluator is v0.1) | must |
| F6 | A dimension sanity check runs after planner output | Numeric dimensions present in the prompt (regex match for patterns like `"50 mm"`, `"20mm"`, `"60 × 40"`) are compared against `Intent.parameters` and feature params. Mismatches log a `DIMENSION_WARNING` entry to `trace.jsonl` and a `warnings` array entry in `status.json`. Does **not** fail the run — it's a visibility signal, not a hard gate | must |
| F7 | A Renderer produces three orthographic PNG views (front, side, top) | `output/<run-id>/renders/{front,side,top}.png` exist as valid PNGs on success. Renderer failure does NOT block exit 0 — STEP is the primary artefact; renders are marked missing in `status.json` and the run continues | should |
| F8 | Each generation lives in `output/<run-id>/` with the artefact set | Folder contains: `prompt.txt`, `intent.json`, `code.py`, `part.step`, `renders/`, `trace.jsonl`, `status.json` (and `error.json` on failure) | must |
| F9 | `status.json` records final state and full cost accounting | JSON contains: `status`, `exit_code`, `started_at`, `finished_at`, `duration_s`, `iterations`, `tokens.{input,output,cache_read,cache_creation}`, `cost_usd_estimate`, `warnings[]`, `artefacts.{...}`. Cost is computed via `maquette/pricing.py` × actual SDK-reported tokens (no approximation). When the SDK exposes a cost field directly, use that as authoritative and fall back to the local calculation | must |
| F10 | `trace.jsonl` logs every state transition with a timestamp | One JSON object per line; `step` values match the state machine (`PROMPT_RECEIVED`, `PLANNING`, `CODE_EMITTING`, `EXECUTING`, …); per-LLM-call entries include `tokens_in`, `tokens_out`, `cache_read_tokens`, `cache_creation_tokens` | must |
| F11 | `run-id` format: `<UTC-ISO timestamp with - separators>__<intent.name slugified>` | Example: `2026-05-12T14-32-08__cube_with_hole`; sortable, unique per second | must |
| F12 | The CLI prints the run directory path on every exit (success or failure) | stdout/stderr contains the absolute or relative run dir path | must |
| F13 | Exit codes follow the documented table | `0` success; `1` generic failure; `2` bad CLI args; `10` planner failed; `11` adapter refused; `12` executor failed (subprocess crash / no STEP); `13` executor timed out. (Exit code `14` is reserved for v0.1 evaluator failures — not used in v0.) | must |
| F14 | CLI flags supported: `--out <path>`, `--max-iter N` (default 1 in v0), `--exec-timeout S` (default 30), `--model <id>`, `-q`/`-v` | Flag values override pyproject defaults; `-q` suppresses everything except final run path; `-v` adds per-LLM-call summaries to stderr | must |

### Deferred from v0 (recorded for traceability)

The following were drafted into the previous `01-requirements.md` revision
and have been deferred to v0.1 or later. They will be planned in
`03-roadmap.md` and detailed in their owning version's requirements doc
when that version is being shaped.

- **Supporting CLI commands** (deferred to v0.1 per probe P2): `maquette
  inspect <run-id>`, `maquette list`, `maquette replay <run-id>`. The v0
  user can still inspect a run by reading `status.json` and `trace.jsonl`
  directly.
- **NX Open adapter and related CLI flags** (deferred to v0.1 per vision
  push-back B1, conflict C1): NX journal emission, `--no-nx` / `--only-nx`
  flags, NX-import CI guard.
- **Vision-LLM Evaluator + refinement loop** (v0.1): vision critique,
  refinement iterations, `critiques.jsonl`, isometric render, `--max-iter`
  default of 3, exit code 14.
- **Sandboxing beyond the subprocess timeout** (deferred to v0.1 per probe
  P3): import guards, network restrictions, filesystem restrictions on the
  generated build123d code. v0 trusts the LLM not to emit destructive code
  (acceptable risk for personal-tool use).
- **Conversational mode and parameter resliders** (v0.2): `maquette
  converse`, `maquette tweak`, session-file persistence.
- **Edge-specific selection + oriented/multi-face hole placement**
  (early v0.1, schema-v2): chamfer/fillet a named edge; place a hole on
  a chosen face/axis. Surfaced by the phase-3.5 blocker
  (`blockers/2026-05-28-v0-references-exceed-schema.md`); to be
  sequenced near the front of v0.1 alongside the Evaluator in
  `03-roadmap.md`.

## Non-functional requirements

| ID | NFR | Target | Verification |
|----|-----|--------|--------------|
| N1 | Single-shot latency (prompt → STEP) | < **20 s** p95 on a simple part for v0 (tightened from 30 s now that NX emission is deferred to v0.1) | Smoke test on the 2 hard-gate references (cube, cylinder — vision § Success criteria); assert wall-clock < 20 s; record p95 across ≥ 10 runs per prompt. The L-bracket showcase is measured too but is best-effort, not gating |
| N2 | LLM cost per generation | < $0.10 on a simple part. **No cost cap behaviour in v0** — overruns are recorded in `status.json.cost_usd_estimate` and the run continues to completion (per gap G2). Cost cap behaviour deferred to v0.1+ if it becomes a real problem | `trace.jsonl` token counts × `maquette/pricing.py` table; assert per-run estimate < $0.10 on the 2 hard-gate references; track actual SDK-reported usage |
| N3 | Adapter determinism | Same `Intent` → byte-identical emitted code | Snapshot tests: emit twice, diff must be empty; CI fails on drift; one fixture per supported kind (11 total per N3 ↔ F4) |
| N4 | Repo hygiene around NX (all milestones, not just v0) | Zero NX imports in `src/` (ever) | CI guard: `grep -r "^import NXOpen\|^from NXOpen" src/` returns nothing |
| N5 | Headless execution | Runs on a Linux server without a display | Smoke test in headless env (no `DISPLAY`); PyVista off-screen + build123d headless |
| N6 | Graceful failure | Executor crash produces a structured `error.json` in the run folder, not a Python traceback to the user | Chaos test: emit deliberately broken code; assert `error.json` present, exit 12, no traceback on stdout |
| N7 | Reproducibility | A future `maquette replay` (v0.1) will produce byte-identical `code.py` from `intent.json` + same maquette version. In v0, the property is verified by re-running the adapter directly on a saved `intent.json` | Test: load a saved `intent.json`, call adapter, diff against committed `code.py` |
| N8 | Secret hygiene | `ANTHROPIC_API_KEY` never logged, never committed | Scan stdout/stderr/trace.jsonl for the env var value; git pre-commit check; `.env` in `.gitignore` |
| N9 | Subprocess timeout enforced | 30 s default kills runaway build123d code without leaving zombie processes | Test with infinite-loop generated code; assert subprocess killed within timeout + 2 s grace |
| N10 | Self-contained run folder | Each `output/<run-id>/` is the complete record of a run; no log files outside it | `ls output/<run-id>` after a run shows all artefacts; no auxiliary log files in repo root or `/tmp` |

## User stories

- **US1** — As the author, I want to type a one-sentence part description and get a STEP file in under 20 s, so I can sketch geometry faster than authoring in CAD by hand.
- **US2** — As a FreeCAD user, I want the produced STEP to open cleanly in FreeCAD with the described geometry, so I can finish the engineering in my preferred tool.
- **US3** — As the author, I want a visible warning when the system might have produced geometry that doesn't match my prompt (dimension sanity check), so I can decide whether to trust the output before opening it in CAD.

(Deferred to v0.1+ user stories: NX seat handoff, auto-refinement on
visual mismatch, run inspection commands. Parameter tweaking is v0.2.)

## User flows

### v0 happy path

```mermaid
sequenceDiagram
    actor User
    participant CLI as maquette.cli
    participant Loop as agent.loop
    participant Planner
    participant Sanity as dimension sanity
    participant Worker
    participant Adapter as build123d_target
    participant Exec as agent.executor
    participant Sub as subprocess
    participant Render as render.orthographic
    participant FS as output/<run-id>/

    User->>CLI: maquette design "<prompt>"
    CLI->>Loop: run(prompt)
    Loop->>FS: mkdir, write prompt.txt
    Loop->>Planner: prompt → Intent
    Planner-->>Loop: Intent (validated)
    Loop->>Sanity: check(prompt, Intent)
    Sanity-->>Loop: ok | warnings[]
    Loop->>FS: write intent.json
    Loop->>Worker: emit(Intent)
    Worker->>Adapter: emit(Intent)
    Adapter-->>Worker: code (str)
    Worker-->>Loop: code.py
    Loop->>FS: write code.py
    Loop->>Exec: execute(code.py)
    Exec->>Sub: spawn(python code.py)
    Sub-->>Exec: STEP file
    Exec->>Render: orthographic(STEP)
    Render-->>Exec: 3 PNGs (or marked missing)
    Exec-->>Loop: result
    Loop->>FS: write part.step, renders/*.png, status.json
    Loop-->>CLI: result summary
    CLI-->>User: print run dir + exit 0
```

### v0 failure path — planner emits invalid Intent

```mermaid
sequenceDiagram
    actor User
    participant CLI as maquette.cli
    participant Loop as agent.loop
    participant Planner
    participant FS as output/<run-id>/

    User->>CLI: maquette design "<prompt>"
    CLI->>Loop: run(prompt)
    Loop->>Planner: prompt → Intent (attempt 1)
    Planner-->>Loop: invalid JSON / schema fail
    Loop->>Planner: retry with stricter prompt (attempt 2)
    Planner-->>Loop: invalid again
    Loop->>FS: write error.json, status.json {status: fail, exit_code: 10}
    Loop-->>CLI: planner exhausted
    CLI-->>User: print run dir + exit 10
```

### v0 failure path — executor timeout

```mermaid
sequenceDiagram
    actor User
    participant CLI as maquette.cli
    participant Loop as agent.loop
    participant Exec as agent.executor
    participant Sub as subprocess
    participant FS as output/<run-id>/

    User->>CLI: maquette design "<prompt>"
    CLI->>Loop: run(prompt)
    Note over Loop: ...(plan, sanity, emit OK)...
    Loop->>Exec: execute(code.py, timeout=30)
    Exec->>Sub: spawn(python code.py)
    Note over Sub: runs > 30 s
    Exec->>Sub: SIGKILL
    Exec-->>Loop: TimeoutError
    Loop->>FS: write error.json, status.json {status: fail, exit_code: 13}
    Loop-->>CLI: executor timed out
    CLI-->>User: print run dir + exit 13
```

## Constraints & assumptions

### Constraints (cannot change)

- **Python 3.11+** required (build123d, PyVista, anthropic SDK all target 3.11+).
- **`ANTHROPIC_API_KEY`** must be present in environment (via `.env` or shell).
- **`src/` must never import `NXOpen`** (CI-enforced, all milestones). The
  NX adapter (v0.1) emits NX code as text against the public API only.
- **No web UI, no daemon, no REST API in v0.** Filesystem-as-state is the
  only state mechanism; the CLI is the only entry point.
- **No recorded NX journals from licensed sessions** anywhere in the repo,
  ever. The NX adapter is written from the public NX Open API docs only.
- **v0 Intent schema = 6 PrimaryKinds + 5 ModifierKinds** (per gap G3).
  The build123d adapter must compile all 11 to valid code.
- **v0 capability bound** (vision § capability bound): v0 commits to
  geometry expressible in the schema (6 + 5) **plus the `extras` relief
  valve** for compound shapes the schema can't name. v0 does **not**
  support edge-specific chamfer/fillet selection (e.g. "the top edge")
  or oriented/multi-face hole placement (e.g. "a hole in *each flange*").
  `extras` is **best-effort** — un-guarded LLM-written code, no
  correctness check until the v0.1 Evaluator. Reference prompts + the
  ship gate stay inside this bound (the L-bracket is a best-effort
  showcase, not a hard gate).

### Assumptions (chosen, may revise)

- **LLM consistency.** Claude is reliable enough at structured outputs to
  validate against pydantic on the first or second attempt for v0 prompts.
  If a retry budget of 1 proves insufficient, raise to 2 and file an open
  question.
- **build123d / OCP stability.** The build123d API does not break between
  v0 development and v0 release. Snapshot tests are pinned to the version
  locked in `pyproject.toml`.
- **PyVista headless rendering of STEP.** PyVista can load STEP (via OCP)
  and render off-screen on a headless Linux box. Verified on nexus.
- **Subprocess sandboxing is sufficient for v0.** The author trusts the
  LLM not to emit destructive code; strict sandboxing is v0.1+ work
  (per probe P3).
- **FreeCAD 1.x opens STEP cleanly.** Required for the v0 success-criterion
  verification.
- **Dimension sanity check is best-effort, not bulletproof.** Regex
  extraction misses written-out numerals ("fifty millimetres"), unit
  inference is naive, and derived dimensions ("centred" implies half-the-size
  coordinates) can produce false positives. The check is a *warning signal*,
  not a hard gate (per F6).

## Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Planner emits invalid JSON | med | med | Retry once with stricter prompt; fail exit 10. Schema is small + explicit in system prompt to keep error rate low |
| R2 | Intent fails schema validation | med | med | Retry once with validation error injected into user message; fail exit 10 |
| R3 | Adapter refuses Intent (unsupported kind) | low | low | F4 requires full schema coverage in v0, so this becomes a programming error rather than a runtime path. Structured `AdapterRefusal` → exit 11 |
| R4 | Subprocess crashes / no STEP produced | low | high | Capture stderr in `error.json`; exit 12 |
| R5 | Subprocess times out | low | med | Hard 30 s default; SIGKILL; write `error.json`; exit 13 |
| R6 | Renderer fails | low | low | Keep STEP, mark renders missing in `status.json`, continue at exit 0 |
| R7 | **Silent semantic failure** (geometry doesn't match prompt) | **high** | **high** | **Materialised in phase-3.5** (blocker `2026-05-28-v0-references-exceed-schema`): the cylinder "top edge" + L-bracket "each flange" references demanded geometry past the v0 capability bound, routed to fragile `extras`. v0 mitigation: (a) reference prompts + ship gate restricted to schema-native geometry (cube, cylinder); (b) F6 dimension check warns; (c) `extras` is explicitly best-effort/un-guarded (the L-bracket is a showcase, not a gate). Proper fix = **early v0.1**: vision-LLM Evaluator + schema-v2 first-class edge selection & hole positioning |
| R8 | Cost overrun on real prompts (above $0.10) | med | med | No cost cap in v0 (per G2). Cost is recorded accurately in `status.json` and surfaces in `maquette list` (v0.1) so overruns are visible. Cap behaviour added in v0.1+ if needed |
| R9 | build123d API churn breaks adapter | low | med | Snapshot tests (one per kind) pin adapter output to a build123d version; regression CI catches drift |
| R10 | LLM cost exceeds $0.10 on the demo cube (vision success criterion miss) | low | high | Prompt-cache the planner system prompt + few-shots (Anthropic prompt caching); tight schema keeps output tokens small. Re-evaluate at first end-to-end run |
| R11 | Dimension sanity check produces too many false positives | med | low | Tune regex patterns iteratively; provide `--no-sanity` flag (v0.1) if needed. v0 accepts the noise as a visibility cost |
