// Phase 6 P6-B.3 — friendly 404 for /workouts/[id] when id is not in the
// static manifest. Reachable via notFound() in page.tsx.

import Link from "next/link";

export default function ExerciseNotFound() {
  return (
    <main className="mx-auto max-w-md px-4 py-16 text-center space-y-4">
      <h1 className="text-2xl font-semibold">Exercise not found</h1>
      <p className="text-sm text-muted-foreground">
        We couldn&apos;t find that exercise in the FitGH library.
      </p>
      <Link
        href="/workouts"
        className="inline-block text-sm font-medium text-emerald-600 underline-offset-4 hover:underline"
      >
        ← Back to workouts
      </Link>
    </main>
  );
}
