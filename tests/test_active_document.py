"""ActiveDocument — the one shared canonical Layer Stack (ADR-0013).

The N16 compare-and-swap race: two writers (the viewport and, in sprint 2, the
agent over MCP) act on the same document. The external-writer entry
(`add_layer(expect_rev=...)`) is the agent's CAS path; a stale revision is
rejected, not silently applied. (The structured *wire* rejection lands with the
MCP mutating tools in sprint 2 — the agent is the first real second writer.)
"""

from __future__ import annotations

import pytest

from touch_backend.active_document import ActiveDocument, StaleRevisionError
from touch_backend.layer_stack import Layer


def _box(layer_id: str) -> Layer:
    return Layer.from_template(
        "box", {"length": 10, "width": 10, "height": 10}, id=layer_id
    )


def test_cas_race_one_applied_one_rejected_then_replanned():
    """Two writers capture the same head; the first wins, the second is rejected
    (N16) and re-plans against the new head — the stack never corrupts."""
    doc = ActiveDocument()
    head = doc.revision  # both writers read this revision (0)

    # Writer A applies against the captured head → succeeds, the head advances.
    assert doc.add_layer(_box("a"), expect_rev=head) == 1

    # Writer B applies against the now-STALE captured head → rejected, no mutation.
    with pytest.raises(StaleRevisionError):
        doc.add_layer(_box("b"), expect_rev=head)
    assert [layer.id for layer in doc.layers] == ["a"]  # B did not corrupt the stack

    # B re-reads the head and re-applies (the re-plan) → succeeds.
    assert doc.add_layer(_box("b"), expect_rev=doc.revision) == 2
    assert [layer.id for layer in doc.layers] == ["a", "b"]


def test_stale_revision_error_carries_structured_fields():
    """The rejection is structured (expected vs head) — the data the MCP envelope
    surfaces so the agent re-plans rather than seeing a traceback (sprint 2)."""
    doc = ActiveDocument()
    doc.add_layer(_box("a"), expect_rev=0)  # head → 1
    with pytest.raises(StaleRevisionError) as exc:
        doc.add_layer(_box("b"), expect_rev=0)
    assert exc.value.expected == 0
    assert exc.value.head == 1


def test_undo_redo_round_trips_on_the_shared_doc():
    doc = ActiveDocument()
    doc.add_layer(_box("a"), expect_rev=doc.revision)
    doc.add_layer(_box("b"), expect_rev=doc.revision)
    assert doc.can_undo and not doc.can_redo

    doc.undo()
    assert [layer.id for layer in doc.layers] == ["a"]
    assert doc.can_redo

    doc.redo()
    assert [layer.id for layer in doc.layers] == ["a", "b"]
    assert not doc.can_redo


def test_a_fresh_add_clears_the_redo_stack():
    doc = ActiveDocument()
    doc.add_layer(_box("a"), expect_rev=doc.revision)
    doc.undo()
    assert doc.can_redo
    doc.add_layer(_box("b"), expect_rev=doc.revision)
    assert not doc.can_redo  # the new edit invalidated redo
