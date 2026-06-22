# 0013 — Shared live document + versioned Layer Stack (session coordination)

- **Status:** Accepted
- **Date:** 2026-06-04
- **Deciders:** vandpaolo
- **Relates to:** [ADR-0012](./0012-layer-stack-authoring.md), [ADR-0014](./0014-mcp-boundary.md); pulls in the deferred T4b multi-doc-ready refactor.

> **Implementation status (2026-06-22).** Accepted, but **deferred-live**. TP1
> built the versioned `LayerStack` + compare-and-swap as a tested **capability**
> and kept the op-history canonical via a transitional bridge (the stack is
> derived per rebuild) — sound, because no second mutator exists yet. The shared
> live document + **live** CAS land in **TP2 sprint 1** (the document cutover,
> before the MCP tools), where the agent is the first concurrent writer this ADR
> coordinates. See blocker `2026-06-22-tp1-bridge-rescope`.

## Context

In the pivot, two surfaces act on the *same* part: the 3D **viewport** and the
**agent** (Claude Code over MCP, ADR-0014). Today `Session` is **per-WS
connection** — each client gets its own document. If the agent's MCP server
connected as just another client, it would edit a *different* document than the
one the viewport shows. We need one live part both surfaces share, without the
two corrupting each other on stale state.

## Decision

**The backend holds ONE shared active document — the Layer Stack — and both the
viewport WS and the agent (via MCP) act on it.**

- **Versioned stack.** Every accepted mutation bumps a **monotonic revision**
  and yields an immutable `(revision, diff)`. The current solid/mesh is a
  derived cache of the stack at the head revision.
- **Compare-and-swap.** Every mutation carries the **expected head revision**;
  if the backend's head has moved, the mutation is **rejected** and the caller
  re-plans against the new head. Optimistic concurrency, no locks — kills the
  stale-context race between viewport and agent.
- **Single executor / one code path.** Both surfaces produce a *layer spec*;
  the backend's single executor implements it. One place to enforce stack
  invariants (validity, append-only).
- **Change feed.** Both surfaces are **stateless views** that rebuild context
  from the revision feed (the agent references state by id — ADR-0015).
- **v0 = one active part at a time.** Editor tabs / multi-document layer on
  later; this supersedes strictly-per-connection `Session` (the T4b refactor,
  pulled forward into the pivot).

## Consequences

- Agent edits appear live in the viewport and vice-versa; the viewport's
  selection is queryable by the agent (`get_selection`, ADR-0014).
- No stale-state corruption; concurrent edits resolve to one-applied /
  one-rejected-and-replanned (N16).
- `Session` evolves from "owns a document" to "a connection attached to the
  shared active document"; the document/stack lifecycle moves up a level.
- Multi-doc (tabs) is additive later: multiple active documents keyed by id.

## Alternatives considered

- **Keep per-connection isolation.** Rejected: the agent and viewport would
  never share a live part — the whole point fails.
- **Two documents kept in sync (agent's + viewport's).** Rejected: two sources
  of truth, a sync protocol, and divergence risk.
- **Locks instead of CAS.** Rejected: an interactive agent + a human clicking
  would deadlock/stall; optimistic CAS + re-plan is the right fit.
