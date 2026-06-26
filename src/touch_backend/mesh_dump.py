"""In-subprocess geometry worker: tessellate + provenance -> serialized Mesh.

Runs **only** inside the executor subprocess — `live_build.build_mesh` appends a
`dump_mesh(...)` call to the emitted stack source, so build123d/OCP load here, in
an ephemeral child process, and never in the long-lived backend. That keeps the
backend GL-clean so it can render off-screen in-process (auto-memory
`render-backend`: importing OCP poisons VTK-OSMesa's Mesa context). The backend
never imports this module — enforced by the "backend orchestrator imports no
native CAD kernel" import-linter contract.

The emitted stack writes `part.step` + one `body_{i}.step` per layer; `dump_mesh`
re-imports the per-layer solids, tessellates the final one, attributes each face
to its owning layer (provenance, F39), and serializes the `Mesh` to `mesh.npz`
(the numpy buffers) + `mesh.json` (ids / anchors / provenance). The parent
reconstructs a `Mesh` from those two files with numpy + json only — no OCP.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

MESH_NPZ = "mesh.npz"
MESH_JSON = "mesh.json"


def dump_mesh(out_dir: str, layer_ids: list[str]) -> None:
    """Tessellate the built stack in `out_dir` and serialize the Mesh artifact.

    Reads `body_{i}.step` for `i in range(len(layer_ids))`, writes `mesh.npz` +
    `mesh.json` into `out_dir`. Invoked as the epilogue of the emitted stack, so
    it runs in the same (sandboxed) subprocess that just built the solids.
    """
    from build123d import import_step

    from touch_backend.tessellate import tessellate

    directory = Path(out_dir)
    solids = [import_step(directory / f"body_{i}.step") for i in range(len(layer_ids))]

    mesh = tessellate(solids[-1])
    _bake_provenance(mesh, solids, layer_ids)
    _write(directory, mesh)


def _bake_provenance(mesh: Any, solids: list[Any], layer_ids: list[str]) -> None:
    """Attribute faces to layers — best-effort (R-B): a provenance failure (e.g.
    an ambiguous boolean) must never fail an otherwise-valid rebuild."""
    from touch_backend import provenance

    try:
        prov = provenance.attribute_stack(solids, layer_ids)
        provenance.bake(mesh, prov)
    except Exception:  # noqa: BLE001 — provenance is advisory, geometry is not
        pass


def _write(directory: Path, mesh: Any) -> None:
    """Serialize the mesh: numpy buffers -> npz, ids/anchors/provenance -> json."""
    np.savez(
        directory / MESH_NPZ,
        vertices=mesh.vertices,
        normals=mesh.normals,
        indices=mesh.indices,
        face_tag_per_triangle=mesh.face_tag_per_triangle,
        edge_tag_per_segment=mesh.edge_tag_per_segment,
    )
    meta = {
        "version": mesh.version,
        "face_ids": [int(fid) for fid in mesh.face_ids],
        "face_anchor": {
            str(fid): list(point) for fid, point in mesh.face_anchor.items()
        },
        "face_provenance": {
            str(fid): {
                "created_by": sorted(entry.created_by),
                "last_modified_by": sorted(entry.last_modified_by),
            }
            for fid, entry in mesh.face_provenance.items()
        },
    }
    (directory / MESH_JSON).write_text(json.dumps(meta), encoding="utf-8")
