// Phase 6 (Workout Library + PWA) — P6-B.1 unit tests for the exercises
// library + filter helpers + zod manifest schema.
//
// Pure logic only — no fs reads (loadManifest is server-side; tested via
// fixture injection here).

import { describe, expect, it } from "vitest";
import {
  DEFAULT_EQUIPMENT_SELECTION,
  type ExerciseEntry,
  filterExercises,
  findExerciseById,
  manifestSchema,
} from "./exercises";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const mk = (
  partial: Partial<ExerciseEntry> & Pick<ExerciseEntry, "id" | "equipment">,
): ExerciseEntry => ({
  id: partial.id,
  name: partial.name ?? partial.id,
  equipment: partial.equipment,
  muscles_primary: partial.muscles_primary ?? ["chest"],
  muscles_secondary: partial.muscles_secondary ?? [],
  category: partial.category ?? "strength",
  level: partial.level ?? "beginner",
  mechanic: partial.mechanic ?? "compound",
  instructions: partial.instructions ?? [],
  poster: partial.poster ?? `/exercises/${partial.id}/poster.webp`,
  detail: partial.detail ?? `/exercises/${partial.id}/detail.webp`,
});

const FIXTURES: ExerciseEntry[] = [
  mk({ id: "Push-Up", equipment: "none", muscles_primary: ["chest"] }),
  mk({ id: "Dumbbell-Press", equipment: "dumbbell", muscles_primary: ["chest"] }),
  mk({ id: "Dumbbell-Row", equipment: "dumbbell", muscles_primary: ["back"] }),
  mk({ id: "Barbell-Squat", equipment: "barbell", muscles_primary: ["legs"] }),
  mk({ id: "Band-Curl", equipment: "bands", muscles_primary: ["arms"] }),
  mk({ id: "KB-Swing", equipment: "kettlebells", muscles_primary: ["glutes"] }),
];

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

describe("DEFAULT_EQUIPMENT_SELECTION", () => {
  it("is exactly ['none', 'dumbbell']", () => {
    expect(DEFAULT_EQUIPMENT_SELECTION).toEqual(["none", "dumbbell"]);
  });
});

// ---------------------------------------------------------------------------
// filterExercises
// ---------------------------------------------------------------------------

describe("filterExercises", () => {
  it("default selection returns only none + dumbbell entries", () => {
    const result = filterExercises(FIXTURES, {
      equipment: DEFAULT_EQUIPMENT_SELECTION,
      muscles: [],
    });
    expect(result.map((e) => e.id).sort()).toEqual(
      ["Dumbbell-Press", "Dumbbell-Row", "Push-Up"],
    );
  });

  it("intersects equipment and muscles (AND across categories, OR within)", () => {
    const result = filterExercises(FIXTURES, {
      equipment: ["dumbbell"],
      muscles: ["chest"],
    });
    expect(result.map((e) => e.id)).toEqual(["Dumbbell-Press"]);
  });

  it("empty selection (no equipment, no muscles) returns all entries", () => {
    const result = filterExercises(FIXTURES, { equipment: [], muscles: [] });
    expect(result).toHaveLength(FIXTURES.length);
  });

  it("empty intersection returns empty array", () => {
    const result = filterExercises(FIXTURES, {
      equipment: ["dumbbell"],
      muscles: ["glutes"],
    });
    expect(result).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// findExerciseById
// ---------------------------------------------------------------------------

describe("findExerciseById", () => {
  it("returns the matching entry", () => {
    const e = findExerciseById(FIXTURES, "Push-Up");
    expect(e?.id).toBe("Push-Up");
  });

  it("returns undefined for missing id", () => {
    expect(findExerciseById(FIXTURES, "Bench-Press")).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// manifestSchema
// ---------------------------------------------------------------------------

describe("manifestSchema", () => {
  it("rejects manifest with unknown equipment", () => {
    const bad = {
      meta: {
        source: "https://github.com/yuhonas/free-exercise-db",
        commit: "abc123",
        license: "Unlicense",
        generated_at: "2026-05-13T00:00:00Z",
      },
      entries: [
        {
          id: "Bad-Entry",
          name: "Bad",
          equipment: "machine", // <— not in the 6-bucket union
          muscles_primary: ["chest"],
          muscles_secondary: [],
          category: "strength",
          level: "beginner",
          mechanic: null,
          instructions: [],
          poster: "/exercises/Bad-Entry/poster.webp",
          detail: "/exercises/Bad-Entry/detail.webp",
        },
      ],
    };
    expect(() => manifestSchema.parse(bad)).toThrow();
  });

  it("accepts a well-formed manifest", () => {
    const good = {
      meta: {
        source: "https://github.com/yuhonas/free-exercise-db",
        commit: "acd61f751fe15d618862ee3084f27e839222a28f",
        license: "Unlicense",
        generated_at: "2026-05-13T13:44:50Z",
      },
      entries: FIXTURES,
    };
    const parsed = manifestSchema.parse(good);
    expect(parsed.entries).toHaveLength(FIXTURES.length);
    expect(parsed.meta.commit).toBe("acd61f751fe15d618862ee3084f27e839222a28f");
  });
});
