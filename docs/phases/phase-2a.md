---
id: phase-2a
title: Pipeline (LLM-facing half)
status: done              # flipped 2026-05-28 via /pm-phase-report
started: 2026-05-18       # ISO date when flipped to in_progress
finished: 2026-05-28      # ISO date when flipped to done
min_goal_met: true        # true | false | null
max_goal_met: true        # true | false | null
blocker: null             # path to blocker doc if status = blocked
depends_on: [phase-1]
audit: audits/2026-05-18-pre-phase-2a-v2.md
---

# Phase 2a — Pipeline (LLM-facing half)

> *Drafted via `/pm-phase-plan` on 2026-05-18. Update via `/pm-phase-plan`
> before `/pm-phase-start`; once `in_progress`, scope is frozen.*

- **Goal:** Prompt → validated `Intent` + sanity warnings, with the
  Worker shim ready to call the (phase-1) build123d adapter. Closes
  F2 (Planner → Intent), F3 (Worker emits via adapter — adapter
  shipped in phase-1, this phase wires the worker shim), F6 (sanity
  check). Partial F9/F10 (token counts captured in `PlanResult`;
  full `trace.jsonl` / `status.json` plumbing lands in phase-2b).
- **Depends on:** [`phase-1`](phase-1.md) (`status: done`); requirements
  F2, F3, F6, F9, F10 approved; architecture § Layered responsibilities
  (`agent.planner`, `agent.sanity`, `agent.worker` rows) approved;
  [ADR 0001](../adr/0001-intent-as-pivot.md), [ADR 0002](../adr/0002-dimension-sanity-check.md),
  [ADR 0003](../adr/0003-prompt-caching-for-cost.md) accepted.
- **Estimated duration:** 3 days.

## Policies locked for this phase

- **Hole-positioning carry-forward (per
  [`phase-1-report.md`](phase-1-report.md) surprise #2 + recommendation
  #2):** the planner system prompt instructs the LLM to route off-centre
  hole positions through `Intent.extras`, not through ad-hoc `params`
  keys. This keeps v0 schema stable, uses the documented escape hatch
  as designed (vision § escape hatch), and defers a schema bump
  (which would be a `/pm-blocker`-driven decision) until v0 reference
  prompts actually require it. Cube-with-hole works as-is; L-bracket
  scenarios use extras.
- **L-bracket / non-primitive shapes (per
  [`phase-1-report.md`](phase-1-report.md) surprise #3):** the planner
  system prompt teaches the LLM that v0 has no `union` modifier and
  no L-shape primary; complex shapes go in `extras` as raw build123d
  source. Phase-1's L-bracket round-trip used a single-plate
  approximation; phase-2a's planner can do better by emitting `extras`
  with the actual L-geometry as build123d code.
- **Coarse edge-selection (per
  [`phase-1-report.md`](phase-1-report.md) surprise #4):** planner is
  told that `fillet`/`chamfer` modifiers chamfer/fillet all edges of
  the target — if the prompt says "top edge only," the planner emits
  `extras` with explicit edge selection. Schema-v2 candidate; not
  fixed here.
- **Sanity-check tolerance:** **±1% or ±0.5 mm, whichever is larger**
  (locked by [ADR 0002](../adr/0002-dimension-sanity-check.md) § Decision item 4).
  Implemented in `agent.sanity`. Referenced from the module's
  docstring so future readers find the ADR without grep.
- **Testing strategy for LLM-dependent code:**
    - **Unit tests use a mocked Anthropic client** (`unittest.mock` patching
      `client.messages.create`). No network, no API key, fast. Bulk of
      tests live here.
    - **Live integration smoke is gated** via
      `pytest.skipif(os.environ.get("ANTHROPIC_API_KEY") is None,
      reason="no API key")`. Runs against real API; one test per v0
      reference prompt; **kept out of the default CI matrix** (no
      `ANTHROPIC_API_KEY` secret in CI yet — phase 3.5 decision).
      Locally the user can run `pytest -m live` (or similar) to
      exercise these on demand.
- **System prompt versioning:** `prompts/planner.system.md` is the
  canonical planner system prompt; hashing (single rolled-up SHA-256
  of `prompts/` directory) is implemented in phase-2b's `agent.loop`,
  per ADR 0003. Phase-2a only ships the file content.
- **Anthropic prompt caching shape** (per ADR 0003): system prompt
  passes as `[{"type": "text", "text": ..., "cache_control":
  {"type": "ephemeral"}}]`. Tested via mock-client assertion that
  the call kwargs include `cache_control`. **Pre-phase verification
  (2026-05-18):** ADR 0003's shape verified against `anthropic==0.102.0`
  by direct SDK introspection — `TextBlockParam` carries
  `cache_control: Optional[CacheControlEphemeralParam]` (per-block,
  matches the ADR). `Usage` fields `input_tokens`, `output_tokens`,
  `cache_read_input_tokens`, `cache_creation_input_tokens` map to
  our `Tokens` dataclass via `getattr(...)`. P2a-R1 + P2a-R5 closed
  before phase start; no `/pm-blocker` filed. (Two additive SDK
  changes noted but not affecting ADR shape: a new request-level
  `cache_control` kwarg alternative, and a `ttl: Literal["5m","1h"]`
  field on `CacheControlEphemeralParam`. Default is still 5m.)

## Minimum deliverable

Phase-2a ships when **all** of the following exist and pass their tests:

- `src/maquette/agent/sanity.py` — `Dimension` value object;
  `DimensionMismatch` value object; `SanityResult` dataclass
  (`{ok: bool, warnings: list[str], mismatches: list[DimensionMismatch]}`);
  `check(prompt: str, intent: Intent) -> SanityResult` with regex
  extraction + ±1%/±0.5 mm tolerance comparison. Pure module: no
  LLM calls, no I/O.
- `src/maquette/agent/planner.py` — `PlanResult` dataclass
  (`{intent: Intent, tokens: Tokens, retries: int}`);
  `plan(client, prompt, model, prompts) -> PlanResult`. Implements:
    - Anthropic prompt-caching call shape per ADR 0003.
    - Token-class mapping: SDK `response.usage` fields →
      `maquette.pricing.Tokens` (`input`, `output`, `cache_read`,
      `cache_creation`).
    - JSON extraction from response text (handles raw JSON, JSON
      inside fenced code block, JSON inside prose).
    - One retry on pydantic `ValidationError` with a stricter
      "your previous output failed schema validation: <error>"
      addendum to the user prompt. Total ≤ 2 LLM calls per `plan()`
      invocation.
    - `AdapterRefusal` is **not** raised by planner — only by
      adapters. Planner raises `PlannerExhausted` (new exception in
      this module) if both attempts fail validation.
- `prompts/planner.system.md` — initial system prompt with:
    - The `Intent` schema (Unit, PrimaryKind, ModifierKind, Parameter,
      PrimaryFeature, Modifier, Intent).
    - Per-kind contract tables (the 11 kinds + their required params).
    - Cube-with-hole few-shot (Intent JSON for `02-data-model.md`
      § Example).
    - v0 schema-gap guidance: hole positioning routes through
      `extras`; complex shapes (L-bracket, etc.) go in `extras`;
      edge selection beyond "all edges" goes in `extras`.
    - Output requirement: emit valid JSON only (no prose; no code
      fences unless the LLM can't help itself, in which case the
      JSON-extraction layer handles it).
- `src/maquette/agent/worker.py` — module-level
  `emit_code(intent: Intent) -> str` delegating to
  `maquette.adapters.build123d_target.emit`. Phase-1 already validated
  the build123d adapter; worker is a thin selection shim for v0
  (only one adapter). `emit_journal(intent)` is **stubbed** in this
  phase, with a `NotImplementedError("v0.1")` body, to surface the
  v0.1 surface area in the public API without exercising it.
- `tests/test_sanity.py` — ≥ 8 tests covering:
    - Single dimension match (positive case).
    - Single dimension mismatch (tolerance edge: just-inside vs
      just-outside ±0.5 mm and ±1%).
    - Multiple-axis prompts (e.g. `60 × 40 × 5 mm`) — extraction
      finds all three.
    - Unit-aware comparison (50 mm vs 5 cm → match).
    - Empty prompt (no extracted dims → `ok = True`).
    - Empty intent (no params → `ok = True`).
- `tests/test_planner.py` — ≥ 6 tests with mocked Anthropic client:
    - Plain JSON response → valid `Intent` + correct `Tokens` mapping.
    - JSON in fenced code block → extracted correctly.
    - Schema-fail first attempt → retry → success on second attempt
      (`retries == 1`).
    - Two consecutive schema fails → `PlannerExhausted` raised after
      2 LLM calls.
    - Call kwargs include `cache_control: {"type": "ephemeral"}` on
      the system prompt (prompt-cache verification).
    - Model id passed through (`model="claude-opus-4-7"` arrives at
      the mocked client unchanged).
- `tests/test_worker.py` — ≥ 2 tests:
    - `worker.emit_code(<cube-with-hole intent>)` returns non-empty
      str, contains `"export_step(body"`.
    - `worker.emit_journal(<any intent>)` raises `NotImplementedError`
      with `"v0.1"` substring.
- `[tool.importlinter]` extended with three new contracts:
    - `agent.sanity` may import only `maquette.intent` + stdlib `re`
      (no other maquette modules; no I/O modules).
    - `agent.planner` may import `maquette.intent`,
      `maquette.intent_validation`, `maquette.pricing`, `anthropic`
      + stdlib (no adapters, agent.\*, render, cli, config).
    - `agent.worker` may import `maquette.intent`, `maquette.adapters`
      + stdlib (no agent.\*, render, cli, config).
- `[tool.coverage.report] include` extended to add the three new
  modules.

## Maximum deliverable

If everything above lands cleanly, also:

- **Per-call duration instrumentation:** `PlanResult` carries
  `duration_s: float` (wall-clock around the SDK call) in addition
  to `tokens` and `retries`. Plumbing for N1 latency tracking lands
  ahead of phase-2b's `trace.jsonl`.
- **Sanity false-positive tests:** prompts using "centred" /
  "centered" — the centring keyword implies derived coordinates
  (half-of-size, etc.) that the regex would otherwise flag as
  mismatches against the size parameter. At least 3 tests:
    1. Cube prompt with "centred" — no warnings expected.
    2. Cylinder prompt with "centred along the X axis" — no warnings
       on derived axis position.
    3. Negative case where the dim is *also* wrong (the centring word
       doesn't whitewash a genuine mismatch).
- **Two more few-shots in `prompts/planner.system.md`:** cylinder-
  with-chamfer and L-bracket-with-holes. The L-bracket few-shot
  demonstrates the `extras`-based escape hatch in action (planner
  emits real L-geometry as build123d code in `extras`).
- **Live-API integration smoke** (gated by `ANTHROPIC_API_KEY`):
  one test per v0 reference prompt running against the real API.
  Marker `@pytest.mark.live`; default `pytest -q` skips. Useful
  locally to catch SDK / system-prompt drift before phase-2b.

## Sprint / day breakdown

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | `agent.sanity` + import-linter contract | `src/maquette/agent/sanity.py` (`Dimension`, `DimensionMismatch`, `SanityResult` frozen dataclasses; module-level `check(prompt, intent) -> SanityResult` with regex extraction `(\d+(?:\.\d+)?)\s*(mm\|cm\|m\|in)` plus delimited `<n>×<n>×<n> mm`; unit-normalised comparison to all Intent numeric values; ±1% or ±0.5 mm tolerance; module docstring links ADR-0002); `[tool.importlinter]` contract `agent.sanity → maquette.intent + stdlib only`; `tests/test_sanity.py` (≥ 8 tests including tolerance edges + multi-axis prompts) | All sanity tests pass; `check("a 50 mm cube", <50 mm cube Intent>)` returns `ok=True`; `lint-imports` reports 4 contracts kept |
| 2 | `agent.planner` + `prompts/planner.system.md` + Anthropic prompt caching + import-linter contract | `src/maquette/agent/planner.py` (`PlanResult` dataclass with `intent + tokens + retries`; `PlannerExhausted` exception; `plan(client, prompt, model, prompts) -> PlanResult` calling `client.messages.create(...)` with cache_control on system prompt; SDK usage → `Tokens` mapping; JSON extraction (try `json.loads` direct, then strip ```\`\`\`json``` fences, then regex-pluck first `{...}` block); one retry on `ValidationError` with stricter user-prompt addendum); `prompts/planner.system.md` (Intent schema + 11-kind contract tables + cube-with-hole few-shot + v0-gap guidance: hole position → extras, complex shapes → extras, edge selection → extras); `[tool.importlinter]` contract `agent.planner → maquette.intent + intent_validation + pricing + anthropic + stdlib`; `tests/test_planner.py` (≥ 6 tests with mocked client covering happy path, code-fenced JSON, single retry, exhaustion, cache_control kwarg, model-id passthrough) | All planner tests pass; mock invocation asserts `cache_control={"type": "ephemeral"}` present on system prompt; `PlannerExhausted` raised after exactly 2 mocked calls in the failing-retry test |
| 3 | `agent.worker` + import-linter contract + (MAX) duration + centred sanity + 3-prompt few-shots + (MAX) live-API gate | `src/maquette/agent/worker.py` (module-level `emit_code(intent) -> str` delegating to `maquette.adapters.build123d_target.emit`; `emit_journal(intent) -> str` stub raising `NotImplementedError("v0.1: NX journal emission not implemented")`); `[tool.importlinter]` contract `agent.worker → maquette.intent + maquette.adapters + stdlib`; `tests/test_worker.py` (delegation + v0.1 stub); (MAX) `PlanResult.duration_s` field + planner wraps SDK call with `time.perf_counter()`; (MAX) ≥ 3 centred-keyword sanity tests; (MAX) cylinder-with-chamfer + L-bracket-with-extras few-shots appended to `prompts/planner.system.md`; (MAX) `@pytest.mark.live` integration tests in `tests/test_planner_live.py` gated by `ANTHROPIC_API_KEY` env var | All worker tests pass; `lint-imports` reports 6 contracts kept (4 from before + sanity + planner + worker = wait, recount: phase-1 had 3; phase-2a Day 1 adds 1; Day 2 adds 1; Day 3 adds 1 → **6 total**); `coverage report` shows ≥ 80% on `agent.sanity` + `agent.planner` + `agent.worker`; (MAX-conditional) `pytest -m live` exercises the 3 v0 reference prompts against real API and asserts `Intent` validates |

## Exit criteria

Phase-2a is `done` when **all** of the following hold:

1. `pyright src/` exits 0.
2. `agent.sanity.check("a 50 mm cube with a 20 mm hole through the centre", <cube-with-hole Intent>)` returns `SanityResult(ok=True, ...)`.
3. `agent.planner.plan(<mocked client>, "a 50 mm cube with a 20 mm hole through the centre", "claude-opus-4-7", <prompts>)` returns a `PlanResult` whose `.intent` validates as an `Intent` (specifically: features contains one `box` and modifiers contains one `hole`).
4. `agent.worker.emit_code(<cube-with-hole Intent>)` returns a non-empty string containing `"export_step(body"` (delegation to the phase-1 adapter works end-to-end).
5. `lint-imports` reports 6 contracts kept, 0 broken (3 phase-0/1 + sanity + planner + worker).
6. `pytest -q` passes; coverage on `agent.sanity`, `agent.planner`, `agent.worker` ≥ 80% each.
7. `grep -rE "^(import NXOpen|from NXOpen)" src/` returns nothing (re-verified).
8. CI green on the most recent push to `main`.
9. `phases/phase-2a-report.md` exists (written via `/pm-phase-report`) capturing surprises and decisions.

## Known risks for this phase

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| P2a-R1 | Anthropic SDK API surface for prompt caching in `anthropic~=0.102.0` differs from the shape recorded in ADR 0003 (e.g., `cache_control` argument name changes, `system` parameter expects a different shape) | med | med | Day 2 first concrete step: write a smoke that calls `client.messages.create(...)` with the documented kwargs against a mocked client; SDK signature errors show up immediately. If the API has drifted, file `/pm-blocker` to update ADR 0003; do not silently adapt. |
| P2a-R2 | System prompt design under-specifies Intent schema → real LLM emits non-parseable JSON or schema-violating fields → high retry rate in practice; cost per generation creeps toward N2's $0.10 ceiling on first runs | high | med | The MIN ships with cube-with-hole few-shot only; phase-2a's tests are mocked so don't exercise this. The user manually runs `pytest -m live` (MAX) before phase-2b to surface drift. If retry rate is bad, iterate the system prompt before phase-2b lands the loop. |
| P2a-R3 | Sanity regex over-flags on derived dimensions ("centred" → 25.0 mm half-size; pattern with `count=4` extracted as a "4 mm" dimension) | med | low | MAX includes ≥ 3 centred-keyword tests. False positives are a *warning*, not a hard gate (per ADR 0002), so the worst case is noise in `status.json.warnings[]`, not a blocked run. Tighten regex if real prompts surface bad patterns; revisit tolerance value if Gap G1 reopens. |
| P2a-R4 | Live-API integration tests are slow + cost money + need a key → if accidentally added to default CI matrix, every push burns $0.05 + 20 s | low | med | `@pytest.mark.live` marker + `addopts = "-m 'not live'"` in `[tool.pytest.ini_options]` ensures default `pytest` skips them. Documented in module docstring of `tests/test_planner_live.py`. CI secret `ANTHROPIC_API_KEY` is **not** added until phase 3.5 (smoke + 3 examples), per roadmap. |
| P2a-R5 | SDK `response.usage` field shape doesn't match expectations (e.g., `cache_read_input_tokens` is None when no cache hit, or named `cache_read` vs `cache_read_input_tokens`) | med | low | Map defensively: `getattr(usage, "input_tokens", 0)` etc. Live smoke (MAX) surfaces real shape. Update mapping if it differs; cost calc tolerates zero on any class. |
| P2a-R6 | JSON extraction regex / heuristic strips a "{...}" inside a string literal in the LLM's reasoning ("the cube has size {50}") and confuses parsing | low | med | Prefer `json.loads` on the raw response first; fall back to stripping fenced code blocks; only as last resort regex-pluck a `{...}` block. Each tier logs in `PlanResult.retries` so failures are diagnosable. |
| P2a-R7 | `prompts/planner.system.md` grows past the ~4000-token budget when MAX adds 2 more few-shots → ADR 0003 cost math drifts; cache-creation cost climbs above $0.10 ceiling on first call | low | low | After all 3 few-shots land (MAX Day 3), token-count the file with `tiktoken` or the Anthropic SDK's tokenizer; if > 4500, trim few-shots (keep one example per class instead of one per kind). |
| P2a-R8 | First phase needing `ANTHROPIC_API_KEY` — user environment may not have it set; doc onboarding gap | low | low | `.env.example` already documents it (phase-0 Day 1). README install steps mention copying `.env.example`. Live smoke tests skip cleanly when key absent. |
| P2a-R9 | Hole positioning carry-forward — planner instructs LLM to use `extras` for off-centre holes, but real prompts may produce broken extras (build123d code that doesn't compile) → executor crash, not planner failure | low | med | Phase-2a doesn't have the executor in scope. The mocked-client tests don't exercise extras output. Risk surfaces in phase-2b round-trip when real planner emits L-bracket-via-extras. Mitigation lives in the system prompt quality + phase-2b error handling. |

## Notes for `/pm-phase-start`

When `/pm-phase-start` runs, the Auditor sub-agent should verify:

- F2 (Planner → Intent), F3 (Worker emits via adapter), F6 (sanity
  check) each have at least one task in the day breakdown.
  - F2: Day 2 (`agent.planner`).
  - F3: Day 3 (`agent.worker` thin shim — adapter shipped phase-1).
  - F6: Day 1 (`agent.sanity`).
- N1 (latency) — partial mitigation via MAX `duration_s` field.
- N2 (cost) — verified via mocked-client tests checking
  `cache_control`; full integration test gated to `pytest -m live`.
- N8 (secret hygiene) — `ANTHROPIC_API_KEY` only read by
  `agent.planner` via the client constructed in caller code; no
  log emission of the key in this phase. (Loop / CLI integration is
  phase-2b / phase-3.)
- ADRs 0001, 0002, 0003 are referenced from the module docstrings of
  `planner.py` and `sanity.py`.
- The four phase-1-report carry-forward items (#1, #2, #4, #6 of
  recommendations) are reflected in the policies section above and
  in the planner system prompt content (#1, #2, #4 specifically).
- Glossary follow-up (recommendation #8 from
  [`phase-1-report.md`](phase-1-report.md)) is **not** in scope here
  — it lives between phase-2a-end and phase-5-start as a `/pm-architecture`
  pass. Audit should not block on it.

After audit passes, `/pm-phase-start` flips this file's
`status: planned` → `status: in_progress`, sets `started: 2026-MM-DD`,
and updates [`03-roadmap.md`](../03-roadmap.md) frontmatter
`active_phase: phase-2a`. Scope-freeze applies from that point.
