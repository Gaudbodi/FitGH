"""Tests for POST /corrections (Phase 4, P4-B.3).

The route writes one row per chip mutation on the scan-result sheet so
the user's last 20 corrections feed into the next scan's system prompt.

T-04-04: user_id always = g.clerk_user_id; body fields ignored.
"""

from __future__ import annotations

import json
from types import SimpleNamespace


def _stub_clerk_signed_in(monkeypatch, *, clerk_user_id: str = "user_corr") -> None:
    import app.middleware.auth as auth_mod

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload={"sub": clerk_user_id, "email": "m@example.com"},
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


def _post_correction(client, body: dict):
    return client.post(
        "/corrections",
        data=json.dumps(body),
        headers={
            "Authorization": "Bearer t",
            "Content-Type": "application/json",
        },
    )


def test_post_correction_creates_doc_with_server_user_id_and_timestamp(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_truth")
    body = {
        "original_name": "rice",
        "corrected_name": "Jollof rice",
        "original_portion_g": 200,
        "corrected_portion_g": 350,
        "original_food_id": None,
        "corrected_food_id": "gh-jollof-rice",
    }
    resp = _post_correction(client, body)
    assert resp.status_code == 201, resp.get_json()
    body_out = resp.get_json()
    assert body_out["ok"] is True
    assert "id" in body_out
    doc = mongo_collections.user_corrections.find_one({"user_id": "user_truth"})
    assert doc is not None
    assert doc["original_name"] == "rice"
    assert doc["corrected_name"] == "Jollof rice"
    assert doc["corrected_at"] is not None
    # No client-supplied user_id sneaked in.
    assert "user_id" in doc
    assert doc["user_id"] == "user_truth"


def test_post_correction_ignores_user_id_in_body(
    client, mongo_collections, monkeypatch
):
    """T-04-04: forged user_id in body is rejected (422) or ignored.

    Pydantic UserCorrectionInput uses extra='forbid' so the request
    422s if the client tries to smuggle a user_id.
    """
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_truth")
    body = {
        "user_id": "user_attacker",
        "original_name": "rice",
        "corrected_name": "Jollof rice",
        "original_portion_g": 200,
        "corrected_portion_g": 350,
        "original_food_id": None,
        "corrected_food_id": "gh-jollof-rice",
    }
    resp = _post_correction(client, body)
    assert resp.status_code == 422
    # No correction was persisted under either user.
    assert mongo_collections.user_corrections.find_one() is None


def test_post_correction_requires_auth_401(client, mongo_collections, monkeypatch):
    import app.middleware.auth as auth_mod

    class _StubClerkAnon:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return SimpleNamespace(
                is_signed_in=False, reason="no_session_token", payload=None
            )

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerkAnon())
    body = {
        "original_name": "x",
        "corrected_name": "y",
        "original_portion_g": 100,
        "corrected_portion_g": 200,
        "original_food_id": None,
        "corrected_food_id": None,
    }
    resp = _post_correction(client, body)
    assert resp.status_code == 401


def test_post_correction_accepts_portion_only_change(
    client, mongo_collections, monkeypatch
):
    """corrected_name=None signals the user only adjusted the portion slider."""
    _stub_clerk_signed_in(monkeypatch)
    body = {
        "original_name": "Jollof rice",
        "corrected_name": None,
        "original_portion_g": 350,
        "corrected_portion_g": 450,
        "original_food_id": "gh-jollof-rice",
        "corrected_food_id": "gh-jollof-rice",
    }
    resp = _post_correction(client, body)
    assert resp.status_code == 201
    doc = mongo_collections.user_corrections.find_one()
    assert doc["corrected_name"] is None
    assert doc["corrected_portion_g"] == 450


def test_post_correction_validates_food_id_pattern(
    client, mongo_collections, monkeypatch
):
    """Pydantic pattern rejects malformed food_id."""
    _stub_clerk_signed_in(monkeypatch)
    body = {
        "original_name": "rice",
        "corrected_name": "Jollof rice",
        "original_portion_g": 200,
        "corrected_portion_g": 350,
        "original_food_id": None,
        "corrected_food_id": "GH-INVALID-uppercase",
    }
    resp = _post_correction(client, body)
    assert resp.status_code == 422
