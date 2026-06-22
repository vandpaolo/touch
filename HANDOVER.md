# Handover — Touch v0, TP1 DONE, TP2 is next

> *Start here in any fresh chat session that opens this project. Once TP2
> closes (`/pm-phase-report`), rewrite "You are here" + "What to do next" for
> the phase after it. Skim "You are here" + "What to do next" in 60 seconds;
> the rest is reference.*

## You are here

- **Project:** **Touch** — open-source AI-native interactive 3D CAD IDE. A part
  is a **Layer Stack** of build123d code; the user drives it with their **own
  Claude Code over MCP** (subscription, zero API tokens). Pivoted from Maquette
  2026-05-29; pivoted again to the Claude-Code/MCP "Layer Stack" model 2026-06-04.
- **Repo** `~/projects/touch`, GitHub `vandpaolo/touch`, package
  `src/touch_backend/`, CLI `touch-backend`. Frontend `web/` (React+Vite+three.js).
- **No phase active** (`active_phase: null`). **T0–T5 + TP1 are DONE.** **TP2
  (document cutover + MCP server) is next** — not yet planned in detail.
- **Scope freeze is OFF** — design docs editable until a phase goes `in_progress`.
- **CI is green:** backend **326** passed, web **15** passed.
- **⚠️ `main` is 63 commits ahead of `origin/main` and UNPUSHED.** Everything is
  committed; nothing is lost. Decide whether to `git push origin main`.

## What's done — TP1 (Layer Stack backend)

TP1 shipped the Layer Stack **backend primitives** via a deliberate **op-history →
stack bridge**. Read [phase-TP1-report.md](docs/phases/phase-TP1-report.md) +
blocker [2026-06-22-tp1-bridge-rescope.md](docs/blockers/2026-06-22-tp1-bridge-rescope.md)
for the full picture. **The single most important thing to understand:**

> **The op-history (`TouchDocument`) is still the canonical live document** (wire /
> persistence / undo-redo). The **`LayerStack` is *derived* from it per rebuild**
> (`session._rebuild_mesh` → `layer_bridge.layers_from_history` → `live_build.build_mesh`),
> used to fold + cache + bake provenance into the mesh, then discarded. The
> versioned **CAS mutation API and layer-native `.touch`** are built and tested as
> **capabilities with no live caller yet.** Wiring them live is **TP2's job.**

### New backend modules (`src/touch_backend/`) — the pivot set

- `layer_stack.py` — `Layer` / `LayerStack`; deterministic `emit` / `emit_layerwise`;
  `rebuild(*, build, cache)` (injected `build` callable → stays OCP-free);
  per-layer content cache; **`add_layer(layer, *, expect_rev)` / `delete_last` +
  `revision` + `StaleRevisionError` (CAS — built, not wired live)**; `to_dict` /
  `from_dict` (layer-native `.touch`, schema 3).
- `layer_bridge.py` — the **bridge**: `layers_from_history(history)` (op → layer,
  reusing `operation_adapter.rhs` threading `body`; box/cyl/sphere → template,
  finder-chamfer → code); `save_stack` / `load_stack` (+ op-history migration).
  **Not wired into session save/open yet.**
- `live_build.py` — `build_mesh(stack, *, timeout_s)`: `emit_layerwise` → Executor →
  import per-layer solids → `provenance.attribute_stack` → tessellate → bake (F39).
- `provenance.py` — `attribute` / `attribute_stack` / `bake`; trim-independent
  surface-key diff → `created_by`/`last_modified_by` sets baked into `Mesh.face_provenance`.
- `templates.py` — `recognize(source) -> Recognized | None` (exact byte-shape match).
- `operation_adapter.py` — `emit(history)` + **`rhs(operation, prev_var)`** (the
  per-op RHS the bridge reuses; box/cyl/sphere/chamfer).
- `agent/executor.py` — **hardened** (F46): network-off + write-guard preamble,
  secret-scrubbed env, timeout/SIGKILL, soft import-lint. Single chokepoint, stdlib-only.

## What to do next (TP2 — document cutover + MCP server)

Plan stub: [phase-TP2.md](docs/phases/phase-TP2.md). Detail via `/pm-phase-plan TP2`,
then `/pm-phase-start TP2` (runs the pre-phase audit).

**TP2 sprint 1 = the document cutover — do it FIRST, before the MCP tools** (the
roadmap + blocker pin this). MCP needs the shared doc as its substrate, and the
agent is the first real consumer that exercises CAS + code-layer authoring.

1. **Make the shared `LayerStack` the canonical live document.** Today `Session`
   holds a per-connection `TouchDocument`. Cut over so the backend holds **one
   shared `LayerStack`**; route the live mutation path + undo/redo through
   `add_layer` / `delete_last` + **CAS** (revision bump per mutation); switch the
   session save/open to the **layer-native `.touch`** (`save_stack`/`load_stack`).
   The capabilities already exist — this is wiring + retiring the op-history-as-truth.
2. **⚠️ The hard part (the same op↔layer wire tension Day 6 deferred):** the FE
   wire is op-based (`MsgDocument.history: Operation[]`, `MsgOp`, `web/doc-store`).
   Making the stack canonical means the wire/snapshot must carry **layers +
   revision**, which cascades to the protocol schema (`protocol/schema.json` →
   codegen) and the FE doc-store. Decide the wire shape early; this is where the
   risk is. (A freeform **code layer** has no op representation — that's *why* the
   cutover is needed: the agent authors code layers.)
3. **Then the MCP server** (separate stdio proc Claude Code spawns, forwards to
   the backend over the WS protocol): geometry tools (query/select/render→image/
   list/get/add/edit/reorder/delete layer) + the structured mutating envelope
   (F41); **`context_packets`** positional + macro (F45/N15); driven from the
   user's **existing** Claude Code (F42); the agent **sees renders**.
- **Exit (the agent-path benchmark):** point your own Claude Code at Touch →
  "build a part with an extrusion, a hole, and a chamfer" → it builds via MCP,
  sees renders, appears live in the viewport — **zero API tokens** (N14); two
  surfaces edit one shared doc, a stale-revision edit is rejected + re-planned (N16).

## Cold-start reading list

1. [phase-TP1-report.md](docs/phases/phase-TP1-report.md) — what shipped, the
   bridge, the deferrals.
2. [blockers/2026-06-22-tp1-bridge-rescope.md](docs/blockers/2026-06-22-tp1-bridge-rescope.md)
   — why the bridge was kept; what moved where.
3. [03-roadmap.md](docs/03-roadmap.md) §§ TP1/TP2/TP3 (re-sequenced) +
   [phase-TP2.md](docs/phases/phase-TP2.md).
4. ADRs [0013](docs/adr/0013-shared-live-document.md) (shared doc + CAS — has a
   *deferred-live* note), [0014](docs/adr/0014-mcp-boundary.md) (MCP boundary),
   [0015](docs/adr/0015-conversation-topology.md) (one brain, two surfaces).
5. `docs/notes/decisions.md` 2026-06-04 entries — the MCP-first sequencing +
   conversation/context topology (the "why").
6. [02-classes.md](docs/02-classes.md) module map (reconciled to reality) +
   [02-architecture.md](docs/02-architecture.md) "TP1 reality" note (§ Pivot additions).

## Dev onboarding / key commands

```bash
source .venv/bin/activate
make secrets-decrypt   # writes .env from secrets.env.sops.yaml (needs host age key)
make ci                # ruff + ruff format --check + pyright + lint-imports + pytest
cd web && npm test     # vitest (the 15 FE tests); npm run typecheck for tsc
python -m touch_backend             # start the WS server
touch-backend design "a 50mm cube"  # the headless engine CLI
```

## GOTCHAS (cost real time — read before coding)

1. **Never import `build123d`/`OCP` at a test module's top level.** pytest imports
   every test file at collection, loading the OCP GL layer, which poisons
   VTK-OSMesa for the in-process render test. Import lazily *inside* functions
   (`tessellate`, `live_build.build_mesh`, `session._build*` already do; tests use
   a lazy `_cube()` helper). Auto-memory `render-backend`.
2. **`pip install -e .` re-pulls stock `vtk`** and shadows headless `vtk-osmesa`
   (crashes render tests). After any reinstall: re-force `vtk-osmesa==9.3.1` from
   `https://wheels.vtk.org`. Auto-memory `render-backend`.
3. **CLI binary is `touch-backend`, not `touch`** (`touch` shadows GNU `/usr/bin/touch`).
4. **Full `pytest` can OOM (exit 137) under `make ci` memory pressure.** It passes
   (~90 s) when run on its own — if `make ci` gets SIGKILL'd, run the gates
   separately (lint/format/pyright/lint-imports, then `pytest -q`).
5. **Provenance accuracy limits (M1/M2, known R-B):** a fused/stacked face gets
   single-owner attribution (wrong for half the face); a perfectly *symmetric*
   trim can be mis-read as untouched. The agent will produce more booleans than
   the click path, so this gets **more visible in TP2** — carry it into TP2's risk list.
6. **The executor write-guard hooks `builtins.open` only** (`os.open`/pathlib
   bypass) — a nudge, not a boundary (ADR-0016); the real OS sandbox is later.

## Git state (decide: push?)

- On `main`, **63 commits ahead of `origin/main`, unpushed.** All TP1 + the
  eval/re-scope/close commits are plain commits on `main` (no feature branch).
  Recommended: `git push origin main` when ready.
- The **MCP feasibility spike** is at `/tmp/touch-spike` (throwaway — claude
  2.1.132, FastMCP stdio; reference for TP2's MCP shape, not in the repo; may
  vanish on reboot).

## Open carry-overs

- **The document cutover** (TP2 sprint 1) — see "What to do next."
- **F45 context packets** → TP2; **F39 FE click→layer highlight** → TP3.
- **Import-linter contracts for the pivot modules** were flagged but NOT added in
  the architecture reconciliation — add them (e.g. `layer_stack` stays
  OCP/executor-free; `layer_bridge`/`live_build` deps) and verify against the
  real import graph.
- **Legacy Maquette `agent/*` Intent pipeline** + `adapters/build123d_target.py`
  still exist, green, off the critical path (the live emitter is `operation_adapter`).
- **`claude-agent-sdk`** is import-guarded; the token-free path is **MCP** (ADR-0014),
  not the SDK (it now needs a paid key).

## Rules in effect

- **Phase discipline:** `/pm-phase-start` before building (freezes design docs
  while `in_progress`); `/pm-phase-report` to close; `/pm-blocker` if a design
  decision turns out wrong mid-phase.
- **Tool-call batching (VSCode):** keep parallel batches ≤ ~3; sequential for
  git/order-sensitive steps; `run_in_background`, not trailing `&`. Env fix:
  `export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3`.
- **Notes capture mid-chat:** noteworthy → append to `docs/notes/*.md`, confirm in
  one line.
- **Auto-memory** at `~/.claude/.../memory/MEMORY.md` loads every session (key:
  `render-backend`, `ci-checks`, `dev-env`, `collaboration-style`, `browser-dev-hosting`).
