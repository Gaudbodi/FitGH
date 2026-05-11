"""Tests for the PyMongo singleton config (SEC-04).

WS-B.5 acceptance:
- MongoClient configured with maxPoolSize=10 (M0 cluster connection-cap).
- tls=True (Atlas requires TLS).

WS-C.2 will add: 'importing db with MONGODB_URI absent must raise'.
"""

from __future__ import annotations

import importlib


def test_db_module_imports_clean_without_mongo_uri(monkeypatch):
    """In Slice B, missing MONGODB_URI must NOT raise — the shim allows None."""
    monkeypatch.delenv("MONGODB_URI", raising=False)
    import app.db as db_mod

    importlib.reload(db_mod)
    assert db_mod.client is None
    assert db_mod.db is None
    assert db_mod.users is None


def test_db_singleton_uses_max_pool_size_10_and_tls(monkeypatch):
    """When MONGODB_URI is set, the singleton must have maxPoolSize=10 + tls=True."""
    # Use a mongomock-style URI; PyMongo will refuse to connect to the bogus
    # host but construction itself succeeds and we can read .options.
    fake_uri = "mongodb://fake-host-not-resolvable:27017/fitgh"
    monkeypatch.setenv("MONGODB_URI", fake_uri)

    import app.db as db_mod

    importlib.reload(db_mod)
    assert db_mod.client is not None

    pool_opts = db_mod.client.options.pool_options
    # SEC-04 invariant: maxPoolSize=10 (M0 connection-cap discipline).
    assert pool_opts.max_pool_size == 10

    # tls=True for Atlas. PyMongo 4.17 stores this as a kwarg in the internal
    # _options dict and materializes an SSL context on pool_options when the
    # kwarg is True. Assert both:
    assert db_mod.client.options._options.get("tls") is True
    assert pool_opts._ssl_context is not None
