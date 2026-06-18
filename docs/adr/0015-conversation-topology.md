# 0015 — Conversation topology & context model: one brain, two surfaces

- **Status:** Accepted
- **Date:** 2026-06-04
- **Deciders:** vandpaolo
- **Relates to:** [ADR-0014](./0014-mcp-boundary.md), [ADR-0013](./0013-shared-live-document.md).

## Context

The brain is the user's Claude Code (ADR-0014). Touch has two interaction
surfaces: a **side panel** (macro instructions) and **positional
click-to-prompt** ("chamfer *this*"). Feeding *everything* — every click,
render image, tool result, layer source — into one growing conversation bloats
context ("memory stacks") and degrades the agent. A four-lens analysis
(2026-06-04, `decisions.md`) resolved the topology and context model.

## Decision

**One brain (Claude Code), reached via two surfaces; the backend is canonical
and the conversation references it by id.**

- **Topology.** A **persistent main thread = the side panel** is the project's
  brain of record (whole-part intent). **Positional click-to-prompt spawns an
  ephemeral subagent *from the main thread*** (Claude Code subagent/Task), seeded
  with a positional packet, with isolated context; it does the local edit and
  **summarizes one line back** to the parent. The main thread keeps project
  history; click-agents are ephemeral. The "click → discuss → accept →
  implement" bubble is a scoped sub-session.
- **Built-in planner** (F22) is demoted to an **optional no-account fallback**;
  Claude Code is the brain for both surfaces.
- **Context model (anti-bloat).** Backend (the Layer Stack) is the source of
  truth; the conversation holds a **compact layer manifest** and references
  state **by id**, pulling full layer source/renders **on demand**. **Renders =
  thumbnails, on demand** (never auto-attached every turn — the #1 bloat).
  System-prompt + MCP tool list kept **byte-stable** for prompt-cache hits.
- **Two context packets.** *Positional*: selection (kind + id + owning layer +
  **finder reference**) + picked point/normal + 1-ring neighbours + touchable
  params + units + stack revision. *Macro*: param table + compact layer outline
  + part bbox + units + recent selection — **no** picked point / 1-ring.
- **Finder references, never raw indices** (ADR-0011); picked-point + normal is
  the disambiguator.

## Consequences

- Per-turn context stays roughly flat over a long session (N15); the macro
  thread isn't polluted by click noise; the project stays coherent in one place.
- **Caveat:** Claude Code subagents are single-shot from the parent's view, so a
  multi-turn interactive refine *inside* a click bubble is either a subagent that
  takes a few autonomous turns, or a harness-managed `--resume` sub-session with
  a turn cap (reuse F7's cap). To validate in the MCP-first milestone.
- Summary fidelity matters: each subagent returns a **structured layer-delta**
  summary, not prose, so the main thread tracks what the part became.

## Alternatives considered

- **One shared conversation for everything.** Rejected: bloats fast (images are
  1.6–4.8K tokens each); macro reasoning degrades.
- **Two fully-independent persistent brains.** Rejected: divergent mental
  models, duplicated work, no single project record.
