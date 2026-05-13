// Barrel export — Phase 5 Plan 05 (P5-C.1).
//
// /dashboard/page.tsx imports this barrel via next/dynamic(ssr:false) so
// Recharts ends up in a client chunk separate from the dashboard's
// server-rendered HTML.

export { WeightChart } from "./weight-chart";
export { WeeklyKcalChart } from "./weekly-kcal-chart";
export { ChartLoadingSkeleton } from "./loading-skeleton";
