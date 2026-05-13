// ScanSheet — Phase 4 Plan 04 (P4-D.1).
//
// Client component. Hosts the camera-first capture, compress→POST flow,
// loading + error states, and the result-chips review pane. On Confirm,
// the corrected chips POST to /api/meals with source="ai_vision" — same
// endpoint as the manual log so persistence is unified.
//
// Flow stages (state machine):
//   idle        — user sees a big "Take or upload" tap target
//   compressing — browser-image-compression runs (target sub-second)
//   scanning    — fetch /api/meals/scan in flight (target ≤ 5s)
//   review      — render ScanResultChips; user edits → Confirm
//   submitting  — POST /api/meals (server enforces source='ai_vision' rules)
//   error       — show friendly message + "Use manual instead" CTA
//
// 429/503 paths bypass `error` and call props.onFallbackToManual so the
// Phase 3 modal opens in create mode (the user's intent is preserved
// even though vision is unavailable).

"use client";

import * as React from "react";
import { CameraIcon, Loader2Icon } from "lucide-react";
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
import type { ComponentDraft } from "./component-chip";
import { ScanResultChips, type UserCorrectionInput } from "./scan-result-chips";
import { compressMealImage } from "@/lib/compress-image";
import {
  visionScanResponseSchema,
  type VisionScanResponse,
} from "@/lib/zod-schemas";

type Stage =
  | "idle"
  | "compressing"
  | "scanning"
  | "review"
  | "submitting"
  | "error";

interface ScanSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onFallbackToManual: () => void;
}

interface ErrorState {
  code: string;
  message: string;
}

function visionComponentToDraft(c: VisionScanResponse["components"][number]): ComponentDraft {
  // Recover an approximate kcal_per_100g for the slider preview — the
  // server already gave us kcal_point post-table-rematch (matched) or
  // LLM midpoint (free-text). Inverting keeps slider drags producing
  // sensible per-100g numbers.
  const per100 = c.portion_g > 0 ? (c.kcal_point * 100) / c.portion_g : 0;
  const protein100 =
    c.portion_g > 0 ? (c.protein_g_point * 100) / c.portion_g : 0;
  return {
    name: c.name,
    food_id: c.matched_food_id,
    portion_g: c.portion_g,
    kcal_per_100g: per100,
    protein_g_per_100g: protein100,
    source: c.matched_food_id ? "table" : "user_corrected",
  };
}

export function ScanSheet({
  open,
  onOpenChange,
  onFallbackToManual,
}: ScanSheetProps) {
  const router = useRouter();
  const [stage, setStage] = React.useState<Stage>("idle");
  const [error, setError] = React.useState<ErrorState | null>(null);
  const [scanResult, setScanResult] = React.useState<VisionScanResponse | null>(
    null,
  );
  const [draftComponents, setDraftComponents] = React.useState<
    ComponentDraft[]
  >([]);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const elapsedRef = React.useRef<NodeJS.Timeout | null>(null);
  const [elapsedSec, setElapsedSec] = React.useState(0);

  // Reset state when the sheet opens.
  React.useEffect(() => {
    if (open) {
      setStage("idle");
      setError(null);
      setScanResult(null);
      setDraftComponents([]);
      setElapsedSec(0);
    }
  }, [open]);

  // Track scan elapsed time during the "scanning" stage so we can show
  // the user the timer (target ≤ 5 s; gives a hard 30 s circuit-breaker
  // via the abort handler).
  React.useEffect(() => {
    if (stage === "scanning") {
      const start = Date.now();
      elapsedRef.current = setInterval(() => {
        setElapsedSec(Math.floor((Date.now() - start) / 1000));
      }, 250);
    } else {
      if (elapsedRef.current) clearInterval(elapsedRef.current);
      elapsedRef.current = null;
    }
    return () => {
      if (elapsedRef.current) clearInterval(elapsedRef.current);
    };
  }, [stage]);

  const postCorrection = React.useCallback(
    async (correction: UserCorrectionInput) => {
      // Best-effort — failures swallow so a missed correction doesn't break
      // the user's flow. The next scan will simply not benefit from this
      // particular correction.
      try {
        await fetch("/api/corrections", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(correction),
        });
      } catch {
        /* swallow */
      }
    },
    [],
  );

  const onFile = async (file: File) => {
    setStage("compressing");
    setError(null);
    try {
      const compressed = await compressMealImage(file);
      setStage("scanning");
      const fd = new FormData();
      fd.append("image", compressed, compressed.name);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30_000);
      let res: Response;
      try {
        res = await fetch("/api/meals/scan", {
          method: "POST",
          body: fd,
          signal: controller.signal,
        });
      } finally {
        clearTimeout(timeout);
      }
      if (res.status === 429) {
        toast.error("You've used today's 8 scans. Switching to manual log.");
        onFallbackToManual();
        onOpenChange(false);
        return;
      }
      if (res.status === 503) {
        toast.error("Vision paused for the day. Switching to manual log.");
        onFallbackToManual();
        onOpenChange(false);
        return;
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}) as Record<string, unknown>);
        const code = (body.error as string) ?? "unknown";
        let message = "Scan failed — try again or log manually.";
        if (code === "vision_parse_failed") {
          message =
            "We couldn't read this photo. Try a clearer shot or log manually.";
        }
        if (code === "invalid_image") {
          message =
            "That image isn't supported (use JPG/PNG/WebP, ≤1 MB after compression).";
        }
        setError({ code, message });
        setStage("error");
        return;
      }
      const json = await res.json();
      const parsed = visionScanResponseSchema.safeParse(json);
      if (!parsed.success) {
        setError({
          code: "schema_mismatch",
          message: "Unexpected response shape. Please log manually.",
        });
        setStage("error");
        return;
      }
      setScanResult(parsed.data);
      setDraftComponents(parsed.data.components.map(visionComponentToDraft));
      setStage("review");
    } catch (e) {
      if ((e as Error).name === "AbortError") {
        setError({
          code: "timeout",
          message: "Scan timed out after 30 seconds. Try again or log manually.",
        });
      } else {
        setError({
          code: "network",
          message: "Network error — please try again or log manually.",
        });
      }
      setStage("error");
    }
  };

  const onChooseFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void onFile(file);
  };

  const onConfirm = async () => {
    if (!scanResult) return;
    if (draftComponents.length === 0) {
      toast.error("Add at least one component before confirming.");
      return;
    }
    setStage("submitting");
    try {
      // Build the same ComponentCreate shape Phase 3 manual log uses,
      // with the vision-only fields (kcal_low, kcal_high, confidence,
      // source) carried through. Server still recomputes kcal_point on
      // matched components from the Ghana table (T-04-05).
      const componentsBody = draftComponents.map((d, idx) => {
        const original = scanResult.components[idx];
        const kcal_low = original?.kcal_low ?? undefined;
        const kcal_high = original?.kcal_high ?? undefined;
        const confidence = original?.confidence ?? undefined;
        const source = original?.source ?? undefined;
        if (d.food_id) {
          return {
            food_id: d.food_id,
            portion_g: d.portion_g,
            kcal_low,
            kcal_high,
            confidence,
            source,
          };
        }
        // Free-text path needs a kcal_point. Use the slider's preview math.
        const kcal_point = Math.round((d.kcal_per_100g * d.portion_g) / 100);
        return {
          name: d.name,
          portion_g: d.portion_g,
          kcal_point,
          kcal_low,
          kcal_high,
          confidence,
          source,
        };
      });
      const body = {
        source: "ai_vision" as const,
        ai_metadata: scanResult.ai_metadata,
        components: componentsBody,
      };
      const res = await fetch("/api/meals", {
        method: "POST",
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
        setError({ code: "save_failed", message: msg });
        setStage("error");
        return;
      }
      toast.success("Meal logged from photo");
      onOpenChange(false);
      router.refresh();
    } catch {
      setError({
        code: "network",
        message: "Network error saving the meal.",
      });
      setStage("error");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Snap a meal</DialogTitle>
          <DialogDescription>
            Take a photo or upload one of your plate. We&apos;ll identify each
            food and estimate kcal. Your photo isn&apos;t stored.
          </DialogDescription>
        </DialogHeader>

        {stage === "idle" && (
          <div className="flex flex-col gap-3">
            <label
              htmlFor="meal-image-input"
              className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-input/60 bg-muted/30 p-8 text-center cursor-pointer hover:bg-muted/50 transition-colors"
            >
              <CameraIcon className="size-8 text-muted-foreground" />
              <span className="font-medium">Take or upload a photo</span>
              <span className="text-xs text-muted-foreground">
                Camera opens on mobile · JPG / PNG / WebP
              </span>
            </label>
            <input
              ref={fileInputRef}
              id="meal-image-input"
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={onChooseFile}
            />
          </div>
        )}

        {stage === "compressing" && (
          <div className="flex flex-col items-center gap-2 py-6">
            <Loader2Icon className="size-6 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Compressing image…</p>
          </div>
        )}

        {stage === "scanning" && (
          <div className="flex flex-col items-center gap-2 py-6">
            <Loader2Icon className="size-6 animate-spin text-muted-foreground" />
            <p className="text-sm font-medium">Estimating kcal…</p>
            <p className="text-xs text-muted-foreground tabular-nums">
              {elapsedSec}s elapsed (target ≤ 5s)
            </p>
          </div>
        )}

        {stage === "review" && scanResult && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between rounded-lg bg-muted/40 p-3 text-xs">
              <span className="text-muted-foreground">Vision range</span>
              <span className="font-medium tabular-nums">
                {scanResult.vision_total_kcal_low}–
                {scanResult.vision_total_kcal_high} kcal
              </span>
            </div>
            <ScanResultChips
              components={draftComponents}
              onChange={setDraftComponents}
              onCorrection={postCorrection}
            />
          </div>
        )}

        {stage === "submitting" && (
          <div className="flex flex-col items-center gap-2 py-6">
            <Loader2Icon className="size-6 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Saving meal…</p>
          </div>
        )}

        {stage === "error" && error && (
          <div className="flex flex-col gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4">
            <p className="text-sm">{error.message}</p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setStage("idle");
                  setError(null);
                }}
              >
                Try again
              </Button>
              <Button
                type="button"
                onClick={() => {
                  onFallbackToManual();
                  onOpenChange(false);
                }}
              >
                Log manually instead
              </Button>
            </div>
          </div>
        )}

        {stage === "review" && (
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={onConfirm}
              disabled={draftComponents.length === 0}
            >
              Confirm meal
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
