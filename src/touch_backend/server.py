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

from touch_backend.active_document import ActiveDocument
from touch_backend.config import Config
from touch_backend.llm_client import make_client
from touch_backend.llm_client.base import LLMClient
from touch_backend.session import Session


class Server:
    """Owns the WS endpoint and per-connection session lifecycle.

    The backend holds ONE shared active document (ADR-0013): every connection's
    `Session` is a view onto the same `ActiveDocument`, so the viewport WS and
    (TP2 sprint 2) the agent over MCP act on the same part. When one writer
    mutates the shared document, the change feed pushes the new snapshot + mesh
    to every other connected viewport (revision-stamped) so edits appear live.
    """

    def __init__(
        self,
        config: Config,
        *,
        client_factory: Callable[[], LLMClient] | None = None,
    ) -> None:
        self._config = config
        self._client_factory = client_factory or (lambda: make_client(config.llm_mode))
        self._active = ActiveDocument()
        self._connections: set[ServerConnection] = set()

    async def _handle(self, connection: ServerConnection) -> None:
        session = Session(
            self._client_factory,
            project_dir=self._config.out_root,
            document=self._active,
        )
        self._connections.add(connection)
        try:
            await connection.send(session.ready())
            await self._greet(session, connection)
            async for raw in connection:
                rev_before = self._active.revision
                for response in session.handle(raw):
                    await connection.send(response)
                # Change feed: a mutation on the shared document bumps the
                # revision → push the new state to every OTHER viewport.
                if self._active.revision != rev_before:
                    await self._broadcast(session, exclude=connection)
        finally:
            self._connections.discard(connection)

    async def _greet(self, session: Session, connection: ServerConnection) -> None:
        """Bring a newly-joined viewport up to date: the existing shared part, or
        the dev demo cube seeded once when the document is empty."""
        if self._active.layers:
            for response in session.snapshot_frames():
                await connection.send(response)
        elif self._config.demo_mesh:
            try:
                for response in session.demo_mesh():
                    await connection.send(response)
            except Exception as exc:  # dev affordance: never kill the connection
                print(f"demo_mesh failed: {exc!r}", file=sys.stderr)

    async def _broadcast(self, session: Session, *, exclude: ServerConnection) -> None:
        """Push the current shared-document snapshot + mesh to every connection
        except the one that just mutated it (which already got its responses)."""
        others = [c for c in self._connections if c is not exclude]
        if not others:
            return
        frames = session.snapshot_frames()
        for conn in others:
            try:
                for response in frames:
                    await conn.send(response)
            except Exception:  # a dead peer; its own handler's finally cleans up
                pass

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
