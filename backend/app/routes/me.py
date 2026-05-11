"""GET /me — authenticated user lookup.

Phase 1 Walking Skeleton — empty shell for WS-B.2 blueprint registration;
WS-B.4 wires the @require_auth decorator and WS-E.2 wires the real Mongo read.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("me", __name__)


@bp.get("/me")
def get_me():
    """Stub — WS-B.4 will gate this with @require_auth."""
    return jsonify({"error": "not_implemented"}), 501
