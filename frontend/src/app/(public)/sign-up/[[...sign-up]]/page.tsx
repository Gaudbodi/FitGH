// Sign-up route — Phase 1 Walking Skeleton (WS-D.2).
// Clerk-hosted sign-up widget. The catch-all `[[...sign-up]]` segment lets
// Clerk handle its own internal sub-routes (verify email, OAuth callback, etc.).
//
// ClerkProvider is scoped to this page (not the root layout) so /, /workouts,
// /privacy don't pay the Clerk script cost (PERF-03). Clerk's <SignUp />
// component needs a ClerkProvider ancestor — it doesn't self-bootstrap from
// the env var alone.

import { ClerkProvider, SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <ClerkProvider>
      <main className="flex min-h-screen items-center justify-center p-6">
        <SignUp />
      </main>
    </ClerkProvider>
  );
}
