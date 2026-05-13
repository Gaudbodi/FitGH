"""Pydantic v2 models for the Phase 4 vision pipeline.

Phase 4 Plan 04 — Task P4-A.1.

The shapes here are the *contract* between the LLM tool-use output, the
Mongo documents that record per-user usage / global spend / corrections,
and the persisted `Meal.ai_metadata` sub-doc that Phase 3 reserved.

There is NEVER a separate `ai_meals` collection — Phase 4 fills the
nullable fields the Phase 3 `Meal` model already declared (kcal_low,
kcal_high, confidence, ai_metadata, source). The day-1 schema is the
forward-compat surface.

T-04-07 (prompt-injection in meal image): `VisionResponse` uses
`extra="forbid"` + bounded numeric ranges so a hostile LLM cannot smuggle
arbitrary fields through the parser.

T-04-05 (client tampering): `AiMetadata` uses `extra="ignore"` so the
/meals POST handler silently drops unknown keys when persisting the meal
under `source == "ai_vision"`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# LLM tool-use output shapes (parsed by app.lib.vision.parse_tool_use_response)
# ---------------------------------------------------------------------------


class VisionComponentRaw(BaseModel):
    """One food component as reported by Claude Sonnet 4.6's tool-use.

    Pre table re-match — `name` is whatever the LLM wrote (possibly
    informal). `kcal_*` are advisory ranges; the persisted `kcal_point` is
    server-computed from the Ghana table (D-TABLE-WINS).

    `extra="forbid"` so the LLM cannot smuggle extra fields the parser
    would otherwise pass through to the persisted Component (T-04-07).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=80)
    kcal_low: int = Field(..., ge=0, le=5000)
    kcal_high: int = Field(..., ge=0, le=5000)
    kcal_point: int = Field(..., ge=0, le=5000)
    portion_g_estimate: int = Field(..., ge=10, le=800)
    confidence: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _kcal_ordering(self):
        if self.kcal_high < self.kcal_low:
            raise ValueError("kcal_high must be >= kcal_low")
        if not (self.kcal_low <= self.kcal_point <= self.kcal_high):
            raise ValueError("kcal_point must lie within [kcal_low, kcal_high]")
        return self


class VisionResponse(BaseModel):
    """Wrapper for the LLM tool-use payload: a list of components.

    Matches the input_schema of ANTHROPIC_TOOL_SCHEMA exactly so
    Pydantic and Anthropic share the same contract.
    """

    model_config = ConfigDict(extra="forbid")

    components: list[VisionComponentRaw] = Field(..., min_length=1, max_length=10)


# ---------------------------------------------------------------------------
# Persisted Mongo document shapes (Phase 4 collections)
# ---------------------------------------------------------------------------


class VisionUsageDoc(BaseModel):
    """One row in `vision_usage` — per-(user_id, date) scan counter.

    Operator-side unique index: `(user_id, date)`. The conditional
    increment `count: {$lt: 8}` in rate_limit.check_and_increment_user_daily
    makes this race-safe (T-04-02).
    """

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., pattern=r"^user_[a-zA-Z0-9_]+$")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    count: int = Field(..., ge=0)
    last_call_at: datetime


class SystemStateDoc(BaseModel):
    """Singleton `system_state` doc with `_id = "vision_budget"`.

    Tracks the global $/day spend + cap. `alert_fired` flips to True the
    first time `spend_usd / DAU > 0.05` on a given UTC day; resets to
    False on day-roll (rate_limit.record_spend handles the rotation).

    Day-rotation is handled by rate_limit; the `date` field carries the
    UTC day-key, and date != today means the doc is stale and a fresh
    one supersedes it.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: Literal["vision_budget"] = Field(default="vision_budget", alias="_id")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    spend_usd: float = Field(..., ge=0.0)
    cap_usd: float = Field(..., ge=0.0)
    alert_fired: bool = Field(default=False)


class UserCorrectionDoc(BaseModel):
    """One row in `user_corrections` — biases next scan's system prompt.

    Operator-side index: `(user_id, corrected_at desc)`.

    `corrected_name` is None when only the portion changed; `corrected_food_id`
    is None when the user picked a free-text label that didn't match a Ghana
    food.
    """

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., pattern=r"^user_[a-zA-Z0-9_]+$")
    original_name: str = Field(..., min_length=1, max_length=80)
    corrected_name: str | None = Field(default=None, max_length=80)
    original_portion_g: int = Field(..., ge=0, le=2000)
    corrected_portion_g: int = Field(..., ge=0, le=2000)
    original_food_id: str | None = Field(default=None, pattern=r"^gh-[a-z0-9-]+$")
    corrected_food_id: str | None = Field(default=None, pattern=r"^gh-[a-z0-9-]+$")
    corrected_at: datetime


# ---------------------------------------------------------------------------
# AiMetadata — matches Phase 3's Meal.ai_metadata reserved sub-doc shape
# ---------------------------------------------------------------------------


class AiMetadata(BaseModel):
    """Persisted alongside a meal when `Meal.source == "ai_vision"`.

    `extra="ignore"` so the POST /meals handler silently drops unknown
    client-supplied keys (T-04-05). The fields here are the only ones
    the server reads/persists.
    """

    model_config = ConfigDict(extra="ignore")

    model: str = Field(..., min_length=1, max_length=80)
    prompt_hash: str = Field(..., min_length=16, max_length=128)
    image_dims: dict = Field(...)
    latency_ms: int = Field(..., ge=0)
    cost_usd: float = Field(..., ge=0.0)


# ---------------------------------------------------------------------------
# Anthropic tool-use schema (programmatic — cannot drift from VisionResponse)
# ---------------------------------------------------------------------------


ANTHROPIC_TOOL_SCHEMA: dict = {
    "name": "report_meal_components",
    "description": (
        "Identify each visible food component on the plate and estimate "
        "kcal range + portion in grams. Always return a kcal range — never "
        "a single point. Match each component to the Ghana food reference "
        "table when confident; otherwise describe the dish in plain English "
        "and the server will fall back to your range midpoint."
    ),
    "input_schema": VisionResponse.model_json_schema(),
}


__all__ = [
    "ANTHROPIC_TOOL_SCHEMA",
    "AiMetadata",
    "SystemStateDoc",
    "UserCorrectionDoc",
    "VisionComponentRaw",
    "VisionResponse",
    "VisionUsageDoc",
]
