// /profile — Phase 2 Plan 02 (P2-D.1).
//
// Server component. Fetches /api/profile; 404 -> /onboarding; 401 ->
// /sign-in; 200 -> renders the client-side ProfileForm with the profile
// as initialValues.

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import type { ProfileResponse } from "@/lib/zod-schemas";
import { ProfileForm } from "./profile-form";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host");

  const res = await fetch(`${proto}://${host}/api/profile`, {
    headers: { cookie: h.get("cookie") ?? "" },
    cache: "no-store",
  });

  if (res.status === 401) redirect("/sign-in");
  if (res.status === 404) redirect("/onboarding");
  if (!res.ok) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <p className="text-sm text-destructive">
          Could not load your profile ({res.status}).
        </p>
      </main>
    );
  }
  const profile = (await res.json()) as ProfileResponse;

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-lg flex-col gap-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">Edit profile</h1>
        <p className="text-sm text-muted-foreground">
          Changes save instantly. Targets recompute on save.
        </p>
      </header>
      <ProfileForm initial={profile} />
    </main>
  );
}
