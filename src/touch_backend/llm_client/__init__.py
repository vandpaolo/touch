"""Pluggable LLM-client abstraction (F31, ADR-0007).

The planner talks to *one* `LLMClient`; two v0 implementations satisfy it:
`AnthropicAPIClient` (the user's API key, OS-keychain) and `ClaudeCodeClient`
(the user's Claude Code subscription via `claude-agent-sdk`). The active client
is chosen at session start from Settings; `make_client(mode)` builds it.
"""

from __future__ import annotations

from touch_backend.llm_client.anthropic_api import AnthropicAPIClient
from touch_backend.llm_client.base import LLMClient, LLMResponse
from touch_backend.llm_client.claude_code import ClaudeCodeClient


def make_client(mode: str, **kwargs) -> LLMClient:
    """Build the client for the given Settings mode."""
    if mode == "anthropic_api":
        return AnthropicAPIClient(**kwargs)
    if mode == "claude_code":
        return ClaudeCodeClient(**kwargs)
    raise ValueError(f"unknown LLM client mode: {mode!r}")


__all__ = [
    "AnthropicAPIClient",
    "ClaudeCodeClient",
    "LLMClient",
    "LLMResponse",
    "make_client",
]
