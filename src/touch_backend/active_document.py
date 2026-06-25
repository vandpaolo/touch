"""The shared active document — the canonical Layer Stack + its lifecycle.

One part open at a time (ADR-0013): the backend holds a single `ActiveDocument`
that the viewport WS and (TP2 sprint 2) the agent over MCP both act on. Every
mutation is compare-and-swap'd on the stack `revision` (N16), the coordination
point a second writer shares.

This is the domain half lifted out of `Session`: the stack, the per-layer fold +
content-addressed cache, layer-native persistence, undo/redo, and the
provenance-baked rebuild (`live_build`). `Session` is the protocol *view* over it
— it owns the wire framing, conversation state, and workspace I/O paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from touch_backend import layer_bridge
from touch_backend.adapters import AdapterRefusal
from touch_backend.layer_stack import Layer, LayerStack
from touch_backend.live_build import GeometryError
from touch_backend.mesh_cache import MeshCache

if TYPE_CHECKING:
    from touch_backend._generated.protocol import Operation
    from touch_backend.tessellate import Mesh

_EXEC_TIMEOUT_S = 30.0


class ActiveDocument:
    """The one shared, canonical Layer Stack + undo/redo + persistence."""

    def __init__(self) -> None:
        self.stack = LayerStack()
        self.name = "untitled"
        self.dirty = False
        # Redo holds undone layers, re-added verbatim on redo (append-only).
        self._redo: list[Layer] = []
        self._mesh_cache = MeshCache()

    # --- read surface ---------------------------------------------------

    @property
    def revision(self) -> int:
        """The stack head revision (the CAS coordination point, ADR-0013)."""
        return self.stack.revision

    @property
    def layers(self) -> list[Layer]:
        return self.stack.layers

    @property
    def can_undo(self) -> bool:
        return len(self.stack.layers) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo) > 0

    # --- mutation (all compare-and-swap on the head) --------------------

    def append_op(self, operation: Operation) -> None:
        """Apply a click-path `Operation` as a new layer (CAS on the head).

        Add-only — the geometry rebuild is the caller's separate step (so it can
        roll back via `rollback_last` on a build failure). Raises `AdapterRefusal`
        on an unsupported op kind before any mutation."""
        layer = layer_bridge.layer_from_operation(operation)
        self.stack.add_layer(layer, expect_rev=self.stack.revision)

    def add_layer(self, layer: Layer) -> int:
        """Append a pre-built `Layer` (the agent/second-writer entry, CAS on the
        head); clears redo + marks dirty. Returns the new revision."""
        rev = self.stack.add_layer(layer, expect_rev=self.stack.revision)
        self._redo = []
        self.dirty = True
        return rev

    def rollback_last(self) -> None:
        """Undo the most recent `append_op`/`add_layer` (a failed build)."""
        self.stack.delete_last(expect_rev=self.stack.revision)

    def clear_redo(self) -> None:
        """A fresh user edit invalidates the redo stack."""
        self._redo = []

    def undo(self) -> None:
        """Append-only undo = delete-last (CAS); stash the layer for redo."""
        self._redo.append(self.stack.delete_last(expect_rev=self.stack.revision))
        self.dirty = True

    def redo(self) -> None:
        """Re-add the most recently undone layer verbatim (CAS)."""
        self.stack.add_layer(self._redo.pop(), expect_rev=self.stack.revision)
        self.dirty = True

    # --- lifecycle ------------------------------------------------------

    def reset(self, *, name: str) -> None:
        """Replace with an empty document (new / new-part)."""
        self.stack = LayerStack()
        self.name = name
        self._redo = []
        self.dirty = False

    def open(self, path: Path) -> None:
        """Load a `.touch` into the stack (layer-native; an old op-history file is
        migrated forward by `load_stack`). Raises on a malformed/unsupported file."""
        self.stack = layer_bridge.load_stack(path)
        self.name = path.stem
        self._redo = []
        self.dirty = False

    def save(self, path: Path) -> None:
        """Write the stack as a layer-native `.touch` (schema 3)."""
        layer_bridge.save_stack(self.stack, path)
        self.dirty = False

    # --- geometry -------------------------------------------------------

    def rebuild_mesh(self) -> Mesh:
        """Fold the stack to a provenance-baked mesh (content-addressed cache in
        front → undo/redo/reopen revisits are free). Raises `AdapterRefusal` /
        `GeometryError` on a build failure."""
        from touch_backend import live_build

        stack = self.stack

        def build(_source: str) -> Mesh:
            return live_build.build_mesh(stack, timeout_s=_EXEC_TIMEOUT_S)

        return stack.rebuild(build=build, cache=self._mesh_cache).mesh


__all__ = ["ActiveDocument", "AdapterRefusal", "GeometryError"]
