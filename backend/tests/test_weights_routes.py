"""Tests for /weights (POST log / GET history).

Phase 2 Plan 02 — Task P2-A.4.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace


def _stub_clerk_signed_in(monkeypatch, *, clerk_user_id: str) -> None:
    import app.middleware.auth as auth_mod

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload={"sub": clerk_user_id, "email": "w@example.com"},
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


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


# ---------------------------------------------------------------------------
# POST /weights
# ---------------------------------------------------------------------------


def test_post_weight_inserts_and_updates_profile_target(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_test_logw")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_logw")

    r = client.post(
        "/weights",
        data=json.dumps({"kg": 90.0}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 201, r.get_data(as_text=True)
    out = r.get_json()
    assert out["kg"] == 90.0
    assert out["user_id"] == "user_test_logw"

    # weight_log inserted
    rows = list(mongo_collections.weight_logs.find({"user_id": "user_test_logw"}))
    assert len(rows) == 1
    assert rows[0]["kg"] == 90.0

    # Profile target recomputed: 10*90 + 6.25*180 - 5*30 + 5 = 1880; *1.55 = 2914; -500 = 2414
    profile = mongo_collections.profiles.find_one({"clerk_id": "user_test_logw"})
    assert profile["weight_kg"] == 90.0
    assert profile["daily_kcal_target"] == 2414


def test_post_weight_409_when_no_profile(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_noprof")
    r = client.post(
        "/weights",
        data=json.dumps({"kg": 70.0}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 409
    assert r.get_json()["error"] == "no_profile"


def test_post_weight_rejects_kg_out_of_range_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_test_oor")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_oor")

    r = client.post(
        "/weights",
        data=json.dumps({"kg": 5.0}),  # below 20 min
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 422

    r = client.post(
        "/weights",
        data=json.dumps({"kg": 500.0}),  # above 400 max
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 422


def test_post_weight_recomputes_protein_for_muscle_gain(
    client, mongo_collections, monkeypatch
):
    _seed_profile(
        mongo_collections,
        "user_test_protein",
        primary_goal="muscle_gain",
        daily_protein_g_target=128,
    )
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_protein")

    r = client.post(
        "/weights",
        data=json.dumps({"kg": 95.0}),
        headers={"Authorization": "Bearer stub", "Content-Type": "application/json"},
    )
    assert r.status_code == 201
    profile = mongo_collections.profiles.find_one({"clerk_id": "user_test_protein"})
    # 95 * 1.6 = 152
    assert profile["daily_protein_g_target"] == 152


# ---------------------------------------------------------------------------
# GET /weights
# ---------------------------------------------------------------------------


def test_get_weights_returns_history_newest_first(
    client, mongo_collections, monkeypatch
):
    now = datetime.now(UTC)
    # Insert 3 weight logs over the past 3 days, intentionally in arbitrary order
    mongo_collections.weight_logs.insert_many([
        {"user_id": "user_test_hist", "kg": 80.0, "logged_at": now - timedelta(days=2)},
        {"user_id": "user_test_hist", "kg": 79.5, "logged_at": now - timedelta(days=1)},
        {"user_id": "user_test_hist", "kg": 79.2, "logged_at": now},
    ])
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_hist")

    r = client.get("/weights", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    entries = r.get_json()["entries"]
    assert len(entries) == 3
    # Newest first
    assert entries[0]["kg"] == 79.2
    assert entries[1]["kg"] == 79.5
    assert entries[2]["kg"] == 80.0


def test_get_weights_respects_limit_param(
    client, mongo_collections, monkeypatch
):
    now = datetime.now(UTC)
    docs = [
        {"user_id": "user_test_lim", "kg": 70.0 + i, "logged_at": now - timedelta(hours=i)}
        for i in range(50)
    ]
    mongo_collections.weight_logs.insert_many(docs)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_lim")

    r = client.get("/weights?limit=5", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    assert len(r.get_json()["entries"]) == 5

    # Default limit is 30
    r = client.get("/weights", headers={"Authorization": "Bearer stub"})
    assert len(r.get_json()["entries"]) == 30

    # Max limit is 100; oversize value clamps to 100
    r = client.get("/weights?limit=999", headers={"Authorization": "Bearer stub"})
    assert len(r.get_json()["entries"]) == 50  # only 50 docs exist; would clamp to 100 otherwise


def test_get_weights_isolated_by_user_id(
    client, mongo_collections, monkeypatch
):
    """T-02-04: querying as user A must never return user B's weights."""
    now = datetime.now(UTC)
    mongo_collections.weight_logs.insert_many([
        {"user_id": "user_alice", "kg": 60.0, "logged_at": now},
        {"user_id": "user_bob", "kg": 80.0, "logged_at": now},
    ])
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_alice")

    r = client.get("/weights", headers={"Authorization": "Bearer stub"})
    entries = r.get_json()["entries"]
    assert len(entries) == 1
    assert entries[0]["kg"] == 60.0
    assert all(e["user_id"] == "user_alice" for e in entries)
