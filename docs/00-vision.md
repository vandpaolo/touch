# 00 — Vision

> *Revised 2026-06-04 for the **Claude-Code / MCP pivot** (decision set in
> `notes/decisions.md`, 2026-06-04). Touch becomes a CAD IDE you point your
> own coding agent at. Prior rewrite 2026-05-29 (Maquette → Touch). Update
> via `/pm-vision`.*

> *Touch: the only thing you do is touch. Orbit the model, click a face,
> say what you want — or hand the whole part to your agent. Geometry takes
> shape under your hands, or under Claude's.*

## The problem

CAD is powerful and slow. For most first-draft and bread-and-butter
parts — brackets, mounts, enclosures, fixtures — the shape is trivial to
*describe* ("a 40×40×25 box, hollow it to a 5 mm shell, cut a USB slot in
that face") but tedious to *build*: sketch, extrude, select faces, place
holes, click through a feature tree, repeat for every revision.

Two things changed the landscape. First, **Maquette** (Touch's shipped
predecessor) proved an LLM can turn a prompt into *correct parametric
geometry* (build123d/OpenCascade) — but one-shot and headless, with no way
to point at geometry or ask a clarifying question. Touch v0 (T0–T5) fixed
that: an interactive, positional, conversational editor — click a face,
say what you want, watch it build, undo instantly.

Second, **coding agents arrived.** Engineers increasingly already have a
capable agent — **Claude Code** — running on a subscription they pay for.
It writes real code fluently, including CAD code (build123d/CadQuery), far
better than it fills in any bespoke schema. The opportunity isn't to build
*a* CAD AI; it's to make CAD a place that **agent can drive** — and to let
*you bring your own*.

## The dream

**Touch is an open-source, standalone CAD IDE that you point your own
Claude Code at — the port between CAD and LLMs.** It keeps everything that
made the editor good (orbit, click, prompt, see, undo) and opens a second,
more powerful door: your agent.

**One brain — your own Claude Code — reached two ways**, both acting on the
same live part:

1. **The side panel** *(the macro thread).* Your main Claude Code conversation
   — the project's brain of record. Whole-part intent: "make the walls 3 mm",
   "add mounting tabs", "design a gearbox". It reads the model, *sees renders*
   of it, writes geometry, and iterates while you watch.
2. **Click-to-prompt** *(positional).* Click a face or edge and a prompt opens,
   carrying the spatial context (what you clicked, where, which layer). The main
   thread **spawns a scoped agent** for that local edit; you refine the feature,
   accept, it implements, and a one-line summary lands back in the main thread.
   This is how a CAD engineer points: "chamfer *this*", "a hole *here*".

The **main thread always keeps the project**; the positional click-agents are
ephemeral and report back to it. A small built-in planner stays only as an
optional no-account fallback — but Claude Code is the brain for both surfaces.

Under both, a part is a **Layer Stack**: free build123d code, where **each
edit is a layer** you can hover, click, and inspect. Layers are clickable
because Touch computes which layer produced each face — so the freedom of
code and the granularity of a feature tree coexist. The common, simple
operations (box, chamfer, …) show up as editable parametric cards;
everything creative shows up as a code layer. The agent authors freely;
you still point and click.

Touch is the **IDE shell**; the brain is whatever agent you bring. Geometry
is the first capability exposed over MCP — analysis (FEM), manufacturing
(CAM), and **third-party extensions** are later workbenches over that same
boundary. The engine underneath stays build123d/OpenCascade, headless and
reusable.

## Scope

The v0 editor (T0–T5: viewport, click-to-prompt, `.touch` history, folder
workspace, clarification, robust selection) is **shipped and retained.**
The pivot builds *on* it.

### In scope — the pivot, milestone 1 (MCP-first)
- **Layer Stack authoring** — a part is an ordered list of build123d
  layers; per-layer content-addressed rebuild + computed provenance →
  clickable layers; structured ops survive as **recognized templates**.
- A **shared live document** in the backend (one active part; viewport and
  agent act on the same thing).
- An **MCP server** exposing geometry as tools (query model, selection,
  render-to-image, add/edit/reorder layer, …), driven by the user's
  **existing Claude Code** — validating the whole loop on the subscription,
  no API tokens, before any embedding.
- The **built-in planner** kept only as an **optional no-account fallback**
  (Claude Code is the brain for both surfaces).
- **Conversation/context model** (`notes/decisions.md` 2026-06-04): main thread
  = project brain of record; positional clicks spawn ephemeral subagents that
  summarize back; the backend Layer Stack is canonical (conversation references
  by id); renders are thumbnails on demand; selection via finder references.

### In scope — the pivot, milestone 2 (embed)
- **Claude Code embedded in the app**: launch + login, a right-side
  **agent panel** (custom chat with geometry-aware tool-call cards + inline
  renders), and a **Layer Stack panel** (the feature tree) — all over the
  same MCP. Two-way selection bridge (click a face ↔ the agent).

### In scope — later milestones (sequencing in `03-roadmap.md`)
- **Editing/reordering earlier layers** (the reference-re-resolution /
  topological-naming subsystem). v0 is append-only.
- A **real OS sandbox** for the executor, gated on opening untrusted parts.
- **Extensions** — third parties add workbenches/tools over the MCP port.
- **FEM / CAM** as workbenches that *consume* the geometry (separate Python
  compute, exchanging STEP/mesh — does not change the editor↔engine
  coupling).
- **Assemblies**; a **hosted / browser** version.

### Out of scope (for now, possibly forever)
- **Feature-parity with commercial CAD** (SolidWorks/NX). Touch is
  AI-native first-draft + edit, not a clone of a 30-year GUI.
- **Its own geometry kernel.** Touch stands on OpenCascade (build123d/OCP).
- **Reselling / embedding Claude's subscription** for *other* users. You
  bring *your own* Claude Code; Touch never proxies someone else's account.
- **Multi-user / real-time collaboration / cloud** in v0. Single user, local.
- **Mesh-only output** (STL/3MF as primary). B-rep / STEP is the model of
  record; meshes are for display.

## Non-goals — explicit

- **Not "an assistant that hands you a draft and leaves."** Touch *is* the
  editor; you (and your agent) model inside it, live.
- **Not a hosted AI service.** Touch is a local IDE + an MCP port; it
  doesn't run models or bill tokens. The intelligence is the agent *you*
  bring (Claude Code on your subscription, or the small built-in planner).
- **Not locked to one authoring format.** The agent writes free build123d;
  Touch does *not* force a custom DSL on it. (This reverses the earlier
  "the LLM never emits free-form CAD code" stance — see Conflict below.)
- **Not a feature recogniser.** It builds from intent/selection/code; it
  does not reverse-engineer imported geometry into editable features.
- **Not a from-scratch UI toolkit.** Web tech (three.js + a VS-Code-style
  shell) in a desktop wrapper.

## Audience

- **Primary:** **CAD engineers who don't write code.** The goal is to bring
  Claude Code's power to people who live in CAD, not in a terminal — through a
  familiar CAD shell where the agent is *intuitively integrated* (a side-panel
  conversation + positional click-to-prompt), on the user's own Claude
  subscription, no per-token cost. They never experience it as "operating a
  coding agent"; they point, describe, and accept.
- **Secondary:** the **open-source CAD / build123d / CadQuery** crowd
  wanting an AI-native, agent-drivable modelling environment — and, later,
  **extension authors** who build workbenches over the MCP port.
- **Tertiary:** people exploring **agentic / MCP-driven design tooling** as
  a pattern — Touch as a reference for "an app your coding agent operates."

## Success criteria

Touch's pivot succeeds when **the same live part can be built two ways:**

1. **Built-in path (the v0 benchmark, retained):** empty editor → click a
   plane → "a 40×40×25 box" → click the top → "hollow it with a 30×30×15
   box" → click a wall → "cut a USB slot here" → export a STEP that opens
   in FreeCAD and matches; and at least one ambiguous prompt triggers a
   clarifying conversation.
2. **Agent path (the new benchmark):** build a part with an **extrusion, a
   hole, and a chamfer** using **both** surfaces — positional click-to-prompt
   for the located features, the side-panel conversation for the rest —
   **entirely through the user's own Claude Code subscription (no API tokens)**,
   each step appearing live in the viewport. (Notably, *hole* and *extrude*
   aren't in the built-in op vocabulary — they arrive as **code layers**, which
   is the Layer Stack's whole point.)

Milestone 1 succeeds headlessly (drive from existing Claude Code);
milestone 2 succeeds when the same flow runs **inside Touch's own agent
panel**, with login, on a packaged build.

Precise non-functional bars (latency, subscription-usage budget per
session) are interactive/per-operation and set in `01-requirements.md` /
phase planning. Qualitative bar: "modeling-with-your-agent-in-Touch beats
alt-tabbing between a code editor and a CAD GUI."

## Strategic-fit map

| Skill / theme | How Touch exercises it |
|---|---|
| Agentic systems / tool use | A live CAD app exposed over **MCP** that an external coding agent drives (read model, see renders, author layers, iterate) with human steering |
| The IDE-as-platform pattern | Touch as an MCP **host/port** — geometry first, FEM/CAM/extensions as future workbenches over the same boundary |
| Bring-your-own-agent / subscription auth | Driving a user's own Claude Code at zero API-token cost; the local IDE owns capability, the user owns the brain |
| Real-time interactive systems | Kernel-server ↔ web-frontend streaming geometry; positional picking; per-layer incremental updates + instant undo |
| Desktop + web dual delivery | One web frontend that runs in a browser (dev) and as a packaged desktop app embedding the agent |
