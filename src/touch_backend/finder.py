# pyright: reportAttributeAccessIssue=false
# (OCP / cadquery-ocp ships no usable type stubs; symbols resolve at runtime.)
"""Finder resolution (ADR-0008): re-identify a selected entity on the rebuilt
solid from geometric predicates, re-evaluated per model state.

v0/T3 supports the `contains_point` predicate → the unique face whose surface
contains the clicked point. Zero or multiple matches is a structured failure
(FinderError) — never a silent wrong-face guess (the F7 clarification UX builds
on this in T5).

Called from the adapter's emitted build123d code at execution time (inside the
Executor subprocess), so OCP is imported lazily (OSMesa GL poisoning, see
auto-memory `render-backend`) and this module stays import-cheap.
"""

from __future__ import annotations

from typing import Any


class FinderError(Exception):
    """A finder did not resolve to exactly one entity (zero or ambiguous)."""


def iter_faces(shape: Any) -> list[Any]:
    """Faces of `shape` in canonical ``TopExp_Explorer`` order.

    The single source of truth for face ids (ADR-0011): `tessellate` tags mesh
    triangles by this same ordinal, so `face id i` here is the face the user
    clicked. `shape` may be a build123d object or a raw ``TopoDS_Shape``.
    """
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS

    shape = getattr(shape, "wrapped", shape)
    faces = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        faces.append(TopoDS.Face_s(explorer.Current()))
        explorer.Next()
    return faces


def resolve_face(
    solid: Any,
    entity_id: int | None,
    point: tuple[float, float, float],
    tol_mm: float = 0.5,
) -> Any:
    """Resolve the selected face on `solid`, tiered per ADR-0011.

    ① `entity_id` (the within-session capture) indexes the canonical face list
    deterministically — immune to edge/corner adjacency and mesh-vs-B-rep float
    gaps. ② On a miss (id out of range, e.g. if a rebuild drifts), fall back to
    the geometric finder (`contains_point`). ③ Zero/ambiguous there raises
    ``FinderError`` → clarification.
    """
    if entity_id is not None:
        faces = iter_faces(solid)
        if 0 <= entity_id < len(faces):
            target = faces[entity_id]
            # Return the *contextful* build123d face (from solid.faces()), not a
            # freshly-wrapped detached Face — its edges must trace back to the
            # solid or build123d treats chamfer/fillet as a 2D op on a loose face.
            for face in solid.faces():
                if face.wrapped.IsSame(target):
                    return face
    return resolve_face_containing(solid, point, tol_mm)


def resolve_face_containing(
    solid: Any,
    point: tuple[float, float, float],
    tol_mm: float = 0.5,
) -> Any:
    """Return the unique build123d ``Face`` of ``solid`` whose surface contains
    ``point`` within ``tol_mm``. Raises ``FinderError`` on zero or many matches.
    """
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.gp import gp_Pnt

    vertex = BRepBuilderAPI_MakeVertex(gp_Pnt(*point)).Vertex()

    matches = [
        face
        for face in solid.faces()
        if BRepExtrema_DistShapeShape(vertex, face.wrapped).Value() <= tol_mm
    ]

    if not matches:
        raise FinderError(f"no face contains point {point} (tol {tol_mm} mm)")
    if len(matches) > 1:
        raise FinderError(f"ambiguous: {len(matches)} faces contain point {point}")
    return matches[0]
