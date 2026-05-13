"""Flask route — POST /corrections (Phase 4, Task P4-B.3).

Writes one row per chip mutation on the scan-result sheet. The user's
last 20 corrections feed into the NEXT scan's system prompt (read in
app/routes/scan.py) so the model biases toward dishes the user has
historically corrected to.

T-04-04 (spoofing): user_id always = g.clerk_user_id; the request body
shape (UserCorrectionInput) uses extra="forbid" so a forged `user_id`
field 422s.
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Blueprint, g, jsonify, request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app import db as db_mod
from app.middleware.auth import require_auth

bp = Blueprint("corrections", __name__)


class UserCorrectionInput(BaseModel):
    """POST /corrections request body shape.

    Excludes server-stamped fields (user_id, corrected_at) so the client
    cannot forge them. extra="forbid" 422s any unknown / smuggled field.
    """

    model_config = ConfigDict(extra="forbid")

    original_name: str = Field(..., min_length=1, max_length=80)
    corrected_name: str | None = Field(default=None, max_length=80)
    original_portion_g: int = Field(..., ge=0, le=2000)
    corrected_portion_g: int = Field(..., ge=0, le=2000)
    original_food_id: str | None = Field(default=None, pattern=r"^gh-[a-z0-9-]+$")
    corrected_food_id: str | None = Field(default=None, pattern=r"^gh-[a-z0-9-]+$")


def _safe_errors(e: ValidationError) -> list[dict]:
    out = []
    for err in e.errors(include_url=False):
        safe = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err:
            safe["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        out.append(safe)
    return out


@bp.post("/corrections")
@require_auth
def post_correction():
    clerk_id = g.clerk_user_id
    try:
        payload = UserCorrectionInput.model_validate_json(request.data)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": _safe_errors(e)}), 422

    doc = payload.model_dump()
    doc["user_id"] = clerk_id  # server-stamped — never read from body
    doc["corrected_at"] = datetime.now(UTC)
    result = db_mod.user_corrections.insert_one(doc)
    return jsonify({"ok": True, "id": str(result.inserted_id)}), 201
