"""T1b day-2 integration tests: the WS server sends `ready` on connect and
turns bad input into structured errors (F21), never a traceback.
"""

from __future__ import annotations

import asyncio
import json

from websockets.asyncio.client import connect

from touch_backend.config import Config
from touch_backend.llm_client.base import LLMResponse
from touch_backend.server import Server


class _MockClient:
    """A canned LLMClient: returns a JSON box Operation, no network."""

    name = "mock"

    def available(self) -> bool:
        return True

    def complete(
        self, *, system: str, prompt: str, max_tokens: int = 2048
    ) -> LLMResponse:
        operation = {
            "id": "01HZMOCK",
            "kind": "box",
            "params": {"length": 10, "width": 10, "height": 10},
            "selection": None,
            "prompt_text": prompt,
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
        return LLMResponse(text=json.dumps(operation))


async def _roundtrip(payloads: list[str]) -> list[dict]:
    """Start the server on an ephemeral port, connect, send each payload, and
    return [ready, *one response per payload]."""
    server = await Server(Config(ws_port=0)).start()
    port = server.sockets[0].getsockname()[1]
    received: list[dict] = []
    try:
        async with connect(f"ws://127.0.0.1:{port}") as ws:
            received.append(json.loads(await ws.recv()))  # the `ready` envelope
            for payload in payloads:
                await ws.send(payload)
                received.append(json.loads(await ws.recv()))
    finally:
        server.close()
        await server.wait_closed()
    return received


def test_ready_on_connect():
    [ready] = asyncio.run(_roundtrip([]))
    assert ready["type"] == "ready"
    assert ready["schema_version"] == 1


def test_invalid_json_is_structured_error():
    _, err = asyncio.run(_roundtrip(["{ not json"]))
    assert err["type"] == "error"
    assert err["code"] == "invalid_json"


def test_schema_mismatch_is_structured_error():
    # valid JSON, but `plan` is missing the required prompt_text
    _, err = asyncio.run(_roundtrip([json.dumps({"type": "plan"})]))
    assert err["type"] == "error"
    assert err["code"] == "invalid_message"
    assert err["where"] == "plan"


def test_valid_but_unwired_message_is_not_implemented():
    # `plan` is now wired; `cancel` is still a stub.
    _, err = asyncio.run(_roundtrip([json.dumps({"type": "cancel"})]))
    assert err["type"] == "error"
    assert err["code"] == "not_implemented"
    assert err["where"] == "cancel"


def test_errors_never_leak_a_traceback():
    _, err = asyncio.run(_roundtrip(["{ not json"]))
    blob = json.dumps(err)
    assert "Traceback" not in blob
    assert ".py" not in blob
    assert 'File "' not in blob


def test_plan_returns_structured_op_and_face_id_mesh():
    """T1b Min exit criterion: a `plan` (mocked LLM) yields a structured op +
    a tessellated mesh carrying per-face IDs."""
    from touch_backend.frames import unpack

    async def scenario():
        server = await Server(
            Config(ws_port=0), client_factory=lambda: _MockClient()
        ).start()
        port = server.sockets[0].getsockname()[1]
        try:
            async with connect(f"ws://127.0.0.1:{port}") as ws:
                json.loads(await ws.recv())  # ready
                await ws.send(
                    json.dumps(
                        {
                            "type": "plan",
                            "prompt_text": "a 10mm cube",
                            "selection": None,
                        }
                    )
                )
                op_msg = json.loads(await ws.recv())
                frame_msg = json.loads(await ws.recv())
                binary = await ws.recv()
        finally:
            server.close()
            await server.wait_closed()
        return op_msg, frame_msg, binary

    op_msg, frame_msg, binary = asyncio.run(scenario())

    assert op_msg["type"] == "op"
    assert op_msg["operation"]["kind"] == "box"
    assert frame_msg["type"] == "meshFrame"
    assert frame_msg["triangle_count"] == 12
    assert set(frame_msg["face_id_to_finder_hint"]) == {str(i) for i in range(6)}
    assert isinstance(binary, (bytes, bytearray))

    mesh = unpack(
        binary,
        version=frame_msg["version"],
        vertex_count=frame_msg["vertex_count"],
        triangle_count=frame_msg["triangle_count"],
        edge_segment_count=frame_msg["edge_segment_count"],
    )
    assert mesh.face_tag_per_triangle.shape[0] == 12
    assert {int(t) for t in mesh.face_tag_per_triangle} == set(range(6))
