import type { Metadata } from "next";
import { Inter } from "next/font/google";
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased font-sans`}>
        {children}
      </body>
    </html>
  );
}
