// Phase 6 P6-B.2 — ExerciseCard (server component).
//
// Renders a single workout-library card: tiny WebP poster + name + small
// equipment/muscle labels. The whole card is a <Link> to /workouts/[id].
// `next/image unoptimized` ships the WebP as-is — the ingest script already
// produced a poster-sized optimised file.

import Image from "next/image";
import Link from "next/link";
import {
  EQUIPMENT_LABEL,
  MUSCLE_LABEL,
  type ExerciseEntry,
} from "@/lib/exercises";

interface Props {
  entry: ExerciseEntry;
}

export function ExerciseCard({ entry }: Props) {
  const primary = entry.muscles_primary[0];
  return (
    <Link
      href={`/workouts/${encodeURIComponent(entry.id)}`}
      className="block overflow-hidden rounded-lg border bg-card text-card-foreground hover:shadow-md transition-shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
    >
      <Image
        src={entry.poster}
        alt={entry.name}
        width={320}
        height={240}
        unoptimized
        loading="lazy"
        className="aspect-[4/3] w-full object-cover"
      />
      <div className="p-3 space-y-1">
        <h3 className="text-sm font-semibold leading-tight">{entry.name}</h3>
        <p className="text-xs text-muted-foreground">
          {EQUIPMENT_LABEL[entry.equipment]}
          {primary ? ` · ${MUSCLE_LABEL[primary]}` : ""}
        </p>
      </div>
    </Link>
  );
}
