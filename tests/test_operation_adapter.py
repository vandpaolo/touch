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


# --- chamfer (T3): resolve the clicked face, chamfer its edges ---------------


def _chamfer_op(length=5, point=(0, 0, 20), op_id="ch1") -> Operation:
    return Operation.model_validate(
        {
            "id": op_id,
            "kind": "chamfer",
            "params": {"length": length},
            "selection": {
                "target": "face",
                "point_xyz": list(point),
                "finder": [
                    {"kind": "contains_point", "point_xyz": list(point), "tol_mm": 0.5}
                ],
                "entity_id_at_capture": 0,
            },
            "prompt_text": "add a 5 mm chamfer here",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )


def test_emit_chamfer_resolves_face_and_chamfers_edges():
    code = operation_adapter.emit(
        [
            _op("box", {"length": 40, "width": 40, "height": 40}, op_id="box1"),
            _chamfer_op(),
        ]
    )
    assert "from touch_backend.finder import resolve_face" in code
    assert "Box(40.0, 40.0, 40.0)" in code
    # id-first (ADR-0011): captured entity id, then point+tol as the fallback.
    assert "resolve_face(op_box1, 0, (0.0, 0.0, 20.0), 0.5).edges()" in code
    assert "length=5.0" in code


def test_emit_chamfer_without_captured_id_emits_none():
    # No captured id → resolve_face(..., None, ...) falls back to the finder.
    op = _chamfer_op()
    op.selection.entity_id_at_capture = None
    code = operation_adapter.emit(
        [_op("box", {"length": 40, "width": 40, "height": 40}, op_id="box1"), op]
    )
    assert "resolve_face(op_box1, None, (0.0, 0.0, 20.0), 0.5).edges()" in code


def test_emit_chamfer_is_deterministic():
    history = [
        _op("box", {"length": 40, "width": 40, "height": 40}, op_id="b"),
        _chamfer_op(),
    ]
    assert operation_adapter.emit(history) == operation_adapter.emit(history)


def test_chamfer_without_selection_is_refused():
    op = _chamfer_op()
    op.selection = None
    with pytest.raises(AdapterRefusal):
        operation_adapter.emit(
            [_op("box", {"length": 40, "width": 40, "height": 40}), op]
        )


def test_chamfer_as_first_op_is_refused():
    with pytest.raises(AdapterRefusal):
        operation_adapter.emit([_chamfer_op()])


def test_chamfer_round_trip_executes_and_adds_faces(tmp_path):
    from build123d import import_step

    from touch_backend.agent.executor import Executor

    code = operation_adapter.emit(
        [
            _op("box", {"length": 40, "width": 40, "height": 40}, op_id="box1"),
            _chamfer_op(),
        ]
    )
    code_path = tmp_path / "code.py"
    code_path.write_text(code, encoding="utf-8")
    result = Executor(tmp_path, 30.0).execute(code_path)

    assert result.step_path is not None, result.error
    solid = import_step(result.step_path)
    # A plain box has 6 faces; chamfering one face's 4 edges adds chamfer faces.
    assert len(solid.faces()) > 6


def test_chamfer_with_edge_adjacent_point_still_builds(tmp_path):
    # F36 money case: a corner point is ambiguous for contains_point (would
    # raise "ambiguous: N faces"), but the captured id (0) resolves the face
    # deterministically, so the chamfer builds end-to-end. A produced STEP (no
    # subprocess error) proves it; we don't import it in-process — that would
    # poison the OSMesa render test that sorts after this file.
    from touch_backend.agent.executor import Executor

    code = operation_adapter.emit(
        [
            _op("box", {"length": 40, "width": 40, "height": 40}, op_id="box1"),
            _chamfer_op(point=(20, 20, 20)),  # a corner — ambiguous by point alone
        ]
    )
    code_path = tmp_path / "code.py"
    code_path.write_text(code, encoding="utf-8")
    result = Executor(tmp_path, 30.0).execute(code_path)

    assert result.step_path is not None, result.error
