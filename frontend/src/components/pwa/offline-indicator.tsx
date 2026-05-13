"use client";

// Phase 6 P6-C.4 — bottom-right amber pill that surfaces when the browser
// reports offline. Hidden when online. Renders a Sonner success toast on
// the false→true transition so the user knows their queued meals are
// about to sync.
//
// SSR-safe: `online` initializes in useEffect (jsdom/SSR has no navigator
// API; reading it during render would NaN the hydration).

import { useEffect, useState } from "react";
import { toast } from "sonner";

export function OfflineIndicator() {
  const [online, setOnline] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setOnline(typeof navigator !== "undefined" ? navigator.onLine : true);

    const onOnline = () => {
      setOnline((prev) => {
        if (!prev) {
          toast.success("Back online — syncing meals...");
        }
        return true;
      });
    };
    const onOffline = () => setOnline(false);

    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  if (!mounted || online) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 rounded-full bg-amber-100 border border-amber-300 text-amber-900 px-3 py-1.5 text-xs font-medium shadow-md">
      Offline — meals will sync on reconnect
    </div>
  );
}
