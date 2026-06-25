"""Per-connection session: protocol parsing + dispatch.

The canonical live document is the **Layer Stack** (ADR-0013): the session holds
one `LayerStack`, every mutation is compare-and-swap'd on its `revision` (the
coordination point the agent over MCP will share in TP2 sprint 2), and geometry
is folded from the stack. The op-history `TouchDocument` is no longer live state
— it is built transiently only for `.touch` I/O (op-native until the Day-2
layer-native cutover), and `_wire_ops` mirrors the layers 1:1 purely to serialize
the op-based `MsgDocument.history` until the protocol carries a layer manifest
(Day 3). The session also owns an `LLMClient` (built lazily on first use).
Parsing goes through the generated protocol models; any failure becomes a
structured `error` (F21) — never a traceback.

Wired: `plan` (append a layer + re-mesh), document lifecycle (`newDoc`/`open`/
`save`/`listFiles`, F10), and `undo`/`redo` (F9, as delete-last / re-add on the
stack). Every document change emits a `document` snapshot so the FE mirror stays
in sync. File I/O is confined to the project dir (`out_root`); names are
sanitized (no path traversal).
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from touch_backend import planner
from touch_backend._generated.protocol import (
    ClarifyingQuestion,
    ConversationTurn,
    DirEntry,
    Kind,
    LayerSummary,
    MsgApplyOp,
    MsgCancel,
    MsgConversationTurn,
    MsgDir,
    MsgDocument,
    MsgError,
    MsgExportStep,
    MsgFileList,
    MsgListDir,
    MsgListFiles,
    MsgNewDoc,
    MsgNewPart,
    MsgOp,
    MsgOpen,
    MsgOpenFolder,
    MsgOpenPart,
    MsgPlan,
    MsgReady,
    MsgRebuild,
    MsgRedo,
    MsgRemovePart,
    MsgRenamePart,
    MsgSave,
    MsgSavePart,
    MsgUndo,
    Operation,
    Selection,
    TouchProtocol,
)
from touch_backend.active_document import ActiveDocument
from touch_backend.adapters import AdapterRefusal
from touch_backend.frames import mesh_frame_envelope, pack
from touch_backend.layer_stack import Layer, LayerStack, LayerStackError
from touch_backend.live_build import GeometryError as _GeometryError
from touch_backend.llm_client.base import LLMClient

SCHEMA_VERSION = 1


class _DocError(Exception):
    """An invalid document file name / path (e.g. traversal attempt)."""


# FE->BE control messages still stubbed (Cancel=T8, Rebuild=T8, ExportStep=T7,
# ApplyOp=later). `plan` + the document/undo/redo messages are handled.
_STUBBED_MESSAGES = (MsgApplyOp, MsgCancel, MsgRebuild, MsgExportStep)

_MAX_CLARIFY_TURNS = 3  # cap the clarification loop (F7); config-tunable later


@dataclass
class _Conversation:
    """In-flight clarification thread (F7): the original click context plus the
    turns so far. Exists only between a question and its resolution."""

    selection: Selection | None
    prompt_text: str
    turns: list[ConversationTurn] = field(default_factory=list)
    attempts: int = 1


def _assistant_turn(text: str) -> ConversationTurn:
    return ConversationTurn.model_validate(
        {"from": "assistant", "text": text, "at": datetime.now(UTC)}
    )


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
        document: ActiveDocument | None = None,
    ) -> None:
        # The canonical document is the shared `ActiveDocument` (ADR-0013); a
        # standalone one is created when none is injected (the Server passes the
        # one shared instance so the viewport + agent act on the same part).
        self.doc = document if document is not None else ActiveDocument()
        self._project_dir = project_dir
        self._workspace_root: Path | None = None
        self._client_factory = client_factory
        self._llm: LLMClient | None = None
        self._conv: _Conversation | None = None

    @property
    def stack(self) -> LayerStack:
        """The canonical Layer Stack (held on the shared `ActiveDocument`)."""
        return self.doc.stack

    def _append_op(self, operation: Operation) -> None:
        """Add a click-path `Operation` as a layer on the canonical stack (CAS,
        add-only — the rebuild is a separate step). Raises `AdapterRefusal`."""
        self.doc.append_op(operation)

    def _rollback_last(self) -> None:
        """Undo the most recent `append_op` (a failed geometry build)."""
        self.doc.rollback_last()

    def _rebuild_mesh(self):
        """Fold the canonical stack to a provenance-baked mesh."""
        return self.doc.rebuild_mesh()

    @staticmethod
    def _layer_summary(layer: Layer) -> LayerSummary:
        """Compact, by-id manifest entry for one layer (N15: identity + params,
        no source — the FE/agent pull source on demand)."""
        return LayerSummary(
            id=layer.id,
            kind=Kind(layer.kind),
            template=layer.template,
            params=layer.params,
            has_selection=layer.selection is not None,
        )

    def ready(self) -> str:
        """The `ready` envelope sent once on connect (F15)."""
        return MsgReady(type="ready", schema_version=SCHEMA_VERSION).model_dump_json()

    def demo_mesh(self) -> list[Response]:
        """Dev-only (config.demo_mesh): seed the document with a connect-time
        cube as the default canvas, so the click->prompt flow has a base solid.
        Throwaway dev affordance; `New` gives an empty document."""
        self._append_op(_DEMO_OP)
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
        if isinstance(message, MsgConversationTurn):
            return self._handle_conversation_turn(message)
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
        if isinstance(message, MsgOpenFolder):
            return self._handle_open_folder(message)
        if isinstance(message, MsgListDir):
            return self._handle_list_dir(message)
        if isinstance(message, MsgOpenPart):
            return self._handle_open_part(message)
        if isinstance(message, MsgSavePart):
            return self._handle_save_part(message)
        if isinstance(message, MsgNewPart):
            return self._handle_new_part(message)
        if isinstance(message, MsgRenamePart):
            return self._handle_rename_part(message)
        if isinstance(message, MsgRemovePart):
            return self._handle_remove_part(message)
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
            result = planner.plan(
                self._client(), message.prompt_text, message.selection
            )
        except planner.PlannerError as exc:
            return [self._error("plan_failed", str(exc), where="plan")]

        # The planner may ask instead of answering (F7): open a clarification
        # thread that the user's reply (a conversationTurn) resumes.
        if isinstance(result, ClarifyingQuestion):
            self._conv = _Conversation(
                selection=message.selection,
                prompt_text=message.prompt_text,
                turns=[_assistant_turn(result.question)],
                attempts=1,
            )
            return [self._clarify_message(result)]

        self._conv = None  # a clean op cancels any stale thread
        return self._apply_operation(result)

    def _handle_conversation_turn(self, message: MsgConversationTurn) -> list[Response]:
        """A user reply (F7): resume planning with the thread; cap the loop."""
        if self._conv is None:
            return [
                self._error(
                    "no_conversation",
                    "no clarification is in progress",
                    where="conversationTurn",
                )
            ]
        conv = self._conv
        conv.turns.append(message.turn)  # the user's reply
        conv.attempts += 1
        if conv.attempts > _MAX_CLARIFY_TURNS:
            self._conv = None
            return [
                self._error(
                    "clarify_exhausted",
                    f"gave up after {_MAX_CLARIFY_TURNS} clarification turns",
                    where="conversationTurn",
                )
            ]
        try:
            result = planner.plan(
                self._client(),
                conv.prompt_text,
                conv.selection,
                attempt=conv.attempts,
                conversation=conv.turns,
            )
        except planner.PlannerError as exc:
            return [self._error("plan_failed", str(exc), where="plan")]

        if isinstance(result, ClarifyingQuestion):
            conv.turns.append(_assistant_turn(result.question))
            return [self._clarify_message(result)]

        self._conv = None
        return self._apply_operation(result)

    def _apply_operation(self, operation: Operation) -> list[Response]:
        """Append a layer (CAS), rebuild geometry, emit op + snapshot + mesh."""
        try:
            self._append_op(operation)  # may refuse an unsupported kind pre-mutation
        except AdapterRefusal as exc:
            return [self._error("adapter_refusal", exc.reason, where=exc.where)]
        try:
            mesh = self._rebuild_mesh()
        except AdapterRefusal as exc:
            self._rollback_last()  # the layer didn't build; don't keep it
            return [self._error("adapter_refusal", exc.reason, where=exc.where)]
        except _GeometryError as exc:
            self._rollback_last()
            return [self._error("geometry_failed", str(exc), where="execute")]

        self.doc.clear_redo()  # a new op invalidates the redo stack
        self.doc.dirty = True
        return [
            # by_alias: the op's conversation turns serialize `from`, not `from_`.
            MsgOp(type="op", operation=operation).model_dump_json(by_alias=True),
            self._snapshot(),
            mesh_frame_envelope(mesh).model_dump_json(),
            pack(mesh),
        ]

    # --- document lifecycle (F10) --------------------------------------

    def _handle_new(self) -> list[Response]:
        self.doc.reset(name="untitled")
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
            self.doc.open(path)
        except AdapterRefusal as exc:
            return [self._error("adapter_refusal", exc.reason, where="open")]
        except (
            json.JSONDecodeError,
            ValidationError,
            OSError,
            ValueError,
            KeyError,
            LayerStackError,
        ):
            return [
                self._error(
                    "open_failed", "could not read the .touch file", where="open"
                )
            ]
        return self._snapshot_with_mesh(where="open")

    def _handle_save(self, message: MsgSave) -> list[Response]:
        try:
            path = self._doc_path(message.name)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="save")]
        self.doc.name = path.stem
        try:
            self.doc.save(path)
        except OSError:
            return [
                self._error(
                    "save_failed", "could not write the .touch file", where="save"
                )
            ]
        return [self._snapshot(), self._file_list()]

    def _handle_list_files(self) -> list[Response]:
        return [self._file_list()]

    # --- undo / redo (F9) ----------------------------------------------

    def _handle_undo(self) -> list[Response]:
        if not self.doc.can_undo:
            return [self._error("nothing_to_undo", "history is empty", where="undo")]
        self.doc.undo()  # append-only delete-last (CAS), stashes the layer for redo
        return self._snapshot_with_mesh(where="undo")

    def _handle_redo(self) -> list[Response]:
        if not self.doc.can_redo:
            return [self._error("nothing_to_redo", "nothing to redo", where="redo")]
        self.doc.redo()  # re-add the undone layer verbatim (CAS)
        return self._snapshot_with_mesh(where="redo")

    # --- workspace folder (ADR-0010) -----------------------------------

    def _handle_open_folder(self, message: MsgOpenFolder) -> list[Response]:
        root = Path(message.path).expanduser()
        if not root.is_dir():
            return [
                self._error(
                    "not_found", f"no such folder: {message.path}", where="openFolder"
                )
            ]
        self._workspace_root = root.resolve()
        return [self._list_dir("")]

    def _handle_list_dir(self, message: MsgListDir) -> list[Response]:
        try:
            return [self._list_dir(message.path)]
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="listDir")]

    def _handle_open_part(self, message: MsgOpenPart) -> list[Response]:
        try:
            path = self._resolve_in_workspace(message.path)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="openPart")]
        if not path.exists():
            return [
                self._error(
                    "not_found", f"no such part: {message.path}", where="openPart"
                )
            ]
        try:
            self.doc.open(path)
        except AdapterRefusal as exc:
            return [self._error("adapter_refusal", exc.reason, where="openPart")]
        except (
            json.JSONDecodeError,
            ValidationError,
            OSError,
            ValueError,
            KeyError,
            LayerStackError,
        ):
            return [
                self._error(
                    "open_failed", "could not read the .touch part", where="openPart"
                )
            ]
        return self._snapshot_with_mesh(where="openPart")

    def _handle_save_part(self, message: MsgSavePart) -> list[Response]:
        try:
            path = self._resolve_in_workspace(message.path)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="savePart")]
        self.doc.name = path.stem
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.doc.save(path)
        except OSError:
            return [
                self._error(
                    "save_failed", "could not write the .touch part", where="savePart"
                )
            ]
        return [self._snapshot(), self._list_dir(self._rel(path.parent))]

    def _handle_new_part(self, message: MsgNewPart) -> list[Response]:
        try:
            path = self._resolve_in_workspace(message.path)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="newPart")]
        if path.exists():
            return [
                self._error(
                    "exists", f"already exists: {message.path}", where="newPart"
                )
            ]
        self.doc.reset(name=path.stem)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.doc.save(path)
        except OSError:
            return [
                self._error(
                    "save_failed", "could not create the .touch part", where="newPart"
                )
            ]
        return [self._snapshot(), self._list_dir(self._rel(path.parent))]

    def _handle_rename_part(self, message: MsgRenamePart) -> list[Response]:
        try:
            src = self._resolve_in_workspace(message.path)
            dst = self._resolve_in_workspace(message.to_path)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="renamePart")]
        if not src.exists():
            return [
                self._error(
                    "not_found", f"no such entry: {message.path}", where="renamePart"
                )
            ]
        if dst.exists():
            return [
                self._error(
                    "exists", f"already exists: {message.to_path}", where="renamePart"
                )
            ]
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
        except OSError:
            return [
                self._error("rename_failed", "could not rename", where="renamePart")
            ]
        out: list[Response] = [self._list_dir(self._rel(src.parent))]
        if dst.parent != src.parent:
            out.append(self._list_dir(self._rel(dst.parent)))
        return out

    def _handle_remove_part(self, message: MsgRemovePart) -> list[Response]:
        try:
            path = self._resolve_in_workspace(message.path)
        except _DocError as exc:
            return [self._error("invalid_path", str(exc), where="removePart")]
        if not path.exists():
            return [
                self._error(
                    "not_found", f"no such entry: {message.path}", where="removePart"
                )
            ]
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError:
            return [
                self._error("remove_failed", "could not remove", where="removePart")
            ]
        return [self._list_dir(self._rel(path.parent))]

    def _resolve_in_workspace(self, relpath: str) -> Path:
        """Resolve a workspace-relative path, contained to the open root (no
        traversal / absolute escape; ADR-0010 / CLAUDE.md boundary rule)."""
        if self._workspace_root is None:
            raise _DocError("no workspace folder is open")
        candidate = (self._workspace_root / relpath).resolve()
        if (
            candidate != self._workspace_root
            and self._workspace_root not in candidate.parents
        ):
            raise _DocError("path escapes the workspace")
        return candidate

    def _rel(self, path: Path) -> str:
        assert self._workspace_root is not None
        return (
            ""
            if path == self._workspace_root
            else str(path.relative_to(self._workspace_root))
        )

    def _list_dir(self, relpath: str) -> str:
        target = self._resolve_in_workspace(relpath)
        entries: list[DirEntry] = []
        if target.is_dir():
            for p in sorted(
                target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
            ):
                entries.append(DirEntry(name=p.name, is_dir=p.is_dir()))
        return MsgDir(type="dir", path=relpath, entries=entries).model_dump_json()

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
            name=self.doc.name,
            layers=[self._layer_summary(layer) for layer in self.doc.layers],
            revision=self.doc.revision,
            dirty=self.doc.dirty,
            can_undo=self.doc.can_undo,
            can_redo=self.doc.can_redo,
        ).model_dump_json(by_alias=True)

    def _snapshot_with_mesh(self, *, where: str) -> list[Response]:
        """Emit the document snapshot + the re-meshed geometry (or just the
        snapshot for an empty document — the viewport clears)."""
        if not self.doc.layers:
            return [self._snapshot()]
        try:
            mesh = self.doc.rebuild_mesh()
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

    @staticmethod
    def _clarify_message(question: ClarifyingQuestion) -> str:
        """Wrap a planner ClarifyingQuestion as a conversationTurn for the FE (F7)."""
        turn = ConversationTurn.model_validate(
            {"from": "assistant", "text": question.question, "at": datetime.now(UTC)}
        )
        # by_alias: ConversationTurn.from_ must serialize as "from" on the wire.
        return MsgConversationTurn(
            type="conversationTurn", turn=turn, question=question
        ).model_dump_json(by_alias=True)

    @staticmethod
    def _error(code: str, message: str, where: str | None = None) -> str:
        return MsgError(
            type="error", code=code, message=message, where=where
        ).model_dump_json()
