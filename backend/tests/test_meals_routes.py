"""Tests for /meals routes (POST + GET + PATCH + DELETE).

Phase 3 Plan 03 — Tasks P3-B.2, P3-B.3, P3-B.4.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_clerk_signed_in(monkeypatch, *, clerk_user_id: str = "user_test") -> None:
    import app.middleware.auth as auth_mod

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload={"sub": clerk_user_id, "email": "m@example.com"},
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


def _seed_profile(
    mongo_collections, clerk_id: str, *, timezone: str = "Africa/Accra"
) -> None:
    now = datetime.now(UTC)
    mongo_collections.profiles.insert_one(
        {
            "clerk_id": clerk_id,
            "name": "Tester",
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
            "privacy_consent_at": now,
            "created_at": now,
            "updated_at": now,
        }
    )


def _seed_foods(mongo_collections) -> None:
    foods = [
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
        },
        {
            "food_id": "gh-banku",
            "name": "Banku",
            "alt_names": [],
            "kcal_per_100g": 145.0,
            "protein_g_per_100g": 2.3,
            "fat_g_per_100g": 0.5,
            "carbs_g_per_100g": 32.0,
            "portion_defaults": [{"label": "1 ball", "grams": 200}],
            "category": "staple",
            "source": "wafct_composite",
            "source_confidence": "medium",
        },
        {
            "food_id": "gh-tilapia-grilled",
            "name": "Grilled tilapia",
            "alt_names": [],
            "kcal_per_100g": 130.0,
            "protein_g_per_100g": 26.0,
            "fat_g_per_100g": 3.0,
            "carbs_g_per_100g": 0.0,
            "portion_defaults": [{"label": "1 medium", "grams": 250}],
            "category": "protein",
            "source": "wafct",
            "source_confidence": "high",
        },
        {
            "food_id": "gh-shito",
            "name": "Shito",
            "alt_names": [],
            "kcal_per_100g": 320.0,
            "protein_g_per_100g": 8.0,
            "fat_g_per_100g": 28.0,
            "carbs_g_per_100g": 8.0,
            "portion_defaults": [{"label": "1 dollop", "grams": 30}],
            "category": "soup_stew",
            "source": "wafct_composite",
            "source_confidence": "low",
        },
    ]
    mongo_collections.ghana_foods.insert_many(foods)


def _hdrs():
    return {
        "Authorization": "Bearer stub",
        "Content-Type": "application/json",
    }


# ===========================================================================
# POST /meals — P3-B.2
# ===========================================================================


def test_post_meal_single_matched_component_persists_and_computes_kcal_point(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {"components": [{"food_id": "gh-jollof-rice", "portion_g": 350}]}
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201, r.get_data(as_text=True)
    out = r.get_json()
    assert out["user_id"] == "user_a"
    assert out["source"] == "manual"
    assert out["ai_metadata"] is None
    # 165 * 350 / 100 = 577.5 -> banker's even -> 578
    assert out["components"][0]["kcal_point"] == 578
    assert out["components"][0]["matched_food_id"] == "gh-jollof-rice"
    assert out["components"][0]["name"] == "Jollof rice"
    assert out["components"][0]["source"] == "table"
    assert out["components"][0]["kcal_low"] is None
    assert out["components"][0]["kcal_high"] is None
    assert out["components"][0]["confidence"] is None
    assert out["total_kcal"] == 578
    # 4 * 350 / 100 = 14
    assert out["total_protein_g"] == 14
    assert "id" in out


def test_post_meal_multi_component_sums_totals(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {
        "components": [
            {"food_id": "gh-banku", "portion_g": 200},
            {"food_id": "gh-tilapia-grilled", "portion_g": 250},
            {"food_id": "gh-shito", "portion_g": 30},
        ]
    }
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201
    out = r.get_json()
    # 145*200/100=290; 130*250/100=325; 320*30/100=96; sum=711
    assert out["total_kcal"] == 290 + 325 + 96
    # 2.3*200/100=4.6->5; 26*250/100=65; 8*30/100=2.4->2; sum=72
    assert out["total_protein_g"] == 5 + 65 + 2
    assert len(out["components"]) == 3


def test_post_meal_free_text_component_persists_with_user_corrected_source(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {
        "components": [
            {"name": "Beans on toast", "portion_g": 200, "kcal_point": 280}
        ]
    }
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201
    out = r.get_json()
    assert out["components"][0]["matched_food_id"] is None
    assert out["components"][0]["source"] == "user_corrected"
    assert out["components"][0]["kcal_point"] == 280
    assert out["components"][0]["protein_g_point"] == 0
    assert out["total_kcal"] == 280


def test_post_meal_rejects_both_food_id_and_kcal_point_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {
        "components": [
            {"food_id": "gh-jollof-rice", "portion_g": 350, "kcal_point": 9999}
        ]
    }
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 422


def test_post_meal_rejects_neither_food_id_nor_kcal_point_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {"components": [{"name": "Mystery", "portion_g": 200}]}
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 422


def test_post_meal_rejects_unknown_food_id_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {"components": [{"food_id": "gh-nope-rice", "portion_g": 200}]}
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 422
    err = r.get_json()
    assert err["error"] == "unknown_food_id"


def test_post_meal_rejects_backdate_older_than_7_days_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    eight_days_ago = (datetime.now(UTC) - timedelta(days=8)).isoformat()
    body = {
        "logged_at": eight_days_ago,
        "components": [{"food_id": "gh-jollof-rice", "portion_g": 350}],
    }
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 422
    err = r.get_json()
    assert err["error"] == "logged_at_out_of_range"


def test_post_meal_rejects_future_logged_at_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    body = {
        "logged_at": future,
        "components": [{"food_id": "gh-jollof-rice", "portion_g": 350}],
    }
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 422


def test_post_meal_accepts_logged_at_now_minus_5_days(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    five_days_ago = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    body = {
        "logged_at": five_days_ago,
        "components": [{"food_id": "gh-jollof-rice", "portion_g": 350}],
    }
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201


def test_post_meal_rejects_user_id_body_attacker_422(
    client, mongo_collections, monkeypatch
):
    """T-03-01: forged user_id in body must be rejected via extra='forbid'."""
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {
        "user_id": "user_attacker",
        "components": [{"food_id": "gh-jollof-rice", "portion_g": 350}],
    }
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 422


def test_post_meal_stores_ai_metadata_as_null(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {"components": [{"food_id": "gh-jollof-rice", "portion_g": 350}]}
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201
    stored = mongo_collections.meals.find_one({"user_id": "user_a"})
    assert stored["ai_metadata"] is None


def test_post_meal_writes_source_manual(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {"components": [{"food_id": "gh-jollof-rice", "portion_g": 350}]}
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201
    stored = mongo_collections.meals.find_one({"user_id": "user_a"})
    assert stored["source"] == "manual"


def test_post_meal_uses_jwt_sub_for_user_id_not_body(
    client, mongo_collections, monkeypatch
):
    """T-03-01 belt-and-braces: even if extra=forbid lets a body through,
    the route stamps user_id from g.clerk_user_id only."""
    _seed_profile(mongo_collections, "user_a")
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")

    body = {"components": [{"food_id": "gh-jollof-rice", "portion_g": 350}]}
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201
    rows = list(mongo_collections.meals.find({}))
    assert len(rows) == 1
    assert rows[0]["user_id"] == "user_a"
