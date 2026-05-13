"""Tests for DELETE /me — cascade delete (profile + weights + users + Clerk).

Phase 2 Plan 02 — Task P2-A.5.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock


def _stub_clerk_with_users_delete(monkeypatch, *, clerk_user_id: str, raises=None):
    """Stub the Clerk SDK so authenticate_request returns signed-in AND
    users.delete is a MagicMock (optionally raising)."""
    import app.middleware.auth as auth_mod

    auth_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload={"sub": clerk_user_id, "email": "delete@example.com"},
    )

    users_mock = MagicMock()
    if raises is not None:
        users_mock.delete.side_effect = raises
    else:
        users_mock.delete.return_value = None

    class _StubClerk:
        users = users_mock

        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return auth_state

    stub = _StubClerk()
    monkeypatch.setattr(auth_mod, "_clerk", stub)
    return stub


def _seed_user_full(mongo_collections, clerk_id: str, *, weights: int = 2):
    now = datetime.now(UTC)
    mongo_collections.users.insert_one({
        "clerk_id": clerk_id,
        "email": "delete@example.com",
        "created_at": now,
        "updated_at": now,
    })
    mongo_collections.profiles.insert_one({
        "clerk_id": clerk_id,
        "name": "ToDelete",
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
    for i in range(weights):
        mongo_collections.weight_logs.insert_one({
            "user_id": clerk_id,
            "kg": 80.0 - i * 0.5,
            "logged_at": now,
        })


# ---------------------------------------------------------------------------


def test_delete_me_cascades_mongo_collections(
    client, mongo_collections, monkeypatch
):
    _seed_user_full(mongo_collections, "user_test_del1", weights=2)
    _stub_clerk_with_users_delete(monkeypatch, clerk_user_id="user_test_del1")

    r = client.delete("/me", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["ok"] is True
    assert body["deleted"]["weight_logs"] == 2
    assert body["deleted"]["profile"] == 1
    assert body["deleted"]["user"] == 1
    assert body["deleted"]["clerk"] is True

    # All three collections cleared for this clerk_id
    assert mongo_collections.users.find_one({"clerk_id": "user_test_del1"}) is None
    assert mongo_collections.profiles.find_one({"clerk_id": "user_test_del1"}) is None
    assert list(mongo_collections.weight_logs.find({"user_id": "user_test_del1"})) == []


def test_delete_me_calls_clerk_sdk_users_delete(
    client, mongo_collections, monkeypatch
):
    _seed_user_full(mongo_collections, "user_test_del2")
    stub = _stub_clerk_with_users_delete(monkeypatch, clerk_user_id="user_test_del2")

    r = client.delete("/me", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200

    # Verify the call signature: users.delete(user_id="user_test_del2")
    stub.users.delete.assert_called_once()
    _, kwargs = stub.users.delete.call_args
    assert kwargs.get("user_id") == "user_test_del2"


def test_delete_me_uses_jwt_user_id_not_body(
    client, mongo_collections, monkeypatch
):
    """T-02-01: forged clerk_id in the body must be ignored; only the
    JWT-bound id gets deleted."""
    _seed_user_full(mongo_collections, "user_test_victim", weights=1)
    # Also seed an "attacker" doc that must NOT be touched
    _seed_user_full(mongo_collections, "user_attacker", weights=1)
    stub = _stub_clerk_with_users_delete(monkeypatch, clerk_user_id="user_test_victim")

    r = client.delete(
        "/me",
        data=json.dumps({"clerk_id": "user_attacker"}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 200

    # Only the JWT-bound user was deleted
    assert mongo_collections.profiles.find_one({"clerk_id": "user_test_victim"}) is None
    assert mongo_collections.profiles.find_one({"clerk_id": "user_attacker"}) is not None

    # And the Clerk SDK was called with the JWT id, not the body id
    _, kwargs = stub.users.delete.call_args
    assert kwargs["user_id"] == "user_test_victim"


def test_delete_me_idempotent_when_already_deleted(
    client, mongo_collections, monkeypatch
):
    """No seed data; calling DELETE /me returns 200 with zero counts."""
    _stub_clerk_with_users_delete(monkeypatch, clerk_user_id="user_test_empty")

    r = client.delete("/me", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["deleted"]["weight_logs"] == 0
    assert body["deleted"]["profile"] == 0
    assert body["deleted"]["user"] == 0


def test_delete_me_treats_clerk_404_as_success(
    client, mongo_collections, monkeypatch
):
    """If Clerk returns 'user not found' (HTTP 404), treat as already-deleted
    success — the cascade is idempotent."""
    _seed_user_full(mongo_collections, "user_test_404")
    not_found = Exception("Clerk says: User not found")
    not_found.status_code = 404  # type: ignore[attr-defined]
    _stub_clerk_with_users_delete(
        monkeypatch, clerk_user_id="user_test_404", raises=not_found
    )

    r = client.delete("/me", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["deleted"]["clerk"] is True


def test_delete_me_returns_502_when_clerk_call_fails(
    client, mongo_collections, monkeypatch
):
    """Mongo cascade succeeds + Clerk SDK raises non-404 -> 502
    clerk_delete_failed with mongo_deleted: true."""
    _seed_user_full(mongo_collections, "user_test_502", weights=2)
    boom = RuntimeError("Clerk gateway timeout")
    _stub_clerk_with_users_delete(
        monkeypatch, clerk_user_id="user_test_502", raises=boom
    )

    r = client.delete("/me", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 502
    body = r.get_json()
    assert body["error"] == "clerk_delete_failed"
    assert body["mongo_deleted"] is True

    # Mongo data IS gone (best-effort cascade)
    assert mongo_collections.users.find_one({"clerk_id": "user_test_502"}) is None
    assert mongo_collections.profiles.find_one({"clerk_id": "user_test_502"}) is None
    assert list(mongo_collections.weight_logs.find({"user_id": "user_test_502"})) == []
