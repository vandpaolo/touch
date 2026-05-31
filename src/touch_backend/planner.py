"""The LLM planner: prompt (+ selection) -> a structured Operation (F22).

v0 skeleton: the planner asks the active `LLMClient` for a JSON Operation and
validates it against the protocol schema. Clarifying-question branches (F7) and
real tool-use/structured-output prompting are refined in T5/T6; the contract
test drives this with a mocked client.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from touch_backend._generated.protocol import Operation, Selection
from touch_backend.llm_client.base import LLMClient

PLANNER_SYSTEM = (
    "You are Touch's CAD planner. Given a natural-language prompt and an "
    "optional selection context, respond with a SINGLE JSON object matching the "
    "Operation schema (fields: id, kind, params, selection, prompt_text, "
    "conversation, created_at). Respond with JSON only — no prose."
)


class PlannerError(Exception):
    """The planner could not derive a valid Operation from the LLM output."""


def plan(
    client: LLMClient,
    prompt_text: str,
    selection: Selection | None = None,
) -> Operation:
    """Turn a prompt (+ optional selection) into a structured Operation."""
    response = client.complete(
        system=PLANNER_SYSTEM, prompt=_build_prompt(prompt_text, selection)
    )
    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise PlannerError("LLM output was not valid JSON") from exc
    try:
        return Operation.model_validate(data)
    except ValidationError as exc:
        raise PlannerError("LLM output did not match the Operation schema") from exc


def _build_prompt(prompt_text: str, selection: Selection | None) -> str:
    if selection is None:
        return prompt_text
    return f"{prompt_text}\n\nSelection context:\n{selection.model_dump_json()}"
