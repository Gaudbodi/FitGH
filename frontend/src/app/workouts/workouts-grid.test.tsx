// Phase 6 P6-B.2 — WorkoutsGrid component tests.
//
// Verifies: renders one card per filtered entry (default selection); empty
// filter result shows the friendly empty-state copy.

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { WorkoutsGrid } from "./workouts-grid";
import type { ExerciseEntry } from "@/lib/exercises";

const mk = (
  id: string,
  equipment: ExerciseEntry["equipment"],
  primary: ExerciseEntry["muscles_primary"][number],
): ExerciseEntry => ({
  id,
  name: id.replace(/-/g, " "),
  equipment,
  muscles_primary: [primary],
  muscles_secondary: [],
  category: "strength",
  level: "beginner",
  mechanic: "compound",
  instructions: [],
  poster: `/exercises/${id}/poster.webp`,
  detail: `/exercises/${id}/detail.webp`,
});

describe("<WorkoutsGrid>", () => {
  it("renders one card per entry that passes the default filter (none + dumbbell)", () => {
    const entries = [
      mk("Push-Up", "none", "chest"),
      mk("Dumbbell-Press", "dumbbell", "chest"),
      mk("Barbell-Squat", "barbell", "legs"),
      mk("KB-Swing", "kettlebells", "glutes"),
    ];
    render(<WorkoutsGrid entries={entries} />);
    // Default filter is none + dumbbell → 2 of 4 cards rendered
    expect(screen.getAllByRole("link")).toHaveLength(2);
    expect(screen.getByText("Push Up")).toBeInTheDocument();
    expect(screen.getByText("Dumbbell Press")).toBeInTheDocument();
  });

  it("shows the empty-state copy when the filter excludes every entry", () => {
    // All barbell entries — default {none, dumbbell} filter excludes all
    const entries = [
      mk("Barbell-Squat", "barbell", "legs"),
      mk("Barbell-Deadlift", "barbell", "back"),
    ];
    render(<WorkoutsGrid entries={entries} />);
    expect(
      screen.getByText(/no exercises match/i),
    ).toBeInTheDocument();
  });
});
