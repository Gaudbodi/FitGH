// Shared kcal-color helper — Phase 5 Plan 05 (P5-D.1).
//
// Refactored out of `src/app/dashboard/kcal-pill.tsx` (Phase 3) so the
// same band logic drives:
//   - KcalPill (existing)
//   - KcalRing (P5-D.2 — needs the stroke hex)
//   - WeeklyKcalChart bar fill (P5-C.3 — needs the hex per-day)
//
// Single source of truth for the RED/AMBER/GREEN bands so any future visual
// adjustment (e.g. switch from 0.9 to 0.85 amber threshold) lands in ONE
// place.

export type KcalBand = "green" | "amber" | "red";

/** Map (consumed, target) -> one of "green" | "amber" | "red".
 *
 * Rules:
 *   - target <= 0: "red" if consumed > 0, else "green" (defensive — target
 *     should never be <= 0 since Phase 2 floors at 1200 kcal, but we
 *     guard so a bad doc doesn't NaN the dashboard).
 *   - consumed > target: "red"
 *   - consumed > 0.9 * target: "amber"
 *   - otherwise: "green"
 */
export function kcalColorBand(
  totalKcal: number,
  targetKcal: number,
): KcalBand {
  if (targetKcal <= 0) return totalKcal > 0 ? "red" : "green";
  if (totalKcal > targetKcal) return "red";
  if (totalKcal > 0.9 * targetKcal) return "amber";
  return "green";
}

/** Tailwind class names + raw hex stroke for the resolved band.
 *
 * The `stroke` hex is what KcalRing and WeeklyKcalChart need — Recharts
 * does NOT understand Tailwind utility classes and CSS variable lookups
 * on SVG attributes are unreliable across browsers. Hex strings are the
 * portable contract.
 */
export function kcalColorClasses(band: KcalBand): {
  bg: string;
  text: string;
  stroke: string;
} {
  switch (band) {
    case "red":
      return {
        bg: "bg-red-100",
        text: "text-red-900",
        stroke: "#dc2626", // tailwind red-600
      };
    case "amber":
      return {
        bg: "bg-amber-100",
        text: "text-amber-900",
        stroke: "#d97706", // tailwind amber-600
      };
    case "green":
    default:
      return {
        bg: "bg-emerald-100",
        text: "text-emerald-900",
        stroke: "#10b981", // tailwind emerald-500
      };
  }
}
