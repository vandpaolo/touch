"""Determinism (N3): same Intent -> byte-identical emit output.

NFR N3 requires that the adapter is a pure function: clock, random, and
environment-state-free. We verify this by loading each committed
fixture's Intent twice and asserting that the two emit() calls produce
identical strings.

Snapshot drift (between commits) is caught by
`tests/test_adapters_build123d.py`; this file catches *intra-run*
non-determinism (e.g., if a future change introduces a set or dict
iteration order that depends on hash randomization).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from touch_backend.adapters import build123d_target
from touch_backend.intent import Intent

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "adapters" / "build123d"
_ALL_KINDS = (
    "box",
    "cylinder",
    "sphere",
    "extrude",
    "revolve",
    "loft",
    "hole",
    "fillet",
    "chamfer",
    "shell",
    "pattern",
)


@pytest.mark.parametrize("kind", _ALL_KINDS)
def test_emit_is_deterministic(kind: str):
    intent_path = _FIXTURE_ROOT / kind / "intent.json"
    blob = intent_path.read_text(encoding="utf-8")
    intent_a = Intent.model_validate_json(blob)
    intent_b = Intent.model_validate_json(blob)
    a = build123d_target.emit(intent_a)
    b = build123d_target.emit(intent_b)
    assert a == b, (
        f"Non-determinism detected for {kind!r}.\n"
        f"--- emit #1 ---\n{a!r}\n"
        f"--- emit #2 ---\n{b!r}"
    )
