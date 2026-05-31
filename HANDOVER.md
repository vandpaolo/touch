# Handover — Touch v0, T1b DONE, T2 is next

> *Start here in any fresh chat session that opens this project. Once
> T2 closes (`/pm-phase-report T2`), rewrite "You are here" + the
> "What to do next" task for the phase after it. Skim "You are here" +
> "What to do next" in 60 seconds; the rest is reference.*

## You are here

- **Project:** **Touch** — AI-native interactive 3D CAD editor
  (click→prompt→evolve), VS-Code-like shell, distributed as a Windows
  `.exe` for engineer friends. Pivoted from Maquette 2026-05-29.
- **Repo dir** `~/projects/touch`, **GitHub** `vandpaolo/touch`, Python
  package `src/touch_backend/`, CLI `touch-backend`, env prefix
  `TOUCH_BACKEND_*`. The rename cascade is fully done.
- **No phase is active** (`active_phase: null`). **T0 + T1a + T1b are
  DONE.** **T2 (frontend skeleton) is next** — not yet planned in detail.
- **Scope freeze is OFF** — design docs editable until a phase goes
  `in_progress`.
- **⚠️ `main` is ~28 commits ahead of `origin/main` and UNPUSHED.** Decide
  whether to `git push origin main` (see "Git state" below). Everything
  is committed; nothing is lost, but origin is stale.

## What's done

- **T0 — packaging spike (DONE, then deleted).** Electron + PyInstaller'd
  Python sidecar (OCP) → admin-free Windows `.exe`, face-tagged cube,
  verified on Windows 11. ADR-0009 holds. The `spike/` tree was deleted in
  T1b day 6 (tags `spike-v0.1.0/.1.1` + PR #1 preserve it).
  [phase-T0-report.md](docs/phases/phase-T0-report.md).
- **T1a — engine rename + dev infra (DONE).** Maquette pipeline → headless
  `touch_backend` (F24); SOPS dev secrets (F29); `/srv/touch/` out_root
  (F30). [phase-T1a-report.md](docs/phases/phase-T1a-report.md).
- **T1b — server + protocol skeleton (DONE; Min met, Max partial).**
  Delivers F19/F20/F21/F22/F31. [phase-T1b-report.md](docs/phases/phase-T1b-report.md).
  The backend now: a localhost WS server speaks a generated protocol,
  plans an `Operation` via a pluggable LLM client, builds **real geometry**
  from it, and streams a face-id'd mesh.

### Backend modules that exist now (`src/touch_backend/`)

- `server.py` — `Server`: websockets/asyncio, binds `127.0.0.1` +
  configurable port (F19); `ready` on connect; per-connection `Session`.
- `session.py` — `Session`: parse→dispatch; `plan` wired end-to-end;
  structured errors (F21, no traceback); `_rebuild_mesh` = emit→executor→
  `import_step`→tessellate.
- `document.py` — `TouchDocument`: in-memory append-only history (load/save
  = T4).
- `planner.py` — `plan(client, prompt, selection) -> Operation` (parses the
  LLM's JSON op; `PlannerError` on bad output).
- `operation_adapter.py` — **NEW** `emit(history) -> build123d source`
  (deterministic; param-only primary kinds box/cylinder/sphere; refuses
  modifiers + profile kinds for now).
- `tessellate.py` — `tessellate(solid) -> Mesh` with per-triangle face IDs
  (F20). **OCP imported lazily** (see GOTCHA below).
- `frames.py` — binary mesh-frame pack/unpack + `meshFrame` envelope.
- `llm_client/` — `LLMClient` Protocol + `AnthropicAPIClient` +
  `ClaudeCodeClient` (import-guarded) + `make_client` (F31).
- `keychain_bridge.py` — `keyring` wrapper for the Anthropic key (F13/N9).
- `config.py` — adds `ws_host`/`ws_port`/`llm_mode`; `out_root` dev default
  `/srv/touch/`.
- `_generated/protocol.py` — generated pydantic models (do not edit; `make
  codegen`). Schema: `protocol/schema.json`; TS bindings:
  `protocol/generated/ts/protocol.ts`.
- **Legacy Maquette `agent/*` Intent pipeline** (planner/worker/executor/
  loop/sanity) + `adapters/build123d_target.py` + `intent.py` still exist,
  green, but **off Touch's critical path** — retired in the deferred
  full `Intent → Operation` refactor (see "Carry-overs").

## What to do next (T2 — frontend skeleton)

Plan stub: [phase-T2.md](docs/phases/phase-T2.md). Detail via
`/pm-phase-plan T2`, then `/pm-phase-start T2` (runs the pre-phase audit).

- `web/` React + TypeScript + Vite; three.js viewport; WS `transport`
  consuming `protocol/generated/ts/protocol.ts`; the VS-Code-like layout.
  Browser-dev mode (N5/N6): the same FE runs as a browser tab against the
  localhost sidecar.
- **Vite `base: "./"`** is required (Electron loads over `file://`; absolute
  base 404s the bundle → blank window). Set it from day one.
- **F2 gap:** the pre-T1b audit flagged that no `web/main` app-shell module
  owns the panel layout (F2). Touch `/pm-architecture` to add it before or
  early in T2.
- Wire the FE WS URL config-driven + a *relative* ws path so the future
  always-on Caddy-hosted browser-dev UI (notes/questions.md) is trivial.

## Dev onboarding / key commands

```bash
source .venv/bin/activate
make secrets-decrypt   # writes .env from secrets.env.sops.yaml (needs host age key)
make hooks             # installs the plaintext-.env pre-commit guard
make codegen           # regenerate protocol bindings (deterministic; commit output)
make ci                # full gate: ruff + ruff format --check + pyright + lint-imports + pytest
python -m touch_backend          # start the WS server
touch-backend design "a 50mm cube"   # the headless engine CLI
```

## GOTCHAS (cost real time this project — read before coding)

1. **`pip install -e .` re-pulls stock `vtk`** (a pyvista dep) and shadows
   the headless `vtk-osmesa`, hard-crashing render tests (`Fatal Python
   error: Aborted`). After ANY reinstall:
   `pip uninstall -y vtk && pip install --force-reinstall --no-deps
   --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1`.
   Installing a single new dep directly (not `-e .`) avoids it.
2. **Never import `build123d`/`OCP` at a test module's top level.** pytest
   imports every test file at collection, loading the OCP GL layer, which
   poisons VTK-OSMesa for the legacy orthographic render test (blank frame),
   regardless of execution order. Import them lazily *inside* functions
   (`tessellate()` and `session._rebuild_mesh` already do; tests use a lazy
   `_cube()` helper). Both gotchas are in auto-memory `render-backend`.
3. **CLI binary is `touch-backend`, not `touch`** — `touch` shadows GNU
   `/usr/bin/touch` inside an active venv.

## Git state (decide: push?)

- On `main`. `main` ≈ 28 commits ahead of `origin/main` (which sits at the
  pre-spike `7960ce7`) — **UNPUSHED**. The spike is removed at HEAD (still
  in history + tags), so pushing `main` now publishes a clean product trunk.
  **Recommended: `git push origin main` soon.**
- `spike/t0-packaging` (PR #1) is kept as the spike record; tags
  `spike-v0.1.0` / `spike-v0.1.1` preserve the artifacts. Don't merge it.
- All T1b work + the repo rename are plain commits on `main` (no feature
  branch). T1a/T1b reports + audits are committed.

## Open carry-overs

- **Full `Intent → Operation` engine refactor** (its own focused effort):
  retire the legacy `agent/*` Intent pipeline + its ~10 tests; add modifier
  geometry (hole/fillet/chamfer/shell/pattern) with finder-resolved
  selection (ADR-0008). `operation_adapter` currently refuses modifiers.
- **Run-folder + `.touch` persistence (T4):** `_rebuild_mesh` uses a tempdir
  per plan; persistent run dirs under `/srv/touch` + load/save land in T4.
- **Bidirectional FE→BE/BE→FE frame contract tests** — write once the FE
  exists (T2).
- **CI:** add a codegen-drift guard (`make codegen` + `git diff --exit-code`);
  bundle the vtk-osmesa swap into a `make dev-install`.
- **3 pre-T1b audit doc-quality FAILs (deferred):** F2 app-shell owner
  (→ T2), `Parameter`/`ClarifyingQuestion` glossary entries,
  `constraints.md` "absorbed into 02-data-model.md" pointer is stale
  (point it at ADR-0004 only). See `docs/audits/2026-05-31-pre-T1b.md`.
- **`claude-agent-sdk`** becomes a hard dep in T6 (currently import-guarded).
- **R10 OCP/OCCT LGPL** `LICENSES/` in the installer before wider
  distribution (≤ T13); code-signing / SmartScreen (R7/R11/R14, T13).
- **Always-on Caddy-hosted browser-dev UI** (notes/questions.md) — T2-era ops.

## Rules in effect

- **Phase discipline:** `/pm-phase-start` before building (scope-freezes
  design docs while `in_progress`); `/pm-phase-report` to close; `/pm-blocker`
  if a design decision turns out wrong mid-phase.
- **Tool-call batching (VSCode):** keep parallel batches ≤ ~3, sequential
  for git/order-sensitive steps, `run_in_background` not trailing `&`. Env
  fix: `export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3`.
- **Notes capture mid-chat:** noteworthy → append to `docs/notes/*.md`,
  confirm in one line.
- **Auto-memory** at `~/.claude/.../memory/MEMORY.md` loads every session
  (key entries: `render-backend`, `ci-checks`, `dev-env`, `collaboration-style`).
