// BFF /api/weights — Phase 2 Plan 02 (P2-D.2).
//
// GET forwards to Flask GET /weights (forwards query string too).
// POST forwards to Flask POST /weights with body verbatim.

import type { NextRequest } from "next/server";
import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const search = req.nextUrl.search; // includes leading "?" if present
  return forwardToFlask("GET", `/weights${search}`);
}

export async function POST(req: NextRequest) {
  const body = await req.text();
  return forwardToFlask("POST", "/weights", body);
}
