"""Tests for the idempotent Ghana foods seeder.

Phase 3 Plan 03 — Task P3-A.5.

The seeder upserts each ghana_foods.json entry by `food_id` and creates the
unique food_id index plus the text-search index on (name, alt_names).
"""

from __future__ import annotations

import json
from pathlib import Path

import mongomock


def _load_seed_json() -> list[dict]:
    seed_path = Path(__file__).resolve().parent.parent / "seeds" / "ghana_foods.json"
    return json.loads(seed_path.read_text())


def _fake_db():
    return mongomock.MongoClient()["fitgh_test"]


def test_seed_inserts_25_into_empty_db():
    from scripts.seed_ghana_foods import seed

    db = _fake_db()
    foods = _load_seed_json()
    counts = seed(db, foods)
    assert counts["added"] == 25
    assert counts["updated"] == 0
    assert counts["unchanged"] == 0
    assert db.ghana_foods.count_documents({}) == 25


def test_seed_is_idempotent_second_run_zero_added():
    from scripts.seed_ghana_foods import seed

    db = _fake_db()
    foods = _load_seed_json()
    seed(db, foods)
    counts2 = seed(db, foods)
    assert counts2["added"] == 0
    assert counts2["updated"] == 0
    assert counts2["unchanged"] == 25
    assert db.ghana_foods.count_documents({}) == 25


def test_seed_upserts_changed_entry():
    from scripts.seed_ghana_foods import seed

    db = _fake_db()
    foods = _load_seed_json()
    seed(db, foods)
    # Mutate one entry's kcal_per_100g and re-seed.
    foods2 = [dict(f) for f in foods]
    foods2[0]["kcal_per_100g"] = foods2[0]["kcal_per_100g"] + 5.0
    counts = seed(db, foods2)
    assert counts["added"] == 0
    assert counts["updated"] == 1
    assert counts["unchanged"] == 24
    stored = db.ghana_foods.find_one({"food_id": foods2[0]["food_id"]})
    assert stored["kcal_per_100g"] == foods2[0]["kcal_per_100g"]


def test_seed_creates_indexes():
    from scripts.seed_ghana_foods import seed

    db = _fake_db()
    foods = _load_seed_json()
    seed(db, foods)
    idx_names = set(db.ghana_foods.index_information().keys())
    assert "food_id_unique" in idx_names
    assert "ghana_foods_text" in idx_names


def test_seed_rejects_invalid_entry():
    """Defence-in-depth: bad entries fail before write."""
    import pytest
    from pydantic import ValidationError

    from scripts.seed_ghana_foods import seed

    db = _fake_db()
    foods = _load_seed_json()
    bad = [dict(f) for f in foods]
    bad[0]["food_id"] = "BAD-ID-FORMAT"  # violates regex
    with pytest.raises(ValidationError):
        seed(db, bad)
