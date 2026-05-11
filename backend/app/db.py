"""Module-level singleton MongoClient for FitGH.

Phase 1 Walking Skeleton — WS-B.3 (Slice B with shim; Slice C/WS-C.2 removes the
shim so missing MONGODB_URI fails loudly at import).

Skeleton Invariant #4 (SEC-04): exactly ONE MongoClient at module scope, with
maxPoolSize=10 (M0 cluster has a 100-connection cap; ten workers x 10 = 100
ceiling), tls=True (Atlas requires TLS), and a 5-second server-selection
timeout so a misconfigured connection fails fast at /health rather than
hanging.

NEVER instantiate MongoClient inside a route handler — that creates a new
connection pool per request and DoS's the cluster (T-01-08 in the threat
register).
"""

from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# Slice B shim: MONGODB_URI may be unset (e.g. before WS-0.1 password rotation
# completes). The shim lets app.create_app() succeed so /health can still
# report 'mongo: stubbed'. WS-C.2 removes this shim — by Slice C, MONGODB_URI
# is mandatory and missing it must raise KeyError at module import.
_mongo_uri = os.environ.get("MONGODB_URI")

client: MongoClient | None = (
    MongoClient(
        _mongo_uri,
        maxPoolSize=10,
        tls=True,
        serverSelectionTimeoutMS=5000,
    )
    if _mongo_uri
    else None
)

# The 'fitgh' database is the only one this app touches (the fitgh-app user
# is readWrite@fitgh only — see SEC-02 / WS-0.1).
db: Database | None = client["fitgh"] if client is not None else None
users: Collection | None = db["users"] if db is not None else None
