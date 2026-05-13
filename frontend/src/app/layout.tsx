import type { Metadata } from "next";
import Link from "next/link";
import { Inter } from "next/font/google";
import { ServicePausedBanner } from "@/components/service-paused-banner";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

// Phase 7 P7-A.1 — route-group restructure (PERF-03 carry-over from Phase 6).
//
// The root layout no longer mounts ClerkProvider. Public routes (/workouts,
// /privacy, /, /sign-in, /sign-up) live under (public)/ with a passthrough
// layout and ship NO Clerk client SDK. Authed routes (/dashboard, /profile,
// /settings, /onboarding, /history) live under (authed)/ whose layout owns
// the ClerkProvider plus the PWA primitives (RegisterSW, OfflineIndicator,
// InstallPrompt) — those only matter for signed-in users posting meals.
//
// Per WS-A.3: control caching by pinning to a single subset; Inter is the
// Phase 1 system font (replaces create-next-app's Geist Sans/Mono pair).
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "FitGH",
  description:
    "Snap a meal, see kcal in seconds, know whether you're hitting your daily target — with food the user actually eats.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} antialiased font-sans flex min-h-screen flex-col`}
      >
        {/* Phase 4 — site-wide banner when global $/day cap is reached.
            Server component; renders null for unsigned-in users or when
            under cap (no extra JS shipped to the client). */}
        <ServicePausedBanner />
        <div className="flex-1">{children}</div>
        {/* Global footer — AUTH-05: /privacy reachable from every page.
            Phase 6 WORK-07 — Free Exercise DB attribution.
            Phase 7 LEGAL-03 — standard health-claim disclaimer. */}
        <footer className="border-t bg-muted/30 px-6 py-3 text-xs text-muted-foreground">
          <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2">
            <span>© FitGH</span>
            <span>
              Exercise data from{" "}
              <a
                href="https://github.com/yuhonas/free-exercise-db"
                className="underline-offset-4 hover:underline"
                rel="noopener noreferrer"
                target="_blank"
              >
                Free Exercise DB
              </a>{" "}
              (Unlicense)
            </span>
            <Link
              href="/privacy"
              className="underline-offset-4 hover:underline"
            >
              Privacy
            </Link>
          </div>
          <p className="mx-auto mt-2 max-w-3xl text-center text-[10px] text-muted-foreground/70">
            FitGH is a fitness tracking tool, not medical advice. Consult a
            qualified clinician for health decisions.
          </p>
        </footer>
        <Toaster richColors closeButton position="top-right" />
      </body>
    </html>
  );
}
