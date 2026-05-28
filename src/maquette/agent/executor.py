"""Subprocess execution of worker-emitted build123d code.

`Executor.execute` runs the emitted ``code.py`` in a child interpreter
with the run directory as its working directory, so the program's
``export_step(..., "part.step")`` lands inside the run folder. It
enforces a wall-clock timeout with a SIGKILL grace (N9), captures the
STEP, and on failure writes a structured ``error.json`` (N6) — never a
raw traceback to the caller.

This module is a pure subprocess manager: it does **not** render (the
Loop owns rendering) and does not import any other maquette module.

Exit codes follow F13: 0 success, 12 execution failure (crash or no
STEP), 13 timeout.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

_EXIT_OK = 0
_EXIT_EXEC_FAILED = 12
_EXIT_TIMEOUT = 13

# SIGKILL grace after SIGTERM on timeout (N9: killed within timeout + 2 s).
_KILL_GRACE_S = 2.0

# Cap stderr captured into error.json so a runaway program can't bloat it.
_STDERR_TAIL_CHARS = 4000

_STEP_NAME = "part.step"
_ERROR_NAME = "error.json"


@dataclass(frozen=True)
class ExecutionResult:
    """Outcome of running emitted code. Rendering is the Loop's job."""

    step_path: Path | None
    error: str | None
    exit_code: int
    duration_s: float


class Executor:
    """Runs emitted code in a sandboxed-by-timeout subprocess."""

    def __init__(self, out_dir: Path, timeout_s: float) -> None:
        self.out_dir = out_dir
        self.timeout_s = timeout_s

    def execute(self, code_path: Path) -> ExecutionResult:
        start = perf_counter()
        proc = subprocess.Popen(
            # Absolute path: the subprocess runs with cwd=out_dir, so a
            # relative code_path would resolve against out_dir and double
            # (out_dir/out_dir/code.py). -I (isolated): do NOT prepend the
            # run dir to sys.path — the emitted file is named code.py (F8)
            # and would otherwise shadow the stdlib `code` module and break
            # build123d's imports. Isolation also ignores env/user-site.
            [sys.executable, "-I", str(code_path.resolve())],
            cwd=self.out_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _, stderr = proc.communicate(timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            stderr = self._terminate(proc)
            duration = perf_counter() - start
            reason = f"execution timed out after {self.timeout_s:g}s"
            self._write_error(reason, _EXIT_TIMEOUT, stderr)
            return ExecutionResult(None, reason, _EXIT_TIMEOUT, duration)

        duration = perf_counter() - start

        if proc.returncode != 0:
            reason = f"subprocess exited with code {proc.returncode}"
            self._write_error(reason, _EXIT_EXEC_FAILED, stderr)
            return ExecutionResult(None, reason, _EXIT_EXEC_FAILED, duration)

        step_path = self.out_dir / _STEP_NAME
        if not step_path.exists() or step_path.stat().st_size == 0:
            reason = "subprocess succeeded but produced no part.step"
            self._write_error(reason, _EXIT_EXEC_FAILED, stderr)
            return ExecutionResult(None, reason, _EXIT_EXEC_FAILED, duration)

        return ExecutionResult(step_path, None, _EXIT_OK, duration)

    def _terminate(self, proc: subprocess.Popen[str]) -> str:
        """SIGTERM, then SIGKILL after a grace window. Returns stderr."""
        proc.terminate()
        try:
            _, stderr = proc.communicate(timeout=_KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            _, stderr = proc.communicate()
        return stderr

    def _write_error(self, reason: str, exit_code: int, stderr: str | None) -> None:
        payload = {
            "reason": reason,
            "exit_code": exit_code,
            "stderr_tail": (stderr or "")[-_STDERR_TAIL_CHARS:],
        }
        (self.out_dir / _ERROR_NAME).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
