import type { Metadata } from "next";
import Link from "next/link";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { Toaster } from "@/components/ui/sonner";
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
          <div className="flex-1">{children}</div>
          {/* Global footer — AUTH-05: a /privacy link must be reachable
              from every page. Phase 7 LEGAL-02 will expand this. */}
          <footer className="border-t bg-muted/30 px-6 py-3 text-xs text-muted-foreground">
            <div className="mx-auto flex max-w-2xl items-center justify-between">
              <span>© FitGH</span>
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
