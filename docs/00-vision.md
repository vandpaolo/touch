# 00 — Vision

> *Rewritten 2026-05-29 for the **Touch** pivot (formerly Maquette).
> Synthesized from `notes/inbox.md` (the 2026-05-29 Touch pivot section +
> architecture research) + the shipped-Maquette vision. Update via
> `/pm-vision`.*

> *Touch: the only thing you do is touch. Orbit the model, click a face,
> say what you want — the part takes shape under your hands.*

## The problem

CAD is powerful and slow. For most first-draft and bread-and-butter
parts — brackets, mounts, enclosures, fixtures — the shape is trivial to
*describe* ("a 40×40×25 box, hollow it to a 5 mm shell, cut a USB slot in
that face") but tedious to *build*: sketch, extrude, select faces, place
holes, click through a feature tree, repeat for every revision.

The predecessor project, **Maquette** (shipped v0), proved an LLM can
turn a natural-language prompt into *correct parametric geometry* via a
strict `Intent` schema + build123d/OpenCascade. But it was **one-shot and
headless** — type a sentence, get a STEP. That design hit a wall exactly
where CAD gets interesting: **ambiguity and position.** "Chamfer the top
edge", "a hole in *this* face" — a single text prompt has no way to point
at geometry, and no way to ask a clarifying question. Maquette's own v0
references broke on precisely those cases.

The missing piece isn't a better prompt. It's a place to **point and
talk**: interactive, positional, conversational.

## The dream

**Touch** is an open-source, AI-native 3D CAD editor. The interface is a
3D workplane (orbit/pan/zoom with classic Siemens-NX mouse controls) and
a VS-Code-style shell — a file/project tree on the left, the viewport in
the centre. The only verb is **touch**:

1. **Click** a face, edge, point, or construction plane.
2. A **prompt box** appears, anchored to what you clicked.
3. You say what you want. Clear instructions execute immediately; unclear
   ones become a short **conversation** until the system has enough to
   act.
4. The model **evolves one operation at a time** — you see each result in
   3D and drive the next step.

Where you click *is* the spatial argument ("hollow *this* from the top",
"a hole *here*"), which is exactly what a one-shot prompt could never
express. Under the hood it's Maquette's engine — build123d/OCP + the
Claude planner — now driven interactively instead of fired once.

You install it as a desktop app, paste in your own Claude API key, and
model. It's built for engineers who live in CAD but shouldn't have to
fight the GUI to rough something out.

## Scope

Milestones are re-baselined for Touch. The shipped Maquette pipeline
(`intent` schema, planner, build123d adapter, executor) is **retained as
Touch's headless engine** — not rebuilt.

### In scope — Touch v0 (POC: "model the mini-PC enclosure by touching")
- A desktop application: 3D viewport (three.js) + NX-style camera + a
  VS-Code-like file/project tree + a settings panel (Claude API key).
- **Click-to-prompt** with positional context: clicking a face/edge/
  point/plane feeds that selection + coordinates to the planner.
- **Conversational clarification:** an ambiguous prompt turns into a
  short back-and-forth instead of a guess.
- **Incremental modelling:** operations accumulate (append-only history);
  each step re-tessellates and updates the live 3D view.
- The architecture from the 2026-05-29 research: a **Python kernel
  server** (build123d/OCP) streaming meshes-with-face-IDs over a
  **WebSocket** to the **three.js** frontend; the *same* frontend runs as
  a **browser tab in headless dev** and **wrapped in a desktop shell for
  the `.exe`** distribution.
- Reuse of the Maquette engine (planner, adapter, executor, pricing,
  config) behind that server.

### In scope — Touch v0.1+ (next)
- A richer operation set; robust face/edge reference that survives edits
  (replicad-style geometric "finders" + server-side ID resolution).
- Undo/redo; a project/document save format (the operation history).
- An automatic correctness check (the Maquette v0.1 vision-Evaluator
  idea, now catching "looks wrong" in the live editor).

### In scope — later milestones (sequencing in `03-roadmap.md`)
- **Assemblies** — multiple parts + mates/constraints (the reason the
  file-tree structure matters from day one).
- **Simulation** — FEA / multibody / dynamics, as a separate Python
  compute service exchanging STEP/mesh (does not change the editor↔engine
  coupling).
- **Control / optimization / heavy numeric**, possibly ML inference —
  the versatility a Python engine keeps open.
- A **hosted / browser** version (the web frontend already runs in a
  browser; this is mostly deployment).

### Out of scope (for now, possibly forever)
- **Feature-parity with commercial CAD** (SolidWorks/NX). Touch is
  AI-native first-draft + edit, not a clone of a 30-year GUI.
- **Rebuilding manual GUI modelling** (sketch-by-sketch toolbars). The
  point is touch+prompt; manual tools come only if they earn their place.
- **Its own geometry kernel.** Touch stands on OpenCascade (via build123d/
  OCP), not a from-scratch B-rep kernel.
- **Multi-user / real-time collaboration / cloud** in v0. Single user,
  local app.
- **Mesh-only output** (STL/3MF as primary). B-rep / STEP is the model of
  record; meshes are for display.
- **Parametric editing of earlier history** in v0 (the topological-naming
  problem). v0 history is append-only.

## Non-goals — explicit

- **Not "an assistant that hands you a draft and leaves"** — that was
  Maquette. Touch *is* the editor; you model inside it. (This is the
  deliberate positioning flip from the predecessor.)
- **Not a constraint solver / assembly mate engine** in v0. Single parts.
- **Not a feature recogniser.** It generates from intent + selection; it
  does not reverse-engineer imported geometry into editable features.
- **Not multi-provider on day one.** Claude is the model; the client is
  abstracted so a swap is cheap, but no provider-agnostic layer upfront.
- **Not a from-scratch UI toolkit.** Lean on web tech (three.js + a
  web-app shell) and a desktop wrapper, not a bespoke native GUI.

## Audience

- **Primary:** the author + a handful of **engineer friends** — working
  engineers who do a lot of CAD, are comfortable with the domain but not
  especially tech-savvy, and would adopt a desktop tool that lets them
  rough out parts by pointing and describing. They install the `.exe` and
  use their own Claude key.
- **Secondary:** the broader **engineer/maker + open-source CAD** crowd
  (FreeCAD / build123d / CadQuery users) wanting an AI-native, positional
  modelling on-ramp.
- **Tertiary:** people exploring **agentic / LLM-driven design tooling**
  as a pattern — Touch as a reference for "click + converse" CAD.

## Success criteria

Touch v0 (the POC) succeeds when **the mini-PC enclosure is modelled
entirely by touching, inside the app, on a clean install:**

1. Open Touch (empty editor). Click an orthogonal plane → prompt
   "a 40 × 40 × 25 box" → the box appears.
2. Click the top face → "hollow it out with a 30 × 30 × 15 box" → it
   becomes a ~5 mm shell.
3. Click a wall face/edge → "cut a USB-sized slot here" → the cutout
   lands at the clicked location.
4. The result exports a STEP that opens in FreeCAD and visually matches
   the intended enclosure.
5. At least one ambiguous prompt triggers a **clarifying conversation**
   rather than a wrong guess.

And **it ships as software a friend can actually run:** a packaged
**Windows `.exe`** that launches, takes a Claude API key in Settings, and
runs the flow above — while the identical frontend also runs as a browser
tab in the author's headless Linux dev environment. (macOS/Linux desktop
builds are a later milestone; Windows is the POC distribution target.)

Precise non-functional bars (per-step latency, LLM cost per modelling
session) are interactive and per-operation rather than one-shot, so they
are set in `01-requirements.md` / phase planning rather than fixed here —
the qualitative bar is "feels responsive enough that touching beats
opening real CAD."

## Strategic-fit map

Touch deliberately exercises skills relevant to applied-AI systems and
engineering-tooling work:

| Skill / theme | How Touch exercises it |
|---|---|
| Agentic systems with bounded autonomy | A click+converse loop where an LLM proposes structured CAD operations against a live model, with human confirmation each step |
| Structured outputs / schema-driven LLM use | The `Intent`/operation schema as the pivot; the LLM never emits free-form CAD code |
| Real-time interactive systems | A kernel-server ↔ web-frontend coupling streaming geometry, with positional picking and incremental updates |
| Desktop + web dual delivery | One web frontend that runs in a browser (dev) and as a packaged desktop app (distribution) over a local service |
