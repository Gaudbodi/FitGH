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
from app.lib.streak import compute_streak
from app.middleware.auth import require_auth
from app.models.meal import ComponentCreate, MealCreate, MealUpdate
from app.models.vision import AiMetadata

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


def _resolve_component(cc: ComponentCreate, *, meal_source: str = "manual") -> dict:
    """Build the persisted-shape Component dict from a ComponentCreate.

    Raises _UnknownFoodIdError when a matched food_id is not catalogued.

    Phase 4 (ai_vision path): when `meal_source == "ai_vision"`, the
    vision-only fields (kcal_low, kcal_high, confidence) are carried
    through to the persisted shape. The `source` field flips to
    "llm_then_table_rematch" (matched) or "user_corrected" (free-text).
    kcal_point is STILL server-computed from the table on the matched
    path (T-04-05 trust anchor).
    """
    is_vision = meal_source == "ai_vision"
    if cc.food_id is not None:
        food = db_mod.ghana_foods.find_one({"food_id": cc.food_id})
        if food is None:
            raise _UnknownFoodIdError(cc.food_id)
        return {
            "name": food["name"],
            "matched_food_id": cc.food_id,
            "portion_g": cc.portion_g,
            "kcal_low": cc.kcal_low if is_vision else None,
            "kcal_high": cc.kcal_high if is_vision else None,
            "kcal_point": compute_kcal_for_component(
                food["kcal_per_100g"], cc.portion_g
            ),
            "protein_g_point": compute_protein_for_component(
                food["protein_g_per_100g"], cc.portion_g
            ),
            "confidence": cc.confidence if is_vision else None,
            "source": "llm_then_table_rematch" if is_vision else "table",
        }
    # Free-text fall-back.
    return {
        "name": cc.name,
        "matched_food_id": None,
        "portion_g": cc.portion_g,
        "kcal_low": cc.kcal_low if is_vision else None,
        "kcal_high": cc.kcal_high if is_vision else None,
        "kcal_point": cc.kcal_point,
        "protein_g_point": 0,
        "confidence": cc.confidence if is_vision else None,
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
        resolved = [
            _resolve_component(cc, meal_source=payload.source)
            for cc in payload.components
        ]
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

    # Phase 4: AiMetadata.extra="ignore" drops unknown client-supplied
    # keys silently (T-04-05); the persisted shape is the canonical
    # sub-doc Phase 3's Meal.ai_metadata reserved.
    ai_meta_persisted: dict | None = None
    if payload.source == "ai_vision" and payload.ai_metadata is not None:
        try:
            ai_meta_persisted = AiMetadata.model_validate(
                payload.ai_metadata
            ).model_dump()
        except ValidationError:
            # Bad ai_metadata is non-fatal — the meal still saves, just
            # without provenance. Logging is fine; not user-facing.
            ai_meta_persisted = None

    total_kcal, total_protein = recompute_meal_totals(resolved)
    now = datetime.now(UTC)
    doc = {
        "user_id": clerk_id,
        "logged_at": logged_at,
        "source": payload.source,
        "components": resolved,
        "total_kcal": total_kcal,
        "total_protein_g": total_protein,
        "ai_metadata": ai_meta_persisted,
        "created_at": now,
        "updated_at": now,
    }
    result = db_mod.meals.insert_one(doc)
    doc["_id"] = result.inserted_id

    # Phase 5 — recompute the soft-streak on the profile doc (DASH-06).
    # Streak day = server-now in the user's local TZ; explicitly NOT the
    # meal's `logged_at` (T-05-07 — backdated meals MUST NOT rewrite
    # streak history). Profile may be missing entirely if a forged BFF
    # call lands before onboarding (defensive; the FE gate normally
    # prevents this).
    profile = db_mod.profiles.find_one({"clerk_id": clerk_id})
    if profile is not None:
        tz = profile.get("timezone") or "UTC"
        new_count, new_state, new_last = compute_streak(
            now_utc=now,
            tz=tz,
            last_logged_at_utc=profile.get("streak_last_logged_at"),
            current_count=int(profile.get("streak_count", 0)),
            current_state=profile.get("streak_state", "active"),
        )
        db_mod.profiles.update_one(
            {"clerk_id": clerk_id},
            {
                "$set": {
                    "streak_count": new_count,
                    "streak_state": new_state,
                    "streak_last_logged_at": new_last,
                    "updated_at": now,
                }
            },
        )

    return jsonify(_meal_to_json(doc)), 201


# ---------------------------------------------------------------------------
# GET /meals
# ---------------------------------------------------------------------------


def _profile_timezone(clerk_id: str) -> str | None:
    profile = db_mod.profiles.find_one({"clerk_id": clerk_id})
    if profile is None:
        return None
    return profile.get("timezone") or "UTC"


@bp.get("/meals")
@require_auth
def get_meals():
    clerk_id = g.clerk_user_id
    date_str = request.args.get("date")

    if date_str is not None:
        # Single-day mode.
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "invalid_date_param"}), 422

        tz = _profile_timezone(clerk_id)
        if tz is None:
            return jsonify({"error": "no_profile"}), 422

        zone = ZoneInfo(tz)
        start_local = datetime.combine(target_date, time.min).replace(tzinfo=zone)
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(UTC)
        end_utc = end_local.astimezone(UTC)

        cursor = db_mod.meals.find(
            {
                "user_id": clerk_id,
                "logged_at": {"$gte": start_utc, "$lt": end_utc},
            }
        ).sort("logged_at", 1)
        docs = list(cursor)
        total_k = sum(int(m.get("total_kcal", 0)) for m in docs)
        total_p = sum(int(m.get("total_protein_g", 0)) for m in docs)
        return (
            jsonify(
                {
                    "date": date_str,
                    "total_kcal": total_k,
                    "total_protein_g": total_p,
                    "meals": [_meal_to_json(m) for m in docs],
                }
            ),
            200,
        )

    # N-day grouped history mode.
    try:
        days = int(request.args.get("days", "30"))
    except ValueError:
        days = 30
    days = max(1, min(days, 30))

    tz = _profile_timezone(clerk_id)
    if tz is None:
        return jsonify({"error": "no_profile"}), 422

    zone = ZoneInfo(tz)
    now_local = datetime.now(UTC).astimezone(zone)
    today_local_midnight = datetime.combine(now_local.date(), time.min).replace(
        tzinfo=zone
    )
    start_local = today_local_midnight - timedelta(days=days - 1)
    end_local = today_local_midnight + timedelta(days=1)
    start_utc = start_local.astimezone(UTC)
    end_utc = end_local.astimezone(UTC)

    cursor = db_mod.meals.find(
        {
            "user_id": clerk_id,
            "logged_at": {"$gte": start_utc, "$lt": end_utc},
        }
    ).sort("logged_at", -1)
    docs = list(cursor)
    return jsonify({"days": _group_by_local_date(docs, tz)}), 200


# ---------------------------------------------------------------------------
# PATCH /meals/<id>
# ---------------------------------------------------------------------------


def _parse_meal_id(raw: str) -> ObjectId | None:
    try:
        return ObjectId(raw)
    except (InvalidId, TypeError):
        return None


@bp.patch("/meals/<id>")
@require_auth
def patch_meal(id):  # noqa: A002
    """Replace meal fields. PATCH semantics:

    - When `components` is supplied, the array is REPLACED ATOMICALLY
      (D-PATCH-REPLACES-COMPONENTS / planner-flagged risk #2 — the FE always
      re-sends the full edited list; a partial PATCH with one component
      would nuke the rest, which is the simpler / less-bug-prone contract).
    - When `logged_at` is supplied, the backdate validator runs (T-03-04).
    - Cross-user ownership check returns 404 (T-03-03), never 403, to avoid
      leaking existence.
    """
    clerk_id = g.clerk_user_id
    oid = _parse_meal_id(id)
    if oid is None:
        return jsonify({"error": "invalid_meal_id"}), 422

    existing = db_mod.meals.find_one({"_id": oid, "user_id": clerk_id})
    if existing is None:
        return jsonify({"error": "meal_not_found"}), 404

    try:
        payload = MealUpdate.model_validate_json(request.data)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": _safe_errors(e)}), 422

    set_fields: dict = {}

    if payload.logged_at is not None:
        try:
            set_fields["logged_at"] = _validate_logged_at(payload.logged_at)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 422

    if payload.components is not None:
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
        set_fields["components"] = resolved
        set_fields["total_kcal"] = total_kcal
        set_fields["total_protein_g"] = total_protein

    set_fields["updated_at"] = datetime.now(UTC)
    db_mod.meals.update_one(
        {"_id": oid, "user_id": clerk_id}, {"$set": set_fields}
    )
    refreshed = db_mod.meals.find_one({"_id": oid, "user_id": clerk_id})
    return jsonify(_meal_to_json(refreshed)), 200


# ---------------------------------------------------------------------------
# DELETE /meals/<id>
# ---------------------------------------------------------------------------


@bp.delete("/meals/<id>")
@require_auth
def delete_meal(id):  # noqa: A002
    clerk_id = g.clerk_user_id
    oid = _parse_meal_id(id)
    if oid is None:
        return jsonify({"error": "invalid_meal_id"}), 422

    existing = db_mod.meals.find_one({"_id": oid, "user_id": clerk_id})
    if existing is None:
        return jsonify({"error": "meal_not_found"}), 404

    db_mod.meals.delete_one({"_id": oid, "user_id": clerk_id})
    return jsonify({"ok": True, "deleted_id": id}), 200
