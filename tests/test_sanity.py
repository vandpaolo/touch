from __future__ import annotations

from maquette.agent.sanity import (
    Dimension,
    DimensionMismatch,
    SanityResult,
    check,
)
from maquette.intent import Intent, Modifier, Parameter, PrimaryFeature


def _cube_with_hole_intent() -> Intent:
    return Intent(
        name="cube_with_hole",
        description="50 mm cube with 20 mm hole",
        parameters=[
            Parameter(name="size", value=50, unit="mm"),
            Parameter(name="hole_diam", value=20, unit="mm"),
        ],
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": 50, "width": 50, "height": 50, "centered": "true"},
            )
        ],
        modifiers=[
            Modifier(
                id="drill",
                kind="hole",
                target="body",
                params={"diameter": 20, "through": "true", "axis": "z"},
            )
        ],
    )


def _simple_cube_intent(size_mm: float = 50.0) -> Intent:
    return Intent(
        name="cube",
        description=f"{size_mm} mm cube",
        parameters=[Parameter(name="size", value=size_mm, unit="mm")],
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": size_mm, "width": size_mm, "height": size_mm},
            )
        ],
    )


def test_dataclasses_are_frozen() -> None:
    d = Dimension(value=50.0, unit="mm", raw="50 mm")
    try:
        d.value = 1.0  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError("Dimension should be frozen")

    m = DimensionMismatch(source="x", expected=1.0, found=2.0, message="m")
    try:
        m.expected = 9.0  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError("DimensionMismatch should be frozen")


def test_cube_with_hole_reference_prompt_matches() -> None:
    intent = _cube_with_hole_intent()
    result = check(
        "a 50 mm cube with a 20 mm hole through the centre",
        intent,
    )
    assert isinstance(result, SanityResult)
    assert result.ok is True
    assert result.warnings == []
    assert result.mismatches == []


def test_single_dimension_match() -> None:
    result = check("a 50 mm cube", _simple_cube_intent(50.0))
    assert result.ok is True


def test_single_dimension_mismatch_just_outside_half_mm() -> None:
    # Intent says 50.0, prompt says 50.6 → diff 0.6 > 0.5 mm and > 1% (0.5)
    intent = _simple_cube_intent(50.0)
    result = check("a 50.6 mm cube", intent)
    assert result.ok is False
    assert len(result.mismatches) == 1
    assert result.mismatches[0].source == "50.6 mm"


def test_single_dimension_just_inside_half_mm() -> None:
    # Intent 50.0, prompt 50.4 → diff 0.4 ≤ max(0.5, 0.5) = 0.5
    intent = _simple_cube_intent(50.0)
    result = check("a 50.4 mm cube", intent)
    assert result.ok is True


def test_one_percent_dominates_over_half_mm_for_large_values() -> None:
    # Intent 1000 mm, prompt 1009 mm → diff 9 ≤ max(10, 0.5) = 10 → match.
    intent = _simple_cube_intent(1000.0)
    result = check("a 1009 mm cube", intent)
    assert result.ok is True

    # Intent 1000 mm, prompt 1011 mm → diff 11 > 10 → mismatch.
    result = check("a 1011 mm cube", _simple_cube_intent(1000.0))
    assert result.ok is False


def test_multi_axis_delimited_prompt() -> None:
    intent = Intent(
        name="brick",
        description="60x40x5 mm brick",
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": 60, "width": 40, "height": 5},
            )
        ],
    )
    result = check("a 60 × 40 × 5 mm brick", intent)
    assert result.ok is True


def test_multi_axis_delimited_finds_all_three() -> None:
    # Intent missing the height value → 5 mm should mismatch.
    intent = Intent(
        name="brick",
        description="",
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": 60, "width": 40, "height": 99},
            )
        ],
    )
    result = check("a 60 × 40 × 5 mm brick", intent)
    assert result.ok is False
    mismatch_sources = {m.source for m in result.mismatches}
    assert "5 mm" in mismatch_sources


def test_unit_aware_comparison_mm_vs_cm() -> None:
    # Intent in cm, prompt in mm: 5 cm == 50 mm → match.
    intent = Intent(
        name="cube",
        description="",
        parameters=[Parameter(name="size", value=5, unit="cm")],
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": 50, "width": 50, "height": 50},
            )
        ],
    )
    result = check("a 50 mm cube", intent)
    assert result.ok is True


def test_unit_aware_comparison_inch_to_mm() -> None:
    # 1 in == 25.4 mm; intent has 25.4 in mm. Prompt "1 in" → match.
    intent = Intent(
        name="plate",
        description="",
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": 25.4, "width": 25.4, "height": 25.4},
            )
        ],
    )
    result = check("a 1 in cube", intent)
    assert result.ok is True


def test_empty_prompt_returns_ok() -> None:
    result = check("", _simple_cube_intent(50.0))
    assert result.ok is True
    assert result.mismatches == []


def test_empty_intent_returns_ok() -> None:
    # No parameters, no features… well, features is required. Use minimal.
    intent = Intent(
        name="empty",
        description="",
        features=[
            PrimaryFeature(id="body", kind="box", params={"hint": "none"}),
        ],
    )
    # No numeric values in intent at all (all params are strings).
    result = check("a 50 mm cube", intent)
    assert result.ok is True


def test_centred_keyword_does_not_create_false_positive() -> None:
    # "centred" implies derived coordinates the regex never sees (no
    # numeric value in the keyword itself). Should yield no warnings.
    intent = _simple_cube_intent(50.0)
    result = check("a 50 mm cube centred at the origin", intent)
    assert result.ok is True
    assert result.warnings == []


def test_centred_cylinder_along_axis_no_false_positive() -> None:
    # Cylinder centred along the X axis — no derived dimensions in
    # the prompt that the regex would flag.
    intent = Intent(
        name="cyl",
        description="",
        parameters=[Parameter(name="r", value=10, unit="mm")],
        features=[
            PrimaryFeature(
                id="body",
                kind="cylinder",
                params={"radius": 10, "height": 30},
            )
        ],
    )
    result = check(
        "a 10 mm radius 30 mm tall cylinder centred along the X axis",
        intent,
    )
    assert result.ok is True


def test_centred_does_not_whitewash_genuine_numeric_mismatch() -> None:
    # Prompt says 80 mm cube, intent has 50 mm. The "centred" word
    # must not suppress the warning.
    intent = _simple_cube_intent(50.0)
    result = check("an 80 mm cube centred at the origin", intent)
    assert result.ok is False
    assert any(m.source == "80 mm" for m in result.mismatches)


def test_no_unit_token_in_prompt_is_not_extracted() -> None:
    # "a cube with 4 walls" → no unit → not extracted → no spurious mismatch.
    result = check("a 50 mm cube with 4 walls", _simple_cube_intent(50.0))
    assert result.ok is True
