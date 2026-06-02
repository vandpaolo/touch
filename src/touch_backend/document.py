"""The Touch document — an ordered, append-only operation history (F8, F10, F23).

The document *is* the source of truth: replaying its `history` reproduces the
solid (live in-memory state is a derived cache, ADR-0008). Persisted as
human-readable `.touch` JSON carrying `schema_version` (N7); `load` runs a
forward-only migration helper so older files keep opening.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from touch_backend._generated.protocol import Operation, Parameter

SCHEMA_VERSION = 1
TOUCH_VERSION = "0.1.0"  # written into .touch files; wired to package metadata later


@dataclass
class TouchDocument:
    """An open document: ordered history of operations (F8, append-only v0)."""

    schema_version: int = SCHEMA_VERSION
    name: str = "untitled"
    description: str = ""
    parameters: list[Parameter] = field(default_factory=list)
    history: list[Operation] = field(default_factory=list)
    created_at: str | None = None
    modified_at: str | None = None
    touch_version: str = TOUCH_VERSION

    def append(self, operation: Operation) -> None:
        """Append an operation to the history (the only mutation in v0)."""
        self.history.append(operation)

    def to_dict(self) -> dict[str, Any]:
        """Canonical serializable form (the `.touch` JSON shape)."""
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "description": self.description,
            "parameters": [p.model_dump(mode="json") for p in self.parameters],
            "history": [op.model_dump(mode="json") for op in self.history],
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "touch_version": self.touch_version,
        }

    def save(self, path: Path) -> None:
        """Write the document to `path` as human-readable, diff-friendly JSON."""
        now = datetime.now(UTC).isoformat()
        if self.created_at is None:
            self.created_at = now
        self.modified_at = now
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> TouchDocument:
        """Read + validate a `.touch` file, migrating older schema versions."""
        data = _migrate(json.loads(path.read_text(encoding="utf-8")))
        return cls(
            schema_version=SCHEMA_VERSION,
            name=data.get("name", "untitled"),
            description=data.get("description", ""),
            parameters=[
                Parameter.model_validate(p) for p in data.get("parameters", [])
            ],
            history=[Operation.model_validate(op) for op in data.get("history", [])],
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
            touch_version=data.get("touch_version", TOUCH_VERSION),
        )


def _migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Forward-only `.touch` migration (N7).

    Readers tolerate newer minor versions that only add fields (we read known
    keys; extras are ignored). Older versions get per-version upgrades here —
    none needed at v1 yet, but the seam is in place. Pre-`schema_version` files
    (treated as v0) are normalised by `load`'s `.get` defaults.
    """
    version = int(data.get("schema_version", 0))
    if version < SCHEMA_VERSION:
        # v0 -> v1: nothing structural changed; load() fills missing fields.
        data["schema_version"] = SCHEMA_VERSION
    return data
