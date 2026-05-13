// DayGroup — Phase 3 Plan 03 (P3-E.1).
//
// SERVER component. Renders one day's worth of meals (read-only — no
// edit / delete buttons; edits happen on /dashboard's TodaysMealsList).

import type { DayMealsResponse } from "@/lib/zod-schemas";

function dateHeader(dateStr: string): string {
  // dateStr is YYYY-MM-DD from the backend. Pass it through Intl to get
  // a weekday suffix; reconstruct as local because the backend already
  // grouped by user-local date.
  const [yyyy, mm, dd] = dateStr.split("-").map((p) => parseInt(p, 10));
  const d = new Date(yyyy, mm - 1, dd);
  const weekday = new Intl.DateTimeFormat("en-US", { weekday: "short" }).format(
    d,
  );
  return `${dateStr} (${weekday})`;
}

function timeOnly(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

export function DayGroup({ day }: { day: DayMealsResponse }) {
  return (
    <section className="flex flex-col gap-2 rounded-lg border border-input/40 bg-card p-4">
      <header className="flex items-center justify-between">
        <h3 className="font-medium">{dateHeader(day.date)}</h3>
        <span className="text-xs tabular-nums text-muted-foreground">
          Total: {day.total_kcal} kcal - {day.total_protein_g} g protein
        </span>
      </header>
      <ul className="flex flex-col gap-1">
        {day.meals.map((meal) => {
          const chips = meal.components.map((c) => c.name).join(" - ");
          return (
            <li
              key={meal.id}
              className="flex flex-col gap-0.5 border-t border-input/20 pt-1 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-baseline gap-2">
                <span className="text-xs tabular-nums text-muted-foreground">
                  {timeOnly(meal.logged_at)}
                </span>
                <span className="text-sm">{chips}</span>
              </div>
              <span className="text-xs tabular-nums font-medium">
                {meal.total_kcal} kcal
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
