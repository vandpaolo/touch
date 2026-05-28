# Maquette

> A maquette is the rough preliminary model an artist makes before
> sculpting the final piece. The AI hands you the maquette; you finish
> the real thing.

Maquette turns a natural-language prompt into an editable parametric
solid plus a STEP file:

1. **An editable parametric solid** in [build123d](https://github.com/gumyr/build123d).
2. **A STEP file** for handoff to any other CAD tool.
3. **Three orthographic renders** via PyVista so you can sanity-check the result.

Maquette is not a CAD tool. It produces first-draft geometry; you finish
the engineering by hand in FreeCAD, Onshape, NX, or whatever you already use.

## Status

**Pre-alpha, v0 in progress.** The pipeline runs end-to-end —
prompt → `Intent` → build123d code → STEP + orthographic renders, all in
a self-contained run folder. The CLI (`maquette design`) is landing in
phase 3; v0 ships after phase 3.5 (manual verification of the three
reference prompts).

## Install

Requires Python `>=3.12,<3.13`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Headless rendering — swap `vtk` for `vtk-osmesa`.** PyVista pulls the
X11-only `vtk` wheel, which segfaults when rendering on a server with no
display. Maquette renders off-screen, so replace it with the OSMesa build
(bundled CPU software GL — no X server, no Xvfb):

```bash
pip uninstall -y vtk
pip install --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1
```

Copy `.env.example` to `.env` and fill in your Anthropic API key:

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-...
```

## Usage

```bash
maquette design "a 50 mm cube with a 20 mm hole through the centre"
```

Flags:

| Flag | Default | Meaning |
|---|---|---|
| `--out <path>` | `output/` | Run-folder root directory |
| `--max-iter N` | `1` | Max refinement iterations (v0 is single-pass) |
| `--exec-timeout S` | `30` | Subprocess execution timeout (seconds) |
| `--model <id>` | `claude-opus-4-7` | Anthropic model id |
| `-q` / `--quiet` | off | Print only the run directory path |
| `-v` / `--verbose` | off | Print per-step detail to stderr |

The v0 reference prompts (the success bar for shipping v0) are:

1. `a 50 mm cube with a 20 mm hole through the centre`
2. `a 30 mm diameter, 40 mm tall cylinder with a 2 mm chamfer on the top edge`
3. `a 60 x 40 x 5 mm L-bracket with a 6 mm hole in the centre of each flange`

Every run produces a self-contained folder under `output/<run-id>/`
(run-id = `<UTC-timestamp>__<name>`) containing `prompt.txt`,
`intent.json`, `code.py`, `part.step`, `renders/{front,side,top}.png`,
`trace.jsonl`, `status.json` (and `error.json` on failure). The CLI
prints the run-folder path on every exit.

## Exit codes

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
- [`docs/02-data-model.md`](docs/02-data-model.md) — the `Intent` schema
- [`docs/02-classes.md`](docs/02-classes.md) — module + class map
- [`docs/03-roadmap.md`](docs/03-roadmap.md) — phased delivery plan
- [`docs/adr/`](docs/adr/) — architecture decision records

For development conventions and the PM Framework, see [`CLAUDE.md`](CLAUDE.md).

## License

[MIT](LICENSE).
