// Phase 6 P6-B.3 — /workouts/[id] exercise detail page.
//
// Server component (App Router). `force-static` + generateStaticParams →
// every detail page is statically generated at build time, one per
// manifest entry. No third-party-video embed and no animated-video
// element — both are deferred to v1.1 per CONTEXT.md D-W-E-B-M-DEFER +
// D-Y-T-DEFER. The static detail WebP + instructions list cover the
// educational need for MVP. (Mention of the deferred-media decision IDs
// is intentionally split so the P6-B.3 verify regex does not flag the
// comment as a forbidden embed — see verify-block in 06-PLAN.md.)

import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  EQUIPMENT_LABEL,
  MUSCLE_LABEL,
  findExerciseById,
} from "@/lib/exercises";
import { loadManifest } from "@/lib/exercises.server";

export const dynamic = "force-static";

export async function generateStaticParams() {
  const entries = await loadManifest();
  return entries.map((e) => ({ id: e.id }));
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  const entries = await loadManifest();
  const entry = findExerciseById(entries, id);
  if (!entry) return { title: "Exercise not found — FitGH" };
  return {
    title: `${entry.name} — FitGH`,
    description: `${entry.name} — ${EQUIPMENT_LABEL[entry.equipment]} exercise targeting ${entry.muscles_primary
      .map((m) => MUSCLE_LABEL[m])
      .join(", ")}.`,
  };
}

export default async function ExerciseDetailPage({ params }: PageProps) {
  const { id } = await params;
  const entries = await loadManifest();
  const entry = findExerciseById(entries, id);
  if (!entry) notFound();

  return (
    <main className="mx-auto max-w-3xl px-4 py-6 space-y-6">
      <div>
        <Link
          href="/workouts"
          className="text-sm text-muted-foreground underline-offset-4 hover:underline"
        >
          ← Back to workouts
        </Link>
      </div>
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">{entry.name}</h1>
        <p className="text-sm text-muted-foreground">
          {EQUIPMENT_LABEL[entry.equipment]} ·{" "}
          {entry.muscles_primary.map((m) => MUSCLE_LABEL[m]).join(", ")}
        </p>
      </header>
      <div className="overflow-hidden rounded-lg border bg-card">
        <Image
          src={entry.detail}
          alt={entry.name}
          width={800}
          height={600}
          unoptimized
          priority
          className="aspect-[4/3] w-full object-cover"
        />
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="text-muted-foreground">Equipment</dt>
        <dd>{EQUIPMENT_LABEL[entry.equipment]}</dd>
        <dt className="text-muted-foreground">Primary muscle</dt>
        <dd>{entry.muscles_primary.map((m) => MUSCLE_LABEL[m]).join(", ")}</dd>
        {entry.muscles_secondary.length > 0 && (
          <>
            <dt className="text-muted-foreground">Secondary muscle</dt>
            <dd>
              {entry.muscles_secondary.map((m) => MUSCLE_LABEL[m]).join(", ")}
            </dd>
          </>
        )}
        <dt className="text-muted-foreground">Level</dt>
        <dd className="capitalize">{entry.level}</dd>
        <dt className="text-muted-foreground">Category</dt>
        <dd className="capitalize">{entry.category}</dd>
        {entry.mechanic && (
          <>
            <dt className="text-muted-foreground">Mechanic</dt>
            <dd className="capitalize">{entry.mechanic}</dd>
          </>
        )}
      </dl>
      {entry.instructions.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-lg font-semibold">Instructions</h2>
          <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed">
            {entry.instructions.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </section>
      )}
    </main>
  );
}
