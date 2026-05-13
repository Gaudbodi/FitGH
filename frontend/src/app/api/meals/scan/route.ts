// BFF /api/meals/scan — Phase 4 Plan 04 (P4-C.1).
//
// POST forwards multipart/form-data (the compressed meal image) verbatim
// to Flask POST /meals/scan. The browser only ever calls this same-origin
// route — Clerk's session cookie is exchanged for a Bearer JWT by
// forwardMultipart.

import type { NextRequest } from "next/server";
import { forwardMultipart } from "@/lib/api-server";

export const dynamic = "force-dynamic";
// Multipart upload bodies skip Next's default body-size limit (1 MB) by
// streaming through to Flask. The compressed image is ≤0.5 MB target so
// 1 MB is plenty; leaving the default in place is fine.

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  return forwardMultipart("POST", "/meals/scan", formData);
}
