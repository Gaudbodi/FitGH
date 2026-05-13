"""Module-level singleton MongoClient for FitGH.

Phase 1 Walking Skeleton — WS-B.3 + WS-C.2 (shim removed; MONGODB_URI mandatory).

Skeleton Invariant #4 (SEC-04): exactly ONE MongoClient at module scope, with
maxPoolSize=10 (M0 cluster has a 100-connection cap; ten workers x 10 = 100
ceiling), tls=True (Atlas requires TLS), and a 5-second server-selection
timeout so a misconfigured connection fails fast at /health rather than
hanging.

NEVER instantiate MongoClient inside a route handler — that creates a new
connection pool per request and DoS's the cluster (T-01-08 in the threat
register).

WS-C.2: `MONGODB_URI` is now mandatory. Importing this module without it set
raises `KeyError` so misconfiguration fails at startup rather than producing a
silent "stubbed" /health.
"""

from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

_mongo_uri = os.environ["MONGODB_URI"]

client: MongoClient = MongoClient(
    _mongo_uri,
    maxPoolSize=10,
    tls=True,
    serverSelectionTimeoutMS=5000,
)

# The 'fitgh' database is the only one this app touches (the fitgh-app user
# is readWrite@fitgh only — see SEC-02 / WS-0.1).
db: Database = client["fitgh"]
users: Collection = db["users"]

# Phase 2 — Onboarding + Profile + Targets (Task P2-A.2).
# These collections are added module-level alongside `users` so route modules
# can `from app.db import profiles` exactly like Phase 1 does for users.
#
# Index strategy (D-STORAGE-NEW-COLLECTIONS, no `ensure_index` on import —
# Phase 1 pattern of zero import-time side effects beyond MongoClient
# construction). Run these once via mongosh after deploy:
#   db.profiles.createIndex({clerk_id: 1}, {unique: true})
#   db.weight_logs.createIndex({user_id: 1, logged_at: -1})
profiles: Collection = db["profiles"]
weight_logs: Collection = db["weight_logs"]
