# Handover — Touch v0, TP2 sprint 2: Day 5 DONE, Day 6 (mutating tools) is next

> *Start here in any fresh chat session. Skim "You are here" + "What to do next"
> in 60 seconds; the rest is reference. When TP2 closes (`/pm-phase-report`),
> rewrite the top two sections for the next phase.*

## You are here

- **Project:** **Touch** — open-source AI-native interactive 3D CAD IDE. A part is
  a **Layer Stack** of build123d code; the user drives it with their **own Claude
  Code over MCP** (subscription, zero API tokens). Pivoted from Maquette
  2026-05-29; pivoted to the Claude-Code/MCP "Layer Stack" model 2026-06-04.
- **Repo** `~/projects/touch`, GitHub `vandpaolo/touch`, package
  `src/touch_backend/`, CLI `touch-backend`. Frontend `web/` (React+Vite+three.js).
- **TP2 is `in_progress`** (`active_phase: TP2`, started 2026-06-22). **Sprint 1
  (document cutover) DONE** (2026-06-25). **Sprint 2 (MCP server) half-built:
  Day 5 (read tools + in-process render) DONE** (`528085c`, atop D5-prep `ca3fd4f`).
  **Day 6 (mutating tools + the C1 append-only envelope) is NEXT** — the
  consequential day: the agent first *writes* geometry. Plan in
  [phase-TP2.md](docs/phases/phase-TP2.md) sprint 2.
- **Scope freeze is ON** (TP2 in_progress): no edits to `00`/`01`/`02`/`03-roadmap`
  design docs until TP2 is `done` or `blocked`. The phase plan + `notes/` are fine.
- **CI is green:** backend **335** passed, web **16** passed; ruff + ruff format +
  pyright + import-linter (**16 contracts**) + codegen-drift all clean.
- **`main` is pushed** — synced with `origin/main` (HEAD `50995ce`). Clean tree.

## What's done most recently — Day 5 + D5-prep — READ THIS

**D5-prep — the backend is now GL-clean (`ca3fd4f`).** The single most important
new fact:

> **OCP/build123d runs ONLY in worker subprocesses now — never in the long-lived
> backend.** `live_build.build_mesh` appends a `dump_mesh` epilogue to the emitted
> stack and runs it in the executor subprocess (`mesh_dump.py`: tessellate +
> provenance → `mesh.npz`+`mesh.json`), then reconstructs the `Mesh` numpy/json-only.
> So the backend never poisons its OSMesa GL context → **`render_view` renders
> in-process** (no render subprocess). Enforced by import-linter contract #15
> ("backend orchestrator imports no native CAD kernel directly", `allow_indirect_imports`).
> Also advances N8 (a geometry crash kills a worker, not the server) + R13 (the
> executor is now the real OCP chokepoint). Decision: `notes/decisions.md` 2026-06-26.

**Day 5 — MCP read tools (`528085c`).** The user's Claude Code spawns `mcp_server`
(FastMCP, stdio) which forwards to the running backend over a **WS client**, acting
on the one shared `ActiveDocument`. What landed:

- **`mcp_server.py`** — a decoupled wire edge (imports NO engine/geometry module;
  contract #16). Five read tools: `get_model_state`, `list_layers`, `get_layer`
  (pulls source the manifest omits, N15), `get_selection`, `render_view`.
  - WS client = `Backend` (lazy persistent connection, 1 reconnect). No request-id
    in the protocol → it **reads until the matching response `type`**, skipping
    unsolicited change-feed pushes + binary frames (reads are idempotent → safe).
- **7 new WS messages** in `protocol/schema.json` (regen'd): `getModelState`
  (→ reuses the `document` snapshot), `getLayer`→`layerSource`, `getSelection`→
  `selectionState`, `renderView`→`renderResult` (base64 PNG inline). `Session`
  handlers act on `self.doc` (the shared doc).
- **`live_render.py`** — `render_thumbnail(stack, *, timeout_s, size=512) -> bytes`:
  emit → Executor → `part.step` → `render.orthographic.isometric` (in-process,
  GL-clean) → PNG bytes. **Reuse this in Day 6 for the envelope thumbnail.**
- **`mcp~=1.28`** added to deps; `touch-backend-mcp` console entry; also runnable as
  `python -m touch_backend.mcp_server`. WS URL from `$TOUCH_MCP_WS_URL` (default
  `ws://127.0.0.1:8765`).
- Tests: `test_live_render.py` (render gate), `test_mcp_server.py` (full read drive +
  non-blank PNG + structured-error path). **Both render in a clean subprocess** —
  see gotcha #2.

**Sprint 1 recap (the substrate Day 6 builds on).** The `LayerStack` IS the
canonical live document: **layer-native** (persistence + wire speak layers),
**shared** (one `ActiveDocument` on the `Server`; viewport + agent act on it),
**CAS'd** (every mutation bumps `revision`; stale → rejected, N16). The op-history
bridge is retired. Commits: D1 `fca1821`, D2 `241ab04`, D3a `ce4ee68`, D3b
`6c7404d`, D4 `6786ae9`.

## What to do next — Day 6: MCP mutating tools + the structured envelope

The agent's first writes. The CAS substrate is already built (D4) and **gets its
first live caller here.**

- **`ActiveDocument.add_layer(layer, *, expect_rev) -> int`** (built + unit-tested
  D4, **no caller yet**) is the second-writer CAS entry. Day 6 wires the MCP
  mutating tools to it. On a stale `expect_rev` it raises `StaleRevisionError`
  (carries `expected`/`head`) → the envelope tells the agent to re-read + re-plan.
- **New WS messages** (add to `protocol/schema.json` → `make codegen` → `Session`
  handlers): `addLayer` (build123d `source` + `expect_rev`), `editLayer` (last only),
  `deleteLayer` (last only), and a **structured envelope response** (e.g.
  `mutationResult`): `{ ok | error, revision, validity {manifold, non_empty},
  thumbnail (base64 PNG), refusal? {permanent, reason, alternative}, downstream_delta,
  finder_rebind_warnings }`.
- **Mutating MCP tools** in `mcp_server.py`: `add_layer(source)`, `edit_layer(source)`
  (replaces the last layer = delete_last + add), `delete_layer()` (delete_last). Each
  returns the envelope. The agent reads `revision` via `get_model_state`, passes it as
  `expect_rev`.
- **C1 refusal (decided, option A):** `reorder_layer` and edit/delete on a **non-last**
  layer return a **permanent / non-retryable, actionable** refusal envelope — name the
  legal alternative (`delete_layer` then `add_layer`) + the last-layer id. **An agent
  test must confirm it re-plans, not retry-thrashes.**
- **Validity** (manifold / non-empty): compute in the worker (extend `mesh_dump` to
  also write `{manifold, non_empty}` into `mesh.json`, OR a sibling check) — it has the
  solid; the backend stays GL-clean. **Thumbnail:** reuse `live_render.render_thumbnail`.
- **Simplification from C1:** because edits/deletes are **last-only**, there is **no
  downstream** to recompute → `downstream_delta` + `finder_rebind_warnings` are
  trivial/empty in v0 (still include the fields for the Day-7+/T15 shape).
- **Then Day 7** — `context_packets` (positional vs macro, F45/N15) + finder-ref lint.
  **Sprint 3 (Days 8–10)** — drive from the user's own Claude Code (zero API tokens,
  N14), N15 flat-token validation, exit benchmark.

**Exit (agent-path benchmark):** point your own Claude Code at Touch → "build a part
with an extrusion, a hole, and a chamfer" (extrusion + hole as **code layers**,
chamfer as a **template** — P1) → it builds via MCP, sees renders, appears live in the
viewport — **zero API tokens** (N14); the two surfaces edit the one shared doc; a
stale-revision edit is rejected + re-planned (N16).

## The MCP wire shape (Day 5, extend in Day 6)

- Read request → response (matched by `type`): `getModelState`→`document`,
  `getLayer{id}`→`layerSource{id,source}`, `getSelection`→`selectionState{selection|null}`,
  `renderView{size?}`→`renderResult{media_type,image_base64}`.
- `get_model_state`/`list_layers` reuse the `document` snapshot (manifest + revision).
- `get_selection` is a **seam**: backend `Session._current_selection` is `None` until
  the FE reports a pick (Day 9 wires the FE→BE selection report).

## TP2 decisions already locked (don't re-litigate — see `notes/decisions.md`)

- **C1 → option A**: MCP `edit`/`delete` are **last-layer only**; `reorder` refuses
  (append-only); full re-edit/reorder is T15 (needs T11 evaluator + T12 schema-v2a).
- **P1**: extrusion + hole render as **code layers**; chamfer stays a **template**.
- **B2/N15**: context-efficiency (per-turn tokens ~flat over ≥20 edits, cache hits > 0)
  is a **Min** deliverable.
- **D2 cutover**: full layer-native, op-history compat dropped entirely.
- **D5-prep (approach B)**: all OCP behind the worker subprocess boundary; backend
  GL-clean; render in-process. (2026-06-26.)
- **D5 render topology**: `render_view` renders backend-side, in-process, synchronously
  (matches the existing blocking-executor model); base64 PNG inline over the wire.

## Cold-start reading list

1. This file's "What's done most recently" + "What to do next".
2. [phase-TP2.md](docs/phases/phase-TP2.md) — sprint-2 table (Day 5 done + the D5-prep
   note; Day 6 next) + the risks section.
3. ADRs [0014](docs/adr/0014-mcp-boundary.md) (MCP boundary — sprint-2 spec),
   [0013](docs/adr/0013-shared-live-document.md) (shared doc + CAS — LIVE),
   [0015](docs/adr/0015-conversation-topology.md) (one brain, two surfaces).
4. `docs/notes/decisions.md` — 2026-06-22 (C1/P1/N15), 2026-06-25 (D2 cutover),
   **2026-06-26 (D5-prep OCP isolation + D5 render topology)**.
5. Code: `mcp_server.py`, `live_render.py`, `mesh_dump.py`, `live_build.py`,
   `session.py` (the new read handlers), `active_document.py` (the `add_layer` CAS entry
   Day 6 calls).

## Dev onboarding / key commands

```bash
source .venv/bin/activate
make secrets-decrypt   # writes .env from secrets.env.sops.yaml (needs host age key)
make ci                # ruff + ruff format --check + pyright + lint-imports + pytest
cd web && npm test     # vitest (16 FE tests); npm run typecheck for tsc -b
make codegen           # regen protocol bindings after editing protocol/schema.json
python -m touch_backend                 # start the WS server (default ws://127.0.0.1:8765)
python -m touch_backend.mcp_server      # the MCP stdio server (forwards to the backend)
touch-backend design "a 50mm cube"      # the headless engine CLI
```

## GOTCHAS (cost real time — read before coding)

1. **Never import `build123d`/`OCP` at a test module's top level.** pytest imports
   every test file at collection, poisoning VTK-OSMesa. Import lazily inside functions.
   Memory `render-backend`.
2. **Render tests must run in a CLEAN SUBPROCESS.** The backend renders in-process
   (it's GL-clean), but the *pytest* interpreter is OCP-poisoned by sibling suites
   (`test_finder`/`test_tessellate`/… run OCP in-process), so an in-process render in a
   test blanks nondeterministically by order. `test_render.py`, `test_live_render.py`,
   `test_mcp_server.py` all render via `subprocess.run([sys.executable, "-c", script])`.
   **Any new render assertion must do the same.**
3. **`pip install -e .` re-pulls stock `vtk`** and shadows headless `vtk-osmesa`.
   After any reinstall: re-force `vtk-osmesa==9.3.1` from `https://wheels.vtk.org`.
   To add a dep, prefer `pip install <pkg>` (not `-e .`).
4. **CLI binary is `touch-backend`** (`touch` shadows GNU `/usr/bin/touch`). The MCP
   entry is `touch-backend-mcp` / `python -m touch_backend.mcp_server`.
5. **Full `pytest` can OOM (exit 137) under `make ci` memory pressure.** It passes
   (~2 min) on its own — if `make ci` gets SIGKILL'd, run the gates separately
   (lint/format/pyright/lint-imports, then `pytest -q -m "not live"`).
6. **Provenance M1/M2 (known R-B):** a fused/stacked face gets single-owner
   attribution; a symmetric trim can read as untouched. The agent emits **more
   booleans** than the click path → **more visible in Day 6** — the envelope's validity
   check + render let the agent self-correct.
7. **The executor write-guard hooks `builtins.open` only** — a nudge, not a boundary
   (ADR-0016); the real OS sandbox is later (R13).
8. **VSCode tool-call batching:** keep parallel batches ≤ ~3; sequential for
   git/order-sensitive steps; `run_in_background`, not trailing `&`. Env fix:
   `export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3`.

## Open carry-overs

- **Import-linter pivot contracts — PARTIALLY discharged.** Done: orchestrator
  no-OCP (#15, which also enforces `layer_stack` OCP-free), `mcp_server` decoupling
  (#16). **Still owed:** the `context_packets` contract (Day 7) + a final sweep at
  Day 10. (16 contracts today.)
- **F39 FE click→owning-layer highlight + Layer Stack panel → TP3.** Provenance is
  baked into `Mesh.face_provenance` but not yet serialized to the FE.
- **`02-classes.md` is stale** — still calls the TP1 bridge canonical AND marks
  `mcp_server`/`context_packets` "NOT BUILT" (mcp_server is now built). Frozen under
  scope-freeze; reconcile at `/pm-phase-report` (along with a possible ADR for the
  D5-prep OCP-worker boundary).
- **Legacy Maquette `agent/*` Intent pipeline** + `adapters/build123d_target.py` still
  exist, green, off the critical path (the live emitter is `operation_adapter`).
- **`claude-agent-sdk`** is import-guarded; the token-free path is **MCP** (ADR-0014).
- **Stale local branches** `phase/t1a-engine-rename`, `spike/t0-packaging` (unpushed) —
  left untouched; delete only deliberately.

## Rules in effect

- **Phase discipline:** TP2 `in_progress` → **scope freeze ON** (no `00`/`01`/`02`/
  `03-roadmap` edits). `/pm-blocker` if a design decision turns out wrong;
  `/pm-phase-report` to close. The phase plan + `notes/` stay editable.
- **Notes capture mid-chat:** noteworthy → append to `docs/notes/*.md`, confirm in one
  line. Commit work per-day on `main`; push when asked. Commit messages: no
  Co-Authored-By line (user preference).
- **Auto-memory** at `~/.claude/.../memory/MEMORY.md` loads every session (keys:
  `render-backend`, `ci-checks`, `dev-env`, `collaboration-style`, `browser-dev-hosting`).
