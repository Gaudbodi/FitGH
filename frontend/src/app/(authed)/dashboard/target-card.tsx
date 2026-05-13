// TargetCard — Phase 2 Plan 02 (P2-C.3).
//
// Server component, no interactivity. Shows daily_kcal_target as a large
// number; the optional protein card renders only on muscle_gain (per the
// must_have "weight-loss users do not see the protein card"). Floor
// disclaimer renders when profile.floor_hit === true.
//
// Phase 5 will replace the static progress placeholder with the Rive ring.

import type { ProfileResponse } from "@/lib/zod-schemas";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface TargetCardProps {
  profile: ProfileResponse;
}

export function TargetCard({ profile }: TargetCardProps) {
  const showProtein =
    profile.primary_goal === "muscle_gain" && profile.daily_protein_g_target !== null;
  const floorValue = profile.sex === "female" ? 1200 : 1500;

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Daily target</CardTitle>
          <CardDescription>
            Computed from Mifflin-St Jeor BMR x activity factor with a{" "}
            {profile.primary_goal === "weight_loss"
              ? "500 kcal deficit (gentle, sustainable loss)"
              : "250 kcal surplus (steady muscle gain)"}.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-4xl font-semibold tracking-tight">
            {profile.daily_kcal_target.toLocaleString()}
            <span className="ml-2 text-base font-normal text-muted-foreground">
              kcal/day
            </span>
          </p>
          {/* Static progress placeholder — Phase 5 replaces this with the
              Rive avatar + animated kcal ring. */}
          <div
            className="h-2 w-full rounded-full bg-muted"
            aria-label="Daily kcal progress placeholder"
          >
            <div className="h-2 w-0 rounded-full bg-primary" />
          </div>
          {profile.floor_hit ? (
            <p className="text-xs text-amber-600 dark:text-amber-400">
              FitGH is a fitness tracking tool, not medical advice. Targets
              below {floorValue} kcal/day are clamped; consult a clinician
              before pursuing aggressive deficits.
            </p>
          ) : null}
        </CardContent>
      </Card>

      {showProtein ? (
        <Card>
          <CardHeader>
            <CardTitle>Protein target</CardTitle>
            <CardDescription>
              1.6 g per kg bodyweight to support muscle gain.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold tracking-tight">
              {profile.daily_protein_g_target}
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                g protein/day
              </span>
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
