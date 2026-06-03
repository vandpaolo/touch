# pyright: reportAttributeAccessIssue=false
# (OCP / cadquery-ocp ships no usable type stubs; its symbols resolve at runtime.)
"""Tessellate an OCP B-rep solid into a render mesh with per-face IDs (F20).

The frontend bakes the per-triangle face IDs into its three.js geometry so
picking is 100% client-side (ADR-0008) — no round-trip per hover/click. Each
TopoDS face becomes one integer face id; every triangle carries the id of the
face it came from. Rebuilt fresh from the T0 spike's proven `face_tag_per_triangle`
pattern (not salvaged).

OCP is imported lazily inside `tessellate()` on purpose: importing the OCP GL
layer at module load poisons VTK-OSMesa's Mesa context for any in-process
off-screen render (see auto-memory `render-backend`). Keeping the import inside
the function keeps it out of the collection-time import graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

MESH_VERSION = 1


@dataclass
class Mesh:
    """Tessellated geometry + the per-triangle face-id map (F20).

    `face_anchor` holds one on-surface point per face id, used to seed the
    click->selection finder hint; it is carried in the JSON mesh-frame envelope,
    not the binary buffers.
    """

    version: int
    vertices: np.ndarray  # float32 (N, 3), world-space
    normals: np.ndarray  # float32 (N, 3)
    indices: np.ndarray  # uint32  (M, 3)
    face_tag_per_triangle: np.ndarray  # uint32 (M,)
    edge_tag_per_segment: np.ndarray  # uint32 (L,)
    face_ids: list[int] = field(default_factory=list)
    face_anchor: dict[int, tuple[float, float, float]] = field(default_factory=dict)


def tessellate(
    solid: Any,
    *,
    linear_deflection: float = 0.1,
    angular_deflection: float = 0.5,
) -> Mesh:
    """Mesh `solid` (a build123d object or a raw TopoDS_Shape) with face IDs."""
    # Lazy OCP import — see the module docstring (OSMesa GL poisoning).
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.GeomLProp import GeomLProp_SLProps
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.TopLoc import TopLoc_Location

    from touch_backend.finder import iter_faces

    shape = getattr(solid, "wrapped", solid)
    BRepMesh_IncrementalMesh(shape, linear_deflection, False, angular_deflection, True)

    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    face_tags: list[int] = []
    face_anchor: dict[int, tuple[float, float, float]] = {}

    # Canonical face ordinal (ADR-0011): the resolver indexes this same order,
    # so a mesh face tag == the face the user clicked. Skip faces with no
    # triangulation, but the id still advances with the explorer order.
    loc = TopLoc_Location()
    for face_id, face in enumerate(iter_faces(shape)):
        triangulation = BRep_Tool.Triangulation_s(face, loc)
        if triangulation is None:
            continue

        trsf = loc.Transformation()
        is_reversed = face.Orientation() == TopAbs_REVERSED
        surface = BRep_Tool.Surface_s(face)
        has_uv = triangulation.HasUVNodes()
        base = len(verts)

        for i in range(1, triangulation.NbNodes() + 1):
            point = triangulation.Node(i).Transformed(trsf)
            verts.append((point.X(), point.Y(), point.Z()))
            nx, ny, nz = 0.0, 0.0, 1.0
            if has_uv:
                uv = triangulation.UVNode(i)
                props = GeomLProp_SLProps(surface, uv.X(), uv.Y(), 1, 1e-6)
                if props.IsNormalDefined():
                    direction = props.Normal().Transformed(trsf)
                    nx, ny, nz = direction.X(), direction.Y(), direction.Z()
                    if is_reversed:
                        nx, ny, nz = -nx, -ny, -nz
            norms.append((nx, ny, nz))

        anchor = triangulation.Node(1).Transformed(trsf)
        face_anchor[face_id] = (anchor.X(), anchor.Y(), anchor.Z())

        for i in range(1, triangulation.NbTriangles() + 1):
            tri = triangulation.Triangle(i)
            n1 = base + tri.Value(1) - 1
            n2 = base + tri.Value(2) - 1
            n3 = base + tri.Value(3) - 1
            if is_reversed:
                n2, n3 = n3, n2
            tris.append((n1, n2, n3))
            face_tags.append(face_id)

    return Mesh(
        version=MESH_VERSION,
        vertices=np.asarray(verts, dtype=np.float32).reshape(-1, 3),
        normals=np.asarray(norms, dtype=np.float32).reshape(-1, 3),
        indices=np.asarray(tris, dtype=np.uint32).reshape(-1, 3),
        face_tag_per_triangle=np.asarray(face_tags, dtype=np.uint32),
        edge_tag_per_segment=np.zeros((0,), dtype=np.uint32),
        face_ids=sorted(face_anchor),
        face_anchor=face_anchor,
    )
