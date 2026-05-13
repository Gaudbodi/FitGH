"""Typed config object for the FitGH Flask backend.

Phase 1 Walking Skeleton — WS-B.2.

Reads ALL required env vars at construction time. Fail-loud (raises on startup)
if a required var is missing, NOT fail-on-first-request — per the plan's
"fail-loud" decision in WS-B.2 acceptance.

Optional vars (e.g. MONGODB_URI in Slice B before Slice C wires Atlas) are
read with .get(); the rest are mandatory via direct subscript.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv(name: str, default: str = "") -> list[str]:
    """Read a comma-separated env var and return a stripped, non-empty list."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    """Runtime configuration for the Flask backend.

    All fields are read from environment by default. Tests may construct Config()
    after monkey-patching env, or pass an explicit Config(...) to create_app().
    """

    # Mongo connection. Optional in Slice B (db.py shims to None); Slice C/WS-C.2
    # removes the shim and the module-level singleton will raise if this is None.
    MONGODB_URI: str | None = field(
        default_factory=lambda: os.environ.get("MONGODB_URI")
    )

    # Clerk JWT verification. CLERK_SECRET_KEY is the API key used to fetch the
    # JWKS public key (one-time at startup); the actual per-request verification
    # is networkless via the cached public key.
    CLERK_SECRET_KEY: str = field(
        default_factory=lambda: os.environ.get("CLERK_SECRET_KEY", "")
    )
    # CSV of allowed `azp` (authorized parties) values on the JWT.
    CLERK_AUTHORIZED_PARTIES: list[str] = field(
        default_factory=lambda: _csv("CLERK_AUTHORIZED_PARTIES")
    )
    # (CLERK_WEBHOOK_SECRET removed 2026-05-12: webhook route deleted in
    # WS-E.1; sync-on-demand inside /me replaces the user.created upsert.)

    # CORS allowlist (SEC-03). NEVER '*' with credentials.
    # Optional under the Render-only architecture — the BFF and Flask are on
    # different Render hostnames but the browser only ever calls the BFF
    # (same-origin), so Flask has no cross-origin browser callers in v1.
    # If empty, Flask-CORS rejects all cross-origin browser requests, which
    # is the intended posture.
    CORS_ALLOWED_ORIGINS: list[str] = field(
        default_factory=lambda: _csv("CORS_ALLOWED_ORIGINS")
    )

    # Sentry DSN; empty disables Sentry init (useful for tests).
    SENTRY_DSN_BACKEND: str = field(
        default_factory=lambda: os.environ.get("SENTRY_DSN_BACKEND", "")
    )

    FLASK_ENV: str = field(
        default_factory=lambda: os.environ.get("FLASK_ENV", "production")
    )

    # Phase 4 — Image -> Kcal Core Loop.
    #
    # ANTHROPIC_API_KEY: Sonnet 4.6 vision API. Mandatory in production
    #   (validated below); tests use a stub via conftest.
    # LLM_VISION_MODEL: env-pinned per CONTEXT D-VISION-MODEL-PIN. Bumping
    #   requires updating MODEL_PRICING_PER_1K in app/lib/vision.py AND
    #   re-running the golden set (Phase 7).
    # VISION_DAILY_CAP_USD: global circuit-breaker cap; default $5/day in
    #   code, overridable per environment.
    # COST_ALERT_WEBHOOK_URL: optional Discord/Slack incoming webhook.
    #   When unset, alerts WARN-log to Render stdout (still observable).
    ANTHROPIC_API_KEY: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )
    LLM_VISION_MODEL: str = field(
        default_factory=lambda: os.environ.get("LLM_VISION_MODEL", "claude-sonnet-4-6")
    )
    VISION_DAILY_CAP_USD: float = field(
        default_factory=lambda: float(
            os.environ.get("VISION_DAILY_CAP_USD", "5.0")
        )
    )
    COST_ALERT_WEBHOOK_URL: str = field(
        default_factory=lambda: os.environ.get("COST_ALERT_WEBHOOK_URL", "")
    )

    def validate(self) -> None:
        """Assert that all REQUIRED env vars are set.

        Called by create_app() at startup (when not in development). Tests may
        skip this by constructing Config() directly without calling validate().

        2026-05-12 rewrite (WS-E.4): CORS_ALLOWED_ORIGINS is no longer
        mandatory in production — under the Render-only architecture the BFF
        and Flask are on different hosts but the browser only ever calls the
        BFF (same-origin), so Flask has no cross-origin browser callers in v1.
        """
        # In production every var below is mandatory.
        if self.FLASK_ENV == "production":
            missing: list[str] = []
            if not self.CLERK_SECRET_KEY:
                missing.append("CLERK_SECRET_KEY")
            if not self.CLERK_AUTHORIZED_PARTIES:
                missing.append("CLERK_AUTHORIZED_PARTIES")
            if not self.MONGODB_URI:
                missing.append("MONGODB_URI")
            # Phase 4 — vision API key is mandatory in production. The
            # /meals/scan route returns 503 without it (anthropic SDK
            # construction fails fast), but failing at startup is
            # preferable to confusing-503s in the field.
            if not self.ANTHROPIC_API_KEY:
                missing.append("ANTHROPIC_API_KEY")
            if missing:
                raise RuntimeError(
                    f"Missing required env vars: {', '.join(missing)}"
                )
