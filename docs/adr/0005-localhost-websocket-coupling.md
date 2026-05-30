# 0005 — Editor↔engine coupling: localhost WebSocket + our own thin protocol

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** vandpaolo
- **Touch-era ADR.** (ADRs 0001–0004 are Maquette-era and remain in
  history; their domain assumptions are superseded by the Touch pivot.)

## Context

Touch is an interactive 3D CAD editor with two hard deployment
constraints (vision § Scope, requirements N4 / N5 / N6):

- It must distribute as a packaged **Windows `.exe`** to non-technical
  engineer friends.
- The developer's **dev environment is headless Linux** — the same
  frontend must run as a plain browser tab during dev.
- Selection / hover / orbit must feel **native-CAD responsive** (N1: <
  50 ms hover→highlight) with **no backend round-trip on selection**.

The kernel is Python (build123d / OCP — see the Maquette engine reuse in
`00-vision.md`) and the frontend is web tech (three.js, TypeScript). The
question is what couples them.

The 2026-05-29 deep-research pass (`docs/notes/inbox.md` § "Architecture
research conclusions") surveyed the field — Onshape, KittyCAD/Zoo,
ocp-vscode, opencascade.js / replicad, etc. — and identified the proven
pattern.

## Decision

**Couple the frontend and the Python kernel as a local client-server
over a single binary WebSocket carrying a thin protocol we define
ourselves.** Specifically:

- The backend runs as a **Python localhost WebSocket server** (the
  *sidecar*) on a configurable port.
- The frontend (Electron renderer in prod, plain browser tab in dev) is
  a **WebSocket client** connecting to `ws://localhost:<port>`.
- The wire is a **single binary WebSocket connection** carrying:
  - **JSON envelopes** for control messages (`plan`, `applyOp`,
    `cancel`, `rebuild`, `exportStep`, `progress`, `conversationTurn`,
    `error`, `ready`, etc.).
  - **Binary frames** for geometry (vertex / normal / index buffers +
    per-triangle face-id tags), each preceded by a tiny JSON envelope
    naming the frame.
- The protocol is **owned by Touch** — schema lives at
  `protocol/schema.json`; TS types + pydantic models are generated from
  it for both ends.
- Picking is **100 % frontend-side**: per-face / per-edge IDs are baked
  into the streamed mesh, three.js raycasts locally, never round-trips
  for hover/click/select. The WS is contacted only on **prompt
  submission**.

## Consequences

- The same web frontend runs as **Electron renderer (prod)** and as a
  **plain browser tab (dev)** with no code divergence — Electron's
  renderer is Chromium, and a browser-tab pointed at the dev sidecar
  consumes the exact same protocol. Satisfies N4 / N5 / N6 from one
  topology.
- Selection feels native-CAD instant (N1) because there is no network
  call between cursor and highlight — the IDs are local.
- WebSocket gives **bidirectional streaming + binary frames + server-
  push** in one mechanism: geometry updates, conversation turns, and
  progress events all flow without polling.
- The local client-server topology generalises cleanly to a future
  hosted version (the same FE can target a remote sidecar) — though
  cross-host concerns (auth, TLS) are explicitly out of v0.
- A protocol we own is **small and purpose-built** — no gRPC / REST /
  WebRTC framework overhead, no impedance mismatch with how a click-and-
  prompt CAD app actually communicates.
- **Cost:** a localhost network port (vs in-process), and the sidecar
  lifecycle to manage (Electron main spawns + supervises the Python
  process — see [ADR-0009](./0009-desktop-shell-electron-sidecar.md)).
- **Cost:** binding to `127.0.0.1` only is enough for v0; if Touch ever
  becomes multi-client or remote, auth becomes its own ADR.

## Alternatives considered

- **In-process IPC (Electron main ↔ Python via stdio / native bindings).**
  Rejected: would not let a browser tab connect (stdio can't be reached
  from a browser), breaking N6. Also awkward for binary mesh data.
- **HTTP / REST with SSE for streaming.** Rejected: no clean
  bidirectional server-push for the conversation+progress pattern;
  requires more framework for less fit.
- **gRPC.** Rejected: browser support requires `grpc-web` + a proxy
  layer — strictly more moving parts for the same delivery as plain WS.
- **WebRTC data channel (à la Zoo/KittyCAD).** Rejected: WebRTC's
  raison d'être is peer-to-peer / NAT traversal / low-latency media; for
  a local single-user app it adds enormous machinery (SDP, ICE, STUN/
  TURN in production) for no benefit. Useful evidence at scale (Zoo
  uses it for *video* streaming from cloud GPUs), not applicable here.
- **Server-rendered pixel streaming (Zoo/KittyCAD's actual model).**
  Rejected: geometry never reaches the client → client-side picking
  becomes impossible; needs cloud GPUs; total over-engineering for a
  local single-user app.
- **In-browser WASM kernel (opencascade.js / replicad / OCP.wasm)** with
  no Python at all. Rejected: ~9 MB brotli cold-start (49 MB raw), and
  it forecloses Touch's long-term plan to grow into Python-ecosystem
  compute (FEA / multibody / control / optimization / ML). The
  Python-strong developer + the future-compute vision both push back.

The chosen pattern is the one already validated by **OCP CAD Viewer
(ocp-vscode)** — Python OCP + `ocp_tessellate` + WebSocket → three.js,
dual VS-Code-webview / plain-browser-tab on `127.0.0.1:3939`. Onshape
runs the same shape at cloud scale.
