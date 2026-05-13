"use client";

// WeeklyKcalChart — Phase 5 Plan 05 (P5-C.3).
//
// Recharts BarChart with a target reference line overlay. The component
// backfills the 7-day window so missing days render as 0-kcal bars rather
// than collapsing the x-axis. Bar fill colours come from the shared
// `kcalColorBand` helper (P5-D.1) — same source of truth as KcalPill and
// KcalRing.

import {
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { kcalColorBand, kcalColorClasses } from "@/lib/kcal-color";
import type { DayMealsResponse } from "@/lib/zod-schemas";

export interface WeeklyKcalChartProps {
  days: ReadonlyArray<DayMealsResponse>;
  targetKcal: number;
  motionDisabled?: boolean;
}

interface ChartDatum {
  date: string;
  total_kcal: number;
  label: string; // Mon | Tue | ...
  fill: string;
}

function ymd(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function buildWindow(
  days: ReadonlyArray<DayMealsResponse>,
  targetKcal: number,
): ChartDatum[] {
  // Build [today-6 .. today]; for each, look up days[].date match or 0.
  const byDate = new Map<string, number>();
  for (const d of days) {
    byDate.set(d.date, d.total_kcal);
  }
  const out: ChartDatum[] = [];
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const day = new Date(today);
    day.setUTCDate(today.getUTCDate() - i);
    const date = ymd(day);
    const total = byDate.get(date) ?? 0;
    const band = kcalColorBand(total, targetKcal);
    const fill = kcalColorClasses(band).stroke;
    out.push({
      date,
      total_kcal: total,
      label: day.toLocaleDateString("en-US", { weekday: "short" }),
      fill,
    });
  }
  return out;
}

export function WeeklyKcalChart({
  days,
  targetKcal,
  motionDisabled = false,
}: WeeklyKcalChartProps) {
  const data = buildWindow(days, targetKcal);

  return (
    <section
      className="space-y-2"
      aria-labelledby="weekly-kcal-chart-heading"
      data-testid="weekly-kcal-chart"
    >
      <h3 id="weekly-kcal-chart-heading" className="text-sm font-medium">
        This week&apos;s kcal vs target
      </h3>
      <div className="h-64 w-full" data-testid="weekly-kcal-chart-canvas">
        <ResponsiveContainer width="100%" height={256}>
          <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
            <XAxis
              dataKey="label"
              fontSize={11}
              stroke="#6b7280"
              tickLine={false}
            />
            <YAxis
              fontSize={11}
              stroke="#6b7280"
              width={48}
              tickFormatter={(v: number) => `${Math.round(v)}`}
            />
            <Tooltip
              formatter={(value) => {
                const n = typeof value === "number" ? value : Number(value);
                return [`${Math.round(n)} kcal`, "Total"];
              }}
              animationDuration={motionDisabled ? 0 : 200}
              contentStyle={{ fontSize: 12 }}
            />
            <ReferenceLine
              y={targetKcal}
              stroke="#64748b"
              strokeDasharray="3 3"
              label={{
                value: "Target",
                position: "right",
                fill: "#64748b",
                fontSize: 10,
              }}
            />
            <Bar
              dataKey="total_kcal"
              isAnimationActive={!motionDisabled}
              animationDuration={600}
              radius={[3, 3, 0, 0]}
            >
              {data.map((d) => (
                <Cell key={d.date} fill={d.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
