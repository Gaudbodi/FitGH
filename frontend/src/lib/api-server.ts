// BFF helper — Phase 2 Plan 02 (P2-C.2).
//
// Forwards a request to Flask with the Clerk Bearer JWT attached. Browser
// never holds the JWT — same-origin BFF call from the client, BFF -> Flask
// is a Render-internal hop with the verified session token.

import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

/**
 * Forward `method path` to `${NEXT_PUBLIC_API_URL}${path}` with the Clerk
 * Bearer JWT. Returns a NextResponse that proxies upstream status + body
 * verbatim. Sets cache: 'no-store'.
 */
export async function forwardToFlask(
  method: "GET" | "POST" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
): Promise<NextResponse> {
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

  const init: RequestInit = {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    cache: "no-store",
  };
  if (body !== undefined) {
    init.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  const upstream = await fetch(`${apiUrl}${path}`, init);
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "content-type":
        upstream.headers.get("content-type") ?? "application/json",
    },
  });
}

/**
 * Forward a multipart/form-data POST to Flask, same JWT-attach shape
 * as forwardToFlask but passing the FormData body through without
 * re-serialisation. Phase 4 — Plan 04 (P4-C.1).
 *
 * Critical: do NOT set Content-Type — Node's fetch infers the
 * multipart boundary from the FormData body. Setting it manually
 * strips the boundary and Flask sees no parts.
 */
export async function forwardMultipart(
  method: "POST",
  path: string,
  formData: FormData,
): Promise<NextResponse> {
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

  const upstream = await fetch(`${apiUrl}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      // No Content-Type — fetch sets the multipart boundary from FormData.
    },
    body: formData,
    cache: "no-store",
  });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "content-type":
        upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
