"""Tests for POST /webhooks/clerk.

WS-B.5 acceptance:
- Missing x-clerk-verified header -> 400 {error:'unverified'}.
- Invalid JSON body                -> 400 {error:'invalid_json'}.
- Valid user.created event         -> upserts users doc (mongomock).
- Valid user.deleted event         -> deletes users doc.
"""

from __future__ import annotations


def test_webhook_rejects_without_verified_header(client):
    """T-01-02 mitigation: BFF MUST set x-clerk-verified before forwarding."""
    r = client.post(
        "/webhooks/clerk",
        json={"type": "user.created", "data": {"id": "user_1"}},
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "unverified"}


def test_webhook_rejects_invalid_json(client):
    """With the header but non-JSON body -> 400 invalid_json."""
    r = client.post(
        "/webhooks/clerk",
        headers={"x-clerk-verified": "true", "Content-Type": "application/json"},
        data="this is not json",
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "invalid_json"}


def test_webhook_user_created_upserts_doc(client, mongo_users):
    """user.created event -> users.update_one({clerk_id}, ..., upsert=True)."""
    payload = {
        "type": "user.created",
        "data": {
            "id": "user_test_abc",
            "email_addresses": [{"email_address": "user@example.com"}],
        },
    }
    r = client.post(
        "/webhooks/clerk",
        headers={"x-clerk-verified": "true"},
        json=payload,
    )
    assert r.status_code == 201
    assert r.get_json() == {"ok": True}

    # Verify the doc was inserted with the expected fields.
    doc = mongo_users.find_one({"clerk_id": "user_test_abc"})
    assert doc is not None
    assert doc["email"] == "user@example.com"
    assert "created_at" in doc
    assert "updated_at" in doc


def test_webhook_user_deleted_removes_doc(client, mongo_users):
    """user.deleted event -> users.delete_one({clerk_id})."""
    mongo_users.insert_one({"clerk_id": "user_to_delete", "email": "x@y.com"})

    r = client.post(
        "/webhooks/clerk",
        headers={"x-clerk-verified": "true"},
        json={"type": "user.deleted", "data": {"id": "user_to_delete"}},
    )
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}
    assert mongo_users.find_one({"clerk_id": "user_to_delete"}) is None


def test_webhook_ignores_unknown_event_type(client, mongo_users):
    """Unknown event types -> 200 {ignored: <type>}."""
    r = client.post(
        "/webhooks/clerk",
        headers={"x-clerk-verified": "true"},
        json={"type": "session.created", "data": {}},
    )
    assert r.status_code == 200
    assert r.get_json() == {"ignored": "session.created"}
