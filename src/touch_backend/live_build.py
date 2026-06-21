"""Build the live mesh for a Layer Stack with computed provenance baked in (Day 9).

One subprocess run emits the stack layer-wise — each intermediate solid to
``body_{i}.step`` plus the final ``part.step`` — then the parent imports the
per-layer solids, attributes every face to its owning layer (provenance,
ADR-0012), tessellates the final solid, and bakes the attribution into the mesh
by face id (F39). Clickability falls out: a clicked face id maps to its layer.

OCP / build123d import lazily inside `build_mesh` (the OSMesa GL-poisoning
discipline, auto-memory `render-backend`); the heavy build runs in the Executor
subprocess.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from touch_backend import layer_stack

if TYPE_CHECKING:
    from touch_backend.layer_stack import LayerStack
    from touch_backend.tessellate import Mesh


class GeometryError(Exception):
    """The stack's emitted code failed to produce a solid."""


def build_mesh(stack: LayerStack, *, timeout_s: float) -> Mesh:
    """Fold the stack to a tessellated mesh with per-layer provenance baked in."""
    from build123d import import_step

    from touch_backend.agent.executor import Executor
    from touch_backend.tessellate import tessellate

    source = layer_stack.emit_layerwise(stack)
    with tempfile.TemporaryDirectory(prefix="touch-rebuild-") as tmp:
        out_dir = Path(tmp)
        code_path = out_dir / "code.py"
        code_path.write_text(source, encoding="utf-8")
        result = Executor(out_dir, timeout_s).execute(code_path)
        if result.step_path is None:
            raise GeometryError(result.error or "execution produced no solid")
        # solid_0 … solid_N (one per layer); the last is the part.
        solids = [
            import_step(out_dir / f"body_{i}.step") for i in range(len(stack.layers))
        ]

    mesh = tessellate(solids[-1])
    _bake_provenance(mesh, solids, stack)
    return mesh


def _bake_provenance(mesh: Mesh, solids: list, stack: LayerStack) -> None:
    """Attribute faces to layers and bake into the mesh — best-effort (R-B).

    Provenance is heuristic; a failure (e.g. an ambiguous boolean) must never
    fail the rebuild. The part still renders, just without per-layer attribution.
    """
    from touch_backend import provenance

    try:
        prov = provenance.attribute_stack(solids, [layer.id for layer in stack.layers])
        provenance.bake(mesh, prov)
    except Exception:  # noqa: BLE001 — provenance is advisory, geometry is not
        pass
