"""The localhost WebSocket server (F19, ADR-0005).

Binds `127.0.0.1` on a configurable port (v0 is localhost-only — no auth/TLS;
remote exposure is a future Caddy/Tailscale concern, see notes/questions.md).
Each connection gets a `Session`; the server sends `ready` on connect and
relays the session's responses. Geometry binary framing lands with the mesh in
T1b day 3.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable

from websockets.asyncio.server import ServerConnection, serve

from touch_backend.config import Config
from touch_backend.llm_client import make_client
from touch_backend.llm_client.base import LLMClient
from touch_backend.session import Session


class Server:
    """Owns the WS endpoint and per-connection session lifecycle."""

    def __init__(
        self,
        config: Config,
        *,
        client_factory: Callable[[], LLMClient] | None = None,
    ) -> None:
        self._config = config
        self._client_factory = client_factory or (lambda: make_client(config.llm_mode))

    async def _handle(self, connection: ServerConnection) -> None:
        session = Session(self._client_factory, project_dir=self._config.out_root)
        await connection.send(session.ready())
        if self._config.demo_mesh:
            try:
                for response in session.demo_mesh():
                    await connection.send(response)
            except Exception as exc:  # dev affordance: never kill the connection
                print(f"demo_mesh failed: {exc!r}", file=sys.stderr)
        async for raw in connection:
            for response in session.handle(raw):
                await connection.send(response)

    async def start(self):
        """Start serving and return the running server (caller owns lifecycle).

        Use `config.ws_port = 0` to bind an ephemeral port (tests read it back
        via `server.sockets[0].getsockname()[1]`).
        """
        return await serve(self._handle, self._config.ws_host, self._config.ws_port)

    def run(self) -> None:
        """Blocking entry point: serve until interrupted."""

        async def _main() -> None:
            server = await self.start()
            host, port = self._config.ws_host, self._config.ws_port
            print(f"touch_backend WS server on ws://{host}:{port}", file=sys.stderr)
            await server.serve_forever()

        asyncio.run(_main())
