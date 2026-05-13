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
