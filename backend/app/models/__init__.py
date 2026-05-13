"""Pydantic v2 models for FitGH MongoDB documents.

Phase 2 Plan 02 — Task P2-A.2.
Phase 3 Plan 03 — Tasks P3-A.1 and P3-A.2 add GhanaFood, Meal et al.

Pattern: each Mongo document has a full `Foo` model (the on-disk shape) and a
`FooCreate` / `FooUpdate` model for inbound request bodies. Server-computed
fields (clerk_id, created_at, daily_kcal_target, total_kcal, ...) are
EXCLUDED from Create/Update so a client cannot forge them (T-02-02, T-02-07,
T-03-01, T-03-02).
"""

from app.models.ghana_food import (
    Category,
    FoodSource,
    GhanaFood,
    PortionDefault,
    SourceConfidence,
)
from app.models.meal import (
    Component,
    ComponentCreate,
    ComponentSource,
    Meal,
    MealCreate,
    MealSource,
    MealUpdate,
)
from app.models.profile import (
    ActivityLevelType,
    Locale,
    PrimaryGoal,
    Profile,
    ProfileCreate,
    ProfileUpdate,
    Sex,
)
from app.models.vision import (
    ANTHROPIC_TOOL_SCHEMA,
    AiMetadata,
    SystemStateDoc,
    UserCorrectionDoc,
    VisionComponentRaw,
    VisionResponse,
    VisionUsageDoc,
)
from app.models.weight_log import WeightLog, WeightLogCreate

__all__ = [
    "ANTHROPIC_TOOL_SCHEMA",
    "ActivityLevelType",
    "AiMetadata",
    "Category",
    "Component",
    "ComponentCreate",
    "ComponentSource",
    "FoodSource",
    "GhanaFood",
    "Locale",
    "Meal",
    "MealCreate",
    "MealSource",
    "MealUpdate",
    "PortionDefault",
    "PrimaryGoal",
    "Profile",
    "ProfileCreate",
    "ProfileUpdate",
    "Sex",
    "SourceConfidence",
    "SystemStateDoc",
    "UserCorrectionDoc",
    "VisionComponentRaw",
    "VisionResponse",
    "VisionUsageDoc",
    "WeightLog",
    "WeightLogCreate",
]
