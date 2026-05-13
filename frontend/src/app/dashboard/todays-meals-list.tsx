// TodaysMealsList — Phase 3 Plan 03 (P3-D.1).
//
// CLIENT component. Renders today's meals list with Edit and Delete
// buttons per row. Delete uses confirm() + router.refresh().

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import type { MealResponse } from "@/lib/zod-schemas";

interface TodaysMealsListProps {
  meals: MealResponse[];
  onEdit: (meal: MealResponse) => void;
}

function timeOnly(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

export function TodaysMealsList({ meals, onEdit }: TodaysMealsListProps) {
  const router = useRouter();
  const [busy, setBusy] = React.useState<string | null>(null);

  if (meals.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No meals logged yet today. Tap <strong>Log meal</strong> to add your
        first one.
      </p>
    );
  }

  const onDelete = async (meal: MealResponse) => {
    if (typeof window !== "undefined") {
      if (!window.confirm("Delete this meal?")) return;
    }
    setBusy(meal.id);
    try {
      const res = await fetch(`/api/meals/${meal.id}`, { method: "DELETE" });
      if (res.status === 404) {
        toast.error("This meal was already removed.");
      } else if (!res.ok) {
        toast.error(`Delete failed (${res.status}).`);
      } else {
        toast.success("Meal deleted");
      }
    } catch {
      toast.error("Network error.");
    } finally {
      setBusy(null);
      router.refresh();
    }
  };

  return (
    <ul className="flex flex-col gap-2">
      {meals.map((meal) => {
        const chips = meal.components.map((c) => c.name).join(" - ");
        return (
          <li
            key={meal.id}
            className="flex flex-col gap-1 rounded-lg border border-input/40 bg-card p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex flex-col">
              <span className="text-xs tabular-nums text-muted-foreground">
                {timeOnly(meal.logged_at)}
              </span>
              <span className="text-sm font-medium">{chips}</span>
              <span className="text-xs tabular-nums text-muted-foreground">
                {meal.total_kcal} kcal - {meal.total_protein_g} g protein
              </span>
            </div>
            <div className="flex gap-2 self-end sm:self-auto">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onEdit(meal)}
                disabled={busy === meal.id}
              >
                Edit
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => onDelete(meal)}
                disabled={busy === meal.id}
              >
                {busy === meal.id ? "..." : "Delete"}
              </Button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
