// (public) route group — Phase 7 P7-A.1.
//
// Passthrough layout for public routes (/workouts, /workouts/[id], /privacy,
// /, /sign-in, /sign-up). The architectural fix for PERF-03 is precisely
// the absence of <ClerkProvider> here: public-route HTML transfers no
// accounts.dev script and emits no Clerk-related third-party blocking time.
//
// Clerk's <SignIn /> and <SignUp /> components self-bootstrap from the
// NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY env var, so the public /sign-in and
// /sign-up pages render correctly without an ancestor ClerkProvider.

export default function PublicLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <>{children}</>;
}
