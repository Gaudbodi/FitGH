"""Idempotent seeder for the ghana_foods catalogue.

Phase 3 Plan 03 — Task P3-A.5.

The catalogue is read-only at runtime; updates happen out-of-band by:
  1. Edit `backend/seeds/ghana_foods.json`.
  2. Commit the edit to the repo.
  3. Run this script ONCE against production Atlas:
     `cd backend && .venv/Scripts/python.exe -m scripts.seed_ghana_foods`

The script is idempotent: re-running it with the same JSON content reports
`unchanged=25`; only changed rows are reported as `updated`.

Per the Phase 1 invariant — no `create_index` on module load. The two
catalogue indexes (food_id unique + name/alt_names text) are created HERE
inside `seed()` rather than in `app/db.py` so the Flask app boots without
side-effect index creation.

Defence-in-depth: each row is re-validated via Pydantic before write — a
hand-edited JSON typo or a stale schema mismatch surfaces with a clear
`ValidationError` rather than corrupting the DB.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pymongo import MongoClient
from pymongo.database import Database

from app.models.ghana_food import GhanaFood

_SEED_PATH = Path(__file__).resolve().parent.parent / "seeds" / "ghana_foods.json"


def seed(db: Database, foods: list[dict]) -> dict[str, int]:
    """Upsert each food by food_id, return {added, updated, unchanged} counts.

    Indexes are created (idempotent in Mongo when the same options are
    re-passed):
      - food_id unique
      - (name, alt_names) compound text index for the /foods search route
    """
    # Validate every row first so a bad entry aborts before any write.
    validated = [GhanaFood.model_validate(f) for f in foods]

    counts = {"added": 0, "updated": 0, "unchanged": 0}
    for food_obj, food_doc in zip(validated, foods):
        food_id = food_obj.food_id
        result = db.ghana_foods.update_one(
            {"food_id": food_id},
            {"$set": food_doc},
            upsert=True,
        )
        if result.upserted_id is not None:
            counts["added"] += 1
        elif result.modified_count > 0:
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1

    # Index creation lives in the seeder per the no-create_index-on-import
    # invariant. `create_index` is idempotent in MongoDB when options match.
    db.ghana_foods.create_index(
        [("food_id", 1)], unique=True, name="food_id_unique"
    )
    db.ghana_foods.create_index(
        [("name", "text"), ("alt_names", "text")], name="ghana_foods_text"
    )

    return counts


def main() -> None:
    """CLI entry point — operator runs against production Atlas."""
    uri = os.environ["MONGODB_URI"]
    client = MongoClient(uri, tls=True, serverSelectionTimeoutMS=10000)
    db = client["fitgh"]

    with _SEED_PATH.open("r", encoding="utf-8") as fh:
        foods = json.load(fh)

    print(f"Seeding ghana_foods from {_SEED_PATH} ({len(foods)} entries)...")
    counts = seed(db, foods)
    print(
        f"Done. added={counts['added']} updated={counts['updated']} "
        f"unchanged={counts['unchanged']}"
    )


if __name__ == "__main__":
    main()
