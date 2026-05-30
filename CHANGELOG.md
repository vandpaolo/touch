# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Phase T1a — Engine rename + salvage + dev infra (2026-05-30)

The Maquette pipeline is resurrected as Touch's headless backend under a
new namespace. No behaviour change — same engine, new identity + dev infra.

#### Changed
- **Package rename (F24):** `src/maquette/` → `src/touch_backend/`. All
  imports, the import-linter contracts (10, all kept), coverage paths,
  and the `[tool.touch_backend]` config section moved to the new name.
- **CLI binary:** `maquette` → **`touch-backend`** (`touch-backend design …`).
  Deliberately *not* `touch` — that shadows GNU `/usr/bin/touch` in an
  active venv.
- **Env-var prefix:** `MAQUETTE_*` → **`TOUCH_BACKEND_*`** (e.g.
  `TOUCH_BACKEND_OUT_ROOT`, `TOUCH_BACKEND_MODEL`).
- **Distribution name:** pyproject `name` is now `touch-backend`.

#### Added
- **SOPS-encrypted dev secrets (F29):** the dev Anthropic key now lives
  encrypted in `secrets.env.sops.yaml` (age recipient in `.sops.yaml`).
  The plaintext `.env` stays gitignored and is blocked from commits by a
  `.githooks/pre-commit` guard + a CI guard step.
- **Dev `out_root` (F30):** on the dev host the backend writes under
  `/srv/touch/` (nexus-ops storage standard), set via
  `TOUCH_BACKEND_OUT_ROOT` in the decrypted `.env`. The portable default
  stays `./output`, so CI and the eventual shipped app are unaffected.
- **`Makefile`:** `secrets-decrypt` / `secrets-encrypt`, `hooks`, `ci`.

#### Dev onboarding (after this change)
1. `pip install -e ".[dev]"`, then swap to headless VTK:
   `pip uninstall -y vtk && pip install --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1`
   (a plain `pip install -e .` re-pulls X11 `vtk` and shadows `vtk-osmesa`).
2. `make secrets-decrypt` — writes a working `.env` (needs the host age key
   at `~/.config/sops/age/keys.txt`).
3. `make hooks` — installs the plaintext-`.env` pre-commit guard.
4. `make ci` — runs the full local gate.

#### Still pending (separate step before T1b)
- **Repo-identity rename:** local dir `maquette/` → `touch/`, the GitHub
  repo + remote, `CLAUDE.md` / `README` / `HANDOVER`, and the pyproject
  `Documentation` URL. Deferred as its own deliberate operation (it
  requires a venv recreate, Claude Code memory-dir migration, and a
  VSCode reopen). Historical Maquette docs are preserved, never renamed.
