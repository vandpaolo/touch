"""Live-API smoke tests for the planner.

Gated by ``ANTHROPIC_API_KEY``. Marked ``@pytest.mark.live`` and excluded
from the default ``pytest`` run via ``addopts = "-m 'not live'"`` in
``pyproject.toml``. Run on demand with::

    pytest -m live

Costs real money (~$0.02-$0.05 per test on Opus 4.7). Kept out of CI
until phase 3.5.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from touch_backend.agent.planner import PlannerExhausted, PromptsBundle, plan
from touch_backend.intent import Intent

_HAS_KEY = os.environ.get("ANTHROPIC_API_KEY") is not None
_MODEL = "claude-opus-4-7"

_PROMPTS_FILE = Path(__file__).resolve().parents[1] / "prompts" / "planner.system.md"


def _bundle() -> PromptsBundle:
    return PromptsBundle(planner_system=_PROMPTS_FILE.read_text())


def _client():  # type: ignore[no-untyped-def]
    from anthropic import Anthropic

    return Anthropic()


@pytest.mark.live
@pytest.mark.skipif(not _HAS_KEY, reason="no ANTHROPIC_API_KEY")
def test_live_cube_with_hole() -> None:
    result = plan(
        _client(),
        "a 50 mm cube with a 20 mm hole through the centre",
        _MODEL,
        _bundle(),
    )
    assert isinstance(result.intent, Intent)
    assert any(f.kind == "box" for f in result.intent.features)
    assert any(m.kind == "hole" for m in result.intent.modifiers)


@pytest.mark.live
@pytest.mark.skipif(not _HAS_KEY, reason="no ANTHROPIC_API_KEY")
def test_live_cylinder_with_chamfer() -> None:
    result = plan(
        _client(),
        "a 30 mm radius cylinder 60 mm tall with a 2 mm chamfer on every edge",
        _MODEL,
        _bundle(),
    )
    assert any(f.kind == "cylinder" for f in result.intent.features)
    assert any(m.kind == "chamfer" for m in result.intent.modifiers)


@pytest.mark.live
@pytest.mark.skipif(not _HAS_KEY, reason="no ANTHROPIC_API_KEY")
def test_live_l_bracket_uses_extras() -> None:
    try:
        result = plan(
            _client(),
            "an L-bracket 100 x 60 x 5 mm with two 6 mm mounting holes",
            _MODEL,
            _bundle(),
        )
    except PlannerExhausted:
        pytest.fail("planner exhausted on L-bracket; system prompt needs tuning")
    # The L-bracket either uses extras or composes from primitives the
    # adapter understands; either way, the intent must validate.
    assert isinstance(result.intent, Intent)
