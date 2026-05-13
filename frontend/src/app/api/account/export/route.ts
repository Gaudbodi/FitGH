// BFF /api/account/export GET — Phase 7 P7-C.3 (LEGAL-02).
//
// Forwards GET to Flask GET /me/export and adds a Content-Disposition
// attachment header so the browser downloads the JSON archive rather than
// rendering it. Filename: fitgh-export-{clerk_id}-{YYYY-MM-DD}.json.
//
// Mirrors the shape of /api/account/route.ts (DELETE handler) for the
// auth + forward bits; the wrinkle is the Content-Disposition mutation
// (forwardToFlask doesn't set it).

import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

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

  const upstream = await fetch(`${apiUrl}/me/export`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  // Pass non-2xx through unchanged — no Content-Disposition mutation.
  if (!upstream.ok) {
    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "content-type":
          upstream.headers.get("content-type") ?? "application/json",
      },
    });
  }

  const body = await upstream.text();
  const date = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  return new NextResponse(body, {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Content-Disposition": `attachment; filename="fitgh-export-${userId}-${date}.json"`,
    },
  });
}
