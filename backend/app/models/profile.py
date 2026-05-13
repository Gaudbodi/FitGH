"""Pydantic v2 Profile + ProfileCreate + ProfileUpdate models.

Phase 2 Plan 02 — Task P2-A.2.

The `profiles` collection is keyed on `clerk_id` (one profile per Clerk user).
We deliberately keep the email/clerk_id pair on the existing `users` collection
(D-STORAGE-NEW-COLLECTIONS) — identity vs body data separation.

T-02-02 (Tampering): `ProfileUpdate` uses `extra="forbid"` so an attacker
cannot smuggle in fields like `clerk_id` or `daily_kcal_target` via PATCH.
T-02-07 (Tampering): server-computed fields (daily_kcal_target,
daily_protein_g_target, floor_hit, privacy_consent_at, created_at,
updated_at, clerk_id) are NEVER read from request bodies — they are stamped
by the route handler.
T-02-08 (Info disclosure): `ProfileCreate` requires `privacy_consent` to be
True via a field_validator; submission with `privacy_consent=False` raises
422 before the row is created.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Sex = Literal["male", "female"]
Locale = Literal["ghana", "diaspora"]
ActivityLevelType = Literal[
    "sedentary",
    "lightly_active",
    "moderately_active",
    "very_active",
    "extra_active",
]
PrimaryGoal = Literal["weight_loss", "muscle_gain"]


# ---------------------------------------------------------------------------
# Full Profile (on-disk shape)
# ---------------------------------------------------------------------------


class Profile(BaseModel):
    """Full Profile document as stored in `profiles` collection."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    clerk_id: str = Field(..., pattern=r"^user_[a-zA-Z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=80)
    sex: Sex
    height_cm: int = Field(..., ge=100, le=230)
    weight_kg: float = Field(..., ge=30.0, le=300.0)
    age: int = Field(..., ge=13, le=100)
    timezone: str = Field(..., min_length=1)
    locale: Locale
    activity_level: ActivityLevelType
    primary_goal: PrimaryGoal
    # Server-computed below.
    daily_kcal_target: int = Field(..., ge=1000, le=10000)
    daily_protein_g_target: int | None = Field(default=None, ge=0, le=600)
    floor_hit: bool = False
    privacy_consent_at: datetime
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ProfileCreate (POST body)
# ---------------------------------------------------------------------------


class ProfileCreate(BaseModel):
    """POST /profile body — what the FE form sends.

    Fields EXCLUDED from this model (because they are server-computed or
    server-stamped):
      - clerk_id (from g.clerk_user_id)
      - daily_kcal_target, daily_protein_g_target, floor_hit (from tdee.py)
      - privacy_consent_at (server timestamp on successful submission)
      - created_at, updated_at (server timestamps)

    Added relative to Profile:
      - privacy_consent: bool (must be True; validator rejects False per
        T-02-08).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=80)
    sex: Sex
    height_cm: int = Field(..., ge=100, le=230)
    weight_kg: float = Field(..., ge=30.0, le=300.0)
    age: int = Field(..., ge=13, le=100)
    timezone: str = Field(..., min_length=1)
    locale: Locale
    activity_level: ActivityLevelType
    primary_goal: PrimaryGoal
    privacy_consent: bool

    @field_validator("privacy_consent")
    @classmethod
    def _consent_must_be_true(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError(
                "privacy_consent must be true; the user must accept the "
                "Anthropic / Clerk / MongoDB Atlas / Render data-processor "
                "disclosure before completing onboarding."
            )
        return v


# ---------------------------------------------------------------------------
# ProfileUpdate (PATCH body)
# ---------------------------------------------------------------------------


class ProfileUpdate(BaseModel):
    """PATCH /profile body — every field optional, unknown fields rejected.

    EXCLUDES `privacy_consent` (cannot be re-toggled — the consent timestamp
    is immutable from this endpoint) AND all server-computed fields. `extra="forbid"`
    enforces this at the Pydantic layer so a forged PATCH with
    `{"clerk_id": "user_attacker"}` returns 422 (T-02-02).
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=80)
    sex: Sex | None = None
    height_cm: int | None = Field(default=None, ge=100, le=230)
    weight_kg: float | None = Field(default=None, ge=30.0, le=300.0)
    age: int | None = Field(default=None, ge=13, le=100)
    timezone: str | None = Field(default=None, min_length=1)
    locale: Locale | None = None
    activity_level: ActivityLevelType | None = None
    primary_goal: PrimaryGoal | None = None
