"""T1b day-2 integration tests: the WS server sends `ready` on connect and
turns bad input into structured errors (F21), never a traceback.
"""

from __future__ import annotations

import asyncio
import json

from websockets.asyncio.client import connect

from touch_backend.config import Config
from touch_backend.server import Server


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


def test_valid_but_unwired_plan_is_not_implemented():
    payload = json.dumps({"type": "plan", "prompt_text": "a box", "selection": None})
    _, err = asyncio.run(_roundtrip([payload]))
    assert err["type"] == "error"
    assert err["code"] == "not_implemented"
    assert err["where"] == "plan"


def test_errors_never_leak_a_traceback():
    _, err = asyncio.run(_roundtrip(["{ not json"]))
    blob = json.dumps(err)
    assert "Traceback" not in blob
    assert ".py" not in blob
    assert 'File "' not in blob
