// SnapMealCta — Phase 4 Plan 04 (P4-D.3).
//
// Client component. Renders the primary "Snap a meal" button on /dashboard.
// Click opens ScanSheet. 429/503/parse errors propagate to the parent's
// onFallbackToManual which opens the Phase 3 MealLogModal in create mode.
//
// Per CONTEXT.md: this is the wedge CTA — rendered ABOVE the manual log.

"use client";

import * as React from "react";
import { CameraIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScanSheet } from "./scan-sheet";

interface SnapMealCtaProps {
  onFallbackToManual: () => void;
}

export function SnapMealCta({ onFallbackToManual }: SnapMealCtaProps) {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <Button
        type="button"
        size="lg"
        className="w-full"
        onClick={() => setOpen(true)}
      >
        <CameraIcon className="size-4 mr-2" />
        Snap a meal
      </Button>
      <ScanSheet
        open={open}
        onOpenChange={setOpen}
        onFallbackToManual={onFallbackToManual}
      />
    </>
  );
}
