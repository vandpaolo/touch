# pyright: reportAttributeAccessIssue=false
# (OCP / cadquery-ocp ships no usable type stubs; its symbols resolve at runtime.)
"""Computed provenance: which layer created / last-modified each face (F39, ADR-0012).

OCCT has no stable cross-op face id, so clickability is *computed*: at each layer
Touch geometrically diffs ``solid_N`` against ``solid_{N-1}`` and attributes every
face of the result to the layer(s) that created or last modified it. The diff is
**trim-independent** — a face is matched to its predecessor by its underlying
*surface* (an infinite plane / cylinder / sphere), not its trimmed boundary — so a
box face that a chamfer clips is recognised as the *same* face, modified, rather
than a new one. Attribution is carried in owner **sets** (a boolean fuse makes one
face multi-owner; robust fuse handling is the Max item — R-B).

This module owns the geometric diff. Aligning the result to the render mesh's
per-face ids (`bake`) is a zero-cost lookup because both index `iter_faces` in the
same canonical order. Faces only in v0 (edges aren't tessellated yet — F20); edge
provenance is the Max item.

OCP is imported lazily inside the functions (the OSMesa GL-poisoning discipline,
auto-memory `render-backend`), so this module stays out of the collection-time
import graph.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from touch_backend.tessellate import Mesh

_NDIG = 6  # rounding for surface-signature keys
_POS_TOL = 1e-4  # mm; centroid-coincidence tolerance for "same geometry"
_AREA_REL_TOL = 1e-4  # relative area tolerance for "same geometry"
_EPS = 1e-9


@dataclass
class ProvenanceEntry:
    """Which layer(s) created and last-modified one face.

    `created_by` is the originating layer(s) (inherited, never overwritten);
    `last_modified_by` is the most-recent layer(s) to change the face.
    """

    created_by: set[str] = field(default_factory=set)
    last_modified_by: set[str] = field(default_factory=set)


@dataclass
class ProvenanceMap:
    """Per-face attribution, keyed by `iter_faces` ordinal (= the mesh face id)."""

    faces: dict[int, ProvenanceEntry] = field(default_factory=dict)


def attribute(
    prev: Any,
    next: Any,
    *,
    layer_id: str,
    prior: ProvenanceMap | None = None,
) -> ProvenanceMap:
    """Attribute every face of ``next`` to a layer, given the previous solid.

    `prev` is the solid before this layer (``None`` for the first, creating
    layer); `prior` is `prev`'s ProvenanceMap (required when `prev` is given).
    Returns `next`'s ProvenanceMap. Pure: no I/O, no mutation of `prior`.
    """
    from touch_backend.finder import iter_faces

    next_faces = iter_faces(next)

    # First layer: it created every face.
    if prev is None:
        return ProvenanceMap(
            faces={
                fid: ProvenanceEntry({layer_id}, {layer_id})
                for fid in range(len(next_faces))
            }
        )
    if prior is None:
        raise ValueError("prior provenance is required when prev is not None")

    prev_faces = iter_faces(prev)
    prev_by_surface: dict[tuple, list[int]] = {}
    for pid, pf in enumerate(prev_faces):
        prev_by_surface.setdefault(_surface_key(pf), []).append(pid)

    faces: dict[int, ProvenanceEntry] = {}
    for nid, nf in enumerate(next_faces):
        candidates = prev_by_surface.get(_surface_key(nf), [])
        pid = _best_match(nf, candidates, prev_faces)
        if pid is None:
            # No predecessor surface → this layer created the face.
            faces[nid] = ProvenanceEntry({layer_id}, {layer_id})
            continue
        inherited = prior.faces[pid]
        if _same_geometry(nf, prev_faces[pid]):
            # Carried over untouched: provenance unchanged.
            faces[nid] = ProvenanceEntry(
                set(inherited.created_by), set(inherited.last_modified_by)
            )
        else:
            # Same surface, changed boundary (e.g. trimmed): this layer is now
            # the last modifier; the original creator is preserved.
            faces[nid] = ProvenanceEntry(set(inherited.created_by), {layer_id})
    return ProvenanceMap(faces=faces)


def attribute_stack(solids: list[Any], layer_ids: list[str]) -> ProvenanceMap:
    """Fold `attribute` across a whole stack: ``solids[i]`` is the solid after
    layer ``layer_ids[i]``. Returns the final solid's ProvenanceMap."""
    if not solids:
        raise ValueError("attribute_stack needs at least one solid")
    if len(solids) != len(layer_ids):
        raise ValueError("solids and layer_ids must be the same length")
    prov = attribute(None, solids[0], layer_id=layer_ids[0])
    for i in range(1, len(solids)):
        prov = attribute(solids[i - 1], solids[i], layer_id=layer_ids[i], prior=prov)
    return prov


def bake(mesh: Mesh, prov: ProvenanceMap) -> Mesh:
    """Attach `prov` to `mesh` by face id (both index `iter_faces`; F39). Mutates."""
    mesh.face_provenance = prov.faces
    return mesh


# ---------- geometric primitives (OCP, lazy) ------------------------------


def _best_match(face: Any, candidates: list[int], prev_faces: list[Any]) -> int | None:
    """The candidate prev face id whose centroid is closest to `face` (or None).

    v0 surfaces are distinct so `candidates` is usually length 1; closest-centroid
    disambiguates the rare collision. A true boolean fuse (one next face from many
    predecessors) is the Max item — here we pick the nearest single owner.
    """
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    _, *target = _area_centroid(face)
    return min(
        candidates,
        key=lambda pid: _distance(target, _area_centroid(prev_faces[pid])[1:]),
    )


def _surface_key(face: Any) -> tuple:
    """A trim-independent signature of a face's underlying surface.

    Uses `BRepAdaptor_Surface` (the canonical OCC classify-and-extract route) so
    a trimmed remnant keys to the same infinite surface as its untrimmed origin.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_SurfaceType

    adaptor = BRepAdaptor_Surface(face)
    surface_type = adaptor.GetType()

    if surface_type == GeomAbs_SurfaceType.GeomAbs_Plane:
        return ("plane", *_canon_plane(*adaptor.Plane().Coefficients()))

    if surface_type == GeomAbs_SurfaceType.GeomAbs_Cylinder:
        cylinder = adaptor.Cylinder()
        axis = cylinder.Axis()
        location = axis.Location()
        return (
            "cylinder",
            round(cylinder.Radius(), _NDIG),
            *_canon_direction(axis.Direction()),
            round(location.X(), _NDIG),
            round(location.Y(), _NDIG),
            round(location.Z(), _NDIG),
        )

    if surface_type == GeomAbs_SurfaceType.GeomAbs_Sphere:
        sphere = adaptor.Sphere()
        centre = sphere.Location()
        return (
            "sphere",
            round(sphere.Radius(), _NDIG),
            round(centre.X(), _NDIG),
            round(centre.Y(), _NDIG),
            round(centre.Z(), _NDIG),
        )

    # Unknown surface type: degrade to a geometry fingerprint (less robust, but
    # never crashes — R-B fail-soft).
    area, cx, cy, cz = _area_centroid(face)
    rounded = (round(area, _NDIG), round(cx, _NDIG), round(cy, _NDIG), round(cz, _NDIG))
    return ("other", *rounded)


def _canon_plane(
    a: float, b: float, c: float, d: float
) -> tuple[float, float, float, float]:
    """Plane coefficients with a sign-canonical normal (orientation-independent)."""
    sign = 1.0
    for component in (a, b, c):
        if abs(component) > _EPS:
            sign = 1.0 if component > 0 else -1.0
            break
    return (
        round(a * sign, _NDIG),
        round(b * sign, _NDIG),
        round(c * sign, _NDIG),
        round(d * sign, _NDIG),
    )


def _canon_direction(direction: Any) -> tuple[float, float, float]:
    """A direction with a sign-canonical orientation (a line, not a ray)."""
    return _canon_plane(direction.X(), direction.Y(), direction.Z(), 0.0)[:3]


def _area_centroid(face: Any) -> tuple[float, float, float, float]:
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face, props)
    centre = props.CentreOfMass()
    return props.Mass(), centre.X(), centre.Y(), centre.Z()


def _distance(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))


def _same_geometry(f1: Any, f2: Any) -> bool:
    """True if two faces have coincident area + centroid (an untouched carry-over)."""
    a1, *c1 = _area_centroid(f1)
    a2, *c2 = _area_centroid(f2)
    if abs(a1 - a2) > _AREA_REL_TOL * max(1.0, a1, a2):
        return False
    return _distance(c1, c2) <= _POS_TOL
