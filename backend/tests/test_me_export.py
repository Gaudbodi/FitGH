"""Tests for GET /me/export — Phase 7 P7-C.1 (LEGAL-02).

Behavior under test:
- 200 happy path: seeded user + profile + 2 weight_logs + 2 meals +
  1 user_correction + 1 vision_usage; JSON response contains 6 arrays
  + _export_metadata; ObjectIds are stringified; datetimes are ISO 8601.
- 200 empty account: only user doc seeded; weight_logs/meals/user_corrections/
  vision_usage are [] (empty arrays, not null); profile is None / null.
- 401 unauth: no Authorization header.
- Cross-user isolation: user A bearer never sees user B data. T-07-01
  mitigation test — verifies the trust anchor `g.clerk_user_id` is honored.

The route MUST read user identity ONLY from `g.clerk_user_id` (set by
@require_auth from the verified JWT), NEVER from request body or query.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from bson import ObjectId


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_clerk_signed_in(
    monkeypatch,
    *,
    clerk_user_id: str = "user_test_abc",
    clerk_email: str | None = "user@example.com",
) -> None:
    """Patch the lazy Clerk client to return a signed-in state."""
    import app.middleware.auth as auth_mod

    payload = {"sub": clerk_user_id}
    if clerk_email is not None:
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


def _seed_user(mongo_collections, clerk_id: str, *, with_extras: bool = True):
    """Seed a user + (optionally) profile + 2 weight_logs + 2 meals + 1
    correction + 1 vision_usage doc."""
    now = datetime.now(UTC)
    mongo_collections.users.insert_one({
        "clerk_id": clerk_id,
        "email": f"{clerk_id}@example.com",
        "created_at": now,
        "updated_at": now,
    })
    if not with_extras:
        return

    mongo_collections.profiles.insert_one({
        "clerk_id": clerk_id,
        "name": "Test User",
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
    })
    for i in range(2):
        mongo_collections.weight_logs.insert_one({
            "user_id": clerk_id,
            "kg": 80.0 - i * 0.5,
            "logged_at": now,
        })
    for i in range(2):
        mongo_collections.meals.insert_one({
            "user_id": clerk_id,
            "components": [{"name": "jollof rice", "kcal": 600, "portion_g": 250}],
            "total_kcal": 600,
            "logged_at": now,
            "source": "scan" if i == 0 else "manual",
        })
    mongo_collections.user_corrections.insert_one({
        "user_id": clerk_id,
        "predicted_total_kcal": 600,
        "corrected_total_kcal": 550,
        "corrected_at": now,
    })
    mongo_collections.vision_usage.insert_one({
        "user_id": clerk_id,
        "date": "2026-05-13",
        "count": 3,
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_export_happy_path(client, mongo_collections, monkeypatch):
    """Seeded with full user state → 200 with all 6 arrays + metadata."""
    clerk_id = "user_export_happy"
    _seed_user(mongo_collections, clerk_id, with_extras=True)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id=clerk_id)

    r = client.get("/me/export", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()

    # 6 expected top-level keys
    expected_keys = {
        "_export_metadata",
        "user",
        "profile",
        "weight_logs",
        "meals",
        "user_corrections",
        "vision_usage",
    }
    assert expected_keys.issubset(body.keys()), (
        f"missing keys: {expected_keys - set(body.keys())}"
    )

    # _export_metadata shape
    meta = body["_export_metadata"]
    assert "export_date" in meta
    assert isinstance(meta["export_date"], str)  # ISO string, not datetime
    assert "T" in meta["export_date"]  # rough ISO-8601 sniff
    assert "app_version" in meta
    assert isinstance(meta["app_version"], str)
    assert meta["schema_version"] == 1

    # Array lengths match seed counts
    assert len(body["weight_logs"]) == 2
    assert len(body["meals"]) == 2
    assert len(body["user_corrections"]) == 1
    assert len(body["vision_usage"]) == 1

    # ObjectIds serialized as strings (not nested {"$oid": "..."} dicts)
    for entry in body["weight_logs"]:
        assert isinstance(entry["_id"], str)
        # Datetimes serialized as ISO strings
        assert isinstance(entry["logged_at"], str)


def test_export_empty_account(client, mongo_collections, monkeypatch):
    """Only user doc seeded → 200 with empty arrays (not null/missing)."""
    clerk_id = "user_export_empty"
    _seed_user(mongo_collections, clerk_id, with_extras=False)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id=clerk_id)

    r = client.get("/me/export", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()

    # The four user-data arrays are empty lists (not None)
    assert body["weight_logs"] == []
    assert body["meals"] == []
    assert body["user_corrections"] == []
    assert body["vision_usage"] == []

    # profile is None / null when the user hasn't completed onboarding yet.
    # (Documented behaviour — the executor chose `null` over missing-key for
    # clearer JSON consumer ergonomics.)
    assert body["profile"] is None

    # _export_metadata still populated
    assert body["_export_metadata"]["schema_version"] == 1


def test_export_unauth(client):
    """No Authorization header → 401."""
    r = client.get("/me/export")
    assert r.status_code == 401, r.get_data(as_text=True)


def test_export_cross_user_isolation(client, mongo_collections, monkeypatch):
    """T-07-01: user A bearer must never see user B data."""
    user_a = "user_export_A"
    user_b = "user_export_B"
    _seed_user(mongo_collections, user_a, with_extras=True)
    _seed_user(mongo_collections, user_b, with_extras=True)

    # Stub the JWT as user A only.
    _stub_clerk_signed_in(monkeypatch, clerk_user_id=user_a)

    r = client.get("/me/export", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()

    # Render the full payload as a JSON string and scan for user_B identifiers.
    import json as _json

    payload_str = _json.dumps(body)
    assert user_b not in payload_str, (
        "T-07-01 violation: user_export_A's export contains user_export_B "
        "identifiers — cross-user isolation broken."
    )
    # Positive check: user_A IS present
    assert user_a in payload_str

    # Counts: user A's seed counts (NOT user A + user B combined)
    assert len(body["weight_logs"]) == 2
    assert len(body["meals"]) == 2
    assert len(body["user_corrections"]) == 1
    assert len(body["vision_usage"]) == 1
