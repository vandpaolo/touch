"""Anthropic API client (F31a): the user's own API key via the OS keychain.

The key is read from `keychain_bridge` (falling back to `ANTHROPIC_API_KEY` in
the env). The `anthropic` SDK and the network client are constructed lazily, so
constructing this object is cheap and offline (smoke-load safe).
"""

from __future__ import annotations

import os
from typing import Any

from touch_backend import keychain_bridge
from touch_backend.llm_client.base import LLMResponse


class AnthropicAPIClient:
    """Talks to the Anthropic API with the user's key (F13a)."""

    name = "anthropic_api"

    def __init__(self, *, api_key: str | None = None, model: str = "claude-opus-4-7"):
        self._model = model
        self._api_key = (
            api_key
            or keychain_bridge.get_anthropic_key()
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        self._client: Any = None

    def available(self) -> bool:
        return bool(self._api_key)

    def _ensure_client(self) -> Any:
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self._api_key)
        return self._client

    def complete(
        self, *, system: str, prompt: str, max_tokens: int = 2048
    ) -> LLMResponse:
        client = self._ensure_client()
        response = client.messages.create(
            model=self._model,
            system=system,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(getattr(block, "text", "") for block in response.content)
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
