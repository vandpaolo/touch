# 00 — Vision

> *Synthesized from `notes/inbox.md` (migrated vault content) on 2026-05-16.
> Update via `/pm-vision`.*

> *A maquette is the rough preliminary model an artist makes before sculpting
> the final piece. The AI hands you the maquette; you finish the real thing.*

## The problem

Going from a design intent in someone's head to an editable CAD model is
slow. The current path is:

- Open CAD (FreeCAD, Onshape, Fusion, NX, SolidWorks).
- Hand-author sketches, extrusions, holes, fillets.
- Tweak parameters by clicking through a feature tree.
- Repeat for every revision, every variant, every "what if it were 20% bigger".

For first-draft geometry — early concept work, parametric variants, jigs and
fixtures, brackets, mounts, enclosures — most of that authoring is mechanical
translation of a sentence ("a 50 mm cube with a 20 mm hole through the centre")
into a feature tree. The shape is trivially describable; the act of typing it
into a CAD GUI is not.

LLMs are good at constrained code generation. CAD has scriptable backends.
Bridging the two should be a small, focused tool — not a re-invention of CAD.

## The dream

Describe a part in natural language. Get back:

1. **An editable parametric solid** in a free, open backend (build123d).
2. **A STEP file** for handoff to any other CAD tool.
3. **An optional NX Open journal** — replay the construction in Siemens NX
   and the features land in the Part Navigator, fully parametric.
4. **Three rendered views + an evaluator critique** so the user can decide
   whether to ship, refine, or rewrite the prompt.

Then open the result in a real CAD tool and finish the engineering by hand.
The system never claims to be the CAD tool. It hands the user a maquette and
gets out of the way.

## Scope

### In scope — v0
- A Python package + CLI: `maquette design "..."`.
- An LLM **Planner** that converts a prompt to a strict `Intent` (pydantic).
- An LLM **Worker** that converts `Intent` to build123d code.
- A subprocess **Executor** that runs the code headless, exports STEP, and
  renders three orthographic PNGs via PyVista.
- A **build123d adapter** (default, in-repo, free).
- Filesystem-as-state: every generation is a folder under `output/` with
  `intent.json`, `code.py`, `renders/`, and the STEP file.

### In scope — v0.1 (next)
- An **NX Open adapter** that *emits* a `.py` journal — zero NX imports in
  repo. (Moved from v0 per push-back B1: keeps v0 on the build123d
  critical path; the strategic-fit benefit is preserved either way since
  the adapter still gets built, just later.)
- Vision-based **Evaluator** + refinement loop (worker / evaluator / refiner).
- Isometric render in addition to the three orthographic views.
- An `examples/` regression corpus (hand-curated good sessions).

### In scope — v0.2 (later)
- Conversational mode (multi-turn refinement before commit).
- Parameter sliders post-generation (regenerate with tweaked dims, no LLM
  round-trip).
- Expansion of the `Intent` schema based on what `extras` is being used for
  most often in practice.

### Out of scope (for now, possibly forever)
- Replacing CAD. The system is a first-draft generator. Engineering judgment
  stays human.
- **Assemblies.** Single parts only in v0.
- **Mesh-only output** (STL/3MF as primary). STEP / B-rep only — meshes are
  a dead end for editable CAD.
- **Web UI.** CLI first. A web frontend can come later if there's a reason.
- **Recorded NX journals from licensed sessions.** The NX adapter is written
  against the public NX Open API only; no licensed-session artefacts in the
  repo, ever.

## Non-goals — explicit

- **Not a constraint solver.** No mate inference, no assembly-level
  constraints in v0. Single parts only.
- **Not a feature recogniser.** The system generates from intent, it does
  not reverse-engineer geometry into intent.
- **Not multi-provider abstracted on day one.** Default to Claude; abstract
  the client so swapping is cheap, but don't build a provider-agnostic
  layer upfront. Premature abstraction.
- **Not a chatbot.** v0 is one-shot. Conversational refinement is v0.2.

## Audience

- **Primary:** the author. Personal tooling for fast first-draft geometry,
  especially for parts where the description-to-feature-tree translation is
  the bottleneck (brackets, mounts, enclosures, fixtures).
- **Secondary:** other engineers who already use free CAD (FreeCAD,
  build123d users) and want a prompt-to-part on-ramp.
- **Tertiary:** NX seat owners who want a fast scratchpad outside the NX
  GUI, with output that lands cleanly back in NX as a real feature tree.

## Success criteria

v0 ships when **all three** v0 reference prompts succeed end-to-end on
a clean clone of the repo (with only `ANTHROPIC_API_KEY` set):

1. **Cube with through-hole** — e.g. `"a 50 mm cube with a 20 mm hole through the centre"`
2. **Cylinder with chamfer** — e.g. `"a 30 mm diameter, 40 mm tall cylinder with a 2 mm chamfer on the top edge"`
3. **Simple L-bracket** — e.g. `"a 60 × 40 × 5 mm L-bracket with a 6 mm hole in the centre of each flange"`

For each prompt, the produced STEP file must open in FreeCAD and show
the described part, within 30 s wall-clock and < $0.10 in API cost.
NX-journal output is verified separately under v0.1.

## Strategic-fit map

**Personal tooling first, portfolio second.** Maquette is built because
the author wants the tool, not as interview cosplay. That said, the
design deliberately exercises three skills relevant to the ABB Robotics
Senior .NET role and to applied-AI systems work in general:

| Skill / theme | How Maquette exercises it |
|---|---|
| Agentic systems with bounded autonomy | Planner / Worker / Executor / Evaluator loop with a strict structured intermediate |
| Structured outputs / schema-driven LLM use | `Intent` (pydantic) as the pivot; no free-form CAD code from the LLM |
| Code generation for licensed / closed APIs | NX Open adapter emits a `.py` journal against the public API, with zero in-repo coupling to the licensed tool |

Looser parallels (digital-twin analogies, multi-target deployment,
licensed-tool hygiene discipline) follow naturally from these three;
they don't need their own rows.
