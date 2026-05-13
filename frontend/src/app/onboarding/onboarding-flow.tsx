"use client";

// Onboarding 3-step single-page conditional flow — Phase 2 Plan 02 (P2-C.1).
//
// Per D-NO-ROUTER-MULTISTEP: useState index, not React Router multi-step,
// so back/forward feels instant.

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { profileCreateSchema, type ProfileCreate } from "@/lib/zod-schemas";
import { IdentityStep } from "./steps/identity-step";
import { BodyGoalStep } from "./steps/body-goal-step";
import { PrivacyStep } from "./steps/privacy-step";

type StepIdx = 0 | 1 | 2;

const STEP_FIELDS: Record<StepIdx, (keyof ProfileCreate)[]> = {
  0: ["name", "sex", "age", "locale"],
  1: ["height_cm", "weight_kg", "activity_level", "primary_goal"],
  2: ["timezone", "privacy_consent"],
};

export function OnboardingFlow() {
  const router = useRouter();
  const [step, setStep] = useState<StepIdx>(0);
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<ProfileCreate>({
    resolver: zodResolver(profileCreateSchema),
    mode: "onBlur",
    defaultValues: {
      name: "",
      // sex/locale/activity_level/primary_goal start undefined so the radios
      // are unselected and validation fires on next-click.
      timezone: "",
      privacy_consent: false as unknown as true,
    } as Partial<ProfileCreate> as ProfileCreate,
  });

  const onNext = async () => {
    const fields = STEP_FIELDS[step];
    const ok = await form.trigger(fields);
    if (!ok) return;
    setStep((s) => (s === 2 ? s : ((s + 1) as StepIdx)));
  };

  const onBack = () => {
    setStep((s) => (s === 0 ? s : ((s - 1) as StepIdx)));
  };

  const onSubmit = form.handleSubmit(async (values) => {
    setServerError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (res.status === 201) {
        router.push("/dashboard");
        router.refresh();
        return;
      }
      const body = await res.json().catch(() => ({} as Record<string, unknown>));
      setServerError(
        typeof body.error === "string"
          ? `${body.error}${body.details ? `: ${JSON.stringify(body.details)}` : ""}`
          : `Request failed (${res.status})`,
      );
    } catch (e) {
      setServerError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setSubmitting(false);
    }
  });

  const consent = form.watch("privacy_consent");
  const submitDisabled = submitting || consent !== true;

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Welcome to FitGH</CardTitle>
          <CardDescription>
            Three quick screens and you&apos;re in. Step {step + 1} of 3.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-6">
            {step === 0 ? <IdentityStep control={form.control} /> : null}
            {step === 1 ? <BodyGoalStep control={form.control} /> : null}
            {step === 2 ? (
              <PrivacyStep control={form.control} setValue={form.setValue} />
            ) : null}

            {serverError ? (
              <p className="text-sm text-destructive" role="alert">
                {serverError}
              </p>
            ) : null}

            <div className="flex justify-between gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={onBack}
                disabled={step === 0 || submitting}
              >
                Back
              </Button>
              {step < 2 ? (
                <Button type="button" onClick={onNext}>
                  Next
                </Button>
              ) : (
                <Button type="submit" disabled={submitDisabled}>
                  {submitting ? "Saving…" : "Finish onboarding"}
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
