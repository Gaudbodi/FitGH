import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { SignOutButton } from "@/components/sign-out-button";

// /dashboard — Phase 1 Walking Skeleton (WS-D.3).
//
// Server component. Calls the BFF /api/me with the inbound cookie so the
// Clerk session is forwarded; reads {email} from the JSON; renders it next
// to the avatar placeholder + a Sign Out button.
//
// Auth gating is double-belted:
//   1) middleware.ts protects /dashboard via auth.protect() before this
//      component renders.
//   2) /api/me 401 -> redirect('/sign-in') below.
//
// Performance: this adds one same-process BFF -> Flask hop. The BFF route
// has reuse value in Phase 2+ (client-side onboarding form, weight log)
// where calling Flask directly would expose the Clerk JWT to the browser.
export default async function DashboardPage() {
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host");

  // Build the same-origin absolute URL. Server components in Next.js 15
  // require absolute URLs for fetch; headers() gives us the deployment host.
  const res = await fetch(`${proto}://${host}/api/me`, {
    headers: { cookie: h.get("cookie") ?? "" },
    cache: "no-store",
  });

  if (res.status === 401) {
    redirect("/sign-in");
  }

  let email: string | undefined;
  if (res.ok) {
    const data = (await res.json()) as { email?: string };
    email = data.email;
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>FitGH Dashboard</CardTitle>
          <CardDescription>
            {email
              ? `Signed in as ${email}`
              : "Signed in — finishing account setup…"}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <Avatar>
              {/* Static SVG placeholder for the Rive avatar — Phase 5 wires
                  the real .riv runtime + state machine. Avoiding
                  @rive-app/* import here keeps the bundle small. */}
              <AvatarFallback aria-label="Avatar placeholder">FG</AvatarFallback>
            </Avatar>
            <p className="text-sm text-muted-foreground">
              Phase 1 walking skeleton — every later feature (profile, kcal
              tracking, vision, workouts) hangs off this proven auth + DB
              round-trip.
            </p>
          </div>
          <SignOutButton />
        </CardContent>
      </Card>
    </main>
  );
}
