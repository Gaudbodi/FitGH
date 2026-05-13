"""Tests for app.models.profile and app.models.weight_log.

Phase 2 Plan 02 — Task P2-A.2.

Pure Pydantic-validation tests; no Flask, no Mongo. Asserts the security
invariants from the threat register at the schema layer:
  - T-02-02 (Tampering): ProfileUpdate rejects unknown fields (extra=forbid).
  - T-02-07 (Tampering): server-computed fields cannot leak through
    ProfileCreate / ProfileUpdate (they aren't on the model).
  - T-02-08 (Info disclosure): ProfileCreate rejects privacy_consent=False.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.profile import (
    Profile,
    ProfileCreate,
    ProfileUpdate,
)
from app.models.weight_log import WeightLogCreate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_create_payload(**overrides) -> dict:
    base = {
        "name": "Ama Boateng",
        "sex": "female",
        "height_cm": 165,
        "weight_kg": 60.5,
        "age": 28,
        "timezone": "Africa/Accra",
        "locale": "ghana",
        "activity_level": "moderately_active",
        "primary_goal": "weight_loss",
        "privacy_consent": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# ProfileCreate
# ---------------------------------------------------------------------------


def test_profile_create_accepts_valid_payload():
    p = ProfileCreate.model_validate(_valid_create_payload())
    assert p.name == "Ama Boateng"
    assert p.privacy_consent is True


def test_profile_create_rejects_consent_false():
    with pytest.raises(ValidationError) as exc_info:
        ProfileCreate.model_validate(_valid_create_payload(privacy_consent=False))
    # The error must mention privacy_consent for the FE to render a useful hint.
    assert "privacy_consent" in str(exc_info.value)


def test_profile_create_rejects_unknown_field():
    # Extra fields like a forged daily_kcal_target must be rejected at the
    # schema layer (T-02-07).
    with pytest.raises(ValidationError) as exc_info:
        ProfileCreate.model_validate(
            _valid_create_payload(daily_kcal_target=99999)
        )
    assert "daily_kcal_target" in str(exc_info.value)


# ---------------------------------------------------------------------------
# ProfileUpdate
# ---------------------------------------------------------------------------


def test_profile_update_accepts_partial_payload():
    p = ProfileUpdate.model_validate({"weight_kg": 62.0})
    assert p.weight_kg == 62.0
    assert p.name is None  # unset fields default to None


def test_profile_update_rejects_unknown_field():
    # T-02-02: an attacker PATCH'ing {clerk_id: "user_attacker"} must 422.
    with pytest.raises(ValidationError) as exc_info:
        ProfileUpdate.model_validate({"clerk_id": "user_attacker"})
    assert "clerk_id" in str(exc_info.value)


def test_profile_update_rejects_clerk_id_field():
    with pytest.raises(ValidationError):
        ProfileUpdate.model_validate({"clerk_id": "user_xxx"})


def test_profile_update_rejects_daily_kcal_target_field():
    # T-02-07: server-computed kcal target cannot be set by the client.
    with pytest.raises(ValidationError):
        ProfileUpdate.model_validate({"daily_kcal_target": 99999})


def test_profile_update_rejects_privacy_consent_at_field():
    # Consent timestamp is immutable from the endpoint.
    with pytest.raises(ValidationError):
        ProfileUpdate.model_validate({"privacy_consent_at": "2026-01-01T00:00:00Z"})


def test_profile_update_rejects_privacy_consent_field():
    # Consent itself cannot be re-toggled from PATCH.
    with pytest.raises(ValidationError):
        ProfileUpdate.model_validate({"privacy_consent": False})


# ---------------------------------------------------------------------------
# Range validators on Create
# ---------------------------------------------------------------------------


def test_height_out_of_range_rejected():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(height_cm=80))
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(height_cm=300))


def test_weight_out_of_range_rejected():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(weight_kg=10.0))
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(weight_kg=500.0))


def test_age_out_of_range_rejected():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(age=10))
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(age=120))


def test_invalid_sex_rejected():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(sex="other"))


def test_invalid_locale_rejected():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(locale="other"))


def test_invalid_activity_level_rejected():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(
            _valid_create_payload(activity_level="couch_potato")
        )


def test_invalid_primary_goal_rejected():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(
            _valid_create_payload(primary_goal="maintain")
        )


def test_name_length_validated():
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(name=""))
    with pytest.raises(ValidationError):
        ProfileCreate.model_validate(_valid_create_payload(name="x" * 81))


# ---------------------------------------------------------------------------
# Profile (full doc) round-trip
# ---------------------------------------------------------------------------


def test_profile_round_trips_full_doc():
    now = datetime.now(UTC)
    doc = {
        "clerk_id": "user_test_abc",
        "name": "Ama Boateng",
        "sex": "female",
        "height_cm": 165,
        "weight_kg": 60.5,
        "age": 28,
        "timezone": "Africa/Accra",
        "locale": "ghana",
        "activity_level": "moderately_active",
        "primary_goal": "muscle_gain",
        "daily_kcal_target": 2150,
        "daily_protein_g_target": 97,
        "floor_hit": False,
        "privacy_consent_at": now,
        "created_at": now,
        "updated_at": now,
    }
    p = Profile.model_validate(doc)
    # Serialize and re-validate
    serialized = p.model_dump(mode="json")
    assert serialized["clerk_id"] == "user_test_abc"
    assert serialized["daily_protein_g_target"] == 97
    assert serialized["floor_hit"] is False


def test_profile_clerk_id_pattern_enforced():
    now = datetime.now(UTC)
    bad = {
        "clerk_id": "not_a_clerk_id",
        "name": "x",
        "sex": "male",
        "height_cm": 180,
        "weight_kg": 80.0,
        "age": 30,
        "timezone": "Africa/Accra",
        "locale": "ghana",
        "activity_level": "sedentary",
        "primary_goal": "weight_loss",
        "daily_kcal_target": 2000,
        "daily_protein_g_target": None,
        "floor_hit": False,
        "privacy_consent_at": now,
        "created_at": now,
        "updated_at": now,
    }
    with pytest.raises(ValidationError):
        Profile.model_validate(bad)


# ---------------------------------------------------------------------------
# WeightLogCreate
# ---------------------------------------------------------------------------


def test_weight_log_kg_range():
    # Accepts 20..400
    WeightLogCreate.model_validate({"kg": 20.0})
    WeightLogCreate.model_validate({"kg": 400.0})
    WeightLogCreate.model_validate({"kg": 70.5})
    # Rejects below 20 and above 400
    with pytest.raises(ValidationError):
        WeightLogCreate.model_validate({"kg": 5.0})
    with pytest.raises(ValidationError):
        WeightLogCreate.model_validate({"kg": 500.0})


def test_weight_log_rejects_unknown_field():
    # T-02-04 doesn't strictly require this, but extra=forbid here keeps the
    # surface tight in case an attacker tries {"user_id": "..."} via the BFF.
    with pytest.raises(ValidationError):
        WeightLogCreate.model_validate({"kg": 70.0, "user_id": "user_attacker"})
