// /settings — Phase 2 Plan 02 (P2-E.2).
//
// Auth-protected by middleware.ts. v1 has only one setting: delete account.

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
