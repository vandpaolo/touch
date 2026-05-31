"""Per-connection session: protocol parsing + dispatch.

The session owns the open `TouchDocument` and turns raw wire messages into
structured responses. Parsing/validation goes through the generated protocol
models; any failure becomes a structured `error` (F21) — never a traceback.
Control-message handlers (`plan`, …) are wired in incrementally; `plan` lands
in T1b day 5.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from touch_backend._generated.protocol import (
    MsgApplyOp,
    MsgCancel,
    MsgError,
    MsgExportStep,
    MsgPlan,
    MsgReady,
    MsgRebuild,
    TouchProtocol,
)
from touch_backend.document import TouchDocument

SCHEMA_VERSION = 1

# FE->BE control messages the session expects to receive from a client.
_CLIENT_MESSAGES = (MsgPlan, MsgApplyOp, MsgCancel, MsgRebuild, MsgExportStep)


class Session:
    """State + message dispatch for one WebSocket connection."""

    def __init__(self) -> None:
        self.document = TouchDocument()

    def ready(self) -> str:
        """The `ready` envelope sent once on connect (F15)."""
        return MsgReady(type="ready", schema_version=SCHEMA_VERSION).model_dump_json()

    def handle(self, raw: str | bytes) -> list[str]:
        """Parse one inbound message and return zero or more JSON responses.

        Never raises on bad input — malformed messages return a structured
        `error` (F21).
        """
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

    def _dispatch(self, message: object) -> list[str]:
        if isinstance(message, _CLIENT_MESSAGES):
            # Handlers are wired incrementally; `plan` lands in T1b day 5.
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

    @staticmethod
    def _error(code: str, message: str, where: str | None = None) -> str:
        return MsgError(
            type="error", code=code, message=message, where=where
        ).model_dump_json()
