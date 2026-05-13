// Clerk middleware — Phase 1 Walking Skeleton (WS-D.1).
//
// Protects /dashboard(.*) and /api/me; leaves /, /sign-in(.*), /sign-up(.*)
// public. Anything not in the public list AND matching the matcher below is
// gated — unauthenticated requests to protected routes redirect to /sign-in
// (Clerk's default behaviour when auth.protect() is called).
//
// References:
//   - https://clerk.com/docs/references/nextjs/clerk-middleware
//   - threat register T-01-01 (spoofing /dashboard)
//   - threat register T-01-10 (elevation of privilege — Flask never trusts
//     X-User-Id; this middleware is the FE-side guard, Flask @require_auth
//     is the trust anchor)

import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Phase 6 (Workout Library + PWA): /workouts(.*) is intentionally NOT in
//   the protected route list. The workout library is browseable pre-login
//   as an onboarding incentive (CONTEXT.md D-PUBLIC-WORKOUTS). The Clerk
//   middleware default-public behaviour applies; no edit to
//   isProtectedRoute is needed. T-01-01 inheritance (Phase 1 middleware
//   threat model) still applies for /dashboard + /api/*.

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/onboarding(.*)",
  "/profile(.*)",
  "/settings(.*)",
  "/history(.*)",
  "/api/me(.*)",
  "/api/profile(.*)",
  "/api/weights(.*)",
  "/api/account(.*)",
  "/api/foods(.*)",
  "/api/meals(.*)",
  // Phase 4 — /api/meals(.*) already covers /api/meals/scan; corrections
  // + scan-budget are top-level BFF routes that need explicit gating.
  "/api/corrections(.*)",
  "/api/scan-budget(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files unless found in search params.
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes.
    "/(api|trpc)(.*)",
  ],
};
