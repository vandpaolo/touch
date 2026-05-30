"""Headless orthographic rendering of a STEP file into PNG views.

Produces three views — front, side, top — as PNGs under
``<out_dir>/renders/``. Pure with respect to its inputs; the only side
effect is writing the PNG files. Rendering is **off-screen** (N5): no X
server required. The venv uses the ``vtk-osmesa`` wheel, which rasterises
on CPU via bundled OSMesa — no DISPLAY, no Xvfb.

This module raises on any hard failure (bad STEP, render error). The
caller (`agent.loop`) decides whether that is fatal — per F7, a render
failure does not block a run that already produced a valid STEP.

STEP -> STL conversion (OpenCascade / OCP) runs in a **subprocess**, not
in this process: OCP and the VTK-OSMesa renderer both grab the Mesa GL
context, and loading OCP first poisons OSMesa so renders come out blank.
Isolating the conversion keeps this process's GL clean for rendering.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pyvista as pv

# Run in a fresh interpreter: import the STEP via build123d/OCP and write
# an STL. Paths arrive as argv (never interpolated) so there is no shell
# or code-injection surface.
_STEP_TO_STL = (
    "import sys, build123d as bd; "
    "bd.export_stl(bd.import_step(sys.argv[1]), sys.argv[2])"
)

# Off-screen is mandatory on a headless server (N5). Set once at import.
pv.OFF_SCREEN = True

# view name -> PyVista camera-preset method. Front looks along -Y (XZ
# plane), side along -X (YZ plane), top along -Z (XY plane).
_VIEWS: dict[str, str] = {
    "front": "view_xz",
    "side": "view_yz",
    "top": "view_xy",
}

_WINDOW_SIZE = [1024, 1024]
_MESH_COLOR = "lightsteelblue"


def orthographic(step_path: Path, out_dir: Path) -> list[Path]:
    """Render ``step_path`` into front/side/top PNGs under ``out_dir/renders``.

    Returns the three written PNG paths in front, side, top order.
    """
    renders_dir = out_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)

    mesh = _load_mesh(step_path)

    paths: list[Path] = []
    for name, view_method in _VIEWS.items():
        png_path = renders_dir / f"{name}.png"
        _render_view(mesh, view_method, png_path)
        paths.append(png_path)

    # OSMesa plotters leave VTK objects that emit noisy __del__ warnings
    # at interpreter shutdown unless explicitly released.
    pv.close_all()
    return paths


def _load_mesh(step_path: Path) -> pv.DataSet | pv.MultiBlock:
    """STEP -> tessellated surface mesh, via a transient STL.

    The B-rep -> STL tessellation runs in a subprocess (OCP isolation,
    see module docstring); PyVista reads the resulting STL. The STL lives
    in a temp dir so ``out_dir`` holds only the PNG artefacts.
    """
    with tempfile.TemporaryDirectory() as tmp:
        stl_path = Path(tmp) / "mesh.stl"
        result = subprocess.run(
            [sys.executable, "-c", _STEP_TO_STL, str(step_path), str(stl_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 or not stl_path.exists():
            raise RuntimeError(
                f"STEP->STL conversion failed for {step_path}:\n{result.stderr}"
            )
        return pv.read(str(stl_path))


def _render_view(
    mesh: pv.DataSet | pv.MultiBlock, view_method: str, out_path: Path
) -> Path:
    plotter = pv.Plotter(off_screen=True, window_size=_WINDOW_SIZE)
    try:
        plotter.add_mesh(mesh, color=_MESH_COLOR, show_edges=True)
        getattr(plotter, view_method)()
        # OSMesa requires an explicit render before the framebuffer holds
        # the geometry; without it the screenshot is a blank frame.
        plotter.render()
        plotter.screenshot(str(out_path))
    finally:
        plotter.close()
    return out_path
