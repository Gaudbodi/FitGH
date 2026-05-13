// KcalPill — Phase 3 Plan 03 (P3-D.1).
//
// SERVER component. Renders a static pill (no client JS, no animation —
// D-NO-ANIMATION-PHASE-3; animated kcal ring is Phase 5).

import { cn } from "@/lib/utils";

interface KcalPillProps {
  totalKcal: number;
  targetKcal: number;
}

export function KcalPill({ totalKcal, targetKcal }: KcalPillProps) {
  const remaining = targetKcal - totalKcal;
  const isOver = totalKcal > targetKcal;
  const isAmber = !isOver && totalKcal > targetKcal * 0.9;

  const bg = isOver
    ? "bg-red-100 text-red-900"
    : isAmber
      ? "bg-amber-100 text-amber-900"
      : "bg-emerald-100 text-emerald-900";

  const remainingLabel = remaining >= 0
    ? `${remaining} remaining`
    : `over by ${Math.abs(remaining)} kcal`;

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-full px-4 py-2 text-sm font-medium tabular-nums",
        bg,
      )}
    >
      <span>
        {totalKcal} / {targetKcal} kcal
      </span>
      <span className="opacity-80">{remainingLabel}</span>
    </div>
  );
}
