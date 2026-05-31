---
id: T2
title: Frontend skeleton (Vite + React + TS + three.js)
status: in_progress
started: 2026-05-31
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T1b]
---

# Phase T2 — Frontend skeleton

- **Goal:** Stand up the `web/` Vite + React + TypeScript frontend with the
  three.js viewport, NX-style camera, transport layer, and the three-panel
  layout shell. Connect over WebSocket to the existing backend and render a
  backend-served mesh. Not yet interactive beyond camera control — picking,
  prompt, and click-to-prompt are T3.

## Depends on

- **T1b done** — WS server (`python -m touch_backend`), `meshFrame` binary
  protocol, and `protocol/schema.json` all shipped.
- **Generated TS protocol** at `protocol/generated/ts/protocol.ts` (via
  `make codegen`).
- **Architecture** — FE component view + FE dependency rules in
  [02-architecture.md](../02-architecture.md) / [02-classes.md](../02-classes.md).
  ⚠️ **Blocked on a `/pm-architecture` pre-pass** (decided 2026-05-31): name
  the `web/app` F2 shell-owner module, add the browser/Electron **capability
  shim**, and fix the protocol-layout doc drift (R3). Must land before
  `/pm-phase-start T2`.
- **Requirements** F2, F3, F19 (FE half), N1, N5, N6 approved.

## Minimum deliverable

`web/` builds via Vite; opening it in a browser tab shows three panels
(file-tree placeholder left, viewport centre, Settings reachable from a
menu); the viewport renders a static mesh **sent by the backend**;
NX-style camera controls work; `web/transport` connects to
`ws://localhost:<port>`; FE consumes the generated `protocol/generated/ts`
types.

## Maximum deliverable

Also: hot-reload polished; basic styling matches a VS-Code-lite look (dark
theme, the three-panel layout with resizable splits).

## Sprint / day breakdown

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 1 | Scaffold `web/` Vite + React + TS project. `vite.config.ts` with **`base: "./"`** from day one; `tsconfig.json`; `package.json`; `index.html`; `src/main.tsx`. | A buildable Vite app under `web/`. | `npm --prefix web run build` succeeds **and** `npm --prefix web run dev` serves a placeholder page reachable in a browser tab on the dev box. |
| 2 | App-shell layout module (F2): `web/app` owns the three-panel composition — file-tree **placeholder** (left), viewport host (centre), Settings reachable from a menu bar. Static placeholders only. Stub the **capability shim** (browser vs Electron) so native surfaces have a browser no-op path. | `web/app` + a VS-Code-lite skeleton + a capability-shim stub. | Opening the tab shows all three surfaces, all reachable, usable at 1920×1080. *(Depends on the `/pm-architecture` pre-pass naming `web/app` + the shim.)* |
| 3 | Protocol-types wiring: FE imports the generated `protocol/generated/ts/protocol.ts` (via a `web/protocol-types` re-export or path alias); document the regen path in `web` (`make codegen` stays the source). | FE can reference typed protocol messages. | A `web/` module imports a generated message type and `tsc --noEmit` passes; regen path documented. |
| 4 | `web/transport`: WS client class. **Config-driven URL** (default `ws://localhost:<port>`) supporting a *relative* ws path for the future Caddy reverse-proxy (notes/questions.md). Parse JSON envelopes + binary `meshFrame`; emit typed events; handle `ready`. **Vitest unit test** for frame decode against a stub WS. | `Transport` class + a passing Vitest decode test. | Unit (Vitest): decodes a `meshFrame` against a stub WS. Integration: connects to a running `python -m touch_backend`, logs `ready`. |
| 5 | BE dev affordance (decided G1): the sidecar emits a known **connect-time demo mesh** (a cube `meshFrame`) behind a dev flag, so the FE has a real backend frame without picking/prompt. Throwaway — deleted once T3 picking drives real geometry. | A dev-flag path in `session.py` that emits a demo `meshFrame` on connect. | Transport receives a real `meshFrame` (a cube) from the sidecar and decodes its vertices/indices/face-id buffers. |
| 6 | `web/doc-store`: FE document-state mirror (current `Mesh`, history stub, dirty flag); subscribes to transport mesh events. **Vitest unit test** for the apply-mesh path. | `DocStore` + a passing Vitest test. | A transport `meshFrame` updates `DocStore` and a subscriber fires with the typed mesh buffers. |
| 7 | `web/viewport`: three.js scene + render loop; `BufferGeometry` from the `DocStore` mesh (vertices, normals, indices, per-triangle `face_id` attribute); lighting + material; mounts into the centre panel. | `Viewport` class. | Viewport mounts a canvas and visibly renders the backend-served cube. |
| 8 | NX-style camera controls (F3): `OrbitControls` rebound — middle-mouse rotate, shift+middle pan, scroll zoom. | NX camera bindings. | Manual: orbit / pan / zoom on the rendered cube behaves equivalently to NX defaults. |
| 9 | End-to-end exit-criterion verification in a browser tab (dev): connect → BE serves mesh → camera orbits it. Capture a screenshot for the report. | Verified Min path. | The exit criterion below holds, observed live in a browser tab. |
| 10 (Max) | VS-Code-lite dark styling + resizable splits; hot-reload polish (HMR clean on edits to viewport/transport/components). | Styled shell. | Dark theme + three-panel resizable layout; editing a component hot-reloads without a full reconnect. |

## Exit criteria

- In a browser tab on the dev box (browser-dev mode, N5/N6), the FE
  connects to a running `python -m touch_backend` over WebSocket.
- The backend serves a mesh; the viewport renders it.
- NX-style camera controls orbit / pan / zoom that mesh.
- `web/` builds clean via Vite (`base: "./"`); FE consumes the generated
  `protocol/generated/ts` types; `tsc --noEmit` green.

## Known risks for this phase

- **R1 — F2 app-shell owner not in the architecture (pre-T1b audit FAIL #1,
  carried).** The FE module map names `viewport`/`picking`/… but no
  `web/app` (or `web/main`) module owns the three-panel layout. **Resolved
  path (decided 2026-05-31):** a `/pm-architecture` pre-pass names `web/app`,
  adds the capability shim, and fixes R3, *before* `/pm-phase-start T2`
  (scope freeze is OFF). Day 2 is gated on it.
- **R2 — How the FE gets a static mesh without picking/prompt (T3).
  Resolved (G1):** Day 5 adds a connect-time demo `meshFrame` behind a dev
  flag in `session.py`; throwaway, removed when T3 picking lands.
- **R3 — Generated-protocol layout drift.** Architecture says
  `protocol/generated/{ts,py}/`; T1b moved pydantic to
  `src/touch_backend/_generated/` and TS stayed at `protocol/generated/ts/`.
  FE must import from the real TS path; don't trust the doc's `py/` sibling.
- **R4 — No FE toolchain on the dev box yet.** First Vite/React/three install;
  node v24 / electron 38 are pinned (auto-memory `dev-env`), but the `web/`
  workspace, lockfile, and `npm` scripts are all new. Budget setup time.
- **R5 — FE dependency-rule enforcement (`dependency-cruiser`) is specified in
  the architecture but not yet wired. Decided (P2): deferred** to a later
  FE-heavy phase (T3+); T2's module set is too small to be worth it yet.
- **R6 — three.js camera/coordinate conventions.** NX-style rebinding +
  Z-up vs three.js Y-up + perspective-vs-ortho choice can eat time; isolate
  to Day 8 and verify manually.
