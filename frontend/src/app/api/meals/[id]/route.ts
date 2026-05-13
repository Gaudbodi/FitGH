// BFF /api/meals/[id] — Phase 3 Plan 03 (P3-C.1).
//
// PATCH and DELETE forward to Flask /meals/<id>. Next 15 async params: the
// `params` prop is now a Promise; await it before reading `id`.

import type { NextRequest } from "next/server";
import { forwardToFlask } from "@/lib/api-server";

export const dynamic = "force-dynamic";

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await req.text();
  return forwardToFlask("PATCH", `/meals/${id}`, body);
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  return forwardToFlask("DELETE", `/meals/${id}`);
}
