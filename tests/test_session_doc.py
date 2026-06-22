"""Session document lifecycle + undo/redo (T4, F9/F10). Drives the Session
directly via handle(json). Most tests are pure protocol/file I/O; the open/redo
tests replay history through the executor (real OCP) — build123d is imported
lazily inside the session, safe under collection."""

from __future__ import annotations

import json

from touch_backend._generated.protocol import Operation
from touch_backend.llm_client.base import LLMResponse
from touch_backend.session import Session


class _MockClient:
    name = "mock"

    def available(self) -> bool:
        return True

    def complete(
        self, *, system: str, prompt: str, max_tokens: int = 2048
    ) -> LLMResponse:
        return LLMResponse(
            text=json.dumps(
                {"kind": "box", "params": {"length": 40, "width": 40, "height": 40}}
            )
        )


def _session(tmp_path) -> Session:
    return Session(lambda: _MockClient(), project_dir=tmp_path)


def _box_op(op_id: str = "b1") -> Operation:
    return Operation.model_validate(
        {
            "id": op_id,
            "kind": "box",
            "params": {"length": 40, "width": 40, "height": 40},
            "selection": None,
            "prompt_text": "a 40 mm cube",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )


def _send(session: Session, payload: dict) -> list[dict]:
    return [
        json.loads(r) for r in session.handle(json.dumps(payload)) if isinstance(r, str)
    ]


def _of_type(msgs: list[dict], t: str) -> dict:
    return next(m for m in msgs if m["type"] == t)


# --- fast (no OCP) ----------------------------------------------------------


def test_new_doc_emits_empty_snapshot(tmp_path):
    s = _session(tmp_path)
    s.document.append(_box_op())
    msgs = _send(s, {"type": "newDoc"})
    snap = _of_type(msgs, "document")
    assert snap["history"] == []
    assert snap["dirty"] is False
    assert snap["can_undo"] is False


def test_list_files_empty(tmp_path):
    [fl] = _send(_session(tmp_path), {"type": "listFiles"})
    assert fl == {"type": "fileList", "files": []}


def test_save_then_list_shows_file(tmp_path):
    s = _session(tmp_path)
    s.document.append(_box_op())
    msgs = _send(s, {"type": "save", "name": "mypart"})

    assert (tmp_path / "mypart.touch").exists()
    assert _of_type(msgs, "document")["dirty"] is False
    assert _of_type(msgs, "fileList")["files"] == ["mypart"]


def test_save_rejects_path_traversal(tmp_path):
    s = _session(tmp_path)
    s.document.append(_box_op())
    [err] = _send(s, {"type": "save", "name": "../escape"})
    assert err["type"] == "error"
    assert err["code"] == "invalid_path"
    assert not (tmp_path.parent / "escape.touch").exists()


def test_open_missing_file_errors(tmp_path):
    [err] = _send(_session(tmp_path), {"type": "open", "name": "nope"})
    assert err["type"] == "error"
    assert err["code"] == "not_found"


def test_undo_to_empty_then_redo_state(tmp_path):
    s = _session(tmp_path)
    s.document.append(_box_op())
    # undo the only op → empty doc, snapshot only (no mesh to render)
    msgs = _send(s, {"type": "undo"})
    snap = _of_type(msgs, "document")
    assert snap["history"] == []
    assert snap["can_redo"] is True


def test_redo_when_empty_errors(tmp_path):
    [err] = _send(_session(tmp_path), {"type": "redo"})
    assert err["type"] == "error"
    assert err["code"] == "nothing_to_redo"


# --- replay through the executor (real OCP) ---------------------------------


def test_save_then_open_round_trip_rebuilds(tmp_path):
    s = _session(tmp_path)
    s.document.append(_box_op())
    _send(s, {"type": "save", "name": "cube"})
    _send(s, {"type": "newDoc"})  # clear

    msgs = _send(s, {"type": "open", "name": "cube"})
    snap = _of_type(msgs, "document")
    assert snap["name"] == "cube"
    assert len(snap["history"]) == 1
    assert snap["history"][0]["kind"] == "box"
    # open replays history → a mesh frame is emitted (string envelope present)
    assert any(m["type"] == "meshFrame" for m in msgs)


def test_redo_rebuilds_geometry(tmp_path):
    s = _session(tmp_path)
    s.document.append(_box_op())
    _send(s, {"type": "undo"})  # → empty
    msgs = _send(s, {"type": "redo"})  # → box again, rebuilt
    assert len(_of_type(msgs, "document")["history"]) == 1
    assert any(m["type"] == "meshFrame" for m in msgs)


# --- clarification branch (F7, T5 D5) ----------------------------------------


class _ClarifyClient:
    """Returns a chamfer with no length → the planner must ask, not guess."""

    name = "mock"

    def available(self) -> bool:
        return True

    def complete(self, *, system: str, prompt: str, max_tokens: int = 2048):
        return LLMResponse(text=json.dumps({"kind": "chamfer", "params": {}}))


def test_underspecified_plan_emits_conversation_turn(tmp_path):
    s = Session(lambda: _ClarifyClient(), project_dir=tmp_path)
    msgs = _send(s, {"type": "plan", "prompt_text": "chamfer this", "selection": None})

    turn = _of_type(msgs, "conversationTurn")
    assert turn["turn"]["from"] == "assistant"
    assert "length" in turn["turn"]["text"].lower()
    assert turn["question"]["question"]  # the structured ClarifyingQuestion
    # nothing applied — no op, no mesh.
    assert s.document.history == []
    assert not any(m["type"] in ("op", "meshFrame") for m in msgs)


_FACE_SEL = {
    "target": "face",
    "point_xyz": [0, 0, 20],
    "finder": [{"kind": "contains_point", "point_xyz": [0, 0, 20], "tol_mm": 0.5}],
    "entity_id_at_capture": 0,
}


def _user_reply(text: str) -> dict:
    return {
        "type": "conversationTurn",
        "turn": {"from": "user", "text": text, "at": "2026-06-03T00:00:00Z"},
    }


class _AskThenAnswerClient:
    """First call asks (chamfer, no length); the reply resolves it (length 5)."""

    name = "mock"

    def __init__(self) -> None:
        self.calls = 0

    def available(self) -> bool:
        return True

    def complete(self, *, system: str, prompt: str, max_tokens: int = 2048):
        self.calls += 1
        params = {} if self.calls == 1 else {"length": 5}
        return LLMResponse(text=json.dumps({"kind": "chamfer", "params": params}))


def test_clarify_then_reply_applies_op_and_records_thread(tmp_path):
    s = Session(lambda: _AskThenAnswerClient(), project_dir=tmp_path)
    s.document.append(_box_op())  # a base solid to chamfer

    asked = _send(s, {"type": "plan", "prompt_text": "chamfer", "selection": _FACE_SEL})
    assert _of_type(asked, "conversationTurn")  # it asked

    msgs = _send(s, _user_reply("5 mm"))  # the reply resolves it
    op = _of_type(msgs, "op")["operation"]
    assert op["kind"] == "chamfer"
    assert op["params"] == {"length": 5}
    # the clarification thread is recorded on the op (F7).
    froms = [t["from"] for t in op["conversation"]]
    assert "assistant" in froms and "user" in froms
    assert any(m["type"] == "meshFrame" for m in msgs)
    assert len(s.document.history) == 2  # box + chamfer


def test_clarify_caps_at_max_turns(tmp_path):
    s = Session(lambda: _ClarifyClient(), project_dir=tmp_path)  # always asks
    s.document.append(_box_op())
    _send(s, {"type": "plan", "prompt_text": "chamfer", "selection": _FACE_SEL})  # a=1
    _send(s, _user_reply("uh"))  # a=2, asks
    _send(s, _user_reply("um"))  # a=3, asks
    msgs = _send(s, _user_reply("er"))  # a=4 > 3 → exhausted

    assert _of_type(msgs, "error")["code"] == "clarify_exhausted"


def test_reply_without_a_conversation_errors(tmp_path):
    msgs = _send(_session(tmp_path), _user_reply("hello?"))
    assert _of_type(msgs, "error")["code"] == "no_conversation"


def test_open_layer_native_file_returns_structured_error(tmp_path):
    """H2: opening a layer-native (schema 3) part via the op-history session path
    must surface a structured error, not crash or silently load an empty doc."""
    s = _session(tmp_path)
    (tmp_path / "stack.touch").write_text(
        '{"schema_version": 3, "revision": 0, "layers": []}', encoding="utf-8"
    )
    [err] = _send(s, {"type": "open", "name": "stack"})
    assert err["type"] == "error"
    assert err["code"] == "open_failed"
