// StreakBadge — Phase 5 Plan 05 (P5-D.3).
//
// SERVER component. Renders the soft-streak pill near the kcal ring.
// Colour-coded by state per DASH-06:
//   active  -> emerald
//   paused  -> amber
//   broken  -> gray
// When streakCount === 0, renders a 'Start a streak' affordance instead
// of the flame.

import type { StreakState } from "@/lib/zod-schemas";
import { cn } from "@/lib/utils";

interface StreakBadgeProps {
  streakCount: number;
  streakState: StreakState;
}

const STATE_CLASSES: Record<StreakState, string> = {
  active: "bg-emerald-100 text-emerald-900",
  paused: "bg-amber-100 text-amber-900",
  broken: "bg-gray-100 text-gray-900",
};

export function StreakBadge({ streakCount, streakState }: StreakBadgeProps) {
  if (streakCount === 0) {
    return (
      <div
        className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-900"
        data-testid="streak-badge"
        data-streak-count="0"
        data-streak-state={streakState}
      >
        <span aria-hidden="true">⚡</span>
        <span>Start a streak</span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium tabular-nums",
        STATE_CLASSES[streakState],
      )}
      data-testid="streak-badge"
      data-streak-count={streakCount}
      data-streak-state={streakState}
      aria-label={`${streakCount}-day streak, ${streakState}`}
    >
      <span aria-hidden="true">🔥</span>
      <span>{streakCount}</span>
    </div>
  );
}
