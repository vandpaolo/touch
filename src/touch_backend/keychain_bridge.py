"""OS-keychain read/write for the user's Anthropic API key (F13, N9).

A thin wrapper over `keyring` so the key never lives in Touch's own files —
it stays in the platform secret store (macOS Keychain / Windows Credential
Manager / Secret Service). Consumed by `llm_client.AnthropicAPIClient`.
"""

from __future__ import annotations

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

SERVICE = "touch_backend"
USERNAME = "anthropic_api_key"


def get_anthropic_key() -> str | None:
    """Return the stored Anthropic API key, or None if unset/unavailable.

    Tolerates a missing OS backend (headless dev box) by returning None rather
    than raising — callers treat that as "no key".
    """
    try:
        return keyring.get_password(SERVICE, USERNAME)
    except KeyringError:
        return None


def set_anthropic_key(key: str) -> None:
    """Store the Anthropic API key in the OS keychain."""
    keyring.set_password(SERVICE, USERNAME, key)


def clear() -> None:
    """Remove the stored key. No-op if nothing is stored."""
    try:
        keyring.delete_password(SERVICE, USERNAME)
    except PasswordDeleteError:
        pass
