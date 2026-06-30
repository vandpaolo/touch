"""Day 5 — the live Layer Stack renders to a non-blank thumbnail (F41, N15).

The render runs in a **fresh subprocess** (like test_render.py): the pytest
process is poisoned by OCP loaded in-process elsewhere in the suite (the
OCP/OSMesa GL conflict — auto-memory `render-backend`), which blanks frames
nondeterministically by test order. A clean interpreter is the only order-
independent way to test it — and it mirrors production, where the backend is a
clean process (OCP runs only in the executor sub-subprocess).

The script does `build_mesh` (the rebuild path) **then** `render_thumbnail` in
the same clean process: that is the OCP-isolation invariant — if `build_mesh`
ever leaked OCP into its own process, the subsequent render would come back
blank and the non-blank assertion below would fail.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_SIZE = 256

# Build a one-box stack, fold it to a mesh (rebuild path), then render the live
# stack to a thumbnail — all in this clean interpreter. Writes the PNG to argv[1].
_RENDER_SCRIPT = """
import sys
from pathlib import Path

from touch_backend._generated.protocol import Operation
from touch_backend.layer_bridge import layers_from_history
from touch_backend.live_build import build_mesh
from touch_backend.live_render import render_thumbnail

box = Operation.model_validate({
    "id": "box1", "kind": "box",
    "params": {"length": 40, "width": 40, "height": 40},
    "selection": None, "prompt_text": "a 40 mm cube",
    "conversation": [], "created_at": "2026-06-01T00:00:00Z",
})
stack = layers_from_history([box])
mesh = build_mesh(stack, timeout_s=60)
assert mesh.face_ids, "rebuild produced no geometry"
png = render_thumbnail(stack, timeout_s=60, size=256)
Path(sys.argv[1]).write_bytes(png)
"""


@pytest.fixture(scope="module")
def iso_png(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("live_render") / "iso.png"
    proc = subprocess.run(
        [sys.executable, "-c", _RENDER_SCRIPT, str(out)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return out


def test_render_thumbnail_writes_a_png(iso_png: Path):
    assert iso_png.exists() and iso_png.stat().st_size > 0
    assert iso_png.read_bytes()[:8] == _PNG_SIG


def test_render_thumbnail_is_not_blank(iso_png: Path):
    """A real render of the box has shaded faces + edges → many colours; a blank
    (poisoned-OSMesa) frame would be a single flat colour."""
    image = Image.open(iso_png).convert("RGB")
    assert image.size == (_SIZE, _SIZE)
    colours = image.getcolors(maxcolors=1 << 24)
    assert colours is not None and len(colours) > 1, "blank render (OSMesa poisoned?)"
