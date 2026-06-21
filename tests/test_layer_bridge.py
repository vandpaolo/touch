"""Day 6 — op-history → Layer Stack bridge (geometry-identical; ADR-0012/0013)."""

from __future__ import annotations

import pytest

from touch_backend import operation_adapter
from touch_backend._generated.protocol import Operation
from touch_backend.adapters import AdapterRefusal
from touch_backend.layer_bridge import layer_from_operation, layers_from_history

_FACE_SEL = {
    "target": "face",
    "point_xyz": [0, 0, 20],
    "finder": [{"kind": "contains_point", "point_xyz": [0, 0, 20], "tol_mm": 0.5}],
    "entity_id_at_capture": 0,
}


def _box_op(op_id: str = "b1") -> Operation:
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


def _chamfer_op(op_id: str = "c1") -> Operation:
    return Operation.model_validate(
        {
            "id": op_id,
            "kind": "chamfer",
            "params": {"length": 5},
            "selection": _FACE_SEL,
            "prompt_text": "chamfer this",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )


def test_box_op_becomes_a_template_layer():
    layer = layer_from_operation(_box_op())
    assert layer.kind == "template"
    assert layer.template == "box"
    assert layer.params == {"length": 40.0, "width": 40.0, "height": 40.0}
    assert layer.source == "body = Box(40.0, 40.0, 40.0)"


def test_chamfer_op_becomes_a_finder_scoped_code_layer():
    op = _chamfer_op()
    layer = layer_from_operation(op)
    assert layer.kind == "code"
    # finder-scoped (not the all-edges template) → stays a code layer
    assert "chamfer(resolve_face(body," in layer.source
    assert "length=5.0" in layer.source
    assert layer.selection is op.selection


def test_bridged_source_is_byte_identical_to_the_op_adapter():
    """Geometry identity: a bridged layer runs the same RHS the op path would."""
    for op in (_box_op(), _chamfer_op()):
        layer = layer_from_operation(op)
        assert layer.source == f"body = {operation_adapter.rhs(op, 'body')}"


def test_unsupported_op_kind_is_refused_not_crashed():
    fillet = Operation.model_validate(
        {
            "id": "f1",
            "kind": "fillet",
            "params": {"radius": 2},
            "selection": None,
            "prompt_text": "fillet",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )
    with pytest.raises(AdapterRefusal):
        layer_from_operation(fillet)


def test_layers_from_history_preserves_order_and_ids():
    stack = layers_from_history([_box_op("a"), _chamfer_op("b")])
    assert [layer.id for layer in stack.layers] == ["a", "b"]
    assert stack.layers[0].kind == "template"
    assert stack.layers[1].kind == "code"
    assert stack.revision == 0
