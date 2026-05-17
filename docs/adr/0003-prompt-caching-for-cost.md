# 0003 — Anthropic prompt caching for cost headroom

- **Status:** Accepted
- **Date:** 2026-05-16
- **Deciders:** vandpaolo

## Context

NFR N2 requires per-generation cost < $0.10 on a simple part. The v0
pipeline runs one LLM call (Planner) per generation.

Current Anthropic pricing (verified 2026-05-16):

| Model | Input ($/Mtok) | Output ($/Mtok) | Cache read ($/Mtok, ~10% of input) | Cache creation ($/Mtok, ~125% of input) |
|---|---|---|---|---|
| `claude-opus-4-7`   | $5.00 | $25.00 | $0.50 | $6.25 |
| `claude-sonnet-4-6` | $3.00 | $15.00 | $0.30 | $3.75 |
| `claude-haiku-4-5`  | $1.00 |  $5.00 | $0.10 | $1.25 |

Note: Opus 4.7 ships with a new tokenizer that produces up to ~35% more
tokens for the same source text vs prior Opus tokenizers.

The Planner's system prompt is large by design — it teaches the model
the Intent schema, the per-kind contracts, and includes few-shot
examples. Estimated v0 sizes (after the Opus 4.7 tokenizer bloat):
~4000 system + ~270 user + ~540 output tokens per call.

### Cost without caching, Opus 4.7

- Input:  4270 × $5/M  ≈ $0.021
- Output:  540 × $25/M ≈ $0.014
- **~$0.035 per call** — already comfortably under N2 ($0.10).
- With one retry: ~$0.070 — still under N2.

### Cost with caching, Opus 4.7

- Cache read:  4000 × $0.50/M ≈ $0.002
- Fresh input:  270 × $5/M    ≈ $0.0014
- Output:       540 × $25/M   ≈ $0.014
- **~$0.017 per call** — ~2× headroom over the no-cache version.
- With one retry: ~$0.034.

So caching is **not strictly required** to hit N2 in v0. It is adopted
anyway because the headroom matters as soon as: (a) the system prompt
grows (more few-shots, more kinds, more examples), (b) the loop runs
multiple times (v0.1 refinement iterations), or (c) the model gets a
follow-up tokenizer change. Caching is also standard practice for
stable system prompts, and it's the only way the cost target survives
schema growth without re-evaluating the whole approach.

## Decision

The Planner uses Anthropic's prompt caching on the system prompt + few-shots:

```python
client.messages.create(
    model="claude-opus-4-7",
    max_tokens=2048,
    system=[
        {
            "type": "text",
            "text": PLANNER_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": prompt}],
)
```

`maquette.pricing` accounts for four token classes per call:
`input`, `output`, `cache_read`, `cache_creation`. The Anthropic SDK
reports these directly via `response.usage`; they are written verbatim
to `trace.jsonl` per call and aggregated into `status.json.tokens` and
`status.json.cost_usd_estimate`.

The prompts directory (`prompts/`) is hashed at startup (single
rolled-up SHA-256 of all file contents, per gap G3 decision) and the
hash is written to `status.json.prompts_hash`. A cache miss after a
known-good hit is therefore diagnosable: the prompt content changed.

## Consequences

**Easier:**

- N2 (cost < $0.10) survives schema growth, retry rounds, and future
  refinement iterations (v0.1).
- Cost accounting is precise: actual SDK-reported token counts × the
  pricing table give the recorded `cost_usd_estimate` (per requirement
  F9 and decision P4).
- Per-class token tracking surfaces in `status.json` (`tokens.input`,
  `tokens.output`, `tokens.cache_read`, `tokens.cache_creation`) so
  cost-hit-rate is observable.

**Harder:**

- Pricing table in `maquette.pricing` must distinguish four token
  classes per model, not two. Slight schema bloat.
- Cache invalidation: any edit to the system prompt forces the next
  call to be cache-creation pricing (~1.25× normal input). Expected
  behaviour, diagnosable via `prompts_hash`.
- The five-minute cache TTL means infrequent single-shot users pay
  cache-creation cost almost every call. The cost target still holds
  (~$0.04 even with creation); batch users benefit most.

**Explicitly traded away:**

- Provider neutrality. Prompt caching is Anthropic-specific. A future
  provider abstraction (vision § decisions deferred) will need a
  generic shape, but v0 reality is Anthropic-only — see vision § Non-goals.
- Static-cost predictability per call. Per-call cost now depends on
  cache hit rate; the < $0.10 target holds in steady state.

## Alternatives considered

### A. Skip caching, ship without

- **What:** Pay full input price every call.
- **Why not:** Works for v0 today (~$0.035/call) but burns the headroom
  needed for v0.1 refinement iterations and future schema growth. Caching
  is cheap to add now and expensive to retrofit when prompts grow.

### B. Use Sonnet 4.6 or Haiku 4.5 instead of Opus

- **What:** Drop to a cheaper model. Sonnet would save ~40%; Haiku ~80%.
- **Why not:** Quality of structured-output adherence on a strict pydantic
  schema is the load-bearing capability. Opus 4.7 is the safest default
  for the planner; downgrading is an open path once schema-success rate
  is measured (see vision § decisions deferred for provider abstraction).

### C. Shorter system prompt (no few-shots)

- **What:** Trim system prompt to ~500 tokens; drop few-shots.
- **Why not:** Few-shots lock the Intent JSON shape cheaply. Without
  them schema-fail rate rises and retries burn cost. Caching keeps
  few-shots cheap; trimming them is the opposite optimization.
