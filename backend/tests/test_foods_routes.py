"""Tests for the /foods read-only search route.

Phase 3 Plan 03 — Task P3-B.1.
"""

from __future__ import annotations

from types import SimpleNamespace


def _stub_clerk_signed_in(monkeypatch, *, clerk_user_id: str = "user_test") -> None:
    import app.middleware.auth as auth_mod

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload={"sub": clerk_user_id, "email": "u@example.com"},
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


def _stub_clerk_signed_out(monkeypatch) -> None:
    import app.middleware.auth as auth_mod

    fake_state = SimpleNamespace(
        is_signed_in=False,
        reason="token-invalid",
        payload=None,
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


def _seed_foods(mongo_collections) -> None:
    """Seed a small fixture set covering ranking edge cases."""
    foods = [
        {
            "food_id": "gh-banku",
            "name": "Banku",
            "alt_names": ["akpele", "fermented corn"],
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
            "food_id": "gh-kenkey-ga",
            "name": "Ga kenkey",
            "alt_names": ["WAFCT-09-302", "komi"],
            "kcal_per_100g": 175.0,
            "protein_g_per_100g": 3.5,
            "fat_g_per_100g": 0.8,
            "carbs_g_per_100g": 39.0,
            "portion_defaults": [{"label": "1 ball", "grams": 220}],
            "category": "staple",
            "source": "wafct",
            "source_confidence": "high",
        },
        {
            "food_id": "gh-jollof-rice",
            "name": "Jollof rice",
            "alt_names": ["jollof", "party rice"],
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
            "food_id": "gh-plantain-fried",
            "name": "Fried plantain",
            "alt_names": ["kaakro", "dodo"],
            "kcal_per_100g": 220.0,
            "protein_g_per_100g": 1.5,
            "fat_g_per_100g": 9.0,
            "carbs_g_per_100g": 32.0,
            "portion_defaults": [{"label": "1 serving", "grams": 150}],
            "category": "side_snack",
            "source": "wafct_composite",
            "source_confidence": "high",
        },
        {
            "food_id": "gh-banku-extra",
            "name": "Banku special",
            "alt_names": ["banku extra"],
            "kcal_per_100g": 155.0,
            "protein_g_per_100g": 3.0,
            "fat_g_per_100g": 1.0,
            "carbs_g_per_100g": 31.0,
            "portion_defaults": [{"label": "1 ball", "grams": 220}],
            "category": "staple",
            "source": "wafct_composite",
            "source_confidence": "low",
        },
    ]
    mongo_collections.ghana_foods.insert_many(foods)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_foods_no_query_returns_all(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch)
    r = client.get("/foods", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    out = r.get_json()
    assert "foods" in out
    assert len(out["foods"]) == 5
    # Alphabetical by name
    names = [f["name"] for f in out["foods"]]
    assert names == sorted(names)


def test_get_foods_substring_match_on_name(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch)
    r = client.get("/foods?q=banku", headers={"Authorization": "Bearer stub"})
    assert r.status_code == 200
    out = r.get_json()
    ids = [f["food_id"] for f in out["foods"]]
    assert "gh-banku" in ids
    assert "gh-banku-extra" in ids
    # Exact-match "Banku" ranks first.
    assert out["foods"][0]["food_id"] == "gh-banku"


def test_get_foods_alt_names_match(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch)
    r = client.get(
        "/foods?q=WAFCT-09-302", headers={"Authorization": "Bearer stub"}
    )
    assert r.status_code == 200
    out = r.get_json()
    ids = [f["food_id"] for f in out["foods"]]
    assert "gh-kenkey-ga" in ids


def test_get_foods_ranks_exact_match_first(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch)
    r = client.get("/foods?q=Banku", headers={"Authorization": "Bearer stub"})
    out = r.get_json()
    assert out["foods"][0]["food_id"] == "gh-banku"


def test_get_foods_respects_limit_clamp(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch)

    r99 = client.get("/foods?limit=99", headers={"Authorization": "Bearer stub"})
    assert r99.status_code == 200
    assert len(r99.get_json()["foods"]) == 5

    r0 = client.get("/foods?limit=0", headers={"Authorization": "Bearer stub"})
    assert r0.status_code == 200
    assert len(r0.get_json()["foods"]) == 1


def test_get_foods_case_insensitive(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch)
    r = client.get("/foods?q=JOLLOF", headers={"Authorization": "Bearer stub"})
    out = r.get_json()
    assert any(f["food_id"] == "gh-jollof-rice" for f in out["foods"])


def test_get_foods_empty_when_no_match(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_in(monkeypatch)
    r = client.get(
        "/foods?q=nonexistent-dish-zzzqq",
        headers={"Authorization": "Bearer stub"},
    )
    assert r.status_code == 200
    assert r.get_json()["foods"] == []


def test_get_foods_requires_auth_401(client, mongo_collections, monkeypatch):
    _seed_foods(mongo_collections)
    _stub_clerk_signed_out(monkeypatch)
    r = client.get("/foods", headers={"Authorization": "Bearer bad"})
    assert r.status_code == 401
