// ChartLoadingSkeleton — Phase 5 Plan 05 (P5-C.1).
//
// Plain Tailwind skeleton rendered by next/dynamic while the Recharts chunk
// downloads. Aspect ratio matches WeightChart + WeeklyKcalChart so layout
// doesn't shift when the real chart hydrates.

export function ChartLoadingSkeleton() {
  return (
    <div
      className="h-64 w-full animate-pulse rounded-md bg-muted"
      aria-hidden="true"
      data-testid="chart-loading-skeleton"
    />
  );
}
