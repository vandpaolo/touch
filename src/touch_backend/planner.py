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

from touch_backend._generated.protocol import Operation, Selection
from touch_backend.llm_client.base import LLMClient

PLANNER_SYSTEM = """You are Touch's CAD planner. Given a natural-language prompt \
and an optional selection context (the face the user clicked), respond with a \
SINGLE JSON object describing ONE operation, with exactly two fields:

  {"kind": <one of: box, cylinder, sphere, chamfer>, "params": { ... }}

Do NOT include id, selection, timestamps, or any prose — only "kind" and \
"params". The selection is supplied separately by the system.

Params per kind (all lengths in millimetres):
  box:      {"length": L, "width": W, "height": H}
  cylinder: {"radius": R, "height": H}
  sphere:   {"radius": R}
  chamfer:  {"length": S}   // S = chamfer size; applies to the selected face's edges

Examples:
  "a 40 mm cube" -> {"kind":"box","params":{"length":40,"width":40,"height":40}}
  "add a 5 mm chamfer here" -> {"kind":"chamfer","params":{"length":5}}
  "a 30 mm radius sphere" -> {"kind":"sphere","params":{"radius":30}}

Respond with JSON only."""


class PlannerError(Exception):
    """The planner could not derive a valid Operation from the LLM output."""


def plan(
    client: LLMClient,
    prompt_text: str,
    selection: Selection | None = None,
) -> Operation:
    """Turn a prompt (+ optional selection) into a structured Operation.

    The LLM supplies `{kind, params}`; the server owns id/timestamp/selection.
    """
    response = client.complete(
        system=PLANNER_SYSTEM, prompt=_build_prompt(prompt_text, selection)
    )
    data = _extract_json(response.text)

    kind = data.get("kind")
    params = data.get("params")
    if not isinstance(kind, str) or not isinstance(params, dict):
        raise PlannerError("LLM output missing 'kind' or 'params'")

    sel = selection.model_dump(mode="json") if selection is not None else None
    payload = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "params": params,
        "selection": sel,
        "prompt_text": prompt_text,
        "conversation": [],
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


def _build_prompt(prompt_text: str, selection: Selection | None) -> str:
    if selection is None:
        return prompt_text
    context = selection.model_dump_json()
    return f"{prompt_text}\n\nSelection context (the clicked face):\n{context}"
