"""GET /health — liveness + Mongo connectivity check.

Phase 1 Walking Skeleton — WS-B.3 + WS-C.2 (stub branch removed).

Reports:
  - {ok: True, mongo: 'connected'}             when ping succeeds.
  - {ok: False, mongo: 'error', detail: type}  on connection error.

The /health endpoint is the canary used by Fly.io's HTTP healthcheck (fly.toml,
WS-G.2) — its job is to fail fast (5s timeout) when Mongo is unreachable so
Fly can route around the bad machine.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from app.db import client

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """Liveness + Mongo connectivity."""
    try:
        # Lightweight ping against the admin db; obeys serverSelectionTimeoutMS
        # configured at the singleton (5s in db.py).
        client.admin.command("ping")
    except Exception as e:  # pylint: disable=broad-except
        # Don't leak the URI / credentials in the error message — keep detail terse.
        return (
            jsonify({"ok": False, "mongo": "error", "detail": type(e).__name__}),
            503,
        )

    return jsonify({"ok": True, "mongo": "connected"}), 200
