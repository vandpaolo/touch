"""MCP server (FastMCP, stdio): the agent-neutral geometry port (F41, ADR-0014).

The user's own Claude Code spawns this as a stdio subprocess; each tool call is
forwarded to the running Touch backend over the WS protocol (a WS client), so the
agent and the viewport act on the **one shared document** (ADR-0013). Read tools
only (Day 5): `get_model_state`, `list_layers`, `get_layer`, `get_selection`,
`render_view`. Mutating tools (CAS `add_layer`/`edit_layer`/`delete_layer` + the
structured envelope) are Day 6.

This process is a thin clean edge: it imports **no** other `touch_backend` module
and no geometry stack — it speaks the wire protocol as raw JSON and relays a
base64 PNG as an MCP `Image`. The backend owns all geometry + rendering. The WS
URL comes from `$TOUCH_MCP_WS_URL` (default `ws://127.0.0.1:8765`).

Correlation: the protocol carries no request id, so a tool sends its request and
reads until the matching response `type` arrives, skipping unsolicited pushes
(change-feed `document`/`meshFrame` broadcasts) and binary frames — harmless for
reads (a skipped `document` push is the same live state).
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP, Image
from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed

_DEFAULT_WS_URL = "ws://127.0.0.1:8765"
_READ_TIMEOUT_S = 35.0  # a renderView blocks on a rebuild; allow headroom


class BackendError(Exception):
    """The backend returned a structured `error` for a forwarded request (F21)."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.code = payload.get("code", "error")
        self.where = payload.get("where")
        super().__init__(payload.get("message", "backend error"))


def _ws_url() -> str:
    return os.environ.get("TOUCH_MCP_WS_URL", _DEFAULT_WS_URL)


@dataclass
class Backend:
    """A reused WS client to the running Touch backend (lazy connect + 1 reconnect)."""

    url: str
    _ws: ClientConnection | None = None

    async def _ensure(self) -> ClientConnection:
        if self._ws is not None:
            return self._ws
        # max_size off: a broadcast mesh binary frame can exceed the 1 MiB default
        # (we skip it, but recv still buffers it).
        self._ws = await ws_connect(self.url, max_size=None)
        return self._ws

    async def request(
        self, payload: dict[str, Any], *, expect: str, timeout: float = _READ_TIMEOUT_S
    ) -> dict[str, Any]:
        """Send `payload`, return the first response whose `type == expect`.

        Reconnects once if the connection dropped (e.g. a backend restart).
        Raises `BackendError` on a structured backend error, `TimeoutError` if no
        matching response arrives in `timeout`.
        """
        try:
            return await self._roundtrip(await self._ensure(), payload, expect, timeout)
        except ConnectionClosed:
            self._ws = None
            return await self._roundtrip(await self._ensure(), payload, expect, timeout)

    async def _roundtrip(
        self,
        ws: ClientConnection,
        payload: dict[str, Any],
        expect: str,
        timeout: float,
    ) -> dict[str, Any]:
        await ws.send(json.dumps(payload))
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"no {expect!r} response within {timeout:g}s")
            message = await asyncio.wait_for(ws.recv(), timeout=remaining)
            if isinstance(message, bytes):
                continue  # a binary mesh frame (greet straggler / broadcast)
            data = json.loads(message)
            kind = data.get("type")
            if kind == expect:
                return data
            if kind == "error":
                raise BackendError(data)
            # else: an unsolicited change-feed push (document/meshFrame) — skip.

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None


mcp = FastMCP("touch")
_backend = Backend(url=_ws_url())


@mcp.tool()
async def get_model_state() -> dict[str, Any]:
    """The current part's state: the layer manifest (ids, kinds, templates,
    params — no source), the stack revision, name, and undo/redo availability."""
    doc = await _backend.request({"type": "getModelState"}, expect="document")
    return {k: v for k, v in doc.items() if k != "type"}


@mcp.tool()
async def list_layers() -> list[dict[str, Any]]:
    """The ordered layers of the current part (id, kind, template, params). The
    build123d source is omitted by design — pull it per layer with get_layer."""
    doc = await _backend.request({"type": "getModelState"}, expect="document")
    return doc.get("layers", [])


@mcp.tool()
async def get_layer(layer_id: str) -> dict[str, Any]:
    """The build123d source of one layer, by its id (from list_layers)."""
    res = await _backend.request(
        {"type": "getLayer", "id": layer_id}, expect="layerSource"
    )
    return {"id": res["id"], "source": res["source"]}


@mcp.tool()
async def get_selection() -> dict[str, Any] | None:
    """The viewport's current selection (target + picked point + finder), or null
    when nothing is selected — the spatial context for a positional edit."""
    res = await _backend.request({"type": "getSelection"}, expect="selectionState")
    return res.get("selection")


@mcp.tool()
async def render_view(size: int | None = None) -> Image:
    """Render the current part to an isometric image so you can see it and
    self-correct. `size` is the optional square edge in px."""
    payload: dict[str, Any] = {"type": "renderView"}
    if size:
        payload["size"] = size
    res = await _backend.request(payload, expect="renderResult")
    return Image(data=base64.b64decode(res["image_base64"]), format="png")


def main() -> None:
    """Entry point: serve the MCP tools over stdio (Claude Code spawns this)."""
    mcp.run()


if __name__ == "__main__":
    main()
