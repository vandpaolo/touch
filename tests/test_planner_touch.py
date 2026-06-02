"""Unit tests for the Touch planner (`touch_backend.planner`) — distinct from
the legacy `agent.planner` (Intent-based). Mocked client; no network.

The LLM supplies only {kind, params}; the planner assembles the Operation and
attaches the frontend-provided Selection (T3 chamfer path).
"""

from __future__ import annotations

import json

import pytest

from touch_backend import planner
from touch_backend._generated.protocol import Operation, Selection
from touch_backend.llm_client.base import LLMResponse


class _CannedClient:
    name = "canned"

    def __init__(self, text: str) -> None:
        self._text = text

    def available(self) -> bool:
        return True

    def complete(self, *, system: str, prompt: str, max_tokens: int = 2048) -> LLMResponse:
        return LLMResponse(text=self._text)


def _face_selection() -> Selection:
    return Selection.model_validate(
        {
            "target": "face",
            "point_xyz": [0, 0, 20],
            "finder": [{"kind": "contains_point", "point_xyz": [0, 0, 20], "tol_mm": 0.5}],
            "face_id_at_capture": 3,
        }
    )


def test_chamfer_op_carries_the_fe_selection() -> None:
    client = _CannedClient(json.dumps({"kind": "chamfer", "params": {"length": 5}}))
    selection = _face_selection()

    op = planner.plan(client, "add a 5 mm chamfer here", selection)

    assert isinstance(op, Operation)
    assert op.kind == "chamfer"
    assert op.params == {"length": 5}
    assert op.prompt_text == "add a 5 mm chamfer here"
    # The selection came from the frontend click, not the LLM.
    assert op.selection is not None
    assert op.selection.face_id_at_capture == 3
    assert op.selection.finder[0].root.kind == "contains_point"
    assert op.id  # server-minted, non-empty
    assert op.created_at is not None


def test_fenced_json_is_tolerated() -> None:
    fenced = "Sure:\n```json\n" + json.dumps({"kind": "box", "params": {"length": 40, "width": 40, "height": 40}}) + "\n```"
    op = planner.plan(_CannedClient(fenced), "a 40 mm cube", None)
    assert op.kind == "box"
    assert op.selection is None


def test_missing_kind_params_raises() -> None:
    with pytest.raises(planner.PlannerError):
        planner.plan(_CannedClient(json.dumps({"foo": "bar"})), "x", None)


def test_non_json_raises() -> None:
    with pytest.raises(planner.PlannerError):
        planner.plan(_CannedClient("I can't help with that."), "x", None)


def test_invalid_kind_raises() -> None:
    client = _CannedClient(json.dumps({"kind": "not_a_kind", "params": {}}))
    with pytest.raises(planner.PlannerError):
        planner.plan(client, "x", None)
