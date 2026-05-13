// Meal-log island — Phase 3 Plan 03 (P3-D.1) + Phase 4 Plan 04 (P4-D.3).
//
// CLIENT component. Owns:
//   - SnapMealCta (Phase 4) — opens ScanSheet for the wedge feature.
//     Lazy-loaded via next/dynamic so the dashboard's initial bundle
//     skips the scan UI + browser-image-compression chunks until the
//     user actually taps "Snap a meal".
//   - "Log meal manually" CTA button (opens MealLogModal in create mode).
//   - TodaysMealsList (calls openEdit on each meal's Edit button).
//   - MealLogModal (single instance, switches between create / edit).
//
// 429/503 from the scan path call openCreate() so the user's intent
// to log a meal persists even when vision is unavailable.

"use client";

import * as React from "react";
import dynamic from "next/dynamic";

import { Button } from "@/components/ui/button";
import { MealLogModal } from "./meal-log-modal";
import { TodaysMealsList } from "./todays-meals-list";
import type { MealResponse } from "@/lib/zod-schemas";

// Lazy-load SnapMealCta — the scan-sheet pulls in browser-image-compression
// (lazy itself) + Dialog + chips. None of it is needed until the user
// taps the button, so next/dynamic with ssr: false keeps the dashboard's
// First Load JS clear of the scan UI. (D-LAZY-COMPRESS extended.)
const SnapMealCta = dynamic(
  () => import("./snap-meal-cta").then((m) => m.SnapMealCta),
  {
    ssr: false,
    loading: () => (
      <Button type="button" size="lg" className="w-full" disabled>
        Snap a meal
      </Button>
    ),
  },
);

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
      <div className="flex flex-col gap-2">
        <SnapMealCta onFallbackToManual={openCreate} />
        <Button
          type="button"
          variant="outline"
          onClick={openCreate}
          className="w-full"
        >
          Log meal manually
        </Button>
      </div>
      <h2 className="text-base font-medium">Today&apos;s meals</h2>
      <TodaysMealsList meals={meals} onEdit={openEdit} />
      <MealLogModal open={open} onOpenChange={setOpen} initial={editTarget} />
    </div>
  );
}
