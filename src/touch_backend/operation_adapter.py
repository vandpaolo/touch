"""Operation history -> build123d source (F24, N10, ADR-0004-lineage).

The Touch analogue of Maquette's `adapters.build123d_target`, but driven by the
new `Operation` schema instead of `Intent{features, modifiers}`. Pure +
deterministic: same history -> byte-identical source (no I/O, clock, or random);
all filesystem effects live in the *emitted* code (`export_step(..., part.step)`),
run by the subprocess `Executor`.

v0 scope: the primary param-only kinds (box, cylinder, sphere). Profile primaries
(extrude/revolve/loft) and the modifiers (hole/fillet/chamfer/shell/pattern) need
profile geometry or finder-resolved selections and are refused until a later
phase — `AdapterRefusal`, never a crash.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Any

from touch_backend._generated.protocol import Operation
from touch_backend.adapters import AdapterRefusal


def emit(history: Sequence[Operation]) -> str:
    """Translate an operation history into deterministic build123d source."""
    if not history:
        raise AdapterRefusal(reason="document has no operations", where="export:empty")

    lines = [
        "# build123d source for a Touch document",
        "from build123d import *",
        "from touch_backend.finder import resolve_face",
        "",
    ]
    last_var = ""
    for operation in history:
        var = "op_" + re.sub(r"\W", "_", operation.id)
        lines.append(f"{var} = {rhs(operation, last_var)}")
        last_var = var

    lines.append(f'export_step({last_var}, "part.step")')
    return "\n".join(lines) + "\n"


def rhs(operation: Operation, prev_var: str) -> str:
    """The build123d right-hand side for one operation, threading `prev_var`.

    The per-op core of `emit`, exposed so the Layer Stack bridge
    (`layer_bridge`) can build a layer's source from the same, proven emitters —
    keeping bridged geometry byte-identical to the op-history path. Raises
    `AdapterRefusal` (never crashes) on an unsupported kind.
    """
    emitter = _DISPATCH.get(operation.kind)
    if emitter is None:
        raise AdapterRefusal(
            reason=f"unsupported operation kind {operation.kind!r} (v0 adapter)",
            where=f"op:{operation.kind}",
        )
    return emitter(operation, prev_var)


def _num(operation: Operation, key: str) -> float:
    value = operation.params.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise AdapterRefusal(
            reason=f"{operation.kind} requires numeric param {key!r}",
            where=f"op:{operation.kind}:{key}",
        )
    return float(value)


def _box(operation: Operation, _prev: str) -> str:
    length = _num(operation, "length")
    width = _num(operation, "width")
    height = _num(operation, "height")
    return f"Box({length}, {width}, {height})"


def _cylinder(operation: Operation, _prev: str) -> str:
    return f"Cylinder({_num(operation, 'radius')}, {_num(operation, 'height')})"


def _sphere(operation: Operation, _prev: str) -> str:
    return f"Sphere({_num(operation, 'radius')})"


def _contains_point(selection: Any) -> tuple[tuple[float, float, float], float]:
    """Extract the (point, tol) of the selection's contains_point finder (the
    chamfer target), falling back to the selection's own point."""
    for predicate in selection.finder:
        root = predicate.root
        if getattr(root, "kind", None) == "contains_point":
            return tuple(root.point_xyz.root), float(root.tol_mm)
    return tuple(selection.point_xyz.root), 0.5


def _chamfer(operation: Operation, prev_var: str) -> str:
    if not prev_var:
        raise AdapterRefusal(
            reason="chamfer needs a base solid to modify", where="op:chamfer"
        )
    if operation.selection is None:
        raise AdapterRefusal(
            reason="chamfer requires a selected face", where="op:chamfer"
        )
    length = _num(operation, "length")
    point, tol = _contains_point(operation.selection)
    entity_id = operation.selection.entity_id_at_capture
    # Resolve the clicked face on the prior solid at run time (id-first per
    # ADR-0011; the point is the finder fallback), chamfer its edges.
    return (
        f"chamfer(resolve_face({prev_var}, {entity_id!r}, {point!r}, {tol}).edges(), "
        f"length={length})"
    )


_DISPATCH: dict[str, Callable[[Operation, str], str]] = {
    "box": _box,
    "cylinder": _cylinder,
    "sphere": _sphere,
    "chamfer": _chamfer,
}
