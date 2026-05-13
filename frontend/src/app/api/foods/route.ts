// BFF /api/foods — Phase 3 Plan 03 (P3-C.1).
//
// GET forwards to Flask GET /foods (forwards query string verbatim — q,
// limit). Browser never holds the Clerk JWT; the BFF attaches it.

import type { NextRequest } from "next/server";
import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const search = req.nextUrl.search; // includes leading "?" if present
  return forwardToFlask("GET", `/foods${search}`);
}
