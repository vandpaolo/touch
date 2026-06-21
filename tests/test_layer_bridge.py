"""Day 6 — op-history → Layer Stack bridge (geometry-identical; ADR-0012/0013)."""

from __future__ import annotations

import pytest

from touch_backend import operation_adapter
from touch_backend._generated.protocol import Operation, Selection
from touch_backend.adapters import AdapterRefusal
from touch_backend.document import TouchDocument
from touch_backend.layer_bridge import (
    layer_from_operation,
    layers_from_history,
    load_stack,
    save_stack,
)
from touch_backend.layer_stack import Layer, LayerStack

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


# ---------- layer-native .touch persistence + migration (Day 7) -----------


def test_save_then_load_round_trips_a_code_layer_with_selection(tmp_path):
    stack = LayerStack(
        layers=[
            Layer.from_template(
                "box", {"length": 10.0, "width": 10.0, "height": 10.0}, id="L0"
            ),
            Layer.from_code(
                "inner = Cylinder(2.0, 50.0)\nbody = body - inner",
                id="L1",
                selection=Selection.model_validate(_FACE_SEL),
            ),
        ],
        revision=3,
    )
    path = tmp_path / "part.touch"
    save_stack(stack, path)

    # Round-trips exactly: template params, verbatim code source, selection, revision.
    assert load_stack(path) == stack


def test_load_migrates_an_op_history_touch_to_a_stack(tmp_path):
    doc = TouchDocument(name="old")
    doc.append(_box_op("a"))
    doc.append(_chamfer_op("b"))
    path = tmp_path / "old.touch"
    doc.save(path)  # schema 2 (op-history)

    stack = load_stack(path)
    assert [layer.kind for layer in stack.layers] == ["template", "code"]
    assert stack.layers[0].template == "box"
    assert "resolve_face(body," in stack.layers[1].source
