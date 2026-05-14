// (public) route group — Phase 7 P7-A.1.
//
// Passthrough layout for public routes (/workouts, /workouts/[id], /privacy,
// /, /sign-in, /sign-up). The architectural fix for PERF-03 is precisely
// the absence of <ClerkProvider> here: public-route HTML for /, /workouts,
// and /privacy transfers no accounts.dev script and emits no Clerk-related
// third-party blocking time.
//
// /sign-in and /sign-up DO need a ClerkProvider (the <SignIn /> and <SignUp />
// components require it — they do not self-bootstrap from the env var). To
// keep the perf win for the other public routes, each of those two pages
// mounts ClerkProvider locally inside the page file.

export default function PublicLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <>{children}</>;
}
