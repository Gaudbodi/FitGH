"use client";

// Onboarding step 1 — Identity. Phase 2 Plan 02 (P2-C.1).

import type { Control } from "react-hook-form";
import { RhfInput } from "@/components/forms/rhf-input";
import { RhfRadioGroup } from "@/components/forms/rhf-radio-group";
import type { ProfileCreate } from "@/lib/zod-schemas";

interface IdentityStepProps {
  control: Control<ProfileCreate>;
}

export function IdentityStep({ control }: IdentityStepProps) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Tell us about you</h2>

      <RhfInput
        control={control}
        name="name"
        label="Your name"
        placeholder="Ama Boateng"
      />

      <RhfRadioGroup
        control={control}
        name="sex"
        label="Sex (used for BMR formula)"
        options={[
          { value: "male", label: "Male" },
          { value: "female", label: "Female" },
        ]}
      />

      <RhfInput
        control={control}
        name="age"
        label="Age"
        type="number"
        placeholder="28"
        coerceNumber
        suffix="years"
      />

      <RhfRadioGroup
        control={control}
        name="locale"
        label="Where are you based?"
        options={[
          { value: "ghana", label: "Ghana" },
          { value: "diaspora", label: "Diaspora (anywhere else)" },
        ]}
      />
    </div>
  );
}
