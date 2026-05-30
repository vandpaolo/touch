# Handover — Touch v0, phase T0 in_progress, Day 1 ready

> *Start here in any fresh chat session that opens this project. Once
> T0 closes (`/pm-phase-report T0`), rewrite "You are here" + the
> "What to do next" task for T1a. Keep this short enough to read in
> 60 seconds.*

## You are here

- **Project:** **Touch** — AI-native interactive 3D CAD editor (click→prompt→evolve), VS-Code-like shell, distributed as a Windows `.exe` for engineer friends. **Pivoted from Maquette** on 2026-05-29 via a full re-baseline cascade (`/pm-vision` → `/pm-requirements` → `/pm-architecture` → `/pm-roadmap`).
- **Repo dir is still `maquette/`** and `src/` is still `src/maquette/` — the rename to `touch_backend/` is a T1a chore.
- **Active phase:** **T0 — Packaging spike** (Electron + PyInstaller'd Python sidecar + OCP → Windows `.exe`). Started 2026-05-30. Status `in_progress`. **Scope is now frozen** on Touch design docs.
- **Day 1 of T0 is the next thing to build.** No code exists yet under `spike/`. Plan: [`docs/phases/phase-T0.md`](docs/phases/phase-T0.md).
- **Last commit:** `84e0f5d` (T0 phase-start). Pushed: through `7960ce7` (architecture); commits `bf3633f`, `ce1726e`, `84e0f5d` are local until `git push`.

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

## What to do next (Day 1)

**Sidecar skeleton on Linux** — see [`docs/phases/phase-T0.md`](docs/phases/phase-T0.md) Day 1 row.

- New tree under `spike/sidecar/` (Python project, separate `venv`, separate `pyproject.toml` — do NOT touch `src/`).
- Module `touch_sidecar/server.py`: `websockets` server on `127.0.0.1:<random ephemeral port>`, prints `TOUCH_READY <port>` on stdout, emits one binary message on client connect — a hand-authored cube mesh (8 vertices, 12 triangles, 6 face tags in `face_tag_per_triangle`).
- Done when: a `wscat` (or scripted Python) client connects and parses out 6 distinct face tags across 12 triangles.

Mesh payload shape is specified in [`docs/02-data-model.md`](docs/02-data-model.md) §Mesh. Don't invent a new shape — match the spec so Day 2's FE wiring is reusable as the reference pattern for T1b.

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

## Last commits (newest first)

- `84e0f5d` — start phase T0 (frontmatter flip + audit addendum) [LOCAL]
- `ce1726e` — plan phase T0 (R1–R9 risk register) [LOCAL]
- `bf3633f` — re-baseline roadmap for Touch (T0–T15) [LOCAL]
- `7960ce7` — re-baseline architecture for Touch [pushed]
- `ae9d146` — pivot vision Maquette → Touch [pushed]

Push when ready: `git push`.
