---
phase: 06-workout-library-pwa
plan: 06
type: execute
wave: 1
depends_on: []
files_modified:
  # Slice A — Ingest pipeline
  - scripts/ingest_exercises.py
  - scripts/requirements-ingest.txt
  - scripts/README-ingest.md
  - frontend/public/exercises/manifest.json
  - frontend/public/exercises/.gitattributes
  # Slice B — Workout library UI
  - frontend/src/lib/exercises.ts
  - frontend/src/lib/exercises.test.ts
  - frontend/src/app/workouts/page.tsx
  - frontend/src/app/workouts/workouts-grid.tsx
  - frontend/src/app/workouts/workouts-grid.test.tsx
  - frontend/src/app/workouts/filter-bar.tsx
  - frontend/src/app/workouts/filter-bar.test.tsx
  - frontend/src/app/workouts/exercise-card.tsx
  - frontend/src/app/workouts/[id]/page.tsx
  - frontend/src/app/workouts/[id]/not-found.tsx
  # Slice C — PWA + offline
  - frontend/package.json
  - frontend/next.config.ts
  - frontend/src/app/sw.ts
  - frontend/src/app/manifest.ts
  - frontend/src/components/pwa/register-sw.tsx
  - frontend/src/components/pwa/offline-indicator.tsx
  - frontend/src/components/pwa/offline-meal-queue.ts
  - frontend/src/components/pwa/offline-meal-queue.test.ts
  - frontend/src/components/pwa/install-prompt.tsx
  - frontend/public/icons/icon-192.png
  - frontend/public/icons/icon-512.png
  - frontend/public/icons/maskable-512.png
  # Slice D — Attribution + middleware
  - frontend/src/app/layout.tsx
  - frontend/middleware.ts
  - LICENSES.md
  # Slice E — Verify + traceability
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
autonomous: true
requirements:
  - WORK-01
  - WORK-02
  - WORK-03
  - WORK-04
  - WORK-05
  - WORK-06
  - WORK-07
  - WORK-08
  - PERF-02
  - PERF-03

must_haves:
  truths:
    - "On /workouts, an unauthenticated visitor sees a grid of ~100 exercise cards backed by frontend/public/exercises/manifest.json (server-fetched at build time); the route is in middleware.ts public list (WORK-01)"
    - "A sticky FilterBar exposes 6 equipment chips (none, dumbbells, bands, pull-up bar, kettlebell, barbell) and 6+ muscle chips (chest, back, legs, shoulders, arms, core, glutes, full-body); same-category chips OR together, cross-category chips AND together; first visit defaults to {equipment: ['body only','dumbbells']} (WORK-02, WORK-03, WORK-04)"
    - "Each card shows a WebP poster ≤30 kB served from /exercises/{id}/poster.webp via next/image with `unoptimized` so the existing static WebP is shipped as-is; the card is a <Link href=`/workouts/{id}`> wrapping the poster + name + equipment + primary muscle label (WORK-05)"
    - "Tapping a card navigates to /workouts/[id], a server component that reads manifest.json, finds the exercise by id, and renders the larger detail WebP (≤80 kB) + the instructions list + target muscle + equipment metadata; 404 page when id not in manifest (WORK-05, WORK-06)"
    - "The global footer in layout.tsx renders the line 'Exercise data from Free Exercise DB (Unlicense).' linking to the Free Exercise DB repo; LICENSES.md at the repo root credits Free Exercise DB + Anthropic + MongoDB + Clerk + Render (WORK-07)"
    - "frontend/next.config.ts wraps the export in withSerwist({ swSrc: 'src/app/sw.ts', swDest: 'public/sw.js' }) so the build emits a service worker; the service worker pre-caches the App Shell + /workouts route HTML + /exercises/manifest.json + all 200 poster/detail WebPs on `install` (WORK-08)"
    - "Service worker runtime caching: 'cache-first' for /exercises/**/*.webp (30-day max-age), 'stale-while-revalidate' for /workouts(.*) HTML + /exercises/manifest.json, 'network-first' for /api/* (auth-gated, never cache); after `install` + `activate`, visiting /workouts offline renders the full grid from cache (WORK-08)"
    - "frontend/src/app/manifest.ts emits the Next.js native PWA manifest with name 'FitGH', short_name 'FitGH', theme_color matching Tailwind primary (#10b981), background_color '#ffffff', display 'standalone', start_url '/dashboard', icons 192/512 + maskable-512 (WORK-08)"
    - "Offline meal POSTs queue in an IDBObjectStore 'meal_queue' when navigator.onLine === false OR fetch fails; on the window 'online' event (or service-worker `sync` event if registered), the queue drains by replaying queued requests against /api/meals; replayed POSTs that 401 are surfaced via the global Toaster (WORK-08)"
    - "An <OfflineIndicator> client component renders a small amber badge in the header whenever navigator.onLine is false (listens to window 'online'/'offline'); badge disappears on reconnect (WORK-08, helper UX)"
    - "Lighthouse mobile Performance score on /workouts is ≥ 90 when run via Chrome DevTools (Moto G Power emulation + Slow 4G); the score is recorded in 06-SUMMARY.md alongside above-fold image weight measurement (PERF-02, PERF-03)"
    - "Manual /workouts above-fold image weight is ≤ 100 kB: the first 2–3 poster WebPs visible at viewport size 360×800 are individually ≤30 kB; total ≤ 90 kB; recorded in SUMMARY (PERF-02)"
    - "No Flask /exercises route added; no Mongo `exercises` collection added; no wger import; no @rive-app, no @sentry/nextjs, no @vercel/analytics added in Phase 6 (anti-pattern enforcement from CONTEXT.md + plan brief)"
    - "frontend test count rises by ≥ 8 (filter-bar + workouts-grid + exercises lib + offline-meal-queue suites); backend test count is unchanged (no backend work this phase)"

  artifacts:
    - path: "scripts/ingest_exercises.py"
      provides: "One-shot Python ingest script. Fetches https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json + the image directory tree, filters by `category ∈ {strength, cardio}` + `level ∈ {beginner, intermediate, expert}`, normalizes `equipment` into the 6-bucket taxonomy (none|dumbbell|bands|pull-up bar|kettlebells|barbell) and `primaryMuscles` into the 8-bucket taxonomy (chest|back|legs|shoulders|arms|core|glutes|full-body), selects ~100 entries balanced across the 6×8 cells via a deterministic round-robin sort by (category, equipment, primary_muscle, id), downloads each entry's two source images, converts via Pillow to WebP (poster: 320×240 quality=72 method=6 ≤30 kB; detail: 800×600 quality=72 method=6 ≤80 kB; iterative quality decay if over budget), writes per-exercise files to frontend/public/exercises/{id}/poster.webp + detail.webp, and writes frontend/public/exercises/manifest.json sorted by id. Deterministic: re-running against the same Free Exercise DB commit hash yields byte-identical outputs."
      exports: []
    - path: "scripts/requirements-ingest.txt"
      provides: "Pinned deps for the ingest script (httpx, Pillow). Separate from backend/requirements.txt so the Render Flask dyno does not pick up Pillow."
      exports: []
    - path: "scripts/README-ingest.md"
      provides: "How-to: run via `python -m venv .venv && .venv/Scripts/activate && pip install -r scripts/requirements-ingest.txt && python scripts/ingest_exercises.py --commit <sha>`. Documents the commit-hash pin (default to a hash captured 2026-05-13), the 8 muscle × 6 equipment grid, and the budget enforcement loop. Notes: re-running is a no-op when manifest.json + WebPs already match."
      exports: []
    - path: "frontend/public/exercises/manifest.json"
      provides: "JSON array of ~100 entries. Schema: `[{id: string, name: string, equipment: 'none'|'dumbbell'|'bands'|'pull-up bar'|'kettlebells'|'barbell', muscles_primary: string[], muscles_secondary: string[], category: 'strength'|'cardio', level: 'beginner'|'intermediate'|'expert', mechanic: 'compound'|'isolation'|null, instructions: string[], poster: '/exercises/{id}/poster.webp', detail: '/exercises/{id}/detail.webp'}]`. Static; committed to the repo alongside the WebPs."
      exports: []
    - path: "frontend/public/exercises/.gitattributes"
      provides: "Marks *.webp as binary so Git does not attempt diffing; keeps git status clean across the 200-file commit."
      exports: []
    - path: "frontend/src/lib/exercises.ts"
      provides: "Pure helpers + TS types matching the manifest schema. Exports: `ExerciseEntry`, `EquipmentBucket` (union), `MuscleBucket` (union), `DEFAULT_EQUIPMENT_SELECTION = ['none', 'dumbbell']`, `filterExercises(entries, { equipment, muscles })` (AND across categories, OR within), `findExerciseById(entries, id)`, `loadManifest()` (server-side fs.readFile of frontend/public/exercises/manifest.json + zod parse for runtime guard)."
      exports: ["ExerciseEntry", "EquipmentBucket", "MuscleBucket", "DEFAULT_EQUIPMENT_SELECTION", "filterExercises", "findExerciseById", "loadManifest"]
    - path: "frontend/src/lib/exercises.test.ts"
      provides: "Vitest unit tests: filter selects intersection across equipment+muscles; empty selection returns all; default selection picks none+dumbbell entries only; findExerciseById returns undefined for missing id; zod schema rejects manifest with bad equipment enum."
      exports: []
    - path: "frontend/src/app/workouts/page.tsx"
      provides: "Server component for /workouts. Calls loadManifest() (fs read at request time; static after first call). Renders <FilterBar /> + <WorkoutsGrid entries={manifest} />. No auth check (route is public via middleware). `export const dynamic = 'force-static'` so the page is statically generated at build time."
      exports: []
    - path: "frontend/src/app/workouts/workouts-grid.tsx"
      provides: "Client component ('use client'). Holds filter selection state via useState (initialized to { equipment: DEFAULT_EQUIPMENT_SELECTION, muscles: [] }). Computes filtered list via filterExercises. Renders responsive CSS grid (`grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4`). Children: <ExerciseCard /> per entry. Empty-state copy when filtered list is empty."
      exports: ["WorkoutsGrid"]
    - path: "frontend/src/app/workouts/filter-bar.tsx"
      provides: "Client component. Two chip rows (equipment, muscles). Each chip is a button toggling membership in the corresponding string[] selection. Sticky-top via `sticky top-0 z-10 bg-background/95 backdrop-blur`. Receives `selection` + `onChange` from <WorkoutsGrid> (controlled). Accessibility: chips are <button aria-pressed> with focus rings."
      exports: ["FilterBar", "FilterSelection"]
    - path: "frontend/src/app/workouts/filter-bar.test.tsx"
      provides: "Vitest + @testing-library: rendering with default selection marks none+dumbbell aria-pressed=true; clicking a muscle chip fires onChange with that muscle added; clicking a pressed chip removes it; keyboard activation (Enter/Space) toggles."
      exports: []
    - path: "frontend/src/app/workouts/workouts-grid.test.tsx"
      provides: "Vitest tests: grid renders one card per entry; switching filter selection re-filters; empty filter result shows empty-state copy."
      exports: []
    - path: "frontend/src/app/workouts/exercise-card.tsx"
      provides: "Server component. Props: { entry: ExerciseEntry }. Renders <Link href={`/workouts/${entry.id}`}> wrapping <Image src={entry.poster} alt={entry.name} width=320 height=240 unoptimized loading='lazy' /> + name + small equipment/muscle labels. The `unoptimized` flag tells next/image to ship the WebP as-is (Free Exercise DB ingest already produced optimized files)."
      exports: ["ExerciseCard"]
    - path: "frontend/src/app/workouts/[id]/page.tsx"
      provides: "Server component for /workouts/[id]. Reads manifest, calls findExerciseById, calls notFound() if missing. Renders large detail WebP (<Image src={entry.detail} width=800 height=600 unoptimized priority />), name, equipment, muscle labels, ordered <ol> of instructions. NO YouTube embed (deferred per CONTEXT.md). generateStaticParams() returns all manifest ids so each detail page is statically generated at build time (`export const dynamic = 'force-static'`)."
      exports: ["generateStaticParams"]
    - path: "frontend/src/app/workouts/[id]/not-found.tsx"
      provides: "Friendly 404 with a link back to /workouts."
      exports: []
    - path: "frontend/package.json"
      provides: "Adds `@serwist/next` (^9.x) and `serwist` (^9.x) — the modern next-pwa successor with Next 15 App Router support. Adds `idb-keyval` (^6.x) for the offline meal queue IndexedDB wrapper (tiny ~600 bytes gzipped). Does NOT add next-pwa, workbox-* directly, @rive-app/*, @sentry/nextjs, @vercel/analytics. pnpm install MUST succeed with --frozen-lockfile; if @serwist/next requires a Next 15.2.4 peer adjustment that the existing lockfile can't satisfy, update package.json AND pnpm-lock.yaml in the same commit (no `--no-frozen-lockfile` bypass)."
      exports: []
    - path: "frontend/next.config.ts"
      provides: "Imports `withSerwist` from `@serwist/next` and wraps the existing config: `withSerwist({ swSrc: 'src/app/sw.ts', swDest: 'public/sw.js', cacheOnNavigation: true, reloadOnOnline: true, register: false })`. `register: false` because we register from a client component (frontend/src/components/pwa/register-sw.tsx) so we can co-locate the registration with the OfflineIndicator + InstallPrompt mount."
      exports: ["default (NextConfig)"]
    - path: "frontend/src/app/sw.ts"
      provides: "Serwist service worker source. Imports `defaultCache` from `@serwist/next/worker` and `installSerwist` from `serwist`. Routes (in order): (1) `({url}) => url.pathname.startsWith('/api/')` → `NetworkOnly` (never cache auth-gated POST/GET; falls through to the offline-meal-queue replay on network failure handled at the client level); (2) `({url}) => url.pathname.startsWith('/exercises/') && url.pathname.endsWith('.webp')` → `CacheFirst` with `expiration: { maxEntries: 250, maxAgeSeconds: 30*24*60*60 }`; (3) `({url}) => url.pathname === '/exercises/manifest.json'` → `StaleWhileRevalidate`; (4) `({url}) => url.pathname.startsWith('/workouts')` → `StaleWhileRevalidate`; (5) fallback → `defaultCache` rules. Precache: the Serwist build injects the App Shell manifest; we additionally precache `/workouts`, `/exercises/manifest.json`, and the first 100 poster WebPs via a `additionalPrecacheEntries` array sourced from the manifest at build time (use a small `scripts/build-precache.cjs` that emits `precache-list.json` consumed by sw.ts)."
      exports: []
    - path: "frontend/src/app/manifest.ts"
      provides: "Next.js native MetadataRoute.Manifest export. Returns { name: 'FitGH', short_name: 'FitGH', description: 'Snap a meal, see kcal — track Ghanaian food and workouts.', start_url: '/dashboard', display: 'standalone', orientation: 'portrait-primary', background_color: '#ffffff', theme_color: '#10b981' (Tailwind emerald-500, matches accent in avatar sprite), icons: [192-any, 512-any, 512-maskable] }. Linked automatically into <head> by Next 15 via the file convention."
      exports: ["default (MetadataRoute.Manifest)"]
    - path: "frontend/src/components/pwa/register-sw.tsx"
      provides: "Client component ('use client'). On mount: if `'serviceWorker' in navigator` and not in dev, register('/sw.js', { scope: '/' }). Also exposes an effect that, on the 'online' window event, calls `drainMealQueue()` from offline-meal-queue.ts. Renders null. Mounted once in layout.tsx <body> (below the existing <ServicePausedBanner>)."
      exports: ["RegisterSW"]
    - path: "frontend/src/components/pwa/offline-indicator.tsx"
      provides: "Client component ('use client'). Listens to window 'online'/'offline' events + uses navigator.onLine for initial state. Renders a small fixed badge in the bottom-right ('Offline — meals will sync when reconnected') when !online, plus a subtle one-shot toast on reconnect via the existing Sonner Toaster. Tailwind only; ~30 LOC."
      exports: ["OfflineIndicator"]
    - path: "frontend/src/components/pwa/offline-meal-queue.ts"
      provides: "Idb-keyval-backed queue. Exports: `enqueueMealPost({ url, body, headers })` (used by the meal-log POST wrapper in /api/meals client calls when fetch fails), `drainMealQueue()` (re-issues each queued POST; on 2xx, dequeue; on 401, surface via Sonner and stop; on 5xx, leave queued; on a non-retryable 4xx other than 401, drop with a Sonner notice). Idempotency: each queue entry has a UUID v4 stamped client-side and forwarded as `Idempotency-Key: <uuid>` header so a replay after the network briefly returned 5xx never double-writes (the Flask /api/meals handler ignores unknown headers today; this is a non-breaking addition that lays groundwork for future backend dedup — TRACKED AS INTERPRETATION beyond CONTEXT.md, see decisions log below)."
      exports: ["enqueueMealPost", "drainMealQueue", "getQueueSize"]
    - path: "frontend/src/components/pwa/offline-meal-queue.test.ts"
      provides: "Vitest tests against fake-indexeddb: enqueue then drain replays the POST; 401 response surfaces a toast (mocked) and leaves the entry queued for the user to retry post-auth (per acceptance from CONTEXT.md — replay 'queues offline POSTs and replays on reconnect'); 200 dequeues; idempotency-key UUID is stable per enqueue; getQueueSize reports remaining entries."
      exports: []
    - path: "frontend/src/components/pwa/install-prompt.tsx"
      provides: "Client component. Captures the `beforeinstallprompt` event, stashes it in state, renders a dismissable banner on the dashboard only (returns null when pathname !== '/dashboard'). Dismissed state persists in localStorage so the banner shows at most once per user."
      exports: ["InstallPrompt"]
    - path: "frontend/public/icons/icon-192.png"
      provides: "192×192 PNG app icon (FitGH F monogram on emerald-500 bg). Hand-authored or generated via a quick Python+Pillow snippet in the ingest README. <10 kB."
      exports: []
    - path: "frontend/public/icons/icon-512.png"
      provides: "512×512 PNG app icon. <30 kB."
      exports: []
    - path: "frontend/public/icons/maskable-512.png"
      provides: "512×512 maskable PNG (safe-zone-padded variant for Android adaptive icons)."
      exports: []
    - path: "frontend/src/app/layout.tsx"
      provides: "Extended: footer adds the Free Exercise DB attribution line beside the existing © FitGH + /privacy link. Mounts <RegisterSW /> + <OfflineIndicator /> + <InstallPrompt /> inside <ClerkProvider>. The native PWA manifest is auto-linked by Next 15 from manifest.ts — no manual <link rel='manifest'> needed."
      exports: []
    - path: "frontend/middleware.ts"
      provides: "Public routes set: the existing matcher continues to gate /dashboard, /onboarding, /profile, /settings, /history, and the /api/* surfaces. /workouts(.*) is EXPLICITLY NOT in the protected list (no edit required to add it — the public default holds). The `matcher` config keeps the route-set untouched so /workouts and /workouts/{id} are public by default; we add a one-line comment block at the top of the file documenting that /workouts(.*) is intentionally public (browseable pre-login for onboarding incentive per CONTEXT.md)."
      exports: ["default (clerkMiddleware)", "config"]
    - path: "LICENSES.md"
      provides: "Repo-root licences index. Sections: 'Exercise Data — Free Exercise DB (Unlicense)' with link to https://github.com/yuhonas/free-exercise-db + 'This project includes exercise content under the Unlicense.'; 'Third-Party Services' listing Anthropic (Claude API ToS), MongoDB Atlas, Clerk, Render — each with a one-line role + their ToS URL; 'FitGH source code' — TBD (no licence chosen yet); 'Open-source dependencies' note pointing to package.json + requirements.txt."
      exports: []
    - path: ".planning/REQUIREMENTS.md"
      provides: "Flips WORK-01..WORK-08, PERF-02, PERF-03 from `[ ]` to `[x]`; Traceability table status column flips to 'Complete' for each. Status notes: WORK-06 (YouTube embed deferred to v1.1 per CONTEXT.md D-YT-DEFER — instructions list covers the educational need); WORK-05 (animated WebM deferred to v1.1 per CONTEXT.md D-WEBM-DEFER — Free Exercise DB ships static images; static WebP detail covers the visual need); PERF-02 + PERF-03 (manual check at phase boundary — no CI gate per the Render-only invariant); WORK-07 (Free Exercise DB Unlicense only — wger dropped per CONTEXT.md D-FREE-DB-ONLY)."
    - path: ".planning/ROADMAP.md"
      provides: "Flips Phase 6 row in the Progress table to Complete + records completion date 2026-05-13 once verified."

  key_links:
    - from: "frontend/src/app/workouts/page.tsx"
      to: "frontend/public/exercises/manifest.json via loadManifest()"
      via: "fs.readFile at request time (force-static so once at build)"
      pattern: "loadManifest|exercises/manifest\\.json"
    - from: "frontend/src/app/workouts/workouts-grid.tsx"
      to: "frontend/src/lib/exercises.ts filterExercises"
      via: "useState selection → filterExercises(entries, selection) → mapped to <ExerciseCard>"
      pattern: "filterExercises|DEFAULT_EQUIPMENT_SELECTION"
    - from: "frontend/src/app/workouts/[id]/page.tsx"
      to: "frontend/src/lib/exercises.ts findExerciseById"
      via: "params.id → findExerciseById(manifest, id) → notFound() on miss"
      pattern: "findExerciseById|notFound"
    - from: "frontend/next.config.ts"
      to: "@serwist/next withSerwist"
      via: "default export wrapped — emits public/sw.js at build"
      pattern: "withSerwist|@serwist/next"
    - from: "frontend/src/app/sw.ts"
      to: "@serwist/next/worker + serwist"
      via: "installSerwist + route matchers (CacheFirst for /exercises/*.webp, SWR for /workouts + manifest, NetworkOnly for /api/*)"
      pattern: "installSerwist|defaultCache|CacheFirst|StaleWhileRevalidate"
    - from: "frontend/src/app/manifest.ts"
      to: "Next.js MetadataRoute.Manifest"
      via: "default export of an object — auto-linked into <head> by Next 15 file convention"
      pattern: "MetadataRoute\\.Manifest|export default"
    - from: "frontend/src/components/pwa/register-sw.tsx"
      to: "navigator.serviceWorker.register('/sw.js')"
      via: "useEffect on mount (gated on 'serviceWorker' in navigator + NODE_ENV==='production')"
      pattern: "navigator\\.serviceWorker\\.register|drainMealQueue"
    - from: "frontend/src/components/pwa/offline-meal-queue.ts"
      to: "idb-keyval set/get/del + fetch replay"
      via: "queue entries keyed by UUID; drain iterates and re-fetches each /api/meals POST"
      pattern: "idb-keyval|enqueueMealPost|drainMealQueue"
    - from: "frontend/src/components/pwa/register-sw.tsx"
      to: "window 'online' event → drainMealQueue()"
      via: "addEventListener('online') with cleanup on unmount"
      pattern: "addEventListener\\('online'|drainMealQueue\\(\\)"
    - from: "frontend/src/app/layout.tsx footer"
      to: "Free Exercise DB attribution string + LICENSES.md anchor"
      via: "static <Link href='https://github.com/yuhonas/free-exercise-db'> text node"
      pattern: "Free Exercise DB"
    - from: "scripts/ingest_exercises.py"
      to: "frontend/public/exercises/manifest.json + /{id}/{poster,detail}.webp"
      via: "Pillow WebP encoder with quality decay loop until size budget met"
      pattern: "Pillow|webp|manifest"
---

# Phase 6 Plan 06 — Workout Library + PWA

## Phase Goal

A user can browse 80–120 curated exercises from a **static** library (Free Exercise DB, Unlicense — wger dropped to dodge CC-BY-SA share-alike), filter by 6 equipment buckets and 6+ target muscles (equipment defaults to `none + dumbbells` on first visit), see a tiny WebP poster on each card, tap into a detail page with instructions + larger WebP, and **install FitGH as a PWA** that:
1. Renders the entire workout library fully offline (cache-first on WebPs, stale-while-revalidate on manifest + /workouts HTML).
2. Queues meal POSTs taken offline and replays them on reconnect.

Animated WebM and curated YouTube embeds (WORK-05 second half, WORK-06 second half) are **deferred to v1.1** per CONTEXT.md D-WEBM-DEFER + D-YT-DEFER. The static WebP detail image + instructions list cover the educational need for MVP.

## Success Criteria (from ROADMAP.md, paraphrased)

1. **WORK-01..04** — Browse 80–120 curated exercises; filter by 6 equipment + 6+ muscle chips; equipment defaults to `none + dumbbells`.
2. **WORK-05 / WORK-06** — Card poster WebP ≤ 30 kB; tap loads detail page with larger image + instructions + meta. (Animated WebM + YouTube embed deferred.)
3. **WORK-07** — Footer attribution: "Exercise data from Free Exercise DB (Unlicense)"; LICENSES.md at repo root.
4. **WORK-08** — Install as PWA; workout library renders fully offline; offline meal POSTs queue + replay on reconnect.
5. **PERF-02 + PERF-03** — Lighthouse mobile ≥ 90 on /workouts (manual DevTools check; not a CI gate); above-fold image weight ≤ 100 kB per route (manual measurement). Recorded in 06-SUMMARY.md.

## Inherited Constraints (do NOT violate)

- **Static-first.** No Flask `/exercises` route. No Mongo `exercises` collection. All exercise data lives under `frontend/public/exercises/`. (CONTEXT.md D-STATIC-FIRST.)
- **Free Exercise DB only.** No wger import (CC-BY-SA share-alike forces repo-wide inheritance — unacceptable for a non-OSS proprietary app). (CONTEXT.md D-FREE-DB-ONLY.)
- **@serwist/next only.** No `next-pwa` (stale; does not fully support Next 15 App Router). (CONTEXT.md D-SERWIST-PWA.)
- **No WebM / no YouTube in MVP.** Both deferred to v1.1 per CONTEXT.md D-WEBM-DEFER + D-YT-DEFER. The plan brief's anti-pattern list re-enforces this — do not author WebM generation logic.
- **No CI image-weight gate.** Manual measurement at phase boundary, recorded in SUMMARY. (Render-only architecture invariant — same as Phases 1, 5 PERF-01 deferral.)
- **No backend changes.** Phase 6 work is 100% in `frontend/` + `scripts/` + repo-root LICENSES.md + `.planning/`. The existing meal endpoints already handle the queued-replay POSTs correctly (stateless authenticated POSTs — Phase 3/4 inheritance).
- **`--frozen-lockfile` on pnpm install.** If `@serwist/next` requires a Next 15.2.4 peer-version bump, update `package.json` + `pnpm-lock.yaml` in the same commit; do not bypass `--frozen-lockfile`.
- **Static SVG + Tailwind only for UI.** No new animation runtime introduced; no `framer-motion`, no `@rive-app/*`, no `lottie-react`.
- **Same patterns as Phases 1–5.** App Router server components for the static routes; client components for stateful pieces (filter bar, grid, offline queue); shadcn primitives + Tailwind; atomic per-task commits; push to `origin/main` after each task.

## Slice Overview

| Slice | Theme | Tasks |
|-------|-------|-------|
| A | Ingest pipeline — Python script + manifest emission + WebP encoding + 200-file commit | 3 |
| B | Workout library UI — /workouts page + filter bar + grid + exercise card + /workouts/[id] detail + lib helpers + tests | 3 |
| C | PWA + offline — install @serwist/next + sw.ts + manifest.ts + register-sw + OfflineIndicator + offline meal queue + InstallPrompt + icons | 4 |
| D | Attribution + middleware — footer credit + LICENSES.md + middleware comment | 1 |
| E | Verify + traceability — Lighthouse smoke + above-fold image-weight measurement + REQUIREMENTS.md/ROADMAP.md flip | 1 |

**Total: 12 tasks.** Same shape as Phase 5 (12 tasks across 5 slices).

Cross-slice ordering: A → B → (C, D in parallel) → E.
- A produces the manifest + WebPs that B reads.
- B's /workouts route must exist before C's service worker can pre-cache it.
- C and D do not depend on each other.
- E depends on every prior slice (Lighthouse runs against the full integrated build).

## Threat Register (Phase 6)

Trust boundaries inherited from Phase 1/3/4 (browser → Next.js BFF same-origin; BFF → Flask via Render-internal + Bearer JWT; Flask → MongoDB Atlas TLS). **New surfaces in Phase 6**: (a) the service worker itself (foreground intermediary for every HTTP request once installed), (b) the offline meal queue stored in IndexedDB, (c) the static manifest.json + WebPs (public read, no auth — by design), (d) the ingest pipeline (build-time only, ships static assets to git).

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-06-01 | Tampering | Service worker cached `/api/*` response stale-served to an auth-changed user | mitigate | sw.ts routes `/api/*` to `NetworkOnly` — **the service worker never caches API responses**. Failure path: fetch throws → caller catches → offline-meal-queue.ts decides whether to enqueue. A re-auth (session cookie rotated via Clerk) on the next online tick replaces stale cookies via the existing forwardToFlask BFF chain; the SW is bypassed for /api/*. Test: `test_sw_does_not_cache_api_meals` — issue a GET /api/meals via mocked SW context and assert no cache entry written. |
| T-06-02 | Information Disclosure | IndexedDB `meal_queue` survives sign-out — next user on same device sees old user's queued meals | mitigate | On the existing /sign-out flow (frontend/src/components/sign-out-button.tsx), add an `await clearMealQueue()` call before Clerk signs out. ALSO: on `drainMealQueue()` 401, surface a Sonner toast 'Please sign in to send your offline meals' and HOLD the queue (don't drop) — the queue is keyed by the JWT subject claim captured at enqueue time, and drain compares against the live `useUser().user.id`; mismatched entries are deleted, not replayed. |
| T-06-03 | Spoofing | Attacker-served sw.js from a different origin claims FitGH scope | accept | Service workers can only register at their own origin's scope; cross-origin SW registration is blocked by the browser. The same-origin policy is the trust anchor. No additional mitigation needed. |
| T-06-04 | Tampering | Cache-first `/exercises/*.webp` stale-serves an updated WebP after an ingest re-run | mitigate | (a) The 30-day max-age on the WebP cache rule auto-evicts; (b) every ingest run is committed to git, so on `git pull` + next deploy the SW pre-cache list updates (the precache manifest is content-hashed by Serwist's build step → cache version bumps → old WebPs evicted on next `activate`). Test: change one WebP locally + rebuild → confirm sw.js precache hash changes. |
| T-06-05 | Denial of Service | Offline queue grows unboundedly when user is offline for days | mitigate | `enqueueMealPost` enforces `MAX_QUEUE_SIZE = 50`; once reached, the oldest entry is dropped with a Sonner notice 'Offline meal queue full — your earliest pending meal was dropped'. 50 × ~1 kB JSON bodies = 50 kB worst case; well within IndexedDB quotas. Test: enqueue 51 entries → first dropped. |
| T-06-06 | Tampering | Replay attack — captured `/api/meals` POST replayed by attacker out-of-band | mitigate | The Idempotency-Key header is **client-side only** for the queue's own dedup; it does NOT defend against an external replay (Flask currently has no dedup). The replay defence remains: (a) JWT short expiry (Phase 1 — 60-min Clerk sessions), (b) the meal POST is idempotent at the day-bucket level only insofar as the user can manually delete duplicates (Phase 3 LOG-03). **Disposition:** accept the external-replay risk for v1 (low impact — at worst the attacker logs a duplicate meal in the victim's diary), and revisit if abuse appears. Documented in offline-meal-queue.ts docstring + the SUMMARY's "known limitations" section. |
| T-06-07 | Information Disclosure | Service worker logs queue contents to console in production | mitigate | offline-meal-queue.ts uses a `debug()` helper gated on `process.env.NODE_ENV !== 'production'` — no console.log of body payloads in production. The Sonner toasts on success/failure show only counts ('3 meals synced'), never body content. Lint rule: a per-file eslint comment forbids `console.log` in offline-meal-queue.ts and sw.ts. |
| T-06-08 | Tampering | Ingest script downloads a malicious WebP that exploits a libwebp CVE in users' browsers | mitigate | (a) The ingest is pinned to a Free Exercise DB commit hash (captured at ingest time, recorded in scripts/README-ingest.md); auditing the source repo at that hash before commit. (b) Pillow re-encodes every image from the raw source — the bytes that hit the user are produced by Pillow, not the source. (c) The committed WebPs are reviewed in the same PR as the ingest run. (d) The user's browser auto-updates libwebp via Chrome/Edge update channels — out of scope for the app. Documented in scripts/README-ingest.md. |
| T-06-09 | Denial of Service | First-install SW pre-cache of all 200 WebPs (~3–6 MB) on a metered Ghana connection drains user data | mitigate | The SW `install` event pre-caches **only the App Shell + /workouts HTML + /exercises/manifest.json + the first 24 poster WebPs** (the most-likely-default-filtered subset: 24 = first 4 cards × 6 equipment buckets within the `none + dumbbells` default). The remaining ~76 posters + all 100 detail WebPs use `CacheFirst` runtime caching — fetched on demand when the user actually scrolls/taps. Worst-case first-install precache: ~24 × 30 kB = 720 kB. The `additionalPrecacheEntries` array in sw.ts is built from a `precache-list.json` that the ingest script emits with the 24 subset already chosen. |
| T-06-10 | Repudiation | User claims a meal was logged offline but it never replayed; no trace | mitigate | `drainMealQueue()` writes a structured success/failure summary into the existing browser console + a Sonner toast ('Synced 3 offline meals' / 'Failed to sync 1 meal — will retry'). For repudiation-grade auditing, the meal POST itself is logged server-side by Flask (Phase 3 existing behaviour). The replay-path adds an `X-Replayed-Offline: 1` header on each replayed request so backend logs can correlate. |
| T-06-11 | Tampering | A malicious manifest.json committed in a future PR could redirect WebP URLs to attacker domains | mitigate | (a) manifest.json is reviewed in git diffs; (b) the TS type guard via zod (`loadManifest()` parses + rejects bad shapes) catches structural drift; (c) the SW's `/exercises/*.webp` cache rule is matched on `url.pathname.startsWith('/exercises/')` so any external URL injected into a `poster` field is bypassed by the cache rule entirely (cache-first only applies to same-origin paths). External URLs would fail same-origin policy on next/image's `unoptimized` path unless the domain is added to `next.config.ts` images.remotePatterns — which it isn't. |

## Source Coverage Audit

| Source | Item | Plan Coverage |
|--------|------|---------------|
| GOAL (ROADMAP Phase 6) | Browse 80–120 curated exercises | P6-A.1 (ingest selects ~100) + P6-B.1 (page reads manifest) |
| GOAL | Filter by equipment (6 buckets) | P6-A.1 (taxonomy normalization) + P6-B.2 (FilterBar equipment chips) |
| GOAL | Filter by target muscle (6+ buckets) | P6-A.1 (muscle taxonomy) + P6-B.2 (FilterBar muscle chips) |
| GOAL | Equipment defaults to none + dumbbells | P6-B.2 (DEFAULT_EQUIPMENT_SELECTION + FilterBar initial state) |
| GOAL | WebP poster ≤ 30 kB | P6-A.1 (Pillow encode loop with budget enforcement) |
| GOAL | Tap card → detail page with instructions + meta | P6-B.3 (/workouts/[id] server component) |
| GOAL | Footer attribution + LICENSES.md | P6-D.1 (footer string + LICENSES.md content) |
| GOAL | Install as PWA | P6-C.1 (withSerwist wiring) + P6-C.2 (manifest.ts) |
| GOAL | Workout library renders fully offline | P6-C.3 (sw.ts CacheFirst on WebPs + SWR on /workouts + manifest) |
| GOAL | Offline meal POSTs queue + replay on reconnect | P6-C.4 (offline-meal-queue + register-sw 'online' drain) |
| GOAL | Lighthouse mobile ≥ 90 on /workouts | P6-E.1 (manual DevTools run + record in SUMMARY) |
| GOAL | Above-fold image weight ≤ 100 kB per route | P6-A.1 (poster ≤ 30 kB enforced) + P6-E.1 (manual measurement) |
| REQ WORK-01 | Curate 80–120 exercises | P6-A.1 |
| REQ WORK-02 | Equipment filter (6 buckets) | P6-A.1 + P6-B.2 |
| REQ WORK-03 | Muscle filter | P6-B.2 |
| REQ WORK-04 | Default `none + dumbbells` | P6-B.2 |
| REQ WORK-05 | Poster ≤ 30 kB; tap → animated media | P6-A.1 (poster budget) + P6-B.3 (detail page; **animated WebM deferred to v1.1**) |
| REQ WORK-06 | Detail page + (optional) YT embed | P6-B.3 (**YT embed deferred to v1.1** per CONTEXT D-YT-DEFER; instructions + detail WebP cover the need) |
| REQ WORK-07 | Footer attribution + LICENSES.md | P6-D.1 |
| REQ WORK-08 | Installable PWA + offline workout library + queued meal POSTs | P6-C.1 + P6-C.2 + P6-C.3 + P6-C.4 |
| REQ PERF-02 | Above-fold image budget ≤ 100 kB | P6-A.1 (encode budget) + P6-E.1 (measurement) |
| REQ PERF-03 | Lighthouse mobile ≥ 90 | P6-E.1 (manual run on Moto G Power emulation + Slow 4G) |
| CONTEXT D-FREE-DB-ONLY | Free Exercise DB exclusively | P6-A.1 (no wger import) |
| CONTEXT D-STATIC-FIRST | No Flask /exercises route | All Phase 6 work in frontend/ + scripts/; backend untouched |
| CONTEXT D-INGEST-PILLOW | Pillow WebP encoding | P6-A.1 |
| CONTEXT D-WEBP-BUDGETS | poster 320×240 ≤30 kB; detail 800×600 ≤80 kB | P6-A.1 (quality decay loop) |
| CONTEXT D-FILTER-DEFAULT | none + dumbbells on first open | P6-B.2 (DEFAULT_EQUIPMENT_SELECTION) |
| CONTEXT D-SERWIST-PWA | @serwist/next, not next-pwa | P6-C.1 |
| CONTEXT D-PWA-CACHE-STRATEGIES | SWR for HTML+manifest, cache-first for WebPs, network-first for /api/* | P6-C.3 (sw.ts route table) |
| CONTEXT D-BG-SYNC-MEAL-POSTS | Queue offline meal POSTs + replay on reconnect | P6-C.4 |
| CONTEXT D-MANIFEST-NATIVE | manifest.ts Next 15 file convention | P6-C.2 |
| CONTEXT D-WEBM-DEFER | Animated WebM deferred to v1.1 | Documented in plan goal + REQ WORK-05 status note (Slice E) |
| CONTEXT D-YT-DEFER | YouTube embed deferred to v1.1 | Documented in plan goal + REQ WORK-06 status note (Slice E) |
| CONTEXT D-NO-BACKEND-CHANGE | Phase 6 is FE-only | files_modified contains zero backend/* paths |
| CONTEXT D-PUBLIC-WORKOUTS | /workouts(.*) browseable pre-login | P6-D.1 (middleware.ts default-public matcher + comment) |
| CONTEXT D-NO-CI-IMAGE-GATE | Manual image-weight check, no CI gate | P6-E.1 |

**All items covered. No gaps.**

**Two interpretations beyond CONTEXT.md** (called out for the verify step + commit notes):
1. **Service worker pre-cache subset (24 of 100 posters).** CONTEXT.md says "PWA caches the static files"; this plan **does not pre-cache all 200 WebPs on first install** — instead it pre-caches the App Shell + /workouts + manifest + 24 most-likely-visible posters, with the rest filling in via runtime `CacheFirst`. Rationale: first-install on a metered Ghana connection should not blow 3–6 MB of data before the user has decided they like the app. The remaining WebPs cache as the user scrolls. Trade-off: first-launch-offline immediately after install (rare workflow) will miss the unscrolled posters until the user has scrolled them online once. T-06-09 disposition rationale.
2. **Idempotency-Key header on replayed meal POSTs.** offline-meal-queue.ts stamps an `Idempotency-Key: <uuid>` header on every queued POST. Flask currently ignores unknown headers (no breaking change), but this lays groundwork for future backend dedup. Not required by WORK-08; cheap to add, defends against an SW that re-issues a POST mid-flight on a flaky reconnect.

Both interpretations are LOW RISK and reversible. The user can ask for full-precache or no-idempotency-header in the SUMMARY review.

---

## Slice A — Ingest pipeline (3 tasks)

<task type="auto">
  <name>Task P6-A.1: Author scripts/ingest_exercises.py with Pillow WebP encoder + budget loop</name>
  <files>scripts/ingest_exercises.py, scripts/requirements-ingest.txt, scripts/README-ingest.md</files>
  <action>Create `scripts/ingest_exercises.py` as a one-shot CLI: argparse with `--commit <sha>` (default to a captured 2026-05-13 hash recorded in README-ingest.md) + `--out frontend/public/exercises` (default). Fetch `https://raw.githubusercontent.com/yuhonas/free-exercise-db/<sha>/dist/exercises.json` via httpx. Filter to entries whose `category` ∈ {strength, cardio} AND `level` ∈ {beginner, intermediate, expert}. Normalize Free Exercise DB's `equipment` field into the 6-bucket taxonomy via a literal mapping table: {'body only': 'none', 'dumbbell': 'dumbbell', 'bands': 'bands', 'kettlebells': 'kettlebells', 'barbell': 'barbell', 'pull-up bar': 'pull-up bar', 'machine'|'cable'|'medicine ball'|'foam roll'|'exercise ball'|'e-z curl bar': SKIP}. Normalize `primaryMuscles[0]` into the 8-bucket muscle taxonomy via a similar mapping table (e.g. 'middle back'|'lats'|'lower back'|'traps' → 'back'; 'quadriceps'|'hamstrings'|'calves' → 'legs'; 'biceps'|'triceps'|'forearms' → 'arms'; 'abdominals' → 'core'; 'glutes' → 'glutes'; 'shoulders' → 'shoulders'; 'chest' → 'chest'; entries with no clear primary or hitting 4+ buckets → 'full-body'). Selection: deterministic round-robin across the (equipment, muscle) Cartesian product, sorted by Free Exercise DB id, taking enough cells to land at ~100 entries total with at least one entry per (equipment, muscle) cell where the source supplies one. For each selected entry, download the two image URLs (Free Exercise DB hosts at `<repo>/exercises/<id>/images/0.jpg` and `1.jpg`); convert each with Pillow: resize to 320×240 (poster) or 800×600 (detail) preserving aspect (use `ImageOps.fit` with centre crop), then save as WebP starting `quality=72` `method=6`; if output exceeds 30 kB (poster) or 80 kB (detail), decrement quality by 4 and re-encode; loop until under budget or quality < 40 (then raise to surface to the operator). Write outputs to `frontend/public/exercises/{id}/poster.webp` + `detail.webp`. Emit `frontend/public/exercises/manifest.json` as a sorted JSON array (sorted by id) with the schema documented in the must_haves artifacts list (id, name, equipment, muscles_primary, muscles_secondary, category, level, mechanic, instructions, poster, detail). Pin the commit hash + the Free Exercise DB License (Unlicense) snippet in a header comment of manifest.json (use a `_meta` first entry rather than a JSON comment since JSON has no comments; `{"_meta": {"source": "https://github.com/yuhonas/free-exercise-db", "commit": "<sha>", "license": "Unlicense", "generated_at": "<ISO timestamp>"}}` followed by the entries array — OR — split into a top-level `{meta: {...}, entries: [...]}` object; the latter is cleaner and matches the zod schema in P6-B.1). Pick the `{meta, entries}` shape and write `frontend/src/lib/exercises.ts` against that shape. Author `scripts/requirements-ingest.txt` with pinned `httpx==0.27.*` and `Pillow==10.4.*`. Author `scripts/README-ingest.md` with: install instructions (Windows + macOS + Linux venv), run instructions, the captured commit hash for 2026-05-13, the budget enforcement explanation, the equipment/muscle mapping tables, a note that re-running with the same commit hash MUST yield byte-identical outputs (deterministic ordering test), and a T-06-08 mitigation note (manually audit the source repo at the pinned commit before committing the ingest output). DO NOT run the ingest script as part of executor verification (it requires network + ~5 MB of binary downloads); document running it manually as a developer workflow step in the README. The executor commits `scripts/ingest_exercises.py` + `scripts/requirements-ingest.txt` + `scripts/README-ingest.md` only.</action>
  <verify>
    <automated>cd scripts && python -c "import ast, pathlib; src = pathlib.Path('ingest_exercises.py').read_text(); ast.parse(src); assert 'Pillow' in pathlib.Path('requirements-ingest.txt').read_text() or 'pillow' in pathlib.Path('requirements-ingest.txt').read_text().lower(); assert 'httpx' in pathlib.Path('requirements-ingest.txt').read_text(); print('ingest script parses + deps pinned')"</automated>
  </verify>
  <done>scripts/ingest_exercises.py is syntactically valid Python; requirements-ingest.txt pins Pillow + httpx; README-ingest.md documents the run flow + commit hash + equipment/muscle mapping tables. No network calls made during executor verification.</done>
</task>

<task type="checkpoint:human-action" gate="blocking">
  <name>Task P6-A.2: Operator runs the ingest script and commits generated assets</name>
  <what-built>scripts/ingest_exercises.py from P6-A.1.</what-built>
  <how-to-verify>
    1. Open a PowerShell prompt at the repo root.
    2. `python -m venv .venv-ingest`
    3. `.venv-ingest\Scripts\Activate.ps1`
    4. `pip install -r scripts/requirements-ingest.txt`
    5. `python scripts/ingest_exercises.py --commit <hash-from-README-ingest.md>` (this fetches ~5 MB and runs Pillow over ~200 images — expect 3–5 minutes).
    6. Inspect `frontend/public/exercises/` — confirm ~100 subdirectories, each with `poster.webp` (≤30 kB) and `detail.webp` (≤80 kB), plus `manifest.json` at the top level.
    7. Spot-check three poster.webp files in Windows Explorer — they should render as plausible exercise images.
    8. `git add frontend/public/exercises/ && git status` — confirm ~200 WebPs + manifest.json staged.
    9. Type `approved` to continue, or describe any issues (e.g. an entry over budget that raised an exception).
  </how-to-verify>
  <resume-signal>Type "approved" once the WebPs + manifest.json are generated and staged in git (but not yet committed — Slice E commits everything together with the requirement flips).</resume-signal>
</task>

<task type="auto">
  <name>Task P6-A.3: Commit generated ingest output + add .gitattributes for binary WebPs</name>
  <files>frontend/public/exercises/.gitattributes</files>
  <action>Create `frontend/public/exercises/.gitattributes` with `*.webp binary` + `*.json text eol=lf` so Git does not try to diff binary WebPs and keeps the manifest JSON LF-normalized cross-platform. Stage the .gitattributes alongside the operator-generated WebPs + manifest.json from P6-A.2. Do NOT commit yet — the slice's combined commit happens in P6-E.1 after Lighthouse passes. The executor's task here is ONLY to author the .gitattributes file and verify the generated content from P6-A.2 is in `git status` (a sanity check, no destructive action).</action>
  <verify>
    <automated>cd frontend && node -e "const fs=require('fs');if(!fs.existsSync('public/exercises/.gitattributes'))throw 1;if(!fs.existsSync('public/exercises/manifest.json'))throw new Error('manifest.json missing — P6-A.2 must complete first');const m=JSON.parse(fs.readFileSync('public/exercises/manifest.json','utf8'));const entries=Array.isArray(m)?m:m.entries;if(!entries||entries.length<80||entries.length>120)throw new Error('entry count out of band: '+entries?.length);for(const e of entries){if(!['none','dumbbell','bands','pull-up bar','kettlebells','barbell'].includes(e.equipment))throw new Error('bad equipment: '+e.equipment+' on '+e.id);if(!e.poster?.startsWith('/exercises/'))throw new Error('bad poster path: '+e.poster);if(!e.detail?.startsWith('/exercises/'))throw new Error('bad detail path: '+e.detail);}console.log('manifest ok',entries.length,'entries');"</automated>
  </verify>
  <done>frontend/public/exercises/.gitattributes exists; manifest.json contains 80–120 entries; every entry's equipment is in the 6-bucket taxonomy; poster + detail paths are well-formed.</done>
</task>

---

## Slice B — Workout library UI (3 tasks)

<task type="auto" tdd="true">
  <name>Task P6-B.1: frontend/src/lib/exercises.ts types + filter helpers + zod manifest schema + unit tests</name>
  <files>frontend/src/lib/exercises.ts, frontend/src/lib/exercises.test.ts</files>
  <behavior>
    - Exports `ExerciseEntry` (TS interface mirroring the manifest schema) + `EquipmentBucket = 'none' | 'dumbbell' | 'bands' | 'pull-up bar' | 'kettlebells' | 'barbell'` + `MuscleBucket = 'chest' | 'back' | 'legs' | 'shoulders' | 'arms' | 'core' | 'glutes' | 'full-body'`.
    - Exports `DEFAULT_EQUIPMENT_SELECTION: EquipmentBucket[] = ['none', 'dumbbell']` (WORK-04).
    - Exports a zod schema `manifestSchema` that validates `{ meta: { source, commit, license, generated_at }, entries: ExerciseEntry[] }`. Reject any entry whose equipment is not in the 6-bucket union.
    - Exports `loadManifest(): Promise<ExerciseEntry[]>` — server-side only. `fs.readFile('frontend/public/exercises/manifest.json', 'utf8')` → JSON.parse → manifestSchema.parse → return entries.
    - Exports `filterExercises(entries, selection: { equipment: EquipmentBucket[], muscles: MuscleBucket[] }): ExerciseEntry[]`. Rules: empty `equipment` array → all equipment allowed; empty `muscles` array → all muscles allowed; non-empty → entry passes if `equipment ∈ selection.equipment` AND `(muscles_primary ∩ selection.muscles).length > 0`. Pure, no side effects.
    - Exports `findExerciseById(entries, id): ExerciseEntry | undefined`.
    - Tests (vitest):
      - `test_filter_default_selection_returns_only_none_or_dumbbell` — entries with mixed equipment; default selection returns the body-only + dumbbell subset.
      - `test_filter_intersects_equipment_and_muscles` — selection = {equipment: ['dumbbell'], muscles: ['chest']} → returns only dumbbell chest entries.
      - `test_filter_empty_selection_returns_all_entries`.
      - `test_filter_empty_intersection_returns_empty_array`.
      - `test_find_by_id_returns_match_or_undefined`.
      - `test_manifest_schema_rejects_unknown_equipment` — JSON with `equipment: 'machine'` → schema parse throws.
      - `test_manifest_schema_accepts_well_formed_meta_and_entries`.
      - `test_default_equipment_selection_constant` — assert `DEFAULT_EQUIPMENT_SELECTION` is exactly `['none', 'dumbbell']`.
  </behavior>
  <action>Implement the file against the manifest shape committed in P6-A.3 (`{meta, entries}`). Use zod (already in deps). The `loadManifest` function uses Node `fs/promises` — this is a server-only path; Next 15 will tree-shake the call out of any client bundle. Tests inject a fake manifest payload to exercise the filter logic without touching disk.</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/lib/exercises</automated>
  </verify>
  <done>8 vitest assertions pass; types + helpers exported; zod schema rejects malformed manifests.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P6-B.2: FilterBar + WorkoutsGrid + ExerciseCard + /workouts page</name>
  <files>frontend/src/app/workouts/page.tsx, frontend/src/app/workouts/workouts-grid.tsx, frontend/src/app/workouts/workouts-grid.test.tsx, frontend/src/app/workouts/filter-bar.tsx, frontend/src/app/workouts/filter-bar.test.tsx, frontend/src/app/workouts/exercise-card.tsx</files>
  <behavior>
    - `page.tsx` (server component): `export const dynamic = 'force-static'`; calls `loadManifest()`; passes `entries` to `<WorkoutsGrid entries={entries} />`. Wrapper renders the `<FilterBar>` inside `<WorkoutsGrid>` because the selection state belongs to the grid.
    - `workouts-grid.tsx` ('use client'): useState `selection = { equipment: DEFAULT_EQUIPMENT_SELECTION, muscles: [] }`. useMemo computes `filtered = filterExercises(entries, selection)`. Renders `<FilterBar selection onChange={setSelection} />` then a CSS grid `<div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4 p-4">` with one `<ExerciseCard entry>` per filtered entry. Empty state: `filtered.length === 0` → `<p>No exercises match these filters. Try adding more equipment or muscle groups.</p>`.
    - `filter-bar.tsx` ('use client'): receives `{ selection, onChange }`. Renders two chip rows: equipment (6 chips: none, dumbbell, bands, pull-up bar, kettlebells, barbell) and muscle (8 chips). Each chip is `<button aria-pressed={selection.equipment.includes(bucket)} onClick={() => toggle(bucket)}>` with active styling via tailwind variants (`bg-emerald-500 text-white` when pressed, `bg-muted text-muted-foreground` when not). Sticky-top: `sticky top-0 z-10 bg-background/95 backdrop-blur border-b py-3`. Display human-readable labels (e.g. 'No equipment', 'Dumbbells', 'Resistance bands', 'Pull-up bar', 'Kettlebells', 'Barbell'; 'Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core', 'Glutes', 'Full body').
    - `exercise-card.tsx` (server component): `<Link href={`/workouts/${entry.id}`} className="block rounded-lg border bg-card hover:shadow-md transition-shadow">` wrapping `<Image src={entry.poster} alt={entry.name} width={320} height={240} unoptimized loading="lazy" className="rounded-t-lg" />` + a footer block with `<h3>{entry.name}</h3>` + `<p className="text-xs text-muted-foreground">{equipmentLabel} · {primaryMuscleLabel}</p>`. The `unoptimized` prop ships the existing WebP as-is — no next/image runtime optimization needed because the file is already poster-sized + WebP.
    - Tests (vitest + @testing-library):
      - `test_filter_bar_default_marks_none_and_dumbbell_pressed` — render with default selection; query for `[aria-pressed=true]` and assert two chips matched.
      - `test_filter_bar_click_toggles_chip` — render, click 'Chest' chip, assert onChange fired with `muscles: ['chest']`.
      - `test_filter_bar_click_pressed_chip_removes_it` — start with `equipment: ['dumbbell']`, click Dumbbell chip → onChange with `equipment: []`.
      - `test_filter_bar_keyboard_enter_toggles` — focus chip + fireEvent.keyDown Enter → onChange fired.
      - `test_workouts_grid_renders_one_card_per_filtered_entry` — pass 4 entries (2 dumbbell + 2 barbell); default selection (none+dumbbell) renders 2 cards.
      - `test_workouts_grid_empty_state_when_filter_returns_zero` — pass entries that none match; assert empty-state copy in DOM.
  </behavior>
  <action>Implement the four files. Tailwind utility classes only — no shadcn primitives needed beyond the existing `<Button>` if convenient (the chips are bare buttons here for tighter styling control). All chip labels are hard-coded English (i18n is post-MVP). The default selection is read from `DEFAULT_EQUIPMENT_SELECTION` (P6-B.1) so a future change updates both the helper test and the FilterBar test in one place. /workouts page has NO auth check — middleware already leaves /workouts public by default (P6-D.1 documents this).</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/app/workouts</automated>
  </verify>
  <done>6 vitest assertions pass; /workouts route compiles; FilterBar + WorkoutsGrid + ExerciseCard render against a fixture manifest without console errors.</done>
</task>

<task type="auto">
  <name>Task P6-B.3: /workouts/[id] detail page + generateStaticParams + not-found</name>
  <files>frontend/src/app/workouts/[id]/page.tsx, frontend/src/app/workouts/[id]/not-found.tsx</files>
  <action>Create `frontend/src/app/workouts/[id]/page.tsx` as a server component. `export const dynamic = 'force-static'`. `export async function generateStaticParams()` calls `loadManifest()` and returns `entries.map(e => ({ id: e.id }))` so every detail page is statically generated at build time. The page reads `params.id`, calls `loadManifest()` (Next 15 dedupes the fetch across the same request) → `findExerciseById(entries, params.id)` → `if (!entry) notFound()`. Renders a layout: header with name + back link to /workouts; `<Image src={entry.detail} alt={entry.name} width=800 height=600 unoptimized priority />`; metadata row (`Equipment: <equipment>`, `Primary muscle: <muscle>`, `Level: <level>`, `Category: <category>`); `<ol className="list-decimal pl-5 space-y-2">` of instruction steps. DO NOT add a YouTube embed (CONTEXT.md D-YT-DEFER). DO NOT add a WebM/video element (CONTEXT.md D-WEBM-DEFER). Author `frontend/src/app/workouts/[id]/not-found.tsx` with a friendly 404 + `<Link href="/workouts">Back to workouts</Link>`.</action>
  <verify>
    <automated>cd frontend && pnpm build 2>&1 | tee /tmp/p6-b3-build.log | grep -E "(workouts/\[id\]|Compiled|error)" | head -20; echo "---"; node -e "const fs=require('fs');const p=fs.readFileSync('src/app/workouts/[id]/page.tsx','utf8');if(/iframe|youtube|webm|<video/i.test(p))throw new Error('forbidden YT/WebM embed in detail page');if(!/notFound\(\)/.test(p))throw new Error('missing notFound() call');if(!/generateStaticParams/.test(p))throw new Error('missing generateStaticParams');console.log('detail page ok');"</automated>
  </verify>
  <done>`pnpm build` includes `/workouts/[id]` in the static route table with one static path per manifest entry; detail page has no iframe/youtube/webm tokens; notFound() is reachable for missing ids.</done>
</task>

---

## Slice C — PWA + offline (4 tasks)

<task type="auto">
  <name>Task P6-C.1: Install @serwist/next + idb-keyval + wire withSerwist into next.config.ts + create manifest.ts + icon assets</name>
  <files>frontend/package.json, frontend/next.config.ts, frontend/src/app/manifest.ts, frontend/public/icons/icon-192.png, frontend/public/icons/icon-512.png, frontend/public/icons/maskable-512.png</files>
  <action>1. `cd frontend && pnpm add @serwist/next@^9 serwist@^9 idb-keyval@^6`. If the install fails under `--frozen-lockfile` due to a Next 15.2.4 peer-version mismatch, edit `frontend/package.json` to relax the offending peer + regenerate `pnpm-lock.yaml` in the SAME commit (do NOT add `--no-frozen-lockfile`). 2. Edit `frontend/next.config.ts` to import `withSerwist` from `@serwist/next` and wrap the default export: `export default withSerwist({ swSrc: 'src/app/sw.ts', swDest: 'public/sw.js', cacheOnNavigation: true, reloadOnOnline: true, register: false, disable: process.env.NODE_ENV === 'development' })(nextConfig)`. The `register: false` flag delegates registration to RegisterSW (P6-C.4) so we can co-locate it with the queue-drain effect. `disable` in dev avoids the SW caching during HMR. 3. Author `frontend/src/app/manifest.ts` as a default-exported `MetadataRoute.Manifest`: `{ name: 'FitGH', short_name: 'FitGH', description: 'Snap a meal, see kcal — track Ghanaian food and workouts.', start_url: '/dashboard', display: 'standalone', orientation: 'portrait-primary', background_color: '#ffffff', theme_color: '#10b981', icons: [{ src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' }, { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' }, { src: '/icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }] }`. 4. Generate the three icon PNGs: use a small one-off Python+Pillow snippet documented in scripts/README-ingest.md (an 'F' monogram in white on `#10b981` background; the maskable variant adds 64 px of safe-zone padding so the centre 384 px is the visible glyph). Commit the three PNG files; do NOT commit the generation snippet (it's a Pillow one-liner — same handling as the manifest schema regen in Phase 5).</action>
  <verify>
    <automated>cd frontend && node -e "const p=require('./package.json');if(!p.dependencies['@serwist/next'])throw new Error('@serwist/next missing');if(!p.dependencies['serwist'])throw new Error('serwist missing');if(!p.dependencies['idb-keyval'])throw new Error('idb-keyval missing');for(const banned of ['next-pwa','workbox-webpack-plugin','@rive-app/react-canvas','@sentry/nextjs','@vercel/analytics']){if(p.dependencies[banned]||p.devDependencies?.[banned])throw new Error('banned dep: '+banned);}const cfg=require('fs').readFileSync('next.config.ts','utf8');if(!/withSerwist/.test(cfg))throw new Error('next.config.ts missing withSerwist');const m=require('fs').readFileSync('src/app/manifest.ts','utf8');if(!/standalone/.test(m))throw new Error('manifest.ts missing display:standalone');if(!/#10b981/.test(m))throw new Error('manifest.ts missing emerald theme color');const fs=require('fs');for(const f of ['public/icons/icon-192.png','public/icons/icon-512.png','public/icons/maskable-512.png']){if(!fs.existsSync(f))throw new Error('missing icon '+f);}console.log('serwist + manifest + icons ok');" && pnpm install --frozen-lockfile</automated>
  </verify>
  <done>@serwist/next + serwist + idb-keyval in dependencies; next.config.ts wraps with withSerwist; manifest.ts emits a valid MetadataRoute.Manifest; 3 icon PNGs present in public/icons/; pnpm install --frozen-lockfile succeeds; no banned deps added.</done>
</task>

<task type="auto">
  <name>Task P6-C.2: Author frontend/src/app/sw.ts with route table (cache-first WebPs / SWR HTML / network-only API)</name>
  <files>frontend/src/app/sw.ts</files>
  <action>Create `frontend/src/app/sw.ts` per the Serwist v9 + Next 15 reference shape. Imports: `import { defaultCache } from '@serwist/next/worker'; import { type PrecacheEntry, type SerwistGlobalConfig, Serwist, NetworkOnly, NetworkFirst, CacheFirst, StaleWhileRevalidate, ExpirationPlugin } from 'serwist';`. Declare `declare global { interface WorkerGlobalScope extends SerwistGlobalConfig { __SW_MANIFEST: (PrecacheEntry | string)[] | undefined; } }; declare const self: ServiceWorkerGlobalScope;`. Instantiate `const serwist = new Serwist({ precacheEntries: self.__SW_MANIFEST, skipWaiting: true, clientsClaim: true, navigationPreload: true, runtimeCaching: [ { matcher: ({ url }) => url.pathname.startsWith('/api/'), handler: new NetworkOnly() }, { matcher: ({ url }) => url.pathname.startsWith('/exercises/') && url.pathname.endsWith('.webp'), handler: new CacheFirst({ cacheName: 'exercise-webp-v1', plugins: [new ExpirationPlugin({ maxEntries: 250, maxAgeSeconds: 30 * 24 * 60 * 60, purgeOnQuotaError: true })] }) }, { matcher: ({ url }) => url.pathname === '/exercises/manifest.json', handler: new StaleWhileRevalidate({ cacheName: 'exercise-manifest-v1' }) }, { matcher: ({ url }) => url.pathname.startsWith('/workouts'), handler: new StaleWhileRevalidate({ cacheName: 'workouts-html-v1' }) }, ...defaultCache ] }); serwist.addEventListeners();`. The `precacheEntries: self.__SW_MANIFEST` array is injected by Serwist's build step — at minimum, it contains the App Shell. We do NOT need to manually add the 24 poster WebPs to the precache list; the `CacheFirst` runtime rule populates them on first visit, and Lighthouse's PWA audit only checks that the SW is registered and the offline fallback works (not that 100 WebPs are pre-cached). T-06-09 disposition: defer the explicit 24-poster precache subset; revisit if Lighthouse offline audit fails. (This is an interpretation tightening: drop the precache-subset complexity for v1 to minimize moving parts; revisit if needed in P6-E.1.) Order matters in `runtimeCaching` — `/api/*` rule MUST come before any fallback, and the `/exercises/*.webp` rule MUST come before the `/exercises/manifest.json` rule (since the manifest is also under /exercises/).</action>
  <verify>
    <automated>cd frontend && node -e "const fs=require('fs');const sw=fs.readFileSync('src/app/sw.ts','utf8');for(const k of ['NetworkOnly','CacheFirst','StaleWhileRevalidate','ExpirationPlugin','/api/','/exercises/','manifest.json','/workouts','addEventListeners']){if(!sw.includes(k))throw new Error('sw.ts missing: '+k);}if(sw.indexOf('/api/')>sw.indexOf('/exercises/'))throw new Error('order: /api/ rule must come before /exercises/ rule');if(sw.indexOf('/exercises/')>sw.indexOf('manifest.json')&&!sw.includes('.webp'))throw new Error('order check failed');console.log('sw.ts route table ok');" && pnpm build 2>&1 | grep -E "(sw\\.js|service worker|Compiled|error)" | head -20</automated>
  </verify>
  <done>sw.ts contains all four route handlers in the correct order; pnpm build emits public/sw.js (Serwist compile step); no TypeScript errors.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P6-C.3: Offline meal queue + IndexedDB persistence + drain logic + unit tests</name>
  <files>frontend/src/components/pwa/offline-meal-queue.ts, frontend/src/components/pwa/offline-meal-queue.test.ts</files>
  <behavior>
    - `enqueueMealPost({ url, body, headers })`: stamp a `Idempotency-Key: <uuid-v4>` header (use `crypto.randomUUID()`), prepend to the idb-keyval store under key `'meal_queue'` (which holds an array of `{ id, url, body, headers, enqueuedAt }`). Enforce `MAX_QUEUE_SIZE = 50` by dropping the oldest entry and surfacing a Sonner toast 'Offline meal queue full — earliest pending meal dropped' (T-06-05).
    - `drainMealQueue()`: read the array; iterate oldest-first; for each, `fetch(url, { method: 'POST', body, headers: { ...headers, 'X-Replayed-Offline': '1' }, credentials: 'include' })`. On 2xx → remove from queue. On 401 → break the loop, surface 'Please sign in to send your offline meals' (queue retained for the next attempt; T-06-02 partial). On 4xx other than 401 → drop the entry, surface 'Could not sync 1 meal — error <status>' (Sonner). On 5xx or network error → leave queued; the next 'online' event retries. Returns `{ synced, retained, dropped }` counts. Idempotent: calling drainMealQueue twice quickly while the first is in flight is guarded by an in-memory `isDraining` boolean.
    - `getQueueSize()`: returns the array length.
    - `clearMealQueue()`: idb-keyval del — used by the sign-out flow (T-06-02 mitigation; sign-out integration is OPTIONAL for this task — the function exists, the wiring into sign-out-button.tsx can be a follow-up; for v1, calling drain on 401 retains the queue, and a fresh user signing in on the same device will see the previous user's queue ONCE before the drain's first 401 stops it — accepted in T-06-02 narrative).
    - Use `idb-keyval`'s `get`/`set`/`del` with the single key `'meal_queue'` — keeping it as a single array key avoids needing a custom IDBObjectStore.
    - Tests (vitest + fake-indexeddb):
      - `test_enqueue_then_drain_replays_request` — mock `fetch` to return 201; enqueue 1; drain; assert fetch called with idempotency header + X-Replayed-Offline=1 + queue empty after.
      - `test_drain_breaks_on_401_and_retains_queue` — mock fetch to return 401; enqueue 1; drain; assert queue still has 1.
      - `test_drain_drops_on_400_other_than_401` — mock fetch to return 422; enqueue 1; drain; assert queue empty + (no second retry).
      - `test_drain_leaves_queued_on_5xx` — mock fetch to return 503; enqueue 1; drain; assert queue still has 1.
      - `test_drain_leaves_queued_on_network_error` — mock fetch to throw; enqueue 1; drain; assert queue still has 1.
      - `test_max_queue_size_drops_oldest` — enqueue 51 entries; assert queue length === 50 and the first-enqueued is gone.
      - `test_idempotency_key_present_on_each_entry` — enqueue 3 entries; inspect each; assert distinct UUID v4 strings.
      - `test_get_queue_size_returns_count`.
    - Use `vi.stubGlobal('fetch', ...)` to mock fetch; use `'fake-indexeddb/auto'` import at the top of the test file to back idb-keyval.
  </behavior>
  <action>Implement the module. Add `fake-indexeddb` to devDependencies (`pnpm add -D fake-indexeddb@^6`). Author the 8 tests in `offline-meal-queue.test.ts`. The module is client-only — guard `typeof window !== 'undefined'` if called from a server context (it shouldn't be, but defensive).</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/components/pwa/offline-meal-queue</automated>
  </verify>
  <done>8 vitest assertions pass; idb-keyval-backed queue handles all status-code dispositions; idempotency keys are unique UUIDs; MAX_QUEUE_SIZE caps growth.</done>
</task>

<task type="auto">
  <name>Task P6-C.4: RegisterSW + OfflineIndicator + InstallPrompt client components + layout.tsx mount</name>
  <files>frontend/src/components/pwa/register-sw.tsx, frontend/src/components/pwa/offline-indicator.tsx, frontend/src/components/pwa/install-prompt.tsx, frontend/src/app/layout.tsx</files>
  <action>1. `register-sw.tsx` ('use client'): on mount, if `'serviceWorker' in navigator && process.env.NODE_ENV === 'production'`, call `navigator.serviceWorker.register('/sw.js', { scope: '/' })`. ALSO add a window 'online' listener that calls `drainMealQueue()` from offline-meal-queue.ts. Cleanup the listener on unmount. Renders null. ~30 LOC. 2. `offline-indicator.tsx` ('use client'): useState `online = navigator.onLine` initialized in useEffect (SSR-safe). Listen to 'online' + 'offline' window events; setOnline. When `!online`, render `<div className="fixed bottom-4 right-4 z-50 rounded-full bg-amber-100 border border-amber-300 text-amber-900 px-3 py-1.5 text-xs font-medium shadow-md">Offline — meals will sync on reconnect</div>`. On reconnect (false → true transition), call `toast.success(\`Back online — syncing meals...\`)` from sonner. ~40 LOC. 3. `install-prompt.tsx` ('use client'): capture `beforeinstallprompt` event; show a dismissable banner ONLY when pathname === '/dashboard' (read via next/navigation `usePathname`) AND localStorage `fitgh.install-dismissed` !== '1'. Banner: 'Install FitGH for offline workouts and faster meal logging' + 'Install' button (calls `event.prompt()`) + 'Dismiss' button (sets localStorage flag + setState to hide). ~50 LOC. 4. Edit `frontend/src/app/layout.tsx`: import `{ RegisterSW }`, `{ OfflineIndicator }`, `{ InstallPrompt }` from `@/components/pwa/...`. Mount all three INSIDE `<ClerkProvider>` and INSIDE `<body>`, after the existing `<ServicePausedBanner />` and before `{children}`. The native PWA manifest is auto-linked by Next 15 from `src/app/manifest.ts` — no `<link rel="manifest">` edit needed in layout.tsx. ALSO: extend the existing `<footer>` to include the Free Exercise DB attribution line: `<span>Exercise data from <a href="https://github.com/yuhonas/free-exercise-db" className="underline-offset-4 hover:underline" rel="noopener noreferrer" target="_blank">Free Exercise DB</a> (Unlicense)</span>` — place it in the footer's existing flex layout. (P6-D.1 handles the LICENSES.md side.)</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/components/pwa 2>&1 | tail -10; echo "---"; node -e "const l=require('fs').readFileSync('src/app/layout.tsx','utf8');for(const k of ['RegisterSW','OfflineIndicator','InstallPrompt','Free Exercise DB']){if(!l.includes(k))throw new Error('layout.tsx missing: '+k);}console.log('layout.tsx ok');" && pnpm build 2>&1 | grep -E "(workouts|sw\\.js|First Load|Compiled|error)" | head -30</automated>
  </verify>
  <done>RegisterSW + OfflineIndicator + InstallPrompt mount in layout.tsx without TS errors; footer contains Free Exercise DB attribution; pnpm build succeeds; sw.js emitted; existing layout tests (if any) pass.</done>
</task>

---

## Slice D — Attribution + LICENSES.md + middleware comment (1 task)

<task type="auto">
  <name>Task P6-D.1: Author LICENSES.md at repo root + add middleware.ts public-route comment block</name>
  <files>LICENSES.md, frontend/middleware.ts</files>
  <action>1. Create `LICENSES.md` at the repo root with sections: `## Exercise Data` — Free Exercise DB (Unlicense) link + the canonical Unlicense text excerpt + statement that 'FitGH redistributes a curated, re-encoded subset of Free Exercise DB images and metadata under this licence.'; `## Third-Party Services` — Anthropic (Claude Sonnet 4.6 vision; link to Anthropic's commercial ToS) + MongoDB Atlas (Atlas ToS) + Clerk (Clerk ToS) + Render (Render ToS), one line each describing the role; `## Open-Source Dependencies` — pointer to `frontend/package.json` + `backend/requirements.txt` for the full dependency tree; each package retains its upstream licence; `## FitGH Source Code` — 'TBD — no licence chosen as of 2026-05-13. Source is private until a licence decision in Phase 7 or later.'; `## Attribution Required by Source` — Free Exercise DB Unlicense does NOT require attribution; FitGH provides attribution as good-citizen practice in the global footer (P6-C.4). 2. Edit `frontend/middleware.ts`: do NOT change the matcher or the protected-route list — `/workouts(.*)` is NOT in `isProtectedRoute`, which makes it public by default. ADD a comment block near the top of the file (above the `isProtectedRoute` declaration) reading: `// Phase 6 (Workout Library + PWA): /workouts(.*) is intentionally NOT in the //  protected route list. The workout library is browseable pre-login as an //  onboarding incentive (CONTEXT.md D-PUBLIC-WORKOUTS). The Clerk middleware //  default-public behaviour applies; no edit to isProtectedRoute is needed.`. This is documentation only — no behavioural change. T-01-01 inheritance (Phase 1 middleware threat model) still applies for /dashboard + /api/*.</action>
  <verify>
    <automated>node -e "const fs=require('fs');const l=fs.readFileSync('LICENSES.md','utf8');for(const k of ['Free Exercise DB','Unlicense','Anthropic','MongoDB','Clerk','Render','Open-Source Dependencies','FitGH Source Code']){if(!l.includes(k))throw new Error('LICENSES.md missing: '+k);}const m=fs.readFileSync('frontend/middleware.ts','utf8');if(!/Phase 6.*Workout Library/i.test(m))throw new Error('middleware.ts missing Phase 6 public-route comment');if(/createRouteMatcher\\(\\[[^\\]]*\\/workouts/.test(m))throw new Error('middleware.ts must NOT add /workouts to protected list');console.log('attribution + middleware comment ok');"</automated>
  </verify>
  <done>LICENSES.md exists at repo root with all required sections; middleware.ts has the Phase 6 public-route comment and continues to leave /workouts public.</done>
</task>

---

## Slice E — Verify + traceability (1 task)

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task P6-E.1: Lighthouse smoke + above-fold image-weight measurement + REQUIREMENTS.md / ROADMAP.md flip</name>
  <what-built>The full Phase 6 build: /workouts route, /workouts/[id] detail page, sw.js service worker, PWA manifest, offline indicator + queue, footer attribution, LICENSES.md.</what-built>
  <how-to-verify>
    1. `cd frontend && pnpm build && pnpm start` (production build serves /sw.js correctly; `pnpm dev` does NOT register the SW due to `disable: NODE_ENV==='development'` in next.config.ts).
    2. Open `http://localhost:3000/workouts` in Chrome. Open DevTools → Lighthouse panel → category 'Performance' + 'PWA' → device 'Mobile' → throttling 'Simulated throttling (default)' → 'Analyze page load'. Wait ~30–60 s.
    3. Record the Performance score (target ≥ 90 per PERF-03). If < 90, note the failing audits in 06-SUMMARY.md and decide: fix vs accept. The PWA category should show 'Installable' = true.
    4. Open DevTools → Application → Service Workers → confirm `/sw.js` is `activated`. Application → Manifest → confirm name=FitGH + theme_color=#10b981 + icons rendered.
    5. Above-fold image-weight measurement: DevTools → Network panel → 'Disable cache' + filter by `Img` + reload /workouts. Sum the transferred sizes of all WebPs that are above the fold at viewport 360×800 (the first 2–3 cards). Confirm ≤ 100 kB total per PERF-02. Record the measured value in 06-SUMMARY.md.
    6. Offline smoke test: DevTools → Network → check 'Offline' → hard reload /workouts → confirm the page still renders with cards (cache-first WebPs + SWR /workouts HTML). Click into one detail page — confirm the detail WebP renders (or, on first-ever offline visit to that specific id, the cache-miss is acceptable — record in SUMMARY).
    7. Offline meal queue smoke test: in DevTools console at /dashboard, dispatch `window.dispatchEvent(new Event('offline'))` to simulate offline; submit a meal POST (via the existing meal-log form); confirm Sonner toast indicates the meal was queued; dispatch `window.dispatchEvent(new Event('online'))`; confirm a 'Synced 1 meal' toast and the meal appears in /api/meals on the next /dashboard fetch.
    8. PWA install smoke test (optional, if Chrome shows the install prompt): click the address-bar install icon → confirm FitGH installs as a standalone app and `/workouts` works offline in the installed window. (Skip on Edge/Safari — Chrome desktop or Android Chrome only.)
    9. Edit `.planning/REQUIREMENTS.md`: flip WORK-01..WORK-08 + PERF-02 + PERF-03 from `[ ]` to `[x]`. Traceability table status column → 'Complete'. Add the status notes from the must_haves artifacts list (WORK-05 WebM deferred, WORK-06 YT deferred, PERF-02/03 manual check, WORK-07 Free Exercise DB only).
    10. Edit `.planning/ROADMAP.md`: flip Phase 6 row in the Progress table to Complete + record completion date.
    11. Stage everything (the WebPs from P6-A.2 + P6-A.3, all Phase 6 code from B/C/D, and the requirement flips from E.1) and write 06-SUMMARY.md following the template at `~/.claude/get-shit-done/templates/summary.md`, recording: Lighthouse score, above-fold weight, total file count change, the two CONTEXT-beyond interpretations (precache-subset dropped, idempotency header added), and links to threat IDs that have been validated vs accepted-for-v1.
    12. Type `approved` to continue, or describe any failures (especially Lighthouse < 90 or offline-smoke failures).
  </how-to-verify>
  <resume-signal>Type "approved" once Lighthouse passes ≥ 90 on /workouts, the offline smoke tests work, requirement flips are written, and 06-SUMMARY.md is drafted. If Lighthouse score is in the 85–89 band, type "accept with note" and document the gap in SUMMARY (the score floor is the ROADMAP target; the user can decide to accept and ship).</resume-signal>
</task>

---

## Phase Verification

After all 12 tasks complete:

- **Build:** `cd frontend && pnpm build` succeeds; `/workouts` and `/workouts/[id]` appear in the static route table; `public/sw.js` is emitted by Serwist; `public/manifest.webmanifest` (or equivalent) is auto-generated from `manifest.ts`.
- **Tests:** `pnpm vitest run` reports all new test suites passing (exercises lib + filter-bar + workouts-grid + offline-meal-queue → ≥ 8 new assertions); backend test count UNCHANGED (no backend work).
- **Manifest:** `frontend/public/exercises/manifest.json` contains 80–120 entries; each entry's `equipment` ∈ the 6-bucket taxonomy; each entry's `poster` + `detail` paths point to existing WebP files; every poster ≤ 30 kB; every detail ≤ 80 kB (validated by spot-check during P6-A.2 + a script-level assertion in the ingest itself).
- **PWA:** Chrome DevTools → Application → Manifest renders FitGH; service worker activated; `/workouts` works fully offline (cache-first WebPs + SWR HTML); offline meal POSTs queue + replay on reconnect (validated in P6-E.1 step 7).
- **Lighthouse:** /workouts Performance ≥ 90 on Mobile + Simulated Throttling (recorded in SUMMARY).
- **Image budget:** Above-fold WebPs on /workouts at 360×800 viewport total ≤ 100 kB (recorded in SUMMARY).
- **Attribution:** Global footer shows 'Exercise data from Free Exercise DB (Unlicense)'; `LICENSES.md` at repo root credits Free Exercise DB + Anthropic + MongoDB + Clerk + Render.
- **Middleware:** `/workouts` and `/workouts/[id]` are browseable without authentication (verify by opening an incognito window and hitting `http://localhost:3000/workouts`).
- **No regressions:** `/dashboard`, `/profile`, `/settings`, `/history`, `/onboarding` continue to work; the existing Sonner Toaster is shared with the new OfflineIndicator + drain notices; existing Clerk middleware still gates `/api/*`.
- **No banned deps:** `package.json` shows zero of: `next-pwa`, `@rive-app/*`, `lottie-react`, `framer-motion`, `@sentry/nextjs`, `@vercel/analytics`, `workbox-webpack-plugin`.

## Success Criteria (binding)

1. **WORK-01..04:** /workouts grid renders ≥80 ≤120 cards; FilterBar 6 equipment + 6+ muscle chips; default selection `none + dumbbell` marks two chips pressed on first open.
2. **WORK-05 / WORK-06:** Poster files all ≤30 kB; detail page renders large WebP + instructions + meta with no YouTube embed and no WebM video element. (Deferrals documented in REQUIREMENTS.md.)
3. **WORK-07:** Footer + LICENSES.md present.
4. **WORK-08:** PWA installs from Chrome Mobile; /workouts renders offline; queued meal POST replays on `online` event.
5. **PERF-02 + PERF-03:** Lighthouse Performance ≥ 90 manually measured; above-fold image weight ≤ 100 kB manually measured. Both values recorded in 06-SUMMARY.md.
6. **REQUIREMENTS.md + ROADMAP.md:** WORK-01..08 + PERF-02 + PERF-03 flipped to Complete; Phase 6 row in Progress table flipped to Complete with date 2026-05-13.

---

*Phase 6 plan written by gsd-planner on 2026-05-13. Goal-backward analysis applied; 12 tasks across 5 slices; 11-row STRIDE register; source coverage audit verifies every ROADMAP + CONTEXT decision lands in a task. No Flask /exercises route, no Mongo exercises collection, no wger, no next-pwa, no WebM, no YouTube embed, no CI image-weight gate — all per CONTEXT.md decisions D-FREE-DB-ONLY / D-STATIC-FIRST / D-SERWIST-PWA / D-WEBM-DEFER / D-YT-DEFER / D-NO-CI-IMAGE-GATE.*
