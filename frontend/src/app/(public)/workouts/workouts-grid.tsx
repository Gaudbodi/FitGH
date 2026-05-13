"use client";

// Phase 6 P6-B.2 — WorkoutsGrid client component.
//
// Owns filter selection state (initialised to DEFAULT_EQUIPMENT_SELECTION
// per CONTEXT D-FILTER-DEFAULT / WORK-04). Renders <FilterBar> + a
// responsive CSS grid of <ExerciseCard>. Empty-state copy when the filter
// excludes every entry.

import { useMemo, useState } from "react";
import {
  DEFAULT_EQUIPMENT_SELECTION,
  filterExercises,
  type ExerciseEntry,
} from "@/lib/exercises";
import { ExerciseCard } from "./exercise-card";
import { FilterBar, type FilterSelection } from "./filter-bar";

interface Props {
  entries: ExerciseEntry[];
}

export function WorkoutsGrid({ entries }: Props) {
  const [selection, setSelection] = useState<FilterSelection>({
    equipment: DEFAULT_EQUIPMENT_SELECTION,
    muscles: [],
  });
  const filtered = useMemo(
    () => filterExercises(entries, selection),
    [entries, selection],
  );

  return (
    <div>
      <FilterBar selection={selection} onChange={setSelection} />
      {filtered.length === 0 ? (
        <p className="px-4 py-12 text-center text-sm text-muted-foreground">
          No exercises match these filters. Try adding more equipment or muscle
          groups.
        </p>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4 p-4">
          {filtered.map((entry, i) => (
            // First 4 cards eager-load with fetchPriority=high (P6-E.1
            // Rule 1 fix — Lighthouse flagged the LCP poster as
            // lazy-loaded).
            <ExerciseCard key={entry.id} entry={entry} priority={i < 4} />
          ))}
        </div>
      )}
    </div>
  );
}
