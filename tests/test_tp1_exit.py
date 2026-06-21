"""TP1 exit criteria — a part built as a stack INCLUDING a freeform code layer,
end to end: clickable (provenance), persists + reopens identical, append-only
undo/redo, and stale-revision rejection (F38/F39/F44/F45/N16, ADR-0012/0013).

The click-to-prompt chamfer (now a finder-scoped layer) and the live
clickable+undoable flow are covered in test_live_build.py.
"""

from __future__ import annotations

import pytest

from touch_backend.layer_bridge import load_stack, save_stack
from touch_backend.layer_stack import Layer, LayerStack, StaleRevisionError
from touch_backend.live_build import build_mesh


def _exit_stack() -> LayerStack:
    # A recognised template + a FREEFORM code layer (an all-edges fillet — not a
    # v0 op, not a recognised template): the long tail the Layer Stack exists for.
    return LayerStack(
        layers=[
            Layer.from_template(
                "box",
                {"length": 20.0, "width": 20.0, "height": 20.0, "centered": True},
                id="base",
            ),
            Layer.from_code("body = fillet(body.edges(), 1.0)", id="round"),
        ]
    )


def test_stack_with_a_freeform_code_layer_is_clickable():
    """Build a part as a stack with a code layer; every face maps to its layer."""
    mesh = build_mesh(_exit_stack(), timeout_s=60)

    assert mesh.face_provenance, "provenance was not baked"
    assert set(mesh.face_ids).issubset(mesh.face_provenance)  # every face clickable
    # The freeform code layer owns the fillet faces it created...
    assert any(e.created_by == {"round"} for e in mesh.face_provenance.values())
    # ...and the surviving box planes are still attributed to the template layer.
    assert any(e.created_by == {"base"} for e in mesh.face_provenance.values())


def test_save_then_reopen_is_identical_including_the_code_layer(tmp_path):
    stack = _exit_stack()
    path = tmp_path / "part.touch"
    save_stack(stack, path)
    assert load_stack(path) == stack  # the code layer's source round-trips


def test_append_only_undo_redo_with_stale_revision_rejected():
    stack = _exit_stack()  # revision 0, two layers
    extra = Layer.from_code("body = body", id="extra")

    assert stack.add_layer(extra, expect_rev=0) == 1  # add
    assert [layer.id for layer in stack.layers] == ["base", "round", "extra"]

    removed = stack.delete_last(expect_rev=1)  # undo = delete-last (append-only)
    assert removed.id == "extra"
    assert stack.revision == 2 and len(stack.layers) == 2

    stack.add_layer(extra, expect_rev=2)  # redo = re-add
    assert len(stack.layers) == 3

    with pytest.raises(StaleRevisionError):  # N16: a stale mutation is rejected
        stack.add_layer(extra, expect_rev=0)
