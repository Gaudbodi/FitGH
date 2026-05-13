// /dashboard — Phase 2 Plan 02 (P2-C.3 + P2-D.2) + Phase 3 Plan 03 (P3-D.2)
//                + Phase 5 Plan 05 (P5-D.3).
//
// Server component. Phase 5 parallel fetches:
//   /api/profile           (existing — also surfaces streak_count / state)
//   /api/weights?limit=90  (Phase 5 — feeds the 30/90 chart + avatar slope)
//   /api/meals?date=<tz>   (Phase 3 — today's bucket for the kcal ring)
//   /api/meals?days=7      (Phase 5 — feeds the weekly bar chart)
// 401 -> /sign-in, 404 -> /onboarding.
//
// Recharts components are dynamic-imported via next/dynamic(ssr:false) so
// the ~25 kB Recharts payload lives in a separate client chunk; the
// dashboard's First Load JS stays under the 260 kB Phase 5 ceiling.

import Link from "next/link";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { SignOutButton } from "@/components/sign-out-button";
import { dashboardCopy } from "@/lib/dashboard-copy";
import type {
  DayMealsResponse,
  ProfileResponse,
  WeightLogResponse,
} from "@/lib/zod-schemas";
import { Avatar } from "@/components/avatar/avatar";
import { ChartsIsland } from "./charts-island";
import { KcalPill } from "./kcal-pill";
import { KcalRing } from "./kcal-ring";
import { MealLogIsland } from "./log-meal-cta";
import { MotionDetector } from "./motion-detector";
import { StreakBadge } from "./streak-badge";
import { TargetCard } from "./target-card";
import { WeightLogCard } from "./weight-log-card";

export const dynamic = "force-dynamic";

async function fetchSameOrigin(path: string, cookie: string, base: string) {
  return fetch(`${base}${path}`, {
    headers: { cookie },
    cache: "no-store",
  });
}

function todayInUserTz(tz: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

export default async function DashboardPage() {
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host");
  const cookie = h.get("cookie") ?? "";
  const base = `${proto}://${host}`;

  // Parallel fetch of everything that doesn't depend on profile.timezone.
  const [profileRes, weightsRes, weekRes] = await Promise.all([
    fetchSameOrigin("/api/profile", cookie, base),
    fetchSameOrigin("/api/weights?limit=90", cookie, base),
    fetchSameOrigin("/api/meals?days=7", cookie, base),
  ]);

  if (profileRes.status === 401) {
    redirect("/sign-in");
  }
  if (profileRes.status === 404) {
    redirect("/onboarding");
  }
  if (!profileRes.ok) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <p className="text-sm text-destructive">
          Could not load your profile ({profileRes.status}).
        </p>
      </main>
    );
  }

  const profile = (await profileRes.json()) as ProfileResponse;
  const weightsBody = weightsRes.ok
    ? ((await weightsRes.json()) as { entries: WeightLogResponse[] })
    : { entries: [] };
  const weekBody = weekRes.ok
    ? ((await weekRes.json()) as { days: DayMealsResponse[] })
    : { days: [] };

  // Backfill: existing Phase 2 docs may lack streak fields. Use safe
  // defaults so the StreakBadge doesn't crash before the first POST.
  const streakCount = profile.streak_count ?? 0;
  const streakState = profile.streak_state ?? "active";

  // Now that profile.timezone is known, fetch today's meals.
  const todayStr = todayInUserTz(profile.timezone);
  const mealsRes = await fetchSameOrigin(
    `/api/meals?date=${todayStr}`,
    cookie,
    base,
  );
  const today: DayMealsResponse = mealsRes.ok
    ? ((await mealsRes.json()) as DayMealsResponse)
    : { date: todayStr, total_kcal: 0, total_protein_g: 0, meals: [] };

  const copy = dashboardCopy[profile.primary_goal];
  const proteinRemaining =
    profile.daily_protein_g_target !== null
      ? Math.max(
          profile.daily_protein_g_target - today.total_protein_g,
          0,
        )
      : undefined;
  const framing = copy.kcalFraming(
    today.total_kcal,
    profile.daily_kcal_target,
    proteinRemaining,
  );

  return (
    <>
      <MotionDetector />
      <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-6 p-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Hi, {profile.name}</h1>
            <p className="text-sm text-muted-foreground">FitGH dashboard</p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/history"
              className="text-sm font-medium underline-offset-4 hover:underline"
            >
              History
            </Link>
            <Link
              href="/profile"
              className="text-sm font-medium underline-offset-4 hover:underline"
            >
              Profile
            </Link>
            <Link
              href="/settings"
              className="text-sm font-medium underline-offset-4 hover:underline"
            >
              Settings
            </Link>
            <SignOutButton />
          </div>
        </header>

        <div className="flex flex-col items-center gap-4">
          <Avatar profile={profile} recentWeights={weightsBody.entries} />
          <div className="flex flex-wrap items-center justify-center gap-2">
            <StreakBadge
              streakCount={streakCount}
              streakState={streakState}
            />
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {copy.targetPillLabel}
            </span>
          </div>
          <KcalRing
            totalKcal={today.total_kcal}
            targetKcal={profile.daily_kcal_target}
          />
          <p className="text-sm text-muted-foreground">{framing}</p>
        </div>

        <KcalPill
          totalKcal={today.total_kcal}
          targetKcal={profile.daily_kcal_target}
        />

        <ChartsIsland
          weights={weightsBody.entries}
          weekDays={weekBody.days}
          targetKcal={profile.daily_kcal_target}
        />

        <MealLogIsland meals={today.meals} />
        <TargetCard profile={profile} />
        <WeightLogCard recentWeights={weightsBody.entries} />

        {!mealsRes.ok && (
          <p className="text-xs text-destructive">
            Could not load today&apos;s meals ({mealsRes.status}).
          </p>
        )}
      </main>
    </>
  );
}
