// BFF /api/corrections — Phase 4 Plan 04 (P4-C.1).
//
// POST forwards the user-correction JSON body verbatim to Flask
// POST /corrections. Called from the ScanResultChips on each chip
// mutation (name swap, portion drag, remove). Best-effort —
// failures swallow silently on the FE so the user's flow isn't broken
// by a missed correction.

import type { NextRequest } from "next/server";
import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const body = await req.text();
  return forwardToFlask("POST", "/corrections", body);
}
