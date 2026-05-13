"""Tests for app.lib.rate_limit (Phase 4, Task P4-A.3).

Covers:
  - check_and_increment_user_daily — race-safe 8/day per-user counter.
  - check_global_budget            — read-only PRE-call check (no $inc).
  - record_spend_post_call         — POST-call atomic $inc with day-roll.
  - mark_alert_fired               — idempotent latch on the singleton.

Per planner-flagged risk #3: A.3 ships the SPLIT shape from day one —
`check_global_budget` (pure read, returns (allowed, current_spend))
and `record_spend_post_call` (post-call atomic $inc) — instead of a
combined `check_and_record_spend` that P4-B.1 would have had to
refactor. This keeps the route logic linear:
  pre-check (read)  -> call Anthropic  -> post-record (atomic $inc).

T-04-03 (global budget race): two requests can both pass the pre-check
and both call Anthropic; both spend records land via $inc, so we may
overshoot the cap by ~1 call (~$0.01). The cap is a circuit breaker,
not a hard quota — overshoot is documented and accepted.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta

import mongomock
import pymongo
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vision_usage_coll():
    """Mongomock vision_usage collection with the unique index Atlas has."""
    coll = mongomock.MongoClient()["fitgh"]["vision_usage"]
    # Mirror the operator-side unique index so dup-key behaviour matches.
    coll.create_index([("user_id", 1), ("date", 1)], unique=True)
    return coll


@pytest.fixture
def system_state_coll():
    coll = mongomock.MongoClient()["fitgh"]["system_state"]
    return coll


# ---------------------------------------------------------------------------
# check_and_increment_user_daily
# ---------------------------------------------------------------------------


def test_first_user_call_creates_doc_with_count_1(vision_usage_coll):
    from app.lib.rate_limit import check_and_increment_user_daily

    allowed, count = check_and_increment_user_daily(
        vision_usage_coll, "user_abc", "2026-05-13"
    )
    assert allowed is True
    assert count == 1
    doc = vision_usage_coll.find_one({"user_id": "user_abc", "date": "2026-05-13"})
    assert doc["count"] == 1
    assert isinstance(doc["last_call_at"], datetime)


def test_subsequent_user_call_increments_count(vision_usage_coll):
    from app.lib.rate_limit import check_and_increment_user_daily

    check_and_increment_user_daily(vision_usage_coll, "user_abc", "2026-05-13")
    allowed, count = check_and_increment_user_daily(
        vision_usage_coll, "user_abc", "2026-05-13"
    )
    assert allowed is True
    assert count == 2


def test_user_daily_cap_blocks_at_8(vision_usage_coll):
    from app.lib.rate_limit import USER_DAILY_CAP, check_and_increment_user_daily

    for _ in range(USER_DAILY_CAP):
        allowed, _ = check_and_increment_user_daily(
            vision_usage_coll, "user_abc", "2026-05-13"
        )
        assert allowed is True
    # 9th call blocked.
    allowed, count = check_and_increment_user_daily(
        vision_usage_coll, "user_abc", "2026-05-13"
    )
    assert allowed is False
    assert count == USER_DAILY_CAP  # didn't over-increment


def test_user_daily_cap_does_not_over_increment(vision_usage_coll):
    """T-04-02: the conditional filter `count: {$lt: 8}` prevents the
    9th-call increment so a user that hammers the endpoint sees count=8
    (not 9 or 10) in vision_usage."""
    from app.lib.rate_limit import check_and_increment_user_daily

    for _ in range(15):
        check_and_increment_user_daily(vision_usage_coll, "user_abc", "2026-05-13")
    doc = vision_usage_coll.find_one({"user_id": "user_abc", "date": "2026-05-13"})
    assert doc["count"] == 8


def test_user_daily_cap_race_at_most_8_succeed(vision_usage_coll):
    """T-04-02: fire 10 simultaneous calls; at most 8 return allowed=True.

    Mongomock honours $inc atomicity within a single Python process so this
    test is deterministic on the mock; Atlas in production uses real
    WiredTiger doc-level locking which is strictly stronger.
    """
    from app.lib.rate_limit import check_and_increment_user_daily

    results: list[bool] = []
    lock = threading.Lock()

    def worker():
        allowed, _ = check_and_increment_user_daily(
            vision_usage_coll, "user_race", "2026-05-13"
        )
        with lock:
            results.append(allowed)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    success_count = sum(1 for r in results if r)
    assert success_count == 8
    doc = vision_usage_coll.find_one({"user_id": "user_race", "date": "2026-05-13"})
    assert doc["count"] == 8


def test_first_call_race_handles_dup_key(vision_usage_coll, monkeypatch):
    """Simulate the unique-index dup-key race: two threads both attempt
    the upsert; the dup-key one retries unconditionally and succeeds with
    count=2.
    """
    from app.lib import rate_limit as rl
    from app.lib.rate_limit import check_and_increment_user_daily

    # Seed an existing doc so the conditional-upsert path races with
    # itself. Then call the function twice serially; the second call
    # should observe a normally-incremented count.
    vision_usage_coll.insert_one(
        {
            "user_id": "user_dup",
            "date": "2026-05-13",
            "count": 1,
            "last_call_at": datetime.now(UTC),
        }
    )
    allowed, count = check_and_increment_user_daily(
        vision_usage_coll, "user_dup", "2026-05-13"
    )
    assert allowed is True
    assert count == 2
    # The function's retry-on-DuplicateKeyError code path is tricky to
    # trigger with mongomock since the upsert+conditional doesn't race
    # against itself in single-threaded code. Verify the function HAS
    # the retry path by patching update_one to raise once, then succeed.
    call_count = {"n": 0}
    real_update_one = vision_usage_coll.update_one

    def fake_update_one(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise pymongo.errors.DuplicateKeyError(
                "fake dup-key on the conditional-upsert"
            )
        return real_update_one(*args, **kwargs)

    monkeypatch.setattr(vision_usage_coll, "update_one", fake_update_one)
    allowed, count = check_and_increment_user_daily(
        vision_usage_coll, "user_dup", "2026-05-13"
    )
    assert allowed is True
    assert count == 3
    assert call_count["n"] >= 2  # the retry path ran

    # Also ensure USER_DAILY_CAP is what we expect.
    assert rl.USER_DAILY_CAP == 8


# ---------------------------------------------------------------------------
# check_global_budget (read-only PRE-call)
# ---------------------------------------------------------------------------


def test_check_global_budget_admits_when_under_cap(system_state_coll):
    from app.lib.rate_limit import check_global_budget

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-13",
            "spend_usd": 1.50,
            "cap_usd": 5.00,
            "alert_fired": False,
        }
    )
    allowed, spend = check_global_budget(
        system_state_coll, "2026-05-13", cap_usd=5.00
    )
    assert allowed is True
    assert spend == 1.50


def test_check_global_budget_denies_when_over_cap(system_state_coll):
    from app.lib.rate_limit import check_global_budget

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-13",
            "spend_usd": 5.50,
            "cap_usd": 5.00,
            "alert_fired": True,
        }
    )
    allowed, spend = check_global_budget(
        system_state_coll, "2026-05-13", cap_usd=5.00
    )
    assert allowed is False
    assert spend == 5.50


def test_check_global_budget_returns_zero_when_no_doc(system_state_coll):
    from app.lib.rate_limit import check_global_budget

    allowed, spend = check_global_budget(
        system_state_coll, "2026-05-13", cap_usd=5.00
    )
    assert allowed is True
    assert spend == 0.0


def test_check_global_budget_treats_stale_date_as_zero(system_state_coll):
    """Day-roll: yesterday's spend doesn't count against today's cap."""
    from app.lib.rate_limit import check_global_budget

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-12",
            "spend_usd": 5.50,
            "cap_usd": 5.00,
            "alert_fired": True,
        }
    )
    allowed, spend = check_global_budget(
        system_state_coll, "2026-05-13", cap_usd=5.00
    )
    assert allowed is True
    assert spend == 0.0


def test_check_global_budget_read_only_does_not_increment(system_state_coll):
    """Critical: the PRE-call check must not mutate spend_usd."""
    from app.lib.rate_limit import check_global_budget

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-13",
            "spend_usd": 1.50,
            "cap_usd": 5.00,
            "alert_fired": False,
        }
    )
    check_global_budget(system_state_coll, "2026-05-13", cap_usd=5.00)
    doc = system_state_coll.find_one({"_id": "vision_budget"})
    assert doc["spend_usd"] == 1.50  # unchanged


# ---------------------------------------------------------------------------
# record_spend_post_call
# ---------------------------------------------------------------------------


def test_record_spend_creates_doc_if_missing(system_state_coll):
    from app.lib.rate_limit import record_spend_post_call

    doc = record_spend_post_call(
        system_state_coll, "2026-05-13", spend_usd=0.005, cap_usd=5.00
    )
    assert doc["_id"] == "vision_budget"
    assert doc["date"] == "2026-05-13"
    assert doc["spend_usd"] == 0.005
    assert doc["cap_usd"] == 5.00
    assert doc["alert_fired"] is False


def test_record_spend_increments_within_day(system_state_coll):
    from app.lib.rate_limit import record_spend_post_call

    record_spend_post_call(system_state_coll, "2026-05-13", 0.005, 5.00)
    doc = record_spend_post_call(system_state_coll, "2026-05-13", 0.003, 5.00)
    assert round(doc["spend_usd"], 6) == 0.008


def test_record_spend_rolls_doc_when_date_changes(system_state_coll):
    """Day-roll: yesterday's doc is replaced — today's call writes a fresh
    one with this call's cost only and alert_fired=False."""
    from app.lib.rate_limit import record_spend_post_call

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-12",
            "spend_usd": 4.99,
            "cap_usd": 5.00,
            "alert_fired": True,
        }
    )
    doc = record_spend_post_call(
        system_state_coll, "2026-05-13", spend_usd=0.005, cap_usd=5.00
    )
    assert doc["date"] == "2026-05-13"
    assert doc["spend_usd"] == 0.005
    assert doc["alert_fired"] is False


def test_record_spend_preserves_alert_fired_within_day(system_state_coll):
    """Alert latch carries forward across calls on the same day so the
    webhook only fires once."""
    from app.lib.rate_limit import record_spend_post_call

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-13",
            "spend_usd": 0.20,
            "cap_usd": 5.00,
            "alert_fired": True,
        }
    )
    doc = record_spend_post_call(system_state_coll, "2026-05-13", 0.005, 5.00)
    assert doc["alert_fired"] is True


# ---------------------------------------------------------------------------
# mark_alert_fired
# ---------------------------------------------------------------------------


def test_mark_alert_fired_sets_latch(system_state_coll):
    from app.lib.rate_limit import mark_alert_fired

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-13",
            "spend_usd": 0.20,
            "cap_usd": 5.00,
            "alert_fired": False,
        }
    )
    mark_alert_fired(system_state_coll, "2026-05-13")
    doc = system_state_coll.find_one({"_id": "vision_budget"})
    assert doc["alert_fired"] is True


def test_mark_alert_fired_idempotent(system_state_coll):
    """Calling twice is a no-op the second time."""
    from app.lib.rate_limit import mark_alert_fired

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-13",
            "spend_usd": 0.20,
            "cap_usd": 5.00,
            "alert_fired": False,
        }
    )
    mark_alert_fired(system_state_coll, "2026-05-13")
    mark_alert_fired(system_state_coll, "2026-05-13")
    doc = system_state_coll.find_one({"_id": "vision_budget"})
    assert doc["alert_fired"] is True


def test_mark_alert_fired_does_not_touch_wrong_day(system_state_coll):
    """Yesterday's doc with date != today is not affected."""
    from app.lib.rate_limit import mark_alert_fired

    system_state_coll.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-12",
            "spend_usd": 0.20,
            "cap_usd": 5.00,
            "alert_fired": False,
        }
    )
    mark_alert_fired(system_state_coll, "2026-05-13")
    doc = system_state_coll.find_one({"_id": "vision_budget"})
    assert doc["alert_fired"] is False


# ---------------------------------------------------------------------------
# today_utc_str
# ---------------------------------------------------------------------------


def test_today_utc_str_returns_yyyymmdd():
    from app.lib.rate_limit import today_utc_str

    s = today_utc_str()
    assert len(s) == 10
    assert s[4] == "-"
    assert s[7] == "-"
    # Within one second of UTC now.
    expected = datetime.now(UTC).strftime("%Y-%m-%d")
    # Allow yesterday boundary slip — but always YYYY-MM-DD shape.
    assert s in {expected, (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")}
