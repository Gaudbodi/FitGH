"""Unit tests for app.lib.streak.compute_streak — Phase 5 Plan 05 (P5-A.2).

Pure-helper tests; no Flask, no Mongo. Inject `now_utc` to drive the state
machine deterministically. 13 cases as enumerated in 05-PLAN.md
must_haves.artifacts.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.lib.streak import compute_streak


def _utc(y, m, d, hh=12, mm=0, ss=0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


# ---------------------------------------------------------------------------
# 1. First-ever log
# ---------------------------------------------------------------------------


def test_first_log_creates_streak():
    now = _utc(2026, 5, 13)
    count, state, last = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=None,
        current_count=0,
        current_state="active",
    )
    assert count == 1
    assert state == "active"
    assert last == now


# ---------------------------------------------------------------------------
# 2. Same-day idempotent
# ---------------------------------------------------------------------------


def test_same_day_idempotent():
    now = _utc(2026, 5, 13, 18, 0)
    earlier = _utc(2026, 5, 13, 8, 0)
    count, state, last = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=earlier,
        current_count=3,
        current_state="active",
    )
    assert count == 3
    assert state == "active"
    # Idempotent: do not churn the timestamp on every same-day log.
    assert last == earlier


# ---------------------------------------------------------------------------
# 3. +1 day active bump
# ---------------------------------------------------------------------------


def test_plus_one_day_active():
    now = _utc(2026, 5, 13)
    yesterday = _utc(2026, 5, 12)
    count, state, last = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=yesterday,
        current_count=5,
        current_state="active",
    )
    assert count == 6
    assert state == "active"
    assert last == now


# ---------------------------------------------------------------------------
# 4. +2 day paused
# ---------------------------------------------------------------------------


def test_plus_two_days_paused():
    now = _utc(2026, 5, 13)
    two_days_ago = _utc(2026, 5, 11)
    count, state, last = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=two_days_ago,
        current_count=4,
        current_state="active",
    )
    # 1-day grace consumed: hold count, flip to paused, anchor at prior log.
    assert count == 4
    assert state == "paused"
    assert last == two_days_ago


# ---------------------------------------------------------------------------
# 5. +3 day broken + restart
# ---------------------------------------------------------------------------


def test_plus_three_days_broken_restart():
    now = _utc(2026, 5, 13)
    three_days_ago = _utc(2026, 5, 10)
    count, state, last = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=three_days_ago,
        current_count=12,
        current_state="active",
    )
    # Broken — but the user just logged, so restart at 1.
    assert count == 1
    assert state == "active"
    assert last == now


# ---------------------------------------------------------------------------
# 6. paused recovery on +1 day
# ---------------------------------------------------------------------------


def test_paused_recovery_on_plus_one():
    now = _utc(2026, 5, 13)
    yesterday = _utc(2026, 5, 12)
    count, state, last = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=yesterday,
        current_count=4,
        current_state="paused",
    )
    # Paused -> active recovery: count was held at 4, now bump.
    assert count == 5
    assert state == "active"
    assert last == now


# ---------------------------------------------------------------------------
# 7. paused → broken+restart on +2 day from paused
# ---------------------------------------------------------------------------


def test_paused_to_broken_on_plus_two():
    now = _utc(2026, 5, 13)
    two_days_ago = _utc(2026, 5, 11)
    count, state, last = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=two_days_ago,
        current_count=4,
        current_state="paused",
    )
    # From paused at +2 → restart at 1, active.
    assert count == 1
    assert state == "active"
    assert last == now


# ---------------------------------------------------------------------------
# 8. tz boundary — Accra
# ---------------------------------------------------------------------------


def test_tz_boundary_accra():
    """Africa/Accra (UTC+0 year-round) day boundary aligns with UTC.
    A user logging at 23:30 UTC and re-logging at 00:30 UTC the next day
    sees both events in the SAME Accra day (00:00 → 23:59 GMT), so the
    second is same-day idempotent."""
    accra = "Africa/Accra"
    first = datetime(2026, 5, 13, 23, 30, tzinfo=UTC)
    second = datetime(2026, 5, 14, 0, 30, tzinfo=UTC)
    # First log
    c1, s1, l1 = compute_streak(
        now_utc=first,
        tz=accra,
        last_logged_at_utc=None,
        current_count=0,
        current_state="active",
    )
    assert (c1, s1) == (1, "active")
    # Second log 1h later (next UTC day, same Accra day → same local day,
    # so the date-delta is exactly 1).
    c2, s2, _ = compute_streak(
        now_utc=second,
        tz=accra,
        last_logged_at_utc=l1,
        current_count=c1,
        current_state=s1,
    )
    # 2026-05-13 23:30 UTC = 2026-05-13 23:30 Accra (UTC+0).
    # 2026-05-14 00:30 UTC = 2026-05-14 00:30 Accra.
    # days_delta = 1, current_state=active → count+1.
    assert c2 == 2
    assert s2 == "active"


# ---------------------------------------------------------------------------
# 9. DST-skip day — Europe/London 2026-03-29
# ---------------------------------------------------------------------------


def test_dst_skip_london():
    """Europe/London springs forward 2026-03-29 (01:00 GMT → 02:00 BST).
    A log on 2026-03-28 followed by a log on 2026-03-29 should still
    register as a +1-day bump in local-date terms, irrespective of the
    23-hour calendar day."""
    london = "Europe/London"
    saturday = datetime(2026, 3, 28, 12, 0, tzinfo=UTC)  # 12:00 GMT
    sunday = datetime(2026, 3, 29, 12, 0, tzinfo=UTC)  # 13:00 BST after spring-forward
    c2, s2, _ = compute_streak(
        now_utc=sunday,
        tz=london,
        last_logged_at_utc=saturday,
        current_count=2,
        current_state="active",
    )
    assert c2 == 3
    assert s2 == "active"


# ---------------------------------------------------------------------------
# 10. High count no overflow
# ---------------------------------------------------------------------------


def test_high_count_no_overflow():
    now = _utc(2026, 5, 13)
    yesterday = _utc(2026, 5, 12)
    count, state, _ = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=yesterday,
        current_count=365,
        current_state="active",
    )
    assert count == 366
    assert state == "active"


# ---------------------------------------------------------------------------
# 11. State machine completeness — every (current_state, days_delta) pair
# ---------------------------------------------------------------------------


def test_state_machine_complete():
    """Verifies every cell in the decision table — 9 (state x delta)
    combinations including the future-skew clock case."""
    now = _utc(2026, 5, 13)
    cases = [
        # (current_state, last_delta_days, current_count, expected_count,
        #  expected_state)
        ("active", 0, 7, 7, "active"),
        ("active", 1, 7, 8, "active"),
        ("active", 2, 7, 7, "paused"),
        ("active", 3, 7, 1, "active"),
        ("paused", 1, 7, 8, "active"),
        ("paused", 2, 7, 1, "active"),
        ("paused", 3, 7, 1, "active"),
        ("broken", 1, 7, 1, "active"),
        ("broken", 5, 7, 1, "active"),
    ]
    for cur_state, delta, cur_count, exp_count, exp_state in cases:
        last = now - timedelta(days=delta)
        c, s, _ = compute_streak(
            now_utc=now,
            tz="UTC",
            last_logged_at_utc=last,
            current_count=cur_count,
            current_state=cur_state,  # type: ignore[arg-type]
        )
        assert c == exp_count, (
            f"state={cur_state} delta={delta}: count {c} != {exp_count}"
        )
        assert s == exp_state, (
            f"state={cur_state} delta={delta}: state {s} != {exp_state}"
        )

    # Future-skew clock case (days_delta < 0) — no-op.
    future = now + timedelta(days=1)
    c, s, last_out = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=future,
        current_count=9,
        current_state="active",
    )
    assert c == 9
    assert s == "active"
    assert last_out == future


# ---------------------------------------------------------------------------
# 12. Sub-second precision safe — microseconds don't trip date math
# ---------------------------------------------------------------------------


def test_subsecond_precision_safe():
    now = datetime(2026, 5, 13, 0, 0, 0, 123456, tzinfo=UTC)
    yesterday = datetime(2026, 5, 12, 23, 59, 59, 999999, tzinfo=UTC)
    c, s, _ = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=yesterday,
        current_count=1,
        current_state="active",
    )
    # Different UTC dates (5/12 → 5/13), delta = 1 day, active bump.
    assert c == 2
    assert s == "active"


# ---------------------------------------------------------------------------
# 13. Missing / invalid tz falls back to UTC
# ---------------------------------------------------------------------------


def test_missing_tz_falls_back_utc():
    now = _utc(2026, 5, 13)
    yesterday = _utc(2026, 5, 12)
    # Empty string
    c, s, _ = compute_streak(
        now_utc=now,
        tz="",
        last_logged_at_utc=yesterday,
        current_count=2,
        current_state="active",
    )
    assert c == 3
    assert s == "active"
    # Invalid string
    c, s, _ = compute_streak(
        now_utc=now,
        tz="Not/A/Real/Zone",
        last_logged_at_utc=yesterday,
        current_count=2,
        current_state="active",
    )
    assert c == 3
    assert s == "active"


# ---------------------------------------------------------------------------
# Bonus: naive datetimes are handled (assumed UTC)
# ---------------------------------------------------------------------------


def test_naive_datetimes_treated_as_utc():
    now = datetime(2026, 5, 13, 12, 0)  # naive
    yesterday = datetime(2026, 5, 12, 12, 0)  # naive
    c, s, _ = compute_streak(
        now_utc=now,
        tz="UTC",
        last_logged_at_utc=yesterday,
        current_count=1,
        current_state="active",
    )
    assert c == 2
    assert s == "active"
