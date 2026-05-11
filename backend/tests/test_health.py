"""Tests for GET /health.

WS-B.5 acceptance:
- /health returns 200 {ok:true, mongo:'stubbed'} when MONGODB_URI is unset.
- /health returns 200 {mongo:'connected'} when client.admin.command('ping') OK.
- /health returns 503 {mongo:'error'} on connection failure.
"""

from __future__ import annotations

from unittest.mock import patch


def test_health_stubbed_when_mongo_uri_unset(client):
    """Slice B path: client is None, /health returns stubbed."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True, "mongo": "stubbed"}


def test_health_connected_when_ping_succeeds(client):
    """When the singleton can ping admin db, /health returns connected."""
    # Patch app.routes.health.client to a mock whose .admin.command works.
    import app.routes.health as health_mod

    class _FakeAdmin:
        def command(self, _cmd: str) -> dict:
            return {"ok": 1.0}

    class _FakeClient:
        admin = _FakeAdmin()

    with patch.object(health_mod, "client", _FakeClient()):
        r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True, "mongo": "connected"}


def test_health_error_when_ping_fails(client):
    """When ping raises, /health returns 503 with sanitized detail."""
    import app.routes.health as health_mod

    class _FakeAdmin:
        def command(self, _cmd: str) -> dict:
            raise ConnectionError("could not reach cluster")

    class _FakeClient:
        admin = _FakeAdmin()

    with patch.object(health_mod, "client", _FakeClient()):
        r = client.get("/health")
    assert r.status_code == 503
    body = r.get_json()
    assert body["ok"] is False
    assert body["mongo"] == "error"
    # detail must be the exception TYPE name, NOT the message (which could
    # contain a URI / password).
    assert body["detail"] == "ConnectionError"
