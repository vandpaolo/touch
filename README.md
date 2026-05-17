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

**Pre-alpha.** Phase 0 (Foundations) is in progress. The pipeline does
not exist yet — only the package skeleton, pinned dependencies, and the
design docs under [`docs/`](docs/).

## Install

Requires Python `>=3.12,<3.13`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and fill in your Anthropic API key:

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-...
```

## Usage (planned, v0)

The v0 CLI is not wired yet. Once Phase 2 lands, the entry point will be:

```bash
maquette design "a 50 mm cube with a 20 mm hole through the centre"
```

The v0 reference prompts (the success bar for shipping v0) are:

1. `a 50 mm cube with a 20 mm hole through the centre`
2. `a 30 mm diameter, 40 mm tall cylinder with a 2 mm chamfer on the top edge`
3. `a 60 x 40 x 5 mm L-bracket with a 6 mm hole in the centre of each flange`

Each run produces a self-contained folder under `output/<run-id>/`
containing `intent.json`, `code.py`, `part.step`, and three render PNGs.

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
