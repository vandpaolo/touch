from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Tokens:
    input: int
    output: int
    cache_read: int
    cache_creation: int


@dataclass(frozen=True)
class ModelPrice:
    input_per_mtoken: float
    output_per_mtoken: float
    cache_read_per_mtoken: float
    cache_creation_per_mtoken: float


_MTOKEN: Final[int] = 1_000_000

_TABLE: Final[dict[str, ModelPrice]] = {
    "claude-opus-4-7": ModelPrice(
        input_per_mtoken=5.00,
        output_per_mtoken=25.00,
        cache_read_per_mtoken=0.50,
        cache_creation_per_mtoken=6.25,
    ),
    "claude-sonnet-4-6": ModelPrice(
        input_per_mtoken=3.00,
        output_per_mtoken=15.00,
        cache_read_per_mtoken=0.30,
        cache_creation_per_mtoken=3.75,
    ),
    "claude-haiku-4-5": ModelPrice(
        input_per_mtoken=1.00,
        output_per_mtoken=5.00,
        cache_read_per_mtoken=0.10,
        cache_creation_per_mtoken=1.25,
    ),
}


def price(model: str, tokens: Tokens) -> float:
    try:
        p = _TABLE[model]
    except KeyError as e:
        raise KeyError(f"unknown model {model!r}; known: {sorted(_TABLE)}") from e
    return (
        tokens.input * p.input_per_mtoken
        + tokens.output * p.output_per_mtoken
        + tokens.cache_read * p.cache_read_per_mtoken
        + tokens.cache_creation * p.cache_creation_per_mtoken
    ) / _MTOKEN


def known_models() -> tuple[str, ...]:
    return tuple(_TABLE)
