"""Recognise known op patterns → editable parametric cards (F40, ADR-0012).

A layer whose source is **exactly** one of Touch's own emitted template shapes
(box / cylinder / sphere / chamfer — the v0 vocabulary) is rendered as an
editable parametric card; everything else is a code card. Recognition is the
inverse of `layer_stack`'s template emitters and is deliberately **dumb** — it
matches the exact byte-shapes `layer_stack` produces (`body = Box(...)`, …), not
arbitrary build123d. The moment it tries to *understand* free code it becomes the
decompiler trap (ADR-0012 carry-forward), so a hand-written or freeform layer
simply doesn't match and stays a code layer.

`recognize` round-trips with `Layer.from_template`: feeding the extracted params
back through the emitter reproduces the original source byte-for-byte.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from touch_backend.layer_stack import Template

# A build123d numeric literal as emitted by `layer_stack._fmt` (repr(float)).
_FLOAT = r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?"


@dataclass(frozen=True)
class Recognized:
    """A matched template + the params extracted from a layer's source."""

    template: Template
    params: dict[str, float | str | bool]


_BOX_CENTERED = re.compile(
    rf"body = Box\(({_FLOAT}), ({_FLOAT}), ({_FLOAT}), "
    r"align=\(Align\.CENTER, Align\.CENTER, Align\.CENTER\)\)"
)
_BOX = re.compile(rf"body = Box\(({_FLOAT}), ({_FLOAT}), ({_FLOAT})\)")
_CYLINDER_X = re.compile(
    rf"body = Cylinder\(({_FLOAT}), ({_FLOAT}), rotation=\(0, 90, 0\)\)"
)
_CYLINDER_Y = re.compile(
    rf"body = Cylinder\(({_FLOAT}), ({_FLOAT}), rotation=\(90, 0, 0\)\)"
)
_CYLINDER = re.compile(rf"body = Cylinder\(({_FLOAT}), ({_FLOAT})\)")
_SPHERE = re.compile(rf"body = Sphere\(({_FLOAT})\)")
_CHAMFER = re.compile(rf"body = chamfer\(body\.edges\(\), ({_FLOAT})\)")


def recognize(source: str) -> Recognized | None:
    """Classify a layer's source: a `Recognized` template+params, or None (code).

    Matches Touch's own emitted forms exactly (full-string); a multi-line or
    differently-formatted block doesn't match and is a code layer.
    """
    text = source.strip()

    match = _BOX_CENTERED.fullmatch(text)
    if match:
        length, width, height = (float(g) for g in match.groups())
        return Recognized(
            "box",
            {"length": length, "width": width, "height": height, "centered": True},
        )

    match = _BOX.fullmatch(text)
    if match:
        length, width, height = (float(g) for g in match.groups())
        return Recognized("box", {"length": length, "width": width, "height": height})

    match = _CYLINDER_X.fullmatch(text)
    if match:
        radius, height = (float(g) for g in match.groups())
        return Recognized("cylinder", {"radius": radius, "height": height, "axis": "x"})

    match = _CYLINDER_Y.fullmatch(text)
    if match:
        radius, height = (float(g) for g in match.groups())
        return Recognized("cylinder", {"radius": radius, "height": height, "axis": "y"})

    match = _CYLINDER.fullmatch(text)
    if match:
        radius, height = (float(g) for g in match.groups())
        return Recognized("cylinder", {"radius": radius, "height": height})

    match = _SPHERE.fullmatch(text)
    if match:
        return Recognized("sphere", {"radius": float(match.group(1))})

    match = _CHAMFER.fullmatch(text)
    if match:
        return Recognized("chamfer", {"distance": float(match.group(1))})

    return None
