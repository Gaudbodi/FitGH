// ServicePausedBanner — Phase 4 Plan 04 (P4-D.3).
//
// Server component. Reads GET /api/scan-budget and renders a banner when
// the global $/day cap has been reached. Absent otherwise. Manual log
// still works because the banner is purely informational.
//
// Auth-aware: the BFF returns 401 for unsigned-in users; we render
// nothing in that case (the banner is dashboard / history furniture,
// not a sign-in nudge).

import { headers } from "next/headers";
import type { ScanBudgetResponse } from "@/lib/zod-schemas";

export async function ServicePausedBanner() {
  // Same-origin fetch so the Clerk session cookie rides along.
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host");
  if (!host) return null;
  const cookie = h.get("cookie") ?? "";
  let res: Response;
  try {
    res = await fetch(`${proto}://${host}/api/scan-budget`, {
      headers: { cookie },
      cache: "no-store",
    });
  } catch {
    return null;
  }
  if (res.status === 401 || !res.ok) return null;
  let body: ScanBudgetResponse;
  try {
    body = (await res.json()) as ScanBudgetResponse;
  } catch {
    return null;
  }
  if (!body.paused) return null;
  return (
    <div className="border-b border-amber-500/30 bg-amber-50 px-6 py-2 text-center text-xs text-amber-900">
      Vision is paused for today (daily cost cap reached). You can still log
      manually.
    </div>
  );
}
