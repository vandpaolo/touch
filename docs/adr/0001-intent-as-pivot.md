# 0001 — Intent as the pivot

- **Status:** Accepted
- **Date:** 2026-05-12
- **Deciders:** vandpaolo

## Context

The system has to take a natural-language prompt and produce editable CAD.
Two backends are in scope: build123d (free, default, in-repo) and Siemens
NX Open (optional, emit-only, user-side).

The naive design — "ask the LLM for build123d code, run it, ship the STEP" —
has three problems:

1. **No validation before execution.** Any hallucination (wrong unit, missing
   argument, made-up API call) becomes a subprocess crash.
2. **One backend at a time.** Going to NX from build123d code means a second
   LLM translation pass per generation. Twice the cost, twice the failure
   surface.
3. **No durable regression corpus.** build123d's API evolves; we want a way
   to keep our reference cases meaningful across upgrades.

A free-form "we'll just prompt-engineer harder" path doesn't fix any of these.

## Decision

Introduce a strict structured intermediate — `Intent` — between the LLM and
the backend code. The LLM emits `Intent` (pydantic), not CAD code. Adapters
translate `Intent` into backend-specific code.

Concretely:

- `maquette.intent.Intent` is the pivot type. It is a small pydantic tree
  with `parameters`, `features`, `modifiers`, and an `extras` escape hatch.
- The **Planner** LLM call emits JSON that must validate against `Intent`.
- **Adapters** (`adapters.build123d_target`, `adapters.nx_open_target`) are
  pure functions: `Intent → str` (source code). They never call an LLM, and
  they never depend on each other.
- `extras` is the relief valve for anything the schema can't express;
  appended verbatim to adapter output. Same `extras` for both adapters
  (i.e., raw build123d code) is acceptable when only targeting build123d;
  NX-flavoured extras are a separate concern only if a user actually needs
  them.

See [02-data-model.md](../02-data-model.md) for the schema, and
[02-architecture.md](../02-architecture.md) + [02-classes.md](../02-classes.md)
for the adapter contract (Adapter Protocol + concrete adapter modules).
*(Originally referenced vault paths `02-intent-schema.md` and
`04-adapters.md`; updated 2026-05-16 for the framework layout.)*

## Consequences

**Easier:**

- **Validation before execution.** Pydantic catches a large fraction of
  hallucinations before any geometry runs.
- **Multi-backend from one generation.** Same `Intent` compiles to build123d
  and NX with no extra LLM cost.
- **Durable regression corpus.** `examples/` stores `intent.json` plus the
  expected emitted code. build123d's API churn breaks adapter snapshots, not
  reference Intents.
- **Caching.** Same `Intent` + same adapter version → byte-identical output.
- **Determinism.** Adapters are pure functions; we can unit-test them
  without ever calling an LLM.

**Harder:**

- **Schema design becomes load-bearing.** The schema is small now, but every
  new feature kind or modifier needs adapter implementations *and* schema
  documentation *and* planner prompt updates. Schema evolution has a tax.
- **The schema is a bottleneck.** Things the schema can't express must go in
  `extras` (raw backend code), which loses multi-backend benefit and validation.
  Heavy `extras` usage in v0 is a signal the schema needs to grow.
- **Two-step LLM flow.** Planner emits Intent, Worker emits code. v0 keeps
  Worker pure (no LLM call — adapter only); if Worker ever needs an LLM
  again (e.g. for `extras` synthesis), we add a second call.

**Explicitly traded away:**

- "Just let the LLM write build123d directly." We chose more structure and
  more upfront work in exchange for fewer surprises at execution time.
- Generality. The schema does NOT cover all of CAD, and we have no
  intention of growing it to. The escape hatch + small surface is the
  point.

## Alternatives considered

### A. Direct code generation (no Intent)

- **What:** Planner prompt → build123d Python directly. Skip pydantic.
- **Why not:** No validation before execution; every backend needs its own
  LLM call; no regression corpus that survives library churn.

### B. Free-form JSON, no schema

- **What:** Planner emits a loose dict; adapters interpret defensively.
- **Why not:** All the costs of having a pivot, none of the validation
  benefits. Adapters become a mess of `if "kind" in obj` checks.

### C. A full-CAD ontology

- **What:** Try to model sketches, edges, faces, datums, mates, constraints
  upfront.
- **Why not:** Enormous schema design effort. Premature. Most v0 prompts are
  satisfiable with ~6 primitive kinds and ~5 modifiers. Start small; grow
  when forced.

### D. Use an existing standard (STEP AP242, JT, IGES) as the pivot

- **What:** Have the LLM emit STEP directly, then parse for the NX adapter.
- **Why not:** STEP is too low-level (B-rep geometry, not features). It
  doesn't capture intent — by the time something is STEP, you've lost the
  feature tree that makes editing useful. The whole point of this project
  is preserving feature-tree intent through to NX's Part Navigator.
