import type { Metadata } from "next";
import Link from "next/link";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { ServicePausedBanner } from "@/components/service-paused-banner";
import { Toaster } from "@/components/ui/sonner";
import { RegisterSW } from "@/components/pwa/register-sw";
import { OfflineIndicator } from "@/components/pwa/offline-indicator";
import { InstallPrompt } from "@/components/pwa/install-prompt";
import "./globals.css";

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

// ClerkProvider reads NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY
// from env automatically (WS-D.1). Server components inside this tree call
// auth() to read the session JWT; client components call useUser().
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${inter.variable} antialiased font-sans flex min-h-screen flex-col`}>
          {/* Phase 4 — site-wide banner when global $/day cap is reached.
              Server component; renders null for unsigned-in users or when
              under cap (no extra JS shipped to the client). */}
          <ServicePausedBanner />
          {/* Phase 6 PWA primitives — RegisterSW + OfflineIndicator render
              null when idle; InstallPrompt only renders on /dashboard
              when Chrome surfaces beforeinstallprompt. */}
          <RegisterSW />
          <OfflineIndicator />
          <InstallPrompt />
          <div className="flex-1">{children}</div>
          {/* Global footer — AUTH-05: a /privacy link must be reachable
              from every page. Phase 6 WORK-07 adds the Free Exercise DB
              attribution alongside. Phase 7 LEGAL-02 may expand further. */}
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
              <Link href="/privacy" className="underline-offset-4 hover:underline">
                Privacy
              </Link>
            </div>
          </footer>
          <Toaster richColors closeButton position="top-right" />
        </body>
      </html>
    </ClerkProvider>
  );
}
