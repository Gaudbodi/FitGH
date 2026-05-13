"""Pydantic v2 models for FitGH MongoDB documents.

Phase 2 Plan 02 — Task P2-A.2.

Pattern: each Mongo document has a full `Foo` model (the on-disk shape) and a
`FooCreate` / `FooUpdate` model for inbound request bodies. Server-computed
fields (clerk_id, created_at, daily_kcal_target, ...) are EXCLUDED from
Create/Update so a client cannot forge them (T-02-02, T-02-07).
"""

from app.models.profile import (
    ActivityLevelType,
    Locale,
    PrimaryGoal,
    Profile,
    ProfileCreate,
    ProfileUpdate,
    Sex,
)
from app.models.weight_log import WeightLog, WeightLogCreate

__all__ = [
    "ActivityLevelType",
    "Locale",
    "PrimaryGoal",
    "Profile",
    "ProfileCreate",
    "ProfileUpdate",
    "Sex",
    "WeightLog",
    "WeightLogCreate",
]
