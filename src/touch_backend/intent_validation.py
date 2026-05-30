from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from touch_backend.intent import (
    Intent,
    Modifier,
    ModifierKind,
    PrimaryFeature,
    PrimaryKind,
)


@dataclass(frozen=True)
class ContractViolation:
    where: str
    kind: str
    field: str | None
    message: str


_NUM: Final = "num"
_STR: Final = "str"

_PRIMARY_REQUIRED: Final[dict[PrimaryKind, dict[str, str]]] = {
    "box": {"length": _NUM, "width": _NUM, "height": _NUM},
    "cylinder": {"radius": _NUM, "height": _NUM},
    "sphere": {"radius": _NUM},
    "extrude": {"profile": _STR, "distance": _NUM},
    "revolve": {"profile": _STR, "axis": _STR, "angle_deg": _NUM},
    "loft": {"sections": _STR},
}

_MODIFIER_REQUIRED: Final[dict[ModifierKind, dict[str, str]]] = {
    "fillet": {"radius": _NUM},
    "chamfer": {"distance": _NUM},
    "shell": {"thickness": _NUM, "open_face": _STR},
    "pattern": {"count": _NUM, "spacing": _NUM, "axis": _STR},
}


def validate_kind_contracts(intent: Intent) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    for f in intent.features:
        violations.extend(_check_feature(f))
    for m in intent.modifiers:
        violations.extend(_check_modifier(m))
    return violations


def _check_feature(f: PrimaryFeature) -> list[ContractViolation]:
    where = f"feature:{f.kind}[{f.id}]"
    spec = _PRIMARY_REQUIRED.get(f.kind)
    if spec is None:
        return [
            ContractViolation(where, f.kind, None, f"unknown primary kind {f.kind!r}")
        ]
    return _check_params(where, f.kind, f.params, spec)


def _check_modifier(m: Modifier) -> list[ContractViolation]:
    where = f"modifier:{m.kind}[{m.id}]"
    if m.kind == "hole":
        return _check_hole(m, where)
    spec = _MODIFIER_REQUIRED.get(m.kind)
    if spec is None:
        return [
            ContractViolation(where, m.kind, None, f"unknown modifier kind {m.kind!r}")
        ]
    return _check_params(where, m.kind, m.params, spec)


def _check_hole(m: Modifier, where: str) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    if "diameter" not in m.params:
        violations.append(
            ContractViolation(
                where, "hole", "diameter", "missing required param 'diameter'"
            )
        )
    else:
        v = m.params["diameter"]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            violations.append(
                ContractViolation(
                    where,
                    "hole",
                    "diameter",
                    f"'diameter' must be numeric, got {type(v).__name__}",
                )
            )
    has_depth = "depth" in m.params
    has_through = m.params.get("through") == "true"
    if not (has_depth or has_through):
        violations.append(
            ContractViolation(
                where,
                "hole",
                None,
                "hole requires either 'depth' or 'through' = \"true\"",
            )
        )
    return violations


def _check_params(
    where: str,
    kind: str,
    params: dict[str, float | str],
    spec: dict[str, str],
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    for name, type_tag in spec.items():
        if name not in params:
            violations.append(
                ContractViolation(where, kind, name, f"missing required param {name!r}")
            )
            continue
        v = params[name]
        if type_tag == _NUM and (
            not isinstance(v, (int, float)) or isinstance(v, bool)
        ):
            violations.append(
                ContractViolation(
                    where,
                    kind,
                    name,
                    f"{name!r} must be numeric, got {type(v).__name__}",
                )
            )
        elif type_tag == _STR and not isinstance(v, str):
            violations.append(
                ContractViolation(
                    where,
                    kind,
                    name,
                    f"{name!r} must be a string, got {type(v).__name__}",
                )
            )
    return violations
