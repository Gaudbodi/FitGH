"""GET /me — authenticated user lookup with sync-on-demand upsert.

Phase 1 Walking Skeleton — WS-E.2 (Render-only rewrite 2026-05-12).

Replaces the deprecated user.created webhook (WS-E.1 deleted it). The user
document in MongoDB is created lazily the first time the signed-in user
hits /me — no webhook endpoint to host, no signature verification path.

Email source for the upsert:
  1) `g.clerk_email` — populated by @require_auth from the JWT `email` claim
     when present (requires the Clerk JWT template to include
     `{{user.primary_email_address}}`).
  2) Fallback: a one-time Clerk SDK fetch on the missing-user path. This
     adds one HTTPS hop the very first time a user signs in; steady-state
     /me calls are networkless because the doc already exists.

The 503 `db_not_configured` branch was deleted — `db.py` raises KeyError
at import time if `MONGODB_URI` is unset, so `users` is never None.

AUTH-06 + SC-1 (ROADMAP Phase 1 — `/dashboard` shows their email).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from flask import Blueprint, g, jsonify

from app import db as db_mod
from app.db import users
from app.middleware.auth import require_auth

bp = Blueprint("me", __name__)

_log = logging.getLogger(__name__)


def _fetch_email_from_clerk(clerk_user_id: str) -> str | None:
    """One-time fetch of a user's primary email from Clerk's API.

    Called only when /me hits the missing-user path AND the JWT didn't carry
    an email claim. Steady-state /me requests never reach this function.
    Returns None on any failure (Clerk SDK error, no email_addresses, etc.)
    so the upsert can still proceed with email=None and the dashboard can
    render a degraded "Signed in" message.
    """
    try:
        from app.middleware.auth import _get_clerk

        clerk = _get_clerk()
        user = clerk.users.get(user_id=clerk_user_id)
        addrs = getattr(user, "email_addresses", None) or []
        if addrs:
            primary = addrs[0]
            return getattr(primary, "email_address", None)
    except Exception as e:  # pragma: no cover — defensive
        _log.warning(
            "clerk SDK fetch failed for %s: %s", clerk_user_id, e
        )
    return None


@bp.get("/me")
@require_auth
def get_me():
    """Return the signed-in user's email; upsert the user doc on first call."""
    clerk_id = g.clerk_user_id
    doc = users.find_one({"clerk_id": clerk_id})
    if doc is not None:
        return jsonify({"email": doc.get("email")})

    # First-time sign-in: upsert from the JWT email claim, or fall back to
    # a Clerk SDK fetch. Sync-on-demand replaces the deprecated webhook.
    email = getattr(g, "clerk_email", None) or _fetch_email_from_clerk(clerk_id)
    now = datetime.now(UTC)
    users.update_one(
        {"clerk_id": clerk_id},
        {
            "$setOnInsert": {
                "clerk_id": clerk_id,
                "email": email,
                "created_at": now,
            },
            "$set": {"updated_at": now},
        },
        upsert=True,
    )
    return jsonify({"email": email})


@bp.delete("/me")
@require_auth
def delete_me():
    """Cascade-delete the signed-in user's FitGH data + Clerk auth record.

    Phase 2 Plan 02 — Task P2-A.5.

    Trust anchor: g.clerk_user_id is set by @require_auth from the verified
    JWT. The endpoint NEVER reads clerk_id from request body or query
    (T-02-01 / T-02-06). Steps:

      1. weight_logs.delete_many({user_id})  — captures deleted count
      2. profiles.delete_one({clerk_id})     — 0 or 1
      3. users.delete_one({clerk_id})        — 0 or 1
      4. clerk.users.delete(user_id=...)     — Clerk SDK

    If step 4 fails, Mongo data is already deleted (best-effort cascade);
    return 502 with {error: clerk_delete_failed, mongo_deleted: true} so
    the FE can show the user a clear "data deleted, auth not" message.

    Idempotent: re-calling after a successful delete returns success because
    Mongo deletes are no-ops and the Clerk SDK call is wrapped in a 404-
    tolerant try/except.

    Per D-NO-WEBHOOKS + memory/render-only-rewrite: this is the ONLY path
    that deletes a Clerk user. There is no user.deleted webhook handler.
    """
    clerk_id = g.clerk_user_id

    weight_count = db_mod.weight_logs.delete_many({"user_id": clerk_id}).deleted_count
    profile_count = db_mod.profiles.delete_one({"clerk_id": clerk_id}).deleted_count
    user_count = db_mod.users.delete_one({"clerk_id": clerk_id}).deleted_count

    # Clerk SDK delete — best-effort, idempotent. Errors after this point
    # are reported but Mongo data is already gone.
    clerk_deleted = False
    clerk_error: str | None = None
    try:
        from app.middleware.auth import _get_clerk

        _get_clerk().users.delete(user_id=clerk_id)
        clerk_deleted = True
    except Exception as e:  # noqa: BLE001 — broad on purpose; we report it
        # Treat "already deleted" (HTTP 404 from Clerk) as success.
        msg = str(e)
        status_code = getattr(e, "status_code", None)
        if status_code == 404 or "not found" in msg.lower():
            _log.info("Clerk user %s already absent; treating delete as success", clerk_id)
            clerk_deleted = True
        else:
            _log.warning(
                "Clerk users.delete failed for %s: %s", clerk_id, msg
            )
            clerk_error = msg

    if not clerk_deleted:
        return (
            jsonify({
                "error": "clerk_delete_failed",
                "mongo_deleted": True,
                "detail": clerk_error,
                "deleted": {
                    "weight_logs": weight_count,
                    "profile": profile_count,
                    "user": user_count,
                    "clerk": False,
                },
            }),
            502,
        )

    return jsonify({
        "ok": True,
        "deleted": {
            "weight_logs": weight_count,
            "profile": profile_count,
            "user": user_count,
            "clerk": True,
        },
    }), 200
