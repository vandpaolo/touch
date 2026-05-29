# 00 — PR-FAQ

> *Synthesized from `notes/inbox.md` (migrated vault content) on 2026-05-16.
> Update via `/pm-vision`. The vault did not contain a PR-FAQ; this is a
> first draft assembled from vision content + reasonable inference. Two
> FAQ slots (biggest risk, what failure looks like) are flagged as Gaps.*

## Press release (as if v1 already shipped)

**Headline:** Describe a part. Get a CAD model in seconds.

**Sub-headline:** Maquette translates plain-language part descriptions into
editable build123d code and STEP files, with optional NX Open journal
handoff that preserves the feature tree.

**Body:**

CAD authoring for first-draft geometry is mostly mechanical translation:
"a 50 mm cube with a 20 mm hole through the centre" is trivially describable
but tedious to type into a feature tree. Engineers spend hours doing what is
essentially dictation in GUI form.

Maquette takes the prompt, asks a strict structured LLM to emit an `Intent`
(a small pydantic schema), then runs deterministic adapters that translate
the Intent into build123d code (run headless to export STEP) and into an
NX Open journal (replay it in NX to get a fully parametric feature tree).

The flow: one command, one prompt, three orthographic renders, a STEP file
ready to open in any CAD tool, and an NX journal ready to land as a real
feature tree. The system never replaces CAD — it hands you a maquette
(rough first draft) and gets out of the way.

## FAQ (internal)

**Why now?**
LLMs are reliable for constrained code generation and structured outputs.
CAD has scriptable backends (build123d, NX Open). Bridging the two with a
small, focused tool is now within reach without re-inventing CAD.

**Who is this for?**
Primary: the author, as personal tooling for fast first-draft geometry
(brackets, mounts, enclosures, jigs). Secondary: free-CAD users wanting a
prompt-to-part on-ramp. Tertiary: NX seat owners wanting a fast scratchpad
with output that lands cleanly back in NX as real features.

**What is the smallest thing we can ship?**
`maquette design "a 50 mm cube with a 20 mm hole through the centre"`
producing a STEP file that opens in FreeCAD and shows the described part,
within 20 s and < $0.10 in API cost.

**What's the biggest risk?**
Silent semantic failure: the LLM emits a valid `Intent`, the adapter
compiles it, the build123d code runs, the STEP file is produced — but
the geometry doesn't match what the prompt described. The user must
visually verify every output, eroding the speed benefit. Mitigations:
the v0.1 vision-based Evaluator catches mismatches; the Intent schema
is intentionally expandable, so categories of semantic mismatch that
surface in practice can be hardened by tightening the schema. If a
backend (e.g. NX Open) turns out to be a brittle source of failures,
we file a `/pm-blocker` and pivot to a different backend (e.g. FreeCAD)
— the multi-backend pattern is robust to backend-specific failure modes.

**How will we know it worked?**
v0 success: the two schema-native references (cube with hole, cylinder
with an all-edges chamfer) generate a STEP that opens cleanly in FreeCAD,
within 20 s and < $0.10 per generation, *within the v0 capability bound*
(no edge-specific selection or oriented multi-face holes — those are
v0.1). The L-bracket (compound shape via the `extras` relief valve) is a
demonstrated best-effort showcase, not a hard gate, since `extras` is
un-guarded until the v0.1 Evaluator. v0.1 adds the NX journal
landing as a real feature tree in the NX Part Navigator for the same
prompts.

**What does failure look like?**
Every prompt produces a STEP that runs but is visually wrong, requiring
the user to open it in CAD and re-verify the geometry by eye every time.
At that point the tool offers no speed advantage over hand-authoring,
and the user stops using it. This is the inverse of the success
criterion: speed without trustworthy correctness is just an expensive toy.
