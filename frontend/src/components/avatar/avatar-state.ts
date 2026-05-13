// Pure helpers for resolving the avatar state key from profile + recent
// weight logs. No React, no DOM — fully unit-testable.
//
// Phase 5 Plan 05 (P5-B.2). State machine described in
// `frontend/src/components/avatar/README.md`.

import type { PrimaryGoal, WeightLogResponse } from "@/lib/zod-schemas";

export type BmiBand =
  | "slim"
  | "healthy-lean"
  | "healthy-firm"
  | "heavier"
  | "much-heavier";

export type GoalDirection = "toward" | "steady" | "away";

export type SexShort = "m" | "f";

// BMI band cutoffs — Mifflin-St Jeor / WHO convention. Boundaries are
// INCLUSIVE on the lower edge:
//   18.5 -> healthy-lean (not slim)
//   25.0 -> healthy-firm (not healthy-lean)
//   28.0 -> heavier
//   32.0 -> much-heavier
export const BMI_CUTOFFS = {
  slim: 18.5,
  healthyLean: 25.0,
  healthyFirm: 28.0,
  heavier: 32.0,
} as const;

// Slope threshold for "trending" — anything within +/- 0.1 kg/week is
// considered "steady".
const SLOPE_FLAT_KG_PER_WEEK = 0.1;

export function bmiBand(weight_kg: number, height_cm: number): BmiBand {
  if (height_cm <= 0) return "healthy-lean"; // defensive
  const heightM = height_cm / 100;
  const bmi = weight_kg / (heightM * heightM);
  if (bmi < BMI_CUTOFFS.slim) return "slim";
  if (bmi < BMI_CUTOFFS.healthyLean) return "healthy-lean";
  if (bmi < BMI_CUTOFFS.healthyFirm) return "healthy-firm";
  if (bmi < BMI_CUTOFFS.heavier) return "heavier";
  return "much-heavier";
}

/** Compute the 7-day (or whatever window the caller passed in) weight
 *  slope as kg/week. `entries` MUST be newest-first (GET /api/weights
 *  contract from Phase 2). Empty / single-entry inputs return 0. */
export function weightSlopeKgPerWeek(
  entries: ReadonlyArray<WeightLogResponse>,
): number {
  if (entries.length < 2) return 0;
  const newest = entries[0];
  const oldest = entries[entries.length - 1];
  const ms = new Date(newest.logged_at).getTime() - new Date(oldest.logged_at).getTime();
  const weeks = Math.max(ms / (7 * 24 * 60 * 60 * 1000), 1 / 7); // floor at 1 day
  return (newest.kg - oldest.kg) / weeks;
}

export function goalDirection(
  primary_goal: PrimaryGoal,
  entries: ReadonlyArray<WeightLogResponse>,
): GoalDirection {
  if (entries.length < 2) return "steady";
  const slope = weightSlopeKgPerWeek(entries);
  if (Math.abs(slope) <= SLOPE_FLAT_KG_PER_WEEK) return "steady";
  if (primary_goal === "weight_loss") {
    return slope < 0 ? "toward" : "away";
  }
  // muscle_gain
  return slope > 0 ? "toward" : "away";
}

export function sexShort(sex: "male" | "female"): SexShort {
  return sex === "female" ? "f" : "m";
}

// Sprite ships 20 explicit states (sex x bmi x dir). The full 5x2x3 = 30
// grid is theoretical. When the resolved state is not present in the
// sprite, fall back to the nearest available one (drop `away` first, then
// fall to `steady`, then to the nearest BMI band).
//
// Keep this set in sync with the actual `<g id="state-...">` blocks in
// `public/avatar-sprite.svg`.
export const SHIPPED_STATES = new Set([
  "m-slim-toward",
  "m-slim-steady",
  "m-slim-away",
  "m-healthy-lean-toward",
  "m-healthy-lean-steady",
  "m-healthy-lean-away",
  "m-healthy-firm-toward",
  "m-healthy-firm-steady",
  "m-heavier-toward",
  "m-heavier-steady",
  "m-much-heavier-toward",
  "f-slim-toward",
  "f-slim-steady",
  "f-slim-away",
  "f-healthy-lean-toward",
  "f-healthy-lean-steady",
  "f-healthy-lean-away",
  "f-healthy-firm-toward",
  "f-healthy-firm-steady",
  "f-heavier-toward",
]);

interface AvatarProfileInput {
  sex: "male" | "female";
  weight_kg: number;
  height_cm: number;
  primary_goal: PrimaryGoal;
}

export function avatarStateKey(
  profile: AvatarProfileInput,
  recentWeights: ReadonlyArray<WeightLogResponse>,
): string {
  const sx = sexShort(profile.sex);
  const band = bmiBand(profile.weight_kg, profile.height_cm);
  const dir = goalDirection(profile.primary_goal, recentWeights);
  const exact = `${sx}-${band}-${dir}`;
  if (SHIPPED_STATES.has(exact)) return exact;
  // Fallback chain: try same band but steady direction.
  const steady = `${sx}-${band}-steady`;
  if (SHIPPED_STATES.has(steady)) return steady;
  // Fall further to toward (most-shipped direction).
  const toward = `${sx}-${band}-toward`;
  if (SHIPPED_STATES.has(toward)) return toward;
  // Last resort — known to ship across every BMI band.
  return `${sx}-healthy-lean-steady`;
}
