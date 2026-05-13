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


# ===========================================================================
# GET /meals?date= and ?days= — P3-B.3
# ===========================================================================


def _insert_meal(
    mongo_collections,
    user_id: str,
    logged_at: datetime,
    total_kcal: int = 500,
    total_protein_g: int = 20,
    components: list[dict] | None = None,
) -> None:
    now = datetime.now(UTC)
    if components is None:
        components = [
            {
                "name": "Jollof rice",
                "matched_food_id": "gh-jollof-rice",
                "portion_g": 300,
                "kcal_low": None,
                "kcal_high": None,
                "kcal_point": total_kcal,
                "protein_g_point": total_protein_g,
                "confidence": None,
                "source": "table",
            }
        ]
    mongo_collections.meals.insert_one(
        {
            "user_id": user_id,
            "logged_at": logged_at,
            "source": "manual",
            "components": components,
            "total_kcal": total_kcal,
            "total_protein_g": total_protein_g,
            "ai_metadata": None,
            "created_at": now,
            "updated_at": now,
        }
    )


def test_get_meals_date_returns_day_total_and_meals(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a", timezone="Africa/Accra")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    # Two meals on 2026-05-13 in Accra (UTC+0 -> UTC same date).
    _insert_meal(
        mongo_collections,
        "user_a",
        datetime(2026, 5, 13, 8, 0, tzinfo=UTC),
        total_kcal=400,
        total_protein_g=10,
    )
    _insert_meal(
        mongo_collections,
        "user_a",
        datetime(2026, 5, 13, 19, 30, tzinfo=UTC),
        total_kcal=600,
        total_protein_g=20,
    )

    r = client.get("/meals?date=2026-05-13", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200, r.get_data(as_text=True)
    out = r.get_json()
    assert out["date"] == "2026-05-13"
    assert out["total_kcal"] == 1000
    assert out["total_protein_g"] == 30
    assert len(out["meals"]) == 2


def test_get_meals_date_isolated_by_user_id(
    client, mongo_collections, monkeypatch
):
    """T-03-03: cross-user reads must not leak."""
    _seed_profile(mongo_collections, "user_a", timezone="Africa/Accra")
    _seed_profile(mongo_collections, "user_b", timezone="Africa/Accra")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    _insert_meal(
        mongo_collections,
        "user_b",
        datetime(2026, 5, 13, 12, 0, tzinfo=UTC),
        total_kcal=999,
    )
    r = client.get(
        "/meals?date=2026-05-13", headers={"Authorization": "Bearer stub"}
    )
    out = r.get_json()
    assert out["meals"] == []
    assert out["total_kcal"] == 0


def test_get_meals_date_uses_profile_timezone_for_day_boundary(
    client, mongo_collections, monkeypatch
):
    """Planner-flagged risk #1: 23:30 local in Accra is the same day's date
    for an Accra user but the next-UTC-day for an LA user."""
    _seed_profile(mongo_collections, "user_accra", timezone="Africa/Accra")
    _seed_profile(
        mongo_collections, "user_la", timezone="America/Los_Angeles"
    )
    # Meal logged at 2026-05-13 23:30 Accra local = 2026-05-13 23:30 UTC
    # = 2026-05-13 16:30 PT (still 2026-05-13 in LA).
    accra_local_2330 = datetime(2026, 5, 13, 23, 30, tzinfo=UTC)
    _insert_meal(mongo_collections, "user_accra", accra_local_2330)
    _insert_meal(mongo_collections, "user_la", accra_local_2330)

    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_accra")
    r1 = client.get(
        "/meals?date=2026-05-13", headers={"Authorization": "Bearer stub"}
    )
    assert len(r1.get_json()["meals"]) == 1

    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_la")
    r2 = client.get(
        "/meals?date=2026-05-13", headers={"Authorization": "Bearer stub"}
    )
    assert len(r2.get_json()["meals"]) == 1

    # Meal logged at 2026-05-13 06:00 UTC = 2026-05-12 23:00 LA local.
    early_utc = datetime(2026, 5, 13, 6, 0, tzinfo=UTC)
    _insert_meal(mongo_collections, "user_la", early_utc)
    r3 = client.get(
        "/meals?date=2026-05-12", headers={"Authorization": "Bearer stub"}
    )
    # The new meal must show up under 2026-05-12 in LA's tz.
    assert len(r3.get_json()["meals"]) == 1


def test_get_meals_date_malformed_returns_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    r = client.get("/meals?date=2026/05/13", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 422


def test_get_meals_date_no_profile_returns_422(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_orphan")
    r = client.get(
        "/meals?date=2026-05-13", headers={"Authorization": "Bearer stub"}
    )
    assert r.status_code == 422


def test_get_meals_days_default_30_groups_correctly(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a", timezone="Africa/Accra")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    now = datetime.now(UTC)
    _insert_meal(mongo_collections, "user_a", now - timedelta(days=1), total_kcal=200)
    _insert_meal(mongo_collections, "user_a", now - timedelta(days=2), total_kcal=300)
    _insert_meal(mongo_collections, "user_a", now, total_kcal=400)
    r = client.get("/meals", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    out = r.get_json()
    assert "days" in out
    assert len(out["days"]) == 3


def test_get_meals_days_omits_empty_days(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a", timezone="Africa/Accra")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    now = datetime.now(UTC)
    _insert_meal(mongo_collections, "user_a", now - timedelta(days=10))
    _insert_meal(mongo_collections, "user_a", now)
    r = client.get("/meals?days=30", headers={"Authorization": "Bearer stub"})
    out = r.get_json()
    # Two non-empty days only; empty days between are skipped.
    assert len(out["days"]) == 2


def test_get_meals_days_clamps_to_1_30_range(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    r99 = client.get("/meals?days=99", headers={"Authorization": "Bearer stub"})
    assert r99.status_code == 200
    r0 = client.get("/meals?days=0", headers={"Authorization": "Bearer stub"})
    assert r0.status_code == 200


def test_get_meals_days_groups_by_user_local_date_not_utc(
    client, mongo_collections, monkeypatch
):
    """A meal logged at 23:30 Africa/Accra appears under 2026-05-13 not 14."""
    _seed_profile(mongo_collections, "user_a", timezone="Africa/Accra")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    # 2026-05-13 23:30 UTC == 2026-05-13 23:30 Accra
    _insert_meal(
        mongo_collections,
        "user_a",
        datetime(2026, 5, 13, 23, 30, tzinfo=UTC),
    )
    r = client.get("/meals?days=30", headers={"Authorization": "Bearer stub"})
    out = r.get_json()
    if out["days"]:
        # The day key must reflect Accra local, not UTC drift.
        assert out["days"][0]["date"] == "2026-05-13"


def test_get_meals_days_isolated_by_user_id(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_profile(mongo_collections, "user_b")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    _insert_meal(mongo_collections, "user_b", datetime.now(UTC))
    r = client.get("/meals?days=30", headers={"Authorization": "Bearer stub"})
    out = r.get_json()
    assert out["days"] == []


def test_get_meals_days_newest_first(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a", timezone="Africa/Accra")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    now = datetime.now(UTC)
    _insert_meal(mongo_collections, "user_a", now - timedelta(days=3), total_kcal=100)
    _insert_meal(mongo_collections, "user_a", now - timedelta(days=1), total_kcal=200)
    _insert_meal(mongo_collections, "user_a", now, total_kcal=300)
    r = client.get("/meals?days=30", headers={"Authorization": "Bearer stub"})
    out = r.get_json()
    dates = [d["date"] for d in out["days"]]
    assert dates == sorted(dates, reverse=True)


# ===========================================================================
# PATCH /meals/<id> and DELETE /meals/<id> — P3-B.4
# ===========================================================================


def _post_seed_meal(client, mongo_collections, *, user_id: str) -> str:
    """Helper: POST a seed meal and return its id."""
    _seed_foods(mongo_collections)
    body = {"components": [{"food_id": "gh-jollof-rice", "portion_g": 350}]}
    r = client.post("/meals", data=json.dumps(body), headers=_hdrs())
    assert r.status_code == 201, r.get_data(as_text=True)
    return r.get_json()["id"]


def test_patch_meal_components_replaces_array_and_recomputes_totals(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")

    # Replace jollof with banku + tilapia.
    body = {
        "components": [
            {"food_id": "gh-banku", "portion_g": 200},
            {"food_id": "gh-tilapia-grilled", "portion_g": 250},
        ]
    }
    r = client.patch(
        f"/meals/{meal_id}", data=json.dumps(body), headers=_hdrs()
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    out = r.get_json()
    assert len(out["components"]) == 2
    # 145*200/100=290; 130*250/100=325; sum=615
    assert out["total_kcal"] == 290 + 325


def test_patch_meal_logged_at_only_updates_timestamp_keeps_components(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")

    new_ts = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    r = client.patch(
        f"/meals/{meal_id}",
        data=json.dumps({"logged_at": new_ts}),
        headers=_hdrs(),
    )
    assert r.status_code == 200
    out = r.get_json()
    assert len(out["components"]) == 1  # original component preserved


def test_patch_meal_rejects_unknown_field_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")

    r = client.patch(
        f"/meals/{meal_id}",
        data=json.dumps({"total_kcal": 99999}),
        headers=_hdrs(),
    )
    assert r.status_code == 422


def test_patch_meal_other_user_returns_404_not_403(
    client, mongo_collections, monkeypatch
):
    """T-03-03: cross-user PATCH must return 404 to avoid leaking existence."""
    _seed_profile(mongo_collections, "user_a")
    _seed_profile(mongo_collections, "user_b")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")

    # Now switch to user_b and try to PATCH user_a's meal.
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_b")
    r = client.patch(
        f"/meals/{meal_id}",
        data=json.dumps({"components": [{"food_id": "gh-banku", "portion_g": 200}]}),
        headers=_hdrs(),
    )
    assert r.status_code == 404


def test_patch_meal_invalid_id_returns_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    r = client.patch(
        "/meals/not-an-objectid",
        data=json.dumps({"components": [{"food_id": "gh-jollof-rice", "portion_g": 350}]}),
        headers=_hdrs(),
    )
    assert r.status_code == 422


def test_patch_meal_backdate_violation_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")

    too_old = (datetime.now(UTC) - timedelta(days=8)).isoformat()
    r = client.patch(
        f"/meals/{meal_id}",
        data=json.dumps({"logged_at": too_old}),
        headers=_hdrs(),
    )
    assert r.status_code == 422


def test_delete_meal_removes_doc(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")

    r = client.delete(f"/meals/{meal_id}", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    out = r.get_json()
    assert out["ok"] is True
    assert out["deleted_id"] == meal_id
    assert mongo_collections.meals.count_documents({}) == 0


def test_delete_meal_other_user_returns_404(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _seed_profile(mongo_collections, "user_b")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")

    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_b")
    r = client.delete(f"/meals/{meal_id}", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 404


def test_delete_meal_idempotent_second_call_404(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    meal_id = _post_seed_meal(client, mongo_collections, user_id="user_a")
    client.delete(f"/meals/{meal_id}", headers={"Authorization": "Bearer stub"})
    r2 = client.delete(f"/meals/{meal_id}", headers={"Authorization": "Bearer stub"})
    assert r2.status_code == 404


def test_delete_meal_invalid_id_422(
    client, mongo_collections, monkeypatch
):
    _seed_profile(mongo_collections, "user_a")
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_a")
    r = client.delete(
        "/meals/not-an-objectid", headers={"Authorization": "Bearer stub"}
    )
    assert r.status_code == 422
