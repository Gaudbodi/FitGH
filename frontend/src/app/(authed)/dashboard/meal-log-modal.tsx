// MealLogModal — Phase 3 Plan 03 (P3-C.3).
//
// Dialog hosting FoodSearch + ComponentChip + running total + Save. Two
// modes:
//   - create: initial is undefined; submit POSTs /api/meals.
//   - edit:   initial is a MealResponse; submit PATCHes /api/meals/<id>.
//
// PATCH semantics (D-PATCH-REPLACES-COMPONENTS / planner-flagged risk #2):
// the FE always sends the FULL edited components array. The server
// replaces the persisted array atomically.

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ComponentChip,
  draftKcal,
  draftProtein,
  type ComponentDraft,
} from "./component-chip";
import { FoodSearch } from "./food-search";
import {
  BACKDATE_MAX_DAYS,
  PORTION_MAX_G,
  PORTION_MIN_G,
  type GhanaFoodResponse,
  type MealResponse,
} from "@/lib/zod-schemas";

interface MealLogModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initial?: MealResponse;
}

function nowLocalForInput(): string {
  // YYYY-MM-DDTHH:mm in the user's local time (browser local — close
  // enough for the modal default; backend interprets datetime in profile.tz).
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
}

function backdateMinForInput(): string {
  const d = new Date(Date.now() - BACKDATE_MAX_DAYS * 24 * 3600 * 1000);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}T00:00`;
}

function localInputToIso(localInput: string): string {
  // <input type="datetime-local"> emits "YYYY-MM-DDTHH:mm" in local time.
  // Construct a Date with that local time + toISOString() for UTC.
  const d = new Date(localInput);
  return d.toISOString();
}

function persistedToDraft(meal: MealResponse): ComponentDraft[] {
  return meal.components.map((c) => {
    // Recover an approximate kcal_per_100g for the slider preview. The
    // server already persisted kcal_point for the original portion; we
    // back-fill the per-100g by inversion so future portion edits keep
    // their preview math.
    const per100 = c.portion_g > 0 ? (c.kcal_point * 100) / c.portion_g : 0;
    const protein100 =
      c.portion_g > 0 ? (c.protein_g_point * 100) / c.portion_g : 0;
    return {
      name: c.name,
      food_id: c.matched_food_id,
      portion_g: c.portion_g,
      kcal_per_100g: per100,
      protein_g_per_100g: protein100,
      source: c.source === "table" ? "table" : "user_corrected",
    };
  });
}

export function MealLogModal({
  open,
  onOpenChange,
  initial,
}: MealLogModalProps) {
  const router = useRouter();
  const [components, setComponents] = React.useState<ComponentDraft[]>([]);
  const [loggedAt, setLoggedAt] = React.useState<string>(nowLocalForInput());
  const [showBackdate, setShowBackdate] = React.useState(false);
  const [showFreeText, setShowFreeText] = React.useState(false);
  const [freeTextName, setFreeTextName] = React.useState("");
  const [freeTextPortion, setFreeTextPortion] = React.useState<number>(200);
  const [freeTextKcal, setFreeTextKcal] = React.useState<number>(200);
  const [submitting, setSubmitting] = React.useState(false);
  const [serverError, setServerError] = React.useState<string | null>(null);

  // When opening, hydrate state from initial (edit mode) or reset (create).
  React.useEffect(() => {
    if (!open) return;
    setServerError(null);
    setShowBackdate(false);
    setShowFreeText(false);
    setFreeTextName("");
    setFreeTextPortion(200);
    setFreeTextKcal(200);
    if (initial) {
      setComponents(persistedToDraft(initial));
      // Convert initial.logged_at (ISO string) to local input format.
      const d = new Date(initial.logged_at);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      const hh = String(d.getHours()).padStart(2, "0");
      const mi = String(d.getMinutes()).padStart(2, "0");
      setLoggedAt(`${yyyy}-${mm}-${dd}T${hh}:${mi}`);
    } else {
      setComponents([]);
      setLoggedAt(nowLocalForInput());
    }
  }, [open, initial]);

  const totalKcal = components.reduce((sum, c) => sum + draftKcal(c), 0);
  const totalProtein = components.reduce(
    (sum, c) => sum + draftProtein(c),
    0,
  );

  const onSelectFood = (food: GhanaFoodResponse) => {
    if (components.length >= 10) {
      setServerError("Maximum 10 components per meal.");
      return;
    }
    const firstPortion = food.portion_defaults[0]?.grams ?? PORTION_MIN_G;
    setComponents((cs) => [
      ...cs,
      {
        name: food.name,
        food_id: food.food_id,
        portion_g: Math.min(
          PORTION_MAX_G,
          Math.max(PORTION_MIN_G, firstPortion),
        ),
        kcal_per_100g: food.kcal_per_100g,
        protein_g_per_100g: food.protein_g_per_100g,
        source: "table",
      },
    ]);
  };

  const addFreeText = () => {
    if (!freeTextName.trim()) {
      setServerError("Free-text component needs a name.");
      return;
    }
    if (freeTextPortion < PORTION_MIN_G || freeTextPortion > PORTION_MAX_G) {
      setServerError(`Portion must be ${PORTION_MIN_G}..${PORTION_MAX_G} g.`);
      return;
    }
    if (freeTextKcal < 0 || freeTextKcal > 5000) {
      setServerError("Kcal must be 0..5000.");
      return;
    }
    if (components.length >= 10) {
      setServerError("Maximum 10 components per meal.");
      return;
    }
    // Synthesize kcal_per_100g for the preview slider.
    const per100 = (freeTextKcal * 100) / freeTextPortion;
    setComponents((cs) => [
      ...cs,
      {
        name: freeTextName.trim(),
        food_id: null,
        portion_g: freeTextPortion,
        kcal_per_100g: per100,
        protein_g_per_100g: 0,
        source: "user_corrected",
      },
    ]);
    setFreeTextName("");
    setFreeTextPortion(200);
    setFreeTextKcal(200);
    setShowFreeText(false);
    setServerError(null);
  };

  const replaceComponent = (idx: number, next: ComponentDraft) => {
    setComponents((cs) => cs.map((c, i) => (i === idx ? next : c)));
  };
  const removeComponent = (idx: number) => {
    setComponents((cs) => cs.filter((_, i) => i !== idx));
  };

  const onSubmit = async () => {
    if (components.length === 0) {
      setServerError("Add at least one component.");
      return;
    }
    setSubmitting(true);
    setServerError(null);
    try {
      const isoLoggedAt = localInputToIso(loggedAt);
      // Build the components array matching the server's ComponentCreate union.
      const componentsBody = components.map((c) => {
        if (c.food_id) {
          return { food_id: c.food_id, portion_g: c.portion_g };
        }
        return {
          name: c.name,
          portion_g: c.portion_g,
          kcal_point: draftKcal(c),
        };
      });
      const body = {
        logged_at: isoLoggedAt,
        components: componentsBody,
      };

      const url = initial ? `/api/meals/${initial.id}` : "/api/meals";
      const method = initial ? "PATCH" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        let msg = `Save failed (${res.status})`;
        try {
          const errBody = await res.json();
          if (errBody.error) msg = `${errBody.error}`;
        } catch {
          /* ignore */
        }
        setServerError(msg);
        return;
      }
      toast.success(initial ? "Meal updated" : "Meal logged");
      onOpenChange(false);
      router.refresh();
    } catch {
      setServerError("Network error. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{initial ? "Edit meal" : "Log meal"}</DialogTitle>
          <DialogDescription>
            Build your meal from one or more components. Sliders snap to 10 g
            increments.
          </DialogDescription>
        </DialogHeader>

        <FoodSearch onSelect={onSelectFood} />

        <div>
          <button
            type="button"
            className="text-xs underline-offset-4 text-muted-foreground hover:underline"
            onClick={() => setShowFreeText((v) => !v)}
          >
            {showFreeText ? "Hide free-text entry" : "+ Free-text component"}
          </button>
          {showFreeText && (
            <div className="mt-2 flex flex-col gap-2 rounded-lg border border-input/40 p-3">
              <Label className="text-xs">Name</Label>
              <Input
                value={freeTextName}
                onChange={(e) => setFreeTextName(e.target.value)}
                placeholder="e.g. Beans on toast"
              />
              <div className="flex gap-2">
                <div className="flex-1">
                  <Label className="text-xs">Portion (g)</Label>
                  <Input
                    type="number"
                    min={PORTION_MIN_G}
                    max={PORTION_MAX_G}
                    step={10}
                    value={freeTextPortion}
                    onChange={(e) =>
                      setFreeTextPortion(parseInt(e.target.value || "0", 10))
                    }
                  />
                </div>
                <div className="flex-1">
                  <Label className="text-xs">Kcal</Label>
                  <Input
                    type="number"
                    min={0}
                    max={5000}
                    value={freeTextKcal}
                    onChange={(e) =>
                      setFreeTextKcal(parseInt(e.target.value || "0", 10))
                    }
                  />
                </div>
              </div>
              <Button type="button" variant="outline" onClick={addFreeText}>
                Add as free-text
              </Button>
            </div>
          )}
        </div>

        {components.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            Search and add a food above to start logging.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {components.map((c, idx) => (
              <ComponentChip
                key={`${c.food_id ?? "free"}-${idx}`}
                component={c}
                onChange={(next) => replaceComponent(idx, next)}
                onRemove={() => removeComponent(idx)}
              />
            ))}
          </div>
        )}

        <div>
          <button
            type="button"
            className="text-xs underline-offset-4 text-muted-foreground hover:underline"
            onClick={() => setShowBackdate((v) => !v)}
          >
            {showBackdate ? "Hide backdate" : "Backdate (up to 7 days)"}
          </button>
          {showBackdate && (
            <div className="mt-2 flex flex-col gap-1">
              <Label className="text-xs">Logged at</Label>
              <Input
                type="datetime-local"
                value={loggedAt}
                onChange={(e) => setLoggedAt(e.target.value)}
                min={backdateMinForInput()}
                max={nowLocalForInput()}
              />
            </div>
          )}
        </div>

        <div className="flex items-center justify-between rounded-lg bg-muted/40 p-3 text-sm">
          <span className="text-muted-foreground">Running total</span>
          <span className="font-medium tabular-nums">
            {totalKcal} kcal - {totalProtein} g protein
          </span>
        </div>

        {serverError && (
          <p className="text-xs text-destructive">{serverError}</p>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={onSubmit}
            disabled={submitting || components.length === 0}
          >
            {submitting ? "Saving..." : initial ? "Update meal" : "Save meal"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
