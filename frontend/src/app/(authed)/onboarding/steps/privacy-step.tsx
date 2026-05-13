"use client";

// Onboarding step 3 — Privacy & finish. Phase 2 Plan 02 (P2-C.1).

import { useEffect } from "react";
import Link from "next/link";
import { Controller, type Control } from "react-hook-form";
import type { UseFormSetValue } from "react-hook-form";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RhfSelect } from "@/components/forms/rhf-select";
import type { ProfileCreate } from "@/lib/zod-schemas";

interface PrivacyStepProps {
  control: Control<ProfileCreate>;
  setValue: UseFormSetValue<ProfileCreate>;
}

const TIMEZONE_OPTIONS = [
  { value: "Africa/Accra", label: "Africa/Accra (GMT)" },
  { value: "Europe/London", label: "Europe/London (BST/GMT)" },
  { value: "America/New_York", label: "America/New York (ET)" },
  { value: "America/Los_Angeles", label: "America/Los Angeles (PT)" },
  { value: "Europe/Paris", label: "Europe/Paris (CET)" },
];

export function PrivacyStep({ control, setValue }: PrivacyStepProps) {
  // Auto-detect timezone on mount; user can override via the Select.
  useEffect(() => {
    try {
      const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (detected) {
        setValue("timezone", detected, { shouldValidate: true });
      }
    } catch {
      // ignore — user picks manually
    }
  }, [setValue]);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Privacy & finish</h2>

      <RhfSelect
        control={control}
        name="timezone"
        label="Timezone"
        options={TIMEZONE_OPTIONS}
        placeholder="We'll auto-detect this"
      />

      <div className="rounded-lg border bg-muted/40 p-4 text-sm">
        <h3 className="text-sm font-semibold">What happens to your data</h3>
        <p className="mt-2 text-muted-foreground">
          When you snap a meal photo later, FitGH sends the image to{" "}
          <strong>Anthropic (Claude Sonnet 4.6)</strong> for kcal estimation
          against a Ghanaian-food calibration table. Your account identity is
          held by <strong>Clerk</strong>, your profile and weight history live
          in <strong>MongoDB Atlas</strong>, and the app runs on{" "}
          <strong>Render</strong>. We do not retain meal images beyond the
          time needed to compute kcal unless you opt into history later.{" "}
          <Link href="/privacy" className="underline">
            Read the full disclosure
          </Link>
          .
        </p>
      </div>

      {/* Phase 7 LEGAL-03 — standard health-claim disclaimer on the
          onboarding consent screen. The same string lives in the global
          footer (root layout) so it's visible from every page. */}
      <p className="rounded-md border border-dashed bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
        FitGH is a fitness tracking tool, not medical advice. Consult a
        qualified clinician for health decisions.
      </p>

      <Controller
        control={control}
        name="privacy_consent"
        render={({ field, fieldState }) => (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-start gap-2">
              <Checkbox
                id="privacy_consent"
                checked={field.value === true}
                onCheckedChange={(checked: boolean) => field.onChange(checked)}
                aria-invalid={fieldState.invalid || undefined}
              />
              <Label
                htmlFor="privacy_consent"
                className="text-sm font-normal leading-snug"
              >
                I understand and consent to sharing meal photos with Anthropic
                when I use the snap-meal feature.
              </Label>
            </div>
            {fieldState.error?.message ? (
              <span className="ml-6 text-xs text-destructive" role="alert">
                {fieldState.error.message}
              </span>
            ) : null}
          </div>
        )}
      />
    </div>
  );
}
