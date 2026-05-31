"""T1b day-4: keychain_bridge get/set/clear against an in-memory keyring backend."""

from __future__ import annotations

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError

from touch_backend import keychain_bridge


class _MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self) -> None:
        super().__init__()
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        try:
            del self._store[(service, username)]
        except KeyError as exc:
            raise PasswordDeleteError("not set") from exc


@pytest.fixture
def mem_keyring():
    previous = keyring.get_keyring()
    keyring.set_keyring(_MemoryKeyring())
    yield
    keyring.set_keyring(previous)


def test_set_get_roundtrip(mem_keyring):
    assert keychain_bridge.get_anthropic_key() is None
    keychain_bridge.set_anthropic_key("sk-test-123")
    assert keychain_bridge.get_anthropic_key() == "sk-test-123"


def test_clear_removes_key(mem_keyring):
    keychain_bridge.set_anthropic_key("sk-test-123")
    keychain_bridge.clear()
    assert keychain_bridge.get_anthropic_key() is None


def test_clear_is_noop_when_unset(mem_keyring):
    keychain_bridge.clear()
    assert keychain_bridge.get_anthropic_key() is None
