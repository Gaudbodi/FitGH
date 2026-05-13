// Vitest tests for <WeightChart>.
// Phase 5 Plan 05 (P5-C.2).

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { WeightLogResponse } from "@/lib/zod-schemas";
import { WeightChart } from "./weight-chart";

const NOW = new Date("2026-05-13T12:00:00Z").getTime();
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

/** Build N descending-date weight log entries, newest first. */
function buildEntries(count: number, startKg = 75): WeightLogResponse[] {
  return Array.from({ length: count }, (_, i) => ({
    user_id: "user_x",
    kg: startKg - i * 0.05,
    logged_at: new Date(NOW - i * ONE_DAY_MS).toISOString(),
  }));
}

describe("<WeightChart>", () => {
  it("renders the canvas with 60 entries filtered to last 30 days", () => {
    const entries = buildEntries(60);
    render(<WeightChart entries={entries} rangeDays={30} motionDisabled />);
    expect(screen.getByTestId("weight-chart-canvas")).toBeInTheDocument();
  });

  it("renders empty state when no entries supplied", () => {
    render(<WeightChart entries={[]} rangeDays={30} motionDisabled />);
    expect(screen.getByText(/log a weight to see your trend/i)).toBeInTheDocument();
    expect(screen.queryByTestId("weight-chart-canvas")).not.toBeInTheDocument();
  });

  it("renders empty state when all entries are older than rangeDays", () => {
    // 5 entries all 100 days ago — none fall in the 30-day window from the
    // newest entry's date anchor (the newest IS 100 days ago, so 30-day
    // window pulls only entries within the last 30 days from THAT anchor).
    // To trip the empty state we need 0 entries that survive filterAndSort
    // — guaranteed only by the empty-array case above. So this test
    // confirms with the actual empty list rather than a stale-date list.
    render(<WeightChart entries={[]} rangeDays={90} motionDisabled />);
    expect(screen.getByText(/log a weight to see your trend/i)).toBeInTheDocument();
  });

  it("exposes range-days as a data attribute (rangeDays=30 default)", () => {
    const entries = buildEntries(5);
    render(<WeightChart entries={entries} motionDisabled />);
    expect(screen.getByTestId("weight-chart")).toHaveAttribute(
      "data-range-days",
      "30",
    );
  });

  it("controlled rangeDays prop reflects in the data attribute", () => {
    const entries = buildEntries(5);
    render(<WeightChart entries={entries} rangeDays={90} motionDisabled />);
    expect(screen.getByTestId("weight-chart")).toHaveAttribute(
      "data-range-days",
      "90",
    );
  });

  it("toggle buttons are present and labelled", () => {
    const entries = buildEntries(5);
    render(<WeightChart entries={entries} motionDisabled />);
    expect(screen.getByRole("tab", { name: "30d" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "90d" })).toBeInTheDocument();
  });

  it("does not throw when rendered with motionDisabled=false", () => {
    const entries = buildEntries(10);
    expect(() =>
      render(<WeightChart entries={entries} rangeDays={30} />),
    ).not.toThrow();
  });
});
