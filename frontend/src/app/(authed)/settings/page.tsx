// /settings — Phase 2 Plan 02 (P2-E.2) + Phase 7 P7-B.1 + P7-C.3.
//
// Auth-protected by middleware.ts. The Data section (P7-B.1, LEGAL-01 link
// target #3 + P7-C.3, LEGAL-02 export UI) sits between the page header and
// the Danger zone.

import Link from "next/link";
import { DeleteAccountButton } from "./delete-account-button";

export const dynamic = "force-dynamic";

export default function SettingsPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-lg flex-col gap-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage your FitGH account.
        </p>
      </header>

      {/* Data section — Phase 7 P7-B.1 + P7-C.3. */}
      <section className="flex flex-col gap-3 rounded-lg border bg-muted/20 p-4">
        <h2 className="text-base font-semibold">Data</h2>
        <p className="text-sm text-muted-foreground">
          Review how we handle your data, or export a copy for your records.
        </p>
        <div className="flex flex-col gap-2 text-sm">
          <Link
            href="/privacy"
            className="underline-offset-4 hover:underline"
          >
            Privacy policy
          </Link>
        </div>
      </section>

      <section className="flex flex-col gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4">
        <h2 className="text-base font-semibold">Danger zone</h2>
        <p className="text-sm text-muted-foreground">
          Permanently delete your FitGH profile, weight history, and Clerk
          account. This action cannot be undone.
        </p>
        <DeleteAccountButton />
      </section>
    </main>
  );
}
