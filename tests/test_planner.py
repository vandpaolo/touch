from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from maquette.agent.planner import (
    PlannerExhausted,
    PlanResult,
    PromptsBundle,
    plan,
)
from maquette.pricing import Tokens

_CUBE_WITH_HOLE_JSON: dict[str, Any] = {
    "name": "cube_with_hole",
    "description": "50 mm cube with 20 mm hole",
    "schema_version": 1,
    "parameters": [
        {"name": "size", "value": 50, "unit": "mm"},
        {"name": "hole_diam", "value": 20, "unit": "mm"},
    ],
    "features": [
        {
            "id": "body",
            "kind": "box",
            "params": {
                "length": 50,
                "width": 50,
                "height": 50,
                "centered": "true",
            },
        }
    ],
    "modifiers": [
        {
            "id": "drill",
            "kind": "hole",
            "target": "body",
            "params": {"diameter": 20, "through": "true", "axis": "z"},
        }
    ],
    "extras": None,
}

_BAD_JSON: dict[str, Any] = {
    "name": "broken",
    "description": "missing features",
    "schema_version": 1,
}


def _make_response(
    text: str,
    *,
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_read: int = 0,
    cache_creation: int = 0,
) -> Any:
    return SimpleNamespace(
        content=[SimpleNamespace(text=text, type="text")],
        usage=SimpleNamespace(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_creation,
        ),
    )


def _bundle() -> PromptsBundle:
    return PromptsBundle(planner_system="SYSTEM PROMPT", hash="deadbeef")


def test_plain_json_response_validates_and_maps_tokens() -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_response(
        json.dumps(_CUBE_WITH_HOLE_JSON),
        input_tokens=270,
        output_tokens=540,
        cache_read=4000,
        cache_creation=0,
    )
    result = plan(
        client, "a 50 mm cube with a 20 mm hole", "claude-opus-4-7", _bundle()
    )

    assert isinstance(result, PlanResult)
    assert result.retries == 0
    assert result.tokens == Tokens(
        input=270, output=540, cache_read=4000, cache_creation=0
    )
    assert result.intent.name == "cube_with_hole"
    assert len(result.intent.features) == 1
    assert result.intent.features[0].kind == "box"
    assert len(result.intent.modifiers) == 1
    assert result.intent.modifiers[0].kind == "hole"


def test_fenced_code_block_extraction() -> None:
    client = MagicMock()
    fenced = "Here is the JSON:\n```json\n" + json.dumps(_CUBE_WITH_HOLE_JSON) + "\n```"
    client.messages.create.return_value = _make_response(fenced)
    result = plan(client, "prompt", "claude-opus-4-7", _bundle())
    assert result.retries == 0
    assert result.intent.name == "cube_with_hole"


def test_retry_on_schema_fail_then_success() -> None:
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_response(json.dumps(_BAD_JSON), input_tokens=10, output_tokens=20),
        _make_response(
            json.dumps(_CUBE_WITH_HOLE_JSON), input_tokens=30, output_tokens=40
        ),
    ]
    result = plan(client, "prompt", "claude-opus-4-7", _bundle())
    assert result.retries == 1
    # Tokens accumulate across both calls.
    assert result.tokens == Tokens(input=40, output=60, cache_read=0, cache_creation=0)
    assert client.messages.create.call_count == 2


def test_two_schema_fails_raise_planner_exhausted() -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_response(json.dumps(_BAD_JSON))
    with pytest.raises(PlannerExhausted):
        plan(client, "prompt", "claude-opus-4-7", _bundle())
    assert client.messages.create.call_count == 2


def test_cache_control_present_on_system_prompt() -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_response(
        json.dumps(_CUBE_WITH_HOLE_JSON)
    )
    plan(client, "prompt", "claude-opus-4-7", _bundle())

    kwargs = client.messages.create.call_args.kwargs
    system = kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["type"] == "text"
    assert system[0]["text"] == "SYSTEM PROMPT"
    assert system[0]["cache_control"] == {"type": "ephemeral"}


def test_model_id_passes_through_unchanged() -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_response(
        json.dumps(_CUBE_WITH_HOLE_JSON)
    )
    plan(client, "prompt", "claude-sonnet-4-6", _bundle())
    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-4-6"


def test_retry_user_message_carries_error_addendum() -> None:
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_response(json.dumps(_BAD_JSON)),
        _make_response(json.dumps(_CUBE_WITH_HOLE_JSON)),
    ]
    plan(client, "the original prompt", "claude-opus-4-7", _bundle())
    second_call = client.messages.create.call_args_list[1]
    user_content = second_call.kwargs["messages"][0]["content"]
    assert "the original prompt" in user_content
    assert "previous output failed" in user_content


def test_non_json_response_triggers_retry_and_exhausts() -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_response("I cannot help with this.")
    with pytest.raises(PlannerExhausted):
        plan(client, "prompt", "claude-opus-4-7", _bundle())
    assert client.messages.create.call_count == 2


def test_usage_fields_missing_defaults_to_zero() -> None:
    # Defensive against SDK variation (P2a-R5).
    client = MagicMock()
    response = SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(_CUBE_WITH_HOLE_JSON), type="text")],
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )
    client.messages.create.return_value = response
    result = plan(client, "prompt", "claude-opus-4-7", _bundle())
    assert result.tokens.cache_read == 0
    assert result.tokens.cache_creation == 0
    assert result.tokens.input == 100
    assert result.tokens.output == 50
