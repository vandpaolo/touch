---
id: TP2
title: MCP server + agent loop (MCP-first)
status: in_progress
started: 2026-06-22
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [TP1]
---

# Phase TP2 — MCP server + agent loop (MCP-first)

- **Goal:** First **the document cutover** (deferred from TP1) — make the shared
  **`LayerStack` the canonical live document** with compare-and-swap **live**;
  then expose Touch's geometry over an **MCP server** the user's **own Claude
  Code** drives, validating the full agent loop on the subscription with **zero
  API tokens**, before embedding (ADR-0013/0014).
- **Min:** **Sprint 1 — the document cutover (before the MCP tools):** the shared
  `LayerStack` is the **canonical** live document; mutations are **compare-and-swap**
  against the head revision (F44/N16 *live*); the session save/open is the
  **layer-native `.touch`** format; the viewport reflects revision changes live;
  **T0–T5 stay green.** **Then:** an **MCP server** (stdio, forwards to the live
  backend over WS) with the geometry tools (`get_model_state` / `get_selection` /
  `render_view→image` / `list_layers` / `get_layer` / `add_layer` /
  `edit_layer`(last) / `delete_layer`(last)) returning the **structured mutating
  envelope** (F41); **positional + macro context packets** (F45/N15); driven from
  the user's **own Claude Code** on the subscription, **zero API tokens**
  (F42/N14); the agent **sees renders and self-corrects**.
- **Max:** downstream-delta / finder-rebind warnings; thumbnail + context tuning;
  multi-edit batching; usage/quota surfacing; the one-brain-two-surfaces
  **ephemeral-subagent** topology (F43 full — otherwise TP3).
- **Exit criterion (agent-path benchmark):** point your own Claude Code at Touch
  → "build a part with an extrusion, a hole, and a chamfer" (positional + macro)
  → it builds via MCP (extrusion + hole as **code layers**, chamfer as a
  **template**), sees renders, appears live in the viewport — **entirely on the
  subscription, zero API tokens** (N14). The viewport and the agent edit the **one
  shared document**; a **stale-revision edit is rejected and re-planned** (N16) —
  the live CAS the cutover wired in. Full CI green (backend + web).
- **Delivers:** F41, F42, F43 (agent loop), F44, F45, N14, N15, N16. *(F44/N16 +
  layer-native `.touch` are wired **live** here, atop the TP1 capabilities.)*

## Depends on

- **TP1 done** — `layer_stack` (versioned stack + CAS + layer-native (de)serialize,
  built **capabilities**), `provenance` (baked into the mesh), `templates`,
  `layer_bridge` (op→layer derivation + migration), `live_build` (mesh + provenance),
  `agent.executor` (workspace-confined, F46), `mesh_cache` — all reused.
- **The bridge re-scope** ([blocker 2026-06-22](../blockers/2026-06-22-tp1-bridge-rescope.md)):
  sprint 1 *is* the deferred live cutover. Op-history is canonical **today** (the
  TP1 bridge); this phase flips canonical to the `LayerStack`.
- **ADR-0013** (shared live doc + CAS), **ADR-0014** (MCP boundary), **ADR-0015**
  (conversation topology / context packets), **ADR-0016** (executor sandbox).
- Requirements **F41, F42, F43, F44, F45, N14, N15, N16**.
- **MCP spike** (2026-06-04, claude 2.1.132, FastMCP stdio): Claude Code ↔ MCP ↔
  **image ingestion** verified — the agent can see tool-returned renders.

## Minimum deliverable

The agent path, end-to-end and token-free, on a cutover live document:

1. The backend holds **one shared active `LayerStack`** as the **canonical** doc
   (not the op-history); every mutation bumps a monotonic **revision** and is
   **compare-and-swap**'d against `expect_rev` (reject → re-plan). Click→prompt,
   undo/redo, and the agent all funnel through this one CAS path.
2. The session **saves/opens the layer-native `.touch`**; an old op-history
   `.touch` **migrates** forward on open.
3. The wire carries the **revision**; the viewport reflects a second writer's
   edits **live** (change feed).
4. An **MCP server** (stdio, FastMCP, forwards to the running backend over a WS
   client) exposes the geometry tools; mutating tools return
   `{ ok|error, render thumbnail, validity (manifold/non-empty), downstream delta
   + finder-rebind warnings }` and go through the same CAS path.
5. **Positional + macro context packets** (F45/N15): id-referenced, finder-ref
   (never raw `.faces()[i]`), renders-on-demand, byte-stable prefix.
6. The user's **own Claude Code** (subscription/OAuth, **no API key**) drives a
   full build, **sees renders, self-corrects** — **zero API tokens** (N14).

**T0–T5 stay green throughout.** Append-only (the MCP `edit_layer`/`delete_layer`
operate on the **last** layer only — re-edit/reorder of earlier layers is T15).

## Maximum deliverable

Richer envelope (downstream-delta + finder-rebind warnings on each mutation);
thumbnail + context-packet tuning; multi-edit batching; usage/quota surfacing;
the F43 **ephemeral-subagent** topology (main thread + positional subagent that
summarizes one line back — otherwise lands with the embedded panel in TP3).

## Sprint / day breakdown

### Sprint 1 — the document cutover (the hard/risky part; before the MCP tools)

> **Re-sequenced during implementation (2026-06-25).** D2 surfaced that a code
> layer can't be serialized over an op-shaped wire, so the **wire layer-manifest +
> revision (originally D3) folded into D2** — the full layer-native cutover (no
> op-history compat) per the user's call (see `notes/decisions.md` 2026-06-25). D3
> is now the remaining live **change-feed** + lifting the active document **above
> the Session** (shared-doc), which is also what D4's two-writer race needs.

| Day | Task | Output | Done when | Status |
|-----|------|--------|-----------|--------|
| 1 | **`LayerStack` becomes the canonical live doc + CAS path.** `Session` holds the canonical `LayerStack` (not an op-history `TouchDocument`); the click→prompt path appends a layer via `add_layer(layer, expect_rev=head)`; undo = `delete_last(expect_rev=head)`, redo re-adds the layer; the head revision is the coordination point. | refactored `session` (canonical stack). | A click→chamfer appends a layer through the CAS API; undo/redo step the stack; the canonical live doc is the `LayerStack`; existing `session`/`server` tests pass; **T0–T5 green**. | **done** (`fca1821`) |
| 2 | **Full layer-native cutover — persistence + wire (absorbed D3's manifest).** Session save → `save_stack`, open → `load_stack` (old op-history migrates). The wire drops op-history: `MsgDocument` carries a compact `LayerSummary[]` manifest + `revision` (codegen regen); `_wire_ops` removed; FE `doc-store` mirrors layers + revision. | layer-native persistence + wire. | Save a part (incl. a code layer) → reopen → identical stack; the app writes layer-native; the wire carries layers + revision; **326 backend + 16 web green**. | **done** (`241ab04`) |
| 3 | **Shared active document + live change-feed.** Lift the active `LayerStack` **above the `Session`** into a `Server`-level shared holder both the viewport WS and the (Day-6) MCP forwarder act on; a second-writer mutation pushes an unsolicited `document` + mesh frame to the viewport (revision-stamped); FE applies agent-originated updates live. | `ActiveDocument` (3a) + shared-doc holder + change feed (3b). | A backend-side mutation on the shared doc pushes `document`(revision) + mesh to a connected viewport; the viewport reflects it; protocol contract green; codegen clean. | **done** (`ce4ee68`, `6c7404d`) |
| 4 | **CAS live end-to-end + stale-rejection.** A mutation carrying a stale `expect_rev` is rejected → caller re-plans; a scripted race (two writers, same rev) → one applied, one rejected. (Second writer simulated; the real agent arrives Day 6.) | `add_layer(expect_rev=…)` CAS entry + race test. | A race test → one applied + one rejected-and-replanned (N16); the stack never corrupts. *(The structured-**wire** rejection lands with the MCP mutating tools in sprint 2, where the agent is the first real second writer.)* **T0–T5 green**. | **done** (`6786ae9`) |

**Sprint 1 (document cutover) complete** — 2026-06-25, all 6 commits green (D1 `fca1821`, D2 `241ab04`, D3a `ce4ee68`, D3b `6c7404d`, D4 `6786ae9`). The `LayerStack` is the canonical, layer-native, shared live document with live CAS + a change-feed; the wire speaks layers + revision. Next: sprint 2 — the MCP server + tools.

### Sprint 2 — MCP server + tools

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 5 | **MCP server skeleton + read-only tools.** Stdio FastMCP process that forwards to the running backend over a WS client; `get_model_state`, `get_selection`, `list_layers` (ids + summary + thumbnail, **not** code), `get_layer`, `render_view → image`. New module `mcp_server` (+ import-linter contract). | `mcp_server` (read path). | A Claude Code lists the tools; a read-only drive (`list_layers` → `get_layer` → `render_view`) returns live state + a real (non-blank) PNG against the live doc; `lint-imports` green with the new contract. |
| 6 | **MCP mutating tools + structured envelope.** `add_layer`, `edit_layer`(last only), `delete_layer`(last only) — through the Day-1/4 CAS path; each returns `{ ok|error, render thumbnail, validity (manifold/non-empty), downstream delta + finder-rebind warnings }`. `reorder_layer` (and edit/delete on a **non-last** layer) returns a structured **append-only refusal**: `permanent`/non-retryable + names the legal alternative (`delete_layer` then `add_layer`) + the last-layer id (C1). | mutating MCP tools. | An MCP `add_layer` builds a layer on the live doc via CAS, returns the envelope (thumbnail + manifold check), appears live in the viewport; a stale `add` is rejected; `reorder` / non-last-edit refuse with a **permanent, actionable** envelope; an agent test confirms it re-plans (delete-last → re-add) rather than retry-thrashing. |
| 7 | **Context packets (F45/N15).** `context_packets.positional(selection)` (selection + owning layer + finder ref + picked point/normal + 1-ring + touchable params + revision) vs `macro(stack)` (param table + compact layer outline + bbox + units; **no** picked point/1-ring); wire into `get_selection`/`get_model_state`. Finder-ref lint (flag raw `.faces()[i]`). | `context_packets` (+ lint). | The two packets differ exactly as specified; generated layer code references geometry via finder helpers (lint flags raw indices); `lint-imports` green with the `context_packets` contract. |

> **D5-prep inserted during implementation (2026-06-26).** Wiring `render_view`
> surfaced that the backend process was permanently OSMesa-poisoned (`build_mesh`
> imported OCP in-parent), so it could never render. Rather than a render-only
> workaround, the root cause was fixed first: **all OCP work was isolated to the
> `mesh_dump` worker subprocess so the backend stays GL-clean** and renders
> in-process (commit `ca3fd4f`; decision + rationale in `notes/decisions.md`
> 2026-06-26 — combined-worker, approach B). This also advances N8 (crash
> isolation) + R13 (the executor is now the real OCP chokepoint). Candidate for a
> short ADR + `02-architecture` reconcile at `/pm-phase-report`.

**Day 5 done** — 2026-06-26, commit `528085c` (atop `ca3fd4f` D5-prep). The
`mcp_server` (FastMCP stdio + WS client) exposes the five read tools
(`get_model_state` / `list_layers` / `get_layer` / `get_selection` /
`render_view`); seven new WS messages + codegen + Session handlers on the shared
doc; `render_view` rasterises **in-process** on the GL-clean backend (non-blank
PNG proven end-to-end in a clean subprocess); `mcp_server` import-linter contract
(16 contracts kept). backend 335 + web 16 green. `get_selection` is the Day-9
seam (returns null until the FE reports a pick). Next: Day 6 — mutating tools +
the C1 append-only envelope.

### Sprint 3 — agent loop + benchmark

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 8 | **Drive from the user's own Claude Code, token-free (F42/N14).** Ship the MCP config; a subscription Claude Code (no API key in env) connects, calls a mutating tool, sees the render, **self-corrects** on the envelope. | working agent loop. | A subscription Claude Code drives an add→render→correct loop on the live doc; **network/billing inspection shows zero `api.anthropic.com` token usage** (N14). |
| 9 | **Context efficiency + two-surface consistency (N15/N16).** A ≥20-edit session: per-turn input tokens stay roughly flat (id-referenced, thumbnails-on-demand), prompt-cache read-hits non-zero; the viewport reflects agent edits live and the agent reads the viewport's selection. | N15/N16 validated. | On a ≥20-edit run, per-turn tokens are ~flat (not O(layers)), cache hits > 0, renders sent only on demand; agent edit → viewport updates; `get_selection` returns the viewport's live pick. |
| 10 | **Exit benchmark + CI.** Run the agent-path benchmark end-to-end (extrusion + hole as code layers, chamfer as a template; positional + macro); run a stale-revision-rejected case; full CI (backend + web). | verified phase. | The exit criteria below hold live; `make ci` + `cd web && npm test` green; import-linter contracts (incl. the TP1-owed pivot-module contracts) green. |

## Exit criteria

- Point your **own Claude Code** (subscription, no API key) at Touch → "build a
  part with an extrusion, a hole, and a chamfer" → it builds **via MCP**
  (extrusion + hole as **code layers**, chamfer as a **template**), **sees
  renders**, the part **appears live** in the viewport — **zero API tokens** (N14).
- The viewport and the agent edit the **one shared `LayerStack`**; the session
  saves/opens the **layer-native `.touch`**; an old op-history `.touch` migrates.
- A **stale-revision edit is rejected and re-planned** (N16); the stack never
  corrupts.
- Per-turn context stays roughly **flat** over a ≥20-edit session (N15).
- **T0–T5 remain green**; full CI passes; import-linter contracts green.

## Known risks for this phase

- **R-A (load-bearing) — the op↔layer cutover regresses the green path and
  cascades.** Flipping canonical from the op-history to the `LayerStack` touches
  T3–T5's working undo/redo, the protocol schema (revision + change feed), and the
  FE `doc-store`. *Mitigation:* sprint 1 *first*, gated on **T0–T5 green** as the
  exit; the wire change (Day 3) is its own step after the backend cutover (Day 1)
  so a pause leaves a coherent state; the TP1 bridge stays available as a
  fallback derivation if the live cutover regresses.
- **M1/M2 — provenance single-owner on fused faces** (TP1 R-B carry-over). The
  agent emits **more booleans** than the click path, so single-owner attribution
  on a stacked-and-fused face will be **more visible**. *Mitigation:* documented
  R-B limit; the envelope's validity check + render lets the agent self-correct;
  robust multi-owner / boundary-signature provenance stays a Max/later item.
- **R14 — MCP surface / subscription-policy churn.** *Mitigation:* spike-verified
  2026-06-04; the built-in API planner (F22) stays the no-account fallback; the
  engine stays MCP-neutral.
- **R15 — context bloat ("memory stacks").** *Mitigation:* N15 — id-referenced
  state, finder refs, renders/thumbnails on demand, byte-stable prefix; validated
  on the ≥20-edit Day-9 run. (The ephemeral-subagent topology that further bounds
  this is TP3 / a Max item here.)
- **R13 — agent-authored code is the executable document (RCE/reliability).**
  *Mitigation:* the workspace-confined executor (F46, TP1) is the single
  chokepoint; per-layer render-and-validate envelope; append-only blast radius.
  (Real OS sandbox before opening untrusted parts — later, R13/T15.)
- **Render path — blank PNGs.** `render_view` depends on the headless render
  backend (vtk-osmesa); known OCP/OSMesa GL conflict + explicit-`render()`
  gotchas can yield blank images the agent can't see. *Mitigation:* assert a
  non-degenerate, non-blank PNG in the Day-5 done-when (the spike used a real
  64×64 because the vision API rejects degenerate sizes).
- **Append-only vs F41's `edit`/`reorder` tools (resolved C1, option A).** F41
  names `edit_layer` + `reorder_layer`, but v0 is append-only (F38; re-edit/reorder
  reopens toponaming, R16/T15). *Resolution (3 independent evals + the plan author,
  unanimous, high confidence):* `edit`/`delete` are **last-layer only**; `reorder`
  (and any non-last edit/delete) returns a **structured, permanent/non-retryable
  refusal** naming the legal alternative + the last-layer id. Full re-edit/reorder
  stays **T15** (needs T11 evaluator + T12 schema-v2a first). *Residual risk:* a
  poorly-worded refusal makes a persistent agent retry-thrash — mitigated by the
  Day-6 done-when (permanent/actionable envelope + an agent re-plan test).
