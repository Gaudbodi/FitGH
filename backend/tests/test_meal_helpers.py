"""Tests for app.lib.meals — pure-function kcal/protein helpers.

Phase 3 Plan 03 — Task P3-A.3.
"""

from __future__ import annotations


def test_compute_kcal_known_values():
    from app.lib.meals import compute_kcal_for_component

    # 165 kcal/100g * 250 g = 412.5 -> banker's round -> 412.
    assert compute_kcal_for_component(165.0, 250) == 412
    # 130 kcal/100g * 200 g = 260 -> exact integer.
    assert compute_kcal_for_component(130.0, 200) == 260


def test_compute_kcal_rounds_half_to_even():
    from app.lib.meals import compute_kcal_for_component

    # 100.0 kcal/100g * 5 g = 5.0 -> exact 5 (no rounding).
    assert compute_kcal_for_component(100.0, 5) == 5
    # 0.5 -> 0 (round half-to-even).
    # 1 kcal/100g * 50 g = 0.5 -> banker's even -> 0.
    assert compute_kcal_for_component(1.0, 50) == 0
    # 3 kcal/100g * 50 g = 1.5 -> banker's even -> 2.
    assert compute_kcal_for_component(3.0, 50) == 2


def test_compute_kcal_zero_portion_returns_zero():
    from app.lib.meals import compute_kcal_for_component

    assert compute_kcal_for_component(165.0, 0) == 0


def test_compute_protein_known_values():
    from app.lib.meals import compute_protein_for_component

    # 4 g/100g * 350 g = 14 g of protein.
    assert compute_protein_for_component(4.0, 350) == 14
    # 22 g/100g * 250 g = 55 g.
    assert compute_protein_for_component(22.0, 250) == 55


def test_recompute_totals_empty_list_returns_zero_zero():
    from app.lib.meals import recompute_meal_totals

    assert recompute_meal_totals([]) == (0, 0)


def test_recompute_totals_three_components_sums():
    from app.lib.meals import recompute_meal_totals

    components = [
        {"kcal_point": 400, "protein_g_point": 8},
        {"kcal_point": 250, "protein_g_point": 30},
        {"kcal_point": 60, "protein_g_point": 1},
    ]
    assert recompute_meal_totals(components) == (710, 39)


def test_constants_match_ui_contract():
    from app.lib.meals import (
        BACKDATE_MAX_DAYS,
        PORTION_MAX_G,
        PORTION_MIN_G,
        PORTION_STEP_G,
    )

    assert PORTION_MIN_G == 10
    assert PORTION_MAX_G == 800
    assert PORTION_STEP_G == 10
    assert BACKDATE_MAX_DAYS == 7
