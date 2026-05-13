// (authed) route group — Phase 7 P7-A.1.
//
// Owns <ClerkProvider> (relocated from the root layout per PERF-03 fix).
// Hosts /dashboard, /profile, /settings, /onboarding, /history. The PWA
// primitives — RegisterSW, OfflineIndicator, InstallPrompt — live here
// because they only matter for signed-in users posting meals (the offline
// meal POST queue is the use case driving them).
//
// middleware.ts already gates these paths via isProtectedRoute — no
// behavioural change, just relocation. URL paths are unchanged: route
// groups strip the parenthesized segment.

import { ClerkProvider } from "@clerk/nextjs";
import { RegisterSW } from "@/components/pwa/register-sw";
import { OfflineIndicator } from "@/components/pwa/offline-indicator";
import { InstallPrompt } from "@/components/pwa/install-prompt";

export default function AuthedLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <RegisterSW />
      <OfflineIndicator />
      <InstallPrompt />
      {children}
    </ClerkProvider>
  );
}
