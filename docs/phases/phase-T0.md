---
id: T0
title: Packaging spike (Electron + Python sidecar + OCP → Windows .exe)
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: []
---

# Phase T0 — Packaging spike

## Goal

Prove Electron + a PyInstaller'd Python sidecar with OCP native libs
packages into a Windows `.exe` that installs and runs on a fresh
non-technical Windows VM — *before* any feature work (ADR-0009 gating
risk for Touch v0).

## Depends on

- No Touch predecessor (T0 is the first Touch phase).
- Architecture: ADR-0009 (Electron + Python sidecar) locked.
- Tooling assumption: GitHub Actions Windows runner is available for
  the cross-build (Linux dev box cannot natively produce a Windows
  installer; cross-building via Wine is out of scope for a spike).

## Minimum deliverable

- A `Touch-spike-0.1.0-setup.exe` installs on a clean Windows VM with
  no prior Python, no prior Node, no admin-required toolchain.
- Launching the `.exe` brings up an Electron window that auto-spawns
  the bundled Python sidecar.
- The renderer connects to `ws://127.0.0.1:<port>` within ~5 s of the
  window opening.
- The sidecar emits a single message on connect: a hardcoded cube
  mesh with per-face IDs baked into a `face_tag_per_triangle`
  attribute.
- three.js renders the cube; mouse hover on a face highlights that
  face **locally** (FE raycaster + face-id lookup, no BE round-trip on
  hover).
- No LLM, no real planner, no `.touch` save, no exports, no settings —
  this spike tests packaging + coupling only.

## Maximum deliverable

- A GitHub Actions workflow that builds the `.exe` on a tag push (early
  validation of F27, even though F27 is officially v0.1 must).
- A headless CI smoke test that launches the produced `.exe` and
  asserts the WS handshake (`TOUCH_READY <port>` on sidecar stdout +
  successful renderer WS connect).
- The bare frontend served as a browser tab against the same sidecar
  on the Linux dev box (proving N5 / N6 — the single FE codebase works
  in both packaged-Electron and browser-dev modes — from day one).

## Sprint / day breakdown

"Day" is a unit of work, not a calendar day. Solo pacing — some take a
calendar day, some take two. All work lives under `spike/` (NOT `src/`)
and is **throwaway** — deleted in T1a / T1b once the real
`src/touch_backend/` lands. The goal is the build/packaging artefacts,
not reusable code.

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Sidecar skeleton on Linux. Python project under `spike/sidecar/` with `touch_sidecar/server.py`: `websockets` server on `127.0.0.1:<random ephemeral port>`, prints `TOUCH_READY <port>` on stdout, emits a single binary message on client connect containing a hand-authored cube mesh with 6 face IDs (vertices + normals + indices + `face_tag_per_triangle`). | `python -m touch_sidecar` runs from a venv and prints the ready line. | A `wscat` (or scripted Python) client connects, reads the binary frame, and parses out 6 distinct face tags across 12 triangles. |
| 2 | Frontend skeleton on Linux. Vite + React + TS project under `spike/web/`; three.js scene; on mount opens a WS to a port from `?port=` URL param; on the first binary frame builds a `BufferGeometry` with the face-id attribute; raycaster reads `face_tag_per_triangle` for the hovered triangle and highlights all triangles sharing that face ID in a different colour. | `npm run dev` serves the FE; `?port=<sidecar port>` connects against the Day-1 sidecar. | In a browser tab pointed at the Linux sidecar, the cube renders; mousing over each of the 6 faces shows a distinct face-coloured highlight; latency feels instant (< 16 ms). |
| 3 | Electron shell on Linux. `spike/shell/main.ts`: spawns the sidecar binary (path-resolved to bundled location), reads `TOUCH_READY <port>` from sidecar stdout, opens a `BrowserWindow` loading the Vite-built `index.html` with `?port=<port>` injected. Supervises: sidecar exit → window closes. | `electron .` from `spike/shell/` brings up a working window with the cube + hover-highlight, sidecar auto-spawned. | The window opens within ~3 s on dev Linux; quitting the window kills the sidecar; killing the sidecar closes the window. |
| 4 | PyInstaller the sidecar (Linux first — confirms the spec before adding Windows variables). `spike/sidecar/build.spec` with explicit `binaries=[...]` block for OCP native libs (audit `OCP.__file__`'s sibling shared libs and ship them all). Hidden-imports audit. `--onedir` (NOT `--onefile`). | A `dist/touch_sidecar/touch_sidecar` directory containing the standalone sidecar binary + libs. | Running the standalone binary from `dist/` on a Linux box with NO Python in PATH still prints `TOUCH_READY <port>` and serves the cube mesh to a `wscat` client. |
| 5 | electron-builder + GitHub Actions Windows build. `spike/shell/package.json` `build` config: bundles the Vite build + the PyInstaller `dist/touch_sidecar/` directory as an extra resource (under `resources/sidecar/`, `asarUnpack`-ed); installs as NSIS; targets Windows x64. `.github/workflows/spike-build.yml`: on tag push matching `spike-v*`, runs PyInstaller (Windows runner, fresh Python) → runs electron-builder → uploads the `.exe` as a release artifact. | Tag-push triggers a CI build; `Touch-spike-0.1.0-setup.exe` appears on the GitHub Release. | `gh release view spike-v0.1.0` shows the `.exe` artifact; the CI run is green; the headless smoke check (Max-goal WS handshake) passes inside the same workflow. |
| 6 | Fresh Windows VM install + verify. Spin up a clean Windows 11 VM (snapshot it the *first* time, revert before each install test). Install the `.exe` as a non-admin user. Launch. Verify the Min deliverable end-to-end. Capture screenshots + cold-start latency. Write `phase-T0-report.md`. | A green/red verdict on Min; the report. | **GREEN** path: the Min checklist holds on the fresh VM → write report → run `/pm-phase-report T0`. **RED** path: file `/pm-blocker` with the specific failure mode; if root cause is fixable in < 2 days, extend the phase; if it is a fundamental PyInstaller+OCP wall, escalate to the ADR-0009 Tauri fallback (which restarts T0 on the Tauri stack, days 1–6 re-run). |

Total: 6 working days. Within the 12-day cap; the 1-day buffer over the
roadmap-gantt's 5-day target absorbs the Day-4-vs-Day-5 split (which
materially lowers the blast radius of R1 — see below).

## Exit criteria

- The Min deliverable holds on a fresh Windows 11 VM: install as a
  non-admin user → launch → cube renders → hover-highlight works → no
  Python or Node prerequisites on the VM.
- Cold-start latency from `.exe` double-click to first rendered frame
  is captured in the phase report (no hard SLA at the spike;
  establishes a baseline for N2 in later phases).
- The GitHub Actions Windows build workflow runs green on a tag push
  (Max — required for the Max-goal claim, optional for Min).
- A browser tab on the Linux dev box, pointed at the same sidecar
  running from a `venv` on Linux, serves the same cube + hover-highlight
  (Max — proves N5 / N6 from day one).
- **OR** the escape hatch fires: `/pm-blocker` filed with the failure
  mode root cause + a recorded decision (extend the phase vs pivot to
  Tauri per ADR-0009).

## Known risks for this phase

| ID | Risk | Mitigation |
|---|---|---|
| R1 | **PyInstaller + OCP native libs.** Highest-probability failure mode. OCP ships large native libs (libTKBRep, libTKMath, libTKernel, …) that PyInstaller's binary-collection step may miss; manifests as a runtime missing-DLL after packaging that didn't appear in dev. | Day-4 PyInstaller spec includes an explicit `binaries=[...]` block enumerating OCP's sibling shared libs (audit `OCP.__file__`'s directory). Day 4 verifies standalone on Linux *before* the Windows variable lands on Day 5, so a failure here is diagnosed without VM overhead. If catastrophic: ADR-0009 escape hatch (Tauri). |
| R2 | **Electron sidecar spawn on Windows.** Process-spawn semantics differ; the bundled sidecar binary path resolution between `resources/app` and `resources/app.asar.unpacked` is a common pitfall. | electron-builder config explicitly places the PyInstaller `--onedir` output under `resources/sidecar/` (NOT inside the ASAR archive; `asarUnpack` rule). `spike/shell/main.ts` resolves the sidecar binary path via `process.resourcesPath`. Tested first in `electron .` dev mode (Day 3) before packaging (Day 5). |
| R3 | **WS connect race.** Electron renderer must wait until the sidecar's WS server has bound the port before connecting; a naive `setTimeout` is fragile across machines. | Sidecar prints `TOUCH_READY <port>` on stdout once the server is listening. Electron `main` reads stdout line-by-line, parses the sentinel, *then* opens the `BrowserWindow` with `?port=<port>`. Renderer retries the connect 3× with backoff before failing visibly. |
| R4 | **Port collision.** A fixed `127.0.0.1:<port>` may already be bound on the user's machine. | Sidecar binds an OS-assigned ephemeral port (`port=0`) and prints the actual port. Main reads + passes downstream. No fixed-port assumption anywhere. |
| R5 | **three.js + per-face-ID mesh.** The cube must be a `BufferGeometry` with a per-triangle face-id attribute; the raycaster must read that attribute to highlight by face (not by triangle). New pattern for this codebase. | Day-2 mesh is hand-authored (6 face tags × 2 triangles each = 12 entries) so the FE wiring is exercised against a deterministic input. Documented as the reference pattern for T1b's real `tessellate` module. |
| R6 | **Windows VM iteration cost.** Setting up a fresh test VM each iteration is slow. | Snapshot a clean Windows 11 install once at the start of Day 6; revert to that snapshot before each install test. Budget at most 3 install/verify cycles per Day 6 — beyond that the failure mode is a phase blocker, not a wrinkle. |
| R7 | **electron-builder signing.** Unsigned installers throw SmartScreen warnings on Windows. | Accepted for the spike — manually click through "More info → Run anyway" on the VM. Signing lands in T13 (auto-update + signed CI build). Phase report must note the SmartScreen prompt as an observed-but-known issue, not a regression. |
| R8 | **Cross-build via CI vs local VM.** GitHub Actions on a Windows runner is the cleanest cross-build path but adds CI-setup overhead on Day 5; a Windows VM with the full toolchain (Python + Node + PyInstaller + electron-builder) installed is workable but slow. | Default path: GitHub Actions. Fallback: if the Actions workflow proves uncooperative on Day 5, do a one-time toolchained Windows VM build as the Min escape hatch (the `.exe` still ships and verifies on Day 6); the CI workflow then becomes a T13 deliverable instead of a T0 Max. |
| R9 | **three.js / WebGL on the Windows VM's virtual GPU.** Fresh Windows VMs default to a software GL renderer; three.js *should* work but may render slowly or fall back unexpectedly. | Enable 3D acceleration in VirtualBox / VMware guest config when creating the snapshot. If real GPU passthrough proves needed, the phase report captures it as a v0 platform requirement for the friend audience (most engineer-friends have real Windows boxes, not VMs). |
