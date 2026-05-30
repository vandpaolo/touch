from __future__ import annotations

import pytest

from touch_backend.adapters import Adapter, AdapterRefusal, build123d_target
from touch_backend.intent import Intent, Modifier, PrimaryFeature


def test_emit_conforms_to_adapter_protocol_at_runtime():
    adapter: Adapter = build123d_target.emit
    assert callable(adapter)


def test_adapter_refusal_carries_reason_and_where():
    refusal = AdapterRefusal(reason="r-text", where="feature:torus")
    assert refusal.reason == "r-text"
    assert refusal.where == "feature:torus"
    assert "feature:torus" in str(refusal)
    assert "r-text" in str(refusal)


def test_unknown_primary_kind_raises_adapter_refusal():
    forged = PrimaryFeature.model_construct(
        id="x", kind="torus", params={"radius": 5.0}
    )
    intent = Intent.model_construct(
        name="t",
        description="t",
        schema_version=1,
        parameters=[],
        features=[forged],
        modifiers=[],
        extras=None,
    )
    with pytest.raises(AdapterRefusal) as exc_info:
        build123d_target.emit(intent)
    assert exc_info.value.where == "feature:torus"
    assert "torus" in exc_info.value.reason


def test_unknown_modifier_kind_raises_adapter_refusal():
    # Empty features so dispatch reaches modifiers without hitting a
    # Day-1 placeholder; intent.model_construct bypasses the schema
    # validator that requires a non-empty features list.
    forged_mod = Modifier.model_construct(
        id="bevel_op", kind="bevel", target=None, params={}
    )
    intent = Intent.model_construct(
        name="t",
        description="t",
        schema_version=1,
        parameters=[],
        features=[],
        modifiers=[forged_mod],
        extras=None,
    )
    with pytest.raises(AdapterRefusal) as exc_info:
        build123d_target.emit(intent)
    assert exc_info.value.where == "modifier:bevel"
    assert "bevel" in exc_info.value.reason


def test_known_kind_box_dispatches_and_emits_source():
    """Day 2: real _emit_box landed, so the dispatch path returns code.

    (Previously this test asserted NotImplementedError for the Day-1
    placeholder. The placeholder is gone; per-kind correctness is
    covered by tests/test_adapters_build123d.py::test_emit_matches_snapshot.)
    """
    box = PrimaryFeature(
        id="body",
        kind="box",
        params={"length": 1.0, "width": 1.0, "height": 1.0},
    )
    intent = Intent(
        name="cube",
        description="dispatch smoke",
        features=[box],
    )
    code = build123d_target.emit(intent)
    assert "body = Box(" in code
