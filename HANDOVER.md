# Handover — Touch v0, phase T0 in_progress, Days 1–4 done, Day 5 next

> *Start here in any fresh chat session that opens this project. Once
> T0 closes (`/pm-phase-report T0`), rewrite "You are here" + the
> "What to do next" task for T1a. Keep this short enough to read in
> 60 seconds.*

## You are here

- **Project:** **Touch** — AI-native interactive 3D CAD editor (click→prompt→evolve), VS-Code-like shell, distributed as a Windows `.exe` for engineer friends. **Pivoted from Maquette** on 2026-05-29 via a full re-baseline cascade (`/pm-vision` → `/pm-requirements` → `/pm-architecture` → `/pm-roadmap`).
- **Repo dir is still `maquette/`** and `src/` is still `src/maquette/` — the rename to `touch_backend/` is a T1a chore.
- **Active phase:** **T0 — Packaging spike** (Electron + PyInstaller'd Python sidecar + OCP → Windows `.exe`). Started 2026-05-30. Status `in_progress`. **Scope is now frozen** on Touch design docs.
- **Days 1–4 done + committed** (all built and verified on the Linux dev box). **Day 5 (electron-builder + GH Actions Windows build) is next** — needs a Windows runner, can't be produced/verified on Linux. Plan: [`docs/phases/phase-T0.md`](docs/phases/phase-T0.md).
- **Last commit:** `3556baf` (Day 4). **All Touch commits are LOCAL/unpushed** — a direct push to `main` was denied (PR-only); publish via a branch/PR. Pushed remote is still at `7960ce7` (architecture).

## What changed (Maquette → Touch)

- Maquette v0 **shipped** under the prior product. Its docs+phases stay in git as historical record (`docs/phases/phase-0.md … phase-3.5-report.md`, ADRs 0001–0004).
- Touch design is fresh: [`docs/00-vision.md`](docs/00-vision.md), [`docs/00-pr-faq.md`](docs/00-pr-faq.md), [`docs/01-requirements.md`](docs/01-requirements.md) (F1–F31 / N1–N12), [`docs/02-architecture.md`](docs/02-architecture.md), [`docs/02-data-model.md`](docs/02-data-model.md), [`docs/02-classes.md`](docs/02-classes.md), ADRs [0005](docs/adr/0005-localhost-websocket-coupling.md)–[0009](docs/adr/0009-desktop-shell-electron-sidecar.md), [`docs/03-roadmap.md`](docs/03-roadmap.md) (Touch phases T0–T15).
- The Maquette engine (planner / intent / adapter / pricing / config) gets renamed + carried over in **T1a**; not relevant to T0.

## Active phase: T0 — Packaging spike

- **Why first:** [ADR-0009](docs/adr/0009-desktop-shell-electron-sidecar.md) — the load-bearing v0 risk is whether Electron + PyInstaller + OCP's native libs actually package into a working Windows `.exe`. Prove it before any feature work. Tauri is the documented fallback if the spike fails.
- **Min:** `.exe` installs on a clean Windows VM (no Python, no Node, no admin), opens an Electron window, spawns the Python sidecar, three.js renders a hardcoded cube with per-face IDs, hovering a face highlights it locally (no LLM, no `.touch`, no exports).
- **Max:** GitHub Actions Windows-runner build on tag push + headless CI smoke check + the same FE in a browser tab against the Linux-running sidecar (proves N5/N6 from day one).
- **All code under `spike/`** (NOT `src/`) — throwaway, deleted in T1a/T1b.
- **6 days, R1–R14** in the plan. Pre-phase audit: [`docs/audits/2026-05-30-pre-T0.md`](docs/audits/2026-05-30-pre-T0.md) (12/12 PASS after addendum).

## Progress so far (Days 1–4, all committed + verified on Linux)

Headless verify: `bash spike/verify_all.sh` → ALL-PASS (Days 1–3).
Day-4 build: `bash spike/sidecar/build_sidecar.sh` → ALL-PASS (`BUILD_RESULT.txt`).

- **Day 1** (`fab21c7`) — `spike/sidecar/`: `websockets` server, ephemeral
  port, prints `TOUCH_READY <port>`, emits the binary cube frame (8 verts /
  12 tris / 6 face tags). Wire format matches [`02-data-model.md`](docs/02-data-model.md) §Mesh
  (`wire.py`); edge tags + finder-hint JSON envelope deferred to T1b.
- **Day 2** (`520f453`) — `spike/web/`: Vite + React + TS + three.js viewport.
  Decodes the frame (`src/wire.ts` mirrors `wire.py`), non-indexed geometry,
  raycaster `faceIndex` → `face_tag_per_triangle` local hover highlight.
  Build green; FE↔BE wire parity verified. **Visual render+hover is the only
  unchecked part — needs a real display.**
- **Day 3** (`46c44db`) — `spike/shell/`: Electron main spawns the sidecar,
  waits for `TOUCH_READY` (R3, no timeout race), opens the viewport with
  `?port=` injected, supervises both directions. `sidecar.ts` is Electron-free
  so `npm run smoke` validates spawn+ready+WS frame headlessly → `SMOKE_OK`.
  **Windowed run needs a display (Electron aborts headless).**
- **Day 4** (`3556baf`) — **R1 proven on Linux.** Sidecar now imports OCP and
  runs a real OCCT compute at startup (`ocp_check.py`: box volume=1000.0).
  `build.spec` discovers OCP's auditwheel libs via `ldd` on the extension
  (they live in `cadquery_ocp.libs/` + `vtkmodules/`, NOT `OCP.libs/`) and
  collects them; `--onedir`, no UPX. The **frozen 679 MB binary runs under
  `env -i` with NO Python on PATH**: OCP_SELFCHECK volume=1000.0 → TOUCH_READY
  → serves the cube. The single highest-risk unknown, now de-risked on Linux.

## What to do next (Day 5 — needs a Windows runner)

**electron-builder + GitHub Actions Windows build** — see [`docs/phases/phase-T0.md`](docs/phases/phase-T0.md) Day 5 row.

- `spike/shell/package.json` `build` config: bundle the Vite build + the
  PyInstaller `dist/touch_sidecar/` dir under `resources/sidecar/`
  (`asarUnpack`-ed); NSIS, Windows x64; `nsis.perMachine:false` +
  `oneClick:false` (R13, non-admin install).
- `.github/workflows/spike-build.yml`: on tag `spike-v*`, Windows runner,
  `setup-python` pinned to 3.12 (R12) → PyInstaller → electron-builder →
  upload `.exe` to a Release. Add the headless WS-handshake smoke (Max goal).
- The Linux box **cannot** produce/verify a Windows installer — Day 5 runs in
  CI, Day 6 is the fresh-Windows-VM verify (yours). `main.ts` already resolves
  the packaged sidecar at `process.resourcesPath/sidecar` (R2).

## Stack (locked)

- Python 3.12.x (pin in `spike/sidecar/pyproject.toml`); `websockets`; `OCP` (only loaded later — Day 1 doesn't need build123d, the cube is hand-authored).
- Node + Vite + React + TypeScript + three.js (Day 2).
- Electron + electron-builder (Day 3 + 5).
- PyInstaller `--onedir` (Day 4).
- GitHub Actions Windows runner (Day 5).

## Where things live

- Long-form thinking: `docs/notes/*.md` (decisions, constraints, inbox, questions, wishes).
- Design (frozen): `docs/00-*`, `docs/01-*`, `docs/02-*`, `docs/adr/`, `docs/03-roadmap.md`.
- This phase: `docs/phases/phase-T0.md`. Touch future phases: `phase-T1a.md` … `phase-T15.md` (stubs only).
- Maquette historical: `docs/phases/phase-0.md … phase-3.5-report.md` (DO NOT modify).
- Audits / blockers: `docs/audits/`, `docs/blockers/`.
- This file (always reread): `HANDOVER.md`.

## Rules in effect

- **Scope freeze.** No edits to `docs/00-*`, `docs/01-*`, `docs/02-*`, `docs/adr/`, `docs/03-roadmap.md` while T0 is `in_progress`. If something in design needs to change, run `/pm-blocker` first.
- **Phase report** when Day-6 exit criteria are met: `/pm-phase-report T0`.
- **Notes capture mid-chat:** when the user says something note-worthy (a new constraint, decision, reference), append it to the right `docs/notes/*.md` and confirm in one line.
- **Auto-memory** at `~/.claude/projects/-home-vandpaolo-projects-maquette/memory/MEMORY.md` is loaded into every conversation. Update on new user preferences / feedback.

## Open carry-overs (none blocking T0)

- Repo dir rename (`maquette/` → `touch/`) and CLAUDE.md/README rewrite is a downstream T1a chore tracked in `docs/notes/inbox.md` + `docs/notes/decisions.md`.
- F27 (auto-update + signed CI) officially v0.1 (T13). T0 may validate the unsigned CI-build path early as a Max stretch.
- SOPS dev-`.env` adoption lands in T1a, not T0.

## Environment notes (observed 2026-05-30, differ from earlier assumptions)

- **node v24.15.0** on the dev box (not v22); **electron 38** installs fine.
- **OCP** = `cadquery-ocp 7.8.1.1` wheel; pulls `vtk 9.3.1` + `numpy`. Native
  OCCT libs are in `site-packages/cadquery_ocp.libs/` (auditwheel,
  hash-suffixed) + `vtkmodules/` — NOT `OCP.libs/`.
- Frozen `--onedir` bundle is **679 MB**.
- Sidecar venv has OCP+pyinstaller installed (gitignored). Rebuild:
  `cd spike/sidecar && python3.12 -m venv .venv && .venv/bin/pip install -e ".[build]"`.
- **Dev box is headless** (no `DISPLAY`/xvfb/GPU): Electron windowed runs and
  WebGL render/hover can't be verified here — only headless coupling can.
- **Session caveat:** the tool-output layer was unreliable this session
  (scrambled/duplicated/fabricated results). Every "PASS" above was
  re-verified against on-disk result files with unique markers. Trust
  `spike/verify_all.sh` + `BUILD_RESULT.txt`, not transcript echoes.

## Last commits (newest first)

- `3556baf` — Day 4: PyInstaller bundles OCP, frozen sidecar runs (R1) [LOCAL]
- `46c44db` — Day 3: Electron shell spawns sidecar [LOCAL]
- `520f453` — Day 2: three.js viewport + hover [LOCAL]
- `fab21c7` — Day 1: sidecar emits face-tagged cube [LOCAL]
- `84e0f5d` / `ce1726e` / `bf3633f` — T0 phase-start / plan / roadmap [LOCAL]
- `7960ce7` — re-baseline architecture for Touch [pushed]

**All Touch work is local.** Direct push to `main` is denied (PR-only). To
publish: branch + PR, or have the user run `git push` after authorizing it.
