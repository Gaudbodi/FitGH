// Sign-in route — Phase 1 Walking Skeleton (WS-D.2).
// Clerk-hosted sign-in widget. The catch-all `[[...sign-in]]` segment lets
// Clerk handle its own internal sub-routes (verify email, factor-two, etc.).
//
// Theming: Phase 1 uses Clerk defaults; Phase 5 (Rive avatar + design system)
// will customize via the `appearance` prop.
//
// ClerkProvider is scoped to this page (not the root layout) so /, /workouts,
// /privacy don't pay the Clerk script cost (PERF-03). Clerk's <SignIn />
// component needs a ClerkProvider ancestor — it doesn't self-bootstrap from
// the env var alone.

import { ClerkProvider, SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <ClerkProvider>
      <main className="flex min-h-screen items-center justify-center p-6">
        <SignIn />
      </main>
    </ClerkProvider>
  );
}
