// Sign-in route — Phase 1 Walking Skeleton (WS-D.2).
// Clerk-hosted sign-in widget. The catch-all `[[...sign-in]]` segment lets
// Clerk handle its own internal sub-routes (verify email, factor-two, etc.).
//
// Theming: Phase 1 uses Clerk defaults; Phase 5 (Rive avatar + design system)
// will customize via the `appearance` prop.

import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <SignIn />
    </main>
  );
}
