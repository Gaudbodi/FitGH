"""Pydantic v2 Meal + Component + MealCreate + MealUpdate models.

Phase 3 Plan 03 — Task P3-A.2.

The `meals` collection stores the FULL multi-component shape from day 1
(ROADMAP Hard Constraint #3). Vision-only fields (`Component.kcal_low`,
`Component.kcal_high`, `Component.confidence`, `Meal.ai_metadata`) are
persisted as `None` from Phase 3 manual-log writes; Phase 4 fills them in
without a schema change.

There is NEVER a separate `ai_meals` collection. The day-1 schema is the
forward-compat surface.

T-03-01 (Spoofing): `MealCreate` uses `extra="forbid"` so a forged
`{"user_id": "user_attacker"}` is rejected with 422.
T-03-02 (Tampering): the `kcal_point` field on `ComponentCreate` is ONLY
accepted in the free-text path (matched_food_id is None). For matched
components the server computes kcal_point from the catalogue; the request
shape simply does not surface a place to inject one.
T-03-04 (Tampering): `logged_at` backdate validation is enforced at the
route layer (it depends on `datetime.now`); the model accepts any datetime.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MealSource = Literal["manual", "ai_vision"]
ComponentSource = Literal["table", "llm_then_table_rematch", "user_corrected"]


# ---------------------------------------------------------------------------
# Persisted shapes (on-disk)
# ---------------------------------------------------------------------------


class Component(BaseModel):
    """Embedded sub-document inside `Meal.components`.

    `name` is copied from `GhanaFood.name` at write time for matched
    components so deletions from the catalogue do not break history.
    `kcal_low / kcal_high / confidence` are vision-only fields — Phase 3
    writes them as None; Phase 4 fills them.
    """

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, max_length=80)
    matched_food_id: str | None = Field(default=None)
    portion_g: int = Field(..., ge=10, le=800)
    kcal_low: int | None = Field(default=None)
    kcal_high: int | None = Field(default=None)
    kcal_point: int = Field(..., ge=0, le=5000)
    protein_g_point: int = Field(..., ge=0, le=600)
    confidence: float | None = Field(default=None)
    source: ComponentSource


class Meal(BaseModel):
    """Full Meal document as stored in `meals` collection."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., pattern=r"^user_[a-zA-Z0-9_]+$")
    logged_at: datetime
    source: MealSource
    components: list[Component] = Field(..., min_length=1, max_length=10)
    total_kcal: int = Field(..., ge=0)
    total_protein_g: int = Field(..., ge=0)
    ai_metadata: dict | None = Field(default=None)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Request body shapes
# ---------------------------------------------------------------------------


class ComponentCreate(BaseModel):
    """One component as supplied in a POST/PATCH /meals body.

    Two valid shapes (enforced by `_exactly_one_path`):
      - Matched: {food_id, portion_g} — server resolves food_id against
        ghana_foods, copies name + computes kcal_point + protein_g_point.
      - Free-text: {name, portion_g, kcal_point} — user supplied kcal value;
        protein_g_point is unknown (set to 0).

    `extra="forbid"` so a matched-component body cannot smuggle in a
    client-supplied kcal_point (T-03-02): the field is declared on this model
    but the validator enforces it is None in the matched path.
    """

    model_config = ConfigDict(extra="forbid")

    food_id: str | None = Field(default=None, pattern=r"^gh-[a-z0-9-]+$")
    name: str | None = Field(default=None, min_length=1, max_length=80)
    portion_g: int = Field(..., ge=10, le=800)
    kcal_point: int | None = Field(default=None, ge=0, le=5000)

    @model_validator(mode="after")
    def _exactly_one_path(self):
        matched = self.food_id is not None
        freetext = self.kcal_point is not None
        if matched == freetext:
            raise ValueError(
                "supply exactly one of {food_id, portion_g} or "
                "{name, portion_g, kcal_point}"
            )
        if freetext and self.name is None:
            raise ValueError("free-text component requires name")
        return self


class MealCreate(BaseModel):
    """POST /meals body."""

    model_config = ConfigDict(extra="forbid")

    logged_at: datetime | None = Field(default=None)
    components: list[ComponentCreate] = Field(..., min_length=1, max_length=10)


class MealUpdate(BaseModel):
    """PATCH /meals/<id> body.

    Per D-PATCH-REPLACES-COMPONENTS (CONTEXT decision): when `components`
    is supplied, the server replaces the array atomically. The FE always
    re-sends the FULL edited components list — there is no per-component
    partial merge.
    """

    model_config = ConfigDict(extra="forbid")

    logged_at: datetime | None = Field(default=None)
    components: list[ComponentCreate] | None = Field(
        default=None, min_length=1, max_length=10
    )
