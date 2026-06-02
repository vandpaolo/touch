"""Live-API smoke test for the Touch planner (`touch_backend.planner`).

Gated by an available Anthropic key and `@pytest.mark.live` (excluded from the
default run via `addopts = "-m 'not live'"`). Run on demand:

    set -a; . ./.env; set +a
    pytest -m live tests/test_planner_touch_live.py

Costs a real API call. Verifies the T3 chamfer-planning path end-to-end.
"""

from __future__ import annotations

import pytest

from touch_backend._generated.protocol import Selection
from touch_backend.llm_client import make_client
from touch_backend.planner import plan


def _available() -> bool:
    return make_client("anthropic_api").available()


def _face_selection() -> Selection:
    return Selection.model_validate(
        {
            "target": "face",
            "point_xyz": [0, 0, 20],
            "finder": [
                {"kind": "contains_point", "point_xyz": [0, 0, 20], "tol_mm": 0.5}
            ],
            "face_id_at_capture": 3,
        }
    )


@pytest.mark.live
@pytest.mark.skipif(not _available(), reason="no anthropic key available")
def test_live_chamfer_planning() -> None:
    op = plan(
        make_client("anthropic_api"), "add a 5 mm chamfer here", _face_selection()
    )
    assert op.kind == "chamfer"
    assert "length" in op.params
    # The selection came from the (mocked) frontend click, not the LLM.
    assert op.selection is not None
    assert op.selection.face_id_at_capture == 3
