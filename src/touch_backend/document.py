"""The in-memory Touch document — an ordered, append-only operation history.

Load/save to `.touch` JSON and replay-from-history land in T4 (F10/F23); for
now this is just the in-memory shape the session edits.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from touch_backend._generated.protocol import Operation


@dataclass
class TouchDocument:
    """An open document: ordered history of operations (F8, append-only v0)."""

    schema_version: int = 1
    name: str = "untitled"
    history: list[Operation] = field(default_factory=list)

    def append(self, operation: Operation) -> None:
        """Append an operation to the history (the only mutation in v0)."""
        self.history.append(operation)
