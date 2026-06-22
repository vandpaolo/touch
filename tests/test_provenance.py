"""Day 3 — computed provenance: layer attribution per face (F39, ADR-0012).

build123d/OCP are imported lazily inside the tests (importing at module top
poisons VTK-OSMesa for the in-process render test — auto-memory `render-backend`).
"""

from __future__ import annotations

import pytest

from touch_backend.provenance import (
    ProvenanceMap,
    attribute,
    attribute_stack,
    bake,
)


def _box(size: float = 40.0):
    from build123d import Box

    return Box(size, size, size)  # centred at origin → faces at +/- size/2


def _box_then_chamfer(distance: float = 2.0):
    from build123d import chamfer

    box = _box()
    return box, chamfer(box.edges(), distance)


# ---------- first layer ---------------------------------------------------


def test_first_layer_owns_every_face():
    box = _box()
    prov = attribute(None, box, layer_id="L0")
    assert len(prov.faces) == 6
    assert all(e.created_by == {"L0"} for e in prov.faces.values())
    assert all(e.last_modified_by == {"L0"} for e in prov.faces.values())


def test_prior_required_when_prev_given():
    box = _box()
    with pytest.raises(ValueError, match="prior provenance is required"):
        attribute(box, box, layer_id="L1")


def test_attribute_stack_length_mismatch_rejected():
    with pytest.raises(ValueError, match="same length"):
        attribute_stack([_box()], ["a", "b"])


# ---------- the canonical [box, chamfer] attribution ----------------------


def test_chamfer_attributes_faces_to_owning_layers():
    box, chamfered = _box_then_chamfer()
    prov = attribute_stack([box, chamfered], ["box", "chamfer"])
    entries = list(prov.faces.values())

    # The chamfer touched everything: it trimmed all 6 box faces and added the
    # bevels — so every face is last-modified by the chamfer.
    assert all("chamfer" in e.last_modified_by for e in entries)

    # Exactly the 6 original box planes survive (trimmed) — created by the box,
    # now last-modified by the chamfer.
    survivors = [e for e in entries if e.created_by == {"box"}]
    assert len(survivors) == 6
    assert all(e.last_modified_by == {"chamfer"} for e in survivors)

    # The remaining faces are the chamfer's own (bevels + corners).
    chamfer_faces = [e for e in entries if e.created_by == {"chamfer"}]
    assert len(chamfer_faces) > 0
    assert len(entries) == 6 + len(chamfer_faces)


# ---------- the unchanged carry-over path ---------------------------------


def test_untouched_faces_keep_their_provenance():
    """A later layer that adds a disjoint solid must NOT re-stamp untouched faces."""
    from build123d import Pos, Sphere

    box = _box(10.0)
    combined = box + Pos(100, 0, 0) * Sphere(3)  # disjoint → box faces untouched
    prov = attribute_stack([box, combined], ["box", "ball"])

    box_faces = [e for e in prov.faces.values() if e.created_by == {"box"}]
    assert len(box_faces) == 6
    # last_modified_by stays "box" — the ball layer left these faces alone.
    assert all(e.last_modified_by == {"box"} for e in box_faces)

    ball_faces = [e for e in prov.faces.values() if e.created_by == {"ball"}]
    assert len(ball_faces) == 1


# ---------- bake into the render mesh -------------------------------------


def test_bake_aligns_provenance_to_mesh_face_ids():
    from touch_backend.tessellate import tessellate

    box, chamfered = _box_then_chamfer()
    mesh = tessellate(chamfered)
    prov = attribute_stack([box, chamfered], ["box", "chamfer"])

    returned = bake(mesh, prov)
    assert returned is mesh
    assert mesh.face_provenance == prov.faces

    # Every clickable (rendered) face id resolves to its owning layer.
    assert set(mesh.face_ids).issubset(prov.faces.keys())
    for fid in mesh.face_ids:
        assert "chamfer" in mesh.face_provenance[fid].last_modified_by


def test_empty_provenance_map_default():
    assert ProvenanceMap().faces == {}


def test_plane_key_sign_is_stable_under_near_zero_noise():
    """H1 regression: the same plane (normal ~+Z) with opposite tiny noise in a
    near-zero component must produce the SAME canonical key — else an untouched
    face is misattributed after a boolean."""
    from touch_backend.provenance import _canon_plane

    assert _canon_plane(1e-8, 0.0, 1.0, -20.0) == _canon_plane(-1e-8, 0.0, 1.0, -20.0)
