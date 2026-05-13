// Vitest tests for <KcalRing>.
// Phase 5 Plan 05 (P5-D.2).

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  KcalRing,
  KCAL_RING_CIRCUMFERENCE,
  KCAL_RING_RADIUS,
} from "./kcal-ring";

function getProgressDashOffset(): number {
  const el = screen.getByTestId("kcal-ring-progress");
  const raw = el.getAttribute("stroke-dashoffset");
  return raw === null ? NaN : Number(raw);
}

describe("<KcalRing>", () => {
  it("geometry constants match r=80 circle", () => {
    expect(KCAL_RING_RADIUS).toBe(80);
    expect(KCAL_RING_CIRCUMFERENCE).toBeCloseTo(2 * Math.PI * 80, 6);
  });

  it("0% consumption -> full dashoffset (no arc visible)", () => {
    render(<KcalRing totalKcal={0} targetKcal={2000} motionDisabled />);
    expect(getProgressDashOffset()).toBeCloseTo(KCAL_RING_CIRCUMFERENCE, 4);
  });

  it("50% consumption -> half dashoffset", () => {
    render(<KcalRing totalKcal={1000} targetKcal={2000} motionDisabled />);
    expect(getProgressDashOffset()).toBeCloseTo(
      KCAL_RING_CIRCUMFERENCE * 0.5,
      4,
    );
  });

  it("just over 90% -> 10% dashoffset and amber stroke", () => {
    // 1801/2000 = 90.05% -> amber per kcalColorBand `> 0.9 * target`.
    render(<KcalRing totalKcal={1801} targetKcal={2000} motionDisabled />);
    expect(getProgressDashOffset()).toBeCloseTo(
      KCAL_RING_CIRCUMFERENCE * (1 - 1801 / 2000),
      4,
    );
    const stroke = screen
      .getByTestId("kcal-ring-progress")
      .getAttribute("stroke");
    expect(stroke?.toLowerCase()).toMatch(/d97706/);
  });

  it("100% consumption -> 0 dashoffset and amber stroke", () => {
    render(<KcalRing totalKcal={2000} targetKcal={2000} motionDisabled />);
    expect(getProgressDashOffset()).toBeCloseTo(0, 4);
  });

  it("120% consumption -> 0 dashoffset clamped and red stroke", () => {
    render(<KcalRing totalKcal={2400} targetKcal={2000} motionDisabled />);
    expect(getProgressDashOffset()).toBeCloseTo(0, 4);
    const stroke = screen
      .getByTestId("kcal-ring-progress")
      .getAttribute("stroke");
    expect(stroke?.toLowerCase()).toMatch(/dc2626/);
  });

  it("renders the consumed kcal as text", () => {
    render(<KcalRing totalKcal={1234} targetKcal={2000} motionDisabled />);
    expect(screen.getByText("1234")).toBeInTheDocument();
    expect(screen.getByText(/2000 kcal/)).toBeInTheDocument();
  });

  it("motionDisabled=true sets transition to 0ms", () => {
    render(<KcalRing totalKcal={1000} targetKcal={2000} motionDisabled />);
    const style = screen
      .getByTestId("kcal-ring-progress")
      .getAttribute("style");
    expect(style).toMatch(/transition:[^;]*0ms/);
  });

  it("motionDisabled=false sets transition to 600ms ease", () => {
    render(<KcalRing totalKcal={1000} targetKcal={2000} />);
    const style = screen
      .getByTestId("kcal-ring-progress")
      .getAttribute("style");
    expect(style).toMatch(/transition:[^;]*600ms/);
  });

  it("does not crash on targetKcal=0", () => {
    expect(() =>
      render(<KcalRing totalKcal={0} targetKcal={0} motionDisabled />),
    ).not.toThrow();
  });
});
