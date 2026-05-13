"""Flask routes for /meals (POST + GET + PATCH + DELETE).

Phase 3 Plan 03 — Tasks P3-B.2, P3-B.3, P3-B.4.

  POST   /meals       — create a meal in the day-1 multi-component shape.
  GET    /meals?date= — single-day list grouped by user's profile timezone.
  GET    /meals?days= — N-day grouped history (default 30, clamped 1..30).
  PATCH  /meals/<id>  — replace meal fields (components array swap atomic).
  DELETE /meals/<id>  — remove a meal (404 also covers cross-user reads).

Trust anchors:
  - @require_auth on every handler. user_id always = g.clerk_user_id; never
    read from request body, path, or query (T-03-01).
  - Pydantic *Create / *Update models with extra="forbid" block tampering
    (T-03-02 forged kcal_point on matched component).
  - Cross-user fetch returns 404 to avoid leaking existence (T-03-03).
  - Backdate validation: BACKDATE_MAX_DAYS days back, +5 min skew forward
    (T-03-04).
  - Unknown food_id rejected pre-write (T-03-07).
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError

from app import db as db_mod
from app.lib.meals import (
    BACKDATE_MAX_DAYS,
    compute_kcal_for_component,
    compute_protein_for_component,
    recompute_meal_totals,
)
from app.middleware.auth import require_auth
from app.models.meal import ComponentCreate, MealCreate, MealUpdate

bp = Blueprint("meals", __name__)

_FUTURE_SKEW = timedelta(minutes=5)


class _UnknownFoodIdError(Exception):
    """Raised by _resolve_component when a matched food_id is not catalogued."""

    def __init__(self, food_id: str):
        super().__init__(f"unknown food_id: {food_id}")
        self.food_id = food_id


def _safe_errors(e: ValidationError) -> list[dict]:
    out = []
    for err in e.errors(include_url=False):
        safe = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err:
            safe["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        out.append(safe)
    return out


def _validate_logged_at(supplied: datetime | None) -> datetime:
    """Return the resolved logged_at (UTC). Raises ValueError on backdate viol."""
    now = datetime.now(UTC)
    if supplied is None:
        return now
    # Ensure tz-aware UTC for comparison.
    if supplied.tzinfo is None:
        supplied = supplied.replace(tzinfo=UTC)
    earliest = now - timedelta(days=BACKDATE_MAX_DAYS)
    latest = now + _FUTURE_SKEW
    if supplied < earliest or supplied > latest:
        raise ValueError("logged_at_out_of_range")
    return supplied.astimezone(UTC)


def _resolve_component(cc: ComponentCreate) -> dict:
    """Build the persisted-shape Component dict from a ComponentCreate.

    Raises _UnknownFoodIdError when a matched food_id is not catalogued.
    """
    if cc.food_id is not None:
        food = db_mod.ghana_foods.find_one({"food_id": cc.food_id})
        if food is None:
            raise _UnknownFoodIdError(cc.food_id)
        return {
            "name": food["name"],
            "matched_food_id": cc.food_id,
            "portion_g": cc.portion_g,
            "kcal_low": None,
            "kcal_high": None,
            "kcal_point": compute_kcal_for_component(
                food["kcal_per_100g"], cc.portion_g
            ),
            "protein_g_point": compute_protein_for_component(
                food["protein_g_per_100g"], cc.portion_g
            ),
            "confidence": None,
            "source": "table",
        }
    # Free-text fall-back.
    return {
        "name": cc.name,
        "matched_food_id": None,
        "portion_g": cc.portion_g,
        "kcal_low": None,
        "kcal_high": None,
        "kcal_point": cc.kcal_point,
        "protein_g_point": 0,
        "confidence": None,
        "source": "user_corrected",
    }


def _meal_to_json(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    if "_id" in doc:
        out["id"] = str(doc["_id"])
    for ts_key in ("logged_at", "created_at", "updated_at"):
        if ts_key in out and hasattr(out[ts_key], "isoformat"):
            out[ts_key] = out[ts_key].isoformat().replace("+00:00", "Z")
    return out


def _local_date_str(dt: datetime, tz: str) -> str:
    """YYYY-MM-DD in the supplied timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(tz)).strftime("%Y-%m-%d")


def _group_by_local_date(meals_docs: list[dict], tz: str) -> list[dict]:
    """Group meals by user-local date, newest day first, empty days skipped."""
    buckets: dict[str, list[dict]] = {}
    for doc in meals_docs:
        d_str = _local_date_str(doc["logged_at"], tz)
        buckets.setdefault(d_str, []).append(doc)

    days = []
    for d_str in sorted(buckets.keys(), reverse=True):
        day_meals = sorted(buckets[d_str], key=lambda m: m["logged_at"])
        total_k = sum(int(m.get("total_kcal", 0)) for m in day_meals)
        total_p = sum(int(m.get("total_protein_g", 0)) for m in day_meals)
        days.append(
            {
                "date": d_str,
                "total_kcal": total_k,
                "total_protein_g": total_p,
                "meals": [_meal_to_json(m) for m in day_meals],
            }
        )
    return days


# ---------------------------------------------------------------------------
# POST /meals
# ---------------------------------------------------------------------------


@bp.post("/meals")
@require_auth
def post_meal():
    clerk_id = g.clerk_user_id
    try:
        payload = MealCreate.model_validate_json(request.data)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": _safe_errors(e)}), 422

    try:
        logged_at = _validate_logged_at(payload.logged_at)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422

    try:
        resolved = [_resolve_component(cc) for cc in payload.components]
    except _UnknownFoodIdError as ex:
        return (
            jsonify(
                {
                    "error": "unknown_food_id",
                    "details": {"food_id": ex.food_id},
                }
            ),
            422,
        )

    total_kcal, total_protein = recompute_meal_totals(resolved)
    now = datetime.now(UTC)
    doc = {
        "user_id": clerk_id,
        "logged_at": logged_at,
        "source": "manual",
        "components": resolved,
        "total_kcal": total_kcal,
        "total_protein_g": total_protein,
        "ai_metadata": None,
        "created_at": now,
        "updated_at": now,
    }
    result = db_mod.meals.insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify(_meal_to_json(doc)), 201
