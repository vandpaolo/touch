from __future__ import annotations

import math
from dataclasses import FrozenInstanceError

import pytest

from maquette.pricing import ModelPrice, Tokens, known_models, price


def test_opus_phase0_reference_value():
    # Phase-0 doc done-when:
    # price("claude-opus-4-7", Tokens(input=1000, output=500, ...)) ~ $0.0175
    cost = price(
        "claude-opus-4-7",
        Tokens(input=1000, output=500, cache_read=0, cache_creation=0),
    )
    assert math.isclose(cost, 0.0175, rel_tol=1e-9)


def test_sonnet_input_only():
    cost = price(
        "claude-sonnet-4-6",
        Tokens(input=1_000_000, output=0, cache_read=0, cache_creation=0),
    )
    assert math.isclose(cost, 3.00, rel_tol=1e-9)


def test_haiku_output_only():
    cost = price(
        "claude-haiku-4-5",
        Tokens(input=0, output=1_000_000, cache_read=0, cache_creation=0),
    )
    assert math.isclose(cost, 5.00, rel_tol=1e-9)


def test_cache_read_priced_at_one_tenth_of_input():
    # Per ADR 0003: cache_read is ~10% of input cost.
    just_input = price(
        "claude-opus-4-7",
        Tokens(input=10_000, output=0, cache_read=0, cache_creation=0),
    )
    just_cache_read = price(
        "claude-opus-4-7",
        Tokens(input=0, output=0, cache_read=10_000, cache_creation=0),
    )
    assert math.isclose(just_cache_read, just_input * 0.10, rel_tol=1e-9)


def test_cache_creation_priced_above_input():
    # Per ADR 0003: cache_creation is ~1.25x input cost.
    just_input = price(
        "claude-opus-4-7",
        Tokens(input=10_000, output=0, cache_read=0, cache_creation=0),
    )
    just_cache_creation = price(
        "claude-opus-4-7",
        Tokens(input=0, output=0, cache_read=0, cache_creation=10_000),
    )
    assert math.isclose(just_cache_creation, just_input * 1.25, rel_tol=1e-9)


def test_four_token_classes_sum():
    cost = price(
        "claude-opus-4-7",
        Tokens(input=4000, output=540, cache_read=4000, cache_creation=0),
    )
    expected = (4000 * 5.00 + 540 * 25.00 + 4000 * 0.50) / 1_000_000
    assert math.isclose(cost, expected, rel_tol=1e-12)


def test_zero_tokens_is_zero_cost():
    cost = price(
        "claude-opus-4-7",
        Tokens(input=0, output=0, cache_read=0, cache_creation=0),
    )
    assert cost == 0.0


def test_unknown_model_raises_key_error():
    with pytest.raises(KeyError, match="unknown model"):
        price("claude-impossible", Tokens(1, 1, 1, 1))


def test_known_models_returns_three_v0_models():
    models = known_models()
    assert set(models) == {
        "claude-opus-4-7",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
    }


def test_tokens_is_frozen():
    t = Tokens(input=1, output=2, cache_read=3, cache_creation=4)
    with pytest.raises(FrozenInstanceError):
        t.input = 99  # type: ignore[misc]


def test_model_price_is_frozen():
    mp = ModelPrice(1.0, 2.0, 3.0, 4.0)
    with pytest.raises(FrozenInstanceError):
        mp.input_per_mtoken = 99.0  # type: ignore[misc]
