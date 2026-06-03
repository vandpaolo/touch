"""Day-1 (T1b) guard: the committed generated protocol bindings import and
validate representative messages. Regenerate with `make codegen`; this test
fails loudly if the committed output drifts from a hand-written sample that the
schema must accept/reject.
"""

import pytest
from pydantic import ValidationError

from touch_backend._generated.protocol import TouchProtocol

_OPERATION = {
    "id": "01HZABCDEF",
    "kind": "box",
    "params": {"length": 50.0, "width": 50.0, "height": 50.0, "centered": "true"},
    "selection": {
        "target": "face",
        "point_xyz": [0.0, 0.0, 0.0],
        "finder": [{"kind": "plane_normal", "axis": "+Z"}],
        "entity_id_at_capture": None,
    },
    "prompt_text": "a 50 mm cube",
    "conversation": [],
    "created_at": "2026-06-01T10:14:00Z",
}


def _validate(message: dict) -> TouchProtocol:
    return TouchProtocol.model_validate({"message": message})


def test_plan_message_validates():
    msg = _validate({"type": "plan", "prompt_text": "a box", "selection": None})
    assert msg.message is not None


def test_op_message_with_full_operation_validates():
    _validate({"type": "op", "operation": _OPERATION})


def test_mesh_frame_message_validates():
    _validate(
        {
            "type": "meshFrame",
            "version": 1,
            "vertex_count": 8,
            "triangle_count": 12,
            "edge_segment_count": 12,
            "face_id_to_finder_hint": {
                "7": {
                    "target": "face",
                    "point_xyz": [0.0, 0.0, 12.5],
                    "finder": [{"kind": "plane_normal", "axis": "+Z"}],
                }
            },
        }
    )


@pytest.mark.parametrize(
    "kind",
    [
        {"kind": "contains_point", "point_xyz": [1.0, 2.0, 3.0], "tol_mm": 0.5},
        {"kind": "surface_type", "value": "cylindrical"},
        {"kind": "of_feature", "op_id": "01HZ"},
        {"kind": "edges_count", "count": 4},
    ],
)
def test_finder_predicate_variants_validate(kind):
    op = {**_OPERATION, "selection": {**_OPERATION["selection"], "finder": [kind]}}
    _validate({"type": "op", "operation": op})


def test_unknown_message_type_is_rejected():
    with pytest.raises(ValidationError):
        _validate({"type": "definitely-not-a-message"})


def test_missing_required_field_is_rejected():
    with pytest.raises(ValidationError):
        _validate({"type": "plan"})  # prompt_text missing
