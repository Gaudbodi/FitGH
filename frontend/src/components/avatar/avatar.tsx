"use client";

// <Avatar> — Phase 5 Plan 05 (P5-B.2). Renders a single sprite reference
// driven by the profile + recent weight logs. Pure presentation; no fetches.
//
// The sprite is served from `/public/avatar-sprite.svg` so the runtime cost
// of this component is just the <svg><use> wrapper (well under 1 kB).

import type { ProfileResponse, WeightLogResponse } from "@/lib/zod-schemas";
import { avatarStateKey } from "./avatar-state";

export interface AvatarProps {
  profile: ProfileResponse;
  recentWeights: ReadonlyArray<WeightLogResponse>;
  size?: number;
  /** Override the sprite path (mostly for storybook / tests). */
  spriteHref?: string;
}

export function Avatar({
  profile,
  recentWeights,
  size = 200,
  spriteHref = "/avatar-sprite.svg",
}: AvatarProps) {
  // The Phase 2 GET /api/weights contract returns newest-first. Trim to the
  // last 14 entries so the slope helper uses the most-recent fortnight even
  // if the parent fetched the full 90-day window for the chart.
  const window = recentWeights.slice(0, 14);
  const stateKey = avatarStateKey(profile, window);

  return (
    <div className="flex justify-center" data-testid="avatar-wrapper">
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        aria-label={`Avatar reflecting your ${profile.primary_goal === "weight_loss" ? "weight-loss" : "muscle-gain"} progress`}
        role="img"
      >
        <use href={`${spriteHref}#state-${stateKey}`} />
      </svg>
    </div>
  );
}
