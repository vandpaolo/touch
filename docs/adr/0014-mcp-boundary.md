# 0014 — The MCP boundary: Touch as an MCP host/port

- **Status:** Accepted
- **Date:** 2026-06-04
- **Deciders:** vandpaolo
- **Relates to:** [ADR-0007](./0007-pluggable-llm-client.md) (retires its SDK subscription path), [ADR-0013](./0013-shared-live-document.md), [ADR-0015](./0015-conversation-topology.md).

## Context

The goal: the user drives Touch with their **own Claude Code, on their
subscription, with zero API tokens**. Research + a spike (2026-06-04, claude
2.1.132, FastMCP stdio) established: the **Agent SDK now requires a paid API
key** (OAuth restricted to Claude Code + claude.ai, Feb 2026), so ADR-0007's
"Claude Code via `claude-agent-sdk` on the subscription" path is **not
token-free**. The supported token-free path is **MCP**: Claude Code (on the
subscription) connects to a local MCP server and calls its tools — verified to
work, including the agent **seeing images** an MCP tool returns.

MCP is also more than a Claude bridge: it's the **extensibility port** — any
MCP-capable agent can drive Touch, and future workbenches (FEM, CAM,
third-party extensions) are additional tool-sets over the same boundary.

## Decision

**Touch ships a local MCP server; the user's own Claude Code (or any MCP agent)
drives Touch through it. MCP is the agent ⇄ live-app boundary and the
extensibility port.**

- **Placement (ADR-0013).** The MCP server is a **separate stdio process that
  Claude Code spawns**, which **forwards to the running Touch backend over the
  existing WS protocol** and acts on the one shared active document. A thin
  adapter — *not* a second geometry engine.
- **Geometry tools:** `get_model_state`, `get_selection`, `render_view → image`,
  `list_layers` (ids + summary + thumbnail, *not* code), `get_layer`,
  `add_layer`, `edit_layer`, `reorder_layer`, `delete_layer`.
- **Mutating tools return a structured envelope:** `{ ok | error, render
  thumbnail, validity check (manifold/non-empty), downstream delta +
  finder-rebind warnings }` — so the agent self-corrects per layer without a
  separate round-trip.
- **Agent-neutral.** Nothing is Claude-specific in the contract; MCP is the
  standard port. Touch never embeds or proxies anyone else's subscription (it's
  *your* Claude Code on *your* machine — sidesteps the reselling-ToS issue).
- **Tokens-free is a property of the auth path**, not the tool layer: the agent
  runs on the user's Claude Code subscription (N14).

## Consequences

- Zero API-token agent path (N14); the live-app bridge (selection, renders as
  the agent's *eyes*, kernel queries) that a dead `.py` file can't provide;
  and the extensibility seam for FEM/CAM/extensions.
- The MCP server is small and stateless (forwards to the backend); the backend
  (ADR-0013) remains the source of truth.
- **Caveat (ADR-0015):** Claude Code subagents are single-shot from the parent's
  view, so a multi-turn interactive click-bubble is a short subagent run or a
  harness-managed `--resume` sub-session with a turn cap — to validate in the
  MCP-first milestone.

## Alternatives considered

- **Claude Agent SDK in-process (ADR-0007's path).** Rejected: now requires a
  paid API key — not token-free. Retained only conceptually for the *fallback*
  API planner (ADR-0007 note).
- **File-watcher only** (agent edits `.py` files, app re-runs). Rejected: no
  live selection, no kernel queries, no in-loop render feedback — it's an editor
  watching files, not an agent driving the app.
- **Hosted service that proxies the subscription.** Rejected: ToS-prohibited and
  off-mission; Touch is a local IDE + an MCP port, not an AI service.
