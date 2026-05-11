"""POST /webhooks/clerk — handler for Clerk user.created / user.deleted.

Phase 1 Walking Skeleton — WS-B.4 wires the x-clerk-verified header check;
WS-F.3 wires the user.created -> users upsert.

The svix signature verification happens on the Next.js BFF (see
frontend/src/app/api/webhooks/clerk/route.ts). When the BFF forwards a
verified payload here, it MUST include the `x-clerk-verified: true` header
(set in BFF code, not user-controlled — Flask's CORS allowlist + Vercel
private hop are the trust anchors).

T-01-01 / T-01-02 in the threat register: the real trust anchor is the
svix verify in the BFF. Flask checks the x-clerk-verified header as a
defence-in-depth signal but does NOT trust it for authentication.
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Blueprint, jsonify, request

from app.db import users

bp = Blueprint("webhooks", __name__)


@bp.post("/webhooks/clerk")
def clerk_webhook():
    """Receive a BFF-svix-verified Clerk event and update Mongo accordingly."""
    # Defence-in-depth: only the BFF sets x-clerk-verified. If absent, the
    # request bypassed our svix verify (or hit Flask directly).
    if request.headers.get("x-clerk-verified") != "true":
        return jsonify({"error": "unverified"}), 400

    evt = request.get_json(silent=True)
    if not evt or not isinstance(evt, dict):
        return jsonify({"error": "invalid_json"}), 400

    evt_type = evt.get("type")
    data = evt.get("data") or {}

    # Slice B fallback: users collection unwired. WS-C.2 removes this branch.
    if users is None:
        return jsonify({"error": "db_not_configured"}), 503

    if evt_type == "user.created":
        clerk_id = data.get("id")
        if not clerk_id:
            return jsonify({"error": "missing_user_id"}), 400
        email_addresses = data.get("email_addresses") or []
        email = (
            email_addresses[0].get("email_address")
            if email_addresses and isinstance(email_addresses[0], dict)
            else None
        )
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
        return jsonify({"ok": True}), 201

    if evt_type == "user.deleted":
        clerk_id = data.get("id")
        if not clerk_id:
            return jsonify({"error": "missing_user_id"}), 400
        users.delete_one({"clerk_id": clerk_id})
        return jsonify({"ok": True}), 200

    # Other event types (user.updated, session.*) are not handled in Phase 1.
    return jsonify({"ignored": evt_type}), 200
