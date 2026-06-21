"""Tests for `touch_backend.agent.executor.Executor`.

Uses tiny hand-written build123d snippets (no LLM) executed in real
subprocesses. Covers the success path, crash -> error.json (N6), the
no-STEP failure, and the timeout path (N9).
"""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from touch_backend.agent.executor import (
    ExecutionResult,
    Executor,
    _import_lint,
    _last_exception_line,
    _scrub_env,
)

_OK_SNIPPET = (
    "from build123d import Box, export_step\n"
    "export_step(Box(10, 10, 10), 'part.step')\n"
)
_CRASH_SNIPPET = "raise RuntimeError('boom from generated code')\n"
_NO_STEP_SNIPPET = "x = 1 + 1\n"
_HANG_SNIPPET = "import time\ntime.sleep(30)\n"
# Ignores SIGTERM, forcing the executor to escalate to SIGKILL (N9).
_SIGTERM_IGNORING_SNIPPET = (
    "import signal, time\n"
    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
    "while True:\n"
    "    time.sleep(0.05)\n"
)


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


def test_relative_out_dir_does_not_double_path(tmp_path: Path, monkeypatch):
    """Regression: a relative out_dir + cwd=out_dir must not double the
    code path (out_dir/out_dir/code.py). The default `touch_backend design`
    uses a relative out_root (output/), so this is the common path."""
    monkeypatch.chdir(tmp_path)
    out = Path("run")
    out.mkdir()
    code_path = out / "code.py"
    code_path.write_text(_OK_SNIPPET, encoding="utf-8")

    result = Executor(out_dir=out, timeout_s=60).execute(code_path)

    assert result.exit_code == 0, f"unexpected failure: {result.error}"
    assert (out / "part.step").stat().st_size > 0


def test_crash_writes_error_json_exit_12(tmp_path: Path):
    code_path = _write_code(tmp_path, _CRASH_SNIPPET)
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)

    assert result.exit_code == 12
    assert result.step_path is None
    # The real exception is surfaced (not the opaque exit code) so the user
    # learns *why* the build failed.
    assert result.error == "RuntimeError: boom from generated code"

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


def test_sigterm_ignoring_process_is_sigkilled(tmp_path: Path):
    """N9: a process that ignores SIGTERM is escalated to SIGKILL and reaped
    within timeout + grace, leaving no orphan (execute() returns promptly)."""
    code_path = _write_code(tmp_path, _SIGTERM_IGNORING_SNIPPET)
    start = perf_counter()
    result = Executor(out_dir=tmp_path, timeout_s=1).execute(code_path)
    elapsed = perf_counter() - start

    assert result.exit_code == 13
    # timeout (1s) + SIGKILL grace (2s) + margin; if SIGKILL had not reaped
    # the child, communicate() would block well past this bound.
    assert elapsed < 8, f"executor did not reap the runaway child (took {elapsed:.1f}s)"


def test_last_exception_line_shortens_qualified_name():
    stderr = (
        "Traceback (most recent call last):\n"
        '  File "code.py", line 4, in <module>\n'
        "    op_2 = chamfer(...)\n"
        "touch_backend.finder.FinderError: no face contains point (20.0, 0.0, 0.0)\n"
    )
    assert (
        _last_exception_line(stderr)
        == "FinderError: no face contains point (20.0, 0.0, 0.0)"
    )


def test_last_exception_line_keeps_bare_name_and_handles_empty():
    assert _last_exception_line("ValueError: try a smaller length") == (
        "ValueError: try a smaller length"
    )
    assert _last_exception_line("") is None
    assert _last_exception_line(None) is None


# --- workspace confinement (F46, ADR-0016) ---------------------------------


def test_network_is_disabled(tmp_path: Path):
    code_path = _write_code(
        tmp_path, "import socket\nsocket.create_connection(('localhost', 9))\n"
    )
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)
    assert result.exit_code == 12
    assert "network is disabled" in (result.error or "")


def test_write_outside_the_workspace_is_blocked(tmp_path: Path):
    escape = tmp_path.parent / "touch_escape.txt"
    code_path = _write_code(tmp_path, f"open({str(escape)!r}, 'w').write('x')\n")
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)
    assert result.exit_code == 12
    assert "write outside the workspace" in (result.error or "")
    assert not escape.exists()


def test_write_inside_the_workspace_is_allowed_and_build_still_works(tmp_path: Path):
    snippet = (
        "from build123d import Box, export_step\n"
        "open('inside.txt', 'w').write('hi')\n"
        "export_step(Box(5, 5, 5), 'part.step')\n"
    )
    code_path = _write_code(tmp_path, snippet)
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)
    assert result.exit_code == 0
    assert (tmp_path / "inside.txt").read_text() == "hi"
    assert (tmp_path / "part.step").stat().st_size > 0


def test_secrets_are_scrubbed_from_the_subprocess_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TOUCH_FAKE_API_KEY", "secret123")
    monkeypatch.setenv("TOUCH_FAKE_PUBLIC", "public-ok")
    snippet = (
        "import os\n"
        "open('env.txt', 'w').write(repr(("
        "os.environ.get('TOUCH_FAKE_API_KEY'), os.environ.get('TOUCH_FAKE_PUBLIC'))))\n"
    )
    Executor(out_dir=tmp_path, timeout_s=60).execute(_write_code(tmp_path, snippet))
    # The *_KEY var is dropped (no secrets in env); the public var is kept.
    assert (tmp_path / "env.txt").read_text() == repr((None, "public-ok"))


def test_scrub_env_drops_secret_named_vars_keeps_path(monkeypatch):
    monkeypatch.setenv("MY_TOKEN", "x")
    monkeypatch.setenv("DB_PASSWORD", "y")
    scrubbed = _scrub_env()
    assert "MY_TOKEN" not in scrubbed and "DB_PASSWORD" not in scrubbed
    assert "PATH" in scrubbed  # essentials kept so OCP still loads


def test_import_lint_warns_on_risky_modules_only():
    assert _import_lint("from build123d import *\nbody = Box(1, 1, 1)\n") == ()
    warnings = _import_lint("import os\nimport socket\nfrom subprocess import run\n")
    assert len(warnings) == 3
    assert any("'os'" in w for w in warnings)
    assert any("'socket'" in w for w in warnings)
    assert any("'subprocess'" in w for w in warnings)


def test_executor_surfaces_import_lint_warnings(tmp_path: Path):
    result = Executor(out_dir=tmp_path, timeout_s=60).execute(
        _write_code(tmp_path, "import os\nx = 1\n")
    )
    assert any("'os'" in w for w in result.warnings)
