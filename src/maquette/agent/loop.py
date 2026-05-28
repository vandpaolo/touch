"""The run orchestrator: prompt -> Intent -> code -> STEP -> renders.

`Loop.run` drives the v0 single-pass state machine

    PROMPT_RECEIVED -> PLANNING -> CODE_EMITTING -> EXECUTING -> DONE_OK
                                 \\-> PLANNING_FAILED | ADAPTER_REFUSED
                                 \\-> EXEC_FAILED | EXEC_TIMEOUT

and is the only module that lays out ``output/<run-id>/``. It writes the
F8 artefact set (`prompt.txt`, `intent.json`, `code.py`, `part.step`,
`renders/`, `trace.jsonl`, `status.json`, and `error.json` on failure),
maps each failure to its F13 exit code, and records cost via `pricing`.

Rendering is owned here (not the executor): after a valid STEP the Loop
calls `render.orthographic` in a try/except so a render failure never
fails an otherwise-good run (F7).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from anthropic import AnthropicError

from maquette.adapters import AdapterRefusal
from maquette.agent import worker
from maquette.agent.executor import Executor
from maquette.agent.planner import PlannerExhausted, PromptsBundle, plan
from maquette.agent.sanity import check
from maquette.intent import Intent
from maquette.intent_validation import validate_kind_contracts
from maquette.pricing import Tokens, known_models, price
from maquette.render import orthographic

_EXIT_OK = 0
_EXIT_GENERIC = 1
_EXIT_PLANNER = 10
_EXIT_ADAPTER = 11

_ERROR_NAME = "error.json"


@dataclass(frozen=True)
class RunConfig:
    model: str = "claude-opus-4-7"
    max_iterations: int = 1  # v0 is single-pass; refinement is v0.1.
    exec_timeout_s: float = 30.0
    sanity_enabled: bool = True
    max_tokens_in: int = 0  # 0 = no cap in v0 (N2 records, never gates).
    max_tokens_out: int = 0


@dataclass
class _Run:
    """Mutable per-run accumulator (not the persisted record)."""

    started_at: datetime
    events: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tokens: Tokens = field(default_factory=lambda: Tokens(0, 0, 0, 0))
    last_t: float = field(default_factory=perf_counter)


class Loop:
    def __init__(
        self,
        out_root: Path,
        cfg: RunConfig,
        client: Any,
        prompts: PromptsBundle,
    ) -> None:
        self.out_root = out_root
        self.cfg = cfg
        self._client = client
        self._prompts = prompts
        self._prompts_hash = hashlib.sha256(
            prompts.planner_system.encode("utf-8")
        ).hexdigest()

    def run(self, prompt: str) -> Path:
        run = _Run(started_at=datetime.now(UTC))
        self._emit(run, "PROMPT_RECEIVED")

        intent, plan_error = self._plan(run, prompt)

        intent_name = intent.name if intent is not None else "unplanned"
        run_dir = self._make_run_dir(run.started_at, intent_name)
        (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

        if intent is None:
            self._emit(run, "PLANNING_FAILED", error=plan_error)
            return self._finalize(
                run_dir, run, "PLANNING_FAILED", _EXIT_PLANNER, plan_error
            )

        (run_dir / "intent.json").write_text(
            intent.model_dump_json(indent=2), encoding="utf-8"
        )

        violations = validate_kind_contracts(intent)
        if violations:
            detail = "; ".join(v.message for v in violations)
            self._emit(run, "PLANNING_FAILED", error=detail, violations=len(violations))
            return self._finalize(
                run_dir, run, "PLANNING_FAILED", _EXIT_PLANNER, detail
            )

        if self.cfg.sanity_enabled:
            self._run_sanity(run, prompt, intent)

        try:
            code = worker.emit_code(intent)
        except AdapterRefusal as e:
            reason = f"{e.where}: {e.reason}"
            self._emit(run, "ADAPTER_REFUSED", error=reason)
            return self._finalize(
                run_dir, run, "ADAPTER_REFUSED", _EXIT_ADAPTER, reason
            )

        code_path = run_dir / "code.py"
        code_path.write_text(code, encoding="utf-8")
        self._emit(run, "CODE_EMITTING")

        result = Executor(run_dir, self.cfg.exec_timeout_s).execute(code_path)
        if result.exit_code != 0:
            state = "EXEC_TIMEOUT" if result.exit_code == 13 else "EXEC_FAILED"
            self._emit(
                run, state, error=result.error, exec_duration_s=result.duration_s
            )
            # The executor already wrote error.json; do not overwrite it.
            return self._finalize(run_dir, run, state, result.exit_code, None)
        self._emit(run, "EXECUTING", exec_duration_s=result.duration_s)

        self._render(run, result.step_path, run_dir)

        self._emit(run, "DONE_OK")
        return self._finalize(run_dir, run, "DONE_OK", _EXIT_OK, None)

    # ---- pipeline steps -------------------------------------------------

    def _plan(self, run: _Run, prompt: str) -> tuple[Intent | None, str | None]:
        try:
            pr = plan(self._client, prompt, self.cfg.model, self._prompts)
        except PlannerExhausted as e:
            return None, f"planner exhausted: {e}"
        except AnthropicError as e:
            # Auth / rate-limit / network errors during planning are a
            # planning failure (exit 10) — the run folder is still written.
            return None, f"anthropic API error: {e}"
        run.tokens = pr.tokens
        self._emit(
            run,
            "PLANNING",
            retries=pr.retries,
            planner_duration_s=pr.duration_s,
            tokens_in=pr.tokens.input,
            tokens_out=pr.tokens.output,
            cache_read_tokens=pr.tokens.cache_read,
            cache_creation_tokens=pr.tokens.cache_creation,
        )
        return pr.intent, None

    def _run_sanity(self, run: _Run, prompt: str, intent: Intent) -> None:
        result = check(prompt, intent)
        for mismatch in result.mismatches:
            run.warnings.append(mismatch.message)
            self._emit(run, "DIMENSION_WARNING", message=mismatch.message)

    def _render(self, run: _Run, step_path: Path | None, run_dir: Path) -> None:
        if step_path is None:
            return
        try:
            orthographic(step_path, run_dir)
        except Exception as e:  # F7: render failure is non-fatal.
            warning = f"render failed: {e}"
            run.warnings.append(warning)
            self._emit(run, "RENDER_FAILED", message=warning)

    # ---- run-dir + writers ----------------------------------------------

    def _make_run_dir(self, started_at: datetime, intent_name: str) -> Path:
        stamp = started_at.strftime("%Y-%m-%dT%H-%M-%S")
        run_id = f"{stamp}__{_slugify(intent_name)}"
        run_dir = self.out_root / run_id
        suffix = 1
        while run_dir.exists():
            run_dir = self.out_root / f"{run_id}_{suffix}"
            suffix += 1
        run_dir.mkdir(parents=True)
        return run_dir

    def _emit(self, run: _Run, step: str, **fields: Any) -> None:
        now = perf_counter()
        event: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "step": step,
            "duration_s": round(now - run.last_t, 6),
        }
        run.last_t = now
        event.update({k: v for k, v in fields.items() if v is not None})
        run.events.append(event)

    def _finalize(
        self,
        run_dir: Path,
        run: _Run,
        status: str,
        exit_code: int,
        error: str | None,
    ) -> Path:
        if error is not None and not (run_dir / _ERROR_NAME).exists():
            (run_dir / _ERROR_NAME).write_text(
                json.dumps({"reason": error, "exit_code": exit_code}, indent=2),
                encoding="utf-8",
            )
        self._write_trace(run_dir, run.events)
        self._write_status(run_dir, run, status, exit_code)
        return run_dir

    def _write_trace(self, run_dir: Path, events: list[dict[str, Any]]) -> None:
        lines = "".join(json.dumps(e) + "\n" for e in events)
        (run_dir / "trace.jsonl").write_text(lines, encoding="utf-8")

    def _write_status(
        self, run_dir: Path, run: _Run, status: str, exit_code: int
    ) -> None:
        finished_at = datetime.now(UTC)
        cost = (
            price(self.cfg.model, run.tokens)
            if self.cfg.model in known_models()
            else 0.0
        )
        renders = sorted(p.name for p in (run_dir / "renders").glob("*.png"))
        payload = {
            "status": status,
            "exit_code": exit_code,
            "started_at": run.started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_s": (finished_at - run.started_at).total_seconds(),
            "iterations": 1,
            "tokens": {
                "input": run.tokens.input,
                "output": run.tokens.output,
                "cache_read": run.tokens.cache_read,
                "cache_creation": run.tokens.cache_creation,
            },
            "cost_usd_estimate": cost,
            "warnings": run.warnings,
            "artefacts": {
                "prompt_txt": (run_dir / "prompt.txt").exists(),
                "intent_json": (run_dir / "intent.json").exists(),
                "code_py": (run_dir / "code.py").exists(),
                "part_step": (run_dir / "part.step").exists(),
                "renders": renders,
                "error_json": (run_dir / _ERROR_NAME).exists(),
            },
            "prompts_hash": self._prompts_hash,
        }
        (run_dir / "status.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "run"
