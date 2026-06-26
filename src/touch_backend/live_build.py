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

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from touch_backend import layer_stack
from touch_backend.mesh_dump import MESH_JSON, MESH_NPZ

if TYPE_CHECKING:
    from touch_backend.layer_stack import LayerStack
    from touch_backend.tessellate import Mesh

# Appended to the emitted stack so tessellation + provenance run in the SAME
# (sandboxed) subprocess that built the solids — build123d/OCP load there, never
# in the backend (the "orchestrator imports no native CAD kernel" contract). The
# worker writes mesh.npz + mesh.json, which `_read_mesh` reconstructs OCP-free.
_MESH_EPILOGUE = (
    "\n\nfrom touch_backend.mesh_dump import dump_mesh\ndump_mesh('.', {layer_ids!r})\n"
)


class GeometryError(Exception):
    """The stack's emitted code failed to produce a solid."""


def build_mesh(stack: LayerStack, *, timeout_s: float) -> Mesh:
    """Fold the stack to a tessellated mesh with per-layer provenance baked in.

    All build123d/OCP work runs in the executor subprocess: the emitted stack
    (which writes `part.step` + per-layer `body_{i}.step`) is followed by a
    `mesh_dump.dump_mesh` epilogue that tessellates + attributes provenance and
    serializes the `Mesh`. This function reconstructs that `Mesh` with numpy +
    json only, so the backend process imports no OCP and stays GL-clean for
    off-screen rendering (auto-memory `render-backend`).
    """
    from touch_backend.agent.executor import Executor

    layer_ids = [layer.id for layer in stack.layers]
    source = layer_stack.emit_layerwise(stack) + _MESH_EPILOGUE.format(
        layer_ids=layer_ids
    )
    with tempfile.TemporaryDirectory(prefix="touch-rebuild-") as tmp:
        out_dir = Path(tmp)
        code_path = out_dir / "code.py"
        code_path.write_text(source, encoding="utf-8")
        result = Executor(out_dir, timeout_s).execute(code_path)
        if result.step_path is None:
            raise GeometryError(result.error or "execution produced no solid")
        if not (out_dir / MESH_NPZ).exists():
            raise GeometryError("execution produced a solid but no mesh artifact")
        return _read_mesh(out_dir)


def _read_mesh(out_dir: Path) -> Mesh:
    """Reconstruct a `Mesh` from the worker's `mesh.npz` + `mesh.json` (no OCP)."""
    from touch_backend.provenance import ProvenanceEntry
    from touch_backend.tessellate import Mesh

    buffers = np.load(out_dir / MESH_NPZ)
    meta = json.loads((out_dir / MESH_JSON).read_text(encoding="utf-8"))
    face_provenance = {
        int(fid): ProvenanceEntry(
            created_by=set(entry["created_by"]),
            last_modified_by=set(entry["last_modified_by"]),
        )
        for fid, entry in meta["face_provenance"].items()
    }
    return Mesh(
        version=meta["version"],
        vertices=buffers["vertices"],
        normals=buffers["normals"],
        indices=buffers["indices"],
        face_tag_per_triangle=buffers["face_tag_per_triangle"],
        edge_tag_per_segment=buffers["edge_tag_per_segment"],
        face_ids=[int(fid) for fid in meta["face_ids"]],
        face_anchor={
            int(fid): tuple(point) for fid, point in meta["face_anchor"].items()
        },
        face_provenance=face_provenance,
    )
