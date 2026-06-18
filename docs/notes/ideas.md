# Notes — Ideas

Speculative thoughts. Things that *might* be worth doing. Not committed.

Ideas in here are not requirements. They feed the **Push-back** and
**Probe** questions in skill output ("you mentioned X as an idea — should
this become a requirement, or stay speculative?").

---

## 2026-06-04 — Pivot idea: "Cursor for CAD" — agent/coding-LLM as the brain

Reframe Touch from a standalone app with an LLM API under the hood toward an
**IDE/toolbox where you plug in your own coding LLM** (ideally Claude Code, or
another agentic CLI) and it drives the geometry. "Open-code for CAD." User is
*not* asking to change anything now — a direction to brainstorm/sequence
post-T5. Three distinct sub-ideas (different sizes):

1. **Provider swap (API key → Claude Code login).** Already designed — F31 +
   ADR-0007 (pluggable `LLMClient`: Anthropic API *and* a Claude Code client via
   `claude-agent-sdk`, subscription, no key). This is phase **T6**. Cheapest
   lever; gives the "log in with Claude Code" feel without a rewrite.

2. **Agentic code authoring (the real "Cursor for CAD", undesigned).** Instead of
   planner→`{kind,params}`→adapter, a coding agent writes/edits build123d Python,
   runs it, **looks at the render**, and iterates. Half-built already: the
   adapter emits build123d *source* (F24), the Executor runs it + returns
   structured errors, and the headless renderer (orthographic PNGs) is exactly
   the "eyes" a multimodal agent needs to self-correct. That edit→run→see→fix
   loop is the differentiator the API planner can't do.

3. **Toolbox / BYO-brain (MCP).** Touch exposes geometry as tools (open part,
   pick face, apply op, tessellate, render, export) any agent/IDE can drive;
   Touch = geometry backend + shell, brain is external. Purest "open-code
   toolbox." A v0.2+ direction, not the next step.

**The one real tension:** structured operation history vs free-form code as the
source of truth. T3–T5 bought append-only ops, finders/click-to-prompt, instant
undo/redo + content cache, portable replayable `.touch`. Letting an agent write
arbitrary code sacrifices most of that. Reconciliations:
- **A — Planner++:** agent still emits the same structured ops, just smarter
  (multi-step, sees renders). Keeps every guarantee.
- **B — Two-tier (lean):** structured ops for click edits + a **code escape
  hatch** for power moves (Maquette's `extras` relief valve already in the data
  model); agent gets the renderer as eyes. Feels like Cursor-for-CAD without
  discarding T3–T5.
- **C — Full pivot:** code *is* the document, agent sole author; trades away
  replay/undo/finders. Resist.

**Recommendation:** keep everything; ship T6 (Claude Code login) for the feel;
pursue option B for the magic; treat MCP-toolbox as a v0.2+ statement. Pursue via
a `/pm-vision` revisit + a new ADR ("agentic vs structured authoring") after T5
closes. Likely reshapes the roadmap (and reframes the vision from "standalone
.exe for a friend" toward "BYO-LLM CAD IDE").

**Open question for the user:** which is the real target — cheap Claude Code
login (T6) or agent-writes-the-code? And is Touch still a standalone `.exe` for a
friend, or "the CAD IDE you point your existing coding agent at"? (The answer
reshapes the vision + who the user is.)

