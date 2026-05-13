// Zod schemas for FitGH — Phase 2 Plan 02 (P2-B.2).
//
// Manual mirror of the Pydantic models in `backend/app/models/profile.py` +
// `backend/app/models/weight_log.py`, with the JSON Schemas in
// `shared/schemas/profile.schema.json` + `weight-log.schema.json` as the
// canonical source of truth (D-SHARED-SCHEMA-MANUAL-MIRROR). We accept the
// drift risk of two hand-maintained schemas in v1 rather than introduce
// codegen — defer codegen until a third stack joins (e.g. a native client).
//
// Constraint sync table — these MUST match Pydantic exactly:
//   name              str           1..80
//   sex               enum          "male" | "female"
//   height_cm         int           100..230
//   weight_kg         float         30..300
//   age               int           13..100
//   timezone          str           min_length 1 (IANA, e.g. "Africa/Accra")
//   locale            enum          "ghana" | "diaspora"
//   activity_level    enum          5 values (see ACTIVITY_LEVELS)
//   primary_goal      enum          "weight_loss" | "muscle_gain"
//   privacy_consent   bool          must be true on create
//   kg (weight_log)   float         20..400
//
// If you change any range/enum here, change Pydantic too — and re-run
// `Profile.model_json_schema()` to regenerate the shared JSON Schema.

import { z } from "zod";

export const SEXES = ["male", "female"] as const;
export const LOCALES = ["ghana", "diaspora"] as const;
export const ACTIVITY_LEVELS = [
  "sedentary",
  "lightly_active",
  "moderately_active",
  "very_active",
  "extra_active",
] as const;
export const PRIMARY_GOALS = ["weight_loss", "muscle_gain"] as const;

export const sexSchema = z.enum(SEXES);
export const localeSchema = z.enum(LOCALES);
export const activityLevelSchema = z.enum(ACTIVITY_LEVELS);
export const primaryGoalSchema = z.enum(PRIMARY_GOALS);

// ProfileCreate — POST /api/profile body. Mirrors Pydantic ProfileCreate
// with the privacy_consent gate (T-02-08); server stamps clerk_id,
// daily_kcal_target, daily_protein_g_target, floor_hit, privacy_consent_at,
// created_at, updated_at.
export const profileCreateSchema = z.object({
  name: z.string().min(1, "Name is required").max(80, "Max 80 characters"),
  sex: sexSchema,
  height_cm: z
    .number()
    .int("Height must be a whole number of cm")
    .min(100, "Minimum 100 cm")
    .max(230, "Maximum 230 cm"),
  weight_kg: z
    .number()
    .min(30, "Minimum 30 kg")
    .max(300, "Maximum 300 kg"),
  age: z
    .number()
    .int("Age must be a whole number")
    .min(13, "Minimum age 13")
    .max(100, "Maximum age 100"),
  timezone: z.string().min(1, "Timezone is required"),
  locale: localeSchema,
  activity_level: activityLevelSchema,
  primary_goal: primaryGoalSchema,
  privacy_consent: z.literal(true, {
    errorMap: () => ({
      message:
        "You must consent to the data-processor disclosure to finish onboarding",
    }),
  }),
});
export type ProfileCreate = z.infer<typeof profileCreateSchema>;

// ProfileUpdate — PATCH /api/profile body. All-optional, but the backend
// enforces extra="forbid" so unknown fields 422 there too.
export const profileUpdateSchema = z.object({
  name: z.string().min(1).max(80).optional(),
  sex: sexSchema.optional(),
  height_cm: z.number().int().min(100).max(230).optional(),
  weight_kg: z.number().min(30).max(300).optional(),
  age: z.number().int().min(13).max(100).optional(),
  timezone: z.string().min(1).optional(),
  locale: localeSchema.optional(),
  activity_level: activityLevelSchema.optional(),
  primary_goal: primaryGoalSchema.optional(),
});
export type ProfileUpdate = z.infer<typeof profileUpdateSchema>;

// WeightLog POST body.
export const weightLogSchema = z.object({
  kg: z.number().min(20, "Minimum 20 kg").max(400, "Maximum 400 kg"),
});
export type WeightLogCreateInput = z.infer<typeof weightLogSchema>;

// Full Profile response shape (what GET /api/profile returns). Useful for
// typing server-component fetches and the dashboard cards.
export interface ProfileResponse {
  clerk_id: string;
  name: string;
  sex: (typeof SEXES)[number];
  height_cm: number;
  weight_kg: number;
  age: number;
  timezone: string;
  locale: (typeof LOCALES)[number];
  activity_level: (typeof ACTIVITY_LEVELS)[number];
  primary_goal: (typeof PRIMARY_GOALS)[number];
  daily_kcal_target: number;
  daily_protein_g_target: number | null;
  floor_hit: boolean;
  privacy_consent_at: string;
  created_at: string;
  updated_at: string;
}

export interface WeightLogResponse {
  user_id: string;
  kg: number;
  logged_at: string;
}
