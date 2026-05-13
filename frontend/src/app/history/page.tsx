// /history — Phase 3 Plan 03 (P3-E.1).
//
// SERVER component. Fetches /api/meals?days=30 and renders DayGroup per
// non-empty day, newest first. Read-only — no edit/delete on /history
// per D-HISTORY-READ-ONLY; mutations happen on /dashboard.

import Link from "next/link";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import type { MealsHistoryResponse } from "@/lib/zod-schemas";
import { DayGroup } from "./day-group";

export const dynamic = "force-dynamic";

async function fetchSameOrigin(path: string, cookie: string, base: string) {
  return fetch(`${base}${path}`, {
    headers: { cookie },
    cache: "no-store",
  });
}

export default async function HistoryPage() {
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host");
  const cookie = h.get("cookie") ?? "";
  const base = `${proto}://${host}`;

  const res = await fetchSameOrigin("/api/meals?days=30", cookie, base);

  if (res.status === 401) {
    redirect("/sign-in");
  }

  if (!res.ok) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-6 p-6">
        <header>
          <h1 className="text-2xl font-semibold">Last 30 days</h1>
        </header>
        <p className="text-sm text-destructive">
          Could not load history ({res.status}).
        </p>
        <Link
          href="/dashboard"
          className="text-sm font-medium underline-offset-4 hover:underline"
        >
          {"← Back to dashboard"}
        </Link>
      </main>
    );
  }

  const body = (await res.json()) as MealsHistoryResponse;
  const days = body.days ?? [];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Last 30 days</h1>
        <Link
          href="/dashboard"
          className="text-sm font-medium underline-offset-4 hover:underline"
        >
          {"← Back to dashboard"}
        </Link>
      </header>

      {days.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No meals logged yet. Head to the dashboard to log your first meal.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {days.map((day) => (
            <DayGroup key={day.date} day={day} />
          ))}
        </div>
      )}
    </main>
  );
}
