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
def mongo_collections(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """Replace app.db.{users,profiles,weight_logs} with mongomock collections.

    Returns a SimpleNamespace with `.users`, `.profiles`, `.weight_logs`
    attributes. Must be requested BEFORE the `client` fixture in tests that
    need DB writes (pytest resolves in argument order). The fixture patches
    BOTH the source module (app.db) AND each route module that imported the
    names at import time (Python copies references into module namespaces;
    Phase 1 deviation #X — both bindings must be patched).
    """
    from types import SimpleNamespace

    fake_client = mongomock.MongoClient()
    fake_db = fake_client["fitgh"]
    fake_users = fake_db["users"]
    fake_profiles = fake_db["profiles"]
    fake_weight_logs = fake_db["weight_logs"]
    fake_ghana_foods = fake_db["ghana_foods"]
    fake_meals = fake_db["meals"]

    import app.db as db_mod
    import app.routes.me as me_route

    monkeypatch.setattr(db_mod, "client", fake_client, raising=False)
    monkeypatch.setattr(db_mod, "db", fake_db, raising=False)
    monkeypatch.setattr(db_mod, "users", fake_users, raising=False)
    monkeypatch.setattr(db_mod, "profiles", fake_profiles, raising=False)
    monkeypatch.setattr(db_mod, "weight_logs", fake_weight_logs, raising=False)
    monkeypatch.setattr(db_mod, "ghana_foods", fake_ghana_foods, raising=False)
    monkeypatch.setattr(db_mod, "meals", fake_meals, raising=False)
    # Patch the names the existing route modules already bound at import.
    monkeypatch.setattr(me_route, "users", fake_users, raising=False)

    # Profile / weights / foods / meals routes import lazily inside
    # create_app (Phase 1 pattern of blueprints inside the factory), so they
    # pick up the patched names when the app fixture re-imports them. But
    # once imported we ALSO need to patch their module-bound references —
    # do that opportunistically if the modules have been loaded.
    import sys
    if "app.routes.profile" in sys.modules:
        prof_mod = sys.modules["app.routes.profile"]
        monkeypatch.setattr(prof_mod, "profiles", fake_profiles, raising=False)
        monkeypatch.setattr(prof_mod, "weight_logs", fake_weight_logs, raising=False)
    if "app.routes.weights" in sys.modules:
        wt_mod = sys.modules["app.routes.weights"]
        monkeypatch.setattr(wt_mod, "weight_logs", fake_weight_logs, raising=False)
        monkeypatch.setattr(wt_mod, "profiles", fake_profiles, raising=False)
    if "app.routes.foods" in sys.modules:
        foods_mod = sys.modules["app.routes.foods"]
        monkeypatch.setattr(foods_mod, "ghana_foods", fake_ghana_foods, raising=False)
    if "app.routes.meals" in sys.modules:
        meals_mod = sys.modules["app.routes.meals"]
        monkeypatch.setattr(meals_mod, "meals", fake_meals, raising=False)
        monkeypatch.setattr(meals_mod, "ghana_foods", fake_ghana_foods, raising=False)
        monkeypatch.setattr(meals_mod, "profiles", fake_profiles, raising=False)

    yield SimpleNamespace(
        users=fake_users,
        profiles=fake_profiles,
        weight_logs=fake_weight_logs,
        ghana_foods=fake_ghana_foods,
        meals=fake_meals,
    )


# Back-compat alias so the existing test_me.py keeps working unchanged.
@pytest.fixture
def mongo_users(mongo_collections) -> Iterator[Any]:
    """Legacy alias returning just the users collection."""
    yield mongo_collections.users
