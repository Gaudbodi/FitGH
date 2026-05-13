// Motion preference detector — Phase 5 Plan 05 (P5-D.3).
//
// Pure helper. SSR-safe: returns all-false when window/navigator are
// undefined so server-rendered components can call it without crashing.
//
// Combines three signals:
//   1. prefers-reduced-motion: reduce  (CSS media query)
//   2. navigator.connection.saveData    (Data Saver flag in Chrome/Edge)
//   3. navigator.connection.effectiveType in {2g, slow-2g, 3g}
//
// Any one of those flips `motionDisabled` to true. MotionDetector then
// sets `data-motion="disabled"` on <html>; globals.css collapses every
// transition/animation site-wide.

export interface MotionPreference {
  reduced: boolean;
  slowConnection: boolean;
  motionDisabled: boolean;
}

const SLOW_TYPES = new Set(["2g", "slow-2g", "3g"]);

// Narrow type for the spec'd-but-not-in-lib NetworkInformation API.
interface NetInfo {
  effectiveType?: string;
  saveData?: boolean;
  addEventListener?: (type: string, listener: () => void) => void;
  removeEventListener?: (type: string, listener: () => void) => void;
}

interface NavigatorWithConnection extends Navigator {
  connection?: NetInfo;
  mozConnection?: NetInfo;
  webkitConnection?: NetInfo;
}

function getConnection(): NetInfo | undefined {
  if (typeof navigator === "undefined") return undefined;
  const nav = navigator as NavigatorWithConnection;
  return nav.connection ?? nav.mozConnection ?? nav.webkitConnection;
}

export function detectMotionPreference(): MotionPreference {
  // SSR / Node test runner without window: never disable.
  if (typeof window === "undefined") {
    return { reduced: false, slowConnection: false, motionDisabled: false };
  }
  const reduced =
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const conn = getConnection();
  const saveData = conn?.saveData === true;
  const slowType =
    typeof conn?.effectiveType === "string" &&
    SLOW_TYPES.has(conn.effectiveType);
  const slowConnection = saveData || slowType;
  return {
    reduced,
    slowConnection,
    motionDisabled: reduced || slowConnection,
  };
}

// Re-exports for MotionDetector to wire change listeners.
export function getNetworkInformation(): NetInfo | undefined {
  return getConnection();
}
