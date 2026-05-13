"use client";

// Sign-out button — Phase 1 Walking Skeleton (WS-D.3).
//
// Wraps Clerk's <SignOutButton> around a shadcn Button. After sign-out,
// Clerk redirects to /sign-in (Clerk's `redirectUrl` prop).
//
// Threat register T-01-01: middleware.ts already protects /dashboard, so
// a hard refresh after sign-out rounds-trips through Clerk's session check
// and lands the user on /sign-in.

import { SignOutButton as ClerkSignOutButton } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";

export function SignOutButton() {
  return (
    <ClerkSignOutButton redirectUrl="/sign-in">
      <Button variant="outline">Sign out</Button>
    </ClerkSignOutButton>
  );
}
