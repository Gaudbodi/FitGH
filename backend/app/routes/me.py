"""GET /me — authenticated user lookup.

Phase 1 Walking Skeleton — WS-B.4 wires @require_auth; WS-E.2 wires the real
Mongo read. AUTH-06 + SEC-04 requirements.

This file is verbatim from research §3.8 with one adaptation: a Slice B
fallback that returns 503 if the `users` collection isn't wired yet (which
happens when MONGODB_URI is unset). WS-C.2 will remove that fallback when
the URI becomes mandatory.
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from app.db import users
from app.middleware.auth import require_auth

bp = Blueprint("me", __name__)


@bp.get("/me")
@require_auth
def get_me():
    """Return the signed-in user's email from the Mongo `users` collection."""
    # Slice B: if MONGODB_URI is unset (db.py shim), `users` is None. Surface
    # this as 503 so the BFF can render a meaningful "service unavailable"
    # state rather than a NoneType AttributeError. WS-C.2 removes this branch.
    if users is None:
        return jsonify({"error": "db_not_configured"}), 503

    user = users.find_one({"clerk_id": g.clerk_user_id})
    if not user:
        # Expected on first sign-in BEFORE the Clerk user.created webhook
        # has landed (race window). The BFF treats 404 as "still setting up
        # your account" and shows a loading state on /dashboard.
        return jsonify({"error": "user_not_found"}), 404

    return jsonify({"email": user.get("email")})
