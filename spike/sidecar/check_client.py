"""Day-1 "done when" check: connect, read the mesh frame, assert 6 face tags.

Usage:
    python check_client.py <port>

Exits 0 if the frame decodes to exactly 12 triangles carrying 6 distinct
face tags (the Day-1 exit criterion), non-zero otherwise.
"""

from __future__ import annotations

import asyncio
import sys

from websockets.asyncio.client import connect

from touch_sidecar.wire import decode


async def _run(port: int) -> int:
    async with connect(f"ws://127.0.0.1:{port}") as ws:
        data = await ws.recv()
    if not isinstance(data, bytes):
        print(f"FAIL: expected a binary frame, got {type(data).__name__}")
        return 1

    mesh = decode(data)
    n_tris = len(mesh.triangles)
    distinct = sorted(set(mesh.face_tag_per_triangle))
    print(f"vertices: {len(mesh.vertices)}")
    print(f"triangles: {n_tris}")
    print(f"distinct face tags: {distinct}")

    ok = n_tris == 12 and len(distinct) == 6
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    return asyncio.run(_run(int(sys.argv[1])))


if __name__ == "__main__":
    raise SystemExit(main())
