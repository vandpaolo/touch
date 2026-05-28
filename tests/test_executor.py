"""Tests for `maquette.agent.executor.Executor`.

Uses tiny hand-written build123d snippets (no LLM) executed in real
subprocesses. Covers the success path, crash -> error.json (N6), the
no-STEP failure, and the timeout path (N9).
"""

from __future__ import annotations

import json
from pathlib import Path

from maquette.agent.executor import ExecutionResult, Executor

_OK_SNIPPET = (
    "from build123d import Box, export_step\n"
    "export_step(Box(10, 10, 10), 'part.step')\n"
)
_CRASH_SNIPPET = "raise RuntimeError('boom from generated code')\n"
_NO_STEP_SNIPPET = "x = 1 + 1\n"
_HANG_SNIPPET = "import time\ntime.sleep(30)\n"


def _write_code(tmp_path: Path, source: str) -> Path:
    code_path = tmp_path / "code.py"
    code_path.write_text(source, encoding="utf-8")
    return code_path


def test_success_produces_step(tmp_path: Path):
    code_path = _write_code(tmp_path, _OK_SNIPPET)
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)

    assert isinstance(result, ExecutionResult)
    assert result.exit_code == 0
    assert result.error is None
    assert result.step_path == tmp_path / "part.step"
    assert result.step_path.stat().st_size > 0
    assert result.duration_s >= 0
    assert not (tmp_path / "error.json").exists()


def test_crash_writes_error_json_exit_12(tmp_path: Path):
    code_path = _write_code(tmp_path, _CRASH_SNIPPET)
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)

    assert result.exit_code == 12
    assert result.step_path is None
    assert result.error is not None

    error_path = tmp_path / "error.json"
    assert error_path.exists(), "error.json not written on crash (N6)"
    payload = json.loads(error_path.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 12
    assert "reason" in payload
    # The original traceback is captured in error.json, not surfaced raw.
    assert "boom from generated code" in payload["stderr_tail"]


def test_no_step_is_exit_12(tmp_path: Path):
    code_path = _write_code(tmp_path, _NO_STEP_SNIPPET)
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)

    assert result.exit_code == 12
    assert result.step_path is None
    assert "part.step" in (result.error or "")
    assert (tmp_path / "error.json").exists()


def test_timeout_is_exit_13(tmp_path: Path):
    code_path = _write_code(tmp_path, _HANG_SNIPPET)
    result = Executor(out_dir=tmp_path, timeout_s=1).execute(code_path)

    assert result.exit_code == 13
    assert result.step_path is None
    assert "timed out" in (result.error or "")
    payload = json.loads((tmp_path / "error.json").read_text(encoding="utf-8"))
    assert payload["exit_code"] == 13
