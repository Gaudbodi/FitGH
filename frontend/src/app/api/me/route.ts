// BFF /api/me — uses the shared forwardToFlask helper (P2-C.2 refactor).
//
// Original WS-D.3 inline implementation has been refactored into
// `frontend/src/lib/api-server.ts`. Behavior is identical: read the verified
// Clerk session via auth(), pull the JWT via getToken(), forward to Flask /me
// as Authorization: Bearer <token>, proxy upstream status+body unchanged.
//
// Threat register T-01-02/T-01-03 invariants preserved.

import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function GET() {
  return forwardToFlask("GET", "/me");
}
