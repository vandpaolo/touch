"""Claude Code client (F31b): the user's Pro/Max subscription via claude-agent-sdk.

`claude-agent-sdk` is imported lazily and guarded — it (and a locally installed,
authed Claude Code CLI) may be absent on a dev box or in CI. Absence must never
break import or smoke-load; `available()` simply reports False. The real
completion path lands in T6.
"""

from __future__ import annotations

import importlib.util


class ClaudeCodeClient:
    """Drives the user's local Claude Code under their subscription (F13b)."""

    name = "claude_code"

    def __init__(self, *, model: str = "claude-opus-4-7"):
        self._model = model

    def available(self) -> bool:
        # SDK importable is the v0 gate; CLI-installed/authed checks land in T6.
        return importlib.util.find_spec("claude_agent_sdk") is not None

    def complete(self, *, system: str, prompt: str, max_tokens: int = 2048):
        if not self.available():
            raise RuntimeError(
                "claude-agent-sdk is not installed; install it and the Claude "
                "Code CLI to use Claude Code mode (F31b)."
            )
        raise NotImplementedError("ClaudeCodeClient.complete lands in T6")
