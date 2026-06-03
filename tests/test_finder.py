"""Finder resolution against a real build123d solid (ADR-0008, T3 day 5).

build123d/OCP are imported lazily inside the tests (importing them at module
top poisons VTK-OSMesa for the in-process render test — auto-memory
`render-backend`).
"""

from __future__ import annotations

import pytest

from touch_backend.finder import FinderError, resolve_face, resolve_face_containing


def _cube():
    # build123d Box is centred at the origin → faces at +/-20.
    from build123d import Box

    return Box(40, 40, 40)


def test_interior_point_resolves_to_one_face() -> None:
    face = resolve_face_containing(_cube(), (0, 0, 20), tol_mm=0.5)
    assert face is not None
    # A cube face is bounded by exactly 4 edges (the chamfer target).
    assert len(face.edges()) == 4


def test_point_off_the_solid_raises() -> None:
    with pytest.raises(FinderError):
        resolve_face_containing(_cube(), (0, 0, 100), tol_mm=0.5)


def test_corner_point_is_ambiguous() -> None:
    # A corner is shared by three faces → not uniquely resolvable.
    with pytest.raises(FinderError):
        resolve_face_containing(_cube(), (20, 20, 20), tol_mm=0.5)


def test_resolve_face_by_id_survives_ambiguous_point() -> None:
    # The money case (F36): a corner point is ambiguous via contains_point, but
    # the captured id resolves deterministically — no FinderError.
    face = resolve_face(_cube(), 0, (20, 20, 20))
    assert len(face.edges()) == 4  # a cube face


def test_resolve_face_id_miss_falls_back_to_finder() -> None:
    # Tier 2: an out-of-range id falls back to the geometric finder.
    face = resolve_face(_cube(), 999, (0, 0, 20))
    assert len(face.edges()) == 4
    # Tier 3: id miss AND no face at the point → FinderError.
    with pytest.raises(FinderError):
        resolve_face(_cube(), 999, (0, 0, 100))
