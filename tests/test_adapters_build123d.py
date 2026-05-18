from __future__ import annotations

from pathlib import Path

import pytest

from maquette.adapters import build123d_target
from maquette.intent import Intent

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "adapters" / "build123d"
_PRIMARY_KINDS = ("box", "cylinder", "sphere", "extrude", "revolve", "loft")
_MODIFIER_KINDS = ("hole", "fillet", "chamfer", "shell", "pattern")
_ALL_KINDS = _PRIMARY_KINDS + _MODIFIER_KINDS


def _load_intent(kind: str) -> Intent:
    intent_path = _FIXTURE_ROOT / kind / "intent.json"
    return Intent.model_validate_json(intent_path.read_text(encoding="utf-8"))


def _expected_source(kind: str) -> str:
    return (_FIXTURE_ROOT / kind / "expected.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("kind", _ALL_KINDS)
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


def test_extras_appended_verbatim():
    """Intent.extras content is appended to emit output unchanged."""
    from maquette.intent import Intent, PrimaryFeature

    extras_text = "# raw build123d snippet\nbody = body.translate((5, 0, 0))\n"
    intent = Intent(
        name="with_extras",
        description="extras escape hatch",
        features=[
            PrimaryFeature(
                id="body",
                kind="box",
                params={"length": 10.0, "width": 10.0, "height": 10.0},
            )
        ],
        extras=extras_text,
    )
    code = build123d_target.emit(intent)
    assert "# --- user extras ---" in code
    assert extras_text in code
    # The extras content must appear after the per-kind emission, not before.
    assert code.index("body = Box(") < code.index("# --- user extras ---")
    assert code.index("# --- user extras ---") < code.index(extras_text)


# Subprocess round-trip tests live in tests/test_adapter_roundtrip.py
# (this file is snapshot-equality only).
