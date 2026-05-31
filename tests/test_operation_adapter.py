"""T1b Max: operation_adapter.emit — Operation history -> deterministic
build123d source (pure; no OCP/build123d imported here)."""

from __future__ import annotations

import pytest

from touch_backend import operation_adapter
from touch_backend._generated.protocol import Operation
from touch_backend.adapters import AdapterRefusal


def _op(kind: str, params: dict, op_id: str = "01HZ") -> Operation:
    return Operation.model_validate(
        {
            "id": op_id,
            "kind": kind,
            "params": params,
            "selection": None,
            "prompt_text": "x",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )


def test_emit_box():
    code = operation_adapter.emit(
        [_op("box", {"length": 30, "width": 20, "height": 10})]
    )
    assert "from build123d import *" in code
    assert "Box(30.0, 20.0, 10.0)" in code
    assert 'export_step(op_01HZ, "part.step")' in code


def test_emit_cylinder_and_sphere():
    cyl = operation_adapter.emit([_op("cylinder", {"radius": 5, "height": 12})])
    assert "Cylinder(5.0, 12.0)" in cyl
    sph = operation_adapter.emit([_op("sphere", {"radius": 7})])
    assert "Sphere(7.0)" in sph


def test_emit_is_deterministic():
    history = [_op("box", {"length": 1, "width": 2, "height": 3})]
    assert operation_adapter.emit(history) == operation_adapter.emit(history)


def test_unsupported_kind_is_refused():
    with pytest.raises(AdapterRefusal):
        operation_adapter.emit([_op("hole", {"diameter": 5, "depth": 2})])


def test_missing_param_is_refused():
    with pytest.raises(AdapterRefusal):
        operation_adapter.emit([_op("box", {"length": 1})])


def test_empty_history_is_refused():
    with pytest.raises(AdapterRefusal):
        operation_adapter.emit([])
