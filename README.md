# Touch

> AI-native interactive 3D CAD editor — click a face, prompt a change,
> watch the model evolve. A VS-Code-like desktop shell distributed as a
> Windows `.exe`.
>
> *Formerly **Maquette** (a headless prompt-to-STEP pipeline); pivoted to
> the interactive editor on 2026-05-29. The Maquette engine lives on as
> Touch's headless core.*

Touch wraps a CAD kernel ([build123d](https://github.com/gumyr/build123d)
on OpenCASCADE) in a desktop editor: select geometry in a three.js
viewport, describe the edit in natural language, and an LLM planner turns
it into an editable, append-only operation history. Exports to STEP for
handoff to any other CAD tool.

## Status

**Pre-alpha, v0 in progress.** Built so far:

- **T0 — packaging spike (done):** Electron + a PyInstaller-frozen Python
  sidecar (OCP native libs) → a Windows `.exe` that installs admin-free
  and renders a face-tagged solid with hover-highlight. Verified on real
  Windows 11. The load-bearing risk is cleared.
- **T1a — engine rename + dev infra (done):** the Maquette pipeline is
  resurrected as the headless backend `touch_backend` (planner, intent,
  adapter, pricing, render), with SOPS-encrypted dev secrets and a
  `/srv/touch/` dev output root. See [`CHANGELOG.md`](CHANGELOG.md).

Next: the server + protocol skeleton (T1b), then the frontend (T2+). The
interactive editor is **not built yet** — today the engine runs via a CLI.

## Repo layout

- [`src/touch_backend/`](src/touch_backend/) — the headless engine (Python sidecar).
- [`spike/`](spike/) — the T0 packaging spike (throwaway; deleted in T1b).
- [`docs/`](docs/) — vision, requirements, architecture, roadmap, ADRs, phase records.

## Develop

Requires Python `>=3.12,<3.13`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# headless rendering: PyVista pulls X11 `vtk`, which segfaults off-screen.
# swap it for the OSMesa (CPU software GL) build:
pip uninstall -y vtk
pip install --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1
```

Dev secrets are SOPS-encrypted (needs the host age key at
`~/.config/sops/age/keys.txt`):

```bash
make secrets-decrypt   # writes a working .env (gitignored)
make hooks             # installs the plaintext-.env pre-commit guard
make ci                # full local gate: ruff, pyright, lint-imports, pytest
```

## Engine CLI

The headless engine runs end-to-end from the command line:

```bash
touch-backend design "a 50 mm cube with a 20 mm hole through the centre"
```

| Flag | Default | Meaning |
|---|---|---|
| `--out <path>` | `/srv/touch` (dev) / `output/` | Run-folder root |
| `--max-iter N` | `1` | Max refinement iterations (v0 is single-pass) |
| `--exec-timeout S` | `30` | Subprocess execution timeout (seconds) |
| `--model <id>` | `claude-opus-4-7` | Anthropic model id |
| `-q` / `--quiet` | off | Print only the run directory path |
| `-v` / `--verbose` | off | Print per-step detail to stderr |

Every run produces a self-contained folder under the output root
(`<UTC-timestamp>__<name>`) with `prompt.txt`, `intent.json`, `code.py`,
`part.step`, `renders/{front,side,top}.png`, `trace.jsonl`, `status.json`
(and `error.json` on failure). The CLI prints the run-folder path on exit.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | generic failure (e.g. `ANTHROPIC_API_KEY` not set) |
| `2` | bad CLI arguments |
| `10` | planner failed (no valid `Intent`, or an API error) |
| `11` | adapter refused the `Intent` |
| `12` | executor failed (subprocess crash / no STEP) |
| `13` | executor timed out |

## Documentation

Design and planning live under [`docs/`](docs/):

- [`docs/00-vision.md`](docs/00-vision.md) — vision and scope
- [`docs/01-requirements.md`](docs/01-requirements.md) — functional + non-functional requirements
- [`docs/02-architecture.md`](docs/02-architecture.md) — system architecture
- [`docs/02-data-model.md`](docs/02-data-model.md) — the data model
- [`docs/02-classes.md`](docs/02-classes.md) — module + class map
- [`docs/03-roadmap.md`](docs/03-roadmap.md) — phased delivery plan
- [`docs/adr/`](docs/adr/) — architecture decision records

For development conventions and the PM Framework, see [`CLAUDE.md`](CLAUDE.md).

## License

[MIT](LICENSE).
