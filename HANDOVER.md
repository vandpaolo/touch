# Handover — Touch v0, T0 DONE, T1a is next

> *Start here in any fresh chat session that opens this project. Once
> T1a closes (`/pm-phase-report T1a`), rewrite "You are here" + the
> "What to do next" task for T1b. Keep this short enough to read in
> 60 seconds.*

## You are here

- **Project:** **Touch** — AI-native interactive 3D CAD editor
  (click→prompt→evolve), VS-Code-like shell, distributed as a Windows
  `.exe` for engineer friends. Pivoted from Maquette 2026-05-29.
- **Repo dir is still `maquette/`** and `src/` is still `src/maquette/`
  — the rename to `src/touch_backend/` is **the T1a headline**.
- **No phase is active** (`active_phase: null`). **T0 is DONE** (Min met
  100% on a real Windows laptop, 2026-05-30). **T1a is next** but NOT
  yet planned in detail — run `/pm-phase-start T1a` (runs the pre-phase
  audit, then flips it to in_progress) when ready to begin.
- **Scope freeze is OFF** — design docs are editable again until a phase
  goes `in_progress`.

## T0 outcome (just closed)

- **The load-bearing v0 risk is cleared.** Electron + PyInstaller-frozen
  Python sidecar (OCP native libs) → Windows NSIS `.exe` that installs
  admin-free, spawns the sidecar, renders a face-tagged cube in three.js
  with working per-face hover-highlight. Verified on a real Windows 11
  laptop. ADR-0009 primary stack holds; Tauri fallback not needed.
- Full writeup + lessons: [`docs/phases/phase-T0-report.md`](docs/phases/phase-T0-report.md).
- **All spike code is under `spike/`** (throwaway — deleted in T1a/T1b).
  Don't salvage it; rebuild fresh in `src/`. But the *patterns* are
  proven — reuse the designs (see report's "Carryover").
- **Shipped via** branch `spike/t0-packaging` (PR #1, **unmerged on
  `main`**) + GitHub releases `spike-v0.1.0` / `spike-v0.1.1`.

## Two bugs T0 caught (will bite T1b if forgotten)

1. **OCP native libs** live in `cadquery_ocp.libs/` + `vtkmodules/`
   (named after the *distribution*), NOT `OCP.libs/`. The PyInstaller
   spec discovers them by globbing `*.libs` + `vtkmodules` — cross-platform
   (Linux auditwheel + Windows delvewheel). Never hardcode the path.
2. **Vite `base: "./"`** is required — Electron loads the renderer over
   `file://`, where the default absolute base 404s the JS bundle (blank
   window). Set relative base in the real frontend (T2) from day one.

## What to do next (T1a — engine rename + salvage)

Plan: [`docs/phases/phase-T1a.md`](docs/phases/phase-T1a.md) (stub — detail it via
`/pm-phase-plan` if it isn't filled, then `/pm-phase-start T1a`).

- Rename `src/maquette/` → `src/touch_backend/`; carry over the Maquette
  pipeline (planner, intent, intent_validation, adapter, pricing, config)
  so existing tests pass under the new namespace. No new behaviour.
- SOPS-encrypt the dev `.env`; default dev `out_root` to `/srv/touch/`.
- Green CI: `ruff check` + `ruff format --check` + `pyright` +
  `lint-imports` (run the full sequence locally before pushing — see
  auto-memory `feedback_ci-checks`).
- Delivers F24, F29, F30. The `spike/` tree stays untouched until T1b.

## Where things live

- Long-form thinking: `docs/notes/*.md` (decisions, constraints, inbox, …).
- Design: `docs/00-*`, `docs/01-*`, `docs/02-*`, `docs/adr/`, `docs/03-roadmap.md`.
- Phases: `docs/phases/phase-T0.md` (+ `-report.md`), `phase-T1a.md` …
  `phase-T15.md` (stubs). Maquette history: `phase-0.md … phase-3.5-report.md`
  (DO NOT modify).
- Spike (throwaway): `spike/sidecar/`, `spike/web/`, `spike/shell/`,
  `.github/workflows/spike-build.yml`.
- This file (always reread): `HANDOVER.md`.

## Rules in effect

- **Phase discipline:** `/pm-phase-start` before building; scope-freezes
  design docs while `in_progress`; `/pm-phase-report` to close;
  `/pm-blocker` if a design decision turns out wrong mid-phase.
- **Tool-call batching (VSCode):** keep parallel batches ≤ ~3, go
  sequential for git/order-sensitive steps, use `run_in_background` not
  trailing `&`, avoid `pkill -f`. Env fix:
  `export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3` (see CLAUDE.md). The
  harness scrambled tool output badly during T0 under high parallelism.
- **Notes capture mid-chat:** noteworthy → append to `docs/notes/*.md`,
  confirm in one line.
- **Auto-memory** at `~/.claude/.../memory/MEMORY.md` loads every session.

## Open carry-overs

- **PR #1 (`spike/t0-packaging`)** unmerged — decide merge vs. keep as a
  spike record before T1a.
- **Repo dir rename** `maquette/` → `touch/` + CLAUDE.md/README rewrite
  (tracked in `docs/notes/inbox.md` + `decisions.md`) — part of T1a.
- **R10 OCP/OCCT LGPL** — add a `LICENSES/` dir to the installer before
  any wider distribution (≤ T13).
- **Deferred to T13:** code-signing / SmartScreen / Defender (R7/R11/R14);
  the `.exe` artifact-name version is hardcoded `0.1.0` (cosmetic).
- **Deferred to T2/T3:** cold-start latency baseline; browser-tab N5/N6
  visual demo (wired, not yet shown live).
- SOPS dev-`.env` adoption lands in T1a.

## Last commits (newest first)

- `e5d5c39` — fix: relative Vite base (packaged blank window) [branch]
- `d4e9e41` — Day 5: electron-builder NSIS + GH Actions Windows build [branch]
- `99ec01e` — docs: cap tool-call batching (VSCode reliability) [branch]
- `8eee255` — docs: handover (days 1–4) [branch]
- `9439046` — Day 4: PyInstaller bundles OCP, frozen sidecar runs (R1) [branch]
- `46c44db` / `520f453` / `fab21c7` — Day 3 / 2 / 1 spike [branch]
- `84e0f5d` / `ce1726e` / `bf3633f` — T0 phase-start / plan / roadmap [LOCAL on main]
- `7960ce7` — re-baseline architecture for Touch [pushed]

**Branches:** `spike/t0-packaging` has Days 1–5 + fixes (pushed, PR #1).
`main` locally has the pre-spike docs commits (`84e0f5d` etc.) still
unpushed. This phase-report commit lands on whichever branch you're on —
check `git branch` before committing T1a work.
