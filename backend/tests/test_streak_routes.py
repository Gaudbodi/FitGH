"""Integration tests for the streak feature wired into POST /meals + POST
/weights — Phase 5 Plan 05 (P5-A.3).

The streak fields live on the existing profiles document (DASH-06,
D-STREAK-ON-PROFILE-DOC). Both POST /meals and POST /weights recompute
the streak after their primary insert and merge the new (count, state,
last_logged_at) into profiles.update_one $set.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace


def _stub_clerk_signed_in(
    monkeypatch, *, clerk_user_id: str = "user_streak_test"
) -> None:
    import app.middleware.auth as auth_mod

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload={"sub": clerk_user_id, "email": "s@example.com"},
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


def _seed_profile(
    mongo_collections,
    clerk_id: str,
    *,
    timezone: str = "Africa/Accra",
    streak_count: int = 0,
    streak_state: str = "active",
    streak_last_logged_at: datetime | None = None,
) -> None:
    now = datetime.now(UTC)
    mongo_collections.profiles.insert_one(
        {
            "clerk_id": clerk_id,
            "name": "Streak Tester",
            "sex": "male",
            "height_cm": 180,
            "weight_kg": 80.0,
            "age": 30,
            "timezone": timezone,
            "locale": "ghana",
            "activity_level": "moderately_active",
            "primary_goal": "weight_loss",
            "daily_kcal_target": 2259,
            "daily_protein_g_target": None,
            "floor_hit": False,
            "streak_count": streak_count,
            "streak_state": streak_state,
            "streak_last_logged_at": streak_last_logged_at,
            "privacy_consent_at": now,
            "created_at": now,
            "updated_at": now,
        }
    )


def _seed_jollof(mongo_collections) -> None:
    mongo_collections.ghana_foods.insert_one(
        {
            "food_id": "gh-jollof-rice",
            "name": "Jollof rice",
            "alt_names": ["jollof"],
            "kcal_per_100g": 165.0,
            "protein_g_per_100g": 4.0,
            "fat_g_per_100g": 5.5,
            "carbs_g_per_100g": 26.0,
            "portion_defaults": [{"label": "1 plate", "grams": 350}],
            "category": "staple",
            "source": "wafct_composite",
            "source_confidence": "medium",
        }
    )


def _post_jollof(client, *, logged_at_iso: str | None = None):
    body = {
        "components": [
            {"food_id": "gh-jollof-rice", "portion_g": 350},
        ],
    }
    if logged_at_iso is not None:
        body["logged_at"] = logged_at_iso
    return client.post(
        "/meals",
        data=json.dumps(body),
        headers={
            "Authorization": "Bearer stub",
            "Content-Type": "application/json",
        },
    )


def _post_weight(client, kg: float = 80.0):
    return client.post(
        "/weights",
        data=json.dumps({"kg": kg}),
        headers={
            "Authorization": "Bearer stub",
            "Content-Type": "application/json",
        },
    )


# ---------------------------------------------------------------------------
# 1. First-ever meal log creates streak.
# ---------------------------------------------------------------------------


def test_first_meal_creates_streak(client, mongo_collections, monkeypatch):
    _seed_profile(mongo_collections, "user_streak_first")
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_first")

    r = _post_jollof(client)
    assert r.status_code == 201, r.get_data(as_text=True)

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_first"}
    )
    assert profile["streak_count"] == 1
    assert profile["streak_state"] == "active"
    assert profile["streak_last_logged_at"] is not None


# ---------------------------------------------------------------------------
# 2. Two POSTs same day = idempotent (no double bump).
# ---------------------------------------------------------------------------


def test_same_day_meal_does_not_double_bump(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_streak_idem")
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_idem")

    r1 = _post_jollof(client)
    assert r1.status_code == 201
    r2 = _post_jollof(client)
    assert r2.status_code == 201

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_idem"}
    )
    assert profile["streak_count"] == 1
    assert profile["streak_state"] == "active"


# ---------------------------------------------------------------------------
# 3. Yesterday → today: count+1.
# ---------------------------------------------------------------------------


def test_yesterday_then_today_meal_increments(
    client, mongo_collections, monkeypatch
):
    yesterday = datetime.now(UTC) - timedelta(days=1)
    _seed_profile(
        mongo_collections,
        "user_streak_y2t",
        streak_count=4,
        streak_state="active",
        streak_last_logged_at=yesterday,
    )
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_y2t")

    r = _post_jollof(client)
    assert r.status_code == 201

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_y2t"}
    )
    assert profile["streak_count"] == 5
    assert profile["streak_state"] == "active"


# ---------------------------------------------------------------------------
# 4. 2-day gap → paused, count holds.
# ---------------------------------------------------------------------------


def test_two_day_gap_meal_paused(client, mongo_collections, monkeypatch):
    two_days_ago = datetime.now(UTC) - timedelta(days=2)
    _seed_profile(
        mongo_collections,
        "user_streak_2gap",
        streak_count=6,
        streak_state="active",
        streak_last_logged_at=two_days_ago,
    )
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_2gap")

    r = _post_jollof(client)
    assert r.status_code == 201

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_2gap"}
    )
    assert profile["streak_count"] == 6  # held
    assert profile["streak_state"] == "paused"


# ---------------------------------------------------------------------------
# 5. 3-day gap → restart at 1, active.
# ---------------------------------------------------------------------------


def test_three_day_gap_meal_restarts(
    client, mongo_collections, monkeypatch
):
    three_days_ago = datetime.now(UTC) - timedelta(days=3)
    _seed_profile(
        mongo_collections,
        "user_streak_3gap",
        streak_count=10,
        streak_state="active",
        streak_last_logged_at=three_days_ago,
    )
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_3gap")

    r = _post_jollof(client)
    assert r.status_code == 201

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_3gap"}
    )
    assert profile["streak_count"] == 1
    assert profile["streak_state"] == "active"


# ---------------------------------------------------------------------------
# 6. Paused → next-day meal recovers to active+1.
# ---------------------------------------------------------------------------


def test_paused_then_next_day_meal_recovers_active(
    client, mongo_collections, monkeypatch
):
    yesterday = datetime.now(UTC) - timedelta(days=1)
    _seed_profile(
        mongo_collections,
        "user_streak_pause_rec",
        streak_count=4,
        streak_state="paused",
        streak_last_logged_at=yesterday,
    )
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_pause_rec")

    r = _post_jollof(client)
    assert r.status_code == 201

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_pause_rec"}
    )
    assert profile["streak_count"] == 5
    assert profile["streak_state"] == "active"


# ---------------------------------------------------------------------------
# 7. First-ever weight log creates streak (interpretation beyond CONTEXT.md).
# ---------------------------------------------------------------------------


def test_first_weight_creates_streak(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_streak_w")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_w")

    r = _post_weight(client, kg=80.0)
    assert r.status_code == 201, r.get_data(as_text=True)

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_w"}
    )
    assert profile["streak_count"] == 1
    assert profile["streak_state"] == "active"
    assert profile["streak_last_logged_at"] is not None
    # And the existing weight target recompute still fires.
    assert profile["weight_kg"] == 80.0
    assert profile["daily_kcal_target"] is not None


# ---------------------------------------------------------------------------
# 8. Cross-user isolation — A's POST doesn't touch B's streak.
# ---------------------------------------------------------------------------


def test_user_a_meal_does_not_touch_user_b_streak(
    client, mongo_collections, monkeypatch
):
    # Seed both users; B has an established streak that must not move.
    yesterday = datetime.now(UTC) - timedelta(days=1)
    _seed_profile(mongo_collections, "user_streak_A")
    _seed_profile(
        mongo_collections,
        "user_streak_B",
        streak_count=9,
        streak_state="active",
        streak_last_logged_at=yesterday,
    )
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_A")

    r = _post_jollof(client)
    assert r.status_code == 201

    profile_a = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_A"}
    )
    profile_b = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_B"}
    )
    assert profile_a["streak_count"] == 1
    assert profile_b["streak_count"] == 9
    assert profile_b["streak_state"] == "active"


# ---------------------------------------------------------------------------
# 9. T-05-07 — backdated meal POST does NOT rewrite streak history.
# ---------------------------------------------------------------------------


def test_backdated_meal_does_not_rewrite_streak_history(
    client, mongo_collections, monkeypatch
):
    """Backdated meal: the meal's logged_at is 3 days ago, but the streak
    uses server-now (today) for the day key. So the streak should bump as
    if the user just logged TODAY, not retroactively fill a 3-day gap."""
    _seed_profile(mongo_collections, "user_streak_backdate")
    _seed_jollof(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_backdate")

    backdated = (datetime.now(UTC) - timedelta(days=3)).replace(
        microsecond=0
    )
    r = _post_jollof(client, logged_at_iso=backdated.isoformat())
    assert r.status_code == 201, r.get_data(as_text=True)

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_backdate"}
    )
    # First-ever streak event today.
    assert profile["streak_count"] == 1
    assert profile["streak_state"] == "active"
    # last_logged_at is today (server-now), not 3 days ago.
    last = profile["streak_last_logged_at"]
    assert last is not None
    today = datetime.now(UTC).date()
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    assert last.astimezone(UTC).date() == today


# ---------------------------------------------------------------------------
# 10. Weight POST also obeys idempotency.
# ---------------------------------------------------------------------------


def test_same_day_weight_does_not_double_bump(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_streak_w_idem")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_streak_w_idem")

    r1 = _post_weight(client, kg=80.0)
    assert r1.status_code == 201
    r2 = _post_weight(client, kg=80.1)
    assert r2.status_code == 201

    profile = mongo_collections.profiles.find_one(
        {"clerk_id": "user_streak_w_idem"}
    )
    assert profile["streak_count"] == 1
    assert profile["streak_state"] == "active"
