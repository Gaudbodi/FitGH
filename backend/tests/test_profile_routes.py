"""Tests for /profile (GET / POST / PATCH).

Phase 2 Plan 02 — Task P2-A.3.

Authenticated paths use the `_stub_clerk_signed_in` helper from test_me.py's
pattern (re-implemented here so the test files stay independent).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace


def _stub_clerk_signed_in(
    monkeypatch,
    *,
    clerk_user_id: str = "user_test_profile",
    clerk_email: str | None = "p@example.com",
) -> None:
    import app.middleware.auth as auth_mod

    payload = {"sub": clerk_user_id}
    if clerk_email:
        payload["email"] = clerk_email

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload=payload,
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


def _valid_create_body(**overrides) -> dict:
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
# GET /profile
# ---------------------------------------------------------------------------


def test_get_profile_401_when_unauthenticated(client):
    r = client.get("/profile")
    assert r.status_code == 401


def test_get_profile_404_when_absent(client, mongo_collections, monkeypatch):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_absent")
    r = client.get("/profile", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 404
    assert r.get_json()["error"] == "profile_not_found"


def test_get_profile_returns_doc(client, mongo_collections, monkeypatch):
    now = datetime.now(UTC)
    mongo_collections.profiles.insert_one({
        "clerk_id": "user_test_alice",
        "name": "Alice",
        "sex": "female",
        "height_cm": 165,
        "weight_kg": 60.0,
        "age": 28,
        "timezone": "Africa/Accra",
        "locale": "ghana",
        "activity_level": "sedentary",
        "primary_goal": "weight_loss",
        "daily_kcal_target": 1500,
        "daily_protein_g_target": None,
        "floor_hit": True,
        "privacy_consent_at": now,
        "created_at": now,
        "updated_at": now,
    })
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_alice")

    r = client.get("/profile", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["clerk_id"] == "user_test_alice"
    assert body["daily_kcal_target"] == 1500
    assert body["floor_hit"] is True


# ---------------------------------------------------------------------------
# POST /profile
# ---------------------------------------------------------------------------


def test_post_profile_creates_and_computes_targets(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_new")
    body = _valid_create_body(
        sex="male",
        weight_kg=80.0,
        height_cm=180,
        age=30,
        activity_level="moderately_active",
        primary_goal="weight_loss",
    )
    r = client.post(
        "/profile",
        data=json.dumps(body),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 201, r.get_data(as_text=True)
    out = r.get_json()
    # 10*80 + 6.25*180 - 5*30 + 5 = 1780; * 1.55 = 2759; -500 = 2259
    assert out["daily_kcal_target"] == 2259
    assert out["daily_protein_g_target"] is None  # weight_loss
    assert out["floor_hit"] is False
    assert out["clerk_id"] == "user_test_new"
    assert "privacy_consent_at" in out
    # Doc actually persisted
    doc = mongo_collections.profiles.find_one({"clerk_id": "user_test_new"})
    assert doc is not None
    assert doc["daily_kcal_target"] == 2259


def test_post_profile_rejects_consent_false_422(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_noconsent")
    body = _valid_create_body(privacy_consent=False)
    r = client.post(
        "/profile",
        data=json.dumps(body),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 422
    assert r.get_json()["error"] == "validation_error"
    # No doc created
    assert mongo_collections.profiles.find_one({"clerk_id": "user_test_noconsent"}) is None


def test_post_profile_ignores_client_supplied_kcal_target(
    client, mongo_collections, monkeypatch
):
    """T-02-07: a forged daily_kcal_target in the body must be rejected (422)
    by the extra='forbid' on ProfileCreate. The server-computed value is
    the only one that lands in the DB."""
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_forge")
    body = _valid_create_body()
    body["daily_kcal_target"] = 99999  # forged
    r = client.post(
        "/profile",
        data=json.dumps(body),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 422


def test_post_profile_floor_hit_sets_disclaimer_flag(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_floor")
    body = _valid_create_body(
        sex="female",
        weight_kg=45.0,
        height_cm=155,
        age=65,
        activity_level="sedentary",
        primary_goal="weight_loss",
    )
    r = client.post(
        "/profile",
        data=json.dumps(body),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 201
    out = r.get_json()
    assert out["floor_hit"] is True
    assert out["daily_kcal_target"] == 1200


def test_post_profile_muscle_gain_computes_protein_target(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_muscle")
    body = _valid_create_body(
        sex="male",
        weight_kg=80.0,
        height_cm=180,
        age=30,
        activity_level="moderately_active",
        primary_goal="muscle_gain",
    )
    r = client.post(
        "/profile",
        data=json.dumps(body),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 201
    out = r.get_json()
    # 80 * 1.6 = 128
    assert out["daily_protein_g_target"] == 128
    # TDEE + 250 = 3009
    assert out["daily_kcal_target"] == 3009


def test_post_profile_weight_loss_protein_target_none(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_wl")
    body = _valid_create_body(primary_goal="weight_loss")
    r = client.post(
        "/profile",
        data=json.dumps(body),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 201
    assert r.get_json()["daily_protein_g_target"] is None


# ---------------------------------------------------------------------------
# PATCH /profile
# ---------------------------------------------------------------------------


def _seed_profile(mongo_collections, clerk_id: str, **overrides) -> None:
    now = datetime.now(UTC)
    base = {
        "clerk_id": clerk_id,
        "name": "Seeded",
        "sex": "male",
        "height_cm": 180,
        "weight_kg": 80.0,
        "age": 30,
        "timezone": "Africa/Accra",
        "locale": "ghana",
        "activity_level": "moderately_active",
        "primary_goal": "weight_loss",
        "daily_kcal_target": 2259,
        "daily_protein_g_target": None,
        "floor_hit": False,
        "privacy_consent_at": now,
        "created_at": now,
        "updated_at": now,
    }
    base.update(overrides)
    mongo_collections.profiles.insert_one(base)


def test_patch_profile_recomputes_targets_on_weight_change(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_test_patch1")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_patch1")

    r = client.patch(
        "/profile",
        data=json.dumps({"weight_kg": 90.0}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    out = r.get_json()
    # BMR = 10*90 + 6.25*180 - 5*30 + 5 = 900 + 1125 - 150 + 5 = 1880
    # TDEE = 1880 * 1.55 = 2914
    # target = 2914 - 500 = 2414
    assert out["weight_kg"] == 90.0
    assert out["daily_kcal_target"] == 2414


def test_patch_profile_rejects_unknown_field_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_test_patch2")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_patch2")

    # T-02-02: forged clerk_id must 422 via Pydantic extra=forbid
    r = client.patch(
        "/profile",
        data=json.dumps({"clerk_id": "user_attacker"}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 422
    # Existing profile untouched
    doc = mongo_collections.profiles.find_one({"clerk_id": "user_test_patch2"})
    assert doc is not None
    # And no doc was created for the attacker id
    assert mongo_collections.profiles.find_one({"clerk_id": "user_attacker"}) is None


def test_patch_profile_404_when_no_profile(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_no_profile")
    r = client.patch(
        "/profile",
        data=json.dumps({"weight_kg": 70.0}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 404


def test_patch_profile_switch_to_muscle_gain_adds_protein(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_test_switch")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_switch")

    r = client.patch(
        "/profile",
        data=json.dumps({"primary_goal": "muscle_gain"}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    out = r.get_json()
    assert out["primary_goal"] == "muscle_gain"
    # 80 * 1.6 = 128
    assert out["daily_protein_g_target"] == 128


# ---------------------------------------------------------------------------
# Cross-user isolation (T-02-04)
# ---------------------------------------------------------------------------


def test_profile_isolated_by_clerk_id(
    client, mongo_collections, monkeypatch
):
    """JWT for user A returns only A's profile even when both A and B exist."""
    _seed_profile(mongo_collections, "user_alice", name="Alice")
    _seed_profile(mongo_collections, "user_bob", name="Bob")

    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_alice")
    r = client.get("/profile", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    assert r.get_json()["name"] == "Alice"
    assert r.get_json()["clerk_id"] == "user_alice"
