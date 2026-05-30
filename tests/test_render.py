"""Headless render tests for `touch_backend.render.orthographic`.

Runs off-screen (no DISPLAY) against the vtk-osmesa backend. Uses a
committed fixture STEP so the test does not depend on the adapter or a
subprocess round-trip.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from touch_backend.render import orthographic

_FIXTURE_STEP = Path(__file__).parent / "fixtures" / "render" / "cube.step"


def test_orthographic_writes_three_pngs(tmp_path: Path):
    paths = orthographic(_FIXTURE_STEP, tmp_path)

    assert [p.name for p in paths] == ["front.png", "side.png", "top.png"]
    renders_dir = tmp_path / "renders"
    for name in ("front", "side", "top"):
        png = renders_dir / f"{name}.png"
        assert png.exists(), f"{name}.png not written"
        assert png.stat().st_size > 0


def test_orthographic_renders_geometry_not_blank(tmp_path: Path):
    """Guard against the OSMesa blank-frame failure mode.

    A correctly rendered cube must show more than the background colour;
    a blank frame would have a single unique colour.
    """
    orthographic(_FIXTURE_STEP, tmp_path)
    front = Image.open(tmp_path / "renders" / "front.png").convert("RGB")
    colors = front.getcolors(maxcolors=front.size[0] * front.size[1])
    assert colors is not None
    assert len(colors) > 1, "render is a single flat colour (blank frame)"


def test_orthographic_is_offscreen():
    """Module import forces PyVista off-screen mode (N5, headless)."""
    import pyvista as pv

    assert pv.OFF_SCREEN is True
