"""Tests for the Flask CORS allowlist (SEC-03).

WS-B.5 acceptance:
- OPTIONS preflight from an ALLOWED origin echoes the origin in
  Access-Control-Allow-Origin.
- OPTIONS preflight from a NON-allowed origin returns no ACAO (or 403).
- Access-Control-Allow-Origin is NEVER '*' when supports_credentials=False
  but we still pin it to the configured origin per SEC-03 invariant.
"""

from __future__ import annotations


def test_preflight_from_allowed_origin_echoes_origin(client):
    """OPTIONS /me from http://localhost:3000 -> ACAO: http://localhost:3000."""
    r = client.options(
        "/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert r.status_code in (200, 204)
    assert r.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    # Authorization MUST be in the allow_headers list (so the BFF can forward it).
    assert "authorization" in r.headers.get("Access-Control-Allow-Headers", "").lower()


def test_preflight_from_evil_origin_does_not_echo(client):
    """OPTIONS /me from http://evil.example.com -> no ACAO (NOT '*')."""
    r = client.options(
        "/me",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # flask-cors typically returns 200 to OPTIONS but omits ACAO for disallowed
    # origins; some configs return 403. Either is acceptable — what we MUST
    # never see is "Access-Control-Allow-Origin: *" or echoing the evil origin.
    acao = r.headers.get("Access-Control-Allow-Origin", "")
    assert acao != "*"
    assert "evil" not in acao.lower()
