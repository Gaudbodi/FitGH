// /privacy — Phase 7 P7-B.1 (LEGAL-01).
//
// Real privacy policy replacing the Phase 2 stub. 6 numbered sections per
// CONTEXT.md template: (1) what we collect, (2) what we don't keep,
// (3) sub-processors, (4) user rights, (5) contact, (6) last updated.
//
// Header carries an amber-bordered disclaimer card: "not been reviewed by
// counsel." Anchor links at the top jump to §1..§6.
//
// The 5 sub-processors named are Anthropic (Claude Sonnet 4.6) / Clerk /
// MongoDB Atlas / Render / GitHub Actions (nightly mongodump backup). NOT
// Cloudflare R2 — R2 is not used in v1.0 (DATA-01 implements backups via
// GH Actions artifact storage with 90-day retention).

import Link from "next/link";

export const metadata = {
  title: "Privacy Policy — FitGH",
  description:
    "FitGH privacy policy: what we collect, what we don't keep, our sub-processors, and your rights.",
};

export default function PrivacyPage() {
  return (
    <main className="prose prose-sm md:prose-base mx-auto w-full max-w-3xl px-6 py-10">
      <header className="not-prose mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">
          FitGH Privacy Policy
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Last updated: 2026-05-13
        </p>
        <div
          role="note"
          className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-100"
        >
          <strong>Disclaimer:</strong> This privacy policy is provided in good
          faith but has not been reviewed by counsel. Review with a lawyer
          before commercial launch.
        </div>
        <nav aria-label="On this page" className="mt-6 text-sm">
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
            <li>
              <a href="#section-1" className="underline-offset-4 hover:underline">
                1. What we collect
              </a>
            </li>
            <li>
              <a href="#section-2" className="underline-offset-4 hover:underline">
                2. What we don&apos;t keep
              </a>
            </li>
            <li>
              <a href="#section-3" className="underline-offset-4 hover:underline">
                3. Sub-processors
              </a>
            </li>
            <li>
              <a href="#section-4" className="underline-offset-4 hover:underline">
                4. Your rights
              </a>
            </li>
            <li>
              <a href="#section-5" className="underline-offset-4 hover:underline">
                5. Contact
              </a>
            </li>
            <li>
              <a href="#section-6" className="underline-offset-4 hover:underline">
                6. Updates
              </a>
            </li>
          </ul>
        </nav>
      </header>

      <section id="section-1">
        <h2>1. What we collect</h2>
        <p>
          FitGH stores only the information we need to deliver the snap-a-meal
          calorie loop and the daily-target dashboard. Specifically:
        </p>
        <ul>
          <li>
            <strong>Identity</strong> — your email address and the OAuth
            tokens issued by your sign-in provider (Google or Apple) when you
            sign up. This is held by our authentication provider Clerk, not
            in our own database.
          </li>
          <li>
            <strong>Profile</strong> — your name, sex, height, weight, age,
            timezone, locale, activity level, and primary goal. You give us
            these during onboarding.
          </li>
          <li>
            <strong>Meal logs</strong> — for every meal you log, we keep its
            estimated total kcal, the list of components (e.g. &quot;jollof
            rice&quot;, &quot;grilled chicken&quot;), each component&apos;s
            portion size, and the timestamp you logged it.
          </li>
          <li>
            <strong>Weight logs</strong> — each weight entry you record, with
            its timestamp.
          </li>
          <li>
            <strong>Meal photos (transient)</strong> — when you snap a meal,
            the image bytes are sent to our vision provider for kcal
            estimation and then discarded. See §2.
          </li>
          <li>
            <strong>Corrections</strong> — when you edit the AI&apos;s kcal
            estimate, we record your correction so we can improve future
            estimates for similar meals.
          </li>
        </ul>
      </section>

      <section id="section-2">
        <h2>2. What we don&apos;t keep</h2>
        <p>
          <strong>Meal images.</strong> The bytes of every meal photo you
          take are sent to Anthropic&apos;s Claude Sonnet 4.6 vision model
          for kcal estimation and then discarded server-side. We do not
          store them in our database, in a blob store, in a CDN, or in our
          application logs. The only copy that survives the request is the
          one on your own device.
        </p>
        <p>
          <strong>Tracking pixels, advertising IDs, or third-party
          analytics.</strong> FitGH v1.0 ships with neither Sentry nor any
          analytics SDK on the frontend.
        </p>
      </section>

      <section id="section-3">
        <h2>3. Sub-processors</h2>
        <p>
          We use the following third-party services to operate FitGH. Each
          one sees only the data flow listed beside it.
        </p>
        <ul>
          <li>
            <strong>Anthropic (Claude Sonnet 4.6)</strong> — receives the
            base64-encoded bytes of each meal photo you snap, plus the
            Ghana-food calibration table we send as system context, and
            returns the kcal estimate and component list. Anthropic&apos;s
            data-retention policy applies to its side of the call; we do
            not retain the image bytes once the response comes back. See{" "}
            <a
              href="https://www.anthropic.com/legal"
              rel="noopener noreferrer"
              target="_blank"
            >
              Anthropic&apos;s legal policies
            </a>
            .
          </li>
          <li>
            <strong>Clerk</strong> — holds your authentication identity
            (email address, OAuth tokens, session tokens). FitGH never sees
            your password. Clerk operates as our identity provider. See{" "}
            <a
              href="https://clerk.com/privacy"
              rel="noopener noreferrer"
              target="_blank"
            >
              Clerk&apos;s privacy policy
            </a>
            .
          </li>
          <li>
            <strong>MongoDB Atlas</strong> — stores your profile, weight
            history, meal logs, and corrections in a hosted MongoDB cluster.
            Each user&apos;s data is keyed by their Clerk user ID. See{" "}
            <a
              href="https://www.mongodb.com/legal/privacy/privacy-policy"
              rel="noopener noreferrer"
              target="_blank"
            >
              MongoDB&apos;s privacy policy
            </a>
            .
          </li>
          <li>
            <strong>Render</strong> — hosts both the FitGH web application
            and the Flask API backend. Render holds the application&apos;s
            ephemeral logs (request method + path + status code, NO request
            bodies and NO meal images). See{" "}
            <a
              href="https://render.com/privacy"
              rel="noopener noreferrer"
              target="_blank"
            >
              Render&apos;s privacy policy
            </a>
            .
          </li>
          <li>
            <strong>GitHub Actions</strong> — runs the nightly{" "}
            <code>mongodump</code> backup job. The encrypted dump is stored
            as a GitHub Actions artifact with a 90-day retention period and
            is accessible only to the operator. Re-importable in case of
            data loss.
          </li>
        </ul>
      </section>

      <section id="section-4">
        <h2>4. Your rights</h2>
        <p>
          You can export and delete your data at any time from your{" "}
          <Link href="/settings" className="underline">
            account settings
          </Link>
          .
        </p>
        <ul>
          <li>
            <strong>Export</strong> — click &quot;Download my data
            (JSON)&quot; in /settings. The download contains your profile,
            every weight log, every meal log with components, every
            correction you&apos;ve submitted, and a usage-count summary of
            your vision API calls. No meal images (we don&apos;t retain
            them).
          </li>
          <li>
            <strong>Delete</strong> — click &quot;Delete account&quot; in
            /settings. This cascades: your MongoDB profile, weight logs,
            meals, and corrections are removed; your Clerk auth record is
            removed; the operation is irreversible.
          </li>
        </ul>
      </section>

      <section id="section-5">
        <h2>5. Contact</h2>
        <p>
          Questions, data-correction requests, or concerns about this
          policy? Email{" "}
          <a href="mailto:francisyiryel@gmail.com" className="underline">
            francisyiryel@gmail.com
          </a>
          .
        </p>
      </section>

      <section id="section-6">
        <h2>6. Updates</h2>
        <p>
          We&apos;ll update this page when our data flows change. The
          &quot;Last updated&quot; date at the top of the page is the
          source of truth. Material changes (a new sub-processor, a change
          in what we retain) will also surface in-app the next time you
          sign in.
        </p>
      </section>
    </main>
  );
}
