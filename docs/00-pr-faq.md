# 00 — PR-FAQ

> *Rewritten 2026-05-29 for the **Touch** pivot. Update via `/pm-vision`.*

## Press release (as if it already shipped)

**Headline:** CAD you can talk to — point at the model and say what you want.

**Sub-headline:** Touch is an open-source 3D CAD editor where you orbit a
part, click a face, and describe the change in plain language. It builds
the geometry, asks when it's unsure, and you watch the model take shape
step by step.

**Body:**

Modelling a simple part in traditional CAD is mostly mechanical: sketch,
extrude, select a face, place a hole, fight the feature tree. The shape
is easy to *say* — "a 40×40×25 box, hollow it to a shell, cut a USB slot
in this wall" — but slow to *click*.

Touch turns that sentence into the workflow. The interface is a 3D
workplane with classic NX-style controls and a VS-Code-like project tree.
You click where you want something to happen, a prompt box appears, and
you describe it. Clear instructions execute immediately; ambiguous ones
become a short conversation. Because Touch knows *where you clicked*, it
can place features positionally — "a hole *here*", "hollow *this* from the
top" — which a one-shot text prompt never could.

Under the hood, a Claude-powered planner converts your click + words into
a structured CAD operation, and a build123d/OpenCascade kernel builds it,
streaming the updated geometry back to the 3D view. You install Touch as a
desktop app, drop in your own Claude API key, and model.

Touch is the evolution of Maquette, a prototype that proved an LLM could
generate correct parametric geometry from a prompt. Touch makes it
interactive, positional, and conversational — a CAD editor, not a one-shot
generator.

## FAQ (internal)

**Why now?**
Maquette (v0) already proved the hard part — an LLM reliably turning
intent into correct build123d/OpenCascade geometry via a strict schema.
The research (2026-05-29) confirmed the coupling is solved: a Python
kernel server streaming meshes to a web 3D frontend over WebSocket is a
proven pattern (Onshape, ocp-vscode), and the *same* frontend runs as a
browser tab in dev or wrapped as a desktop `.exe`. The remaining work is
product, not unsolved research.

**Who is this for?**
Primary: the author + engineer friends — working engineers who do lots of
CAD, aren't especially tech-savvy, and want to rough out parts by pointing
and describing, running a desktop app with their own Claude key.
Secondary: the broader engineer/maker + open-source-CAD crowd wanting
AI-native modelling. Tertiary: people exploring click+converse / agentic
design tooling.

**What is the smallest thing we can ship?**
Touch v0 (POC): model the mini-PC enclosure entirely by touching —
empty editor → click a plane → "a 40×40×25 box" → click the top →
"hollow it with a 30×30×15 box" → click a wall → "cut a USB slot here" →
export a STEP that opens in FreeCAD and matches — in a packaged `.exe` a
friend can install and run with their own API key.

**What's the biggest risk?**
Two. (1) **Picking that survives edits** — clicking a face and reliably
mapping it back to the right CAD face, especially as the model changes
(the topological-naming problem). Mitigation: kernel owns face identity +
per-face IDs in the streamed mesh (Onshape-style) and operations
referenced by re-derivable geometry (replicad-style "finders"); v0 stays
append-only to sidestep the worst of it. (2) **Desktop packaging** of a
web frontend + a Python/OpenCascade backend into a `.exe` that
non-technical friends can run — native-dependency bundling is fiddly.
Mitigation: prove it with an early end-to-end spike (round-trip +
picked-face + packaged `.exe`) before building features.

**How will we know it worked?**
The full mini-PC enclosure flow works *inside the app* on a clean
install; the produced STEP opens in FreeCAD and matches; at least one
ambiguous prompt triggers a clarifying conversation instead of a wrong
guess; and an engineer friend successfully installs the `.exe`, enters
their key, and models something.

**What does failure look like?**
Clicking a face gives the wrong geometry or the wrong selection often
enough that you stop trusting it; or the `.exe` is too fragile for a
non-technical friend to install and run; or the click+converse loop is
slower/clunkier than just opening real CAD. At that point Touch is a demo,
not a tool people reach for.
