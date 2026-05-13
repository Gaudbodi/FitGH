"""Race-safe Mongo helpers for the Phase 4 daily caps + cost breaker.

Phase 4 Plan 04 — Task P4-A.3.

Two cap mechanisms guard the vision route:

  1. Per-user 8/day. Counter doc in `vision_usage` keyed on (user_id, date).
     The conditional-update pattern below is the race-safety guarantee
     (T-04-02):

         vision_usage.update_one(
             {"user_id": uid, "date": today, "count": {"$lt": CAP}},
             {"$inc": {"count": 1}, ...},
             upsert=True,
         )

     With the unique index on (user_id, date), two concurrent first-call
     upserts may race the DuplicateKeyError path — we catch + retry once
     unconditionally to land on a stable existing doc.

  2. Global $/day. Single doc {_id: "vision_budget"} in `system_state`.
     The check is SPLIT into two functions (planner-flagged risk #3 — A.3
     ships the split shape from day one to keep B.1's route logic linear):

       - `check_global_budget(coll, today, cap)` — pure READ. Returns
         `(allowed, current_spend)`. NEVER mutates spend_usd.
       - `record_spend_post_call(coll, today, cost, cap)` — POST-call
         atomic $inc with day-roll. Returns the updated doc.

     T-04-03 (race): two requests may both pass the pre-check and both
     call Anthropic; both record_spend_post_call $inc calls land, so we
     overshoot by ~1 call (~$0.01). The cap is a circuit breaker, not a
     hard quota — overshoot is accepted (CONTEXT D-GLOBAL-BREAKER-RACE-SAFE).

  3. `mark_alert_fired(coll, today)` — idempotent latch on the singleton's
     alert_fired flag so the cost-alert webhook only fires once per day.

All helpers take a Mongo collection HANDLE so they're trivially
mongomock-testable. NO Flask imports. NO route-level logic — that lives
in `app/routes/scan.py` (P4-B.1).
"""

from __future__ import annotations

from datetime import UTC, datetime

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

USER_DAILY_CAP = 8
DEFAULT_VISION_DAILY_CAP_USD = 5.0


def today_utc_str() -> str:
    """Single source of truth for the daily key."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Per-user 8/day
# ---------------------------------------------------------------------------


def check_and_increment_user_daily(
    vision_usage_coll, user_id: str, today_str: str
) -> tuple[bool, int]:
    """Atomically increment count when below the cap; return (allowed, count).

    Returns:
        (True, new_count)  on successful increment (count <= CAP).
        (False, CAP)       when count already == CAP — no increment.

    Race-safe via the conditional filter `count: {$lt: CAP}` — if a
    parallel request just landed the cap-th increment, this one's
    `update_one` matches no docs and `upserted_id` is None and the
    existing doc still has count==CAP, so we return (False, CAP).

    On unique-index DuplicateKeyError (two parallel first-call upserts
    race), retry ONCE without the conditional filter — at that point
    the doc exists and the conditional $inc will succeed (count < CAP)
    or no-op (count >= CAP).
    """
    filter_q = {"user_id": user_id, "date": today_str, "count": {"$lt": USER_DAILY_CAP}}
    update = {
        "$inc": {"count": 1},
        "$set": {"last_call_at": datetime.now(UTC)},
        "$setOnInsert": {"user_id": user_id, "date": today_str},
    }
    try:
        result = vision_usage_coll.update_one(filter_q, update, upsert=True)
    except DuplicateKeyError:
        # Two parallel first-call upserts raced; the other thread won the
        # insert, the conditional filter prevented us from incrementing
        # because the filter requires count < CAP AND the doc to match
        # (user_id, date). Retry without the conditional filter so we
        # land on the existing doc.
        result = vision_usage_coll.update_one(
            {"user_id": user_id, "date": today_str, "count": {"$lt": USER_DAILY_CAP}},
            update,
            upsert=False,
        )

    # Did we increment?
    if result.upserted_id is not None or result.modified_count > 0:
        doc = vision_usage_coll.find_one({"user_id": user_id, "date": today_str})
        return (True, doc["count"])

    # No match → existing doc has count >= CAP. Return current count.
    doc = vision_usage_coll.find_one({"user_id": user_id, "date": today_str})
    if doc is None:
        # Should be unreachable, but guard anyway.
        return (False, 0)
    return (False, doc["count"])


# ---------------------------------------------------------------------------
# Global $/day — split into pre-check (read) + post-call record (write)
# ---------------------------------------------------------------------------


def check_global_budget(
    system_state_coll, today_str: str, cap_usd: float
) -> tuple[bool, float]:
    """PRE-call read-only check. Returns (allowed, current_spend_usd).

    NEVER mutates spend_usd. Day-roll handling: if the doc's `date` !=
    today_str, treat as zero spend (record_spend_post_call replaces the
    doc on the next call).
    """
    doc = system_state_coll.find_one({"_id": "vision_budget"})
    if doc is None or doc.get("date") != today_str:
        return (True, 0.0)
    spend = float(doc.get("spend_usd", 0.0))
    effective_cap = float(doc.get("cap_usd", cap_usd))
    if spend >= effective_cap:
        return (False, spend)
    return (True, spend)


def record_spend_post_call(
    system_state_coll, today_str: str, spend_usd: float, cap_usd: float
) -> dict:
    """POST-call atomic spend record. Returns the updated doc.

    Day-roll: if the existing doc's `date` != today_str, REPLACE it with
    a fresh doc (this call's spend, alert_fired=False, today's date).
    Otherwise $inc atomically.

    Always upserts so the very first call of the day lands a fresh doc.
    """
    # Day-roll first: replace any stale-dated doc with a fresh one.
    stale_filter = {"_id": "vision_budget", "date": {"$ne": today_str}}
    fresh_doc = {
        "_id": "vision_budget",
        "date": today_str,
        "spend_usd": float(spend_usd),
        "cap_usd": float(cap_usd),
        "alert_fired": False,
    }
    replaced = system_state_coll.find_one_and_replace(
        stale_filter,
        fresh_doc,
        upsert=False,
        return_document=ReturnDocument.AFTER,
    )
    if replaced is not None:
        return replaced

    # Same-day path: atomic $inc + upsert (covers the missing-doc case too).
    result = system_state_coll.find_one_and_update(
        {"_id": "vision_budget", "date": today_str},
        {
            "$inc": {"spend_usd": float(spend_usd)},
            "$setOnInsert": {
                "_id": "vision_budget",
                "date": today_str,
                "cap_usd": float(cap_usd),
                "alert_fired": False,
            },
            "$set": {"cap_usd": float(cap_usd)},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return result


# ---------------------------------------------------------------------------
# Alert latch
# ---------------------------------------------------------------------------


def mark_alert_fired(system_state_coll, today_str: str) -> None:
    """Set alert_fired=True on the today's-day singleton. Idempotent."""
    system_state_coll.update_one(
        {"_id": "vision_budget", "date": today_str},
        {"$set": {"alert_fired": True}},
    )


__all__ = [
    "DEFAULT_VISION_DAILY_CAP_USD",
    "USER_DAILY_CAP",
    "check_and_increment_user_daily",
    "check_global_budget",
    "mark_alert_fired",
    "record_spend_post_call",
    "today_utc_str",
]
