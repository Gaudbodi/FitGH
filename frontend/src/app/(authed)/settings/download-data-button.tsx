"use client";

// DownloadDataButton — Phase 7 P7-C.3 (LEGAL-02).
//
// Fetches GET /api/account/export, reads the response as a Blob, parses the
// upstream Content-Disposition filename, and triggers a browser download
// via an anchor.click() against a createObjectURL. Toast feedback on
// success/failure. Disables the button while the request is in flight and
// announces aria-busy for screen readers.

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

function _parseFilenameFromContentDisposition(
  header: string | null,
): string | null {
  if (!header) return null;
  // Handles: attachment; filename="..."  (and an optional filename*=UTF-8'')
  const match = /filename\s*=\s*"?([^"';]+)"?/i.exec(header);
  return match ? match[1] : null;
}

export default function DownloadDataButton() {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/account/export", {
        method: "GET",
        credentials: "same-origin",
      });
      if (!response.ok) {
        throw new Error(`Export failed (${response.status})`);
      }
      const blob = await response.blob();
      const fallbackFilename = `fitgh-export-${new Date().toISOString().slice(0, 10)}.json`;
      const filename =
        _parseFilenameFromContentDisposition(
          response.headers.get("Content-Disposition"),
        ) ?? fallbackFilename;

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      // Revoke after a tick so Safari has had time to read the URL.
      setTimeout(() => URL.revokeObjectURL(url), 1000);

      toast.success("Your data has started downloading.");
    } catch (e) {
      // Swallow the specific error and surface a generic message — we
      // don't want to leak server-side state to the toast.
      console.error("[/api/account/export] failed:", e);
      toast.error("Could not export your data. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      type="button"
      variant="outline"
      onClick={handleClick}
      disabled={isLoading}
      aria-busy={isLoading}
    >
      {isLoading ? "Preparing…" : "Download my data (JSON)"}
    </Button>
  );
}
