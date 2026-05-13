"use client";

// WeightLogCard — Phase 2 Plan 02 (P2-D.2).
//
// Client component on /dashboard. Single number input + Log button -> POST
// /api/weights -> router.refresh() so the server component refetches and
// the TargetCard reflects the recomputed kcal target (server-side recompute
// happens in POST /weights — P2-A.4).
//
// Avoids importing RHF + Zod here on purpose — those primitives are heavy
// (~50 kB) and the single-field form doesn't justify them on /dashboard
// which has a 180 kB First Load JS manual budget (PERF-01). Validation is
// done inline: kg must be 20..400 (mirrors backend WeightLogCreate); the
// backend re-validates so we are not skipping defence-in-depth.

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { WeightLogResponse } from "@/lib/zod-schemas";

interface WeightLogCardProps {
  recentWeights: WeightLogResponse[];
}

function fmtDate(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function WeightLogCard({ recentWeights }: WeightLogCardProps) {
  const router = useRouter();
  const [kgInput, setKgInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    const kg = Number.parseFloat(kgInput);
    if (Number.isNaN(kg)) {
      setError("Enter a number");
      return;
    }
    if (kg < 20 || kg > 400) {
      setError("Weight must be between 20 and 400 kg");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/weights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kg }),
      });
      if (res.status === 201) {
        toast.success(`Logged ${kg} kg`);
        setKgInput("");
        router.refresh();
        return;
      }
      if (res.status === 409) {
        setError("Finish onboarding before logging weights — redirecting…");
        router.push("/onboarding");
        return;
      }
      const body = await res.json().catch(() => ({} as Record<string, unknown>));
      setError(
        typeof body.error === "string" ? body.error : `Request failed (${res.status})`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setSubmitting(false);
    }
  };

  const visible = showAll ? recentWeights : recentWeights.slice(0, 7);
  const hasMore = recentWeights.length > 7;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Log a weight</CardTitle>
        <CardDescription>
          Updates your daily kcal target instantly.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={onSubmit} className="flex items-end gap-3">
          <div className="flex-1 flex flex-col gap-1.5">
            <Label htmlFor="weight-kg">Today&apos;s weight</Label>
            <div className="relative">
              <Input
                id="weight-kg"
                type="number"
                step="0.1"
                min="20"
                max="400"
                value={kgInput}
                onChange={(e) => setKgInput(e.target.value)}
                className="pr-10"
                placeholder="75.0"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                kg
              </span>
            </div>
          </div>
          <Button type="submit" disabled={submitting || !kgInput}>
            {submitting ? "Logging…" : "Log"}
          </Button>
        </form>
        {error ? (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}

        {recentWeights.length > 0 ? (
          <div className="flex flex-col gap-1.5">
            <h3 className="text-sm font-medium">Recent entries</h3>
            <ul className="flex flex-col gap-1 text-sm">
              {visible.map((w) => (
                <li
                  key={`${w.user_id}-${w.logged_at}`}
                  className="flex items-center justify-between rounded-md border bg-card px-3 py-2"
                >
                  <span className="font-medium">{w.kg} kg</span>
                  <span className="text-xs text-muted-foreground">
                    {fmtDate(w.logged_at)}
                  </span>
                </li>
              ))}
            </ul>
            {hasMore ? (
              <button
                type="button"
                onClick={() => setShowAll((s) => !s)}
                className="self-start text-xs text-muted-foreground underline-offset-4 hover:underline"
              >
                {showAll
                  ? "Show recent only"
                  : `View all (${recentWeights.length})`}
              </button>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No entries yet — log one above to start your history.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
