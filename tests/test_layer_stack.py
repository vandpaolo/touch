"""Day 1 — the Layer Stack model + deterministic emission (ADR-0012, F38).

Covers the `Layer`/`LayerStack` model, `emit` shape + byte-for-byte determinism,
and one real build123d subprocess run proving the emitted script is runnable.
"""

from __future__ import annotations

import pytest

from touch_backend.agent.executor import Executor
from touch_backend.layer_stack import (
    Layer,
    LayerStack,
    LayerStackError,
    emit,
)

# A multi-line freeform code layer: proves verbatim inlining + module-scope
# threading of `body` (a through-hole drilled into the previous solid).
_CODE_LAYER = "inner = Cylinder(3.0, 50.0)\nbody = body - inner"


def _box_code_stack() -> LayerStack:
    return LayerStack(
        layers=[
            Layer.from_template(
                "box",
                {"length": 20, "width": 20, "height": 20, "centered": True},
                id="L0",
            ),
            Layer.from_code(_CODE_LAYER, id="L1"),
        ]
    )


# ---------- model ---------------------------------------------------------


def test_template_layer_generates_source_and_keeps_params():
    layer = Layer.from_template("box", {"length": 10, "width": 2, "height": 3}, id="L0")
    assert layer.kind == "template"
    assert layer.template == "box"
    assert layer.params == {"length": 10, "width": 2, "height": 3}
    assert layer.source == "body = Box(10.0, 2.0, 3.0)"
    assert layer.input_hash is None and layer.output_hash is None


def test_code_layer_preserves_source_verbatim():
    layer = Layer.from_code(_CODE_LAYER, id="L1")
    assert layer.kind == "code"
    assert layer.source == _CODE_LAYER
    assert layer.template is None
    assert layer.params == {}


def test_empty_code_layer_rejected():
    with pytest.raises(LayerStackError, match="empty source"):
        Layer.from_code("   \n  ", id="bad")


def test_unknown_template_rejected():
    with pytest.raises(LayerStackError, match="unknown template"):
        Layer.from_template("torus", {}, id="bad")  # type: ignore[arg-type]


def test_missing_template_param_rejected():
    with pytest.raises(LayerStackError, match="missing required param"):
        Layer.from_template("box", {"length": 1}, id="bad")


def test_stack_defaults_to_revision_zero():
    assert LayerStack().revision == 0
    assert LayerStack().layers == []


# ---------- emit ----------------------------------------------------------


def test_emit_threads_body_and_exports():
    source = emit(_box_code_stack())
    assert source.startswith("from build123d import *\n")
    assert "body = Box(20.0, 20.0, 20.0, align=(Align.CENTER" in source
    assert _CODE_LAYER in source  # code layer inlined verbatim
    assert source.rstrip().endswith('export_step(body, "part.step")')


def test_emit_full_script_is_exactly_shaped():
    source = emit(_box_code_stack())
    expected = (
        "from build123d import *\n"
        "\n"
        "# layer L0 (template:box)\n"
        "body = Box(20.0, 20.0, 20.0, "
        "align=(Align.CENTER, Align.CENTER, Align.CENTER))\n"
        "\n"
        "# layer L1 (code)\n"
        "inner = Cylinder(3.0, 50.0)\n"
        "body = body - inner\n"
        "\n"
        'export_step(body, "part.step")\n'
    )
    assert source == expected


def test_emit_is_deterministic_byte_identical():
    stack = _box_code_stack()
    assert emit(stack) == emit(stack)
    # an independently constructed equivalent stack emits identically
    assert emit(stack) == emit(_box_code_stack())


def test_emit_chamfer_template_is_all_edges():
    stack = LayerStack(
        layers=[
            Layer.from_template(
                "box", {"length": 30, "width": 30, "height": 30}, id="L0"
            ),
            Layer.from_template("chamfer", {"distance": 1.5}, id="L1"),
        ]
    )
    source = emit(stack)
    assert "body = chamfer(body.edges(), 1.5)" in source


def test_emit_empty_stack_rejected():
    with pytest.raises(LayerStackError, match="empty stack"):
        emit(LayerStack())


# ---------- runnable (real build123d subprocess) --------------------------


def test_emitted_script_actually_builds(tmp_path):
    """The emitted [box, code] script runs in build123d and produces a STEP."""
    code_path = tmp_path / "code.py"
    code_path.write_text(emit(_box_code_stack()), encoding="utf-8")

    result = Executor(out_dir=tmp_path, timeout_s=60).execute(code_path)

    assert result.error is None
    assert result.exit_code == 0
    assert result.step_path is not None
    assert result.step_path.exists() and result.step_path.stat().st_size > 0
