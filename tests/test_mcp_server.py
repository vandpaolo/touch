"""Day 5 — the MCP read tools forward to the live backend over WS (F41, ADR-0014).

The full read drive (get_model_state / list_layers / get_layer / get_selection /
render_view) runs in a **clean subprocess**: render_view rasterises in-process on
the backend, and the pytest interpreter is OCP-poisoned by other suites (the
OSMesa GL conflict — auto-memory `render-backend`), which would blank the frame.
A fresh interpreter is order-independent and mirrors production (the backend is a
clean process). The subprocess writes the read-tool results as JSON + the render
PNG; the parent asserts on both. The structured-error path needs no render, so it
runs in-process.
"""

from __future__ import annotations

import asyncio
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from touch_backend import mcp_server
from touch_backend._generated.protocol import Operation
from touch_backend.config import Config
from touch_backend.mcp_server import Backend, BackendError
from touch_backend.server import Server

_PNG_SIG = b"\x89PNG\r\n\x1a\n"

# Start a real WS server (shared doc seeded with one box layer), point the
# mcp_server backend client at it, drive every read tool, and write the results
# (JSON) + the render (PNG) to argv[1]/argv[2]. Runs in a clean interpreter so
# the in-process backend render is not blanked by suite-wide OCP poisoning.
_DRIVE_SCRIPT = """
import asyncio, json, sys
from pathlib import Path

from touch_backend import mcp_server
from touch_backend._generated.protocol import Operation
from touch_backend.config import Config
from touch_backend.mcp_server import Backend
from touch_backend.server import Server

BOX = Operation.model_validate({
    "id": "box1", "kind": "box",
    "params": {"length": 40, "width": 40, "height": 40},
    "selection": None, "prompt_text": "a 40 mm cube",
    "conversation": [], "created_at": "2026-06-01T00:00:00Z",
})


async def main(result_path, png_path):
    srv = Server(Config(ws_port=0), client_factory=lambda: None)
    srv._active.append_op(BOX)
    ws_server = await srv.start()
    port = ws_server.sockets[0].getsockname()[1]
    mcp_server._backend = Backend(url=f"ws://127.0.0.1:{port}")
    try:
        state = await mcp_server.get_model_state()
        layers = await mcp_server.list_layers()
        layer = await mcp_server.get_layer(layers[0]["id"])
        selection = await mcp_server.get_selection()
        image = await mcp_server.render_view(size=256)
        Path(png_path).write_bytes(image.data)
        Path(result_path).write_text(json.dumps({
            "revision": state["revision"],
            "n_layers": len(state["layers"]),
            "template": layers[0]["template"],
            "source": layer["source"],
            "selection": selection,
        }))
    finally:
        await mcp_server._backend.close()
        ws_server.close()
        await ws_server.wait_closed()


asyncio.run(main(sys.argv[1], sys.argv[2]))
"""


def test_mcp_read_tools_and_render_drive_the_live_backend(tmp_path: Path):
    result_path = tmp_path / "result.json"
    png_path = tmp_path / "iso.png"
    proc = subprocess.run(
        [sys.executable, "-c", _DRIVE_SCRIPT, str(result_path), str(png_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    result = json.loads(result_path.read_text())
    assert result["revision"] == 1 and result["n_layers"] == 1
    assert result["template"] == "box"
    # get_layer pulls the source the manifest omits (N15); a box emits Box(...).
    assert "Box(" in result["source"]
    # No FE selection report yet (Day 9) → the read tool returns null cleanly.
    assert result["selection"] is None

    # render_view → a non-blank PNG thumbnail over the wire.
    png = png_path.read_bytes()
    assert png[:8] == _PNG_SIG
    image = Image.open(io.BytesIO(png)).convert("RGB")
    assert image.size == (256, 256)
    colours = image.getcolors(maxcolors=1 << 24)
    assert colours is not None and len(colours) > 1, "blank render over the wire"


def _box_op() -> Operation:
    return Operation.model_validate(
        {
            "id": "box1",
            "kind": "box",
            "params": {"length": 40, "width": 40, "height": 40},
            "selection": None,
            "prompt_text": "a 40 mm cube",
            "conversation": [],
            "created_at": "2026-06-01T00:00:00Z",
        }
    )


def test_get_layer_unknown_id_is_a_structured_backend_error():
    """A bad id surfaces as a structured BackendError (F21) — no render needed,
    so this runs in-process."""

    async def scenario():
        srv = Server(Config(ws_port=0), client_factory=lambda: None)
        srv._active.append_op(_box_op())
        ws_server = await srv.start()
        port = ws_server.sockets[0].getsockname()[1]
        mcp_server._backend = Backend(url=f"ws://127.0.0.1:{port}")
        try:
            with pytest.raises(BackendError) as exc:
                await mcp_server.get_layer("no-such-layer")
            return exc.value
        finally:
            await mcp_server._backend.close()
            ws_server.close()
            await ws_server.wait_closed()

    error = asyncio.run(scenario())
    assert error.code == "not_found"
    assert error.where == "getLayer"
