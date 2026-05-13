// WeightLogCard placeholder — Phase 2 Plan 02 (P2-C.3 stub).
//
// Filled in by P2-D.2 with the full POST /api/weights flow + history list.
// This placeholder is here so /dashboard builds cleanly between P2-C.3 and
// P2-D.2 commits.

import type { WeightLogResponse } from "@/lib/zod-schemas";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface WeightLogCardProps {
  recentWeights: WeightLogResponse[];
}

export function WeightLogCard({ recentWeights }: WeightLogCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Log a weight</CardTitle>
        <CardDescription>
          Coming next — the weight log input + history list lands in P2-D.2.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {recentWeights.length} historical entries available.
        </p>
      </CardContent>
    </Card>
  );
}
