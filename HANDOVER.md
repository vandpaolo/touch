# Handover — Touch v0, T1a DONE, T1b is next

> *Start here in any fresh chat session that opens this project. Once
> T1b closes (`/pm-phase-report T1b`), rewrite "You are here" + the
> "What to do next" task for the phase after it. Keep this short enough
> to read in 60 seconds.*

## You are here

- **Project:** **Touch** — AI-native interactive 3D CAD editor
  (click→prompt→evolve), VS-Code-like shell, distributed as a Windows
  `.exe` for engineer friends. Pivoted from Maquette 2026-05-29.
- **Repo + package are renamed.** Repo dir is `touch/`, GitHub repo is
  `vandpaolo/touch`, the Python package is `src/touch_backend/`, the CLI
  is `touch-backend`, env prefix is `TOUCH_BACKEND_*`. (If you still see
  `maquette/` as the dir, the OS-level rename step hasn't been run yet —
  see the repo-rename runbook at the bottom.)
- **No phase is active** (`active_phase: null`). **T0 + T1a are DONE.**
  **T1b is next** but NOT yet planned in detail — run `/pm-phase-plan T1b`
  to fill the day breakdown, then `/pm-phase-start T1b` (runs the
  pre-phase audit, flips it to in_progress).
- **Scope freeze is OFF** — design docs are editable again until a phase
  goes `in_progress`.

## What's done

- **T0 — packaging spike (DONE).** Electron + PyInstaller-frozen Python
  sidecar (OCP native libs) → admin-free Windows `.exe`, face-tagged cube
  with hover-highlight, verified on real Windows 11. ADR-0009 holds.
  Report: [`docs/phases/phase-T0-report.md`](docs/phases/phase-T0-report.md).
- **T1a — engine rename + dev infra (DONE).** Maquette pipeline → headless
  `touch_backend` (F24); SOPS dev secrets (F29); `/srv/touch/` out_root
  (F30). Full CI gate green (164 tests, 96% cov). Single session, no
  blockers. Report: [`docs/phases/phase-T1a-report.md`](docs/phases/phase-T1a-report.md).

## What to do next (T1b — server + protocol skeleton)

Plan: [`docs/phases/phase-T1b.md`](docs/phases/phase-T1b.md) (stub — detail it via
`/pm-phase-plan T1b`, then `/pm-phase-start T1b`).

- Stand up the localhost WebSocket server + the editor↔engine protocol
  (ADR-0005), the `.touch` JSON document (ADR-0006), and the new modules
  the architecture calls for. Delete the throwaway `spike/` tree.
- **Resolve the executor process-model TBD** (`02-classes.md:331`, FAIL #7
  in the pre-T1a audit) when planning the executor — record the T0
  spike's outcome in `docs/notes/decisions.md`.

## Two bugs T0 caught (will bite T1b if forgotten)

1. **OCP native libs** live in `cadquery_ocp.libs/` + `vtkmodules/` (named
   after the *distribution*), NOT `OCP.libs/`. The PyInstaller spec globs
   `*.libs` + `vtkmodules` — never hardcode the path.
2. **Vite `base: "./"`** is required — Electron loads the renderer over
   `file://`, where the default absolute base 404s the JS bundle (blank
   window). Set relative base in the real frontend (T2) from day one.

## Dev onboarding (after a fresh clone / the dir rename)

1. `pip install -e ".[dev]"`, then swap to headless VTK:
   `pip uninstall -y vtk && pip install --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1`
   (a plain `pip install -e .` re-pulls X11 `vtk` and shadows `vtk-osmesa`).
2. `make secrets-decrypt` — writes a working `.env` (needs the host age key).
3. `make hooks` — installs the plaintext-`.env` pre-commit guard.
4. `make ci` — full local gate.

## Where things live

- Long-form thinking: `docs/notes/*.md` (decisions, constraints, inbox, …).
- Design: `docs/00-*`, `docs/01-*`, `docs/02-*`, `docs/adr/`, `docs/03-roadmap.md`.
- Phases: `phase-T0.md` … `phase-T15.md` (+ `-report.md`). Maquette history:
  `phase-0.md … phase-3.5-report.md` (DO NOT modify — preserved history).
- Engine: `src/touch_backend/`. Spike (throwaway, until T1b): `spike/`.
- This file (always reread): `HANDOVER.md`.

## Rules in effect

- **Phase discipline:** `/pm-phase-start` before building; scope-freezes
  design docs while `in_progress`; `/pm-phase-report` to close;
  `/pm-blocker` if a design decision turns out wrong mid-phase.
- **Tool-call batching (VSCode):** keep parallel batches ≤ ~3, go
  sequential for git/order-sensitive steps, use `run_in_background` not a
  trailing `&`. Env fix: `export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3`.
- **Notes capture mid-chat:** noteworthy → append to `docs/notes/*.md`,
  confirm in one line.
- **Auto-memory** at `~/.claude/.../memory/MEMORY.md` loads every session.

## Open carry-overs

- **PR #1 (`spike/t0-packaging`)** kept as a spike record (not merged);
  releases `spike-v0.1.0` / `spike-v0.1.1` preserve the artifacts.
- **Three pre-T1a audit FAILs** (doc hygiene, none blocking): executor TBD
  (#7, → T1b above); Maquette-era `constraints.md` "absorbed" marker (#8,
  annotate); phase-report frontmatter key mismatch `min_met` vs
  `min_goal_met` (#9, standardize the template).
- **R10 OCP/OCCT LGPL** — add a `LICENSES/` dir to the installer before
  any wider distribution (≤ T13).
- **Deferred to T13:** code-signing / SmartScreen / Defender (R7/R11/R14).
- **Deferred to T2/T3:** cold-start latency baseline; browser-tab N5/N6
  visual demo.

## Repo-rename runbook (run once, with VSCode CLOSED, if not already done)

The code identity is renamed; the OS-level move must be run by you:

```bash
# 1. move the working tree
mv ~/projects/maquette ~/projects/touch
cd ~/projects/touch

# 2. recreate the venv (it hardcodes the old absolute path)
rm -rf .venv && python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip uninstall -y vtk && pip install --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1
make secrets-decrypt && make hooks

# 3. migrate the Claude Code memory dir (keyed to the project path)
mv ~/.claude/projects/-home-vandpaolo-projects-maquette \
   ~/.claude/projects/-home-vandpaolo-projects-touch

# 4. reopen VSCode at ~/projects/touch
```

The GitHub repo (`vandpaolo/touch`) and git remote are renamed in-session.
