"""Clerk JWT verification middleware for FitGH Flask.

Phase 1 Walking Skeleton — WS-B.4. AUTH-06 requirement.

Encodes Gotcha G5 / Skeleton Invariant #2 EXACTLY as research §3.8 specifies:
the clerk-backend-api SDK's authenticate_request() requires an httpx.Request
(NOT Flask's request). The wrapper below constructs an httpx.Request from
flask.request.{method, url, headers} and passes it in.

This file is verbatim from .planning/phases/01-walking-skeleton/01-RESEARCH.md
§3.8 with two adaptations:
  1. Deferred Clerk client instantiation: research has _clerk constructed at
     module import; we lazy-init via _get_clerk() so the module imports
     cleanly when CLERK_SECRET_KEY is unset (e.g. pytest collection on a
     dev box without a Clerk account yet).
  2. Same lazy treatment for _authorized_parties.

The lazy-init is documented in the plan WS-B.4 acceptance: "Module imports
succeed even when CLERK_SECRET_KEY is unset (deferred check OR set a dev
stub in tests)."

Networkless property: clerk-backend-api caches the JWKS public key after the
first call (TTL ~1h); subsequent authenticate_request() calls validate the
signature locally without an outbound HTTPS hop. Verified per research §3.7.
"""

from __future__ import annotations

import os
from functools import wraps

import httpx

# clerk-backend-api 5.0.6 exposes AuthenticateRequestOptions at the package
# root, NOT at clerk_backend_api.jwks_helpers (the path quoted in research
# §3.8 was for an earlier SDK release; the new SDK refactored security types
# into clerk_backend_api.security.types and re-exports the relevant ones at
# the top level). Verified at runtime; deviation noted in SUMMARY.md.
from clerk_backend_api import AuthenticateRequestOptions, Clerk
from flask import current_app, g, jsonify, request

_clerk: Clerk | None = None
_authorized_parties: list[str] | None = None


def _get_clerk() -> Clerk:
    """Lazy-init the Clerk SDK client. Raises if CLERK_SECRET_KEY is unset."""
    global _clerk
    if _clerk is None:
        secret = os.environ.get("CLERK_SECRET_KEY")
        if not secret:
            raise RuntimeError(
                "CLERK_SECRET_KEY is not set; @require_auth cannot verify JWTs"
            )
        _clerk = Clerk(bearer_auth=secret)
    return _clerk


def _get_authorized_parties() -> list[str]:
    """Lazy-init the authorized-parties list from env / app config."""
    global _authorized_parties
    if _authorized_parties is None:
        # Prefer the Flask app config (set from Config dataclass) when running
        # inside a request; fall back to env for module-level scripts.
        try:
            cfg = current_app.config["FITGH"]
            _authorized_parties = list(cfg.CLERK_AUTHORIZED_PARTIES)
        except (RuntimeError, KeyError):
            raw = os.environ.get("CLERK_AUTHORIZED_PARTIES", "")
            _authorized_parties = [p.strip() for p in raw.split(",") if p.strip()]
    return _authorized_parties


def require_auth(f):
    """Verify the Clerk JWT on the inbound request, networkless.

    On success: sets g.clerk_user_id = JWT `sub` claim, then invokes the
    wrapped handler.
    On failure: returns 401 {error: 'unauthorized', reason: <state.reason>}.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        # CANONICAL FORM per research §3.8 / Gotcha G5. The clerk-backend-api
        # SDK only accepts httpx.Request — passing Flask's request object
        # directly raises a TypeError. Build an httpx.Request from flask.request
        # attributes; .url MUST be stringified (research §3.8 calls this out).
        httpx_req = httpx.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
        )
        state = _get_clerk().authenticate_request(
            httpx_req,
            AuthenticateRequestOptions(
                authorized_parties=_get_authorized_parties()
            ),
        )
        if not state.is_signed_in:
            # state.reason is an AuthErrorReason enum in clerk-backend-api 5.x;
            # str() gives the human-readable variant name. Plain `state.reason`
            # is NOT JSON-serializable (Rule 1 deviation logged in SUMMARY.md).
            reason = state.reason
            return (
                jsonify(
                    {
                        "error": "unauthorized",
                        "reason": str(reason) if reason is not None else None,
                    }
                ),
                401,
            )

        # JWT verified. `sub` is the Clerk user id (e.g. user_2abc...); stash
        # on g so the route handler can use it without re-decoding.
        g.clerk_user_id = state.payload.get("sub")
        # WS-E.2: also stash email if the JWT template includes it as a
        # claim. /me uses this for the sync-on-demand upsert; if absent here,
        # /me falls back to a one-time Clerk SDK fetch on the missing-user path.
        # Clerk session JWTs by default do NOT include email — customize the
        # JWT template in the Clerk dashboard (Sessions -> Customize session
        # token) and add: `"email": "{{user.primary_email_address}}"`.
        g.clerk_email = (
            state.payload.get("email")
            or state.payload.get("primary_email_address")
        )
        return f(*args, **kwargs)

    return wrapper
