"""Flask route — POST /meals/scan (the wedge feature).

Phase 4 Plan 04 — Tasks P4-B.1 + P4-B.2.

Flow:
  1. @require_auth (Phase 1).
  2. PRE-1 user-cap: check_and_increment_user_daily — 429 on cap hit.
  3. PRE-2 global budget: check_global_budget — 503 on cap hit; on 503
     we ROLL BACK the user-cap increment (the call was never made).
  4. Read image bytes (≤1 MB; image/jpeg|png|webp). 400 on invalid.
  5. base64-encode for the Anthropic body.
  6. Build cached system prompt (Ghana foods + last 20 user corrections).
  7. Call Anthropic Sonnet 4.6 messages.create with tool_use.
  8. del image bytes + base64 immediately (T-04-01).
  9. parse_tool_use_response (retry once on ValidationError/no-block).
 10. table_rematch — table wins kcal_point.
 11. record_spend_post_call with actual token cost.
 12. Cost-alert check (P4-B.2): fires when spend_per_dau > 0.05 AND
     not yet alerted today.
 13. Return {components, ai_metadata, vision_total_kcal_*, user_daily_*}.

Plus a small GET /scan-budget endpoint (read-only system_state snapshot)
that the FE's ServicePausedBanner consumes.

Trust anchors:
  - user_id always = g.clerk_user_id; NEVER read from form/body (T-04-04).
  - No image bytes persist (T-04-01) — del + handler-scope only.
  - Pydantic VisionResponse strict-validates the LLM output (T-04-07).
  - Anthropic key/Auth header NEVER appears in exception chain (T-04-06)
    — we re-raise as a plain RuntimeError BEFORE app.logger.exception
    sees the original.
"""

from __future__ import annotations

import base64
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from flask import Blueprint, current_app, g, jsonify, request
from pydantic import ValidationError

from app import db as db_mod
from app.lib.rate_limit import (
    USER_DAILY_CAP,
    check_and_increment_user_daily,
    check_global_budget,
    mark_alert_fired,
    record_spend_post_call,
    today_utc_str,
)
from app.lib.vision import (
    build_system_prompt,
    build_user_message,
    compute_cost_usd,
    parse_tool_use_response,
    table_rematch,
)
from app.middleware.auth import require_auth
from app.models.vision import ANTHROPIC_TOOL_SCHEMA

bp = Blueprint("scan", __name__)

_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
_IMAGE_HARD_CAP_BYTES = 1_048_576  # 1 MB — FE compresses to 0.5 MB target.
_COST_PER_DAU_THRESHOLD = 0.05  # OBS-03


def _decrement_user_cap(user_id: str, today_str: str) -> None:
    """Roll back a successful conditional-increment on `vision_usage`.

    Called when a subsequent pre-check (global budget) or an image-validation
    error means we never actually called Anthropic for this user. Net-zero
    against the user's daily quota.
    """
    db_mod.vision_usage.update_one(
        {"user_id": user_id, "date": today_str},
        {"$inc": {"count": -1}},
    )


def _tomorrow_utc_midnight_iso() -> str:
    """Reset window for the daily-cap 429 response."""
    now = datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return tomorrow.isoformat().replace("+00:00", "Z")


def _call_anthropic(
    *,
    api_key: str,
    model: str,
    system_blocks: list[dict],
    user_message_content: list[dict],
) -> Any:
    """Wrap the Anthropic SDK call with defence-in-depth on error paths.

    T-04-06 (info disclosure): on SDK error, log the exception class name
    via app.logger.exception under a fixed message but DROP the original
    exception args before re-raising so the Authorization header (or any
    other request-context detail) cannot leak into Render's stdout/log
    aggregator.
    """
    import anthropic  # lazy — keeps pytest --collect-only fast on machines
    # without the package, and lets respx intercept the underlying httpx.

    client = anthropic.Anthropic(api_key=api_key)
    try:
        return client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_blocks,
            tools=[ANTHROPIC_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "report_meal_components"},
            messages=[{"role": "user", "content": user_message_content}],
        )
    except Exception:
        # Log the class name only — `repr` on some Anthropic error types
        # includes the request URL + headers. Drop the original via
        # `raise ... from None` so the chain doesn't carry sensitive args.
        current_app.logger.exception("anthropic_call_failed")
        raise RuntimeError("anthropic_call_failed") from None


def _maybe_fire_cost_alert(
    updated_state: dict, today_str: str, cfg: Any
) -> None:
    """OBS-03 cost-alert hook.

    Fires the webhook ONCE per day when spend_per_dau exceeds the
    $0.05 threshold (T-04-08 — single-fire prevents DoS amplification).

    DAU = count of distinct (user_id) docs in vision_usage for today.
    The unique index on (user_id, date) means count_documents on
    {date: today} is cheap.
    """
    if updated_state.get("alert_fired"):
        return
    dau_today = db_mod.vision_usage.count_documents({"date": today_str})
    if dau_today == 0:
        # First call of the day — usage doc just created; cheap edge.
        dau_today = 1
    spend_usd = float(updated_state.get("spend_usd", 0.0))
    cap_usd = float(updated_state.get("cap_usd", cfg.VISION_DAILY_CAP_USD))
    spend_per_dau = spend_usd / dau_today
    if spend_per_dau <= _COST_PER_DAU_THRESHOLD:
        return
    payload = {
        "content": (
            f"FitGH cost alert: ${spend_usd:.4f} spend / {dau_today} DAU "
            f"today = ${spend_per_dau:.4f}/DAU > ${_COST_PER_DAU_THRESHOLD} "
            f"threshold (OBS-03). Cap: ${cap_usd:.2f}."
        )
    }
    webhook_url = cfg.COST_ALERT_WEBHOOK_URL
    if webhook_url:
        try:
            httpx.post(webhook_url, json=payload, timeout=3.0)
        except Exception as e:  # noqa: BLE001 — webhook MUST NOT 500 the scan
            current_app.logger.warning(
                "cost_alert_post_failed: %r", type(e).__name__
            )
    else:
        current_app.logger.warning(
            "cost_alert_no_webhook: %s", payload["content"]
        )
    # Latch — single-fire per day (T-04-08).
    mark_alert_fired(db_mod.system_state, today_str)


@bp.post("/meals/scan")
@require_auth
def post_scan():
    cfg = current_app.config["FITGH"]
    clerk_id = g.clerk_user_id
    today_str = today_utc_str()

    # PRE-1: per-user 8/day cap.
    allowed, count = check_and_increment_user_daily(
        db_mod.vision_usage, clerk_id, today_str
    )
    if not allowed:
        return (
            jsonify(
                {
                    "error": "daily_cap",
                    "count": count,
                    "limit": USER_DAILY_CAP,
                    "reset_at": _tomorrow_utc_midnight_iso(),
                }
            ),
            429,
        )

    # PRE-2: global $/day budget. Read-only — never mutates spend.
    budget_allowed, current_spend = check_global_budget(
        db_mod.system_state, today_str, cfg.VISION_DAILY_CAP_USD
    )
    if not budget_allowed:
        # Rollback user-cap increment — we never called Anthropic.
        _decrement_user_cap(clerk_id, today_str)
        return (
            jsonify(
                {
                    "error": "service_paused",
                    "reason": "daily_budget",
                    "spend_usd": current_spend,
                    "cap_usd": cfg.VISION_DAILY_CAP_USD,
                }
            ),
            503,
        )

    # Image input. Validate BEFORE doing any work.
    image_file = request.files.get("image")
    if image_file is None:
        _decrement_user_cap(clerk_id, today_str)
        return jsonify({"error": "invalid_image", "reason": "missing"}), 400
    mime = image_file.mimetype or ""
    if mime not in _ALLOWED_MIME:
        _decrement_user_cap(clerk_id, today_str)
        return jsonify({"error": "invalid_image", "reason": "mime"}), 400
    image_bytes = image_file.read()
    if not image_bytes:
        _decrement_user_cap(clerk_id, today_str)
        return jsonify({"error": "invalid_image", "reason": "empty"}), 400
    if len(image_bytes) > _IMAGE_HARD_CAP_BYTES:
        _decrement_user_cap(clerk_id, today_str)
        return jsonify({"error": "invalid_image", "reason": "too_large"}), 400

    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    # Build system prompt — Ghana foods (25 docs) + last 20 corrections.
    ghana_foods = list(db_mod.ghana_foods.find({}, {"_id": 0}))
    user_corrections = list(
        db_mod.user_corrections.find({"user_id": clerk_id})
        .sort("corrected_at", -1)
        .limit(20)
    )
    prompt_pkg = build_system_prompt(ghana_foods, user_corrections)
    system_blocks = prompt_pkg["system"]
    prompt_hash = prompt_pkg["prompt_hash"]

    user_content = build_user_message(image_b64, mime)

    # Anthropic call (retry once on parse failure).
    t0 = time.monotonic()
    try:
        resp = _call_anthropic(
            api_key=cfg.ANTHROPIC_API_KEY,
            model=cfg.LLM_VISION_MODEL,
            system_blocks=system_blocks,
            user_message_content=user_content,
        )
    except RuntimeError:
        # Bytes already in memory; explicitly clear and 502.
        del image_bytes
        del image_b64
        _decrement_user_cap(clerk_id, today_str)
        return (
            jsonify({"error": "vision_call_failed"}),
            502,
        )

    try:
        parsed = parse_tool_use_response(resp)
    except (ValueError, ValidationError):
        # Retry ONCE — Anthropic tool-use is deterministic enough that a
        # one-shot retry usually fixes a transient blip.
        try:
            resp = _call_anthropic(
                api_key=cfg.ANTHROPIC_API_KEY,
                model=cfg.LLM_VISION_MODEL,
                system_blocks=system_blocks,
                user_message_content=user_content,
            )
            parsed = parse_tool_use_response(resp)
        except (RuntimeError, ValueError, ValidationError):
            del image_bytes
            del image_b64
            _decrement_user_cap(clerk_id, today_str)
            return jsonify({"error": "vision_parse_failed"}), 502

    latency_ms = int((time.monotonic() - t0) * 1000)

    # T-04-01: drop image bytes immediately. Handler scope ends shortly
    # anyway, but explicit beats implicit for the audit.
    del image_bytes
    del image_b64

    # Table re-match — table wins kcal_point.
    components = table_rematch(parsed.components, db_mod.ghana_foods)

    # Record spend (post-call atomic increment).
    usage = getattr(resp, "usage", None)
    if usage is not None:
        input_uncached = int(getattr(usage, "input_tokens", 0) or 0)
        input_cached = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        output_tok = int(getattr(usage, "output_tokens", 0) or 0)
    else:
        input_uncached = input_cached = output_tok = 0
    cost_usd = compute_cost_usd(
        input_cached_tokens=input_cached,
        input_uncached_tokens=input_uncached,
        output_tokens=output_tok,
        model=cfg.LLM_VISION_MODEL,
    )
    updated_state = record_spend_post_call(
        db_mod.system_state, today_str, cost_usd, cfg.VISION_DAILY_CAP_USD
    )

    # Cost-alert webhook (single-fire latch).
    _maybe_fire_cost_alert(updated_state, today_str, cfg)

    vision_total_kcal_low = sum(int(c["kcal_low"] or 0) for c in components)
    vision_total_kcal_high = sum(int(c["kcal_high"] or 0) for c in components)

    return (
        jsonify(
            {
                "components": components,
                "ai_metadata": {
                    "model": cfg.LLM_VISION_MODEL,
                    "prompt_hash": prompt_hash,
                    # image_dims is a Phase-7 / v2 hook — populating it
                    # requires Pillow (we're not adding it for v1).
                    "image_dims": {"w": 0, "h": 0},
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd,
                },
                "vision_total_kcal_low": vision_total_kcal_low,
                "vision_total_kcal_high": vision_total_kcal_high,
                "user_daily_count": count,
                "user_daily_limit": USER_DAILY_CAP,
            }
        ),
        200,
    )


# ---------------------------------------------------------------------------
# GET /scan-budget — read-only system_state snapshot for the FE banner.
# ---------------------------------------------------------------------------


@bp.get("/scan-budget")
@require_auth
def get_scan_budget():
    cfg = current_app.config["FITGH"]
    today_str = today_utc_str()
    doc = db_mod.system_state.find_one({"_id": "vision_budget"})
    if doc is None or doc.get("date") != today_str:
        return (
            jsonify(
                {
                    "spend_usd": 0.0,
                    "cap_usd": cfg.VISION_DAILY_CAP_USD,
                    "paused": False,
                    "date": today_str,
                }
            ),
            200,
        )
    spend = float(doc.get("spend_usd", 0.0))
    cap = float(doc.get("cap_usd", cfg.VISION_DAILY_CAP_USD))
    return (
        jsonify(
            {
                "spend_usd": spend,
                "cap_usd": cap,
                "paused": spend >= cap,
                "date": today_str,
            }
        ),
        200,
    )
