"""Subprocess execution of worker-emitted build123d code.

`Executor.execute` runs the emitted ``code.py`` in a child interpreter
with the run directory as its working directory, so the program's
``export_step(..., "part.step")`` lands inside the run folder. It
enforces a wall-clock timeout with a SIGKILL grace (N9), captures the
STEP, and on failure writes a structured ``error.json`` (N6) — never a
raw traceback to the caller.

This module is a pure subprocess manager: it does **not** render (the
Loop owns rendering) and does not import any other touch_backend module.

Exit codes follow F13: 0 success, 12 execution failure (crash or no
STEP), 13 timeout.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
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
# The wrapped script actually run = guards + the layer's code. Not "code.py"
# (which would shadow the stdlib `code` module under a run dir on sys.path).
_RUN_NAME = "__touch_exec__.py"

# Env var names matching this are dropped from the subprocess env (no secrets
# in env, F46/ADR-0016). PATH / LD_LIBRARY_PATH etc. are kept so OCP still loads.
_SECRET_RE = re.compile(r"secret|key|token|password|passwd|credential", re.IGNORECASE)

# Modules a layer shouldn't need; the soft import-lint warns (does not block).
_RISKY_MODULES = ("os", "socket", "subprocess")

# Workspace-confinement guards prepended to every executed layer (F46,
# ADR-0016). A NUDGE, not a security boundary — a real OS sandbox replaces this
# before opening untrusted parts. Disables Python sockets and Python-level writes
# outside the workspace; OCC's C++ STEP write (`part.step`, in cwd) is unaffected.
_SECURITY_PREAMBLE = """\
# --- Touch executor guards (F46, ADR-0016): a nudge, not a security boundary.
import builtins as _tb, os as _tos, socket as _tsock, sys as _tsys


def _touch_no_network(*_a, **_k):
    raise OSError("network is disabled in the Touch executor (F46)")


# Block *connecting*, not socket creation — leaving `socket.socket` a real
# (subclassable) class so importing ssl/asyncio (`class SSLSocket(socket)`)
# still works. Connecting is the actual network act, and a layer never needs it.
_tsock.socket.connect = _touch_no_network
_tsock.socket.connect_ex = _touch_no_network
_tsock.create_connection = _touch_no_network

_tallowed = tuple(
    _tos.path.realpath(d) for d in (_tos.getcwd(), _tsys.prefix, _tsys.base_prefix)
)
_touch_real_open = _tb.open


def _touch_guarded_open(file, mode="r", *a, **k):
    if not isinstance(file, int) and any(m in mode for m in ("w", "a", "x", "+")):
        target = _tos.path.realpath(file)
        if not any(
            target == d or target.startswith(d + _tos.sep) for d in _tallowed
        ):
            raise OSError("write outside the workspace is disabled (F46): " + str(file))
    return _touch_real_open(file, mode, *a, **k)


_tb.open = _touch_guarded_open
# --- end guards
"""


def _scrub_env() -> dict[str, str]:
    """The parent env minus secret-named vars (F46): no API keys reach a layer."""
    return {k: v for k, v in os.environ.items() if not _SECRET_RE.search(k)}


def _import_lint(source: str) -> tuple[str, ...]:
    """Soft warnings for a layer importing `os`/`socket`/`subprocess` (F46).

    Advisory only — never blocks execution; the executor is a nudge in v0.
    """
    return tuple(
        f"layer imports {module!r} (discouraged; the executor sandbox is a nudge in v0)"
        for module in _RISKY_MODULES
        if re.search(rf"\b(?:import\s+{module}\b|from\s+{module}\b)", source)
    )


def _last_exception_line(stderr: str | None) -> str | None:
    """The final line of a Python traceback — "SomeError: detail" — with any
    module-qualified exception name shortened to its bare class. None if stderr
    holds no usable line."""
    if not stderr:
        return None
    lines = [ln.strip() for ln in stderr.strip().splitlines() if ln.strip()]
    if not lines:
        return None
    last = lines[-1]
    match = re.match(r"^([\w.]+)(:\s.*)$", last)
    if match and "." in match.group(1):
        return match.group(1).rsplit(".", 1)[-1] + match.group(2)
    return last


@dataclass(frozen=True)
class ExecutionResult:
    """Outcome of running emitted code. Rendering is the Loop's job."""

    step_path: Path | None
    error: str | None
    exit_code: int
    duration_s: float
    # Soft import-lint advisories (F46); empty for a clean layer.
    warnings: tuple[str, ...] = field(default_factory=tuple)


class Executor:
    """Runs emitted code in a sandboxed-by-timeout subprocess."""

    def __init__(self, out_dir: Path, timeout_s: float) -> None:
        self.out_dir = out_dir
        self.timeout_s = timeout_s

    def execute(self, code_path: Path) -> ExecutionResult:
        start = perf_counter()
        source = code_path.read_text(encoding="utf-8")
        warnings = _import_lint(source)
        # Single chokepoint (F46): every layer runs through the same guards +
        # scrubbed env. Guards are prepended; the layer's own tracebacks still
        # surface (the error message is the last exception line, line-agnostic).
        run_path = self.out_dir / _RUN_NAME
        run_path.write_text(_SECURITY_PREAMBLE + "\n" + source, encoding="utf-8")

        proc = subprocess.Popen(
            # Absolute path: the subprocess runs with cwd=out_dir, so a relative
            # path would resolve against out_dir and double. -I (isolated): do
            # NOT prepend the run dir to sys.path, and ignore user-site. env:
            # secrets scrubbed (no API keys reach a layer).
            [sys.executable, "-I", str(run_path.resolve())],
            cwd=self.out_dir,
            env=_scrub_env(),
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
            return ExecutionResult(None, reason, _EXIT_TIMEOUT, duration, warnings)

        duration = perf_counter() - start

        if proc.returncode != 0:
            # Surface the real exception (e.g. "FinderError: no face contains
            # point …") instead of the opaque exit code — the traceback tail is
            # what tells the user *why* the build failed.
            reason = _last_exception_line(stderr) or (
                f"subprocess exited with code {proc.returncode}"
            )
            self._write_error(reason, _EXIT_EXEC_FAILED, stderr)
            return ExecutionResult(None, reason, _EXIT_EXEC_FAILED, duration, warnings)

        step_path = self.out_dir / _STEP_NAME
        if not step_path.exists() or step_path.stat().st_size == 0:
            reason = "subprocess succeeded but produced no part.step"
            self._write_error(reason, _EXIT_EXEC_FAILED, stderr)
            return ExecutionResult(None, reason, _EXIT_EXEC_FAILED, duration, warnings)

        return ExecutionResult(step_path, None, _EXIT_OK, duration, warnings)

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
