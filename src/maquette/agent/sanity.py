"""F6 dimension sanity check (see ADR 0002).

Pure module: extracts numeric dimensions from a natural-language prompt via
regex, compares them against the values in an ``Intent`` (parameters +
feature/modifier params), and reports any prompt-extracted dimension that
fails to match any Intent value within ±1% or ±0.5 mm (whichever is larger).

The sanity check is a *visibility signal*, not a hard gate: the loop logs
warnings and continues. See ADR 0002 § Decision.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from maquette.intent import Intent, Unit

_UNIT_TO_MM: dict[str, float] = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
}

_DELIMITED_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[×xX]\s*(\d+(?:\.\d+)?)"
    r"(?:\s*[×xX]\s*(\d+(?:\.\d+)?))?"
    r"\s*(mm|cm|m|in)\b"
)
_SINGLE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(mm|cm|m|in)\b")


@dataclass(frozen=True)
class Dimension:
    value: float
    unit: Unit
    raw: str

    @property
    def value_mm(self) -> float:
        return self.value * _UNIT_TO_MM[self.unit]


@dataclass(frozen=True)
class DimensionMismatch:
    source: str
    expected: float
    found: float | None
    message: str


@dataclass(frozen=True)
class SanityResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    mismatches: list[DimensionMismatch] = field(default_factory=list)


def check(prompt: str, intent: Intent) -> SanityResult:
    """Compare prompt dimensions against Intent values.

    Returns ``SanityResult(ok=True, ...)`` when every dimension found in
    the prompt has a matching value somewhere in ``intent`` within the
    tolerance defined by ADR 0002. Empty prompts and empty intents both
    yield ``ok=True``.
    """
    extracted = _extract_dimensions(prompt)
    if not extracted:
        return SanityResult(ok=True, warnings=[], mismatches=[])

    intent_values_mm = _collect_intent_values_mm(intent)
    if not intent_values_mm:
        return SanityResult(ok=True, warnings=[], mismatches=[])

    mismatches: list[DimensionMismatch] = []
    for dim in extracted:
        expected_mm = dim.value_mm
        nearest = _nearest(expected_mm, intent_values_mm)
        if not _within_tolerance(expected_mm, nearest):
            mismatches.append(
                DimensionMismatch(
                    source=dim.raw,
                    expected=expected_mm,
                    found=nearest,
                    message=(
                        f"prompt mentions {dim.raw} (={expected_mm:g} mm) but "
                        f"no Intent value matches within tolerance "
                        f"(nearest: {nearest:g} mm)"
                    ),
                )
            )

    warnings = [m.message for m in mismatches]
    return SanityResult(ok=not mismatches, warnings=warnings, mismatches=mismatches)


def _extract_dimensions(prompt: str) -> list[Dimension]:
    dims: list[Dimension] = []
    consumed: list[tuple[int, int]] = []

    for m in _DELIMITED_RE.finditer(prompt):
        unit = m.group(4)
        for grp_idx in (1, 2, 3):
            v = m.group(grp_idx)
            if v is None:
                continue
            dims.append(
                Dimension(
                    value=float(v),
                    unit=unit,  # type: ignore[arg-type]
                    raw=f"{v} {unit}",
                )
            )
        consumed.append((m.start(), m.end()))

    for m in _SINGLE_RE.finditer(prompt):
        if any(start <= m.start() < end for start, end in consumed):
            continue
        unit = m.group(2)
        dims.append(
            Dimension(
                value=float(m.group(1)),
                unit=unit,  # type: ignore[arg-type]
                raw=m.group(0),
            )
        )

    return dims


def _collect_intent_values_mm(intent: Intent) -> list[float]:
    values: list[float] = []
    for p in intent.parameters:
        values.append(p.value * _UNIT_TO_MM[p.unit])
    for f in intent.features:
        for v in f.params.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                values.append(float(v))
    for mod in intent.modifiers:
        for v in mod.params.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                values.append(float(v))
    return values


def _nearest(target: float, values: list[float]) -> float | None:
    if not values:
        return None
    return min(values, key=lambda v: abs(v - target))


def _within_tolerance(expected_mm: float, found_mm: float | None) -> bool:
    if found_mm is None:
        return False
    tol = max(0.01 * abs(expected_mm), 0.5)
    return abs(found_mm - expected_mm) <= tol
