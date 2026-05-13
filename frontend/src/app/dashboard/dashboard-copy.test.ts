// Vitest unit tests for goal-aware dashboard copy.
// Phase 5 Plan 05 (P5-D.1).

import { describe, expect, it } from "vitest";
import { dashboardCopy } from "@/lib/dashboard-copy";

describe("dashboardCopy.weight_loss", () => {
  const copy = dashboardCopy.weight_loss;

  it("kcalFraming under target returns 'X kcal under target' string", () => {
    expect(copy.kcalFraming(1500, 2000)).toBe("You're 500 kcal under target");
  });

  it("kcalFraming over target returns 'X kcal over' string", () => {
    expect(copy.kcalFraming(2200, 2000)).toBe("You're 200 kcal over target");
  });

  it("kcalFraming exactly at target returns 'on target'", () => {
    expect(copy.kcalFraming(2000, 2000)).toBe("You're right on target");
  });

  it("ignores protein argument", () => {
    // protein argument should not change weight_loss copy.
    expect(copy.kcalFraming(1500, 2000, 50)).toBe(
      "You're 500 kcal under target",
    );
  });

  it("targetPillLabel mentions loss target", () => {
    expect(copy.targetPillLabel).toMatch(/loss/i);
  });

  it("secondaryCta is Log a meal", () => {
    expect(copy.secondaryCta.label).toBe("Log a meal");
    expect(copy.secondaryCta.href).toBe("/dashboard");
  });

  it("exposes all four required keys", () => {
    expect(copy.targetPillLabel).toBeTruthy();
    expect(copy.secondaryCta).toBeTruthy();
    expect(copy.weeklyChartTitle).toBeTruthy();
    expect(copy.weightChartTitle).toBeTruthy();
  });
});

describe("dashboardCopy.muscle_gain", () => {
  const copy = dashboardCopy.muscle_gain;

  it("kcalFraming with protein remaining emphasises protein", () => {
    expect(copy.kcalFraming(2000, 2600, 50)).toBe("50 g protein remaining");
  });

  it("kcalFraming with proteinRemainingG=0 falls back to kcal language", () => {
    expect(copy.kcalFraming(1500, 2600, 0)).toBe(
      "You're 1100 kcal under target",
    );
  });

  it("kcalFraming with no protein argument falls back to kcal language", () => {
    expect(copy.kcalFraming(1500, 2600)).toBe(
      "You're 1100 kcal under target",
    );
  });

  it("targetPillLabel mentions gain target", () => {
    expect(copy.targetPillLabel).toMatch(/gain/i);
  });

  it("exposes all four required keys", () => {
    expect(copy.targetPillLabel).toBeTruthy();
    expect(copy.secondaryCta).toBeTruthy();
    expect(copy.weeklyChartTitle).toBeTruthy();
    expect(copy.weightChartTitle).toBeTruthy();
  });
});

describe("dashboardCopy cross-goal differences", () => {
  it("weight_loss and muscle_gain return distinct pill labels", () => {
    expect(dashboardCopy.weight_loss.targetPillLabel).not.toBe(
      dashboardCopy.muscle_gain.targetPillLabel,
    );
  });

  it("kcalFraming differs when protein remaining is supplied for muscle_gain", () => {
    const wl = dashboardCopy.weight_loss.kcalFraming(1500, 2000, 30);
    const mg = dashboardCopy.muscle_gain.kcalFraming(1500, 2000, 30);
    expect(wl).not.toBe(mg);
  });
});
