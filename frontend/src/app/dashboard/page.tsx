// /dashboard — Phase 2 Plan 02 (P2-C.3 + P2-D.2).
//
// Server component. Fetches /api/profile + /api/weights in parallel.
//   401 -> redirect("/sign-in")
//   404 -> redirect("/onboarding") (profile missing — gate per phase goal)
//   200 -> render TargetCard + WeightLogCard
//
// Auth gating is double-belted: middleware.ts protects /dashboard via
// auth.protect(); /api/profile 401 also redirects.

import Link from "next/link";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { SignOutButton } from "@/components/sign-out-button";
import type { ProfileResponse, WeightLogResponse } from "@/lib/zod-schemas";
import { TargetCard } from "./target-card";
import { WeightLogCard } from "./weight-log-card";

export const dynamic = "force-dynamic";

async function fetchSameOrigin(path: string, cookie: string, base: string) {
  return fetch(`${base}${path}`, {
    headers: { cookie },
    cache: "no-store",
  });
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

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Hi, {profile.name}</h1>
          <p className="text-sm text-muted-foreground">
            FitGH dashboard
          </p>
        </div>
        <div className="flex items-center gap-2">
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

      <TargetCard profile={profile} />
      <WeightLogCard recentWeights={weightsBody.entries} />
    </main>
  );
}
