# 00 — PR-FAQ

> *Revised 2026-06-04 for the **Claude-Code / MCP pivot** (`notes/decisions.md`,
> 2026-06-04). Prior rewrite 2026-05-29 (Maquette → Touch). Update via `/pm-vision`.*

## Press release (as if it already shipped)

**Headline:** Point your own Claude Code at CAD — the IDE where your agent builds the part.

**Sub-headline:** Touch is an open-source 3D CAD IDE. Click a face and say
what you want, or hand the whole part to your own Claude Code over MCP — on
your subscription, no API tokens. It writes the geometry, *sees* the render,
and you watch the model take shape, layer by clickable layer.

**Body:**

Modelling a simple part in traditional CAD is mostly mechanical: sketch,
extrude, select a face, place a hole, fight the feature tree. The shape is
easy to *say* but slow to *click*.

Touch gives you two ways to model the same live part. **Touch it:** orbit
with NX-style controls, click where you want a change, and describe it — a
small built-in brain handles quick edits with no account. **Or hand it to
your agent:** Touch is an MCP server, so the **Claude Code you already run**
can read the model, see renders of it, write build123d, and iterate —
designing a whole enclosure or a parametric gearbox — while you watch and
click in to steer. Your subscription, no per-token cost.

A part in Touch is a **Layer Stack**: free build123d code where every edit
is a layer you can hover and click. You get the full expressiveness of code
*and* the granularity of a feature tree, because Touch knows which layer
made each face. Common operations show as editable parametric cards; the
creative stuff shows as code.

Touch is the IDE; the brain is whatever agent you bring. Geometry is the
first thing it exposes over MCP — analysis, manufacturing, and third-party
extensions are later workbenches over the same port. Underneath, it's the
proven build123d/OpenCascade engine from the shipped v0 editor.

## FAQ (internal)

**Why now?**
The v0 editor (T0–T5) shipped: interactive click-to-prompt, `.touch`
history, folder workspace, conversational clarification, robust selection.
And the integration we needed exists and was **spike-verified** (2026-06-04):
Claude Code drives a local MCP server **on the subscription, no API tokens**,
streams parseable events for a custom panel, and **sees images** an MCP tool
returns (it described a real render). MCP is the standard, supported port;
the remaining work is product, not unsolved research.

**Who is this for?**
Primary: **CAD engineers who don't write code** — people who live in CAD, not a
terminal, getting Claude Code's power through a familiar shell where the agent
is intuitively integrated (side-panel conversation + positional click-to-prompt),
on their own subscription, no per-token cost. They point, describe, and accept;
they never feel like they're "operating a coding agent." Secondary: the
open-source CAD / build123d crowd, and later extension authors building
workbenches over the MCP port. Tertiary: people exploring agentic/MCP-driven
design tooling.

**What is the smallest thing we can ship?**
Milestone 1 (MCP-first): the backend becomes a **Layer Stack** with a shared
live document and an **MCP server**; you point your **existing Claude Code**
at it and say "build a 40×40×25 enclosure with a USB slot" — it authors
layers, sees the render, and the part appears live in Touch's viewport where
you can click a face. No embedding yet, no API tokens. Milestone 2 embeds the
agent panel + login inside the app.

**What's the biggest risk?**
Three. (1) **Topological naming** — clicking a face and mapping it to the
right geometry as the model changes; mitigated by per-face IDs + geometric
finders + append-only v0. (2) **Agent-authored code** is the document you
execute — reliability (non-manifold/wrong-face) and safety; mitigated by
per-layer render-and-validate feedback, the recognized-template/finder model,
and a workspace-confined executor (real OS sandbox before opening others'
parts). (3) **Dependence on Claude Code / MCP staying open** and on
subscription usage limits for an agentic loop; mitigated by keeping the
built-in planner as a no-account fallback and the engine provider-neutral.

**How will we know it worked?**
Milestone 1: your own Claude Code, over MCP, builds the enclosure on your
subscription with zero API tokens, you *see* it live and click a face to
steer. Milestone 2: the same flow runs inside Touch's own agent panel on a
packaged build, with login. The built-in click-to-prompt benchmark (the v0
mini-PC flow) still passes.

**What does failure look like?**
The agent's code is wrong/non-manifold often enough that you stop trusting
it; or clicking a face still mis-selects; or driving your agent in Touch is
clunkier than alt-tabbing between a code editor and a CAD GUI; or the
subscription/usage path is too fragile/limited for a real modelling loop. At
that point Touch is a demo, not a tool people reach for.
