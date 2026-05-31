"""`python -m touch_backend` — start the WebSocket server.

Loads `.env` (so TOUCH_BACKEND_* + the dev out_root apply), builds Config, and
runs the server until interrupted.
"""

from __future__ import annotations

from dotenv import load_dotenv

from touch_backend.config import Config
from touch_backend.server import Server


def main() -> None:
    load_dotenv()
    Server(Config.load()).run()


if __name__ == "__main__":
    main()
