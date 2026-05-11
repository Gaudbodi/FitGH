"""Tests for the Sentry before_send PII scrubber (OBS-01).

WS-B.5 acceptance (plus FLAG-2 from plan check folded in):
- Removes request.headers.authorization (case-insensitive).
- Removes user.email and user.username (and user.id per our defensive default).
- Removes extra.email and extra.user_id.
- Removes breadcrumbs[].data.image  (Phase 4 vision events — pre-emptive).
- Removes breadcrumbs[].data.kcal   (Phase 4 vision events — pre-emptive).

These tests EXECUTE the scrub() function directly with synthetic events.
"""

from __future__ import annotations

from app.extensions import scrub


def test_scrubs_authorization_header_lowercase():
    event = {
        "request": {"headers": {"authorization": "Bearer leaked.jwt.xyz"}},
    }
    out = scrub(event, hint={})
    assert out is not None
    assert "authorization" not in out["request"]["headers"]


def test_scrubs_authorization_header_titlecase():
    """Some libraries TitleCase headers; the scrubber must catch both."""
    event = {
        "request": {"headers": {"Authorization": "Bearer leaked.jwt.xyz"}},
    }
    out = scrub(event, hint={})
    assert "Authorization" not in out["request"]["headers"]


def test_scrubs_user_email_and_username_and_id():
    event = {
        "user": {
            "email": "user@example.com",
            "username": "user",
            "id": "user_2abc",
        }
    }
    out = scrub(event, hint={})
    user = out["user"]
    assert "email" not in user
    assert "username" not in user
    assert "id" not in user


def test_scrubs_extra_email_and_user_id():
    event = {"extra": {"email": "u@x.com", "user_id": "user_2abc", "other": "kept"}}
    out = scrub(event, hint={})
    extra = out["extra"]
    assert "email" not in extra
    assert "user_id" not in extra
    # Non-PII keys are preserved.
    assert extra["other"] == "kept"


def test_scrubs_breadcrumb_data_kcal_and_image():
    """FLAG-2 from plan check: kcal + image breadcrumbs MUST be redacted.

    Phase 4 (vision) emits breadcrumbs with data.kcal totals and data.image
    bytes. Even though Phase 1 produces no such breadcrumbs, the scrubber
    contract must be in place from commit 1 so retrofitting in Phase 4
    is not required.
    """
    event = {
        "breadcrumbs": {
            "values": [
                {
                    "category": "vision",
                    "message": "scan finished",
                    "data": {
                        "image": b"\xff\xd8\xff\xe0 jpeg bytes here",
                        "kcal": 540,
                        "duration_ms": 1850,  # non-PII, MUST be preserved
                    },
                }
            ]
        }
    }
    out = scrub(event, hint={})
    crumb = out["breadcrumbs"]["values"][0]
    assert "image" not in crumb["data"]
    assert "kcal" not in crumb["data"]
    assert crumb["data"]["duration_ms"] == 1850


def test_scrubs_breadcrumb_data_email_and_legacy_list_shape():
    """Legacy Sentry payloads sometimes have breadcrumbs as a plain list."""
    event = {
        "breadcrumbs": [
            {"category": "auth", "data": {"email": "u@x.com", "ok": True}},
        ]
    }
    out = scrub(event, hint={})
    crumb = out["breadcrumbs"][0]
    assert "email" not in crumb["data"]
    assert crumb["data"]["ok"] is True


def test_scrub_returns_event_not_none():
    """scrub() should never drop the event — only redact keys."""
    event = {"request": {"headers": {"authorization": "Bearer x"}}}
    out = scrub(event, hint={})
    assert out is not None
    assert out is event  # in-place mutation
