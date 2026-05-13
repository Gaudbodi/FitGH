// Vitest unit tests for the shared kcal-color helper.
// Phase 5 Plan 05 (P5-D.1).

import { describe, expect, it } from "vitest";
import { kcalColorBand, kcalColorClasses } from "@/lib/kcal-color";

describe("kcalColorBand", () => {
  it("0 of 2000 -> green", () => {
    expect(kcalColorBand(0, 2000)).toBe("green");
  });

  it("1799 of 2000 (89.95%) -> green (below 90%)", () => {
    expect(kcalColorBand(1799, 2000)).toBe("green");
  });

  it("1801 of 2000 (90.05%) -> amber", () => {
    expect(kcalColorBand(1801, 2000)).toBe("amber");
  });

  it("2000 of 2000 -> amber (exactly target is not over)", () => {
    expect(kcalColorBand(2000, 2000)).toBe("amber");
  });

  it("2001 of 2000 -> red (over by 1)", () => {
    expect(kcalColorBand(2001, 2000)).toBe("red");
  });

  it("3000 of 2000 -> red (well over)", () => {
    expect(kcalColorBand(3000, 2000)).toBe("red");
  });

  it("defensive: target=0 with consumed>0 -> red", () => {
    expect(kcalColorBand(500, 0)).toBe("red");
  });

  it("defensive: target=0 with consumed=0 -> green", () => {
    expect(kcalColorBand(0, 0)).toBe("green");
  });

  it("defensive: negative target -> red on any positive consumed", () => {
    expect(kcalColorBand(100, -100)).toBe("red");
  });
});

describe("kcalColorClasses", () => {
  it("green returns emerald classes + hex stroke", () => {
    const r = kcalColorClasses("green");
    expect(r.bg).toContain("emerald");
    expect(r.text).toContain("emerald");
    expect(r.stroke).toMatch(/^#[0-9a-f]{6}$/i);
  });

  it("amber returns amber classes + hex stroke", () => {
    const r = kcalColorClasses("amber");
    expect(r.bg).toContain("amber");
    expect(r.text).toContain("amber");
    expect(r.stroke).toMatch(/^#[0-9a-f]{6}$/i);
  });

  it("red returns red classes + hex stroke", () => {
    const r = kcalColorClasses("red");
    expect(r.bg).toContain("red");
    expect(r.text).toContain("red");
    expect(r.stroke).toMatch(/^#[0-9a-f]{6}$/i);
  });
});
