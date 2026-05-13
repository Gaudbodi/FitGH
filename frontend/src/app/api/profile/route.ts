// BFF /api/profile — Phase 2 Plan 02 (P2-C.2).
//
// Forwards GET / POST / PATCH to Flask /profile via the shared helper.
// Bodies are passed through verbatim; Flask's Pydantic ProfileCreate /
// ProfileUpdate enforces field allow-listing (T-02-02, T-02-07).

import type { NextRequest } from "next/server";
import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function GET() {
  return forwardToFlask("GET", "/profile");
}

export async function POST(req: NextRequest) {
  const body = await req.text();
  return forwardToFlask("POST", "/profile", body);
}

export async function PATCH(req: NextRequest) {
  const body = await req.text();
  return forwardToFlask("PATCH", "/profile", body);
}
