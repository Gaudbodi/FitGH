"""Tests for the PyMongo singleton config (SEC-04).

WS-B.5 + WS-C.2 acceptance:
- MongoClient configured with maxPoolSize=10 (M0 cluster connection-cap).
- tls=True (Atlas requires TLS).
- Importing db with MONGODB_URI absent MUST raise KeyError (WS-C.2 — shim removed).
"""

from __future__ import annotations

import importlib

import pytest


def test_db_module_import_raises_when_mongo_uri_absent(monkeypatch):
    """WS-C.2: missing MONGODB_URI fails loudly at module import."""
    monkeypatch.delenv("MONGODB_URI", raising=False)
    import app.db as db_mod

    with pytest.raises(KeyError, match="MONGODB_URI"):
        importlib.reload(db_mod)


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
