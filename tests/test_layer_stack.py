"""Day 1 — the Layer Stack model + deterministic emission (ADR-0012, F38).

Covers the `Layer`/`LayerStack` model, `emit` shape + byte-for-byte determinism,
and one real build123d subprocess run proving the emitted script is runnable.
"""

from __future__ import annotations

import hashlib

import pytest

from touch_backend.agent.executor import Executor
from touch_backend.layer_stack import (
    Layer,
    LayerStack,
    LayerStackError,
    StaleRevisionError,
    emit,
)
from touch_backend.mesh_cache import MeshCache

# A multi-line freeform code layer: proves verbatim inlining + module-scope
# threading of `body` (a through-hole drilled into the previous solid).
_CODE_LAYER = "inner = Cylinder(3.0, 50.0)\nbody = body - inner"


def _box_layer() -> Layer:
    return Layer.from_template(
        "box",
        {"length": 20, "width": 20, "height": 20, "centered": True},
        id="L0",
    )


def _box_only_stack() -> LayerStack:
    return LayerStack(layers=[_box_layer()])


def _box_code_stack() -> LayerStack:
    return LayerStack(layers=[_box_layer(), Layer.from_code(_CODE_LAYER, id="L1")])


class _CountingBuilder:
    """Fake `build(source) -> mesh`: records sources, returns a fresh mesh per call."""

    def __init__(self) -> None:
        self.sources: list[str] = []

    def __call__(self, source: str) -> object:
        self.sources.append(source)
        return object()


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


# ---------- fold + per-layer cache (Day 2) --------------------------------


def test_rebuild_builds_on_miss_then_serves_from_cache():
    cache, builder, stack = MeshCache(), _CountingBuilder(), _box_code_stack()

    first = stack.rebuild(build=builder, cache=cache)
    assert first.cache_hit is False
    assert first.executed_layers == 2
    assert len(builder.sources) == 1  # one subprocess for the whole stack

    second = stack.rebuild(build=builder, cache=cache)
    assert second.cache_hit is True
    assert second.executed_layers == 0
    assert second.mesh is first.mesh
    assert len(builder.sources) == 1  # no re-exec on an unchanged rebuild


def test_unchanged_prefix_is_served_from_cache():
    cache, builder = MeshCache(), _CountingBuilder()

    _box_only_stack().rebuild(build=builder, cache=cache)  # caches the [box] prefix
    _box_code_stack().rebuild(build=builder, cache=cache)  # caches [box, code]
    assert len(builder.sources) == 2

    # Revisiting the earlier [box] state (e.g. undo) is served, no re-exec.
    revisit = _box_only_stack().rebuild(build=builder, cache=cache)
    assert revisit.cache_hit is True
    assert len(builder.sources) == 2


def test_first_dirty_is_the_resume_point():
    cache, builder = MeshCache(), _CountingBuilder()
    _box_only_stack().rebuild(build=builder, cache=cache)  # [box] prefix now cached

    # Appending the code layer: box is clean, the code layer is first dirty.
    result = _box_code_stack().rebuild(build=builder, cache=cache)
    assert result.cache_hit is False
    assert result.first_dirty == 1

    # Nothing cached → the whole stack is dirty from layer 0.
    fresh = _box_code_stack().rebuild(build=_CountingBuilder(), cache=MeshCache())
    assert fresh.first_dirty == 0


def test_rebuild_runs_each_layer_source_once():
    builder = _CountingBuilder()
    _box_code_stack().rebuild(build=builder, cache=MeshCache())
    built = builder.sources[0]
    assert built.count("body = Box(") == 1
    assert built.count(_CODE_LAYER) == 1


def test_rebuild_assigns_chained_deterministic_hashes():
    stack = _box_code_stack()
    stack.rebuild(build=_CountingBuilder(), cache=MeshCache())

    base = hashlib.sha256(b"").hexdigest()
    assert stack.layers[0].input_hash == base
    assert stack.layers[0].output_hash is not None
    # the chain links: layer N's input is layer N-1's output
    assert stack.layers[1].input_hash == stack.layers[0].output_hash

    # an independently built equivalent stack chains to identical hashes
    other = _box_code_stack()
    other.rebuild(build=_CountingBuilder(), cache=MeshCache())
    assert [layer.output_hash for layer in other.layers] == [
        layer.output_hash for layer in stack.layers
    ]


def test_rebuild_empty_stack_rejected():
    with pytest.raises(LayerStackError, match="empty stack"):
        LayerStack().rebuild(build=_CountingBuilder(), cache=MeshCache())


class _RealBuilder:
    """Real `build(source) -> Mesh`: Executor subprocess + import_step + tessellate.

    OCP-touching imports stay inside the call (the OSMesa lazy-import discipline,
    auto-memory `render-backend`).
    """

    def __init__(self, root) -> None:
        self.root = root
        self.calls = 0

    def __call__(self, source: str):
        from build123d import import_step

        from touch_backend.tessellate import tessellate

        self.calls += 1
        run_dir = self.root / f"build{self.calls}"
        run_dir.mkdir()
        code_path = run_dir / "code.py"
        code_path.write_text(source, encoding="utf-8")
        result = Executor(out_dir=run_dir, timeout_s=60).execute(code_path)
        assert result.step_path is not None, result.error
        return tessellate(import_step(result.step_path))


def test_rebuild_produces_a_real_mesh_and_caches_it(tmp_path):
    from touch_backend.tessellate import Mesh

    cache, builder, stack = MeshCache(), _RealBuilder(tmp_path), _box_code_stack()

    first = stack.rebuild(build=builder, cache=cache)
    assert isinstance(first.mesh, Mesh)
    assert first.cache_hit is False
    assert builder.calls == 1

    second = stack.rebuild(build=builder, cache=cache)
    assert second.cache_hit is True
    assert builder.calls == 1  # served from cache, no second subprocess


# ---------- versioned mutations + compare-and-swap (Day 5) ----------------


def _code(id: str) -> Layer:
    return Layer.from_code("body = body.rotate(Axis.Z, 45)", id=id)


def test_add_layer_appends_and_bumps_revision():
    stack = _box_only_stack()
    assert stack.revision == 0

    new_rev = stack.add_layer(_code("L1"), expect_rev=0)
    assert new_rev == 1
    assert stack.revision == 1
    assert [layer.id for layer in stack.layers] == ["L0", "L1"]


def test_add_layer_stale_revision_rejected_without_mutating():
    stack = _box_only_stack()
    stack.add_layer(_code("L1"), expect_rev=0)  # head is now 1
    before = list(stack.layers)

    with pytest.raises(StaleRevisionError) as exc:
        stack.add_layer(_code("L2"), expect_rev=0)  # stale
    assert exc.value.expected == 0 and exc.value.head == 1

    # Rejected mutation left the stack exactly as it was — no corruption (N16).
    assert stack.revision == 1
    assert stack.layers == before


def test_concurrent_edits_on_same_revision_one_wins():
    """Two surfaces plan against revision 0; one applies, one is rejected (N16)."""
    stack = _box_only_stack()
    head = stack.revision

    applied = stack.add_layer(_code("from-viewport"), expect_rev=head)
    assert applied == 1

    with pytest.raises(StaleRevisionError):
        stack.add_layer(_code("from-agent"), expect_rev=head)

    # Exactly one edit landed; the loser re-plans against the new head.
    assert [layer.id for layer in stack.layers] == ["L0", "from-viewport"]
    assert stack.revision == 1


def test_delete_last_removes_top_and_bumps_revision():
    stack = _box_only_stack()
    stack.add_layer(_code("L1"), expect_rev=0)

    removed = stack.delete_last(expect_rev=1)
    assert removed.id == "L1"
    assert [layer.id for layer in stack.layers] == ["L0"]
    assert stack.revision == 2


def test_delete_last_stale_revision_rejected():
    stack = _box_only_stack()
    stack.add_layer(_code("L1"), expect_rev=0)
    with pytest.raises(StaleRevisionError):
        stack.delete_last(expect_rev=0)
    assert [layer.id for layer in stack.layers] == ["L0", "L1"]
    assert stack.revision == 1


def test_delete_last_on_empty_stack_rejected():
    with pytest.raises(LayerStackError, match="empty stack"):
        LayerStack().delete_last(expect_rev=0)


def test_add_then_delete_round_trips_to_same_layers():
    stack = _box_only_stack()
    stack.add_layer(_code("L1"), expect_rev=0)
    stack.delete_last(expect_rev=1)
    # Append-only undo (delete-last) returns the layer set; revision keeps climbing.
    assert [layer.id for layer in stack.layers] == ["L0"]
    assert stack.revision == 2
