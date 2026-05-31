"""T1b day-4: both LLM clients satisfy the Protocol and smoke-load (no network)."""

from __future__ import annotations

import pytest

from touch_backend.llm_client import (
    AnthropicAPIClient,
    ClaudeCodeClient,
    LLMClient,
    make_client,
)


def test_make_client_builds_anthropic():
    client = make_client("anthropic_api", api_key="sk-test")
    assert isinstance(client, AnthropicAPIClient)
    assert isinstance(client, LLMClient)
    assert client.name == "anthropic_api"
    assert client.available() is True


def test_make_client_builds_claude_code():
    client = make_client("claude_code")
    assert isinstance(client, ClaudeCodeClient)
    assert isinstance(client, LLMClient)
    assert client.name == "claude_code"
    # SDK absent in dev/CI -> available() is False, but must not crash
    assert isinstance(client.available(), bool)


def test_anthropic_unavailable_without_a_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("touch_backend.keychain_bridge.get_anthropic_key", lambda: None)
    assert AnthropicAPIClient().available() is False


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        make_client("nope")
