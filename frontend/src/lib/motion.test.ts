// Vitest tests for the motion preference helper.
// Phase 5 Plan 05 (P5-D.3).

import { afterEach, describe, expect, it, vi } from "vitest";
import { detectMotionPreference } from "./motion";

const originalMatchMedia = window.matchMedia;

afterEach(() => {
  window.matchMedia = originalMatchMedia;
  // Clean up any spoofed connection.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete (navigator as any).connection;
});

function stubMatchMedia(reduceMatches: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query.includes("reduce") && reduceMatches,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
    onchange: null,
  }));
}

function stubConnection(value: {
  effectiveType?: string;
  saveData?: boolean;
}) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (navigator as any).connection = {
    ...value,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
}

describe("detectMotionPreference", () => {
  it("returns all-false when neither media nor connection signal", () => {
    stubMatchMedia(false);
    const r = detectMotionPreference();
    expect(r).toEqual({
      reduced: false,
      slowConnection: false,
      motionDisabled: false,
    });
  });

  it("flags reduced when prefers-reduced-motion matches", () => {
    stubMatchMedia(true);
    const r = detectMotionPreference();
    expect(r.reduced).toBe(true);
    expect(r.motionDisabled).toBe(true);
  });

  it("flags slowConnection when effectiveType is 2g", () => {
    stubMatchMedia(false);
    stubConnection({ effectiveType: "2g" });
    const r = detectMotionPreference();
    expect(r.slowConnection).toBe(true);
    expect(r.motionDisabled).toBe(true);
  });

  it("flags slowConnection when effectiveType is slow-2g", () => {
    stubMatchMedia(false);
    stubConnection({ effectiveType: "slow-2g" });
    expect(detectMotionPreference().slowConnection).toBe(true);
  });

  it("flags slowConnection when effectiveType is 3g", () => {
    stubMatchMedia(false);
    stubConnection({ effectiveType: "3g" });
    expect(detectMotionPreference().slowConnection).toBe(true);
  });

  it("does NOT flag slowConnection for 4g or 5g", () => {
    stubMatchMedia(false);
    stubConnection({ effectiveType: "4g" });
    expect(detectMotionPreference().slowConnection).toBe(false);
    stubConnection({ effectiveType: "5g" });
    expect(detectMotionPreference().slowConnection).toBe(false);
  });

  it("flags slowConnection when saveData=true regardless of type", () => {
    stubMatchMedia(false);
    stubConnection({ effectiveType: "4g", saveData: true });
    expect(detectMotionPreference().slowConnection).toBe(true);
  });

  it("any single signal flips motionDisabled to true", () => {
    stubMatchMedia(true);
    stubConnection({ effectiveType: "4g" });
    expect(detectMotionPreference().motionDisabled).toBe(true);
  });
});
