# Phase 6: Workout Library + PWA — Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — user driving autonomous mode)

<domain>
## Phase Boundary

A user browses 80–120 curated exercises, filters by equipment (none, dumbbells, bands, pull-up bar, kettlebell, barbell) and target muscle (chest, back, legs, shoulders, arms, core, glutes, full-body), sees a tiny WebP poster on each card, taps to load an animated WebM/GIF, and installs FitGH as a PWA that works offline for the workout library — plus queues meal logs (Phase 4 vision + Phase 3 manual) taken on flaky connections.

</domain>

<decisions>
## Implementation Decisions

### Data sources — Free Exercise DB only (Unlicense)

**Locked deviation from the original ROADMAP picks.** Original plan was "Free Exercise DB Unlicense + wger CC-BY-SA". Going **Free Exercise DB exclusively** to dodge wger's share-alike licence — Free Exercise DB has ~800 entries which is far more than the 80–120 we need, so the wger backstop is unnecessary.

- Source: https://github.com/yuhonas/free-exercise-db — Unlicense (effectively public domain, no attribution required).
- Curate **~100 entries** spanning the 6 muscle groups × 6 equipment buckets per the ROADMAP filter axes.
- Attribution: footer credit anyway (good-citizen practice): "Exercise data from Free Exercise DB (Unlicense)". `LICENSES.md` in repo root.

### Static-first architecture (no backend route for exercises)

- Exercises are **static reference data** — they never change at runtime. Serve from `frontend/public/exercises/manifest.json` + per-exercise asset folders. **No Flask `/exercises` endpoint needed.**
- Client-side filter/search over the 100-entry manifest (trivially fast in JS — no need for backend search index).
- This sidesteps Render's Free tier compute for static lookups AND makes offline-first trivial (PWA caches the static files).

### Ingest script

- `scripts/ingest_exercises.py` (Python) — one-shot, run manually pre-deploy:
  1. Fetches Free Exercise DB JSON from raw GitHub.
  2. Filters to the 6 muscle groups × 6 equipment buckets defined in ROADMAP.
  3. Selects ~100 representative exercises (balanced across muscle/equipment).
  4. Downloads images, converts each to **WebP** via Pillow (poster: 320×240, q=72, ≤30 kB; detail: 800×600 same q, ≤80 kB).
  5. Writes per-exercise WebP files to `frontend/public/exercises/<exercise_id>/poster.webp` and `detail.webp`.
  6. Writes normalized JSON to `frontend/public/exercises/manifest.json` — `[{id, name, equipment, muscles_primary[], muscles_secondary[], category, level, mechanic, instructions[], poster: "/exercises/{id}/poster.webp", detail: "/exercises/{id}/detail.webp"}]`.
- The ingest script commits its output to the repo (the WebP files + manifest.json go into git). Idempotent — re-running with the same source yields identical files (deterministic ordering).

### Frontend routes + UX

- `/workouts` — grid/list of exercise cards; sticky filter bar (equipment chips + muscle chips). Cards show WebP poster + name + equipment + primary muscle.
- `/workouts/[id]` — exercise detail. Shows large WebP, instructions list, equipment, target muscles. (Optional YouTube embed deferred — see Deferred Ideas.)
- Equipment filter defaults to **`none + dumbbells`** on first open (per ROADMAP SC).
- Empty-state for filter combinations with no matches.

### PWA + offline strategy

- Use **`@serwist/next`** (the modern `next-pwa` successor that supports Next.js 15 App Router). Install + wire `app/sw.ts` service worker.
- **Cache strategies:**
  - `/workouts/*` HTML + `manifest.json` → **stale-while-revalidate** (offline-first; checks network in background).
  - `/exercises/**/*.webp` → **cache-first** (rarely changes; cache lasts 30 days).
  - `/api/*` → **network-first** (auth-gated, must hit Clerk/Atlas).
  - Other assets → **stale-while-revalidate**.
- **Background sync for meal POSTs:** queue offline POSTs to `/api/meals` and `/api/meals/scan` (the latter only if the device has the image in its `BackgroundFetch` API support; otherwise reject offline). Replay on `online` event.
- **Manifest:** `frontend/src/app/manifest.ts` (Next.js native PWA manifest) with `name: "FitGH"`, theme color from existing Tailwind palette, 192/512 icons, `display: standalone`.
- **PWA install prompt:** show as a dismissable banner on the dashboard after first successful sign-in (defer for first session — don't badger).

### Image sizing + bundle budget

- Poster WebP target: ≤ 30 kB each (320×240 q=72). Manifest with 100 posters = ~3 MB total — cached eagerly by service worker on first install.
- Detail WebP: ≤ 80 kB each. Loaded on demand when the user opens an exercise detail page.
- ROADMAP says "above-fold image weight ≤ 100 KB per route enforced in CI" — **CI gate intentionally absent** per the Render-only architecture. Manual check at phase boundary. /workouts above-fold = 2–3 posters initially visible = 60–90 kB, under target.

### Lighthouse mobile ≥ 90 (workout-library route)

Target stated in ROADMAP SC-5. **Validated manually with Lighthouse from DevTools** (Moto G Power emulation + Slow 4G throttle). Not a CI gate. Record the score in the SUMMARY; flag if < 90.

### Backend changes (minimal)

- **No `/exercises` route added** (static frontend serves everything).
- **No new collection** in Mongo (exercises live in `public/`).
- Phase 6 backend work is limited to verifying the existing meal endpoints handle offline-queued requests correctly (which they already do — they're stateless authenticated POSTs).

</decisions>

<code_context>
## Existing Code Insights

- `frontend/next.config.ts` — needs `withSerwist` wrapper after install.
- `frontend/src/app/layout.tsx` — already exports root metadata; PWA manifest reference goes here via the native `manifest.ts` route.
- `frontend/middleware.ts` — Clerk route matcher; **add `/workouts(.*)`** as a public route (workout library is browsable without login — onboarding incentive).
- `frontend/src/app/dashboard/page.tsx` — link to `/workouts` in main navigation.
- `frontend/src/components/avatar/` and `frontend/src/components/charts/` (Phase 5) — same component-co-location pattern for Phase 6's exercise components.
- `frontend/src/lib/api-server.ts` — BFF helper; not used by `/workouts` (static).

</code_context>

<specifics>
## Specific Ideas

- Card layout uses CSS grid with `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))` — responsive without media queries.
- Filter chips are sticky on scroll; clicking a chip OR'd with same-category, AND'd across categories (e.g., "dumbbells OR none" + "chest"). Matches the natural mental model.
- Exercise detail page is server-rendered (no client JS needed beyond image lazy-load) — keeps PWA cacheable.
- Service worker registration uses Next.js's built-in `next/serwist` integration; no manual `navigator.serviceWorker.register()` call needed.
- Offline indicator: a small persistent badge in the header when `!navigator.onLine`. Disappears on reconnect.

</specifics>

<deferred>
## Deferred Ideas

- **Curated YouTube embed (lite-youtube-embed pattern)** mentioned in ROADMAP SC-2: defer to v1.1. WebP detail image + instructions list cover the educational need.
- **WebM/GIF animations** mentioned in ROADMAP SC-2: defer to v1.1. Free Exercise DB primarily ships static images. Adding animated equivalents would require sourcing or generating them — over-scope for MVP.
- **wger source backstop:** dropped entirely (Free Exercise DB has enough breadth).
- **Workout-of-the-day / programming:** v2.
- **User-favorited exercises:** v2.
- **Form check video uploads:** v2+.

</deferred>

---

*Phase: 06-workout-library-pwa*
*Context auto-generated: 2026-05-13 (discuss skipped per user-driven autonomous mode)*
