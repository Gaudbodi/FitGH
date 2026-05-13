// BFF route /api/me — Phase 1 Walking Skeleton (WS-D.3).
//
// Server-side Route Handler. Reads the verified Clerk session via auth(),
// pulls the session JWT via auth().getToken(), and forwards it to Flask
// /me as `Authorization: Bearer <token>`. The browser never sees or sets
// the JWT — same-origin to the BFF, BFF -> Flask is a Render-internal hop.
//
// Threat register:
//   T-01-02: Flask verifies the JWT networkless via clerk-backend-api.
//   T-01-03: The browser cannot tamper with the JWT in transit because it
//            never holds it; the BFF reads it from the verified session.

import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Never cache a per-user response. Without this, Next.js may statically
// generate /api/me at build time with the placeholder Clerk env and a
// signed-out auth() — which is wrong both for prerender and for the first
// real request after deploy.
export const dynamic = "force-dynamic";

export async function GET() {
  const { userId, getToken } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const token = await getToken();
  if (!token) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    return NextResponse.json(
      { error: "api_url_not_configured" },
      { status: 503 },
    );
  }

  const upstream = await fetch(`${apiUrl}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  // Proxy the upstream status + body straight through. Flask owns the
  // shape of {email} / {error,reason} responses; the BFF is a thin pass.
  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" },
  });
}
