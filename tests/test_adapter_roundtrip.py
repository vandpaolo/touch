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
from maquette.intent import Intent

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
