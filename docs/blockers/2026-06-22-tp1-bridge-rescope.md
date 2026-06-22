---
id: 2026-06-22-tp1-bridge-rescope
phase: TP1
severity: soft
status: resolved
discovered: 2026-06-22
resolved: 2026-06-22
re_entry: architecture
---

# TP1 shipped the Layer Stack as a derived view, not the live document — re-scope needed

## What

TP1 built the Layer Stack primitives as a **tested backend library**, but via a
deliberate **op-history → stack bridge** (Day 6, the `layer_bridge` + `live_build`
path): the op-history (`TouchDocument`) is still the canonical live document
(wire / persistence / undo-redo), and the `LayerStack` is *derived from it per
rebuild*. As a result, several of the phase plan's **MIN-as-written** deliverables
were not wired into the running product:

- **Shared live document + versioned compare-and-swap (F44/N16)** — `LayerStack.add_layer` / `delete_last` / `StaleRevisionError` are built and unit-tested but have **zero live callers**; `Session` is still per-connection op-history; undo/redo mutate `document.history` directly. The "stale-revision rejected" exit criterion passes only in a hand-built unit test.
- **Layer-native `.touch` persistence** — `to_dict`/`from_dict` + `save_stack`/`load_stack` round-trip (incl. a code layer) and migrate op-history forward, but the **session still saves/opens op-history**; the layer-native format is never written by the app. (The exit criterion "reopen → identical stack incl. a code layer" holds only as a standalone library round-trip.)
- **F45 context-packets module** — not built (only the finder-reference half of F45 is live).
- **F39 click→owning-layer highlight** — provenance is computed and **baked into the backend mesh**, but never serialized to the FE; there is no Layer Stack panel and no wire channel, so the live "click a face → its layer highlights" behaviour is not achievable.

What IS live and tested: the Layer model + deterministic emit, the fold + content-addressed cache, computed provenance (baked into the mesh on the live rebuild), template recognition, and the hardened workspace-confined executor.

This was surfaced by an independent 4-agent eval + a 3-lens decision panel
(2026-06-22). The geometry/correctness of what shipped is sound (two real bugs —
provenance sign instability and a layer-native-load silent-empty — were fixed in
commit `0dc8f58`).

## Why the design did not anticipate it

The phase plan's MIN deliverable and exit criteria **conflated two things**:
building the Layer Stack *primitives* (a backend phase) with *wiring them live as
the one shared document* (an integration that depends on consumers TP1 doesn't
have). The Day-6 bridge was the correct call — it protected the working T3–T5
undo/redo + protocol path (the phase's own **risk R-A**) by keeping the proven
op-history surface intact while still exercising the fold / cache / provenance on
the real rebuild path. But the plan never recorded that the *live cutover*
depends on:

- a **second mutator** and a **freeform-code-layer producer** — both arrive with
  the **agent over MCP (TP2)**. CAS exists (ADR-0013) precisely to coordinate the
  viewport and the agent; with one writer it has nothing to race, so it is
  currently dead code, not a gap.
- the **Layer Stack panel** — the consumer of F39's face→layer highlight —
  which is **TP3**.

So the deferral is real, sound, and consumer-driven, but **unrecorded**: ADR-0013
and the `02-classes.md` module map describe a more-finished system than exists,
and the only record of the transitional reality lives in code docstrings.

## Re-entry point

**Architecture** (plus roadmap / phase-plan re-sequencing):

- `/pm-architecture` — record the **transitional bridge** explicitly (op-history
  canonical, stack derived per-rebuild, shared-doc/CAS built-but-unwired); fix the
  stale `02-classes.md` module map (add `layer_bridge` + `live_build`; correct
  `add_layer(layer, expect_rev)`, `recognize(source) -> Recognized`,
  `attribute(prev, next, layer_id, prior)`; relocate `executor` to
  `agent.executor`; mark `mcp_server` / `context_packets` as not-yet-built);
  note ADR-0013's TP1-deferred-live status; add import-linter contracts +
  the `Mesh.face_provenance` field.
- `/pm-roadmap` + `/pm-phase-plan` — re-sequence the deferred work onto its
  consumers (see Proposed resolution).

The requirements themselves (F38–F47) are unchanged — this is a *when*, not a
*what*. Requirements re-entry is **not** needed.

## Proposed resolution

**Keep the bridge** (eval + panel validated). Re-scope:

- **TP1 MIN** = the delivered backend primitives (model + emit, fold + cache,
  computed provenance baked into the mesh, template recognition, layer-native
  persistence *capability*, CAS *capability*, workspace-confined executor).
- **TP2 sprint 1 (before the MCP tools)** = the **document cutover**: make the
  shared `LayerStack` the canonical live document with CAS live, and switch the
  session's save/open to the layer-native `.touch` format — so CAS and
  persistence are exercised against their first real consumer (the agent).
- **TP2** also gains the **F45 context-packets** module.
- **TP3** gains the **F39 FE click→layer-highlight** channel + Layer Stack panel.
- Record **M1/M2** as known R-B provenance limits: a fused/stacked face gets
  single-owner attribution (wrong for half the face on the common stack-and-fuse
  case), and a perfectly *symmetric* trim can be mis-read as untouched. Robust
  multi-owner / boundary-signature provenance stays a Max/later item.

After `/pm-architecture` (+ `/pm-roadmap` + `/pm-phase-plan`) lock the re-scope,
resolve this blocker, then `/pm-phase-report` closes TP1 on the corrected scope.

## Resolution

**Decided 2026-06-22: keep the bridge** (validated by an independent 4-agent eval
+ a 3-lens decision panel — the deferred items' consumers arrive in TP2/TP3, so
wiring them live now would build ahead of consumers and re-open risk R-A). The
re-scope was locked across the design layers:

- **Roadmap** (`/pm-roadmap`, commit `a24cde7`): TP1 = the Layer Stack backend
  **primitives**; **TP2 sprint 1** = the document cutover (make the shared
  `LayerStack` canonical + CAS **live** + switch the session to layer-native
  `.touch`) **before** the MCP tools; **F45** context packets → TP2; **F39** FE
  click→owning-layer highlight → **TP3**. Requirements F38–F47 unchanged.
- **Architecture** (`/pm-architecture`, commit `c3f8cf3`): `02-classes.md` module
  map reconciled (`operation_adapter` + `agent.executor`; corrected
  `layer_stack`/`provenance`/`templates` signatures; **added `layer_bridge` +
  `live_build`**; `mcp_server`/`context_packets` marked **NOT BUILT — TP2**);
  `02-architecture.md` "TP1 reality" note (op-history canonical, stack derived per
  rebuild, shared-doc/CAS built-but-unwired); `02-data-model.md` `Mesh.face_provenance`;
  **ADR-0013** deferred-live status note.

Also done in the same round: two real bugs found by the eval fixed (`0dc8f58` —
provenance plane-sign instability, layer-native `.touch` silent-load guard); a
DRY cleanup (`67afc30`); the **M1/M2** provenance accuracy limits (single-owner on
a fused face; symmetric-trim false-negative) recorded as known R-B limits.

Outcome: the bridge stays; TP1's true delivery is now reflected in the design
docs; the deferred live integration is owned by TP2/TP3. TP1 returns to
`in_progress` on the corrected scope; `/pm-phase-report` closes it next.
