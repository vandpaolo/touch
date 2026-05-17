from __future__ import annotations

import pytest
from pydantic import ValidationError

from maquette.intent import Intent, Modifier, Parameter, PrimaryFeature


def _box_feature(fid: str = "body") -> PrimaryFeature:
    return PrimaryFeature(
        id=fid,
        kind="box",
        params={"length": 50.0, "width": 50.0, "height": 50.0},
    )


def _hole_modifier(mid: str = "drill", target: str | None = "body") -> Modifier:
    return Modifier(
        id=mid,
        kind="hole",
        target=target,
        params={"diameter": 20.0, "through": "true"},
    )


def test_minimal_intent_constructs():
    intent = Intent(
        name="cube",
        description="bare cube",
        features=[_box_feature()],
    )
    assert intent.schema_version == 1
    assert intent.parameters == []
    assert intent.modifiers == []
    assert intent.extras is None
    assert intent.features[0].id == "body"


def test_full_intent_with_modifier_and_parameter():
    intent = Intent(
        name="cube_with_hole",
        description="50 mm cube with 20 mm hole",
        parameters=[Parameter(name="size", value=50, unit="mm")],
        features=[_box_feature()],
        modifiers=[_hole_modifier()],
        extras=None,
    )
    assert intent.parameters[0].unit == "mm"
    assert intent.modifiers[0].target == "body"


def test_invalid_unit_rejected():
    with pytest.raises(ValidationError):
        Parameter(name="size", value=50, unit="ft")  # type: ignore[arg-type]


def test_invalid_primary_kind_rejected():
    with pytest.raises(ValidationError):
        PrimaryFeature(id="x", kind="torus", params={})  # type: ignore[arg-type]


def test_invalid_modifier_kind_rejected():
    with pytest.raises(ValidationError):
        Modifier(id="m", kind="bevel", target=None, params={})  # type: ignore[arg-type]


def test_duplicate_feature_ids_rejected():
    with pytest.raises(ValidationError, match="duplicate feature ids"):
        Intent(
            name="dup",
            description="dup",
            features=[_box_feature("a"), _box_feature("a")],
        )


def test_duplicate_modifier_ids_rejected():
    with pytest.raises(ValidationError, match="duplicate modifier ids"):
        Intent(
            name="dup",
            description="dup",
            features=[_box_feature("a")],
            modifiers=[
                _hole_modifier("m", target="a"),
                _hole_modifier("m", target="a"),
            ],
        )


def test_dangling_modifier_target_rejected():
    with pytest.raises(ValidationError, match="targets unknown feature"):
        Intent(
            name="dangle",
            description="dangling target",
            features=[_box_feature("body")],
            modifiers=[_hole_modifier("drill", target="ghost")],
        )


def test_modifier_target_none_is_allowed():
    intent = Intent(
        name="global_mod",
        description="modifier without target",
        features=[_box_feature("body")],
        modifiers=[_hole_modifier("drill", target=None)],
    )
    assert intent.modifiers[0].target is None


def test_extras_default_none():
    intent = Intent(
        name="x",
        description="x",
        features=[_box_feature()],
    )
    assert intent.extras is None


def test_extras_string_accepted():
    intent = Intent(
        name="x",
        description="x",
        features=[_box_feature()],
        extras="# raw build123d snippet\n",
    )
    assert intent.extras is not None
    assert "build123d" in intent.extras


def test_schema_version_overrideable():
    intent = Intent(
        name="future",
        description="future-schema payload",
        schema_version=2,
        features=[_box_feature()],
    )
    assert intent.schema_version == 2


def test_features_required():
    with pytest.raises(ValidationError):
        Intent(name="empty", description="no features")  # type: ignore[call-arg]


def test_json_roundtrip():
    intent = Intent(
        name="cube_with_hole",
        description="50 mm cube with 20 mm hole",
        parameters=[Parameter(name="size", value=50, unit="mm")],
        features=[_box_feature()],
        modifiers=[_hole_modifier()],
    )
    blob = intent.model_dump_json()
    restored = Intent.model_validate_json(blob)
    assert restored == intent
