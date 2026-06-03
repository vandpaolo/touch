"""Headless render tests for `touch_backend.render.orthographic`.

Runs off-screen (no DISPLAY) against the vtk-osmesa backend. Uses a
committed fixture STEP so the test does not depend on the adapter or a
subprocess round-trip.

The render itself runs in a *fresh subprocess*: the vtk-osmesa GL context is
poisoned by OCP loaded in-process elsewhere in the suite (the OCP/OSMesa GL
conflict — auto-memory `render-backend`), which blanks the frame
nondeterministically depending on test order. A clean interpreter is the only
way this test is order-independent. The tests then assert on the written PNGs
in-process (PIL only — no OCP/GL).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

_FIXTURE_STEP = Path(__file__).parent / "fixtures" / "render" / "cube.step"

_RENDER_SCRIPT = """
import sys
from pathlib import Path
from touch_backend.render import orthographic
orthographic(Path(sys.argv[1]), Path(sys.argv[2]))
"""


@pytest.fixture(scope="module")
def renders_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("render")
    proc = subprocess.run(
        [sys.executable, "-c", _RENDER_SCRIPT, str(_FIXTURE_STEP), str(out)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return out / "renders"


def test_orthographic_writes_three_pngs(renders_dir: Path):
    for name in ("front", "side", "top"):
        png = renders_dir / f"{name}.png"
        assert png.exists(), f"{name}.png not written"
        assert png.stat().st_size > 0


def test_orthographic_renders_geometry_not_blank(renders_dir: Path):
    """Guard against the OSMesa blank-frame failure mode.

    A correctly rendered cube must show more than the background colour;
    a blank frame would have a single unique colour.
    """
    front = Image.open(renders_dir / "front.png").convert("RGB")
    colors = front.getcolors(maxcolors=front.size[0] * front.size[1])
    assert colors is not None
    assert len(colors) > 1, "render is a single flat colour (blank frame)"


def test_orthographic_is_offscreen():
    """Importing the render module forces PyVista off-screen mode (N5, headless)."""
    import pyvista as pv

    import touch_backend.render  # noqa: F401  (import has the off-screen side effect)

    assert pv.OFF_SCREEN is True
