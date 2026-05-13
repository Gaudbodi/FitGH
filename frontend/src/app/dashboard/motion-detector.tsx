"use client";

// MotionDetector — Phase 5 Plan 05 (P5-D.3).
//
// Renders nothing. On mount: read `detectMotionPreference()` and toggle
// `data-motion="disabled"` on <html>. Subscribes to matchMedia 'change' and
// navigator.connection 'change' so the attribute stays in sync if the user
// toggles their OS preference or their network shifts.

import { useEffect } from "react";
import {
  detectMotionPreference,
  getNetworkInformation,
} from "@/lib/motion";

export function MotionDetector() {
  useEffect(() => {
    const root = document.documentElement;

    const update = () => {
      const { motionDisabled } = detectMotionPreference();
      if (motionDisabled) {
        root.dataset.motion = "disabled";
      } else {
        delete root.dataset.motion;
      }
    };

    // Initial sync (also runs on every dependency change which has none).
    update();

    let mediaQuery: MediaQueryList | null = null;
    if (typeof window.matchMedia === "function") {
      mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      mediaQuery.addEventListener("change", update);
    }

    const conn = getNetworkInformation();
    conn?.addEventListener?.("change", update);

    return () => {
      mediaQuery?.removeEventListener("change", update);
      conn?.removeEventListener?.("change", update);
    };
  }, []);

  return null;
}
