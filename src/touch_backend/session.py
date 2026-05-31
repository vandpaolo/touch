"""Per-connection session: protocol parsing + dispatch.

The session owns the open `TouchDocument` and an `LLMClient` (built lazily from
a factory on first use). Parsing goes through the generated protocol models; any
failure becomes a structured `error` (F21) — never a traceback. `plan` is wired
end-to-end (mocked client in tests); the other control messages are stubbed.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

from touch_backend import planner
from touch_backend._generated.protocol import (
    MsgApplyOp,
    MsgCancel,
    MsgError,
    MsgExportStep,
    MsgOp,
    MsgPlan,
    MsgReady,
    MsgRebuild,
    TouchProtocol,
)
from touch_backend.adapters import AdapterRefusal
from touch_backend.document import TouchDocument
from touch_backend.frames import mesh_frame_envelope, pack
from touch_backend.llm_client.base import LLMClient

SCHEMA_VERSION = 1
_EXEC_TIMEOUT_S = 30.0


class _GeometryError(Exception):
    """The emitted code failed to produce a solid."""


# FE->BE control messages the session expects from a client.
_CLIENT_MESSAGES = (MsgPlan, MsgApplyOp, MsgCancel, MsgRebuild, MsgExportStep)

Response = str | bytes


class Session:
    """State + message dispatch for one WebSocket connection."""

    def __init__(self, client_factory: Callable[[], LLMClient]) -> None:
        self.document = TouchDocument()
        self._client_factory = client_factory
        self._llm: LLMClient | None = None

    def ready(self) -> str:
        """The `ready` envelope sent once on connect (F15)."""
        return MsgReady(type="ready", schema_version=SCHEMA_VERSION).model_dump_json()

    def handle(self, raw: str | bytes) -> list[Response]:
        """Parse one inbound message and return zero or more responses (JSON
        strings and/or binary frames). Never raises on bad input (F21)."""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            return [self._error("invalid_json", "message was not valid JSON")]
        if not isinstance(data, dict):
            return [self._error("invalid_message", "envelope must be a JSON object")]

        declared = data.get("type")
        where = declared if isinstance(declared, str) else None
        try:
            envelope = TouchProtocol.model_validate({"message": data})
        except ValidationError:
            return [
                self._error(
                    "invalid_message",
                    "message did not match the protocol schema",
                    where=where,
                )
            ]
        if envelope.message is None:
            return [self._error("invalid_message", "empty message")]

        return self._dispatch(envelope.message.root)

    def _client(self) -> LLMClient:
        if self._llm is None:
            self._llm = self._client_factory()
        return self._llm

    def _dispatch(self, message: object) -> list[Response]:
        if isinstance(message, MsgPlan):
            return self._handle_plan(message)
        if isinstance(message, _CLIENT_MESSAGES):
            return [
                self._error(
                    "not_implemented",
                    f"{message.type} is not handled yet",
                    where=message.type,
                )
            ]
        where = getattr(message, "type", None)
        return [
            self._error(
                "unexpected_message",
                "this message type is server->client only",
                where=where if isinstance(where, str) else None,
            )
        ]

    def _handle_plan(self, message: MsgPlan) -> list[Response]:
        try:
            operation = planner.plan(
                self._client(), message.prompt_text, message.selection
            )
        except planner.PlannerError as exc:
            return [self._error("plan_failed", str(exc), where="plan")]

        self.document.append(operation)

        try:
            mesh = self._rebuild_mesh()
        except AdapterRefusal as exc:
            self.document.history.pop()  # the op didn't take; don't keep it
            return [self._error("adapter_refusal", exc.reason, where=exc.where)]
        except _GeometryError as exc:
            self.document.history.pop()
            return [self._error("geometry_failed", str(exc), where="execute")]

        envelope = mesh_frame_envelope(mesh)
        return [
            MsgOp(type="op", operation=operation).model_dump_json(),
            envelope.model_dump_json(),
            pack(mesh),
        ]

    def _rebuild_mesh(self):
        """Build the current solid from the operation history and tessellate it.

        Real geometry path (adapter -> subprocess executor -> tessellate). OCP /
        build123d are imported lazily — importing them at module top poisons
        VTK-OSMesa for the in-process render test (auto-memory `render-backend`);
        the heavy OCP build itself runs in the Executor *subprocess*.
        """
        from build123d import import_step

        from touch_backend import operation_adapter
        from touch_backend.agent.executor import Executor
        from touch_backend.tessellate import tessellate

        code = operation_adapter.emit(self.document.history)
        with tempfile.TemporaryDirectory(prefix="touch-rebuild-") as tmp:
            out_dir = Path(tmp)
            code_path = out_dir / "code.py"
            code_path.write_text(code, encoding="utf-8")
            result = Executor(out_dir, _EXEC_TIMEOUT_S).execute(code_path)
            if result.step_path is None:
                raise _GeometryError(result.error or "execution produced no solid")
            solid = import_step(result.step_path)
        return tessellate(solid)

    @staticmethod
    def _error(code: str, message: str, where: str | None = None) -> str:
        return MsgError(
            type="error", code=code, message=message, where=where
        ).model_dump_json()
