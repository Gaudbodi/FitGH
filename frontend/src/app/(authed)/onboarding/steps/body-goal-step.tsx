"use client";

// Onboarding step 2 — Body & goal. Phase 2 Plan 02 (P2-C.1).
//
// Includes a LIVE preview card showing the computed daily kcal target via
// frontend/src/lib/tdee.ts. The displayed number on /dashboard always comes
// from the server response (P2-C.3); this preview is for instant feedback
// during onboarding.

import type { Control } from "react-hook-form";
import { useWatch } from "react-hook-form";
import { RhfInput } from "@/components/forms/rhf-input";
import { RhfRadioGroup } from "@/components/forms/rhf-radio-group";
import { RhfSelect } from "@/components/forms/rhf-select";
import { dailyKcalTarget, dailyProteinGTarget } from "@/lib/tdee";
import type { ProfileCreate } from "@/lib/zod-schemas";

interface BodyGoalStepProps {
  control: Control<ProfileCreate>;
}

const ACTIVITY_OPTIONS = [
  { value: "sedentary", label: "Sedentary (little or no exercise)" },
  { value: "lightly_active", label: "Lightly active (1-3 days / week)" },
  { value: "moderately_active", label: "Moderately active (3-5 days / week)" },
  { value: "very_active", label: "Very active (6-7 days / week)" },
  { value: "extra_active", label: "Extra active (intense daily training)" },
];

const GOAL_OPTIONS = [
  { value: "weight_loss", label: "Weight loss" },
  { value: "muscle_gain", label: "Muscle gain" },
];

export function BodyGoalStep({ control }: BodyGoalStepProps) {
  // Subscribe to fields needed for the preview. useWatch only re-renders
  // THIS component on change, not the rest of the form.
  const watched = useWatch({
    control,
    name: ["sex", "weight_kg", "height_cm", "age", "activity_level", "primary_goal"],
  });
  const [sex, weight_kg, height_cm, age, activity_level, primary_goal] = watched;

  let previewKcal: number | null = null;
  let floorHit = false;
  let previewProtein: number | null = null;

  if (
    (sex === "male" || sex === "female") &&
    typeof weight_kg === "number" && weight_kg >= 30 && weight_kg <= 300 &&
    typeof height_cm === "number" && height_cm >= 100 && height_cm <= 230 &&
    typeof age === "number" && age >= 13 && age <= 100 &&
    activity_level &&
    primary_goal
  ) {
    try {
      const r = dailyKcalTarget(
        sex,
        weight_kg,
        height_cm,
        age,
        activity_level,
        primary_goal,
      );
      previewKcal = r.kcal_target;
      floorHit = r.floor_hit;
      previewProtein = dailyProteinGTarget(weight_kg, primary_goal);
    } catch {
      previewKcal = null;
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Your body and goal</h2>

      <RhfInput
        control={control}
        name="height_cm"
        label="Height"
        type="number"
        placeholder="175"
        suffix="cm"
        coerceNumber
      />
      <RhfInput
        control={control}
        name="weight_kg"
        label="Weight"
        type="number"
        placeholder="70"
        suffix="kg"
        step="0.1"
        coerceNumber
      />
      <RhfSelect
        control={control}
        name="activity_level"
        label="Activity level"
        options={ACTIVITY_OPTIONS}
      />
      <RhfRadioGroup
        control={control}
        name="primary_goal"
        label="Primary goal"
        options={GOAL_OPTIONS}
      />

      {previewKcal !== null ? (
        <div className="mt-4 rounded-lg border bg-muted/40 p-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Estimated daily target
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {previewKcal.toLocaleString()} kcal/day
          </p>
          {previewProtein !== null ? (
            <p className="mt-0.5 text-sm text-muted-foreground">
              + {previewProtein} g protein (muscle gain target)
            </p>
          ) : null}
          {floorHit ? (
            <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
              FitGH is a fitness tracking tool, not medical advice. Targets
              below {sex === "female" ? 1200 : 1500} kcal/day are clamped;
              consult a clinician before pursuing aggressive deficits.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
