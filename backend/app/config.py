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
    # Svix webhook signing secret (used only inside the Flask handler if we ever
    # accept the webhook directly; in v1 the BFF does the svix verify).
    CLERK_WEBHOOK_SECRET: str = field(
        default_factory=lambda: os.environ.get("CLERK_WEBHOOK_SECRET", "")
    )

    # CORS allowlist (SEC-03). NEVER '*' with credentials.
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

    def validate(self) -> None:
        """Assert that all REQUIRED env vars are set.

        Called by create_app() at startup (when not in development). Tests may
        skip this by constructing Config() directly without calling validate().
        """
        # In production every var below is mandatory.
        if self.FLASK_ENV == "production":
            missing: list[str] = []
            if not self.CLERK_SECRET_KEY:
                missing.append("CLERK_SECRET_KEY")
            if not self.CLERK_AUTHORIZED_PARTIES:
                missing.append("CLERK_AUTHORIZED_PARTIES")
            if not self.CORS_ALLOWED_ORIGINS:
                missing.append("CORS_ALLOWED_ORIGINS")
            if not self.MONGODB_URI:
                missing.append("MONGODB_URI")
            if missing:
                raise RuntimeError(
                    f"Missing required env vars: {', '.join(missing)}"
                )
