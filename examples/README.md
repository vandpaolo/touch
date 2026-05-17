# Examples

This directory is reserved for hand-curated **regression cases** — known-good
sessions used to verify the planner / adapter / executor pipeline keeps
working as the schema and prompts evolve.

## Status

**Empty in phase-0.** Real cases land in Phase 4 (the first golden-set
seed) and Phase 7b (the curated regression corpus). See
[`docs/03-roadmap.md`](../docs/03-roadmap.md).

## Format (planned)

Each case will be a self-contained subfolder mirroring `output/<run-id>/`,
minus the per-run noise:

```
examples/<slug>/
  prompt.txt        # the user prompt verbatim
  intent.json       # the validated Intent emitted by the planner
  code.py           # the build123d source emitted by the adapter
  renders/          # the three orthographic PNGs
  part.step         # the exported STEP file
```

Explicitly **excluded** from the fixture format: `trace.jsonl` (noisy,
contains per-call timings and token counts) and `status.json` (mostly
contains derived telemetry).

The three v0 reference prompts ([`docs/00-vision.md`](../docs/00-vision.md)
§ Success criteria) will be the first three cases when Phase 4 lands.
