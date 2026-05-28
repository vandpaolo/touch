"""Tests for `maquette.cli` via Typer's CliRunner.

`Loop` is monkeypatched (no real API, no subprocess) and `load_dotenv`
is neutered so the repo's `.env` does not leak the real key into tests.
The env is controlled explicitly per test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from maquette import cli as cli_mod
from maquette.cli import app

runner = CliRunner()


def _fake_loop(exit_code: int, capture: dict):
    class FakeLoop:
        def __init__(self, out_root, cfg, client, prompts):
            capture["out_root"] = out_root
            capture["cfg"] = cfg
            capture["prompts"] = prompts
            self._out_root = out_root

        def run(self, prompt: str) -> Path:
            capture["prompt"] = prompt
            run_dir = self._out_root / "2026-01-01T00-00-00__test"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "status.json").write_text(
                json.dumps({"exit_code": exit_code}), encoding="utf-8"
            )
            return run_dir

    return FakeLoop


@pytest.fixture
def cli_env(monkeypatch):
    """Neuter dotenv loading and give the CLI a (fake) API key by default."""
    monkeypatch.setattr(cli_mod, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_design_happy_path_exit_0(tmp_path, monkeypatch, cli_env):
    capture: dict = {}
    monkeypatch.setattr(cli_mod, "Loop", _fake_loop(0, capture))

    result = runner.invoke(app, ["design", "a 50 mm cube", "--out", str(tmp_path)])

    assert result.exit_code == 0
    assert capture["prompt"] == "a 50 mm cube"
    run_dir = tmp_path / "2026-01-01T00-00-00__test"
    assert str(run_dir) in result.output  # F12: run dir printed


@pytest.mark.parametrize("code", [10, 11, 12, 13])
def test_exit_code_maps_from_status(tmp_path, monkeypatch, cli_env, code):
    capture: dict = {}
    monkeypatch.setattr(cli_mod, "Loop", _fake_loop(code, capture))

    result = runner.invoke(app, ["design", "x", "--out", str(tmp_path)])

    assert result.exit_code == code
    # F12: the run dir is printed even on failure exits.
    assert str(tmp_path / "2026-01-01T00-00-00__test") in result.output


def test_missing_api_key_exit_1(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_mod, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Loop must never be reached; make it explode if it is.
    monkeypatch.setattr(cli_mod, "Loop", _fake_loop(0, {}))

    result = runner.invoke(app, ["design", "x", "--out", str(tmp_path)])

    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.output


def test_flags_reach_the_config(tmp_path, monkeypatch, cli_env):
    capture: dict = {}
    monkeypatch.setattr(cli_mod, "Loop", _fake_loop(0, capture))

    result = runner.invoke(
        app,
        [
            "design",
            "x",
            "--out",
            str(tmp_path),
            "--max-iter",
            "5",
            "--exec-timeout",
            "12",
            "--model",
            "claude-haiku-4-5",
        ],
    )

    assert result.exit_code == 0
    assert capture["out_root"] == tmp_path
    rc = capture["cfg"]
    assert rc.max_iterations == 5
    assert rc.exec_timeout_s == 12.0
    assert rc.model == "claude-haiku-4-5"


def test_bad_arg_exit_2(tmp_path, cli_env):
    result = runner.invoke(app, ["design", "x", "--max-iter", "not-an-int"])
    assert result.exit_code == 2


def test_help_lists_all_flags():
    result = runner.invoke(app, ["design", "--help"])
    assert result.exit_code == 0
    for flag in ("--out", "--max-iter", "--exec-timeout", "--model", "-q", "-v"):
        assert flag in result.output
