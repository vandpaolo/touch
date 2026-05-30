"""WebSocket server for the T0 spike.

Binds an OS-assigned ephemeral port on 127.0.0.1 (R4: no fixed-port
assumption), prints ``TOUCH_READY <port>`` to stdout once listening (R3: the
Electron main process parses this sentinel before opening the renderer
window), and emits a single binary mesh frame to each client on connect.
"""

from __future__ import annotations

import asyncio

import websockets
from websockets.asyncio.server import ServerConnection, serve

from . import cube
from .ocp_check import ocp_selfcheck
from .wire import Mesh, encode

_FRAME: bytes = encode(
    Mesh(
        vertices=cube.VERTICES,
        normals=cube.NORMALS,
        triangles=cube.TRIANGLES,
        face_tag_per_triangle=cube.FACE_TAG_PER_TRIANGLE,
    )
)


async def _handler(websocket: ServerConnection) -> None:
    # The spike emits the mesh once on connect, then idles. No request
    # protocol yet — that lands in T1b.
    await websocket.send(_FRAME)
    try:
        await websocket.wait_closed()
    except websockets.ConnectionClosed:
        pass


async def serve_forever() -> None:
    # R1: prove OCP's native libs are present and loadable *before* announcing
    # ready. In the PyInstaller bundle this is the line that fails loudly if
    # the OCCT shared libs were not collected.
    print(f"OCP_SELFCHECK {ocp_selfcheck()}", flush=True)

    async with serve(_handler, "127.0.0.1", 0) as server:
        sock = next(iter(server.sockets))
        port = sock.getsockname()[1]
        # Sentinel MUST be the first thing on stdout and flushed immediately.
        print(f"TOUCH_READY {port}", flush=True)
        await asyncio.get_running_loop().create_future()  # run forever


def main() -> None:
    try:
        asyncio.run(serve_forever())
    except KeyboardInterrupt:
        pass
