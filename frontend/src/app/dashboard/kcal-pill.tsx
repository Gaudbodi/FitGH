// KcalPill — Phase 3 Plan 03 (P3-D.1); refactored Phase 5 (P5-D.1).
//
// SERVER component. Renders the static pill (no client JS). The visual
// kcal RING is the new Phase 5 animated companion (KcalRing); the pill
// remains as the textual remaining-kcal callout BELOW the ring.

import { kcalColorBand, kcalColorClasses } from "@/lib/kcal-color";
import { cn } from "@/lib/utils";

interface KcalPillProps {
  totalKcal: number;
  targetKcal: number;
}

export function KcalPill({ totalKcal, targetKcal }: KcalPillProps) {
  const band = kcalColorBand(totalKcal, targetKcal);
  const { bg, text } = kcalColorClasses(band);

  const remaining = targetKcal - totalKcal;
  const remainingLabel =
    remaining >= 0
      ? `${remaining} remaining`
      : `over by ${Math.abs(remaining)} kcal`;

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-full px-4 py-2 text-sm font-medium tabular-nums",
        bg,
        text,
      )}
    >
      <span>
        {totalKcal} / {targetKcal} kcal
      </span>
      <span className="opacity-80">{remainingLabel}</span>
    </div>
  );
}
