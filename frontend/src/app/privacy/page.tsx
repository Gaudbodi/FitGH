// /privacy — Phase 2 Plan 02 (P2-E.1).
//
// Static server component. Stub disclosure linked from onboarding screen 3
// and from the global footer in layout.tsx. AUTH-05 success criterion.
//
// Real Privacy Policy copy (LEGAL-02) is Phase 7 work.

import Link from "next/link";

export const metadata = {
  title: "Privacy disclosure — FitGH",
  description:
    "FitGH privacy disclosure naming the data processors used in v1.",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-6 p-6 leading-relaxed">
      <header>
        <h1 className="text-2xl font-semibold">
          FitGH Privacy Disclosure — v1 (stub)
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This is a Phase 2 stub. The full Privacy Policy is Phase 7 work.
          The processor list below is real and reflects who actually sees
          your data today.
        </p>
      </header>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Data processors</h2>
        <ul className="flex flex-col gap-3 text-sm">
          <li>
            <strong>Anthropic (Claude Sonnet 4.6)</strong> — when you snap a
            meal photo, FitGH sends the image to Anthropic&apos;s vision API
            so it can estimate kcal against a Ghanaian-food calibration
            table. Meal photos are NOT retained server-side beyond the
            time needed for the kcal estimate (this becomes true in
            Phase 4 when the snap-meal loop ships; Phase 2 does not send
            any photos yet, but the consent stance is fixed now).
          </li>
          <li>
            <strong>Clerk</strong> — handles your sign-in identity, email,
            and authentication methods.
          </li>
          <li>
            <strong>MongoDB Atlas</strong> — stores your profile, weight
            history, and (from Phase 3) meal logs.
          </li>
          <li>
            <strong>Render</strong> — hosts the FitGH frontend and backend
            services.
          </li>
        </ul>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">What we don&apos;t do</h2>
        <ul className="flex flex-col gap-1 text-sm">
          <li>
            We do <strong>not</strong> retain meal images server-side beyond
            the time required to call the vision model (effective Phase 4).
          </li>
          <li>
            We do <strong>not</strong> share your data with advertisers or
            data brokers.
          </li>
          <li>
            We do <strong>not</strong> sell your data.
          </li>
        </ul>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Data requests</h2>
        <p className="text-sm">
          You can delete your account (which cascades to all FitGH data plus
          your Clerk auth record) from{" "}
          <Link href="/settings" className="underline">
            /settings
          </Link>
          . For other data requests, email{" "}
          <a
            href="mailto:privacy@fitgh.app"
            className="underline"
          >
            privacy@fitgh.app
          </a>
          .
        </p>
      </section>

      <footer className="mt-4 text-xs text-muted-foreground">
        <Link href="/dashboard" className="underline-offset-4 hover:underline">
          ← Back to dashboard
        </Link>
      </footer>
    </main>
  );
}
