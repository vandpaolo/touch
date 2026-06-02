# touch_backend/mesh_cache — content-addressed tessellation cache (ADR-0010).
#
# A rebuild is a pure function of the emitted build123d source, so the source
# hash is a sound content key. Undo / redo / re-open revisit history prefixes
# we have already built; without a cache each pays a fresh OCP subprocess
# rebuild (~2.5 s). Keying on the source turns those into instant lookups.
from __future__ import annotations

import hashlib
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from touch_backend.tessellate import Mesh


class MeshCache:
    """Bounded LRU mapping emitted-source-hash -> tessellated Mesh.

    Owns its own storage; callers hash via `key()`, then `get()` / `put()`.
    The LRU bound keeps a long editing session from growing without limit.
    """

    def __init__(self, capacity: int = 64) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._store: OrderedDict[str, Mesh] = OrderedDict()

    @staticmethod
    def key(code: str) -> str:
        """Content key for a rebuild's emitted source."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Mesh | None:
        mesh = self._store.get(key)
        if mesh is not None:
            self._store.move_to_end(key)
        return mesh

    def put(self, key: str, mesh: Mesh) -> None:
        self._store[key] = mesh
        self._store.move_to_end(key)
        while len(self._store) > self._capacity:
            self._store.popitem(last=False)

    def __len__(self) -> int:
        return len(self._store)
