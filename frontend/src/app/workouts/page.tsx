// Phase 6 P6-B.2 — /workouts list page.
//
// Server component (App Router). Reads the static manifest at build time
// (`force-static`), passes the entry list down to the client <WorkoutsGrid>
// which holds the filter selection state. No auth check — middleware leaves
// /workouts public by default (CONTEXT D-PUBLIC-WORKOUTS / WORK-01).

import { loadManifest } from "@/lib/exercises.server";
import { WorkoutsGrid } from "./workouts-grid";

export const dynamic = "force-static";

export const metadata = {
  title: "Workouts — FitGH",
  description:
    "Browse curated bodyweight, dumbbell, kettlebell, band, and barbell exercises. Filter by equipment and target muscle.",
};

export default async function WorkoutsPage() {
  const entries = await loadManifest();
  return (
    <main className="mx-auto max-w-6xl">
      <header className="px-4 pt-6 pb-2">
        <h1 className="text-2xl font-semibold">Workout library</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {entries.length} exercises. Filter by equipment and muscle group.
        </p>
      </header>
      <WorkoutsGrid entries={entries} />
    </main>
  );
}
