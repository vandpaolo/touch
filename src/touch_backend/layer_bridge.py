"""Bridge the op-history wire model onto the Layer Stack (TP1 Day 6).

TP1 keeps the T0-T5 `Operation` history as the wire + persistence + undo/redo
truth (the FE mirror and `.touch` are op-based), but the live *geometry* document
is now the Layer Stack (ADR-0012/0013). This module derives a `LayerStack` from
an op-history so the rebuild folds through `LayerStack.rebuild` — exercising the
fold, cache, and (later) provenance on the real path — while the geometry stays
byte-identical because each layer's source comes from the same proven
`operation_adapter` emitters, threading the stack's `body` variable.

The stack is a **pure function of the history**, re-derived per rebuild — never
parallel mutable state — so the existing undo/redo/save/open path (which mutates
the op-history directly) stays correct. The Day-5 versioned mutation API
(`add_layer`/`delete_last` + CAS) is for the agent/MCP surface (TP2), not this
single-surface viewport path.

box/cylinder/sphere ops are recognised as parametric template layers (F40); the
finder-scoped chamfer (selection-resolved, not all-edges) stays a code layer.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from touch_backend import operation_adapter, templates
from touch_backend._generated.protocol import Operation
from touch_backend.document import TouchDocument
from touch_backend.layer_stack import LAYER_SCHEMA_VERSION, Layer, LayerStack


def layer_from_operation(operation: Operation) -> Layer:
    """One op → one stack layer (template when recognised, else a code layer)."""
    source = f"body = {operation_adapter.rhs(operation, 'body')}"
    recognized = templates.recognize(source)
    if recognized is not None:
        return Layer.from_template(
            recognized.template,
            recognized.params,
            id=operation.id,
            selection=operation.selection,
        )
    return Layer.from_code(source, id=operation.id, selection=operation.selection)


def layers_from_history(history: Sequence[Operation]) -> LayerStack:
    """Derive the live Layer Stack from an op-history (a pure function of it).

    Raises `AdapterRefusal` (via `operation_adapter`) on an unsupported op kind —
    the same failure the op-history path raised, so callers handle it unchanged.
    """
    return LayerStack(layers=[layer_from_operation(op) for op in history])


def save_stack(stack: LayerStack, path: Path) -> None:
    """Persist a Layer Stack as layer-native `.touch` JSON (Day 7, N7)."""
    path.write_text(json.dumps(stack.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_stack(path: Path) -> LayerStack:
    """Load a `.touch` as a Layer Stack, migrating the op-history format forward.

    A layer-native file (schema >= 3) loads directly; an older op-history file
    (schema <= 2, T0-T5) is migrated by bridging its history to layers — so old
    parts keep opening as stacks (N7). A migrated template op becomes a template
    layer; a migrated finder-scoped chamfer becomes a code layer.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if int(data.get("schema_version", 0)) >= LAYER_SCHEMA_VERSION:
        return LayerStack.from_dict(data)
    return layers_from_history(TouchDocument.load(path).history)
