# Architecture Decision Records

Lightweight ADRs for decisions that are hard to reverse later.

## When to write one

- Picks one technology, pattern, or boundary over alternatives.
- Will be expensive to undo later.
- A future contributor (or future-you) would otherwise rediscover from scratch.

Don't write one for trivial choices. Don't retro-fit one to a shipped decision
unless someone asks "why did we do it this way?" — that's the signal.

## Format

One file per ADR, numbered: `NNNN-short-slug.md`. Numbers are monotonic; never
renumber. A superseded ADR stays in place — write a new one that references it.

Required sections:

```markdown
# NNNN — Short title

- **Status:** Proposed | Accepted | Superseded by NNNN
- **Date:** YYYY-MM-DD
- **Deciders:** name(s)

## Context
What's the situation that forced a decision?

## Decision
What did we decide?

## Consequences
What becomes easier? What becomes harder? What did we explicitly trade away?

## Alternatives considered
What else was on the table, and why we didn't pick it.
```

## Index

### Maquette-era (v0 shipped, prior product — kept for history; their domain assumptions are bounded by the Maquette CLI vision)

- [0001 — Intent as the pivot](./0001-intent-as-pivot.md) — Accepted (2026-05-12)
- [0002 — Dimension sanity check as a v0 guardrail](./0002-dimension-sanity-check.md) — Accepted (2026-05-16)
- [0003 — Anthropic prompt caching for the cost target](./0003-prompt-caching-for-cost.md) — Accepted (2026-05-16)
- [0004 — build123d export variable convention](./0004-build123d-export-variable.md) — Accepted (2026-05-28)

### Touch-era (current product — interactive 3D CAD editor; supersedes the Maquette domain framing)

- [0005 — Editor↔engine coupling: localhost WebSocket + our own thin protocol](./0005-localhost-websocket-coupling.md) — Accepted (2026-05-29)
- [0006 — `.touch` JSON as the native document format](./0006-touch-document-format.md) — Accepted (2026-05-29)
- [0007 — Pluggable LLM client + Claude Code subscription path](./0007-pluggable-llm-client.md) — Accepted (2026-05-29)
- [0008 — Picking and face-identity: kernel IDs + finders + append-only v0](./0008-picking-and-face-identity.md) — Accepted (2026-05-29)
- [0009 — Desktop shell: Electron + Python sidecar (+ the packaging spike)](./0009-desktop-shell-electron-sidecar.md) — Accepted (2026-05-29)
