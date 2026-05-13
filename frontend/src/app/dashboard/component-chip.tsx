// ComponentChip — Phase 3 Plan 03 (P3-C.2).
//
// Client component. Renders ONE component row inside the meal-log modal:
// chip with food name + portion slider + live kcal_point preview + remove
// button. Emits onChange with the updated draft.
//
// FE-side kcal preview = round(kcal_per_100g * portion_g / 100). The
// server is the source of truth on submit; this is a preview-only mirror
// of app.lib.meals.compute_kcal_for_component.

"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  PORTION_MAX_G,
  PORTION_MIN_G,
  PORTION_STEP_G,
} from "@/lib/zod-schemas";
import { XIcon } from "lucide-react";

export interface ComponentDraft {
  name: string;
  food_id: string | null; // null = free-text component
  portion_g: number;
  kcal_per_100g: number; // derived for preview only
  protein_g_per_100g: number;
  source: "table" | "user_corrected";
}

interface ComponentChipProps {
  component: ComponentDraft;
  onChange: (next: ComponentDraft) => void;
  onRemove: () => void;
}

function previewKcal(c: ComponentDraft): number {
  return Math.round((c.kcal_per_100g * c.portion_g) / 100);
}

function previewProtein(c: ComponentDraft): number {
  return Math.round((c.protein_g_per_100g * c.portion_g) / 100);
}

export function ComponentChip({
  component,
  onChange,
  onRemove,
}: ComponentChipProps) {
  const handleValueChange = (raw: number | readonly number[]) => {
    const next = Array.isArray(raw) ? raw[0] : (raw as number);
    onChange({ ...component, portion_g: next });
  };

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-input/40 bg-card p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col">
          <span className="font-medium leading-tight">{component.name}</span>
          <span className="text-xs text-muted-foreground">
            {component.food_id ? "Matched (Ghana table)" : "Free-text entry"}
          </span>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={onRemove}
          aria-label="Remove component"
        >
          <XIcon />
        </Button>
      </div>

      <Slider
        min={PORTION_MIN_G}
        max={PORTION_MAX_G}
        step={PORTION_STEP_G}
        value={[component.portion_g]}
        onValueChange={handleValueChange}
      />

      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground tabular-nums">
          {component.portion_g} g - {previewProtein(component)} g protein
        </span>
        <span className="font-medium tabular-nums">
          {previewKcal(component)} kcal
        </span>
      </div>
    </div>
  );
}

// Exported helpers reused by the modal's running-total view.
export function draftKcal(c: ComponentDraft): number {
  return previewKcal(c);
}

export function draftProtein(c: ComponentDraft): number {
  return previewProtein(c);
}
