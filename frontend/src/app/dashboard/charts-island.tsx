"use client";

// ChartsIsland — Phase 5 Plan 05 (P5-D.3).
//
// Client wrapper that lazy-loads the Recharts components via next/dynamic
// with ssr:false. Next 15 forbids ssr:false in Server Components, so the
// dashboard server page imports THIS island instead. The Recharts payload
// ships ONLY to the client and ONLY when this island renders.

import nextDynamic from "next/dynamic";
import { ChartLoadingSkeleton } from "@/components/charts/loading-skeleton";
import type { DayMealsResponse, WeightLogResponse } from "@/lib/zod-schemas";

const WeightChart = nextDynamic(
  () => import("@/components/charts").then((m) => m.WeightChart),
  { ssr: false, loading: () => <ChartLoadingSkeleton /> },
);

const WeeklyKcalChart = nextDynamic(
  () => import("@/components/charts").then((m) => m.WeeklyKcalChart),
  { ssr: false, loading: () => <ChartLoadingSkeleton /> },
);

export interface ChartsIslandProps {
  weights: ReadonlyArray<WeightLogResponse>;
  weekDays: ReadonlyArray<DayMealsResponse>;
  targetKcal: number;
}

export function ChartsIsland({
  weights,
  weekDays,
  targetKcal,
}: ChartsIslandProps) {
  return (
    <>
      <WeeklyKcalChart days={weekDays} targetKcal={targetKcal} />
      <WeightChart entries={weights} rangeDays={30} />
    </>
  );
}
