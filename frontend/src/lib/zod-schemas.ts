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

// ===========================================================================
// Phase 3 — Manual Meal Log + Ghana Table (P3-C.1)
// ===========================================================================
//
// Manual mirror of the Pydantic models in `backend/app/models/ghana_food.py` +
// `backend/app/models/meal.py`, with the JSON Schemas in
// `shared/schemas/ghana-food.schema.json` + `meal.schema.json` as the
// canonical source of truth.
//
// Constraint sync table — these MUST match Pydantic exactly:
//   food_id           pattern       ^gh-[a-z0-9-]+$
//   name              str           1..80
//   alt_names         list[str]     0..10 entries
//   kcal_per_100g     float         0..900
//   protein/fat/carb  float         0..100 g/100g
//   portion_defaults  list          1..6 entries (label 1..40, grams 1..2000)
//   category          enum          staple | soup_stew | protein | side_snack
//   source            enum          wafct | wafct_composite | usda
//   source_confidence enum          high | medium | low
//   portion_g (cmp)   int           10..800
//   kcal_point        int           0..5000
//   components/meal   list[cmp]     1..10 entries
//   logged_at         datetime      validator: backdate ≤ 7 days, future ≤ 5 min
//
// FE-side preview math uses Math.round (matches Python banker's rounding for
// the typical input range).

export const PORTION_MIN_G = 10;
export const PORTION_MAX_G = 800;
export const PORTION_STEP_G = 10;
export const BACKDATE_MAX_DAYS = 7;

export const CATEGORIES = [
  "staple",
  "soup_stew",
  "protein",
  "side_snack",
] as const;
export const FOOD_SOURCES = ["wafct", "wafct_composite", "usda"] as const;
export const FOOD_SOURCE_CONFIDENCES = ["high", "medium", "low"] as const;
export const MEAL_SOURCES = ["manual", "ai_vision"] as const;
export const COMPONENT_SOURCES = [
  "table",
  "llm_then_table_rematch",
  "user_corrected",
] as const;

export const categorySchema = z.enum(CATEGORIES);
export const foodSourceSchema = z.enum(FOOD_SOURCES);
export const foodSourceConfidenceSchema = z.enum(FOOD_SOURCE_CONFIDENCES);
export const mealSourceSchema = z.enum(MEAL_SOURCES);
export const componentSourceSchema = z.enum(COMPONENT_SOURCES);

export const portionDefaultSchema = z.object({
  label: z.string().min(1).max(40),
  grams: z.number().int().min(1).max(2000),
});
export type PortionDefault = z.infer<typeof portionDefaultSchema>;

export const ghanaFoodSchema = z.object({
  food_id: z.string().regex(/^gh-[a-z0-9-]+$/),
  name: z.string().min(1).max(80),
  alt_names: z.array(z.string()).max(10),
  kcal_per_100g: z.number().min(0).max(900),
  protein_g_per_100g: z.number().min(0).max(100),
  fat_g_per_100g: z.number().min(0).max(100),
  carbs_g_per_100g: z.number().min(0).max(100),
  portion_defaults: z.array(portionDefaultSchema).min(1).max(6),
  category: categorySchema,
  source: foodSourceSchema,
  source_confidence: foodSourceConfidenceSchema,
});
export type GhanaFoodResponse = z.infer<typeof ghanaFoodSchema>;

// ComponentCreate is a discriminated-ish union: either {food_id, portion_g}
// or {name, portion_g, kcal_point}. The Pydantic side uses a model_validator
// for exactly-one-of; Zod's z.union runs both branches.
//
// Phase 4 — both branches gain OPTIONAL vision-only fields (kcal_low,
// kcal_high, confidence, source). When omitted (manual log path), the
// shape matches Phase 3 verbatim. Backend ignores them when meal-level
// `source != "ai_vision"`.
export const componentCreateMatchedSchema = z.object({
  food_id: z.string().regex(/^gh-[a-z0-9-]+$/),
  portion_g: z.number().int().min(PORTION_MIN_G).max(PORTION_MAX_G),
  kcal_low: z.number().int().min(0).max(5000).optional(),
  kcal_high: z.number().int().min(0).max(5000).optional(),
  confidence: z.number().min(0).max(1).optional(),
  source: componentSourceSchema.optional(),
});
export const componentCreateFreeTextSchema = z.object({
  name: z.string().min(1).max(80),
  portion_g: z.number().int().min(PORTION_MIN_G).max(PORTION_MAX_G),
  kcal_point: z.number().int().min(0).max(5000),
  kcal_low: z.number().int().min(0).max(5000).optional(),
  kcal_high: z.number().int().min(0).max(5000).optional(),
  confidence: z.number().min(0).max(1).optional(),
  source: componentSourceSchema.optional(),
});
export const componentCreateSchema = z.union([
  componentCreateMatchedSchema,
  componentCreateFreeTextSchema,
]);
export type ComponentCreateInput = z.infer<typeof componentCreateSchema>;

// Phase 4 — AiMetadata sub-doc (carried on the meal-level POST body
// when source="ai_vision"). Mirrors backend AiMetadata Pydantic with
// extra="ignore" — unknown fields on the wire are silently dropped
// server-side (T-04-05).
export const aiMetadataSchema = z.object({
  model: z.string().min(1).max(80),
  prompt_hash: z.string().min(16).max(128),
  image_dims: z.object({ w: z.number().int(), h: z.number().int() }),
  latency_ms: z.number().int().min(0),
  cost_usd: z.number().min(0),
});
export type AiMetadata = z.infer<typeof aiMetadataSchema>;

export const mealCreateSchema = z.object({
  logged_at: z.string().datetime().optional(),
  components: z.array(componentCreateSchema).min(1).max(10),
  source: mealSourceSchema.optional(),  // default "manual" server-side
  ai_metadata: aiMetadataSchema.optional(),
});
export type MealCreateInput = z.infer<typeof mealCreateSchema>;

export const mealUpdateSchema = z.object({
  logged_at: z.string().datetime().optional(),
  components: z.array(componentCreateSchema).min(1).max(10).optional(),
});
export type MealUpdateInput = z.infer<typeof mealUpdateSchema>;

// Response types — what GET /api/meals + POST /api/meals serve.
export interface ComponentResponse {
  name: string;
  matched_food_id: string | null;
  portion_g: number;
  kcal_low: number | null;
  kcal_high: number | null;
  kcal_point: number;
  protein_g_point: number;
  confidence: number | null;
  source: (typeof COMPONENT_SOURCES)[number];
}

export interface MealAiMetadata {
  model?: string;
  prompt_hash?: string;
  image_dims?: [number, number];
  latency_ms?: number;
  cost_usd?: number;
}

export interface MealResponse {
  id: string;
  user_id: string;
  logged_at: string;
  source: (typeof MEAL_SOURCES)[number];
  components: ComponentResponse[];
  total_kcal: number;
  total_protein_g: number;
  ai_metadata: MealAiMetadata | null;
  created_at: string;
  updated_at: string;
}

export interface DayMealsResponse {
  date: string;
  total_kcal: number;
  total_protein_g: number;
  meals: MealResponse[];
}

export interface MealsHistoryResponse {
  days: DayMealsResponse[];
}

// ===========================================================================
// Phase 4 — Image → Kcal Core Loop (P4-C.1)
// ===========================================================================
//
// Manual mirror of `shared/schemas/vision-response.schema.json` and the
// extended meal.schema.json. The scan-sheet (P4-D.1) calls
// fetch("/api/meals/scan") and zod-parses the response against
// `visionScanResponseSchema`.

// One component as it comes back from /api/meals/scan — post-table-rematch,
// so kcal_point is the table value (matched path) or LLM midpoint (free-text).
export const visionComponentSchema = z.object({
  name: z.string().min(1).max(80),
  matched_food_id: z.string().regex(/^gh-[a-z0-9-]+$/).nullable(),
  portion_g: z.number().int().min(PORTION_MIN_G).max(PORTION_MAX_G),
  kcal_low: z.number().int().min(0).nullable(),
  kcal_high: z.number().int().min(0).nullable(),
  kcal_point: z.number().int().min(0),
  protein_g_point: z.number().int().min(0),
  confidence: z.number().min(0).max(1).nullable(),
  source: componentSourceSchema,
});
export type VisionComponent = z.infer<typeof visionComponentSchema>;

export const visionScanResponseSchema = z.object({
  components: z.array(visionComponentSchema).min(1).max(10),
  ai_metadata: aiMetadataSchema,
  vision_total_kcal_low: z.number().int().min(0),
  vision_total_kcal_high: z.number().int().min(0),
  user_daily_count: z.number().int().min(0),
  user_daily_limit: z.number().int().min(1),
});
export type VisionScanResponse = z.infer<typeof visionScanResponseSchema>;

// POST /api/corrections body shape.
export const userCorrectionInputSchema = z.object({
  original_name: z.string().min(1).max(80),
  corrected_name: z.string().max(80).nullable(),
  original_portion_g: z.number().int().min(0).max(2000),
  corrected_portion_g: z.number().int().min(0).max(2000),
  original_food_id: z.string().regex(/^gh-[a-z0-9-]+$/).nullable(),
  corrected_food_id: z.string().regex(/^gh-[a-z0-9-]+$/).nullable(),
});
export type UserCorrectionInput = z.infer<typeof userCorrectionInputSchema>;

// GET /api/scan-budget response — fuels the ServicePausedBanner.
export interface ScanBudgetResponse {
  spend_usd: number;
  cap_usd: number;
  paused: boolean;
  date: string;
}
