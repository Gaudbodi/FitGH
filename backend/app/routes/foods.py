"""Flask routes for /foods (GET search over the read-only Ghana catalogue).

Phase 3 Plan 03 — Task P3-B.1.

The `ghana_foods` collection is read-only at runtime — it is populated by
`scripts.seed_ghana_foods` and edited by the operator out-of-band. There is
no POST/PATCH/DELETE on this resource by design.

The /foods route is `@require_auth`-protected (T-03-05): the catalogue is
not user-private but exposing it to unauthenticated scrapers is unnecessary.
The catalogue size is bounded to 25 entries so a full scan is cheap.

Ranking is done in Python (small in-memory sort over the result set) rather
than via Mongo's $text index — the result-set is at most 25 entries and the
relevance algorithm is tailored to the catalogue size. The seeder still
creates the text index for forward compat / search performance at scale.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app import db as db_mod
from app.middleware.auth import require_auth

bp = Blueprint("foods", __name__)


def _food_to_json(doc: dict) -> dict:
    """Strip the Mongo `_id` field for the JSON response."""
    return {k: v for k, v in doc.items() if k != "_id"}


def _rank(food: dict, q: str) -> tuple[int, str]:
    """Lower rank tuples sort first.

    0 = name exact match
    1 = name starts with q
    2 = name contains q
    3 = alt_name contains q
    """
    name_l = food["name"].lower()
    if name_l == q:
        return (0, name_l)
    if name_l.startswith(q):
        return (1, name_l)
    if q in name_l:
        return (2, name_l)
    return (3, name_l)


def _matches(food: dict, q: str) -> bool:
    """Case-insensitive substring match on name or any alt_name."""
    if q in food["name"].lower():
        return True
    for alt in food.get("alt_names") or []:
        if q in alt.lower():
            return True
    return False


@bp.get("/foods")
@require_auth
def get_foods():
    q_raw = request.args.get("q", "").strip()
    try:
        limit = int(request.args.get("limit", "10"))
    except ValueError:
        limit = 10
    # Clamp 1..25 per T-03-05.
    limit = max(1, min(limit, 25))

    cursor = db_mod.ghana_foods.find({})
    foods = list(cursor)

    if q_raw:
        q = q_raw.lower()
        foods = [f for f in foods if _matches(f, q)]
        foods.sort(key=lambda f: _rank(f, q))
    else:
        foods.sort(key=lambda f: f["name"].lower())

    foods = foods[:limit]
    return jsonify({"foods": [_food_to_json(f) for f in foods]}), 200
