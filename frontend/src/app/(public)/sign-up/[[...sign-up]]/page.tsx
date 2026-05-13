// Sign-up route — Phase 1 Walking Skeleton (WS-D.2).
// Clerk-hosted sign-up widget. The catch-all `[[...sign-up]]` segment lets
// Clerk handle its own internal sub-routes (verify email, OAuth callback, etc.).

import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <SignUp />
    </main>
  );
}
