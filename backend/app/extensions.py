"""Sentry initialization + PII scrubber for FitGH backend.

Phase 1 Walking Skeleton — WS-B.2.

This module is the implementation of skeleton invariant #3: Sentry PII scrubbers
present at commit 1, NOT retrofitted. The scrub() function MUST drop these keys
from every event before it leaves the process:

- request.headers.authorization      (Bearer JWTs — never log)
- user.email / user.username         (PII)
- extra.email / extra.user_id        (PII)
- breadcrumbs[].data.image           (image bytes from meal scans, Phase 4)
- breadcrumbs[].data.kcal            (kcal totals — privacy-sensitive)

Plan FLAG-2 (WS-B.5 test_sentry_scrubber.py) requires assertions for
breadcrumbs.data.kcal and breadcrumbs.data.image — folded in.
"""

from __future__ import annotations

from typing import Any, Mapping

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.pymongo import PyMongoIntegration

from app.config import Config


def scrub(event: dict[str, Any], hint: Mapping[str, Any]) -> dict[str, Any] | None:
    """Sentry before_send hook: strip PII + Authorization headers + meal data.

    Returns the (mutated) event, or None to drop it entirely. We never drop the
    event today — we just redact keys. If you want to drop entire event types
    (e.g. health-check 200s), add that logic here.
    """
    # 1) Request headers — never let Authorization leave the process.
    request = event.get("request")
    if isinstance(request, dict):
        headers = request.get("headers")
        if isinstance(headers, dict):
            # Both lowercase and TitleCase variants — Sentry normalizes but be safe.
            for key in list(headers.keys()):
                if key.lower() == "authorization":
                    headers.pop(key, None)

    # 2) user.* PII — Clerk gives us user IDs / emails as part of the session;
    #    never include them in Sentry context.
    user = event.get("user")
    if isinstance(user, dict):
        user.pop("email", None)
        user.pop("username", None)
        # Keep user.id only if it's the Clerk sub (opaque to humans) — but per
        # OBS-01 the safer default is to drop it too.
        user.pop("id", None)

    # 3) extra.* fields — devs may attach PII via sentry_sdk.set_extra().
    extra = event.get("extra")
    if isinstance(extra, dict):
        extra.pop("email", None)
        extra.pop("user_id", None)

    # 4) breadcrumbs — Phase 4 will emit breadcrumbs with image bytes / kcal
    #    totals; scrub their `data` payloads here so the contract holds from
    #    commit 1 (FLAG-2 from plan check).
    breadcrumbs = event.get("breadcrumbs")
    # Sentry can put breadcrumbs at event['breadcrumbs'] as either a list (old)
    # or {'values': [...]} (new). Handle both shapes.
    if isinstance(breadcrumbs, dict):
        values = breadcrumbs.get("values", [])
    elif isinstance(breadcrumbs, list):
        values = breadcrumbs
    else:
        values = []
    for crumb in values:
        if isinstance(crumb, dict):
            data = crumb.get("data")
            if isinstance(data, dict):
                data.pop("image", None)
                data.pop("kcal", None)
                data.pop("email", None)

    return event


def init_sentry(cfg: Config) -> None:
    """Initialize Sentry SDK with FitGH's scrubber + integrations.

    No-op if SENTRY_DSN_BACKEND is empty (e.g. in tests).
    """
    if not cfg.SENTRY_DSN_BACKEND:
        return

    sentry_sdk.init(
        dsn=cfg.SENTRY_DSN_BACKEND,
        # send_default_pii defaults to False but be explicit.
        send_default_pii=False,
        # Custom scrubber wins over send_default_pii defaults.
        before_send=scrub,
        # FlaskIntegration auto-instruments request handling; PyMongoIntegration
        # adds query traces.
        integrations=[FlaskIntegration(), PyMongoIntegration()],
        environment=cfg.FLASK_ENV,
        # Conservative tracing default for Phase 1; tune in Phase 7.
        traces_sample_rate=0.1,
    )
