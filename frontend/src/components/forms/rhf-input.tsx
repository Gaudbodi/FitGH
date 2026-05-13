"use client";

// RHF-bound shadcn Input wrapper — Phase 2 Plan 02 (P2-B.3).
//
// Used by onboarding-flow.tsx and profile-form.tsx for every text/number
// input. Renders label + input + error message + optional unit suffix.

import { Controller, type Control, type FieldPath, type FieldValues } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface RhfInputProps<TFieldValues extends FieldValues> {
  control: Control<TFieldValues>;
  name: FieldPath<TFieldValues>;
  label: string;
  type?: "text" | "number" | "email";
  placeholder?: string;
  suffix?: string;
  step?: string | number;
  className?: string;
  // If true, coerces the value to a number on change (numeric inputs).
  coerceNumber?: boolean;
}

export function RhfInput<TFieldValues extends FieldValues>({
  control,
  name,
  label,
  type = "text",
  placeholder,
  suffix,
  step,
  className,
  coerceNumber = false,
}: RhfInputProps<TFieldValues>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <div className={cn("flex flex-col gap-1.5", className)}>
          <Label htmlFor={name}>{label}</Label>
          <div className="relative">
            <Input
              id={name}
              type={type}
              placeholder={placeholder}
              step={step}
              aria-invalid={fieldState.invalid || undefined}
              {...field}
              value={field.value ?? ""}
              onChange={(e) => {
                const raw = e.target.value;
                if (coerceNumber) {
                  if (raw === "") {
                    field.onChange(undefined);
                  } else {
                    const num = Number(raw);
                    field.onChange(Number.isNaN(num) ? raw : num);
                  }
                } else {
                  field.onChange(raw);
                }
              }}
              className={cn(suffix ? "pr-10" : undefined)}
            />
            {suffix ? (
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                {suffix}
              </span>
            ) : null}
          </div>
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
