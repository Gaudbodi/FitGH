// /onboarding — Phase 2 Plan 02 (P2-C.1).
//
// Server component that calls the BFF /api/profile with cookie forwarded;
//   200 -> redirect("/dashboard")     (already onboarded)
//   401 -> redirect("/sign-in")
//   else (404 / 503) -> render <OnboardingFlow/>

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { OnboardingFlow } from "./onboarding-flow";

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host");

  const res = await fetch(`${proto}://${host}/api/profile`, {
    headers: { cookie: h.get("cookie") ?? "" },
    cache: "no-store",
  });

  if (res.status === 200) {
    redirect("/dashboard");
  }
  if (res.status === 401) {
    redirect("/sign-in");
  }
  // 404 (no profile yet) or 503 (api_url_not_configured) -> render the form.
  return <OnboardingFlow />;
}
