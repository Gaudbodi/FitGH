// TDEE preview math — Phase 2 Plan 02 (P2-B.2).
//
// EXACT mirror of `backend/app/lib/tdee.py`. The displayed kcal target on
// /dashboard always comes from the server response; this module is only used
// for the live preview during onboarding screen 2 and the /profile edit form.
//
// If FE preview diverges from BE persisted value, that is a sync bug — the
// P2-F.1 end-to-end smoke explicitly compares the two numbers.
//
// Constants MUST stay byte-identical with the Python file:
//   ACTIVITY_FACTORS, KCAL_FLOORS, PROTEIN_FACTOR_G_PER_KG.

export type Sex = "male" | "female";
export type ActivityLevel =
  | "sedentary"
  | "lightly_active"
  | "moderately_active"
  | "very_active"
  | "extra_active";
export type PrimaryGoal = "weight_loss" | "muscle_gain";

export const ACTIVITY_FACTORS: Record<ActivityLevel, number> = {
  sedentary: 1.2,
  lightly_active: 1.375,
  moderately_active: 1.55,
  very_active: 1.725,
  extra_active: 1.9,
};

export const KCAL_FLOORS: Record<Sex, number> = {
  male: 1500,
  female: 1200,
};

export const PROTEIN_FACTOR_G_PER_KG = 1.6;

// Half-up rounding to mirror Python's Decimal(...).quantize(ROUND_HALF_UP).
// JS's Math.round rounds half-to-even for ties at .5 in some implementations
// (engine-dependent), so we implement explicit half-up.
function roundHalfUp(value: number): number {
  return Math.floor(value + 0.5);
}

export function bmrMifflinStJeor(
  sex: Sex,
  weightKg: number,
  heightCm: number,
  age: number,
): number {
  if (sex === "male") {
    return 10 * weightKg + 6.25 * heightCm - 5 * age + 5;
  }
  if (sex === "female") {
    return 10 * weightKg + 6.25 * heightCm - 5 * age - 161;
  }
  throw new Error(`invalid sex: ${sex}`);
}

export function tdee(bmr: number, activityLevel: ActivityLevel): number {
  const factor = ACTIVITY_FACTORS[activityLevel];
  if (factor === undefined) {
    throw new Error(`invalid activity_level: ${activityLevel}`);
  }
  return bmr * factor;
}

export interface KcalTargetResult {
  kcal_target: number;
  floor_hit: boolean;
}

export function dailyKcalTarget(
  sex: Sex,
  weightKg: number,
  heightCm: number,
  age: number,
  activityLevel: ActivityLevel,
  primaryGoal: PrimaryGoal,
): KcalTargetResult {
  if (sex !== "male" && sex !== "female") {
    throw new Error(`invalid sex: ${sex}`);
  }
  if (primaryGoal !== "weight_loss" && primaryGoal !== "muscle_gain") {
    throw new Error(`invalid primary_goal: ${primaryGoal}`);
  }

  const bmr = bmrMifflinStJeor(sex, weightKg, heightCm, age);
  const tdeeKcal = tdee(bmr, activityLevel);
  const target =
    primaryGoal === "weight_loss" ? tdeeKcal - 500 : tdeeKcal + 250;

  const floor = KCAL_FLOORS[sex];
  if (target < floor) {
    return { kcal_target: floor, floor_hit: true };
  }
  return { kcal_target: roundHalfUp(target), floor_hit: false };
}

export function dailyProteinGTarget(
  weightKg: number,
  primaryGoal: PrimaryGoal,
): number | null {
  if (primaryGoal !== "weight_loss" && primaryGoal !== "muscle_gain") {
    throw new Error(`invalid primary_goal: ${primaryGoal}`);
  }
  if (primaryGoal !== "muscle_gain") {
    return null;
  }
  return roundHalfUp(weightKg * PROTEIN_FACTOR_G_PER_KG);
}
