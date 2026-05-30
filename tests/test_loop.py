"""Tests for `touch_backend.agent.loop.Loop`.

The planner (LLM) is mocked; the worker, executor, and renderer run for
real, so each happy-path test is a true emit -> subprocess -> STEP ->
PNG round-trip. Failure paths monkeypatch the relevant stage.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from touch_backend.adapters import AdapterRefusal
from touch_backend.agent import loop as loop_mod
from touch_backend.agent.loop import Loop, RunConfig
from touch_backend.agent.planner import PlannerExhausted, PlanResult, PromptsBundle
from touch_backend.intent import Intent
from touch_backend.pricing import Tokens

_PROMPTS_FILE = Path(__file__).resolve().parents[1] / "prompts" / "planner.system.md"

_HOLE_INTENT = (
    Path(__file__).parent
    / "fixtures"
    / "adapters"
    / "build123d"
    / "hole"
    / "intent.json"
)
_CUBE_PROMPT = "a 50 mm cube with a 20 mm hole through the centre"


def _intent() -> Intent:
    return Intent.model_validate_json(_HOLE_INTENT.read_text(encoding="utf-8"))


def _loop(tmp_path: Path) -> Loop:
    return Loop(
        out_root=tmp_path,
        cfg=RunConfig(),
        client=object(),
        prompts=PromptsBundle(planner_system="SYSTEM PROMPT v0"),
    )


def _patch_plan(monkeypatch, *, intent=None, tokens=None, exc=None) -> None:
    def fake_plan(client, prompt, model, prompts):  # noqa: ANN001
        if exc is not None:
            raise exc
        return PlanResult(
            intent=intent,
            tokens=tokens or Tokens(100, 50, 200, 10),
            retries=0,
            duration_s=0.4,
        )

    monkeypatch.setattr(loop_mod, "plan", fake_plan)


def _status(run_dir: Path) -> dict:
    return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))


def _trace_steps(run_dir: Path) -> list[str]:
    lines = (run_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line)["step"] for line in lines]


def test_happy_path_produces_full_artefact_set(tmp_path, monkeypatch):
    _patch_plan(monkeypatch, intent=_intent())
    run_dir = _loop(tmp_path).run(_CUBE_PROMPT)

    for name in (
        "prompt.txt",
        "intent.json",
        "code.py",
        "part.step",
        "trace.jsonl",
        "status.json",
    ):
        assert (run_dir / name).exists(), f"missing {name}"
    assert len(list((run_dir / "renders").glob("*.png"))) == 3

    status = _status(run_dir)
    assert status["status"] == "DONE_OK"
    assert status["exit_code"] == 0
    assert status["iterations"] == 1
    assert set(status["tokens"]) == {"input", "output", "cache_read", "cache_creation"}
    assert status["cost_usd_estimate"] > 0
    assert len(status["prompts_hash"]) == 64  # sha256 hex
    assert status["artefacts"]["renders"] == ["front.png", "side.png", "top.png"]

    steps = _trace_steps(run_dir)
    assert steps[0] == "PROMPT_RECEIVED"
    assert steps[-1] == "DONE_OK"
    for expected in ("PLANNING", "CODE_EMITTING", "EXECUTING"):
        assert expected in steps
    assert "__" in run_dir.name  # F11 run-id format


def test_planning_failure_exit_10(tmp_path, monkeypatch):
    _patch_plan(monkeypatch, exc=PlannerExhausted("no valid intent"))
    run_dir = _loop(tmp_path).run("asdfghjkl")

    status = _status(run_dir)
    assert status["status"] == "PLANNING_FAILED"
    assert status["exit_code"] == 10
    assert (run_dir / "error.json").exists()
    assert not (run_dir / "intent.json").exists()
    assert run_dir.name.endswith("__unplanned")


def test_anthropic_api_error_is_planning_failure(tmp_path, monkeypatch):
    """P3-Q1: an Anthropic API error during planning -> exit 10 + run folder."""
    from anthropic import AnthropicError

    _patch_plan(monkeypatch, exc=AnthropicError("rate limited"))
    run_dir = _loop(tmp_path).run("a 50 mm cube")

    status = _status(run_dir)
    assert status["status"] == "PLANNING_FAILED"
    assert status["exit_code"] == 10
    assert (run_dir / "error.json").exists()
    assert (run_dir / "status.json").exists()  # complete folder despite the error


def test_adapter_refusal_exit_11(tmp_path, monkeypatch):
    _patch_plan(monkeypatch, intent=_intent())

    def refuse(_intent):
        raise AdapterRefusal(reason="no NX equivalent", where="feature:loft")

    monkeypatch.setattr(loop_mod.worker, "emit_code", refuse)
    run_dir = _loop(tmp_path).run(_CUBE_PROMPT)

    status = _status(run_dir)
    assert status["status"] == "ADAPTER_REFUSED"
    assert status["exit_code"] == 11
    assert (run_dir / "error.json").exists()
    assert not (run_dir / "part.step").exists()


def test_exec_failure_exit_12(tmp_path, monkeypatch):
    _patch_plan(monkeypatch, intent=_intent())
    monkeypatch.setattr(
        loop_mod.worker, "emit_code", lambda _i: "raise RuntimeError('boom')\n"
    )
    run_dir = _loop(tmp_path).run(_CUBE_PROMPT)

    status = _status(run_dir)
    assert status["status"] == "EXEC_FAILED"
    assert status["exit_code"] == 12
    assert (run_dir / "error.json").exists()  # written by the executor


def test_sanity_mismatch_warns_but_succeeds(tmp_path, monkeypatch):
    # The hole-fixture intent is a 50 mm cube; the prompt claims 80 mm.
    _patch_plan(monkeypatch, intent=_intent())
    run_dir = _loop(tmp_path).run("an 80 mm cube with a 20 mm hole through the centre")

    status = _status(run_dir)
    assert status["exit_code"] == 0
    assert status["status"] == "DONE_OK"
    assert status["warnings"], "expected a dimension warning"
    assert "DIMENSION_WARNING" in _trace_steps(run_dir)


def test_render_failure_is_non_fatal(tmp_path, monkeypatch):
    _patch_plan(monkeypatch, intent=_intent())

    def boom(step_path, out_dir):
        raise RuntimeError("render exploded")

    monkeypatch.setattr(loop_mod, "orthographic", boom)
    run_dir = _loop(tmp_path).run(_CUBE_PROMPT)

    status = _status(run_dir)
    assert status["exit_code"] == 0
    assert status["status"] == "DONE_OK"
    assert (run_dir / "part.step").exists()
    assert status["artefacts"]["renders"] == []
    assert any("render failed" in w for w in status["warnings"])


@pytest.mark.live
@pytest.mark.skipif(
    os.environ.get("ANTHROPIC_API_KEY") is None, reason="no ANTHROPIC_API_KEY"
)
def test_live_end_to_end_cube(tmp_path):
    """Exit criterion #5: a real Loop.run produces the full run folder."""
    from anthropic import Anthropic

    prompts = PromptsBundle(planner_system=_PROMPTS_FILE.read_text(encoding="utf-8"))
    loop = Loop(out_root=tmp_path, cfg=RunConfig(), client=Anthropic(), prompts=prompts)
    run_dir = loop.run(_CUBE_PROMPT)

    for name in (
        "prompt.txt",
        "intent.json",
        "code.py",
        "part.step",
        "trace.jsonl",
        "status.json",
    ):
        assert (run_dir / name).exists(), f"missing {name}"
    assert len(list((run_dir / "renders").glob("*.png"))) == 3
    status = _status(run_dir)
    assert status["status"] == "DONE_OK"
    assert status["exit_code"] == 0
    assert status["cost_usd_estimate"] > 0
