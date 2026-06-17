"""The LLM planner: prompt (+ selection) -> a structured Operation (F22).

The LLM decides only the operation *kind* and its *params* (a small, robust ask).
The server assembles the full Operation around that: it mints the id + timestamp
and attaches the frontend-provided Selection (the clicked face) — the LLM never
fabricates the selection or identity. Clarifying-question branches (F7) land in
T5; live provider config is T6.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from touch_backend._generated.protocol import (
    ClarifyingQuestion,
    ConversationTurn,
    Operation,
    Selection,
)
from touch_backend.llm_client.base import LLMClient

# Required numeric params per operation kind. A missing one triggers a
# clarifying question (F7) rather than a guessed dimension (ADR/T5).
REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "box": ("length", "width", "height"),
    "cylinder": ("radius", "height"),
    "sphere": ("radius",),
    "chamfer": ("length",),
}

PLANNER_SYSTEM = """You are Touch's CAD planner. Given a natural-language prompt \
and an optional selection context (the face the user clicked), respond with a \
SINGLE JSON object.

Normally respond with exactly two fields:

  {"kind": <one of: box, cylinder, sphere, chamfer>, "params": { ... }}

Do NOT include id, selection, timestamps, or any prose — only "kind" and \
"params". The selection is supplied separately by the system.

Params per kind (all lengths in millimetres):
  box:      {"length": L, "width": W, "height": H}
  cylinder: {"radius": R, "height": H}
  sphere:   {"radius": R}
  chamfer:  {"length": S}   // S = chamfer size; applies to the selected face's edges

IMPORTANT: include ONLY parameters the user explicitly gave. NEVER invent a \
missing dimension — omit it, and the system will ask the user. If the request \
is too vague to choose a kind at all, respond instead with:

  {"clarify": "<a short question to the user>"}

Examples:
  "a 40 mm cube" -> {"kind":"box","params":{"length":40,"width":40,"height":40}}
  "add a 5 mm chamfer here" -> {"kind":"chamfer","params":{"length":5}}
  "chamfer this edge" -> {"kind":"chamfer","params":{}}   // no size given; system asks
  "a 30 mm radius sphere" -> {"kind":"sphere","params":{"radius":30}}
  "do something cool" -> {"clarify":"What would you like to create or change?"}

Respond with JSON only."""


class PlannerError(Exception):
    """The planner could not derive a valid Operation from the LLM output."""


def plan(
    client: LLMClient,
    prompt_text: str,
    selection: Selection | None = None,
    *,
    attempt: int = 1,
    conversation: list[ConversationTurn] | None = None,
) -> Operation | ClarifyingQuestion:
    """Turn a prompt (+ optional selection) into a structured Operation, or a
    ClarifyingQuestion (F7) when the request is ambiguous or under-specified.

    The LLM supplies `{kind, params}` or `{clarify}`; the server owns
    id/timestamp/selection. `attempt` is the conversation turn count (the
    session caps it); `conversation` is the clarification thread so far — fed to
    the LLM as context and recorded on the resulting Operation.
    """
    response = client.complete(
        system=PLANNER_SYSTEM,
        prompt=_build_prompt(prompt_text, selection, conversation),
    )
    data = _extract_json(response.text)

    # The LLM may ask instead of answering (a prompt too vague to choose a kind).
    clarify = data.get("clarify")
    if isinstance(clarify, str) and clarify.strip():
        return ClarifyingQuestion(question=clarify.strip(), attempt=attempt)

    kind = data.get("kind")
    params = data.get("params")
    if not isinstance(kind, str) or not isinstance(params, dict):
        raise PlannerError("LLM output missing 'kind' or 'params'")

    # Contract-driven clarification (F7): a missing required param means ask,
    # never guess a dimension the user did not give.
    missing = _missing_params(kind, params)
    if missing:
        return ClarifyingQuestion(question=_ask_for(kind, missing), attempt=attempt)

    sel = selection.model_dump(mode="json") if selection is not None else None
    turns = [t.model_dump(mode="json", by_alias=True) for t in (conversation or [])]
    payload = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "params": params,
        "selection": sel,
        "prompt_text": prompt_text,
        "conversation": turns,
        "created_at": datetime.now(UTC).isoformat(),
    }
    try:
        return Operation.model_validate(payload)
    except ValidationError as exc:
        raise PlannerError(f"invalid operation from LLM: kind={kind!r}") from exc


def _extract_json(text: str) -> dict[str, Any]:
    """Parse a JSON object from the LLM text, tolerating code fences / prose."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    raise PlannerError("LLM output was not a JSON object")


def _missing_params(kind: str, params: dict[str, Any]) -> list[str]:
    """Required params of `kind` that are absent or non-numeric (so we must ask)."""
    return [
        name
        for name in REQUIRED_PARAMS.get(kind, ())
        if not isinstance(params.get(name), (int, float))
        or isinstance(params.get(name), bool)
    ]


def _ask_for(kind: str, missing: list[str]) -> str:
    """A short clarifying question for the missing dimension(s)."""
    names = ", ".join(missing)
    return f"What {names} (in mm) should the {kind} have?"


def _build_prompt(
    prompt_text: str,
    selection: Selection | None,
    conversation: list[ConversationTurn] | None = None,
) -> str:
    parts = [prompt_text]
    if conversation:
        thread = "\n".join(f"{t.from_}: {t.text}" for t in conversation)
        parts.append(f"Conversation so far:\n{thread}")
    if selection is not None:
        parts.append(
            f"Selection context (the clicked face):\n{selection.model_dump_json()}"
        )
    return "\n\n".join(parts)
