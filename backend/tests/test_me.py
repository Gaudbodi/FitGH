"""Tests for GET /me.

Phase 1 Walking Skeleton — WS-E.2 (sync-on-demand upsert).

Behavior under test:
- No Authorization header                             -> 401 unauthorized
- Garbage Bearer token                                -> 401 unauthorized
- Authenticated + users doc exists                    -> 200 {email}
- Authenticated + users doc MISSING (first sign-in)   -> upsert with email
                                                        from JWT claim,
                                                        return 200 {email}

The 503 `db_not_configured` branch is gone (WS-E.2 deletes the dead code in
me.py — `users` is always a real Collection now that MONGODB_URI is mandatory
at db.py import time).

For authenticated-path tests, we stub the Clerk SDK's
`authenticate_request` to return a signed-in `RequestState` so the real
@require_auth path runs but with deterministic claims. Full live JWT
verification is exercised end-to-end in WS-F.0 (local smoke) and WS-F.2.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_clerk_signed_in(
    monkeypatch,
    *,
    clerk_user_id: str = "user_test_abc",
    clerk_email: str | None = "user@example.com",
) -> None:
    """Patch the lazy Clerk client to return a signed-in state.

    Bypasses real JWT verification while keeping the @require_auth code path
    intact — including the `g.clerk_user_id` / `g.clerk_email` claim stash.
    """
    import app.middleware.auth as auth_mod

    payload = {"sub": clerk_user_id}
    if clerk_email is not None:
        payload["email"] = clerk_email

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload=payload,
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


# ---------------------------------------------------------------------------
# Unauthenticated paths
# ---------------------------------------------------------------------------


def test_me_without_auth_returns_401(client):
    """No Authorization header -> 401 unauthorized."""
    r = client.get("/me")
    assert r.status_code == 401
    body = r.get_json()
    assert body["error"] == "unauthorized"
    # The reason must be a string (not the AuthErrorReason enum object) so
    # the response is JSON-serializable. This is the Rule 1 fix from WS-B.4.
    assert isinstance(body["reason"], str) or body["reason"] is None


def test_me_with_invalid_bearer_returns_401(client):
    """Garbage Bearer token -> Clerk SDK rejects -> 401."""
    r = client.get("/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert r.status_code == 401
    assert r.get_json()["error"] == "unauthorized"


# ---------------------------------------------------------------------------
# Authenticated paths
# ---------------------------------------------------------------------------


def test_me_returns_existing_user_email(client, mongo_users, monkeypatch):
    """When a users doc exists for clerk_user_id, /me returns its email."""
    mongo_users.insert_one(
        {
            "clerk_id": "user_test_abc",
            "email": "existing@example.com",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    )
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_test_abc")

    r = client.get("/me", headers={"Authorization": "Bearer stub-jwt"})
    assert r.status_code == 200
    assert r.get_json() == {"email": "existing@example.com"}

    # Sync-on-demand must NOT overwrite the email on existing docs.
    doc = mongo_users.find_one({"clerk_id": "user_test_abc"})
    assert doc is not None
    assert doc["email"] == "existing@example.com"


def test_me_sync_on_demand_upserts_missing_user(
    client, mongo_users, monkeypatch
):
    """When no users doc exists, /me upserts one from the JWT email claim."""
    # Sanity: no doc yet.
    assert mongo_users.find_one({"clerk_id": "user_test_new"}) is None

    _stub_clerk_signed_in(
        monkeypatch,
        clerk_user_id="user_test_new",
        clerk_email="new@example.com",
    )

    r = client.get("/me", headers={"Authorization": "Bearer stub-jwt"})
    assert r.status_code == 200
    assert r.get_json() == {"email": "new@example.com"}

    # The doc was created with the expected fields.
    doc = mongo_users.find_one({"clerk_id": "user_test_new"})
    assert doc is not None
    assert doc["email"] == "new@example.com"
    assert "created_at" in doc
    assert "updated_at" in doc
