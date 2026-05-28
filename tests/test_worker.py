from __future__ import annotations

import pytest

from maquette.agent import worker
from maquette.intent import Intent, Modifier, Parameter, PrimaryFeature


def _cube_with_hole() -> Intent:
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
                params={
                    "length": 50,
                    "width": 50,
                    "height": 50,
                    "centered": "true",
                },
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


def test_emit_code_delegates_to_build123d_adapter() -> None:
    src = worker.emit_code(_cube_with_hole())
    assert isinstance(src, str)
    assert src.strip() != ""
    assert "export_step(body" in src


def test_emit_code_includes_box_construction() -> None:
    src = worker.emit_code(_cube_with_hole())
    assert "Box(" in src


def test_emit_journal_raises_v01_stub() -> None:
    with pytest.raises(NotImplementedError) as exc:
        worker.emit_journal(_cube_with_hole())
    assert "v0.1" in str(exc.value)
