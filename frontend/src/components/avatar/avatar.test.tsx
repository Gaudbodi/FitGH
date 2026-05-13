// Vitest tests for the Avatar component + pure state helpers.
// Phase 5 Plan 05 (P5-B.2).

import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import type { ProfileResponse, WeightLogResponse } from "@/lib/zod-schemas";
import {
  bmiBand,
  goalDirection,
  avatarStateKey,
  SHIPPED_STATES,
} from "./avatar-state";
import { Avatar } from "./avatar";

// ---------------------------------------------------------------------------
// bmiBand
// ---------------------------------------------------------------------------

describe("bmiBand", () => {
  it("classifies under 18.5 as slim", () => {
    // 50 kg / 1.7^2 = 17.3
    expect(bmiBand(50, 170)).toBe("slim");
  });

  it("classifies 18.5 boundary as healthy-lean", () => {
    // BMI exactly 18.5 -> healthy-lean (inclusive lower)
    const kg = 18.5 * 1.7 * 1.7; // 53.465
    expect(bmiBand(kg, 170)).toBe("healthy-lean");
  });

  it("classifies 24.99 as healthy-lean", () => {
    // BMI 24.99 -> healthy-lean (< 25.0 cutoff)
    const kg = 24.99 * 1.7 * 1.7;
    expect(bmiBand(kg, 170)).toBe("healthy-lean");
  });

  it("classifies 25.0 as healthy-firm", () => {
    const kg = 25.0 * 1.7 * 1.7;
    expect(bmiBand(kg, 170)).toBe("healthy-firm");
  });

  it("classifies 27.99 as healthy-firm", () => {
    const kg = 27.99 * 1.7 * 1.7;
    expect(bmiBand(kg, 170)).toBe("healthy-firm");
  });

  it("classifies 28.0 as heavier", () => {
    const kg = 28.0 * 1.7 * 1.7;
    expect(bmiBand(kg, 170)).toBe("heavier");
  });

  it("classifies 32+ as much-heavier", () => {
    const kg = 32.0 * 1.7 * 1.7;
    expect(bmiBand(kg, 170)).toBe("much-heavier");
  });

  it("is defensive against zero height", () => {
    expect(bmiBand(70, 0)).toBe("healthy-lean");
  });
});

// ---------------------------------------------------------------------------
// goalDirection
// ---------------------------------------------------------------------------

const ONE_WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const NOW = new Date("2026-05-13T12:00:00Z").getTime();

function fakeWeights(...kgs: number[]): WeightLogResponse[] {
  // Newest first — entry 0 is "now", subsequent entries are 1 week back each.
  return kgs.map((kg, i) => ({
    user_id: "user_x",
    kg,
    logged_at: new Date(NOW - i * ONE_WEEK_MS).toISOString(),
  }));
}

describe("goalDirection", () => {
  it("returns steady on empty array", () => {
    expect(goalDirection("weight_loss", [])).toBe("steady");
  });

  it("returns steady on single entry", () => {
    expect(goalDirection("weight_loss", fakeWeights(80))).toBe("steady");
  });

  it("weight_loss with negative slope is toward", () => {
    // newest=78, oldest=80 (1 wk back) -> slope = (78-80)/1 = -2 kg/wk
    expect(goalDirection("weight_loss", fakeWeights(78, 80))).toBe("toward");
  });

  it("weight_loss with positive slope is away", () => {
    expect(goalDirection("weight_loss", fakeWeights(82, 80))).toBe("away");
  });

  it("muscle_gain with positive slope is toward", () => {
    expect(goalDirection("muscle_gain", fakeWeights(82, 80))).toBe("toward");
  });

  it("muscle_gain with negative slope is away", () => {
    expect(goalDirection("muscle_gain", fakeWeights(78, 80))).toBe("away");
  });

  it("returns steady when |slope| <= 0.1 kg/wk", () => {
    // 80.05 vs 80.0 over 1 week -> slope ~0.05 kg/wk
    expect(goalDirection("weight_loss", fakeWeights(80.05, 80.0))).toBe(
      "steady",
    );
  });
});

// ---------------------------------------------------------------------------
// avatarStateKey
// ---------------------------------------------------------------------------

describe("avatarStateKey", () => {
  it("concatenates sex-bmi-direction correctly for female weight_loss toward", () => {
    // weight=55, height=165 -> BMI = 55 / 1.65^2 = 20.2 -> healthy-lean
    const profile = {
      sex: "female" as const,
      weight_kg: 55,
      height_cm: 165,
      primary_goal: "weight_loss" as const,
    };
    // Descending weights (newest first) over 1 week -> negative slope -> toward
    const weights = fakeWeights(54, 56);
    expect(avatarStateKey(profile, weights)).toBe("f-healthy-lean-toward");
  });

  it("falls back to a shipped state when the resolved key is missing", () => {
    // m-much-heavier-away is NOT in the shipped sprite. Force that combo.
    // BMI ~36 -> much-heavier; weight_loss with positive slope -> away
    const profile = {
      sex: "male" as const,
      weight_kg: 110,
      height_cm: 175,
      primary_goal: "weight_loss" as const,
    };
    const weights = fakeWeights(110, 108); // gaining -> "away" for weight_loss
    const key = avatarStateKey(profile, weights);
    expect(SHIPPED_STATES.has(key)).toBe(true);
    // Specifically should fall back to m-much-heavier-toward (only shipped
    // m-much-heavier variant).
    expect(key).toBe("m-much-heavier-toward");
  });

  it("never returns an unshipped state key", () => {
    // Enumerate a bunch of combos.
    const sexes: Array<"male" | "female"> = ["male", "female"];
    const heights = [155, 170, 185];
    const weights = [50, 70, 90, 110];
    const goals: Array<"weight_loss" | "muscle_gain"> = [
      "weight_loss",
      "muscle_gain",
    ];
    for (const sex of sexes) {
      for (const h of heights) {
        for (const w of weights) {
          for (const g of goals) {
            const key = avatarStateKey(
              { sex, weight_kg: w, height_cm: h, primary_goal: g },
              fakeWeights(w, w + 1), // some slope
            );
            expect(SHIPPED_STATES.has(key)).toBe(true);
          }
        }
      }
    }
  });
});

// ---------------------------------------------------------------------------
// <Avatar> renders correctly
// ---------------------------------------------------------------------------

function buildProfile(
  overrides: Partial<ProfileResponse> = {},
): ProfileResponse {
  return {
    clerk_id: "user_test",
    name: "Test",
    sex: "female",
    height_cm: 165,
    weight_kg: 60,
    age: 28,
    timezone: "Africa/Accra",
    locale: "ghana",
    activity_level: "moderately_active",
    primary_goal: "weight_loss",
    daily_kcal_target: 1800,
    daily_protein_g_target: null,
    floor_hit: false,
    privacy_consent_at: "2026-05-13T00:00:00Z",
    created_at: "2026-05-13T00:00:00Z",
    updated_at: "2026-05-13T00:00:00Z",
    ...overrides,
  };
}

describe("<Avatar>", () => {
  it("renders a <use> pointing at the sprite for the resolved state", () => {
    const { container } = render(
      <Avatar
        profile={buildProfile()}
        recentWeights={fakeWeights(58, 60)} // toward
      />,
    );
    const useEl = container.querySelector("use");
    expect(useEl).not.toBeNull();
    const href = useEl?.getAttribute("href") ?? "";
    expect(href).toMatch(/\/avatar-sprite\.svg#state-/);
    // newest=58, oldest=60 -> toward for weight_loss; female; BMI ~22 -> healthy-lean
    expect(href).toBe("/avatar-sprite.svg#state-f-healthy-lean-toward");
  });

  it("renders with the default size of 200", () => {
    const { container } = render(
      <Avatar profile={buildProfile()} recentWeights={[]} />,
    );
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("width")).toBe("200");
    expect(svg?.getAttribute("height")).toBe("200");
  });

  it("supports a custom size prop", () => {
    const { container } = render(
      <Avatar profile={buildProfile()} recentWeights={[]} size={120} />,
    );
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("width")).toBe("120");
  });
});
