"use client";

// Phase 6 P6-B.2 — Sticky filter bar with equipment + muscle chip rows.
//
// Two chip rows: equipment (6 chips) and muscle (8 chips). Each chip is a
// bare <button aria-pressed> with focus rings. Same-category chips OR
// together; cross-category chips AND together (the AND is applied by
// filterExercises in @/lib/exercises). Controlled component — selection
// state owned by the parent <WorkoutsGrid>.

import {
  EQUIPMENT_LABEL,
  MUSCLE_LABEL,
  type EquipmentBucket,
  type MuscleBucket,
} from "@/lib/exercises";

export interface FilterSelection {
  equipment: EquipmentBucket[];
  muscles: MuscleBucket[];
}

interface Props {
  selection: FilterSelection;
  onChange: (next: FilterSelection) => void;
}

const EQUIPMENT_CHIPS: EquipmentBucket[] = [
  "none",
  "dumbbell",
  "bands",
  "pull-up bar",
  "kettlebells",
  "barbell",
];

const MUSCLE_CHIPS: MuscleBucket[] = [
  "chest",
  "back",
  "legs",
  "shoulders",
  "arms",
  "core",
  "glutes",
  "full-body",
];

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value)
    ? list.filter((x) => x !== value)
    : [...list, value];
}

interface ChipProps {
  label: string;
  pressed: boolean;
  onToggle: () => void;
}

function Chip({ label, pressed, onToggle }: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onToggle}
      className={
        "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 " +
        "focus-visible:ring-offset-2 " +
        (pressed
          ? "bg-emerald-500 text-white border-emerald-500"
          : "bg-muted text-muted-foreground border-transparent hover:bg-muted/80")
      }
    >
      {label}
    </button>
  );
}

export function FilterBar({ selection, onChange }: Props) {
  return (
    <div className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur py-3 px-4 space-y-2">
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Filter by equipment"
      >
        {EQUIPMENT_CHIPS.map((bucket) => (
          <Chip
            key={bucket}
            label={EQUIPMENT_LABEL[bucket]}
            pressed={selection.equipment.includes(bucket)}
            onToggle={() =>
              onChange({
                ...selection,
                equipment: toggle(selection.equipment, bucket),
              })
            }
          />
        ))}
      </div>
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Filter by muscle group"
      >
        {MUSCLE_CHIPS.map((bucket) => (
          <Chip
            key={bucket}
            label={MUSCLE_LABEL[bucket]}
            pressed={selection.muscles.includes(bucket)}
            onToggle={() =>
              onChange({
                ...selection,
                muscles: toggle(selection.muscles, bucket),
              })
            }
          />
        ))}
      </div>
    </div>
  );
}
