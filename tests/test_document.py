"""TouchDocument save/load + schema migration (T4, F10/N7). Pure JSON + pydantic
— no OCP/build123d, so safe to import at module top."""

from __future__ import annotations

import json

from touch_backend._generated.protocol import Operation
from touch_backend.document import SCHEMA_VERSION, TouchDocument


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


def test_save_load_round_trip(tmp_path):
    doc = TouchDocument(name="cube", description="demo", history=[_box_op()])
    path = tmp_path / "cube.touch"
    doc.save(path)
    loaded = TouchDocument.load(path)

    assert loaded.name == "cube"
    assert loaded.description == "demo"
    assert loaded.schema_version == SCHEMA_VERSION
    assert [op.model_dump() for op in loaded.history] == [
        op.model_dump() for op in doc.history
    ]


def test_touch_file_is_human_readable_json(tmp_path):
    path = tmp_path / "cube.touch"
    TouchDocument(name="cube", history=[_box_op()]).save(path)
    text = path.read_text()
    data = json.loads(text)
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["history"][0]["kind"] == "box"
    assert "\n" in text  # indented / diff-friendly, not a single line


def test_save_sets_timestamps(tmp_path):
    doc = TouchDocument(name="x")
    doc.save(tmp_path / "x.touch")
    assert doc.created_at is not None
    assert doc.modified_at is not None


def test_migration_normalizes_old_version(tmp_path):
    old = {
        "schema_version": 0,
        "name": "old",
        "history": [_box_op().model_dump(mode="json")],
    }
    path = tmp_path / "old.touch"
    path.write_text(json.dumps(old))
    loaded = TouchDocument.load(path)

    assert loaded.schema_version == SCHEMA_VERSION
    assert loaded.description == ""
    assert loaded.parameters == []
    assert loaded.history[0].kind == "box"


def test_tolerates_newer_file_with_extra_fields(tmp_path):
    # N7: a newer minor that only adds fields still opens (extras ignored).
    newer = {
        "schema_version": SCHEMA_VERSION,
        "name": "fut",
        "history": [_box_op().model_dump(mode="json")],
        "future_field": {"whatever": 1},
    }
    path = tmp_path / "fut.touch"
    path.write_text(json.dumps(newer))
    loaded = TouchDocument.load(path)

    assert loaded.name == "fut"
    assert loaded.history[0].kind == "box"
