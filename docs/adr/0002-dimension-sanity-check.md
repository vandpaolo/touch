# 0002 — Dimension sanity check as a v0 guardrail

- **Status:** Accepted
- **Date:** 2026-05-16
- **Deciders:** vandpaolo

## Context

Requirement F6 introduces a dimension sanity check between the Planner
and the Worker. This addresses risk R7 (silent semantic failure: the
LLM emits a valid `Intent`, the adapter compiles it, build123d runs, a
STEP is produced — but the geometry doesn't match what the prompt said).

The proper mitigation for R7 is the v0.1 vision-LLM Evaluator. v0 ships
without it. Without any guard, v0 fails the PR-FAQ failure mode: every
prompt produces a STEP that runs but is visually wrong, the user has to
re-verify each output, and the tool offers no speed advantage.

A cheap intermediate guard catches the most common class of mismatch —
*numeric* mismatch, the kind a regex can spot — at near-zero cost, with
no LLM call.

## Decision

Introduce `maquette.agent.sanity`, a pure module with one entry point:

```python
def check(prompt: str, intent: Intent) -> SanityResult: ...
```

The implementation:

1. Extract numeric dimensions from the prompt with regex patterns
   (`(\d+(?:\.\d+)?)\s*(mm|cm|m|in)`, plus delimited forms like
   `60 × 40 × 5 mm`).
2. Walk `Intent.parameters` and feature/modifier `params`, collecting
   all numeric values + their effective units.
3. Compare each prompt-extracted dimension to the Intent values.
4. Tolerance: **±1% or ±0.5 mm, whichever is larger** (default; tracked
   as Gap G1 — may tighten after first runs).
5. Return `SanityResult { ok, warnings, mismatches }`. `ok = False` if
   any mismatch; `warnings` are user-readable strings; `mismatches` are
   structured for downstream tooling.

Loop calls `sanity.check()` after Planner returns and before Worker is
called. If `ok = False`, Loop:

- Logs a `DIMENSION_WARNING` entry to `trace.jsonl` per mismatch.
- Adds the warnings to `status.json.warnings[]`.
- **Continues the run** — sanity check is a *visibility signal*, not a
  hard gate. The user sees the warning and decides whether to trust
  the geometry.

`--no-sanity` CLI flag is **not** added in v0 (R11). If false positives
become painful, the flag is a v0.1 follow-up.

## Consequences

**Easier:**

- A class of silent semantic failures (mismatched dimensions) becomes
  visible at no LLM cost.
- The user gets a quick "look here first" signal before opening the
  STEP in CAD.
- v0 ships with R7 partially mitigated, not fully unmitigated.

**Harder:**

- A new module (`agent.sanity`) and a new state in the loop. Adds
  complexity to the pipeline.
- Regex extraction has false positives ("centred" implies coordinates
  equal to half the size — the extracted "50 mm" may "match" twice).
  And false negatives ("fifty millimetres" written out).
- Tolerance tuning is open (Gap G1).

**Explicitly traded away:**

- Hard-gate semantics. A non-warning run is *not* a guarantee of
  semantic correctness; it just means the regex didn't find a mismatch.
- LLM-driven semantic checks in v0 (those wait for v0.1 Evaluator).

## Alternatives considered

### A. Ship v0 with no semantic guard at all

- **What:** Accept R7 fully; let the user inspect everything by eye.
- **Why not:** Even the demo cube prompt has clear numeric content. A
  regex catches the most obvious failure class for free. Shipping
  without it leaves the PR-FAQ failure mode (`a`) wide open in v0.

### B. Embed sanity logic inside `agent.planner`

- **What:** Skip the separate module; have the planner call its own
  sanity check after returning.
- **Why not:** Coupling. The sanity check has no LLM dependency and
  works on `(str, Intent)` — natural standalone module. Also testable
  in isolation without mocking the LLM.

### C. Make sanity a hard gate (fail the run on mismatch)

- **What:** If `ok = False`, fail with a new exit code; no STEP produced.
- **Why not:** Regex is too noisy to be a hard gate. False positives
  (derived dims, alternative phrasings) would block legit runs. A
  *warning* preserves user agency.

### D. LLM-based sanity check (small fast model double-checking the Intent)

- **What:** Run a small Claude Haiku call comparing prompt + Intent.
- **Why not:** Adds cost (N2), adds latency (N1), and v0.1 already
  brings the proper vision Evaluator. Premature.
