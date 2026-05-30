# 0007 — Pluggable LLM client + Claude Code subscription path

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** vandpaolo

## Context

Touch's end-users are engineer friends running a Windows `.exe`. They
need to authenticate the LLM. Two realistic auth modes exist for Claude:

1. **An Anthropic API key** — pay-per-token, requires creating a
   developer account, billing setup, and pasting a key into a settings
   panel. The default Maquette-era path.
2. **A Claude Pro / Max subscription** — flat-rate (~$20 or ~$100/mo),
   already covers Claude Code. Heavy users save money vs API, and there
   is **no per-prompt cost anxiety**.

Anthropic ships the **Claude Agent SDK** (`claude-agent-sdk` on PyPI;
TypeScript variant exists too). It can drive a locally-installed Claude
Code instance programmatically, **borrowing the user's subscription
auth** — no API key needed in Touch.

The Maquette planner (`planner.plan(client, prompt, model, prompts)`)
already takes a `client` parameter. Touch can keep that shape, abstracted
behind a Protocol, with two implementations.

## Decision

**Touch ships a `LLMClient` Protocol with two v0 implementations,
selectable in Settings:**

- `AnthropicAPIClient` — wraps `anthropic.Anthropic`. Reads the user's
  API key from the OS keychain via `keychain_bridge` (requirement F13a /
  N9).
- `ClaudeCodeClient` — wraps `claude-agent-sdk`'s `ClaudeSDKClient`.
  Uses the user's local Claude Code login (no key stored in Touch).

The Settings panel offers the choice. Claude Code mode is **hidden when
Claude Code isn't installed or authed** — Touch probes for it on
startup. The Anthropic-API mode is the no-extra-install default.

The planner is refactored to take the Protocol:

```python
class LLMClient(Protocol):
    def call(self, prompt: str, system: str, *, model: str | None = None,
             tokens_budget: int | None = None) -> Response: ...
```

Both implementations normalise their respective SDK responses into a
shared `Response` (text + `Tokens` usage).

## Consequences

- Friends with a **Claude Pro/Max subscription save money** and don't
  face per-prompt cost anxiety — a real product win.
- Touch **stores no credential** in Claude Code mode; Claude Code owns
  its own auth lifecycle. Less attack surface in Touch itself.
- The Protocol cleanly extends to a **third provider** (Vertex AI, AWS
  Bedrock, OpenAI, …) when there's a reason — one more `LLMClient` impl,
  no planner change.
- **Cost:** the Claude Code path requires the friend to install Claude
  Code separately and run `claude login` once. That's an extra step
  Touch shouldn't try to automate — but it must be clearly explained in
  Settings (an in-app guide / link).
- **Cost:** `claude-agent-sdk` is a younger SDK than the Anthropic API
  SDK; it may churn. Pinning a tested version + treating the abstraction
  as the fallback ("if Claude Code breaks, use API mode") limits the
  blast radius.
- **Cost:** the Claude Code path may not expose the same fine-grained
  controls (prompt caching shape, exact model selection, etc.) as the
  direct API. Where possible, both implementations expose the same
  controls; where not, the Protocol degrades gracefully.

## Alternatives considered

- **API-only (current Maquette path).** Rejected: leaves subscription
  users overpaying / wary of every click.
- **Claude Code only.** Rejected: requires every friend to install
  Claude Code (extra friction) and locks out friends who'd rather just
  paste an API key.
- **Shell out to `claude -p "<prompt>"` instead of the SDK.** Acceptable
  as a fallback inside `ClaudeCodeClient`, but the SDK is the preferred
  primary because it returns structured responses and surfaces errors
  cleanly.
- **A provider-abstraction layer (LiteLLM, LangChain, etc.)** abstracting
  many providers at once. Rejected: too much surface for v0; we only
  need Claude two ways, both first-party.
