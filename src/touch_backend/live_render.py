"""Render the live Layer Stack to a PNG thumbnail the agent can see (F41, N15).

On-demand rendering for the MCP ``render_view`` tool: fold the stack to a STEP
(the Executor subprocess, which is the only place build123d/OCP runs), then
rasterise one isometric thumbnail **in-process**. This is only possible because
the backend is GL-clean — OCP never loads here, so VTK-OSMesa's off-screen
context is unpoisoned (auto-memory `render-backend`; the `mesh_dump`/`live_build`
worker boundary). Returns PNG bytes so the backend ships a small image over the
wire, not a heavy STEP.

Like `live_build`, this module imports no OCP: `Executor` is a stdlib subprocess
manager and `render.orthographic` is pyvista-only (its STEP->STL step is itself
subprocess-isolated). Enforced by the "orchestrator imports no native CAD kernel"
contract.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from touch_backend import layer_stack
from touch_backend.live_build import GeometryError

if TYPE_CHECKING:
    from touch_backend.layer_stack import LayerStack

_DEFAULT_SIZE = 512


def render_thumbnail(
    stack: LayerStack, *, timeout_s: float, size: int = _DEFAULT_SIZE
) -> bytes:
    """Fold `stack` to a STEP and return one isometric PNG thumbnail as bytes.

    Raises `GeometryError` if the stack does not build (no solid produced).
    """
    from touch_backend.agent.executor import Executor
    from touch_backend.render.orthographic import isometric

    if not stack.layers:
        raise GeometryError("empty stack: nothing to render")

    source = layer_stack.emit(stack)
    with tempfile.TemporaryDirectory(prefix="touch-render-") as tmp:
        out_dir = Path(tmp)
        code_path = out_dir / "code.py"
        code_path.write_text(source, encoding="utf-8")
        result = Executor(out_dir, timeout_s).execute(code_path)
        if result.step_path is None:
            raise GeometryError(result.error or "execution produced no solid")
        png_path = isometric(result.step_path, out_dir, size=size)
        return png_path.read_bytes()
