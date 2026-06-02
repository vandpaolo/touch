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
