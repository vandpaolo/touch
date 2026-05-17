from __future__ import annotations

from collections.abc import Callable
from typing import Final

from maquette.adapters import Adapter, AdapterRefusal
from maquette.intent import Intent, Modifier, ModifierKind, PrimaryFeature, PrimaryKind


def emit(intent: Intent) -> str:
    """Translate a validated Intent into build123d Python source.

    Pure function: no I/O, no clock, no random, no environment reads.
    All filesystem effects live in the *emitted* code, not in this
    module.
    """
    parts: list[str] = [_preamble(intent)]

    for f in intent.features:
        emitter = _PRIMARY_DISPATCH.get(f.kind)
        if emitter is None:
            raise AdapterRefusal(
                reason=f"unknown PrimaryKind {f.kind!r}",
                where=f"feature:{f.kind}",
            )
        parts.append(emitter(f))

    for m in intent.modifiers:
        modifier_emitter = _MODIFIER_DISPATCH.get(m.kind)
        if modifier_emitter is None:
            raise AdapterRefusal(
                reason=f"unknown ModifierKind {m.kind!r}",
                where=f"modifier:{m.kind}",
            )
        parts.append(modifier_emitter(m))

    if intent.extras:
        parts.append(_extras_block(intent.extras))

    parts.append(_export(intent))
    return "\n".join(parts)


# ---------- preamble / export / extras (filled in Days 2-4) ---------------


def _preamble(intent: Intent) -> str:
    # Day 2 fills imports + parameter declarations.
    return f"# build123d source for Intent: {intent.name}\n"


def _export(intent: Intent) -> str:
    # Day 4 fills STEP-export emission.
    return "# STEP export will land Day 4\n"


def _extras_block(extras: str) -> str:
    # Day 3 fills verbatim-append behaviour.
    raise NotImplementedError("_extras_block: Day 3")


# ---------- per-kind emitters (placeholders until Days 2-3) ----------------


def _emit_box(f: PrimaryFeature) -> str:
    raise NotImplementedError("_emit_box: Day 2")


def _emit_cylinder(f: PrimaryFeature) -> str:
    raise NotImplementedError("_emit_cylinder: Day 2")


def _emit_sphere(f: PrimaryFeature) -> str:
    raise NotImplementedError("_emit_sphere: Day 2")


def _emit_extrude(f: PrimaryFeature) -> str:
    raise NotImplementedError("_emit_extrude: Day 2")


def _emit_revolve(f: PrimaryFeature) -> str:
    raise NotImplementedError("_emit_revolve: Day 2")


def _emit_loft(f: PrimaryFeature) -> str:
    raise NotImplementedError("_emit_loft: Day 2")


def _emit_hole(m: Modifier) -> str:
    raise NotImplementedError("_emit_hole: Day 3")


def _emit_fillet(m: Modifier) -> str:
    raise NotImplementedError("_emit_fillet: Day 3")


def _emit_chamfer(m: Modifier) -> str:
    raise NotImplementedError("_emit_chamfer: Day 3")


def _emit_shell(m: Modifier) -> str:
    raise NotImplementedError("_emit_shell: Day 3")


def _emit_pattern(m: Modifier) -> str:
    raise NotImplementedError("_emit_pattern: Day 3")


_PRIMARY_DISPATCH: Final[dict[PrimaryKind, Callable[[PrimaryFeature], str]]] = {
    "box": _emit_box,
    "cylinder": _emit_cylinder,
    "sphere": _emit_sphere,
    "extrude": _emit_extrude,
    "revolve": _emit_revolve,
    "loft": _emit_loft,
}

_MODIFIER_DISPATCH: Final[dict[ModifierKind, Callable[[Modifier], str]]] = {
    "hole": _emit_hole,
    "fillet": _emit_fillet,
    "chamfer": _emit_chamfer,
    "shell": _emit_shell,
    "pattern": _emit_pattern,
}


# Static conformance check (pyright verifies this assignment is well-typed).
_: Adapter = emit
