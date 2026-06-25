# Handover — Touch v0, TP2 sprint 1 DONE, sprint 2 (MCP server) is next

> *Start here in any fresh chat session that opens this project. Skim "You are
> here" + "What to do next" in 60 seconds; the rest is reference. When TP2 closes
> (`/pm-phase-report`), rewrite the top two sections for the next phase.*

## You are here

- **Project:** **Touch** — open-source AI-native interactive 3D CAD IDE. A part is
  a **Layer Stack** of build123d code; the user drives it with their **own Claude
  Code over MCP** (subscription, zero API tokens). Pivoted from Maquette
  2026-05-29; pivoted to the Claude-Code/MCP "Layer Stack" model 2026-06-04.
- **Repo** `~/projects/touch`, GitHub `vandpaolo/touch`, package
  `src/touch_backend/`, CLI `touch-backend`. Frontend `web/` (React+Vite+three.js).
- **TP2 is `in_progress`** (`active_phase: TP2`, started 2026-06-22). **Sprint 1
  (the document cutover) is DONE** (6 code commits, 2026-06-25). **Sprint 2 — the
  MCP server + tools — is next** (plan Days 5–7 in [phase-TP2.md](docs/phases/phase-TP2.md)).
- **Scope freeze is ON** (TP2 in_progress): no edits to `00`/`01`/`02`/`03-roadmap`
  design docs until TP2 is `done` or `blocked`. The phase plan + `notes/` are fine.
- **CI is green:** backend **331** passed, web **16** passed; ruff + ruff format +
  pyright + import-linter (14 contracts) + codegen-drift all clean.
- **`main` is pushed** — synced with `origin/main` (HEAD `65f9a98`). Clean tree.

## What's done — TP2 sprint 1 (the document cutover) — READ THIS

The TP1 op-history→stack **bridge is retired.** The single most important thing to
internalize is now the **inverse** of TP1's handover:

> **The `LayerStack` IS the canonical live document.** It is **layer-native**
> (persistence + the wire both speak layers), **shared** (one instance on the
> `Server`, both the viewport and — sprint 2 — the agent act on it), and **CAS'd**
> (every mutation bumps a `revision`; a stale mutation is rejected, N16). The
> op-history `TouchDocument` is **no longer live state** — it survives only as a
> transient read inside `layer_bridge.load_stack` for migrating *old* `.touch`
> files forward. Geometry folds straight from the canonical stack (no bridge).

What landed, in order (all green, all on `main`):

- **D1 (`fca1821`)** — `Session` holds the canonical `LayerStack`; mutations go
  through `add_layer`/`delete_last(expect_rev=head)` (CAS); undo/redo = delete-last
  / re-add of `Layer`s.
- **D2 (`241ab04`)** — **fully layer-native, no op-history compat** (user's call:
  "migrate immediately, no regret"). `.touch` save/open = `save_stack`/`load_stack`.
  The wire dropped op-history: **`MsgDocument` carries `LayerSummary[]` (a compact
  manifest: id/kind/template/params/has_selection, **no source** — N15) + `revision`**;
  `_wire_ops` deleted; FE `doc-store` mirrors layers + revision. (See
  `notes/decisions.md` 2026-06-25 — this folded the wire half of the old D3 into D2,
  because a **code layer has no op form** to serialize.)
- **D3a (`ce4ee68`)** — extracted **`active_document.py`** (`ActiveDocument`: the
  domain — stack + undo/redo + persistence + provenance-baked `rebuild_mesh`).
  `Session` is now the protocol **view** that delegates to it (thin shims kept:
  `Session.stack` property, `_append_op`/`_rollback_last`/`_rebuild_mesh`).
- **D3b (`6c7404d`)** — the `Server` holds **one shared `ActiveDocument`**; every
  `Session` is a view onto it. **Change feed:** a mutation that bumps the shared
  `revision` pushes the new `document` snapshot + mesh to every *other* connected
  viewport; a newly-joined viewport is greeted with current state. Added
  `Session.snapshot_frames()`. Test: two viewports, A's plan appears live on B.
- **D4 (`6786ae9`)** — **`ActiveDocument.add_layer(layer, *, expect_rev)`** is the
  **agent's explicit-CAS entry** (the second-writer path). Race test: two writers
  on the same head → one applied, one `StaleRevisionError` (carries `expected`/
  `head`) → re-plan; stack never corrupts. `tests/test_active_document.py`.

## Seams / deferrals in place for sprint 2 (nothing is broken or stubbed-shut)

- **`ActiveDocument.add_layer(expect_rev=…)` has NO live caller yet** — it is
  built + unit-tested, and its **first caller is the MCP mutating tool (Day 6)**.
  This is the intended seam, not dead code (unlike TP1's CAS, the consumer is days
  away in the same phase). The click path uses `append_op`/`undo`/`redo` (inline
  head read — a single in-process writer can't be stale against itself).
- **The structured *wire* rejection for a stale CAS is not on the wire yet** —
  `StaleRevisionError` already carries `expected`/`head`; the **MCP mutating-tool
  envelope (Day 6)** is where it surfaces to the agent so it re-plans.
- **The change feed broadcasts on any revision change** — including a rolled-back
  failed op (rev advances +2, layers unchanged → a *harmless redundant* re-push of
  current state). Fine for v0; tighten only if it shows up.
- **`MsgOp` (the click-path `op` message) is still emitted**; the FE `applyOp` now
  just marks dirty (the `LayerSummary[]` manifest in the following `document`
  snapshot is authoritative). The agent path won't emit `MsgOp`.
- **`mcp` / FastMCP is NOT a dependency yet** — Day 5's first step adds it to
  `pyproject.toml` (env change: new package + lockfile). The 2026-06-04 spike used
  a throwaway venv at `/tmp/touch-spike` (may vanish on reboot).

## What to do next — TP2 sprint 2 (the MCP server + tools)

Plan: [phase-TP2.md](docs/phases/phase-TP2.md) sprint 2 (Days 5–7). Architecture is
**locked by [ADR-0014](docs/adr/0014-mcp-boundary.md)**: a **separate stdio process
Claude Code spawns**, which **forwards to the running backend over the WS protocol**
and acts on the shared `ActiveDocument` (so the agent + viewport share a part
automatically — sprint 1 built exactly this substrate).

- **Day 5 — MCP skeleton + read-only tools.** Add the `mcp` dep. New module
  `mcp_server` (FastMCP, stdio) that opens a **WS client** to the backend.
  Read tools: `get_model_state`, `get_selection`, `list_layers` (ids+summary+
  thumbnail, **not** source), `get_layer`, `render_view → image`. **This needs new
  WS protocol messages** (`getModelState`/`listLayers`/`getLayer`/`renderView` +
  responses) in `protocol/schema.json` → `make codegen` → backend `Session`
  handlers. Render: `render/orthographic.py` `orthographic(step_path, out_dir)`
  turns the executor's `part.step` into PNGs (headless vtk-osmesa). **Assert a
  non-blank PNG** (the spike used a real 64×64 — the vision API rejects degenerate
  sizes; see render-backend gotchas). Add the `mcp_server` import-linter contract.
- **Day 6 — MCP mutating tools + the structured envelope.** `add_layer`,
  `edit_layer`(**last only**), `delete_layer`(**last only**) through the
  `ActiveDocument.add_layer(expect_rev=…)` CAS path; each returns
  `{ ok|error, render thumbnail, validity (manifold/non-empty), downstream delta +
  finder-rebind warnings }`. `reorder_layer` (and any non-last edit/delete) returns
  a **permanent/non-retryable, actionable append-only refusal** (names
  `delete_layer`→`add_layer` + the last-layer id) — **decided C1, option A**: full
  re-edit/reorder reopens toponaming and stays **T15** (see `notes/decisions.md`
  2026-06-22). An agent test must confirm it re-plans, not retry-thrashes.
- **Day 7 — context packets (F45/N15).** New module `context_packets`:
  `positional(selection)` (selection + owning layer + finder ref + picked point/
  normal + 1-ring + touchable params + revision) vs `macro(stack)` (param table +
  compact layer outline + bbox + units; **no** picked point/1-ring). Finder-ref lint
  (flag raw `.faces()[i]`). Wire into `get_selection`/`get_model_state`.
- **Sprint 3 (Days 8–10)** — drive from the user's own Claude Code (F42, **zero API
  tokens** N14), N15 flat-token validation on a ≥20-edit session, exit benchmark.

**Exit (the agent-path benchmark):** point your own Claude Code at Touch → "build a
part with an extrusion, a hole, and a chamfer" (extrusion + hole as **code layers**,
chamfer as a **template** — decided P1) → it builds via MCP, sees renders, appears
live in the viewport — **zero API tokens** (N14); the two surfaces edit the one
shared doc; a stale-revision edit is rejected + re-planned (N16).

## TP2 decisions already locked (don't re-litigate — see `notes/decisions.md`)

- **C1 → option A**: MCP `edit`/`delete` are **last-layer only**; `reorder` refuses
  (append-only); full re-edit/reorder is T15 (needs T11 evaluator + T12 schema-v2a).
  3 independent evals + author, unanimous.
- **P1**: extrusion + hole render as **code layers**; chamfer stays a **template**.
- **B2/N15**: context-efficiency (per-turn tokens ~flat over ≥20 edits, cache
  hits > 0) is a **Min** deliverable.
- **D2 cutover**: full layer-native, op-history compat dropped entirely.

## Cold-start reading list

1. This file's "What's done — sprint 1" + "Seams/deferrals".
2. [phase-TP2.md](docs/phases/phase-TP2.md) — the day table (sprint 1 marked done,
   sprint 2 next) + risks.
3. ADRs [0014](docs/adr/0014-mcp-boundary.md) (MCP boundary — the sprint-2 spec),
   [0013](docs/adr/0013-shared-live-document.md) (shared doc + CAS — now LIVE),
   [0015](docs/adr/0015-conversation-topology.md) (one brain, two surfaces → context packets).
4. `docs/notes/decisions.md` — 2026-06-22 (C1/P1/N15) + 2026-06-25 (the D2 cutover).
5. [02-classes.md](docs/02-classes.md) module map — note `mcp_server` /
   `context_packets` are marked **NOT BUILT — TP2** (build them this sprint).
   *(The map still describes the TP1 bridge as canonical; it's stale post-cutover
   but frozen under scope-freeze — reconcile at `/pm-phase-report`.)*

## Dev onboarding / key commands

```bash
source .venv/bin/activate
make secrets-decrypt   # writes .env from secrets.env.sops.yaml (needs host age key)
make ci                # ruff + ruff format --check + pyright + lint-imports + pytest
cd web && npm test     # vitest (16 FE tests); npm run typecheck for tsc -b
python -m touch_backend             # start the WS server
touch-backend design "a 50mm cube"  # the headless engine CLI
```

## GOTCHAS (cost real time — read before coding)

1. **Never import `build123d`/`OCP` at a test module's top level.** pytest imports
   every test file at collection, loading the OCP GL layer, poisoning VTK-OSMesa
   for the render test. Import lazily *inside* functions (`tessellate`,
   `live_build.build_mesh`, `active_document.rebuild_mesh` already do). Memory `render-backend`.
2. **`render_view` blank-PNG risk:** OCP-before-render poisons the Mesa GL context →
   blank frames; OSMesa needs an explicit `plotter.render()` before screenshot. The
   STEP→render path runs in a subprocess that never imports build123d (see
   `render/orthographic.py`). Assert a **non-degenerate, non-blank** PNG in Day 5.
3. **`pip install -e .` re-pulls stock `vtk`** and shadows headless `vtk-osmesa`.
   After any reinstall: re-force `vtk-osmesa==9.3.1` from `https://wheels.vtk.org`.
4. **CLI binary is `touch-backend`** (`touch` shadows GNU `/usr/bin/touch`).
5. **Full `pytest` can OOM (exit 137) under `make ci` memory pressure.** It passes
   (~90 s) on its own — if `make ci` gets SIGKILL'd, run the gates separately
   (lint/format/pyright/lint-imports, then `pytest -q -m "not live"`).
6. **Provenance M1/M2 (known R-B):** a fused/stacked face gets single-owner
   attribution; a perfectly *symmetric* trim can read as untouched. The agent emits
   **more booleans than the click path**, so this gets **more visible in sprint 2** —
   the MCP envelope's validity check + render let the agent self-correct.
7. **The executor write-guard hooks `builtins.open` only** (`os.open`/pathlib
   bypass) — a nudge, not a boundary (ADR-0016); the real OS sandbox is later (R13).
8. **VSCode tool-call batching:** keep parallel batches ≤ ~3; sequential for
   git/order-sensitive steps; `run_in_background`, not trailing `&`. Env fix:
   `export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3`.

## Open carry-overs

- **Import-linter contracts for the pivot modules are STILL OWED** (TP1 carry-over,
  not done in sprint 1): `layer_stack` stays OCP/executor-free; `layer_bridge`/
  `live_build`/`active_document` deps; and the new `mcp_server`/`context_packets`
  contracts. The plan folds these into Days 5/7/10. (`lint-imports` shows 14
  contracts today — the pivot ones aren't among them.)
- **F39 FE click→owning-layer highlight + the Layer Stack panel → TP3.** The
  provenance is baked into the mesh (`Mesh.face_provenance`) but not serialized to
  the FE; there's no layer panel in TP2 (the manifest is the wire's layer view).
- **Legacy Maquette `agent/*` Intent pipeline** + `adapters/build123d_target.py`
  still exist, green, off the critical path (the live emitter is `operation_adapter`).
- **`claude-agent-sdk`** is import-guarded; the token-free path is **MCP** (ADR-0014),
  not the SDK (needs a paid key).
- **Stale local branches** `phase/t1a-engine-rename` and `spike/t0-packaging`
  (ahead 2, unpushed) — left untouched; delete only deliberately.
- **`02-classes.md` module map is stale post-cutover** (still calls the bridge
  canonical) — frozen under scope-freeze; reconcile at `/pm-phase-report`.

## Rules in effect

- **Phase discipline:** TP2 is `in_progress` → **scope freeze ON** (no `00`/`01`/
  `02`/`03-roadmap` edits). `/pm-blocker` if a design decision turns out wrong;
  `/pm-phase-report` to close. The phase plan + `notes/` stay editable.
- **Notes capture mid-chat:** noteworthy → append to `docs/notes/*.md`, confirm in
  one line.
- **Auto-memory** at `~/.claude/.../memory/MEMORY.md` loads every session (keys:
  `render-backend`, `ci-checks`, `dev-env`, `collaboration-style`, `browser-dev-hosting`).
