"""Day 9 — live rebuild bakes per-layer provenance into the mesh (F39, F45).

A click→chamfer becomes a chamfer layer whose faces are attributable to it; the
build runs the real executor + OCP (build123d imported lazily inside the build).
"""

from __future__ import annotations

from touch_backend._generated.protocol import Operation
from touch_backend.layer_bridge import layers_from_history
from touch_backend.live_build import build_mesh
from touch_backend.session import Session

# Top face of a 40 mm cube centred at the origin (faces at +/- 20).
_FACE_SEL = {
    "target": "face",
    "point_xyz": [0, 0, 20],
    "finder": [{"kind": "contains_point", "point_xyz": [0, 0, 20], "tol_mm": 0.5}],
    "entity_id_at_capture": 0,
}


def _box_op(op_id: str = "box1") -> Operation:
    return Operation.model_validate(
        {
            "id": op_id,
            "kind": "box",
            "params": {"length": 40, "width": 40, "height": 40},
            "selection": None,
            "prompt_text": "a 40 mm cube",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )


def _chamfer_op(op_id: str = "cham1") -> Operation:
    return Operation.model_validate(
        {
            "id": op_id,
            "kind": "chamfer",
            "params": {"length": 3},
            "selection": _FACE_SEL,
            "prompt_text": "chamfer this 3 mm",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )


def test_single_box_layer_owns_every_face():
    mesh = build_mesh(layers_from_history([_box_op("box1")]), timeout_s=60)
    assert mesh.face_provenance, "provenance was not baked"
    assert set(mesh.face_ids).issubset(mesh.face_provenance)
    assert all(e.created_by == {"box1"} for e in mesh.face_provenance.values())


def test_chamfer_faces_attribute_to_the_chamfer_layer():
    stack = layers_from_history([_box_op("box1"), _chamfer_op("cham1")])
    mesh = build_mesh(stack, timeout_s=60)

    entries = [mesh.face_provenance[f] for f in mesh.face_ids]
    # The chamfer is face-scoped (only the selected top face's edges), so:
    # its own bevel faces exist...
    assert any(e.created_by == {"cham1"} for e in entries)
    # ...the surviving box planes are still attributed to the box...
    assert any(e.created_by == {"box1"} for e in entries)
    # ...it modified the selected face + its neighbours (last-modified chamfer)...
    assert any("cham1" in e.last_modified_by for e in entries)
    # ...and an untouched face (e.g. the bottom) keeps the box as last modifier.
    assert any(
        e.created_by == {"box1"} and e.last_modified_by == {"box1"} for e in entries
    )


def test_session_rebuild_is_clickable_and_undoable(tmp_path):
    """The live session flow: click→chamfer is clickable (provenance) + undoable."""
    session = Session(lambda: None, project_dir=tmp_path)
    session._append_op(_box_op("box1"))
    session._append_op(_chamfer_op("cham1"))

    mesh = session._rebuild_mesh()
    assert any("cham1" in e.last_modified_by for e in mesh.face_provenance.values())

    # Undo = delete-last on the canonical stack; all faces revert to the box.
    session._rollback_last()
    reverted = session._rebuild_mesh()
    assert all(e.created_by == {"box1"} for e in reverted.face_provenance.values())
