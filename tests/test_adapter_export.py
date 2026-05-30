"""Adapter export-variable contract tests (ADR-0004).

Covers `build123d_target._export` via the public `emit`:
- feature-based Intents export `features[-1].id` (unchanged behaviour);
- extras-only Intents export the reserved `body` variable;
- degenerate Intents (no features, no extras) raise AdapterRefusal;
- the extras-only L-bracket round-trips to a STEP on disk.

Snapshot equality for all 11 per-kind fixtures lives in
`tests/test_adapters_build123d.py`; this file is the export-path spec.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from touch_backend.adapters import AdapterRefusal, build123d_target
from touch_backend.intent import Intent, Modifier, PrimaryFeature

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "adapters" / "build123d"


def test_feature_based_exports_last_feature_id():
    """Feature-based Intent exports features[-1].id, not `body`."""
    intent = Intent(
        name="cyl",
        description="single cylinder, non-body id",
        features=[
            PrimaryFeature(
                id="cyl", kind="cylinder", params={"radius": 5.0, "height": 10.0}
            )
        ],
    )
    code = build123d_target.emit(intent)
    assert 'export_step(cyl, "part.step")' in code
    assert "export_step(body" not in code


def test_feature_based_with_modifier_exports_last_feature_id():
    """Modifiers reassign in place; export still targets the last feature id."""
    intent = Intent(
        name="cube_with_hole",
        description="50 mm cube, 20 mm through hole",
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={
                    "length": 50.0,
                    "width": 50.0,
                    "height": 50.0,
                    "centered": "true",
                },
            )
        ],
        modifiers=[
            Modifier(
                id="drill",
                kind="hole",
                target="body",
                params={"diameter": 20.0, "through": "true"},
            )
        ],
    )
    code = build123d_target.emit(intent)
    assert 'export_step(body, "part.step")' in code


def test_extras_only_exports_body():
    """Extras-only Intent (empty features) exports the reserved `body` var."""
    intent = Intent(
        name="extras_only",
        description="geometry supplied entirely via extras",
        features=[],
        extras="from build123d import Box\nbody = Box(10, 10, 10)",
    )
    code = build123d_target.emit(intent)
    assert 'export_step(body, "part.step")' in code


def test_parameter_named_like_build123d_fn_does_not_shadow(tmp_path: Path):
    """A parameter named after a build123d function (e.g. 'chamfer') must
    not be emitted as a top-level assignment that shadows it — else the
    modifier's chamfer(...) call crashes ('float' object is not callable)."""
    from touch_backend.intent import Parameter

    intent = Intent(
        name="cyl_chamfered",
        description="cylinder with an all-edges chamfer; param named 'chamfer'",
        parameters=[Parameter(name="chamfer", value=2.0, unit="mm")],
        features=[
            PrimaryFeature(
                id="body", kind="cylinder", params={"radius": 15.0, "height": 40.0}
            )
        ],
        modifiers=[
            Modifier(id="c1", kind="chamfer", target="body", params={"distance": 2.0})
        ],
    )
    code = build123d_target.emit(intent)
    assert "\nchamfer = 2.0" not in code  # not emitted as a shadowing assignment
    assert "chamfer(body.edges(), 2.0)" in code  # the function call survives

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=tmp_path,
    )
    assert result.returncode == 0, f"round-trip failed:\n{result.stderr}"
    assert (tmp_path / "part.step").stat().st_size > 0


def test_degenerate_intent_refuses():
    """No features and no extras -> AdapterRefusal(where='export:empty')."""
    intent = Intent(
        name="empty",
        description="nothing to build",
        features=[],
        extras=None,
    )
    with pytest.raises(AdapterRefusal) as excinfo:
        build123d_target.emit(intent)
    assert excinfo.value.where == "export:empty"


def test_extras_only_l_bracket_snapshot():
    """The l_bracket_extras fixture emits the expected source verbatim."""
    root = _FIXTURE_ROOT / "l_bracket_extras"
    intent = Intent.model_validate_json(
        (root / "intent.json").read_text(encoding="utf-8")
    )
    emitted = build123d_target.emit(intent)
    expected = (root / "expected.py").read_text(encoding="utf-8")
    assert emitted == expected
    assert emitted.rstrip().endswith('export_step(body, "part.step")')


def test_extras_only_l_bracket_roundtrip(tmp_path: Path):
    """The extras-only L-bracket round-trips: emit -> subprocess -> STEP.

    This is the carry-forward #1 regression: before the ADR-0004 fix an
    extras-only Intent emitted no `export_step` call and produced no STEP.
    """
    root = _FIXTURE_ROOT / "l_bracket_extras"
    intent = Intent.model_validate_json(
        (root / "intent.json").read_text(encoding="utf-8")
    )
    code = build123d_target.emit(intent)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        f"l_bracket_extras round-trip failed.\n--- stderr ---\n{result.stderr}"
    )
    step_path = tmp_path / "part.step"
    assert step_path.exists(), f"part.step not created under {tmp_path}"
    assert step_path.stat().st_size > 0
