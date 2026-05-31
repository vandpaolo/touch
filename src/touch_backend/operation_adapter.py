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

from touch_backend._generated.protocol import Operation
from touch_backend.adapters import AdapterRefusal


def emit(history: Sequence[Operation]) -> str:
    """Translate an operation history into deterministic build123d source."""
    if not history:
        raise AdapterRefusal(reason="document has no operations", where="export:empty")

    lines = ["# build123d source for a Touch document", "from build123d import *", ""]
    last_var = ""
    for operation in history:
        emitter = _DISPATCH.get(operation.kind)
        if emitter is None:
            raise AdapterRefusal(
                reason=f"unsupported operation kind {operation.kind!r} (v0 adapter)",
                where=f"op:{operation.kind}",
            )
        var = "op_" + re.sub(r"\W", "_", operation.id)
        lines.append(f"{var} = {emitter(operation)}")
        last_var = var

    lines.append(f'export_step({last_var}, "part.step")')
    return "\n".join(lines) + "\n"


def _num(operation: Operation, key: str) -> float:
    value = operation.params.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise AdapterRefusal(
            reason=f"{operation.kind} requires numeric param {key!r}",
            where=f"op:{operation.kind}:{key}",
        )
    return float(value)


def _box(operation: Operation) -> str:
    length = _num(operation, "length")
    width = _num(operation, "width")
    height = _num(operation, "height")
    return f"Box({length}, {width}, {height})"


def _cylinder(operation: Operation) -> str:
    return f"Cylinder({_num(operation, 'radius')}, {_num(operation, 'height')})"


def _sphere(operation: Operation) -> str:
    return f"Sphere({_num(operation, 'radius')})"


_DISPATCH: dict[str, Callable[[Operation], str]] = {
    "box": _box,
    "cylinder": _cylinder,
    "sphere": _sphere,
}
