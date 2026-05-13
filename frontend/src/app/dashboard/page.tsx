// /dashboard — Phase 2 Plan 02 (P2-C.3 + P2-D.2) + Phase 3 Plan 03 (P3-D.2).
//
// Server component. Fetches /api/profile + /api/weights in parallel, then
// (once profile.timezone is known) fetches /api/meals?date=<today_in_tz>.
//   401 on profile -> redirect("/sign-in")
//   404 on profile -> redirect("/onboarding")
//   200 -> render KcalPill + TargetCard + WeightLogCard + MealLogIsland.
//
// Auth gating is double-belted: middleware.ts protects /dashboard via
// auth.protect(); /api/profile 401 also redirects.

import Link from "next/link";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { SignOutButton } from "@/components/sign-out-button";
import type {
  DayMealsResponse,
  ProfileResponse,
  WeightLogResponse,
} from "@/lib/zod-schemas";
import { KcalPill } from "./kcal-pill";
import { MealLogIsland } from "./log-meal-cta";
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
  // Intl en-CA formatter emits YYYY-MM-DD directly — no manual padding.
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

  const [profileRes, weightsRes] = await Promise.all([
    fetchSameOrigin("/api/profile", cookie, base),
    fetchSameOrigin("/api/weights?limit=30", cookie, base),
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

  return (
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

      <KcalPill
        totalKcal={today.total_kcal}
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
  );
}
