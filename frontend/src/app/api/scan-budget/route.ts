// BFF /api/scan-budget — Phase 4 Plan 04 (P4-D.3 hook).
//
// GET forwards to Flask GET /scan-budget. The ServicePausedBanner reads
// the {paused: bool} flag during server-side render of /dashboard and
// /history and renders a site-wide banner when the global $/day cap
// has been reached.

import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function GET() {
  return forwardToFlask("GET", "/scan-budget");
}
