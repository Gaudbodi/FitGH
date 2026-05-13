"""Shared pytest fixtures for the FitGH backend test suite.

Phase 1 Walking Skeleton — WS-B.5.

The `client` fixture builds a Flask test client with stubbed env vars; the
`mongo_users` fixture monkey-patches `app.db.users` to a mongomock collection
so route tests can write/read without touching real Atlas.

WS-C.2: MONGODB_URI is now mandatory at db module import. Conftest sets a
non-resolvable URI so `import app.db` succeeds (construction is lazy) but any
actual network call would fail — tests that need DB behavior must use the
`mongo_users` fixture to swap in mongomock.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import mongomock
import pytest

# ---- Env setup -------------------------------------------------------------

_FAKE_MONGODB_URI = "mongodb://fake-host-not-resolvable:27017/fitgh"


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the env required for create_app() to succeed in tests."""
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_stub_for_tests_xxxxxxxxxxxxxxxx")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:3000")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("FLASK_ENV", "development")
    # Non-resolvable URI so `import app.db` succeeds (PyMongo construction is
    # lazy — DNS only happens on first command). Tests requiring DB behavior
    # use the `mongo_users` fixture to swap in mongomock.
    monkeypatch.setenv("MONGODB_URI", _FAKE_MONGODB_URI)
    monkeypatch.delenv("SENTRY_DSN_BACKEND", raising=False)
    # Reset the lazy-init globals in middleware.auth so each test starts clean.
    import app.middleware.auth as auth_mod

    auth_mod._clerk = None
    auth_mod._authorized_parties = None


# ---- App + client ----------------------------------------------------------


@pytest.fixture
def app(_set_env: None):  # noqa: ARG001 — depends on autouse fixture order
    """Construct a fresh Flask app per test."""
    # Re-import inside the fixture so env changes are picked up. Avoid stale
    # module-level singletons (db.client) — reload db module.
    import importlib

    import app as app_pkg
    import app.db as db_mod

    importlib.reload(db_mod)
    importlib.reload(app_pkg)

    application = app_pkg.create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


# ---- mongomock plumbing ----------------------------------------------------


@pytest.fixture
def mongo_users(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """Replace app.db.users with a mongomock collection.

    Must be requested BEFORE the `client` fixture in tests that need DB writes
    (pytest resolves in argument order). The fixture patches BOTH the source
    module (app.db) AND the route modules that imported `users` at import time
    (Python copies the reference into the route's module namespace).
    """
    fake_client = mongomock.MongoClient()
    fake_db = fake_client["fitgh"]
    fake_users = fake_db["users"]

    import app.db as db_mod
    import app.routes.me as me_route

    monkeypatch.setattr(db_mod, "client", fake_client, raising=False)
    monkeypatch.setattr(db_mod, "db", fake_db, raising=False)
    monkeypatch.setattr(db_mod, "users", fake_users, raising=False)
    # Patch the name the route module already bound at import time.
    # (The webhook route was deleted in WS-E.1; sync-on-demand inside /me
    # replaces the user.created upsert path.)
    monkeypatch.setattr(me_route, "users", fake_users, raising=False)

    yield fake_users
