"use client";

// Phase 6 P6-C.4 — service-worker registration + offline-meal-queue drain.
//
// Mounted once at the root of the app (in layout.tsx). On mount, in
// production only, registers /sw.js. ALSO subscribes to window 'online'
// so reconnects automatically drain queued meal POSTs. Renders null.
//
// Production-only gating matches the `disable: NODE_ENV==='development'`
// in next.config.ts — the SW is not bundled into the dev build, so
// attempting register() in dev would fail and noisily log.

import { useEffect } from "react";
import { drainMealQueue } from "./offline-meal-queue";

export function RegisterSW() {
  useEffect(() => {
    if (typeof window === "undefined") return;

    if (
      "serviceWorker" in navigator &&
      process.env.NODE_ENV === "production"
    ) {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/" })
        .catch((err) => {
          // Failure here is non-fatal — the app still works without SW.
          console.warn("[RegisterSW] /sw.js registration failed:", err);
        });
    }

    const onOnline = () => {
      void drainMealQueue();
    };
    window.addEventListener("online", onOnline);
    return () => {
      window.removeEventListener("online", onOnline);
    };
  }, []);

  return null;
}
