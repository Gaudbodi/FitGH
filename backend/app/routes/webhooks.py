"""POST /webhooks/clerk — receives svix-verified Clerk webhooks from the BFF.

Phase 1 Walking Skeleton — empty shell for WS-B.2; WS-B.4 wires the
x-clerk-verified header check and WS-F.3 wires the user.created handler.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("webhooks", __name__)


@bp.post("/webhooks/clerk")
def clerk_webhook():
    """Stub — WS-B.4 will check x-clerk-verified header; WS-F.3 will upsert."""
    return jsonify({"error": "not_implemented"}), 501
