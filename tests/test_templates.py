"""Day 4 — recognised templates: classify a layer's source (F40, ADR-0012)."""

from __future__ import annotations

import pytest

from touch_backend.layer_stack import Layer
from touch_backend.templates import Recognized, recognize

# (template, params) covering every recognised v0 shape + variant.
_SAMPLES = [
    ("box", {"length": 20.0, "width": 10.0, "height": 5.0}),
    ("box", {"length": 20.0, "width": 10.0, "height": 5.0, "centered": True}),
    ("cylinder", {"radius": 3.0, "height": 8.0}),
    ("cylinder", {"radius": 3.0, "height": 8.0, "axis": "x"}),
    ("cylinder", {"radius": 3.0, "height": 8.0, "axis": "y"}),
    ("sphere", {"radius": 4.0}),
    ("chamfer", {"distance": 1.5}),
]


@pytest.mark.parametrize(("template", "params"), _SAMPLES)
def test_recognises_emitted_templates_and_round_trips(template, params):
    layer = Layer.from_template(template, params, id="L")

    recognized = recognize(layer.source)
    assert recognized is not None
    assert recognized.template == template
    assert recognized.params == params

    # Feeding the extracted params back reproduces the source byte-for-byte.
    reemitted = Layer.from_template(recognized.template, recognized.params, id="L")
    assert reemitted.source == layer.source


def test_centered_and_plain_box_are_distinguished():
    plain = recognize("body = Box(1.0, 2.0, 3.0)")
    centered = recognize(
        "body = Box(1.0, 2.0, 3.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))"
    )
    assert plain == Recognized("box", {"length": 1.0, "width": 2.0, "height": 3.0})
    assert centered is not None and centered.params.get("centered") is True


def test_freeform_code_is_not_recognized():
    assert recognize("inner = Cylinder(3.0, 50.0)\nbody = body - inner") is None
    assert recognize("body = body.rotate(Axis.Z, 45)") is None


@pytest.mark.parametrize(
    "source",
    [
        "body = Box(1.0, 2.0)",  # too few args
        "result = Box(1.0, 2.0, 3.0)",  # wrong variable
        "body = Box(1.0, 2.0, 3.0)  # comment",  # trailing junk
        "body = chamfer(body.faces(), 1.0)",  # not the chamfer-edges shape
        "",  # empty
    ],
)
def test_malformed_or_near_miss_is_not_recognized(source):
    assert recognize(source) is None
