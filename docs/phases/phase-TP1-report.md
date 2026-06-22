---
phase: TP1
status: done
min_met: true
max_met: false
duration_planned_days: 10
duration_actual_days: 4
---

# Phase TP1 — Layer Stack backend — Report

Closed 2026-06-22 on the **corrected scope** (see blocker
[2026-06-22-tp1-bridge-rescope](../blockers/2026-06-22-tp1-bridge-rescope.md)).
TP1 delivered the Layer Stack **backend primitives**, all CI-green
(backend 326 + web 15), via a deliberate op-history→stack **bridge**. The live
shared-document integration was deferred to its consumers (TP2/TP3).

## What shipped

Sprint rows (all 10 landed; several deliver their *backend half*, with the live
integration deferred per the re-scope):

| Day | Task | Status | Artefact |
|-----|------|--------|----------|
| 1 | `Layer`/`LayerStack` model + `emit` | **done** | `layer_stack.py` (`0f3241f`) |
| 2 | Deterministic fold + per-layer content cache | **done** | `layer_stack.rebuild` (`00f3986`) |
| 3 | Computed provenance → face attribution | **done** | `provenance.py` (`0da0c0f`) |
| 4 | Recognized templates vs code layers | **done** | `templates.py` (`c3fdd2c`) |
| 5 | Versioned stack + compare-and-swap | **done (capability)** | `add_layer`/`delete_last`/CAS (`506b1a9`) — not wired live |
| 6 | Session → shared-doc refactor | **done (bridge)** | rebuild routes through the derived stack (`ee94efc`); op-history kept canonical |
| 7 | `.touch` persistence for the stack | **done (capability)** | `to_dict`/`from_dict` + `save_stack`/`load_stack` + migration (`6c14712`) — session still saves op-history |
| 8 | Workspace-confined executor (F46) | **done** | `agent/executor.py` guards (`9100c1f`) |
| 9 | Wire click→layers (provenance baked) | **done (backend)** | `live_build.py` bakes provenance into the live mesh (`2ec5e71`); FE channel deferred |
| 10 | Exit verification + CI | **done** | `test_tp1_exit.py`, full CI green (`22635fd`) |

Live and tested: the Layer model + deterministic emit, the fold + content-addressed
cache, computed provenance baked into the live rebuild mesh, template recognition,
the hardened workspace-confined executor, and the op-history→stack bridge.
Delivers **F38, F40, F46**, F39 (computed provenance, backend), F45
(finder-reference selection); F44/N16 + layer-native `.touch` as built capabilities.

Post-build round (after the eval): a DRY cleanup (`67afc30`), two real bug fixes
(`0dc8f58`), and the re-scope (`fc21f5d`/`a24cde7`/`c3f8cf3`/`6fed316`).

## What slipped (and why)

Deferred to consumers (the bridge decision — sound, validated by an independent
4-agent eval + 3-lens panel; the deferred items have no consumer until later
phases):

- **Live shared document + compare-and-swap (F44/N16)** and **session
  layer-native `.touch` persistence** → **TP2 sprint 1** (the document cutover,
  before the MCP tools). CAS coordinates the viewport *and the agent*; the agent
  (second mutator) arrives with MCP, so CAS has nothing to race until then.
- **F45 context-packets module** → **TP2** (feeds the agent's two surfaces).
- **F39 FE click→owning-layer highlight** → **TP3** (needs the Layer Stack panel
  to consume the provenance; backend provenance is done).

**Max not met:** no FE Layer Stack list; robust provenance through booleans/
fillets not done (single-owner attribution on a fused face is a known R-B limit).

## Surprises

- **The bridge kept geometry byte-identical.** Deriving the stack from the
  op-history and reusing `operation_adapter`'s exact per-op emitters (`rhs`,
  threading `body`) meant face-ids and geometry were unchanged — T0–T5 stayed
  green through the Day-6 refactor (risk R-A never bit).
- **The deferrals weren't being tracked.** The day-by-day green tests masked that
  several MIN-as-written deliverables (shared-doc/CAS live, layer-native session
  persistence, FE clickability) were built-but-unwired. An independent eval
  surfaced this; the gap was *bookkeeping*, not code — fixed via the re-scope.
- **Two real bugs** (eval, both reproduced + fixed in `0dc8f58`): provenance
  plane-sign canonicalization was unstable under float noise (could misattribute
  an untouched face after a boolean); a layer-native `.touch` opened via the
  op-history loader silently loaded **empty**. Both now have regression tests.
- **Provenance accuracy limits (M1/M2):** a fused/stacked face gets single-owner
  attribution (wrong for half the face on the common stack-and-fuse case); a
  perfectly *symmetric* trim can be mis-read as untouched. Recorded as known R-B
  limits; robust multi-owner / boundary-signature provenance is a Max/later item.

## Decisions taken mid-phase

- Blocker [2026-06-22-tp1-bridge-rescope](../blockers/2026-06-22-tp1-bridge-rescope.md)
  (soft) — **resolved**: keep the op-history→stack bridge; re-sequence the live
  document cutover to TP2 sprint 1, F45 packets to TP2, F39 FE highlight to TP3;
  reconcile the design-of-record (module map, ADR-0013, `Mesh.face_provenance`)
  with what shipped.
- Day-6 cutover-strategy decision (recorded in conversation + the blocker):
  **bridge / keep op-wire** chosen over a full cutover, to protect the green path.

## Recommended changes for next phase

- **TP2 must do the document cutover FIRST**, before the MCP tools: make the
  shared `LayerStack` the canonical live document with CAS **live**, and switch
  the session save/open to the layer-native `.touch` format — that is the
  substrate the MCP server acts on, and the agent is the first real consumer that
  exercises CAS (N16) and code-layer authoring/persistence.
- Carry the **M1/M2** provenance limits into TP2's risk list — the agent will
  produce more booleans than the click path, so single-owner attribution on fused
  faces will be more visible.
- Add **import-linter contracts** for the pivot modules (`layer_stack` stays
  OCP/executor-free; `layer_bridge`/`live_build` deps) — flagged but not added in
  the architecture reconciliation.
