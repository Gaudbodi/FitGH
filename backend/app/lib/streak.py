"""Soft-streak with 1-day grace — Phase 5 Plan 05 (P5-A.2).

Pure helper. No Mongo, no clock side effect. Callers supply the wall-clock
`now_utc` (so tests can drive deterministic timelines) and the user's IANA
timezone string. The helper:

  1. Converts `now_utc` and `last_logged_at_utc` to the user's local date
     via `zoneinfo.ZoneInfo(tz)` (falls back to UTC if `tz` is empty or
     invalid).
  2. Computes the integer day-delta between the two local dates.
  3. Walks the state machine in the table below and returns the new
     (count, state, last_logged_at_utc) tuple.

State machine — Phase 5 CONTEXT.md D-STREAK-1-DAY-GRACE:

  | current_state | last_local        | today_local | new_count        | new_state |
  |---------------|-------------------|-------------|------------------|-----------|
  | *             | None              | today       | 1                | active    |
  | active        | today             | today       | unchanged        | active    |  # idempotent same-day
  | active        | today − 1         | today       | count+1          | active    |  # normal bump
  | active        | today − 2         | today       | count (unchanged)| paused    |  # 1-day grace consumed
  | active        | today − ≥3        | today       | 1                | active    |  # broken+restart
  | paused        | today − 1         | today       | count+1          | active    |  # paused recovery
  | paused        | today − ≥2        | today       | 1                | active    |  # broken+restart
  | broken        | *                 | today       | 1                | active    |  # restart
  | *             | future (skew)     | today       | unchanged        | unchanged |  # clock-skew safety

Race acceptance — T-05-03: Two simultaneous POST /meals + POST /weights
from the same user can both read the same stale `streak_last_logged_at`
and concurrently $set their independent computations. Same-day double log
is idempotent (rule 2), so two same-day concurrent events both compute
"no-op" or both compute "+1" depending on whether last_local==today_local.
The exact-millisecond day-boundary race is bounded to ≤1-count drift in
the user's entire lifetime; we do NOT lock the profile doc. Documented and
accepted; surface is invisible to the user.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

StreakState = Literal["active", "paused", "broken"]


def _safe_zone(tz: str | None) -> ZoneInfo:
    """Resolve tz string to a ZoneInfo; fall back to UTC on empty/invalid."""
    if not tz:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def compute_streak(
    *,
    now_utc: datetime,
    tz: str,
    last_logged_at_utc: datetime | None,
    current_count: int,
    current_state: StreakState,
) -> tuple[int, StreakState, datetime]:
    """Return (new_count, new_state, new_last_logged_at_utc).

    The caller MUST persist all three returned values onto the profile doc.
    `new_last_logged_at_utc` is the supplied `now_utc` whenever the streak
    advances (count changes OR state transitions to active) OR is the prior
    `last_logged_at_utc` otherwise (idempotent same-day, clock-skew safety).
    """
    zone = _safe_zone(tz)

    # Normalize now_utc to tz-aware UTC then convert to local date.
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=UTC)
    today_local = now_utc.astimezone(zone).date()

    # First-ever log — no last_logged_at on the profile.
    if last_logged_at_utc is None:
        return 1, "active", now_utc

    # Normalize last_logged_at to tz-aware UTC then to local date.
    last = last_logged_at_utc
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    last_local = last.astimezone(zone).date()

    days_delta = (today_local - last_local).days

    # Clock-skew safety: future last_logged_at means a previous request was
    # stamped with a server clock ahead of ours. Treat as no-op.
    if days_delta < 0:
        return current_count, current_state, last_logged_at_utc

    # Same-day log — idempotent. Don't bump count, don't move state, keep
    # the prior last_logged_at so the timestamp isn't churned on every meal.
    if days_delta == 0:
        return current_count, current_state, last_logged_at_utc

    # +1 day: depends on current_state.
    if days_delta == 1:
        if current_state == "active":
            return current_count + 1, "active", now_utc
        if current_state == "paused":
            # Paused recovery — count had been held; now bump it.
            return current_count + 1, "active", now_utc
        # broken → restart.
        return 1, "active", now_utc

    # +2 days: 1-day grace consumed (only meaningful from active).
    if days_delta == 2:
        if current_state == "active":
            # Hold the count; flip to paused. The PREVIOUS streak day's
            # last_logged_at is preserved so the grace window is anchored.
            return current_count, "paused", last_logged_at_utc
        # From paused or broken at +2 → restart.
        return 1, "active", now_utc

    # +3 days or more: broken+restart from any state.
    return 1, "active", now_utc
