// ScanResultChips — Phase 4 Plan 04 (P4-D.2).
//
// Vertical list of editable ComponentChips, reusing Phase 3's chip + FoodSearch
// primitives verbatim. The difference from MealLogModal's chip layout is
// the side-effect: each chip mutation (name swap, portion drag, remove)
// fires onCorrection so the parent (ScanSheet) can POST /api/corrections
// BEFORE the user presses Confirm. That way even if the user abandons,
// the next scan benefits from the partial correction.
//
// Per CONTEXT.md "Tap-to-edit chips UI" #1–4:
//   1. Tap-to-edit name via FoodSearch (cmdk over /api/foods).
//   2. Portion slider (debounced 500 ms before firing correction).
//   3. Remove chip (fires a "rejected entirely" correction).
//   4. Add component (no correction — LLM omission, not a correction).

"use client";

import * as React from "react";
import { PencilIcon, PlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ComponentChip, type ComponentDraft } from "./component-chip";
import { FoodSearch } from "./food-search";
import {
  PORTION_MAX_G,
  PORTION_MIN_G,
  type GhanaFoodResponse,
} from "@/lib/zod-schemas";

// Local shape — the BFF body is mirrored from this in scan-sheet.tsx.
export interface UserCorrectionInput {
  original_name: string;
  corrected_name: string | null;
  original_portion_g: number;
  corrected_portion_g: number;
  original_food_id: string | null;
  corrected_food_id: string | null;
}

interface ScanResultChipsProps {
  components: ComponentDraft[];
  onChange: (next: ComponentDraft[]) => void;
  onCorrection: (correction: UserCorrectionInput) => void;
}

const PORTION_DEBOUNCE_MS = 500;

export function ScanResultChips({
  components,
  onChange,
  onCorrection,
}: ScanResultChipsProps) {
  // Track the "initial" snapshot per index so portion-correction can compare
  // to the LLM's original value (not the latest in-flight drag).
  const initialSnapshotRef = React.useRef<ComponentDraft[]>([]);
  React.useEffect(() => {
    // First render: capture the LLM-provided components as the baseline.
    if (initialSnapshotRef.current.length === 0) {
      initialSnapshotRef.current = components.map((c) => ({ ...c }));
    }
  }, [components]);

  const [editingIdx, setEditingIdx] = React.useState<number | null>(null);
  const [addingNew, setAddingNew] = React.useState(false);

  // Per-chip debounce timer for portion changes.
  const debounceRef = React.useRef<Record<number, NodeJS.Timeout>>({});

  const fireCorrectionFromInitial = (
    idx: number,
    next: ComponentDraft,
  ) => {
    const initial = initialSnapshotRef.current[idx];
    if (!initial) return;
    onCorrection({
      original_name: initial.name,
      corrected_name: next.name !== initial.name ? next.name : null,
      original_portion_g: initial.portion_g,
      corrected_portion_g: next.portion_g,
      original_food_id: initial.food_id,
      corrected_food_id: next.food_id,
    });
  };

  const replaceComponent = (idx: number, next: ComponentDraft) => {
    onChange(components.map((c, i) => (i === idx ? next : c)));
    // Debounce so a single slider drag fires ONE correction.
    if (debounceRef.current[idx]) clearTimeout(debounceRef.current[idx]);
    debounceRef.current[idx] = setTimeout(() => {
      fireCorrectionFromInitial(idx, next);
    }, PORTION_DEBOUNCE_MS);
  };

  const removeComponent = (idx: number) => {
    const initial = initialSnapshotRef.current[idx];
    if (initial) {
      // "Rejected entirely" correction — corrected_food_id=null + portion=0
      // signals the user said "this isn't on my plate."
      onCorrection({
        original_name: initial.name,
        corrected_name: null,
        original_portion_g: initial.portion_g,
        corrected_portion_g: 0,
        original_food_id: initial.food_id,
        corrected_food_id: null,
      });
    }
    onChange(components.filter((_, i) => i !== idx));
  };

  const swapDish = (idx: number, food: GhanaFoodResponse) => {
    const firstPortion = food.portion_defaults[0]?.grams ?? PORTION_MIN_G;
    const next: ComponentDraft = {
      name: food.name,
      food_id: food.food_id,
      portion_g: Math.min(
        PORTION_MAX_G,
        Math.max(PORTION_MIN_G, firstPortion),
      ),
      kcal_per_100g: food.kcal_per_100g,
      protein_g_per_100g: food.protein_g_per_100g,
      source: "table",
    };
    onChange(components.map((c, i) => (i === idx ? next : c)));
    // Fire correction immediately — name swap is a discrete event.
    fireCorrectionFromInitial(idx, next);
    setEditingIdx(null);
  };

  const onAddNewFood = (food: GhanaFoodResponse) => {
    if (components.length >= 10) {
      setAddingNew(false);
      return;
    }
    const firstPortion = food.portion_defaults[0]?.grams ?? PORTION_MIN_G;
    const newDraft: ComponentDraft = {
      name: food.name,
      food_id: food.food_id,
      portion_g: Math.min(
        PORTION_MAX_G,
        Math.max(PORTION_MIN_G, firstPortion),
      ),
      kcal_per_100g: food.kcal_per_100g,
      protein_g_per_100g: food.protein_g_per_100g,
      source: "table",
    };
    onChange([...components, newDraft]);
    // Per CONTEXT spec: "Add component" does NOT fire a correction
    // (it's an LLM omission, not a correction of a prior identification).
    setAddingNew(false);
  };

  return (
    <div className="flex flex-col gap-3">
      {components.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No components yet. Add one below.
        </p>
      )}
      {components.map((c, idx) => (
        <div key={`${c.food_id ?? "free"}-${idx}`} className="flex flex-col gap-2">
          <ComponentChip
            component={c}
            onChange={(next) => replaceComponent(idx, next)}
            onRemove={() => removeComponent(idx)}
          />
          <div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setEditingIdx(idx === editingIdx ? null : idx)}
              className="h-7 px-2 text-xs"
            >
              <PencilIcon className="size-3 mr-1" />
              {editingIdx === idx ? "Cancel change" : "Change dish"}
            </Button>
            {editingIdx === idx && (
              <div className="mt-1">
                <FoodSearch onSelect={(food) => swapDish(idx, food)} />
              </div>
            )}
          </div>
        </div>
      ))}
      <div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setAddingNew((v) => !v)}
          className="h-8"
          disabled={components.length >= 10}
        >
          <PlusIcon className="size-3 mr-1" />
          {addingNew ? "Cancel" : "Add component"}
        </Button>
        {addingNew && (
          <div className="mt-2">
            <FoodSearch onSelect={onAddNewFood} />
          </div>
        )}
      </div>
    </div>
  );
}
