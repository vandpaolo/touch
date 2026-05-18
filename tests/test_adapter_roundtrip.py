"""Round-trip tests: emit -> subprocess -> STEP file on disk.

Snapshot tests for emit correctness live in
`tests/test_adapters_build123d.py`. This file verifies that emitted
code actually *runs* under the build123d kernel and produces a STEP
file.

Each test uses `cwd=tmp_path` so the emitted code's
`export_step(..., "part.step")` lands in an isolated location and
never pollutes the repo.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from maquette.adapters import build123d_target
from maquette.intent import Intent, Modifier, Parameter, PrimaryFeature

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "adapters" / "build123d"


def _run_emit(intent: Intent, run_dir: Path) -> subprocess.CompletedProcess[str]:
    code = build123d_target.emit(intent)
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=run_dir,
    )


def test_box_roundtrip(tmp_path: Path):
    """The box fixture round-trips end-to-end: emit -> subprocess -> STEP."""
    intent = Intent.model_validate_json(
        (_FIXTURE_ROOT / "box" / "intent.json").read_text(encoding="utf-8")
    )
    result = _run_emit(intent, tmp_path)
    assert result.returncode == 0, (
        f"box round-trip failed.\n--- stderr ---\n{result.stderr}"
    )
    step_path = tmp_path / "part.step"
    assert step_path.exists(), f"part.step not created under {tmp_path}"
    assert step_path.stat().st_size > 0


def test_cylinder_with_chamfer_roundtrip(tmp_path: Path):
    """v0 reference prompt #2: 30 mm diameter, 40 mm tall cylinder + 2 mm chamfer.

    Phase-1 day-5 (MAX). The data-model spec leaves edge selection
    coarse for v0 — the chamfer is applied to *all* edges of the
    cylinder (both rims), not just the top edge the prompt mentions.
    First-class edge selection would land in a schema-v2 phase.
    """
    intent = Intent(
        name="cylinder_with_chamfer",
        description="30 mm diameter, 40 mm tall cylinder with a 2 mm chamfer",
        parameters=[
            Parameter(name="diameter", value=30, unit="mm"),
            Parameter(name="height", value=40, unit="mm"),
            Parameter(name="chamfer_size", value=2, unit="mm"),
        ],
        features=[
            PrimaryFeature(
                id="body",
                kind="cylinder",
                params={"radius": 15.0, "height": 40.0},
            )
        ],
        modifiers=[
            Modifier(
                id="c1",
                kind="chamfer",
                target="body",
                params={"distance": 2.0},
            )
        ],
    )
    result = _run_emit(intent, tmp_path)
    assert result.returncode == 0, (
        f"cylinder-with-chamfer round-trip failed.\n--- stderr ---\n{result.stderr}"
    )
    step_path = tmp_path / "part.step"
    assert step_path.exists()
    assert step_path.stat().st_size > 0


def test_l_bracket_with_holes_roundtrip(tmp_path: Path):
    """v0 reference prompt #3: L-bracket with a hole in each flange.

    Phase-1 day-5 (MAX). **Known v0 schema limitations exercised
    here** — this test asserts emit-and-execute produces a valid STEP,
    NOT that the resulting geometry visually matches an L-bracket:

    1. v0 schema has no union/combine modifier and no L-shape primary,
       so a real L-bracket cannot be modelled in the 11 kinds alone.
       The planner LLM would use Intent.extras for this — that's a
       phase-2a concern. This test uses a single-plate approximation
       (60 x 40 x 5 mm).
    2. v0 schema does not carry hole position; current _emit_hole
       drills at origin. Both holes overlap. Visually the resulting
       STEP has one through-hole at the plate's center, not two on
       separate flanges. Hole positioning lands in a follow-up phase.

    Both gaps are recorded in the phase-1 report. The test passes the
    Day-5 done-when bar ("STEP > 0 bytes") and exposes the gaps cleanly.
    """
    intent = Intent(
        name="l_bracket_approx",
        description=(
            "Approximate L-bracket as a flat plate (v0 schema lacks "
            "union and L-shape primitives); 6 mm holes (positions "
            "ignored by current _emit_hole)."
        ),
        parameters=[
            Parameter(name="length", value=60, unit="mm"),
            Parameter(name="width", value=40, unit="mm"),
            Parameter(name="thickness", value=5, unit="mm"),
            Parameter(name="hole_diam", value=6, unit="mm"),
        ],
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": 60.0, "width": 40.0, "height": 5.0},
            )
        ],
        modifiers=[
            Modifier(
                id="h1",
                kind="hole",
                target="body",
                params={"diameter": 6.0, "through": "true"},
            ),
            Modifier(
                id="h2",
                kind="hole",
                target="body",
                params={"diameter": 6.0, "through": "true"},
            ),
        ],
    )
    result = _run_emit(intent, tmp_path)
    assert result.returncode == 0, (
        f"l-bracket round-trip failed.\n--- stderr ---\n{result.stderr}"
    )
    step_path = tmp_path / "part.step"
    assert step_path.exists()
    assert step_path.stat().st_size > 0


def test_cube_with_hole_roundtrip(tmp_path: Path):
    """The cube-with-hole reference (data-model.md § Example) round-trips.

    This is the phase-1 day-4 main deliverable. Verifies:
    - emit produces runnable build123d code for the canonical v0 example
    - subprocess execution under cwd=tmp_path completes successfully
    - part.step is created and is non-empty (B-rep encoded STEP)

    A manual FreeCAD check (visually confirm the geometry matches a
    50 mm centered cube with a 20 mm through-hole) is recorded in the
    phase-1 report rather than asserted here.
    """
    intent = Intent.model_validate_json(
        (_FIXTURE_ROOT / "hole" / "intent.json").read_text(encoding="utf-8")
    )
    result = _run_emit(intent, tmp_path)
    assert result.returncode == 0, (
        f"cube-with-hole round-trip failed.\n--- stderr ---\n{result.stderr}"
    )
    step_path = tmp_path / "part.step"
    assert step_path.exists(), f"part.step not created under {tmp_path}"
    assert step_path.stat().st_size > 0
