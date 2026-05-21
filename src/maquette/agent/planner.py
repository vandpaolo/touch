"""F2 Planner (see ADR 0001, ADR 0003).

Wraps a single Anthropic Messages call with prompt caching on the system
prompt (ADR 0003). Parses the response into a validated ``Intent`` with
one retry on schema / JSON failure. Stateless; the only side effect is
the network call delegated to the caller-supplied client.

The retry budget is 2 LLM calls total per ``plan(...)`` invocation. If
both attempts fail validation, ``PlannerExhausted`` is raised.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic
from pydantic import ValidationError

from maquette.intent import Intent
from maquette.pricing import Tokens


class PlannerExhausted(Exception):
    """Raised when both planner attempts fail to produce a valid Intent."""


@dataclass(frozen=True)
class PromptsBundle:
    """In-memory record of the ``prompts/`` directory.

    Phase-2a only requires ``planner_system``; the SHA-256 ``hash`` is
    populated by ``agent.loop`` in phase-2b (per ADR 0003).
    """

    planner_system: str
    hash: str = ""


@dataclass(frozen=True)
class PlanResult:
    intent: Intent
    tokens: Tokens
    retries: int


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_BLOCK_RE = re.compile(r"(\{.*\})", re.DOTALL)


def plan(
    client: Anthropic,
    prompt: str,
    model: str,
    prompts: PromptsBundle,
) -> PlanResult:
    """Call the LLM, extract JSON, validate as Intent. One retry on failure.

    Total LLM calls per invocation: at most 2. The system prompt is sent
    with ``cache_control: {"type": "ephemeral"}`` (ADR 0003) so repeated
    calls within the cache TTL pay cache-read pricing on the system half.
    """
    cumulative = _zero_tokens()
    user_content = prompt
    last_error: str | None = None

    for attempt in range(2):
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": prompts.planner_system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_content}],
        )
        cumulative = _add_tokens(cumulative, _tokens_from_response(response))
        text = _response_text(response)

        payload = _extract_json(text)
        if payload is None:
            last_error = (
                "could not extract a JSON object from the response; "
                "please return raw JSON only."
            )
        else:
            try:
                intent = Intent.model_validate(payload)
            except ValidationError as e:
                last_error = f"schema validation failed: {e}"
            else:
                return PlanResult(intent=intent, tokens=cumulative, retries=attempt)

        user_content = (
            prompt
            + "\n\nYour previous output failed: "
            + last_error
            + "\nReturn JSON matching the Intent schema."
        )

    raise PlannerExhausted(
        f"Planner exhausted after 2 attempts; last error: {last_error}"
    )


def _zero_tokens() -> Tokens:
    return Tokens(input=0, output=0, cache_read=0, cache_creation=0)


def _add_tokens(a: Tokens, b: Tokens) -> Tokens:
    return Tokens(
        input=a.input + b.input,
        output=a.output + b.output,
        cache_read=a.cache_read + b.cache_read,
        cache_creation=a.cache_creation + b.cache_creation,
    )


def _tokens_from_response(response: Any) -> Tokens:
    usage = getattr(response, "usage", None)
    return Tokens(
        input=int(getattr(usage, "input_tokens", 0) or 0),
        output=int(getattr(usage, "output_tokens", 0) or 0),
        cache_read=int(getattr(usage, "cache_read_input_tokens", 0) or 0),
        cache_creation=int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
    )


def _response_text(response: Any) -> str:
    content = getattr(response, "content", None)
    if content is None:
        return ""
    chunks: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            chunks.append(text)
    return "\n".join(chunks)


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        pass
    else:
        if isinstance(result, dict):
            return result

    m = _JSON_FENCE_RE.search(text)
    if m:
        try:
            result = json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(result, dict):
                return result

    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            result = json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(result, dict):
                return result

    return None
