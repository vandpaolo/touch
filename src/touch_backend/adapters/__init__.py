from __future__ import annotations

from typing import Protocol

from touch_backend.intent import Intent


class Adapter(Protocol):
    """Structural contract every concrete adapter satisfies.

    The shape is `(intent: Intent) -> str`. Concrete adapters expose this
    as a module-level function; the `__call__` form lets bare functions
    satisfy the Protocol statically (pyright structural callable check).
    """

    def __call__(self, intent: Intent, /) -> str: ...


class AdapterRefusal(Exception):
    """An adapter cannot translate the given Intent.

    Carries a human-readable `reason` and a structured `where` field
    (e.g. `feature:loft`, `modifier:bevel`) so the Loop can surface
    the failure location in `error.json` without parsing free text.
    """

    def __init__(self, reason: str, where: str) -> None:
        super().__init__(f"{where}: {reason}")
        self.reason = reason
        self.where = where


__all__ = ["Adapter", "AdapterRefusal"]
