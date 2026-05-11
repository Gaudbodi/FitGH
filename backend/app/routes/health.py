"""GET /health — liveness + Mongo connectivity check.

Phase 1 Walking Skeleton — WS-B.3 fills in the real ping; WS-B.2 lands the
empty blueprint shell so create_app() can register it.
"""

from __future__ import annotations

from flask import Blueprint

bp = Blueprint("health", __name__)


@bp.get("/health")
def health() -> dict:  # noqa: D401 — terse handler
    """Stubbed health response — Slice C / WS-B.3 wires real Mongo ping."""
    return {"ok": True, "mongo": "stubbed"}
