// Goal-aware dashboard copy — Phase 5 Plan 05 (P5-D.1).
//
// Single source of truth for the strings the dashboard shows that change
// based on the user's `primary_goal`. Centralised here so localisation is a
// matter of swapping this file, not hunting through components.

import type { PrimaryGoal } from "@/lib/zod-schemas";

export interface DashboardCopy {
  /** Headline string sitting next to the kcal ring. The protein argument is
   *  only consulted for muscle_gain — passing it for weight_loss is a no-op
   *  (defensive). When muscle_gain is given and proteinRemainingG > 0 the
   *  copy emphasises protein. */
  kcalFraming: (
    consumed: number,
    target: number,
    proteinRemainingG?: number,
  ) => string;
  /** Small chip near the avatar/streak — the weekly goal pace target. */
  targetPillLabel: string;
  /** Secondary CTA below the ring. */
  secondaryCta: { label: string; href: string };
  /** Chart titles. */
  weeklyChartTitle: string;
  weightChartTitle: string;
}

export const dashboardCopy: Record<PrimaryGoal, DashboardCopy> = {
  weight_loss: {
    kcalFraming: (consumed, target) => {
      const diff = target - consumed;
      if (diff > 0) return `You're ${diff} kcal under target`;
      if (diff < 0) return `You're ${Math.abs(diff)} kcal over target`;
      return "You're right on target";
    },
    targetPillLabel: "Loss target: −0.5 kg / week",
    secondaryCta: { label: "Log a meal", href: "/dashboard" },
    weeklyChartTitle: "This week's kcal vs target",
    weightChartTitle: "Weight trend",
  },
  muscle_gain: {
    kcalFraming: (consumed, target, proteinRemainingG) => {
      if (proteinRemainingG !== undefined && proteinRemainingG > 0) {
        return `${proteinRemainingG} g protein remaining`;
      }
      // Fall back to kcal language when protein need is satisfied.
      const diff = target - consumed;
      if (diff > 0) return `You're ${diff} kcal under target`;
      if (diff < 0) return `You're ${Math.abs(diff)} kcal over target`;
      return "You're right on target";
    },
    targetPillLabel: "Gain target: +0.25 kg / week",
    secondaryCta: { label: "Log a meal", href: "/dashboard" },
    weeklyChartTitle: "This week's kcal vs target",
    weightChartTitle: "Weight trend",
  },
};
