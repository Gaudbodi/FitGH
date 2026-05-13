"use client";

// Phase 6 P6-C.4 — Chrome 'beforeinstallprompt' capture + dismissable
// install banner. Shown ONLY on /dashboard (the meal-snap home, highest-
// engagement context) and ONLY if the user hasn't dismissed it before.
//
// localStorage flag 'fitgh.install-dismissed' = '1' suppresses the banner
// permanently for that browser profile (good-citizen UX — don't nag).

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const DISMISS_KEY = "fitgh.install-dismissed";

export function InstallPrompt() {
  const pathname = usePathname();
  const [event, setEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(true); // default true → hidden
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setDismissed(localStorage.getItem(DISMISS_KEY) === "1");

    const handler = (e: Event) => {
      e.preventDefault();
      setEvent(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => {
      window.removeEventListener("beforeinstallprompt", handler);
    };
  }, []);

  if (!mounted) return null;
  if (pathname !== "/dashboard") return null;
  if (dismissed) return null;
  if (!event) return null;

  const onInstall = async () => {
    await event.prompt();
    setEvent(null);
  };

  const onDismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="fixed bottom-4 left-1/2 z-40 -translate-x-1/2 rounded-lg border bg-card px-4 py-3 text-sm shadow-lg flex items-center gap-3">
      <span>Install FitGH for offline workouts and faster meal logging</span>
      <button
        type="button"
        onClick={onInstall}
        className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700"
      >
        Install
      </button>
      <button
        type="button"
        onClick={onDismiss}
        className="text-xs text-muted-foreground hover:text-foreground"
      >
        Dismiss
      </button>
    </div>
  );
}
