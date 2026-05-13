"""Flask routes for /profile (GET / POST / PATCH).

Phase 2 Plan 02 — Task P2-A.3.

  GET /profile     — returns the signed-in user's profile or 404 if missing
                     (frontend uses 404 to redirect to /onboarding).
  POST /profile    — creates / replaces the profile from the onboarding form
                     payload. Server-computes daily_kcal_target,
                     daily_protein_g_target, floor_hit; stamps clerk_id,
                     privacy_consent_at, created_at, updated_at.
  PATCH /profile   — partial edit; merges provided fields, recomputes
                     targets, updates updated_at. Returns 404 if no profile.

Trust anchor: @require_auth. The route NEVER reads clerk_id from the body
(T-02-01 / T-02-06). Pydantic ProfileCreate / ProfileUpdate enforce field
allow-listing via extra='forbid' (T-02-02). TDEE recompute on every write
(T-02-07). Cross-user isolation via clerk_id filter on every query (T-02-04).

Module imports `app.db` as a module reference (not the names directly) so
tests can monkey-patch `app.db.profiles` and have route handlers see the
patched value on next call. (Phase 1 had to patch both bindings; we adopt
the module-attribute pattern here to avoid that footgun.)
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError

from app import db as db_mod
from app.lib.tdee import daily_kcal_target, daily_protein_g_target
from app.middleware.auth import require_auth
from app.models.profile import ProfileCreate, ProfileUpdate

bp = Blueprint("profile", __name__)


def _safe_errors(e: ValidationError) -> list[dict]:
    """Coerce Pydantic ValidationError.errors() into a JSON-safe list.

    Pydantic's `ctx` field can contain the original ValueError instance, which
    Flask's JSON encoder cannot serialize. Replace each error's `ctx` with a
    dict of stringified values.
    """
    out = []
    for err in e.errors(include_url=False):
        safe = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err:
            safe["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        out.append(safe)
    return out


def _profile_to_json(doc: dict) -> dict:
    """Serialize a Mongo profile doc to JSON-safe dict.

    Mongo returns datetimes as native Python datetime; Flask's jsonify handles
    them via the default encoder, but we explicitly format as ISO-8601 UTC for
    a stable contract. The _id ObjectId is dropped (the FE keys on clerk_id).
    """
    out = {k: v for k, v in doc.items() if k != "_id"}
    for field in ("privacy_consent_at", "created_at", "updated_at"):
        if field in out and hasattr(out[field], "isoformat"):
            v = out[field]
            # Ensure UTC suffix
            out[field] = v.isoformat().replace("+00:00", "Z")
    return out


def _compute_targets(
    sex: str,
    weight_kg: float,
    height_cm: int,
    age: int,
    activity_level: str,
    primary_goal: str,
) -> dict:
    kcal = daily_kcal_target(
        sex=sex,  # type: ignore[arg-type]
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        activity_level=activity_level,  # type: ignore[arg-type]
        primary_goal=primary_goal,  # type: ignore[arg-type]
    )
    protein = daily_protein_g_target(weight_kg, primary_goal)  # type: ignore[arg-type]
    return {
        "daily_kcal_target": kcal["kcal_target"],
        "daily_protein_g_target": protein,
        "floor_hit": kcal["floor_hit"],
    }


@bp.get("/profile")
@require_auth
def get_profile():
    clerk_id = g.clerk_user_id
    doc = db_mod.profiles.find_one({"clerk_id": clerk_id})
    if doc is None:
        return jsonify({"error": "profile_not_found"}), 404
    return jsonify(_profile_to_json(doc)), 200


@bp.post("/profile")
@require_auth
def post_profile():
    clerk_id = g.clerk_user_id
    try:
        payload = ProfileCreate.model_validate_json(request.data)
    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "details": _safe_errors(e),
        }), 422

    targets = _compute_targets(
        sex=payload.sex,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        age=payload.age,
        activity_level=payload.activity_level,
        primary_goal=payload.primary_goal,
    )
    now = datetime.now(UTC)

    # Existing-profile case: keep created_at + privacy_consent_at stable.
    existing = db_mod.profiles.find_one({"clerk_id": clerk_id})
    created_at = existing["created_at"] if existing else now
    privacy_consent_at = (
        existing["privacy_consent_at"] if existing else now
    )

    doc = {
        "clerk_id": clerk_id,
        "name": payload.name,
        "sex": payload.sex,
        "height_cm": payload.height_cm,
        "weight_kg": payload.weight_kg,
        "age": payload.age,
        "timezone": payload.timezone,
        "locale": payload.locale,
        "activity_level": payload.activity_level,
        "primary_goal": payload.primary_goal,
        **targets,
        "privacy_consent_at": privacy_consent_at,
        "created_at": created_at,
        "updated_at": now,
    }

    db_mod.profiles.update_one(
        {"clerk_id": clerk_id},
        {"$set": doc},
        upsert=True,
    )

    return jsonify(_profile_to_json(doc)), 201


@bp.patch("/profile")
@require_auth
def patch_profile():
    clerk_id = g.clerk_user_id
    try:
        update = ProfileUpdate.model_validate_json(request.data)
    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "details": _safe_errors(e),
        }), 422

    existing = db_mod.profiles.find_one({"clerk_id": clerk_id})
    if existing is None:
        return jsonify({"error": "profile_not_found"}), 404

    update_dict = update.model_dump(exclude_unset=True)
    # Merge into existing doc to recompute targets from the FULL set of
    # post-patch values (don't just compute from the partial PATCH body).
    merged = {**existing, **update_dict}

    targets = _compute_targets(
        sex=merged["sex"],
        weight_kg=merged["weight_kg"],
        height_cm=merged["height_cm"],
        age=merged["age"],
        activity_level=merged["activity_level"],
        primary_goal=merged["primary_goal"],
    )
    now = datetime.now(UTC)

    set_fields = {**update_dict, **targets, "updated_at": now}
    db_mod.profiles.update_one(
        {"clerk_id": clerk_id},
        {"$set": set_fields},
    )

    updated = db_mod.profiles.find_one({"clerk_id": clerk_id})
    return jsonify(_profile_to_json(updated)), 200
