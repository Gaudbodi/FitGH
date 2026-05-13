// Phase 6 (Workout Library + PWA) — P6-B.1 exercises lib.
//
// Pure helpers + TS types matching the manifest schema emitted by
// scripts/ingest_exercises.py. Server-side loadManifest reads from
// `frontend/public/exercises/manifest.json` at request time; Next 15
// dedupes the call across the same render so calling it from both
// `/workouts` and `/workouts/[id]` is cheap.
//
// CONTEXT decisions: D-STATIC-FIRST (no Flask /exercises route),
// D-FILTER-DEFAULT (DEFAULT_EQUIPMENT_SELECTION = ['none', 'dumbbell']).

import { z } from "zod";

// ---------------------------------------------------------------------------
// Public TS types
// ---------------------------------------------------------------------------

export type EquipmentBucket =
  | "none"
  | "dumbbell"
  | "bands"
  | "pull-up bar"
  | "kettlebells"
  | "barbell";

export type MuscleBucket =
  | "chest"
  | "back"
  | "legs"
  | "shoulders"
  | "arms"
  | "core"
  | "glutes"
  | "full-body";

export interface ExerciseEntry {
  id: string;
  name: string;
  equipment: EquipmentBucket;
  muscles_primary: MuscleBucket[];
  muscles_secondary: MuscleBucket[];
  category: "strength" | "cardio";
  level: "beginner" | "intermediate" | "expert";
  mechanic: "compound" | "isolation" | null;
  instructions: string[];
  poster: string;
  detail: string;
}

export const DEFAULT_EQUIPMENT_SELECTION: EquipmentBucket[] = [
  "none",
  "dumbbell",
];

// ---------------------------------------------------------------------------
// zod schema (T-06-11 mitigation — type guard against manifest tampering)
// ---------------------------------------------------------------------------

const equipmentEnum = z.enum([
  "none",
  "dumbbell",
  "bands",
  "pull-up bar",
  "kettlebells",
  "barbell",
]);

const muscleEnum = z.enum([
  "chest",
  "back",
  "legs",
  "shoulders",
  "arms",
  "core",
  "glutes",
  "full-body",
]);

const exerciseEntrySchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  equipment: equipmentEnum,
  muscles_primary: z.array(muscleEnum),
  muscles_secondary: z.array(muscleEnum),
  category: z.enum(["strength", "cardio"]),
  level: z.enum(["beginner", "intermediate", "expert"]),
  mechanic: z.enum(["compound", "isolation"]).nullable(),
  instructions: z.array(z.string()),
  poster: z.string().startsWith("/exercises/"),
  detail: z.string().startsWith("/exercises/"),
});

export const manifestSchema = z.object({
  meta: z.object({
    source: z.string().url(),
    commit: z.string().min(7),
    license: z.string().min(1),
    generated_at: z.string().min(1),
  }),
  entries: z.array(exerciseEntrySchema),
});

export type Manifest = z.infer<typeof manifestSchema>;

// ---------------------------------------------------------------------------
// Filter selection
// ---------------------------------------------------------------------------

export interface FilterSelection {
  equipment: EquipmentBucket[];
  muscles: MuscleBucket[];
}

/**
 * Filter exercises by equipment + muscle selection.
 *
 * Rules:
 * - Empty `equipment` array → all equipment allowed (no filter on that axis).
 * - Empty `muscles` array → all muscles allowed (no filter on that axis).
 * - Non-empty → entry passes if equipment ∈ selection.equipment AND
 *   (muscles_primary ∩ selection.muscles).length > 0.
 *
 * Pure, no side effects. AND across categories, OR within (matches the
 * natural mental model from CONTEXT.md "specifics").
 */
export function filterExercises(
  entries: ExerciseEntry[],
  selection: FilterSelection,
): ExerciseEntry[] {
  const { equipment, muscles } = selection;
  return entries.filter((e) => {
    if (equipment.length > 0 && !equipment.includes(e.equipment)) {
      return false;
    }
    if (muscles.length > 0) {
      const hit = e.muscles_primary.some((m) => muscles.includes(m));
      if (!hit) return false;
    }
    return true;
  });
}

export function findExerciseById(
  entries: ExerciseEntry[],
  id: string,
): ExerciseEntry | undefined {
  return entries.find((e) => e.id === id);
}

// Note: server-side `loadManifest()` lives in `./exercises.server.ts` so the
// client bundle that imports filter helpers doesn't statically reference
// node:fs/promises. Both modules share types + schema from this file.

// ---------------------------------------------------------------------------
// Display-label helpers (used by FilterBar + ExerciseCard)
// ---------------------------------------------------------------------------

export const EQUIPMENT_LABEL: Record<EquipmentBucket, string> = {
  none: "No equipment",
  dumbbell: "Dumbbells",
  bands: "Resistance bands",
  "pull-up bar": "Pull-up bar",
  kettlebells: "Kettlebells",
  barbell: "Barbell",
};

export const MUSCLE_LABEL: Record<MuscleBucket, string> = {
  chest: "Chest",
  back: "Back",
  legs: "Legs",
  shoulders: "Shoulders",
  arms: "Arms",
  core: "Core",
  glutes: "Glutes",
  "full-body": "Full body",
};
