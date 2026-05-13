"""Flask routes for /weights (POST log / GET history).

Phase 2 Plan 02 — Task P2-A.4.

  POST /weights — insert a WeightLog row AND update profile.weight_kg +
                  recompute daily_kcal_target / daily_protein_g_target /
                  floor_hit on the existing profile doc (D-WEIGHTLOG-ON-
                  DASHBOARD). Returns 409 no_profile when the user has not
                  finished onboarding.
  GET /weights  — return entries newest-first, default limit 30, max 100.

Trust anchor: @require_auth. user_id is always derived from
g.clerk_user_id; never from the body or query (T-02-04).
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError

from app import db as db_mod
from app.lib.tdee import daily_kcal_target, daily_protein_g_target
from app.middleware.auth import require_auth
from app.models.weight_log import WeightLogCreate

bp = Blueprint("weights", __name__)


def _safe_errors(e: ValidationError) -> list[dict]:
    out = []
    for err in e.errors(include_url=False):
        safe = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err:
            safe["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        out.append(safe)
    return out


def _weight_log_to_json(doc: dict) -> dict:
    out = {k: v for k, v in doc.items() if k != "_id"}
    if "logged_at" in out and hasattr(out["logged_at"], "isoformat"):
        out["logged_at"] = out["logged_at"].isoformat().replace("+00:00", "Z")
    return out


@bp.post("/weights")
@require_auth
def post_weight():
    clerk_id = g.clerk_user_id
    try:
        payload = WeightLogCreate.model_validate_json(request.data)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": _safe_errors(e)}), 422

    profile = db_mod.profiles.find_one({"clerk_id": clerk_id})
    if profile is None:
        # User must finish onboarding before logging weights — the dashboard
        # redirect-to-onboarding gate normally prevents this from happening,
        # but a forged BFF call would land here.
        return jsonify({"error": "no_profile"}), 409

    now = datetime.now(UTC)
    entry = {
        "user_id": clerk_id,
        "kg": payload.kg,
        "logged_at": now,
    }
    db_mod.weight_logs.insert_one(entry)

    # Recompute profile targets so the dashboard reflects the new weight.
    # Without this step the displayed kcal target goes stale until the user
    # navigates to /profile and re-saves (PROF-04 / PROF-07 mesh).
    new_targets = daily_kcal_target(
        sex=profile["sex"],
        weight_kg=payload.kg,
        height_cm=profile["height_cm"],
        age=profile["age"],
        activity_level=profile["activity_level"],
        primary_goal=profile["primary_goal"],
    )
    new_protein = daily_protein_g_target(payload.kg, profile["primary_goal"])
    db_mod.profiles.update_one(
        {"clerk_id": clerk_id},
        {
            "$set": {
                "weight_kg": payload.kg,
                "daily_kcal_target": new_targets["kcal_target"],
                "daily_protein_g_target": new_protein,
                "floor_hit": new_targets["floor_hit"],
                "updated_at": now,
            }
        },
    )

    return jsonify(_weight_log_to_json(entry)), 201


@bp.get("/weights")
@require_auth
def get_weights():
    clerk_id = g.clerk_user_id
    try:
        limit = int(request.args.get("limit", "30"))
    except ValueError:
        limit = 30
    limit = max(1, min(limit, 100))

    cursor = (
        db_mod.weight_logs.find({"user_id": clerk_id})
        .sort("logged_at", -1)
        .limit(limit)
    )
    entries = [_weight_log_to_json(d) for d in cursor]
    return jsonify({"entries": entries}), 200
