"""Tests for Pydantic GhanaFood + Meal models (Phase 3, Tasks P3-A.1 and P3-A.2).

The file is shared between A.1 (GhanaFood + PortionDefault) and A.2
(Meal + Component + MealCreate + MealUpdate) because the two models form a
cohesive domain.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# P3-A.1: GhanaFood + PortionDefault
# ---------------------------------------------------------------------------


def _valid_food_kwargs(**overrides) -> dict:
    base = {
        "food_id": "gh-jollof-rice",
        "name": "Jollof rice",
        "alt_names": ["jollof"],
        "kcal_per_100g": 165.0,
        "protein_g_per_100g": 4.0,
        "fat_g_per_100g": 5.0,
        "carbs_g_per_100g": 28.0,
        "portion_defaults": [{"label": "1 plate", "grams": 350}],
        "category": "staple",
        "source": "wafct_composite",
        "source_confidence": "medium",
    }
    base.update(overrides)
    return base


def test_ghana_food_food_id_pattern_rejected_for_uppercase():
    from app.models.ghana_food import GhanaFood

    with pytest.raises(ValidationError):
        GhanaFood(**_valid_food_kwargs(food_id="GH-Jollof"))


def test_ghana_food_food_id_pattern_rejected_for_underscores():
    from app.models.ghana_food import GhanaFood

    with pytest.raises(ValidationError):
        GhanaFood(**_valid_food_kwargs(food_id="gh_jollof_rice"))


def test_ghana_food_portion_defaults_must_have_at_least_one():
    from app.models.ghana_food import GhanaFood

    with pytest.raises(ValidationError):
        GhanaFood(**_valid_food_kwargs(portion_defaults=[]))


def test_ghana_food_category_enum_rejects_unknown():
    from app.models.ghana_food import GhanaFood

    with pytest.raises(ValidationError):
        GhanaFood(**_valid_food_kwargs(category="dessert"))


def test_ghana_food_source_enum_rejects_unknown():
    from app.models.ghana_food import GhanaFood

    with pytest.raises(ValidationError):
        GhanaFood(**_valid_food_kwargs(source="madeup"))


def test_ghana_food_extra_field_rejected():
    from app.models.ghana_food import GhanaFood

    with pytest.raises(ValidationError):
        GhanaFood(**_valid_food_kwargs(extra_field="surprise"))


def test_portion_default_grams_range_rejected_at_zero():
    from app.models.ghana_food import PortionDefault

    with pytest.raises(ValidationError):
        PortionDefault(label="empty plate", grams=0)


def test_ghana_food_valid_round_trip():
    from app.models.ghana_food import GhanaFood

    food = GhanaFood(**_valid_food_kwargs())
    assert food.food_id == "gh-jollof-rice"
    assert food.portion_defaults[0].grams == 350


# ---------------------------------------------------------------------------
# P3-A.2: Meal + Component + MealCreate + MealUpdate
# ---------------------------------------------------------------------------


def test_component_create_matched_path_validates():
    from app.models.meal import ComponentCreate

    cc = ComponentCreate(food_id="gh-jollof-rice", portion_g=350)
    assert cc.food_id == "gh-jollof-rice"
    assert cc.kcal_point is None


def test_component_create_free_text_path_validates():
    from app.models.meal import ComponentCreate

    cc = ComponentCreate(name="Beans on toast", portion_g=200, kcal_point=280)
    assert cc.food_id is None
    assert cc.kcal_point == 280


def test_component_create_neither_path_rejected_422():
    from app.models.meal import ComponentCreate

    with pytest.raises(ValidationError):
        ComponentCreate(portion_g=200)


def test_component_create_both_paths_rejected_422():
    from app.models.meal import ComponentCreate

    with pytest.raises(ValidationError):
        ComponentCreate(food_id="gh-jollof-rice", portion_g=200, kcal_point=500)


def test_component_create_portion_g_step_not_enforced_at_model_level():
    """The 10g step is a UI / route concern; the model accepts any 10..800."""
    from app.models.ghana_food import GhanaFood  # noqa: F401
    from app.models.meal import ComponentCreate

    # 137 is not a multiple of 10 but the model should accept it.
    cc = ComponentCreate(food_id="gh-jollof-rice", portion_g=137)
    assert cc.portion_g == 137


def test_component_create_portion_g_out_of_range():
    from app.models.meal import ComponentCreate

    with pytest.raises(ValidationError):
        ComponentCreate(food_id="gh-jollof-rice", portion_g=5)
    with pytest.raises(ValidationError):
        ComponentCreate(food_id="gh-jollof-rice", portion_g=801)


def test_component_create_free_text_requires_name():
    from app.models.meal import ComponentCreate

    with pytest.raises(ValidationError):
        ComponentCreate(portion_g=200, kcal_point=280)


def test_meal_create_rejects_empty_components():
    from app.models.meal import MealCreate

    with pytest.raises(ValidationError):
        MealCreate(components=[])


def test_meal_create_rejects_too_many_components():
    from app.models.meal import ComponentCreate, MealCreate

    too_many = [
        ComponentCreate(food_id="gh-jollof-rice", portion_g=100) for _ in range(11)
    ]
    with pytest.raises(ValidationError):
        MealCreate(components=too_many)


def test_meal_create_rejects_unknown_field():
    from app.models.meal import MealCreate

    with pytest.raises(ValidationError):
        MealCreate(
            components=[{"food_id": "gh-jollof-rice", "portion_g": 200}],
            total_kcal=99999,
        )


def test_meal_create_rejects_user_id_in_body():
    """T-03-01: a forged user_id in the body must be rejected (extra=forbid)."""
    from app.models.meal import MealCreate

    with pytest.raises(ValidationError):
        MealCreate(
            components=[{"food_id": "gh-jollof-rice", "portion_g": 200}],
            user_id="user_attacker",
        )


def test_meal_update_components_optional():
    from app.models.meal import MealUpdate

    upd = MealUpdate()
    assert upd.logged_at is None
    assert upd.components is None


def test_meal_update_rejects_unknown_field():
    from app.models.meal import MealUpdate

    with pytest.raises(ValidationError):
        MealUpdate(total_kcal=12345)


def test_meal_update_components_empty_rejected():
    """min_length=1 when present."""
    from app.models.meal import MealUpdate

    with pytest.raises(ValidationError):
        MealUpdate(components=[])


def test_meal_serializes_ai_metadata_none_as_null():
    """Forward-compat for Phase 4: ai_metadata=None survives a model dump."""
    from app.models.meal import Component, Meal

    now = datetime.now(UTC)
    m = Meal(
        user_id="user_test",
        logged_at=now,
        source="manual",
        components=[
            Component(
                name="Jollof rice",
                matched_food_id="gh-jollof-rice",
                portion_g=350,
                kcal_low=None,
                kcal_high=None,
                kcal_point=578,
                protein_g_point=14,
                confidence=None,
                source="table",
            )
        ],
        total_kcal=578,
        total_protein_g=14,
        ai_metadata=None,
        created_at=now,
        updated_at=now,
    )
    dumped = m.model_dump()
    assert dumped["ai_metadata"] is None
    assert dumped["components"][0]["kcal_low"] is None
    assert dumped["components"][0]["kcal_high"] is None
    assert dumped["components"][0]["confidence"] is None
