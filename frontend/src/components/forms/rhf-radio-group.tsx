"use client";

// RHF-bound shadcn RadioGroup wrapper — Phase 2 Plan 02 (P2-B.3).
//
// Used for sex / locale / primary_goal pickers in onboarding + profile.
// Backed by @base-ui/react RadioGroup which exposes `value` + `onValueChange`
// like Radix.

import { Controller, type Control, type FieldPath, type FieldValues } from "react-hook-form";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export interface RadioOption {
  value: string;
  label: string;
}

interface RhfRadioGroupProps<TFieldValues extends FieldValues> {
  control: Control<TFieldValues>;
  name: FieldPath<TFieldValues>;
  label: string;
  options: RadioOption[];
  className?: string;
}

export function RhfRadioGroup<TFieldValues extends FieldValues>({
  control,
  name,
  label,
  options,
  className,
}: RhfRadioGroupProps<TFieldValues>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <div className={cn("flex flex-col gap-2", className)}>
          <span className="text-sm font-medium leading-none">{label}</span>
          <RadioGroup
            value={field.value ?? ""}
            onValueChange={(v) => field.onChange(v)}
            aria-invalid={fieldState.invalid || undefined}
          >
            {options.map((opt) => (
              <div key={opt.value} className="flex items-center gap-2">
                <RadioGroupItem id={`${name}-${opt.value}`} value={opt.value} />
                <Label htmlFor={`${name}-${opt.value}`} className="font-normal">
                  {opt.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
          {fieldState.error?.message ? (
            <span className="text-xs text-destructive" role="alert">
              {fieldState.error.message}
            </span>
          ) : null}
        </div>
      )}
    />
  );
}
