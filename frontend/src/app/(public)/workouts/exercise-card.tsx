// Phase 6 P6-B.2 — ExerciseCard (server component).
//
// Renders a single workout-library card: tiny WebP poster + name + small
// equipment/muscle labels. The whole card is a <Link> to /workouts/[id].
// `next/image unoptimized` ships the WebP as-is — the ingest script already
// produced a poster-sized optimised file.
//
// `priority` (P6-E.1 Rule 1 fix): when set, the poster is eager-loaded
// with fetchPriority='high'. The grid hands `priority=true` to the first
// 4 cards (the above-the-fold viewport at 360×800 fits roughly 1–2 cards;
// 4 covers the common 420×900 phone case too). Without this, Lighthouse
// flagged the LCP poster as lazy-loaded and the LCP audit collapsed to
// 0/100 (LCP 4.3 s, audit score 0.42).

import Image from "next/image";
import Link from "next/link";
import {
  EQUIPMENT_LABEL,
  MUSCLE_LABEL,
  type ExerciseEntry,
} from "@/lib/exercises";

interface Props {
  entry: ExerciseEntry;
  priority?: boolean;
}

export function ExerciseCard({ entry, priority = false }: Props) {
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
        {...(priority
          ? { priority: true, fetchPriority: "high" as const }
          : { loading: "lazy" as const })}
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
