"use client";

// ProfileForm — Phase 2 Plan 02 (P2-D.1).
//
// Reuses RhfInput / RhfSelect / RhfRadioGroup from P2-B.3. Live preview card
// uses frontend/src/lib/tdee.ts. PATCH /api/profile on save; the response
// carries the recomputed server-side target which we render after success.
//
// Per D-EDIT-REUSES-COMPONENTS: same primitives as onboarding; single form,
// no step gating.

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RhfInput } from "@/components/forms/rhf-input";
import { RhfSelect } from "@/components/forms/rhf-select";
import { RhfRadioGroup } from "@/components/forms/rhf-radio-group";
import { dailyKcalTarget, dailyProteinGTarget } from "@/lib/tdee";
import {
  profileUpdateSchema,
  type ProfileResponse,
  type ProfileUpdate,
} from "@/lib/zod-schemas";

const ACTIVITY_OPTIONS = [
  { value: "sedentary", label: "Sedentary" },
  { value: "lightly_active", label: "Lightly active" },
  { value: "moderately_active", label: "Moderately active" },
  { value: "very_active", label: "Very active" },
  { value: "extra_active", label: "Extra active" },
];

const TIMEZONE_OPTIONS = [
  { value: "Africa/Accra", label: "Africa/Accra (GMT)" },
  { value: "Europe/London", label: "Europe/London (BST/GMT)" },
  { value: "America/New_York", label: "America/New York (ET)" },
  { value: "America/Los_Angeles", label: "America/Los Angeles (PT)" },
  { value: "Europe/Paris", label: "Europe/Paris (CET)" },
];

interface ProfileFormProps {
  initial: ProfileResponse;
}

export function ProfileForm({ initial }: ProfileFormProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<ProfileUpdate>({
    resolver: zodResolver(profileUpdateSchema),
    mode: "onBlur",
    defaultValues: {
      name: initial.name,
      sex: initial.sex,
      height_cm: initial.height_cm,
      weight_kg: initial.weight_kg,
      age: initial.age,
      timezone: initial.timezone,
      locale: initial.locale,
      activity_level: initial.activity_level,
      primary_goal: initial.primary_goal,
    },
  });

  const watched = useWatch({
    control: form.control,
    name: ["sex", "weight_kg", "height_cm", "age", "activity_level", "primary_goal"],
  });
  const [sex, weight_kg, height_cm, age, activity_level, primary_goal] = watched;

  let previewKcal: number | null = null;
  let floorHit = false;
  let previewProtein: number | null = null;
  if (
    (sex === "male" || sex === "female") &&
    typeof weight_kg === "number" &&
    typeof height_cm === "number" &&
    typeof age === "number" &&
    activity_level &&
    primary_goal
  ) {
    try {
      const r = dailyKcalTarget(sex, weight_kg, height_cm, age, activity_level, primary_goal);
      previewKcal = r.kcal_target;
      floorHit = r.floor_hit;
      previewProtein = dailyProteinGTarget(weight_kg, primary_goal);
    } catch {
      previewKcal = null;
    }
  }

  const onSubmit = form.handleSubmit(async (values) => {
    setServerError(null);
    setSubmitting(true);
    try {
      // Only send dirty fields so PATCH stays minimal (and we don't trip
      // extra=forbid by sending unchanged values that the server would
      // accept anyway — keeping the wire payload small is also nice).
      const dirtyKeys = Object.keys(form.formState.dirtyFields) as (keyof ProfileUpdate)[];
      const dirtyValues: Partial<ProfileUpdate> = {};
      for (const k of dirtyKeys) {
        // @ts-expect-error — index signature on a discriminated record
        dirtyValues[k] = values[k];
      }
      // No dirty values? Just show a success toast without an API call.
      if (Object.keys(dirtyValues).length === 0) {
        toast.success("No changes to save");
        setSubmitting(false);
        return;
      }
      const res = await fetch("/api/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dirtyValues),
      });
      if (res.status === 200) {
        toast.success("Profile saved");
        router.refresh();
        setSubmitting(false);
        return;
      }
      const body = await res.json().catch(() => ({} as Record<string, unknown>));
      setServerError(
        typeof body.error === "string"
          ? `${body.error}${body.details ? `: ${JSON.stringify(body.details)}` : ""}`
          : `Request failed (${res.status})`,
      );
    } catch (e) {
      setServerError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <RhfInput control={form.control} name="name" label="Your name" />
      <RhfRadioGroup
        control={form.control}
        name="sex"
        label="Sex"
        options={[
          { value: "male", label: "Male" },
          { value: "female", label: "Female" },
        ]}
      />
      <RhfInput
        control={form.control}
        name="age"
        label="Age"
        type="number"
        coerceNumber
        suffix="years"
      />
      <RhfRadioGroup
        control={form.control}
        name="locale"
        label="Locale"
        options={[
          { value: "ghana", label: "Ghana" },
          { value: "diaspora", label: "Diaspora" },
        ]}
      />
      <RhfInput
        control={form.control}
        name="height_cm"
        label="Height"
        type="number"
        suffix="cm"
        coerceNumber
      />
      <RhfInput
        control={form.control}
        name="weight_kg"
        label="Weight"
        type="number"
        step="0.1"
        suffix="kg"
        coerceNumber
      />
      <RhfSelect
        control={form.control}
        name="activity_level"
        label="Activity level"
        options={ACTIVITY_OPTIONS}
      />
      <RhfRadioGroup
        control={form.control}
        name="primary_goal"
        label="Primary goal"
        options={[
          { value: "weight_loss", label: "Weight loss" },
          { value: "muscle_gain", label: "Muscle gain" },
        ]}
      />
      <RhfSelect
        control={form.control}
        name="timezone"
        label="Timezone"
        options={TIMEZONE_OPTIONS}
      />

      {previewKcal !== null ? (
        <Card className="bg-muted/40">
          <CardHeader>
            <CardTitle className="text-sm">Updated daily target preview</CardTitle>
            <CardDescription>
              Server recomputes on save; this preview matches.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-1">
            <p className="text-xl font-semibold">
              {previewKcal.toLocaleString()} kcal/day
            </p>
            {previewProtein !== null ? (
              <p className="text-sm text-muted-foreground">
                + {previewProtein} g protein/day
              </p>
            ) : null}
            {floorHit ? (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                Floor reached — consult a clinician before pursuing larger
                deficits.
              </p>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {serverError ? (
        <p className="text-sm text-destructive" role="alert">
          {serverError}
        </p>
      ) : null}

      <div className="flex justify-end gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
          disabled={submitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
