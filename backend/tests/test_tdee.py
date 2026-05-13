"""Tests for app.lib.tdee — Mifflin-St Jeor BMR, TDEE, kcal target, protein target.

Phase 2 Plan 02 — Task P2-A.1.

Pure-function tests; no Flask, no Mongo. Each known-value case was hand-computed
against the published Mifflin-St Jeor formulas; the float assertions use small
tolerances to absorb IEEE-754 rounding without masking real bugs.
"""

from __future__ import annotations

import pytest

from app.lib.tdee import (
    ACTIVITY_FACTORS,
    KCAL_FLOORS,
    bmr_mifflin_st_jeor,
    daily_kcal_target,
    daily_protein_g_target,
    tdee,
)


def test_bmr_male_known_value():
    # 70 kg, 175 cm, 30 y -> 10*70 + 6.25*175 - 5*30 + 5 = 700 + 1093.75 - 150 + 5 = 1648.75
    assert bmr_mifflin_st_jeor("male", 70, 175, 30) == pytest.approx(1648.75)


def test_bmr_female_known_value():
    # 60 kg, 165 cm, 28 y -> 10*60 + 6.25*165 - 5*28 - 161 = 600 + 1031.25 - 140 - 161 = 1330.25
    assert bmr_mifflin_st_jeor("female", 60, 165, 28) == pytest.approx(1330.25)


def test_tdee_all_five_activity_levels_have_correct_factor():
    expected = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9,
    }
    assert ACTIVITY_FACTORS == expected
    bmr = 1500.0
    for level, factor in expected.items():
        assert tdee(bmr, level) == pytest.approx(bmr * factor)


def test_target_weight_loss_subtracts_500():
    # male 80kg 180cm 30y moderately_active weight_loss:
    # BMR = 10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5 = 1780
    # TDEE = 1780 * 1.55 = 2759
    # target = 2759 - 500 = 2259, floor 1500 -> no floor
    result = daily_kcal_target("male", 80, 180, 30, "moderately_active", "weight_loss")
    assert result["floor_hit"] is False
    assert result["kcal_target"] == 2259


def test_target_muscle_gain_adds_250():
    # male 80kg 180cm 30y moderately_active muscle_gain:
    # TDEE = 2759 -> target = 2759 + 250 = 3009
    result = daily_kcal_target("male", 80, 180, 30, "moderately_active", "muscle_gain")
    assert result["floor_hit"] is False
    assert result["kcal_target"] == 3009


def test_floor_kicks_in_for_small_sedentary_female():
    # female 45 kg 155 cm 65 y sedentary weight_loss:
    # BMR = 10*45 + 6.25*155 - 5*65 - 161 = 450 + 968.75 - 325 - 161 = 932.75
    # TDEE = 932.75 * 1.2 = 1119.3
    # target = 1119.3 - 500 = 619.3 -> clamp to 1200, floor_hit=True
    result = daily_kcal_target("female", 45, 155, 65, "sedentary", "weight_loss")
    assert result["floor_hit"] is True
    assert result["kcal_target"] == 1200


def test_floor_kicks_in_for_small_sedentary_male():
    # male 50 kg 160 cm 70 y sedentary weight_loss:
    # BMR = 500 + 1000 - 350 + 5 = 1155
    # TDEE = 1155 * 1.2 = 1386 -> -500 = 886 -> clamp to 1500
    result = daily_kcal_target("male", 50, 160, 70, "sedentary", "weight_loss")
    assert result["floor_hit"] is True
    assert result["kcal_target"] == 1500


def test_floor_not_hit_for_typical_male():
    # Same as test_target_weight_loss_subtracts_500 — just an explicit floor-not-hit check.
    result = daily_kcal_target("male", 80, 180, 30, "moderately_active", "weight_loss")
    assert result["floor_hit"] is False


def test_protein_target_only_for_muscle_gain():
    assert daily_protein_g_target(70, "weight_loss") is None
    assert daily_protein_g_target(70, "muscle_gain") is not None


def test_protein_target_rounds():
    # 70 kg * 1.6 = 112
    assert daily_protein_g_target(70, "muscle_gain") == 112
    # 73.4 kg * 1.6 = 117.44 -> 117
    assert daily_protein_g_target(73.4, "muscle_gain") == 117
    # 73.5 kg * 1.6 = 117.6 -> 118
    assert daily_protein_g_target(73.5, "muscle_gain") == 118


def test_invalid_activity_level_raises_value_error():
    with pytest.raises(ValueError, match="activity_level"):
        tdee(1500.0, "couch_potato")  # type: ignore[arg-type]


def test_invalid_primary_goal_raises_value_error():
    with pytest.raises(ValueError, match="primary_goal"):
        daily_kcal_target("male", 80, 180, 30, "moderately_active", "maintain")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="primary_goal"):
        daily_protein_g_target(80, "maintain")  # type: ignore[arg-type]


def test_invalid_sex_raises_value_error():
    with pytest.raises(ValueError, match="sex"):
        bmr_mifflin_st_jeor("other", 80, 180, 30)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="sex"):
        daily_kcal_target("other", 80, 180, 30, "moderately_active", "weight_loss")  # type: ignore[arg-type]


def test_kcal_floors_match_design():
    assert KCAL_FLOORS == {"male": 1500, "female": 1200}
