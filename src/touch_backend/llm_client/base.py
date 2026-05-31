"""Shared types for the LLM-client abstraction (F31, ADR-0007).

Kept separate from the package `__init__` so the concrete clients can import
`LLMResponse` without a circular import.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class LLMResponse:
    """A single completion result + token usage (for pricing, F14)."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0


@runtime_checkable
class LLMClient(Protocol):
    """The swappable LLM call surface. Both v0 clients satisfy this."""

    name: str

    def available(self) -> bool:
        """Whether this client can run now (key present / SDK installed+authed).

        Drives Settings hiding Claude Code mode when unavailable (F31).
        """
        ...

    def complete(
        self, *, system: str, prompt: str, max_tokens: int = 2048
    ) -> LLMResponse:
        """Run one completion. Real calls are exercised in T6."""
        ...
