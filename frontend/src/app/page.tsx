import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// FitGH landing — Phase 1 Walking Skeleton (WS-D.2).
// Minimal CTA shell pointing at the Clerk-hosted sign-in / sign-up routes.
// Signed-in users typing `/` will see this; we don't auto-redirect because
// `/` is intentionally public per middleware.ts (only /dashboard is gated).
//
// Note: the shadcn Button in this repo wraps @base-ui/react/button and does
// not expose an `asChild` prop. We style Links with `buttonVariants` instead.

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>FitGH</CardTitle>
          <CardDescription>
            Snap a meal, see kcal in seconds, know whether you&apos;re hitting
            your daily target — with food you actually eat.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Link href="/sign-in" className={buttonVariants()}>
            Sign in
          </Link>
          <Link
            href="/sign-up"
            className={buttonVariants({ variant: "outline" })}
          >
            Create an account
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
