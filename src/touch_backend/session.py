"""Per-connection session: protocol parsing + dispatch.

The session owns the open `TouchDocument` and an `LLMClient` (built lazily from
a factory on first use). Parsing goes through the generated protocol models; any
failure becomes a structured `error` (F21) — never a traceback.

Wired: `plan` (append an op + re-mesh), document lifecycle (`newDoc`/`open`/
`save`/`listFiles`, F10), and `undo`/`redo` (F9). Every document change emits a
`document` snapshot so the FE mirror stays in sync. File I/O is confined to the
project dir (`out_root`); names are sanitized (no path traversal).
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
    MsgDocument,
    MsgError,
    MsgExportStep,
    MsgFileList,
    MsgListFiles,
    MsgNewDoc,
    MsgOp,
    MsgOpen,
    MsgPlan,
    MsgReady,
    MsgRebuild,
    MsgRedo,
    MsgSave,
    MsgUndo,
    Operation,
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


class _DocError(Exception):
    """An invalid document file name / path (e.g. traversal attempt)."""


# FE->BE control messages still stubbed (Cancel=T8, Rebuild=T8, ExportStep=T7,
# ApplyOp=later). `plan` + the document/undo/redo messages are handled.
_STUBBED_MESSAGES = (MsgApplyOp, MsgCancel, MsgRebuild, MsgExportStep)

Response = str | bytes

# Dev-only demo geometry (T2): a 40 mm cube, built through the real pipeline.
_DEMO_OP = Operation.model_validate(
    {
        "id": "demo-cube",
        "kind": "box",
        "params": {"length": 40, "width": 40, "height": 40},
        "selection": None,
        "prompt_text": "demo cube",
        "conversation": [],
        "created_at": "2026-06-01T00:00:00Z",
    }
)


class Session:
    """State + message dispatch for one WebSocket connection."""

    def __init__(
        self,
        client_factory: Callable[[], LLMClient],
        *,
        project_dir: Path = Path("output"),
    ) -> None:
        self.document = TouchDocument()
        self._project_dir = project_dir
        self._client_factory = client_factory
        self._llm: LLMClient | None = None
        self._dirty = False
        self._redo: list[Operation] = []

    def ready(self) -> str:
        """The `ready` envelope sent once on connect (F15)."""
        return MsgReady(type="ready", schema_version=SCHEMA_VERSION).model_dump_json()

    def demo_mesh(self) -> list[Response]:
        """Dev-only (config.demo_mesh): seed the document with a connect-time
        cube as the default canvas, so the click->prompt flow has a base solid.
        Throwaway dev affordance; `New` gives an empty document."""
        self.document.append(_DEMO_OP)
        mesh = self._rebuild_mesh()
        return [
            self._snapshot(),
            mesh_frame_envelope(mesh).model_dump_json(),
            pack(mesh),
        ]

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
        if isinstance(message, MsgNewDoc):
            return self._handle_new()
        if isinstance(message, MsgOpen):
            return self._handle_open(message)
        if isinstance(message, MsgSave):
            return self._handle_save(message)
        if isinstance(message, MsgListFiles):
            return self._handle_list_files()
        if isinstance(message, MsgUndo):
            return self._handle_undo()
        if isinstance(message, MsgRedo):
            return self._handle_redo()
        if isinstance(message, _STUBBED_MESSAGES):
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

    # --- planning -------------------------------------------------------

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

        self._redo = []  # a new op invalidates the redo stack
        self._dirty = True
        return [
            MsgOp(type="op", operation=operation).model_dump_json(),
            self._snapshot(),
            mesh_frame_envelope(mesh).model_dump_json(),
            pack(mesh),
        ]

    # --- document lifecycle (F10) --------------------------------------

    def _handle_new(self) -> list[Response]:
        self.document = TouchDocument()
        self._redo = []
        self._dirty = False
        return [self._snapshot()]

    def _handle_open(self, message: MsgOpen) -> list[Response]:
        try:
            path = self._doc_path(message.name)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="open")]
        if not path.exists():
            return [
                self._error("not_found", f"no such file: {message.name}", where="open")
            ]
        try:
            self.document = TouchDocument.load(path)
        except (json.JSONDecodeError, ValidationError, OSError):
            return [
                self._error(
                    "open_failed", "could not read the .touch file", where="open"
                )
            ]
        self._redo = []
        self._dirty = False
        return self._snapshot_with_mesh(where="open")

    def _handle_save(self, message: MsgSave) -> list[Response]:
        try:
            path = self._doc_path(message.name)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="save")]
        self.document.name = path.stem
        try:
            self.document.save(path)
        except OSError:
            return [
                self._error(
                    "save_failed", "could not write the .touch file", where="save"
                )
            ]
        self._dirty = False
        return [self._snapshot(), self._file_list()]

    def _handle_list_files(self) -> list[Response]:
        return [self._file_list()]

    # --- undo / redo (F9) ----------------------------------------------

    def _handle_undo(self) -> list[Response]:
        if not self.document.history:
            return [self._error("nothing_to_undo", "history is empty", where="undo")]
        self._redo.append(self.document.history.pop())
        self._dirty = True
        return self._snapshot_with_mesh(where="undo")

    def _handle_redo(self) -> list[Response]:
        if not self._redo:
            return [self._error("nothing_to_redo", "nothing to redo", where="redo")]
        self.document.history.append(self._redo.pop())
        self._dirty = True
        return self._snapshot_with_mesh(where="redo")

    # --- helpers --------------------------------------------------------

    def _doc_path(self, name: str) -> Path:
        """Resolve `name` to a `.touch` path inside the project dir. Rejects path
        traversal outright (separators / `..` / absolute) — CLAUDE.md boundary
        rule — rather than silently rewriting it."""
        if (
            not name
            or ".." in name
            or "/" in name
            or "\\" in name
            or Path(name).is_absolute()
        ):
            raise _DocError("invalid file name")
        stem = name[: -len(".touch")] if name.endswith(".touch") else name
        if not stem:
            raise _DocError("invalid file name")
        self._project_dir.mkdir(parents=True, exist_ok=True)
        path = (self._project_dir / f"{stem}.touch").resolve()
        if path.parent != self._project_dir.resolve():
            raise _DocError("file name escapes the project directory")
        return path

    def _file_list(self) -> str:
        self._project_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(p.stem for p in self._project_dir.glob("*.touch"))
        return MsgFileList(type="fileList", files=files).model_dump_json()

    def _snapshot(self) -> str:
        return MsgDocument(
            type="document",
            name=self.document.name,
            history=self.document.history,
            dirty=self._dirty,
            can_undo=len(self.document.history) > 0,
            can_redo=len(self._redo) > 0,
        ).model_dump_json()

    def _snapshot_with_mesh(self, *, where: str) -> list[Response]:
        """Emit the document snapshot + the re-meshed geometry (or just the
        snapshot for an empty document — the viewport clears)."""
        if not self.document.history:
            return [self._snapshot()]
        try:
            mesh = self._rebuild_mesh()
        except AdapterRefusal as exc:
            return [
                self._snapshot(),
                self._error("adapter_refusal", exc.reason, where=exc.where),
            ]
        except _GeometryError as exc:
            return [
                self._snapshot(),
                self._error("geometry_failed", str(exc), where=where),
            ]
        return [
            self._snapshot(),
            mesh_frame_envelope(mesh).model_dump_json(),
            pack(mesh),
        ]

    def _rebuild_mesh(self, history: list[Operation] | None = None):
        """Build the solid from an operation history and tessellate it.

        Real geometry path (adapter -> subprocess executor -> tessellate). OCP /
        build123d are imported lazily — importing them at module top poisons
        VTK-OSMesa for the in-process render test (auto-memory `render-backend`);
        the heavy OCP build itself runs in the Executor *subprocess*.
        """
        from build123d import import_step

        from touch_backend import operation_adapter
        from touch_backend.agent.executor import Executor
        from touch_backend.tessellate import tessellate

        if history is None:
            history = self.document.history
        code = operation_adapter.emit(history)
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
