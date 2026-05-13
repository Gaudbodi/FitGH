// Phase 6 P6-B.1 — server-only manifest loader.
//
// Lives in a separate module from `./exercises.ts` so the filter helpers
// can be safely imported from client components without dragging in
// node:fs/promises (which webpack rejects in the client bundle).
//
// Called from `/workouts/page.tsx` and `/workouts/[id]/page.tsx`. Both
// pages set `export const dynamic = 'force-static'`, so this runs at
// build time only. Next 15 dedupes the call across the same render.

import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { type ExerciseEntry, manifestSchema } from "./exercises";

// SERVER-ONLY: import this module only from server components. The
// `node:fs/promises` import would fail webpack's client-bundle scheme check.
// We do not add the `server-only` package here because the call sites
// (workouts page.tsx + [id]/page.tsx) are server components by construction
// (no "use client"), and Next 15's App Router will tree-shake this module
// out of any client bundle that does not import it.

export async function loadManifest(): Promise<ExerciseEntry[]> {
  const manifestPath = join(
    process.cwd(),
    "public",
    "exercises",
    "manifest.json",
  );
  const raw = await readFile(manifestPath, "utf8");
  const parsed = manifestSchema.parse(JSON.parse(raw));
  return parsed.entries;
}
