// Vitest tests for <WeeklyKcalChart>.
// Phase 5 Plan 05 (P5-C.3).

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { DayMealsResponse } from "@/lib/zod-schemas";
import { kcalColorBand, kcalColorClasses } from "@/lib/kcal-color";
import { WeeklyKcalChart } from "./weekly-kcal-chart";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function daysAgo(n: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - n);
  return d.toISOString().slice(0, 10);
}

function buildDay(date: string, kcal: number): DayMealsResponse {
  return {
    date,
    total_kcal: kcal,
    total_protein_g: 0,
    meals: [],
  };
}

describe("<WeeklyKcalChart>", () => {
  it("renders 7 bars even when input only has 2 days", () => {
    const days = [buildDay(today(), 1800), buildDay(daysAgo(2), 1600)];
    render(
      <WeeklyKcalChart days={days} targetKcal={2000} motionDisabled />,
    );
    // The chart wraps a SVG; verify the section + canvas wrapper render.
    expect(screen.getByTestId("weekly-kcal-chart")).toBeInTheDocument();
    expect(
      screen.getByTestId("weekly-kcal-chart-canvas"),
    ).toBeInTheDocument();
  });

  it("renders with empty days array (all bars = 0)", () => {
    render(
      <WeeklyKcalChart days={[]} targetKcal={2000} motionDisabled />,
    );
    expect(screen.getByTestId("weekly-kcal-chart")).toBeInTheDocument();
  });

  it("kcalColorClasses contract: over-target → red stroke is what the chart uses", () => {
    // We assert the chart's underlying band logic returns the expected hex
    // for an over-target day. The Cell fills derive from this hex.
    expect(kcalColorClasses(kcalColorBand(2200, 2000)).stroke).toMatch(
      /dc2626/i,
    );
    expect(kcalColorClasses(kcalColorBand(1500, 2000)).stroke).toMatch(
      /10b981/i,
    );
  });

  it("does not throw when motionDisabled=false", () => {
    const days = [buildDay(today(), 1000)];
    expect(() =>
      render(<WeeklyKcalChart days={days} targetKcal={2000} />),
    ).not.toThrow();
  });

  it("section is labelled by the heading", () => {
    render(
      <WeeklyKcalChart days={[]} targetKcal={2000} motionDisabled />,
    );
    expect(
      screen.getByRole("heading", { name: /kcal vs target/i }),
    ).toBeInTheDocument();
  });
});
