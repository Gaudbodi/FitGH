"use client";

// WeightChart — Phase 5 Plan 05 (P5-C.2).
//
// Recharts LineChart. Lazy-loaded into the /dashboard route via
// next/dynamic so Recharts (~25 kB gzipped) lives in a client chunk
// that doesn't tax the dashboard's server-rendered HTML JS budget.
//
// Props expose `motionDisabled` so the parent (or MotionDetector via the
// data-motion attribute) can short-circuit chart animation under
// prefers-reduced-motion / slow connections.

import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { WeightLogResponse } from "@/lib/zod-schemas";

export type WeightChartRange = 30 | 90;

export interface WeightChartProps {
  entries: ReadonlyArray<WeightLogResponse>;
  rangeDays?: WeightChartRange;
  motionDisabled?: boolean;
  onRangeChange?: (r: WeightChartRange) => void;
}

const STROKE = "#10b981"; // tailwind emerald-500

interface ChartDatum {
  kg: number;
  date: string; // YYYY-MM-DD
}

function filterAndSort(
  entries: ReadonlyArray<WeightLogResponse>,
  rangeDays: WeightChartRange,
): ChartDatum[] {
  if (entries.length === 0) return [];
  // Treat the most-recent entry as the anchor of the rangeDays window.
  // Entries are newest-first per Phase 2 GET /api/weights contract.
  const sortedAsc = [...entries].sort(
    (a, b) =>
      new Date(a.logged_at).getTime() - new Date(b.logged_at).getTime(),
  );
  const newest = sortedAsc[sortedAsc.length - 1];
  const cutoff =
    new Date(newest.logged_at).getTime() - rangeDays * 24 * 60 * 60 * 1000;
  return sortedAsc
    .filter((e) => new Date(e.logged_at).getTime() >= cutoff)
    .map((e) => ({
      kg: e.kg,
      date: e.logged_at.slice(0, 10), // YYYY-MM-DD
    }));
}

export function WeightChart({
  entries,
  rangeDays: controlledRange,
  motionDisabled = false,
  onRangeChange,
}: WeightChartProps) {
  const [localRange, setLocalRange] = useState<WeightChartRange>(30);
  const rangeDays = controlledRange ?? localRange;

  const data = filterAndSort(entries, rangeDays);

  const setRange = (r: WeightChartRange) => {
    if (onRangeChange) {
      onRangeChange(r);
    } else {
      setLocalRange(r);
    }
  };

  return (
    <section
      className="space-y-2"
      aria-labelledby="weight-chart-heading"
      data-testid="weight-chart"
      data-range-days={rangeDays}
    >
      <div className="flex items-center justify-between">
        <h3 id="weight-chart-heading" className="text-sm font-medium">
          Weight trend
        </h3>
        <div className="flex gap-1" role="tablist" aria-label="Date range">
          {([30, 90] as const).map((r) => (
            <button
              key={r}
              type="button"
              role="tab"
              aria-selected={r === rangeDays}
              onClick={() => setRange(r)}
              className={
                r === rangeDays
                  ? "rounded-md bg-foreground px-2 py-1 text-xs font-medium text-background"
                  : "rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-muted"
              }
            >
              {r}d
            </button>
          ))}
        </div>
      </div>
      {data.length === 0 ? (
        <p className="rounded-md border border-dashed border-muted p-6 text-center text-sm text-muted-foreground">
          Log a weight to see your trend
        </p>
      ) : (
        <div className="h-64 w-full" data-testid="weight-chart-canvas">
          <ResponsiveContainer width="100%" height={256}>
            <LineChart
              data={data}
              margin={{ top: 8, right: 16, left: 0, bottom: 4 }}
            >
              <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(d: string) => d.slice(5)}
                fontSize={11}
                stroke="#6b7280"
              />
              <YAxis
                tickFormatter={(v: number) => `${v.toFixed(1)} kg`}
                domain={["dataMin - 1", "dataMax + 1"]}
                fontSize={11}
                stroke="#6b7280"
                width={56}
              />
              <Tooltip
                formatter={(value) => {
                  const n = typeof value === "number" ? value : Number(value);
                  return [`${n.toFixed(1)} kg`, "Weight"];
                }}
                animationDuration={motionDisabled ? 0 : 200}
                contentStyle={{ fontSize: 12 }}
              />
              <Line
                type="monotone"
                dataKey="kg"
                stroke={STROKE}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 4 }}
                isAnimationActive={!motionDisabled}
                animationDuration={600}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
