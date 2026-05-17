from __future__ import annotations

from maquette.intent import Intent, Modifier, PrimaryFeature
from maquette.intent_validation import ContractViolation, validate_kind_contracts


def _intent(
    features: list[PrimaryFeature],
    modifiers: list[Modifier] | None = None,
) -> Intent:
    return Intent(
        name="t",
        description="t",
        features=features,
        modifiers=modifiers or [],
    )


def _violations_for_feature(f: PrimaryFeature) -> list[ContractViolation]:
    return validate_kind_contracts(_intent([f]))


def _violations_for_modifier(m: Modifier) -> list[ContractViolation]:
    body = PrimaryFeature(
        id="body",
        kind="box",
        params={"length": 10.0, "width": 10.0, "height": 10.0},
    )
    return validate_kind_contracts(_intent([body], [m]))


# ---------- primary features -----------------------------------------------


def test_box_positive():
    f = PrimaryFeature(
        id="b",
        kind="box",
        params={"length": 50.0, "width": 50.0, "height": 50.0},
    )
    assert _violations_for_feature(f) == []


def test_box_negative_missing_height():
    f = PrimaryFeature(id="b", kind="box", params={"length": 50.0, "width": 50.0})
    violations = _violations_for_feature(f)
    assert len(violations) == 1
    assert violations[0].field == "height"
    assert violations[0].where == "feature:box[b]"


def test_cylinder_positive():
    f = PrimaryFeature(id="c", kind="cylinder", params={"radius": 15.0, "height": 40.0})
    assert _violations_for_feature(f) == []


def test_cylinder_negative_missing_radius():
    f = PrimaryFeature(id="c", kind="cylinder", params={"height": 40.0})
    violations = _violations_for_feature(f)
    assert any(v.field == "radius" for v in violations)


def test_sphere_positive():
    f = PrimaryFeature(id="s", kind="sphere", params={"radius": 10.0})
    assert _violations_for_feature(f) == []


def test_sphere_negative_missing_radius():
    f = PrimaryFeature(id="s", kind="sphere", params={})
    violations = _violations_for_feature(f)
    assert len(violations) == 1
    assert violations[0].field == "radius"


def test_extrude_positive():
    f = PrimaryFeature(
        id="e",
        kind="extrude",
        params={"profile": "sketch_a", "distance": 5.0},
    )
    assert _violations_for_feature(f) == []


def test_extrude_negative_missing_profile():
    f = PrimaryFeature(id="e", kind="extrude", params={"distance": 5.0})
    violations = _violations_for_feature(f)
    assert any(v.field == "profile" for v in violations)


def test_revolve_positive():
    f = PrimaryFeature(
        id="r",
        kind="revolve",
        params={"profile": "sketch_a", "axis": "z", "angle_deg": 360.0},
    )
    assert _violations_for_feature(f) == []


def test_revolve_negative_missing_axis():
    f = PrimaryFeature(
        id="r",
        kind="revolve",
        params={"profile": "sketch_a", "angle_deg": 360.0},
    )
    violations = _violations_for_feature(f)
    assert any(v.field == "axis" for v in violations)


def test_loft_positive():
    f = PrimaryFeature(id="l", kind="loft", params={"sections": "sketch_a,sketch_b"})
    assert _violations_for_feature(f) == []


def test_loft_negative_missing_sections():
    f = PrimaryFeature(id="l", kind="loft", params={})
    violations = _violations_for_feature(f)
    assert any(v.field == "sections" for v in violations)


# ---------- modifiers ------------------------------------------------------


def test_hole_positive_through():
    m = Modifier(
        id="h",
        kind="hole",
        target="body",
        params={"diameter": 6.0, "through": "true"},
    )
    assert _violations_for_modifier(m) == []


def test_hole_positive_depth():
    m = Modifier(
        id="h",
        kind="hole",
        target="body",
        params={"diameter": 6.0, "depth": 4.0},
    )
    assert _violations_for_modifier(m) == []


def test_hole_negative_missing_diameter():
    m = Modifier(id="h", kind="hole", target="body", params={"through": "true"})
    violations = _violations_for_modifier(m)
    assert any(v.field == "diameter" for v in violations)


def test_hole_negative_neither_depth_nor_through():
    m = Modifier(id="h", kind="hole", target="body", params={"diameter": 6.0})
    violations = _violations_for_modifier(m)
    assert len(violations) == 1
    assert violations[0].field is None
    assert "depth" in violations[0].message
    assert "through" in violations[0].message


def test_fillet_positive():
    m = Modifier(id="f", kind="fillet", target="body", params={"radius": 2.0})
    assert _violations_for_modifier(m) == []


def test_fillet_negative_missing_radius():
    m = Modifier(id="f", kind="fillet", target="body", params={})
    violations = _violations_for_modifier(m)
    assert any(v.field == "radius" for v in violations)


def test_chamfer_positive():
    m = Modifier(id="c", kind="chamfer", target="body", params={"distance": 1.5})
    assert _violations_for_modifier(m) == []


def test_chamfer_negative_missing_distance():
    m = Modifier(id="c", kind="chamfer", target="body", params={})
    violations = _violations_for_modifier(m)
    assert any(v.field == "distance" for v in violations)


def test_shell_positive():
    m = Modifier(
        id="s",
        kind="shell",
        target="body",
        params={"thickness": 1.0, "open_face": "+z"},
    )
    assert _violations_for_modifier(m) == []


def test_shell_negative_missing_open_face():
    m = Modifier(id="s", kind="shell", target="body", params={"thickness": 1.0})
    violations = _violations_for_modifier(m)
    assert any(v.field == "open_face" for v in violations)


def test_pattern_positive():
    m = Modifier(
        id="p",
        kind="pattern",
        target="body",
        params={"count": 4.0, "spacing": 10.0, "axis": "x"},
    )
    assert _violations_for_modifier(m) == []


def test_pattern_negative_missing_spacing():
    m = Modifier(
        id="p",
        kind="pattern",
        target="body",
        params={"count": 4.0, "axis": "x"},
    )
    violations = _violations_for_modifier(m)
    assert any(v.field == "spacing" for v in violations)


# ---------- aggregate behavior ---------------------------------------------


def test_empty_intent_no_violations():
    body = PrimaryFeature(
        id="body",
        kind="box",
        params={"length": 1.0, "width": 1.0, "height": 1.0},
    )
    assert validate_kind_contracts(_intent([body])) == []


def test_violations_accumulate_across_features_and_modifiers():
    bad_box = PrimaryFeature(id="b", kind="box", params={"length": 1.0})
    body = PrimaryFeature(
        id="body",
        kind="box",
        params={"length": 1.0, "width": 1.0, "height": 1.0},
    )
    bad_hole = Modifier(id="h", kind="hole", target="body", params={})
    intent = _intent([body, bad_box], [bad_hole])
    violations = validate_kind_contracts(intent)
    # bad_box: 2 missing (width, height); bad_hole: 2 (diameter + depth/through rule)
    assert len(violations) == 4


def test_numeric_field_with_string_value_flagged():
    f = PrimaryFeature(
        id="b",
        kind="box",
        params={"length": 50.0, "width": 50.0, "height": "fifty"},
    )
    violations = _violations_for_feature(f)
    assert len(violations) == 1
    assert violations[0].field == "height"
    assert "numeric" in violations[0].message


def test_string_field_with_numeric_value_flagged():
    f = PrimaryFeature(
        id="e",
        kind="extrude",
        params={"profile": 42.0, "distance": 5.0},
    )
    violations = _violations_for_feature(f)
    assert len(violations) == 1
    assert violations[0].field == "profile"
    assert "string" in violations[0].message
