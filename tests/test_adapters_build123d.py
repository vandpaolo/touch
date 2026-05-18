from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from maquette.adapters import build123d_target
from maquette.intent import Intent

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "adapters" / "build123d"
_PRIMARY_KINDS = ("box", "cylinder", "sphere", "extrude", "revolve", "loft")


def _load_intent(kind: str) -> Intent:
    intent_path = _FIXTURE_ROOT / kind / "intent.json"
    return Intent.model_validate_json(intent_path.read_text(encoding="utf-8"))


def _expected_source(kind: str) -> str:
    return (_FIXTURE_ROOT / kind / "expected.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("kind", _PRIMARY_KINDS)
def test_emit_matches_snapshot(kind: str):
    intent = _load_intent(kind)
    emitted = build123d_target.emit(intent)
    expected = _expected_source(kind)
    assert emitted == expected, (
        f"Snapshot drift for {kind!r}.\n"
        f"--- expected ({_FIXTURE_ROOT / kind / 'expected.py'}) ---\n"
        f"{expected!r}\n"
        f"--- got ---\n"
        f"{emitted!r}"
    )


def test_box_emit_runs_under_subprocess():
    """The box fixture's emitted code must execute without error.

    Per phase-1 plan Day 2 done-when: 'emit output for the `box` fixture
    runs without error under `python -c "<output>"` (no STEP export yet
    — just BREP construction smoke)'.
    """
    intent = _load_intent("box")
    code = build123d_target.emit(intent)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"build123d construction smoke failed.\n"
        f"--- code ---\n{code}\n"
        f"--- stderr ---\n{result.stderr}"
    )
