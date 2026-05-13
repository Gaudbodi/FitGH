// BFF /api/meals — Phase 3 Plan 03 (P3-C.1).
//
// GET forwards to Flask GET /meals (forwards query string — date / days).
// POST forwards to Flask POST /meals with body verbatim.

import type { NextRequest } from "next/server";
import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const search = req.nextUrl.search;
  return forwardToFlask("GET", `/meals${search}`);
}

export async function POST(req: NextRequest) {
  const body = await req.text();
  return forwardToFlask("POST", "/meals", body);
}
