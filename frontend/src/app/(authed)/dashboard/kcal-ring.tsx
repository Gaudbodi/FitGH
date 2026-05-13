"use client";

// KcalRing — Phase 5 Plan 05 (P5-D.2).
//
// 180x180 SVG ring. Two concentric circles: a gray track + a colour-banded
// progress arc using stroke-dasharray + stroke-dashoffset. When totalKcal
// changes, the CSS transition animates the dashoffset over 600ms — that
// transition is collapsed by globals.css `[data-motion='disabled']` so
// reduced-motion users see an instantaneous update.
//
// Color stroke is shared with KcalPill + WeeklyKcalChart via kcal-color.ts.

import { kcalColorBand, kcalColorClasses } from "@/lib/kcal-color";

interface KcalRingProps {
  totalKcal: number;
  targetKcal: number;
  motionDisabled?: boolean;
}

// Geometry. r=80 inside a 180x180 svg (cx=cy=90) leaves a 10px padding
// for stroke width without clipping.
const R = 80;
const CIRC = 2 * Math.PI * R;

export function KcalRing({
  totalKcal,
  targetKcal,
  motionDisabled = false,
}: KcalRingProps) {
  const safeTarget = targetKcal > 0 ? targetKcal : 1;
  const pct = Math.min(Math.max(totalKcal / safeTarget, 0), 1);
  const offset = CIRC * (1 - pct);
  const band = kcalColorBand(totalKcal, targetKcal);
  const { stroke } = kcalColorClasses(band);

  // Transition collapses to 0ms when MotionDetector flips data-motion on
  // <html>. The inline 600ms is the default; the global CSS rule overrides
  // it via the !important duration. We also short-circuit at the prop
  // level so consumers that pass motionDisabled=true skip the transition
  // even without the global stylesheet (defensive).
  const transition = motionDisabled
    ? "stroke-dashoffset 0ms"
    : "stroke-dashoffset 600ms ease";

  return (
    <div
      className="flex flex-col items-center gap-1"
      data-testid="kcal-ring-wrapper"
    >
      <svg
        width={180}
        height={180}
        viewBox="0 0 180 180"
        role="img"
        aria-label={`${totalKcal} of ${targetKcal} kcal consumed`}
      >
        {/* Track */}
        <circle
          cx={90}
          cy={90}
          r={R}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={10}
        />
        {/* Progress arc — rotated -90deg so it starts from 12 o'clock. */}
        <circle
          cx={90}
          cy={90}
          r={R}
          fill="none"
          stroke={stroke}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={offset}
          transform="rotate(-90 90 90)"
          style={{ transition }}
          data-testid="kcal-ring-progress"
        />
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="20"
          fontWeight="600"
          fill="currentColor"
          className="tabular-nums"
        >
          {totalKcal}
        </text>
        <text
          x="50%"
          y="62%"
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="11"
          fill="currentColor"
          opacity={0.6}
        >
          / {targetKcal} kcal
        </text>
      </svg>
    </div>
  );
}

// Export geometry constants for tests.
export const KCAL_RING_RADIUS = R;
export const KCAL_RING_CIRCUMFERENCE = CIRC;
