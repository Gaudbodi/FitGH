// Meal-log island — Phase 3 Plan 03 (P3-D.1).
//
// CLIENT component. Owns:
//   - "Log meal" CTA button (opens MealLogModal in create mode).
//   - TodaysMealsList (calls openEdit on each meal's Edit button).
//   - MealLogModal (single instance, switches between create / edit).
//
// Kept as one cohesive island per the plan's note that splitting the
// three filenames is OK as long as the three responsibilities are
// present. The dashboard imports just <MealLogIsland />.

"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { MealLogModal } from "./meal-log-modal";
import { TodaysMealsList } from "./todays-meals-list";
import type { MealResponse } from "@/lib/zod-schemas";

interface MealLogIslandProps {
  meals: MealResponse[];
}

export function MealLogIsland({ meals }: MealLogIslandProps) {
  const [open, setOpen] = React.useState(false);
  const [editTarget, setEditTarget] = React.useState<MealResponse | undefined>(
    undefined,
  );

  const openCreate = () => {
    setEditTarget(undefined);
    setOpen(true);
  };
  const openEdit = (m: MealResponse) => {
    setEditTarget(m);
    setOpen(true);
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-medium">Today&apos;s meals</h2>
        <Button type="button" onClick={openCreate}>
          Log meal
        </Button>
      </div>
      <TodaysMealsList meals={meals} onEdit={openEdit} />
      <MealLogModal open={open} onOpenChange={setOpen} initial={editTarget} />
    </div>
  );
}
