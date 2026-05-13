"""Pydantic v2 WeightLog + WeightLogCreate models.

Phase 2 Plan 02 — Task P2-A.2.

The `weight_logs` collection is one document per weight entry:
  {user_id: <clerk_id>, kg: <float>, logged_at: <UTC datetime>}

T-02-04 (Info disclosure): the route filters by user_id from the JWT; this
model does not enforce it — the route handler does, after pulling
g.clerk_user_id from the verified token.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WeightLog(BaseModel):
    """Full WeightLog document as stored in `weight_logs` collection."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., pattern=r"^user_[a-zA-Z0-9_]+$")
    kg: float = Field(..., ge=20.0, le=400.0)
    logged_at: datetime


class WeightLogCreate(BaseModel):
    """POST /weights body. Only `kg` — user_id and logged_at are server-set."""

    model_config = ConfigDict(extra="forbid")

    kg: float = Field(..., ge=20.0, le=400.0)
