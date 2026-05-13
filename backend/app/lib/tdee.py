"""TDEE / kcal-target / protein-target pure functions for FitGH.

Phase 2 Plan 02 — Task P2-A.1.

This module is the contract that `backend/app/routes/profile.py` and
`backend/app/routes/weights.py` consume. The frontend has a TS mirror at
`frontend/src/lib/tdee.ts` (D-SHARED-SCHEMA-MANUAL-MIRROR) — the formulas,
activity factors, kcal floors, and protein factor MUST stay identical.
The end-to-end smoke (P2-F.1) compares the FE preview number against the
BE-persisted number; any divergence is a bug.

Formulas:
  - BMR: Mifflin-St Jeor (1990) — NOT Harris-Benedict, NOT Katch-McArdle.
      male:   10*kg + 6.25*cm - 5*age + 5
      female: 10*kg + 6.25*cm - 5*age - 161
  - TDEE: BMR * activity factor (Mifflin's published 1.2..1.9 range).
  - Daily kcal target:
      weight_loss: TDEE - 500  (≈0.5 kg/wk loss, sustainable)
      muscle_gain: TDEE + 250  (≈0.25 kg/wk gain)
      Floor: 1500 male, 1200 female; clamp + set floor_hit=True.
      Round half-up to integer.
  - Daily protein target (muscle_gain only): round(weight_kg * 1.6).
      weight_loss users get None (no protein card on dashboard).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal, TypedDict

Sex = Literal["male", "female"]
ActivityLevel = Literal[
    "sedentary",
    "lightly_active",
    "moderately_active",
    "very_active",
    "extra_active",
]
PrimaryGoal = Literal["weight_loss", "muscle_gain"]

ACTIVITY_FACTORS: dict[str, float] = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

KCAL_FLOORS: dict[str, int] = {
    "male": 1500,
    "female": 1200,
}

PROTEIN_FACTOR_G_PER_KG: float = 1.6


class KcalTargetResult(TypedDict):
    kcal_target: int
    floor_hit: bool


def _round_half_up(value: float) -> int:
    """Round half-up to integer; Python's default banker's rounding is wrong here."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def bmr_mifflin_st_jeor(
    sex: Sex,
    weight_kg: float,
    height_cm: float,
    age: int,
) -> float:
    """Mifflin-St Jeor basal metabolic rate (kcal/day) — returns float for chained math."""
    if sex == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    if sex == "female":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    raise ValueError(f"invalid sex: {sex!r}")


def tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Total Daily Energy Expenditure = BMR * activity factor."""
    if activity_level not in ACTIVITY_FACTORS:
        raise ValueError(f"invalid activity_level: {activity_level!r}")
    return bmr * ACTIVITY_FACTORS[activity_level]


def daily_kcal_target(
    sex: Sex,
    weight_kg: float,
    height_cm: float,
    age: int,
    activity_level: ActivityLevel,
    primary_goal: PrimaryGoal,
) -> KcalTargetResult:
    """Compute the user's daily kcal target with floor enforcement."""
    if sex not in ("male", "female"):
        raise ValueError(f"invalid sex: {sex!r}")
    if primary_goal not in ("weight_loss", "muscle_gain"):
        raise ValueError(f"invalid primary_goal: {primary_goal!r}")
    # tdee() validates activity_level

    bmr = bmr_mifflin_st_jeor(sex, weight_kg, height_cm, age)
    tdee_kcal = tdee(bmr, activity_level)

    if primary_goal == "weight_loss":
        target = tdee_kcal - 500
    else:  # muscle_gain
        target = tdee_kcal + 250

    floor = KCAL_FLOORS[sex]
    floor_hit = target < floor
    if floor_hit:
        return {"kcal_target": floor, "floor_hit": True}
    return {"kcal_target": _round_half_up(target), "floor_hit": False}


def daily_protein_g_target(
    weight_kg: float,
    primary_goal: PrimaryGoal,
) -> int | None:
    """Protein target in grams/day. Only meaningful for muscle_gain users."""
    if primary_goal not in ("weight_loss", "muscle_gain"):
        raise ValueError(f"invalid primary_goal: {primary_goal!r}")
    if primary_goal != "muscle_gain":
        return None
    return _round_half_up(weight_kg * PROTEIN_FACTOR_G_PER_KG)
