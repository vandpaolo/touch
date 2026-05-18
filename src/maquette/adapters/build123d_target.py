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
    lines = [
        f"# build123d source for Intent: {intent.name}",
        "from build123d import *",
    ]
    if intent.parameters:
        lines.append("")
        lines.append("# parameters (units assumed mm in v0)")
        for p in intent.parameters:
            lines.append(f"{p.name} = {p.value}")
    return "\n".join(lines) + "\n"


def _export(intent: Intent) -> str:
    # Day 4 fills STEP-export emission.
    return "# STEP export will land Day 4\n"


def _extras_block(extras: str) -> str:
    # Day 3 fills verbatim-append behaviour.
    raise NotImplementedError("_extras_block: Day 3")


# ---------- per-kind emitters (placeholders until Days 2-3) ----------------


def _is_truthy_str(value: float | str | None) -> bool:
    return isinstance(value, str) and value.strip().lower() == "true"


_AXIS_MAP = {"x": "Axis.X", "y": "Axis.Y", "z": "Axis.Z"}


def _emit_box(f: PrimaryFeature) -> str:
    p = f.params
    length = float(p["length"])
    width = float(p["width"])
    height = float(p["height"])
    if _is_truthy_str(p.get("centered")):
        return (
            f"{f.id} = Box({length}, {width}, {height}, "
            f"align=(Align.CENTER, Align.CENTER, Align.CENTER))\n"
        )
    return f"{f.id} = Box({length}, {width}, {height})\n"


def _emit_cylinder(f: PrimaryFeature) -> str:
    p = f.params
    radius = float(p["radius"])
    height = float(p["height"])
    # v0: axis param is recorded but build123d Cylinder defaults Z-aligned;
    # non-Z axes are emitted as a rotation kwarg.
    axis = p.get("axis")
    if isinstance(axis, str) and axis.lower() == "x":
        return f"{f.id} = Cylinder({radius}, {height}, rotation=(0, 90, 0))\n"
    if isinstance(axis, str) and axis.lower() == "y":
        return f"{f.id} = Cylinder({radius}, {height}, rotation=(90, 0, 0))\n"
    return f"{f.id} = Cylinder({radius}, {height})\n"


def _emit_sphere(f: PrimaryFeature) -> str:
    radius = float(f.params["radius"])
    return f"{f.id} = Sphere({radius})\n"


def _emit_extrude(f: PrimaryFeature) -> str:
    # v0 doesn't model sketches as first-class entities; the profile name
    # is emitted as a bare identifier the emitted code expects to exist
    # (typically supplied via Intent.extras until schema v2 lands).
    profile = str(f.params["profile"])
    distance = float(f.params["distance"])
    return f"{f.id} = extrude({profile}, {distance})\n"


def _emit_revolve(f: PrimaryFeature) -> str:
    profile = str(f.params["profile"])
    angle = float(f.params["angle_deg"])
    axis_key = str(f.params["axis"]).lower()
    axis_expr = _AXIS_MAP.get(axis_key, "Axis.Z")
    return f"{f.id} = revolve({profile}, {axis_expr}, angle={angle})\n"


def _emit_loft(f: PrimaryFeature) -> str:
    # loft.sections is stored as a comma-separated string of profile names
    # (per phase-0 surprise #4; the contract validator verifies presence
    # only). Parse here; if format becomes ambiguous, file /pm-blocker
    # to widen Intent.PrimaryFeature.params per phase-1.md P1-R5.
    raw = str(f.params["sections"])
    names = [s.strip() for s in raw.split(",") if s.strip()]
    sections = "[" + ", ".join(names) + "]"
    return f"{f.id} = loft({sections})\n"


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
