"use client";

// DeleteAccountButton — Phase 2 Plan 02 (P2-E.2).
//
// Renders the destructive button + shadcn Dialog confirmation with a typed
// "DELETE" gate. On confirm: DELETE /api/account -> if 200, useClerk()
// signOut() -> push /sign-in. On 502 clerk_delete_failed: show inline
// error and DO NOT sign the user out (data is gone but Clerk auth is
// still valid; let them retry).

import { useState } from "react";
import { useClerk } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function DeleteAccountButton() {
  const { signOut } = useClerk();
  const [open, setOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canConfirm = confirmText === "DELETE" && !submitting;

  const onConfirm = async () => {
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/account", { method: "DELETE" });
      if (res.status === 200) {
        // Mongo data + Clerk auth record both gone. Clear the local
        // Clerk session and land on /sign-in.
        await signOut({ redirectUrl: "/sign-in" });
        return;
      }
      if (res.status === 502) {
        const body = (await res.json().catch(() => ({}))) as {
          error?: string;
          mongo_deleted?: boolean;
        };
        setError(
          body.mongo_deleted
            ? "Your FitGH data was deleted, but auth deletion failed. Contact support@fitgh.app to finish — you can also retry by clicking Delete account again."
            : (body.error ?? "Account deletion partially failed."),
        );
        setSubmitting(false);
        return;
      }
      const text = await res.text();
      setError(`Request failed (${res.status}): ${text}`);
      setSubmitting(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <>
      <Button
        type="button"
        variant="destructive"
        onClick={() => {
          setOpen(true);
          setConfirmText("");
          setError(null);
        }}
      >
        Delete account
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger className="hidden" />
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Permanently delete your account?</DialogTitle>
            <DialogDescription>
              This will delete your FitGH profile, weight history, and Clerk
              account in one go. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <Label htmlFor="delete-confirm">
              Type <strong>DELETE</strong> to confirm
            </Label>
            <Input
              id="delete-confirm"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="DELETE"
              autoComplete="off"
            />
            {error ? (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={onConfirm}
              disabled={!canConfirm}
            >
              {submitting ? "Deleting…" : "Delete account"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
