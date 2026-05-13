"""Tests for the conditional Sentry initialisation.

Phase 1 Walking Skeleton — WS-E.3 (Render-only rewrite 2026-05-12).

The 2026-05-12 rewrite defers OBS-01 (Sentry FE/BE wiring) until a real bug
demands it. The scrubber code in app.extensions.scrub() stays in place and
its contract is enforced by test_sentry_scrubber.py (7 cases). What this
file asserts is the *init* path:

  1. With SENTRY_DSN_BACKEND unset, init_sentry(cfg) is a no-op — sentry_sdk.init
     is NEVER called. This is what makes Phase 1 deploy on Render with zero
     Sentry config friction.
  2. With SENTRY_DSN_BACKEND set, init_sentry(cfg) DOES call sentry_sdk.init
     and passes our scrubber as the `before_send` hook.

Re-enabling Sentry in a later phase is one env-var away; the scrubber
contract is enforced from commit 1.
"""

from __future__ import annotations

from unittest.mock import patch

from app.config import Config
from app.extensions import init_sentry, scrub


def test_init_sentry_is_noop_when_dsn_unset(monkeypatch):
    """No DSN => no sentry_sdk.init call (zero-config Phase 1 deploy)."""
    monkeypatch.delenv("SENTRY_DSN_BACKEND", raising=False)
    cfg = Config()
    assert cfg.SENTRY_DSN_BACKEND == ""

    with patch("app.extensions.sentry_sdk.init") as mock_init:
        init_sentry(cfg)
        mock_init.assert_not_called()


def test_init_sentry_calls_init_with_scrubber_when_dsn_set(monkeypatch):
    """With a DSN, sentry_sdk.init runs once and gets our before_send=scrub."""
    monkeypatch.setenv(
        "SENTRY_DSN_BACKEND",
        "https://stub@o0.ingest.sentry.io/1",
    )
    cfg = Config()
    assert cfg.SENTRY_DSN_BACKEND

    with patch("app.extensions.sentry_sdk.init") as mock_init:
        init_sentry(cfg)
        mock_init.assert_called_once()
        kwargs = mock_init.call_args.kwargs
        # The scrubber from extensions.py is the OBS-01 contract anchor; it
        # MUST be the before_send hook the moment Sentry comes back on.
        assert kwargs.get("before_send") is scrub
        # send_default_pii=False is the safety net under the scrubber.
        assert kwargs.get("send_default_pii") is False
