"use client";

// RHF-bound shadcn Select wrapper — Phase 2 Plan 02 (P2-B.3).
//
// Backed by @base-ui/react's Select primitive (shadcn re-exports from
// @/components/ui/select). Uses controlled `value` + `onValueChange` —
// base-ui mirrors the Radix pattern.

import { Controller, type Control, type FieldPath, type FieldValues } from "react-hook-form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: string;
}

interface RhfSelectProps<TFieldValues extends FieldValues> {
  control: Control<TFieldValues>;
  name: FieldPath<TFieldValues>;
  label: string;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
}

export function RhfSelect<TFieldValues extends FieldValues>({
  control,
  name,
  label,
  options,
  placeholder = "Select an option",
  className,
}: RhfSelectProps<TFieldValues>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <div className={cn("flex flex-col gap-1.5", className)}>
          <Label htmlFor={name}>{label}</Label>
          <Select
            value={field.value ?? ""}
            onValueChange={(v) => field.onChange(v)}
          >
            <SelectTrigger
              id={name}
              className="w-full"
              aria-invalid={fieldState.invalid || undefined}
            >
              <SelectValue placeholder={placeholder} />
            </SelectTrigger>
            <SelectContent>
              {options.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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
