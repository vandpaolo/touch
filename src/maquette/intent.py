from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Unit = Literal["mm", "cm", "m", "in"]
PrimaryKind = Literal["box", "cylinder", "sphere", "extrude", "revolve", "loft"]
ModifierKind = Literal["hole", "fillet", "chamfer", "shell", "pattern"]


class Parameter(BaseModel):
    name: str
    value: float
    unit: Unit


class PrimaryFeature(BaseModel):
    id: str = Field(..., description="Stable id; modifiers target by id")
    kind: PrimaryKind
    params: dict[str, float | str]


class Modifier(BaseModel):
    id: str
    kind: ModifierKind
    target: str | None = Field(
        default=None,
        description="PrimaryFeature.id this modifier applies to, if applicable",
    )
    params: dict[str, float | str]


class Intent(BaseModel):
    name: str
    description: str
    schema_version: int = 1
    parameters: list[Parameter] = Field(default_factory=list)
    features: list[PrimaryFeature]
    modifiers: list[Modifier] = Field(default_factory=list)
    extras: str | None = Field(
        default=None,
        description="Escape hatch: raw backend code appended after adapter output",
    )

    @model_validator(mode="after")
    def validate_references(self) -> Intent:
        feature_ids = [f.id for f in self.features]
        if len(set(feature_ids)) != len(feature_ids):
            raise ValueError("duplicate feature ids")
        modifier_ids = [m.id for m in self.modifiers]
        if len(set(modifier_ids)) != len(modifier_ids):
            raise ValueError("duplicate modifier ids")
        feature_id_set = set(feature_ids)
        for m in self.modifiers:
            if m.target is not None and m.target not in feature_id_set:
                raise ValueError(
                    f"modifier {m.id!r} targets unknown feature {m.target!r}"
                )
        return self
