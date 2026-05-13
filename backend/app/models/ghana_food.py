"""Pydantic v2 GhanaFood + PortionDefault models (Phase 3, Task P3-A.1).

The `ghana_foods` collection is a read-only catalogue keyed on `food_id`
(e.g. `gh-jollof-rice`). Entries are sourced from FAO/INFOODS WAFCT (West
African Food Composition Table) directly where possible, and from
WAFCT-component summation (tagged `wafct_composite`) for composite Ghanaian
dishes such as jollof rice, waakye, kontomire, shito.

Source-of-truth: this Pydantic model. The JSON Schema at
`shared/schemas/ghana-food.schema.json` is generated from `model_json_schema()`;
the FE Zod mirror at `frontend/src/lib/zod-schemas.ts` is hand-maintained per
D-SHARED-SCHEMA-MANUAL-MIRROR (Phase 2 inheritance).

Per CONTEXT.md "Implementation Decisions": macro percentages do NOT need to
sum to 100 (water / ash / fibre balance), so no cross-field validator on the
macro fields. Range bounds (0..100 g/100g for protein, fat, carbs;
0..900 kcal/100g) are biology-plausibility caps.

`extra="forbid"` so a typo in a seed JSON field name fails loudly at load
time rather than silently dropping data.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["staple", "soup_stew", "protein", "side_snack"]
FoodSource = Literal["wafct", "wafct_composite", "usda"]
SourceConfidence = Literal["high", "medium", "low"]


class PortionDefault(BaseModel):
    """One culturally meaningful portion entry for a Ghana food.

    The FIRST entry in a food's `portion_defaults` list is the Ghana-cultural
    canonical portion (e.g. "1 ball of banku" = 200 g); subsequent entries are
    diaspora alternatives (e.g. "1 cup" = 200 g, "100 g" = 100 g).
    """

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., min_length=1, max_length=40)
    grams: int = Field(..., ge=1, le=2000)


class GhanaFood(BaseModel):
    """Full GhanaFood document as stored in `ghana_foods` collection."""

    model_config = ConfigDict(extra="forbid")

    food_id: str = Field(..., pattern=r"^gh-[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=80)
    alt_names: list[str] = Field(default_factory=list, max_length=10)
    kcal_per_100g: float = Field(..., ge=0.0, le=900.0)
    protein_g_per_100g: float = Field(..., ge=0.0, le=100.0)
    fat_g_per_100g: float = Field(..., ge=0.0, le=100.0)
    carbs_g_per_100g: float = Field(..., ge=0.0, le=100.0)
    portion_defaults: list[PortionDefault] = Field(..., min_length=1, max_length=6)
    category: Category
    source: FoodSource
    source_confidence: SourceConfidence
