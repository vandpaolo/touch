---
phase: T0
title: Packaging spike (Electron + Python sidecar + OCP → Windows .exe)
status: done
started: 2026-05-30
finished: 2026-05-30
min_goal_met: true
max_goal_met: partial
---

# Phase T0 Report — Packaging spike

## Summary

The load-bearing v0 risk is **cleared**. Electron + a PyInstaller-frozen
Python sidecar carrying OCP's native OCCT libraries packages into a Windows
NSIS `.exe` that installs without admin, auto-spawns the sidecar, connects
over a localhost WebSocket, and renders a face-tagged cube in three.js with
working local per-face hover-highlight — verified on a real Windows 11 laptop
from a clean install. ADR-0009's primary stack holds; the Tauri escape hatch
was not needed. All six "days" of work landed in a single session under
`spike/` (throwaway), and the Windows build went green on the **first** tag
push (`spike-v0.1.0`), with one follow-up (`spike-v0.1.1`) to fix a renderer
asset-path bug that only surfaced in the packaged `file://` load.

## Goal vs. outcome

| Goal | Planned | Actual | Status |
|------|---------|--------|--------|
| Min  | `.exe` installs on a clean no-Python/no-Node/no-admin Windows machine → Electron window → spawns sidecar → WS connect → three.js renders hardcoded face-tagged cube → local hover-highlight | All of it, confirmed on a real Windows 11 laptop. Status bar reported `mesh: 8 verts, 12 tris, 6 faces`; all 6 faces highlight distinct colours on hover, instantly. | ✅ |
| Max  | GH Actions Windows build on tag push + headless CI smoke (WS handshake) + same FE in a browser tab against the Linux sidecar (N5/N6) | CI build ✅ (green first try); CI smoke ✅ (asserts OCP_SELFCHECK volume=1000.0 + TOUCH_READY on the frozen `.exe`); browser-tab N5/N6 path ⚠️ wired (`host: true`, `?port=`) and exercised headlessly via wire-parity check, but not visually demonstrated in a browser tab this session. | ⚠️ partial |

## What shipped

All under `spike/` (throwaway; deleted in T1a/T1b). Commits on branch
`spike/t0-packaging` (PR #1), not yet merged to `main`.

- **Day 1** (`fab21c7`) — `spike/sidecar/`: `websockets` server on an
  ephemeral `127.0.0.1` port (R4), prints `TOUCH_READY <port>` (R3), emits a
  binary cube mesh frame (8 verts / 12 tris / 6 face tags). Wire format
  matches `docs/02-data-model.md` §Mesh (`wire.py`); `edge_tag_per_segment` +
  `face_id_to_finder_hint` JSON envelope deferred to T1b.
- **Day 2** (`520f453`) — `spike/web/`: Vite + React + TS + three.js viewport.
  `src/wire.ts` mirrors `wire.py`; non-indexed `BufferGeometry`; raycaster
  `faceIndex` → `face_tag_per_triangle` O(1) lookup → local hover-highlight,
  no BE round-trip (N1). The reference picking pattern for T1b's real
  `tessellate`.
- **Day 3** (`46c44db`) — `spike/shell/`: Electron main spawns the sidecar,
  parses `TOUCH_READY` before opening the window (R3, no timeout race), injects
  `?port=`, supervises both directions. `sidecar.ts` kept Electron-free so the
  spawn/ready logic is headless-testable (`npm run smoke` → `SMOKE_OK`).
- **Day 4** (`9439046`) — **R1 proven on Linux.** Sidecar imports OCP and runs
  a real OCCT computation at startup (`ocp_check.py`: box volume = 1000.0).
  `build.spec` collects OCP's vendored native libs; `--onedir`, no UPX (R11).
  Frozen 679–692 MB bundle runs under `env -i` with no Python on PATH.
- **Day 5** (`d4e9e41`) — electron-builder NSIS config (`extraResources`
  bundles web + sidecar; `perMachine:false` + `oneClick:false`, R13) +
  `.github/workflows/spike-build.yml` (tag `spike-v*` → Windows runner →
  PyInstaller → frozen-`.exe` pwsh smoke → vite build → NSIS → Release upload).
- **Day 6** (this report) — installed `Touch-spike-0.1.0-setup.exe` (from
  release `spike-v0.1.1`) on a real Windows 11 laptop. Min deliverable
  confirmed end-to-end.
- **Fix** (`e5d5c39`) — relative Vite `base: "./"` (see Surprises).

CI: `spike-v0.1.0` run (first tag) green end-to-end; `spike-v0.1.1` green with
the renderer fix. Installer artifact ≈ 175–184 MB (NSIS-compressed).

## What slipped / deferred

- **Browser-tab N5/N6 visual demo** — the dual-mode FE is wired and was
  exercised headlessly (wire-parity check), but not shown live in a browser
  tab against the Linux sidecar. Cheap to demo later; the architecture is
  proven, only the screenshot is missing. Carries as a Max-goal footnote, not
  a T1 blocker.
- **Cold-start latency baseline** (an exit-criterion line item) — not formally
  timed this session. Observationally "a few seconds" double-click → cube.
  Establish a real number when T2/T3 wire the actual app; no SLA at the spike.
- **R10 — OCP/OCCT LGPL redistribution** — a `LICENSES/` dir was NOT added to
  the installer this session. Because the spike was published to a personal
  GitHub Release, this should be addressed **before any wider distribution**.
  Carries to T13 (release hardening) at the latest; flag if friends get builds
  sooner.
- **Code-signing / SmartScreen / Defender (R7, R11, R14)** — deliberately out
  of scope; deferred to T13. SmartScreen "Run anyway" was hit as expected.

## Surprises & lessons

1. **OCP's native libs are not where the plan assumed (R1 nuance).** The plan
   said "audit `OCP.__file__`'s sibling shared libs" — but `cadquery-ocp`
   vendors its ~200 OCCT libs in a sibling dir named after the *distribution*
   (`cadquery_ocp.libs/`, plus `vtkmodules/`), **not** `OCP.libs/`. The first
   `build.spec` hardcoded `OCP.libs/` and failed loudly (the guard caught it
   pre-bundle). Fix: discover the lib dirs by globbing `*.libs` + `vtkmodules`,
   which is also **cross-platform** (Linux auditwheel + Windows delvewheel) —
   an earlier `ldd`-based version was Linux-only and would have failed on the
   Windows runner. Lesson for T1b: never hardcode the wheel-vendored lib path.
2. **Packaged-app blank window: Vite `base` (`e5d5c39`).** The first Windows
   `.exe` opened a blank window — the renderer's JS 404'd as
   `file:///C:/assets/index-*.js`. Vite's default `base: "/"` emits absolute
   asset paths that, over Electron's `file://`, resolve to the drive root.
   Fix: `base: "./"`. Invisible in dev (Days 2–3 served over `http://`), only
   the packaged `file://` load exposed it. Lesson for T2: set relative base in
   the real frontend from day one.
3. **R1 was real but tractable.** The highest-probability failure mode did
   bite (lib discovery), but the Day-4-on-Linux-first split meant it was
   diagnosed without any Windows/VM overhead — exactly the blast-radius
   reduction the plan intended. The frozen sidecar's startup OCCT self-check
   (volume = 1000.0) turned "did the libs come along?" into a one-line pass/fail
   that runs identically on Linux, in CI, and on the user's laptop.
4. **CI Windows build was clean first-try** — once the spec was cross-platform.
   `setup-python@3.12` (R12) + the glob-based lib collection meant delvewheel's
   layout "just worked." No DLL-hell iteration, contrary to expectation.
5. **GitHub VM (laptop) > clean VM for this audience.** Verified on a real
   Windows 11 laptop with a real GPU rather than a snapshotted VM (R6/R9).
   That's the more representative test for the "engineer friends" audience and
   sidestepped the software-WebGL worry (R9) entirely.
6. **Process: the harness tool-output layer was unreliable this session**
   (empty/duplicated/occasionally fabricated results under high tool-call
   parallelism in the VSCode extension). Mitigated mid-session by capping
   batches (`CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3` + a CLAUDE.md rule,
   `99ec01e`) and verifying every result against on-disk files. Captured so
   T1+ doesn't relearn it.

## Carryover into next phase (T1a)

- **Repo/dir rename** `maquette/` → `touch_backend/` (tracked pre-existing
  carry-over) is the T1a headline; `spike/` stays untouched until T1b deletes
  it.
- **Reusable patterns proven here** (rebuild fresh in `src/`, don't salvage the
  throwaway code): the `TOUCH_READY` ready-handshake; ephemeral-port handoff;
  the `face_tag_per_triangle` mesh frame + raycaster picking; the glob-based
  OCP lib-collection `build.spec`; the relative-Vite-base requirement; the
  electron-builder `extraResources`/`perMachine:false` config.
- **Open spike items** to fold into later phases: R10 LICENSES (≤ T13, sooner
  if distributing), code-signing (T13), cold-start latency baseline (T2/T3),
  browser-tab N5/N6 visual demo, and the cosmetic artifact-name-vs-git-tag
  version mismatch (the `.exe` is hardcoded `0.1.0`).
- **Branch state:** `spike/t0-packaging` (PR #1) is unmerged on `main`. Decide
  merge vs. leave-as-spike-record before T1a starts.

## Metrics

- **Commits:** 8 spike/doc commits (`fab21c7` → `e5d5c39`) on `spike/t0-packaging`.
- **CI:** 2 green Windows builds (`spike-v0.1.0`, `spike-v0.1.1`); first build
  passed all steps first try.
- **Artifacts:** frozen sidecar bundle ≈ 679–692 MB (`--onedir`); NSIS
  installer ≈ 175–184 MB; 92 `libTK*` OCCT libs collected.
- **Stack (observed):** Python 3.12, `cadquery-ocp` 7.8.1.1, node v24, electron
  38, pyinstaller 6.20, vtk 9.3.1.
- **Bugs found & fixed:** 2 (OCP lib-dir discovery; Vite absolute base).
- **Calendar:** Days 1–6 + fix completed in a single session, 2026-05-30.
