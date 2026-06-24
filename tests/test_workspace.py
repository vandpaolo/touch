"""Workspace folder ops (T4 W1, ADR-0010): openFolder / listDir / part CRUD,
path-contained. Drives the Session directly via handle(json). File-op tests are
fast; openPart replays history through the executor (real OCP)."""

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


def _box_op() -> Operation:
    return Operation.model_validate(
        {
            "id": "b1",
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


def test_open_folder_lists_root_dirs_first(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "b.touch").write_text("{}")
    (tmp_path / "a.touch").write_text("{}")
    s = _session(tmp_path)

    [dir_msg] = _send(s, {"type": "openFolder", "path": str(tmp_path)})
    assert dir_msg["type"] == "dir"
    assert dir_msg["path"] == ""
    names = [(e["name"], e["is_dir"]) for e in dir_msg["entries"]]
    assert names == [("sub", True), ("a.touch", False), ("b.touch", False)]


def test_list_dir_lazy_subdir(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "p.touch").write_text("{}")
    s = _session(tmp_path)
    _send(s, {"type": "openFolder", "path": str(tmp_path)})

    [dir_msg] = _send(s, {"type": "listDir", "path": "sub"})
    assert [e["name"] for e in dir_msg["entries"]] == ["p.touch"]


def test_no_workspace_open_errors(tmp_path):
    [err] = _send(_session(tmp_path), {"type": "listDir", "path": ""})
    assert err["type"] == "error" and err["code"] == "invalid_path"


def test_new_part_creates_and_opens(tmp_path):
    s = _session(tmp_path)
    _send(s, {"type": "openFolder", "path": str(tmp_path)})
    msgs = _send(s, {"type": "newPart", "path": "widget.touch"})

    assert (tmp_path / "widget.touch").exists()
    assert _of_type(msgs, "document")["history"] == []
    assert any(e["name"] == "widget.touch" for e in _of_type(msgs, "dir")["entries"])


def test_save_then_open_round_trip(tmp_path):
    s = _session(tmp_path)
    _send(s, {"type": "openFolder", "path": str(tmp_path)})
    s._append_op(_box_op())  # pretend we modelled a cube
    _send(s, {"type": "savePart", "path": "cube.touch"})
    assert (tmp_path / "cube.touch").exists()

    _send(s, {"type": "newDoc"})  # clear the session
    msgs = _send(s, {"type": "openPart", "path": "cube.touch"})
    snap = _of_type(msgs, "document")
    assert len(snap["history"]) == 1 and snap["history"][0]["kind"] == "box"
    assert any(m["type"] == "meshFrame" for m in msgs)  # replayed to geometry


def test_rename_part(tmp_path):
    s = _session(tmp_path)
    _send(s, {"type": "openFolder", "path": str(tmp_path)})
    _send(s, {"type": "newPart", "path": "old.touch"})
    [dir_msg] = _send(
        s, {"type": "renamePart", "path": "old.touch", "to_path": "new.touch"}
    )
    names = [e["name"] for e in dir_msg["entries"]]
    assert "new.touch" in names and "old.touch" not in names


def test_remove_part(tmp_path):
    s = _session(tmp_path)
    _send(s, {"type": "openFolder", "path": str(tmp_path)})
    _send(s, {"type": "newPart", "path": "doomed.touch"})
    [dir_msg] = _send(s, {"type": "removePart", "path": "doomed.touch"})
    assert all(e["name"] != "doomed.touch" for e in dir_msg["entries"])


def test_path_traversal_rejected(tmp_path):
    s = _session(tmp_path)
    _send(s, {"type": "openFolder", "path": str(tmp_path)})
    [err] = _send(s, {"type": "openPart", "path": "../escape.touch"})
    assert err["type"] == "error" and err["code"] == "invalid_path"
    [err2] = _send(s, {"type": "savePart", "path": "/etc/evil.touch"})
    assert err2["type"] == "error" and err2["code"] == "invalid_path"
