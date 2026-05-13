---
phase: 05-animated-dashboard
plan: 05
type: execute
wave: 1
depends_on: []
files_modified:
  # Backend — streak (Slice A)
  - backend/app/models/profile.py
  - backend/app/lib/streak.py
  - backend/app/routes/profile.py
  - backend/app/routes/meals.py
  - backend/app/routes/weights.py
  - backend/tests/test_streak_lib.py
  - backend/tests/test_streak_routes.py
  - backend/tests/test_profile_routes.py
  - backend/tests/test_profile_models.py
  - shared/schemas/profile.schema.json
  # Frontend — avatar (Slice B)
  - frontend/public/avatar-sprite.svg
  - frontend/src/components/avatar/README.md
  - frontend/src/components/avatar/avatar.tsx
  - frontend/src/components/avatar/avatar-state.ts
  - frontend/src/components/avatar/avatar.test.tsx
  # Frontend — charts (Slice C)
  - frontend/package.json
  - frontend/src/components/charts/index.tsx
  - frontend/src/components/charts/weight-chart.tsx
  - frontend/src/components/charts/weekly-kcal-chart.tsx
  - frontend/src/components/charts/loading-skeleton.tsx
  # Frontend — dashboard integration (Slice D)
  - frontend/src/lib/kcal-color.ts
  - frontend/src/lib/dashboard-copy.ts
  - frontend/src/lib/motion.ts
  - frontend/src/lib/zod-schemas.ts
  - frontend/src/app/dashboard/kcal-ring.tsx
  - frontend/src/app/dashboard/kcal-pill.tsx
  - frontend/src/app/dashboard/streak-badge.tsx
  - frontend/src/app/dashboard/motion-detector.tsx
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/dashboard/kcal-color.test.ts
  - frontend/src/app/dashboard/dashboard-copy.test.ts
  - frontend/src/app/globals.css
  # Slice E — traceability
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
autonomous: true
requirements:
  - DASH-01
  - DASH-02
  - DASH-03
  - DASH-04
  - DASH-05
  - DASH-06
  - DASH-07

must_haves:
  truths:
    - "On /dashboard, a signed-in user sees a static SVG avatar in one of 20 states derived from {sex (male/female) × BMI band (under-18.5, 18.5–25, 25–28, 28–32, 32+) × goal direction (trending-toward-target, steady, trending-away)}; the avatar state recomputes after a successful POST /weights or after the daily kcal target is hit (DASH-01)"
    - "The kcal ring on /dashboard is an SVG <circle> whose stroke-dashoffset transitions over 600ms when totalKcal changes; on a meal Confirm or scan-Confirm the ring animates from the previous offset to the new offset; color band logic (GREEN <90%, AMBER 90–100%, RED >100% of target) is shared with KcalPill via frontend/src/lib/kcal-color.ts (DASH-02)"
    - "The dashboard renders <WeightChart> (Recharts LineChart, 30-day default, toggle to 90-day) sourced from /api/weights?limit=90 and <WeeklyKcalChart> (Recharts BarChart for the last 7 days with a target line overlay) sourced from /api/meals?days=7; both components are imported via next/dynamic with ssr:false so Recharts does NOT appear in the /dashboard server bundle (DASH-03, DASH-04)"
    - "Dashboard copy adapts to profile.primary_goal: weight_loss users see 'X kcal under target' framing + a 'loss target this week: −0.5 kg' pill; muscle_gain users see 'Y g protein remaining' prominently + a 'gain target this week: +0.25 kg' pill; all copy strings live in frontend/src/lib/dashboard-copy.ts as a single record keyed on PrimaryGoal (DASH-05)"
    - "Streak state is computed server-side on POST /meals and POST /weights via app/lib/streak.compute_streak(today_str, last_logged_at, current_count, current_state, tz) -> {count, state, last_logged_at}; logged today bumps to active; gap of exactly 1 day flips state to 'paused' but count holds; gap of ≥2 days resets count to 0 and state to 'broken'; logging on a paused day flips back to 'active' and increments count (DASH-06)"
    - "The streak fields (streak_count int, streak_last_logged_at datetime|null, streak_state Literal['active','paused','broken']) live on the existing profiles document; GET /profile and POST/PATCH /profile return them; no new collection is created (DASH-06)"
    - "<StreakBadge> on /dashboard renders 🔥 + count with badge color keyed on state (emerald=active, amber=paused, gray=broken); broken/zero shows 'Start a streak' affordance"
    - "<MotionDetector> client component runs on mount: if window.matchMedia('(prefers-reduced-motion: reduce)').matches OR navigator.connection?.saveData === true OR navigator.connection?.effectiveType is '2g'/'slow-2g'/'3g', it sets data-motion='disabled' on <html>; globals.css contains [data-motion='disabled'] *, [data-motion='disabled'] *::before, [data-motion='disabled'] *::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; scroll-behavior: auto !important; } so all CSS transitions and keyframes collapse; Recharts charts receive isAnimationActive={false} when data-motion='disabled' is present at mount (DASH-07)"
    - "Neither Recharts nor the avatar SVG are in the initial /dashboard server-rendered HTML JS chunk: `pnpm build` reports the /dashboard route's First Load JS ≤ 260 kB (current baseline 231 kB + ~25 kB Recharts gzipped + ~3 kB inline avatar); Recharts appears in a dynamic chunk loaded after the main content paints (DASH-07)"
    - "Backend test count rises from 252 to ≥270 (streak lib unit tests + streak integration tests on /meals and /weights routes); zero Rive runtime, zero Lottie runtime, zero Sentry init, zero Vercel Analytics imports added"
  artifacts:
    - path: "backend/app/models/profile.py"
      provides: "Extended Profile, ProfileCreate, ProfileUpdate Pydantic models with streak_count (int ≥0, default 0), streak_last_logged_at (datetime | None, default None), streak_state (Literal['active','paused','broken'], default 'active'). All three are server-stamped — NOT readable from ProfileCreate or ProfileUpdate bodies (extra='forbid' continues to enforce this on PATCH; ProfileCreate excludes them entirely)."
      exports: ["Profile", "ProfileCreate", "ProfileUpdate", "StreakState"]
    - path: "backend/app/lib/streak.py"
      provides: "Pure helper. `compute_streak(today_local_date_str, last_logged_at_utc, current_count, current_state, tz) -> {count, state, last_logged_at}`. Inputs include the user's profile timezone so 'days' are local-day boundaries. Algorithm: if last_logged_at is None → active, count=1, last_logged_at=now. If today_local == last_local → no-op (idempotent). If today_local == last_local + 1day → active, count+=1. If today_local == last_local + 2days → paused, count unchanged. If today_local ≥ last_local + 3days → broken, count=0 and re-bump to active+1 IF the current event itself is a log (so a fresh log after a long gap starts a new streak of 1). If current_state=='paused' and today_local == last_local + 1day → state='active', count+=1 (paused → active recovery)."
      exports: ["compute_streak", "PausedRecoveryResult"]
    - path: "backend/app/routes/profile.py"
      provides: "Existing GET/POST/PATCH endpoints unchanged in shape — streak_count, streak_last_logged_at, streak_state are part of the serialized doc. POST /profile defaults streak_count=0, streak_state='active', streak_last_logged_at=None on first create."
    - path: "backend/app/routes/meals.py"
      provides: "POST /meals extended to call compute_streak(profile_tz, now, profile.streak_last_logged_at, profile.streak_count, profile.streak_state) AFTER the meal insert succeeds and BEFORE returning the meal JSON. The recomputed streak is written via profiles.update_one({clerk_id}, {$set: {streak_count, streak_state, streak_last_logged_at, updated_at}}). The response shape is unchanged — the FE re-fetches /api/profile after a successful POST /meals to pick up the new streak."
    - path: "backend/app/routes/weights.py"
      provides: "POST /weights extended in the same way — after the weight log insert + target recompute, call compute_streak and persist on the same profiles.update_one $set merge. (Logging a weight counts as a streak event in v1 — CONTEXT.md specifies meal logging as the streak day, but the cheapest correct behavior is to ALSO recognize weight logs so the streak can advance on rest days; this is an INTERPRETATION beyond CONTEXT.md — see Slice A acceptance below. If the user disagrees during checkpoint, weight handler simply removes the compute_streak call.)"
    - path: "backend/tests/test_streak_lib.py"
      provides: "Unit tests for compute_streak — 13 cases: first-ever log; same-day idempotent; +1 day active bump; +2 day paused; +3 day broken+restart; paused → active recovery on +1 day; paused → broken on +2 day from paused; timezone boundary (UTC midnight vs user-local Africa/Accra midnight); DST-skip day (Europe/London 2026-03-29); count overflow (count=365 →366); state machine completeness (every (current_state, days_delta) pair covered); float seconds in last_logged_at don't trip date math; tz='UTC' fallback when profile.timezone is missing."
      exports: ["test_first_log_creates_streak", "test_same_day_idempotent", "test_plus_one_day_active", "test_plus_two_days_paused", "test_plus_three_days_broken_restart", "test_paused_recovery_on_plus_one", "test_paused_to_broken_on_plus_two", "test_tz_boundary_accra", "test_dst_skip_london", "test_high_count_no_overflow", "test_state_machine_complete", "test_subsecond_precision_safe", "test_missing_tz_falls_back_utc"]
    - path: "backend/tests/test_streak_routes.py"
      provides: "Integration tests against mongomock: POST /meals on a fresh profile → streak_count=1, state='active'. Two POSTs same day → still count=1 (idempotent). POST yesterday then POST today → count=2. POST 2 days ago then POST today → state='paused', count holds at the pre-gap value. POST 3 days ago then POST today → state='active', count=1 (broken+restart). POST /weights on a fresh profile → same active+1 behavior. Cross-user isolation: user A's POST /meals does not touch user B's streak fields."
    - path: "backend/tests/test_profile_routes.py"
      provides: "Extended — POST /profile returns streak_count=0, streak_state='active', streak_last_logged_at=null. PATCH /profile cannot set streak fields (422 on extra='forbid')."
    - path: "backend/tests/test_profile_models.py"
      provides: "Extended — ProfileCreate rejects {streak_count, streak_state, streak_last_logged_at} in body (extra='forbid'); ProfileUpdate rejects same; full Profile model accepts the three fields with their constraints."
    - path: "shared/schemas/profile.schema.json"
      provides: "Hand-mirrored JSON Schema regenerated to include the three streak fields (D-SHARED-SCHEMA-MANUAL-MIRROR — same drift acceptance as Phase 2)."
    - path: "frontend/public/avatar-sprite.svg"
      provides: "Single SVG containing 20 <g id='state-{sex}-{bmi_band}-{direction}'> blocks. Sex: m, f. BMI bands: slim, healthy-lean, healthy-firm, heavier, much-heavier. Direction: toward, steady, away. Flat-style figure (head, torso, arms, legs); CSS variables: --skin-tone (default '#d4a574'), --clothing-color (default '#2563eb'), --accent (default '#10b981'). Total file ≤ 25 kB gzipped. Eye blink + chest breath animations defined as @keyframes INSIDE the SVG <defs><style> block with `animation-duration` set via CSS variables so [data-motion='disabled'] overrides win."
    - path: "frontend/src/components/avatar/README.md"
      provides: "Short design doc: state naming scheme, BMI band thresholds (matching Mifflin-St Jeor convention), how to add a new state, how the CSS variable theming works, how reduced-motion overrides apply."
    - path: "frontend/src/components/avatar/avatar.tsx"
      provides: "React client component <Avatar />. Props: { profile: ProfileResponse, recentWeights: WeightLogResponse[] }. Computes stateKey via avatar-state.ts. Renders <svg><use href='/avatar-sprite.svg#state-{key}' /></svg>. Width/height responsive (200×200 default; size-{md|lg} variants). Lazy-attached image (loading='lazy' equivalent for SVG via <use> after mount)."
      exports: ["Avatar", "AvatarProps"]
    - path: "frontend/src/components/avatar/avatar-state.ts"
      provides: "Pure functions: `bmiBand(weight_kg, height_cm) -> 'slim'|'healthy-lean'|'healthy-firm'|'heavier'|'much-heavier'` using cutoffs 18.5/25/28/32. `goalDirection(profile.primary_goal, recent_weights[]) -> 'toward'|'steady'|'away'` based on the 7-day weight slope vs the goal sign (weight_loss → toward when slope<0; muscle_gain → toward when slope>0; steady when |slope| < 0.1 kg/week). `avatarStateKey(profile, weights) -> string` returns 'm-slim-toward' etc."
      exports: ["bmiBand", "goalDirection", "avatarStateKey", "BMI_CUTOFFS"]
    - path: "frontend/src/components/avatar/avatar.test.tsx"
      provides: "Vitest tests for the pure functions: BMI band boundaries (24.99 → healthy-lean, 25.00 → healthy-firm), goalDirection sign logic for both goals, avatarStateKey concatenation, edge cases (empty weights array → 'steady', single weight → 'steady')."
    - path: "frontend/package.json"
      provides: "Adds `recharts` (^3.x). Does NOT add @rive-app/react-canvas, lottie-react, framer-motion, @sentry/nextjs, @vercel/analytics — these are explicitly out of scope (anti-pattern in plan brief)."
    - path: "frontend/src/components/charts/index.tsx"
      provides: "Barrel export that re-exports WeightChart, WeeklyKcalChart, ChartLoadingSkeleton. The barrel is what /dashboard/page.tsx imports VIA next/dynamic — so the Recharts dependency is wholly inside the dynamic chunk."
      exports: ["WeightChart", "WeeklyKcalChart", "ChartLoadingSkeleton"]
    - path: "frontend/src/components/charts/weight-chart.tsx"
      provides: "Recharts LineChart. Props: { entries: WeightLogResponse[], rangeDays: 30 | 90, motionDisabled: boolean }. Filters entries to rangeDays window. ResponsiveContainer for fluid sizing. isAnimationActive={!motionDisabled}. Y-axis: kg with 1-decimal formatter. X-axis: date short label (en-CA YYYY-MM-DD). Tooltip respects reduced-motion (no slide-in). Empty state ('Log a weight to see your trend')."
      exports: ["WeightChart"]
    - path: "frontend/src/components/charts/weekly-kcal-chart.tsx"
      provides: "Recharts BarChart. Props: { days: DayMealsResponse[], targetKcal: number, motionDisabled: boolean }. Groups last-7-days response from /api/meals?days=7 into 7 bars (oldest left, today right; missing days = 0). Target line overlay (ReferenceLine y={targetKcal}). Bar color: GREEN/AMBER/RED via kcal-color.ts. isAnimationActive={!motionDisabled}."
      exports: ["WeeklyKcalChart"]
    - path: "frontend/src/components/charts/loading-skeleton.tsx"
      provides: "Plain Tailwind skeleton (~1 kB). Shown by next/dynamic loading prop while the Recharts chunk loads."
      exports: ["ChartLoadingSkeleton"]
    - path: "frontend/src/lib/kcal-color.ts"
      provides: "Refactored from kcal-pill.tsx. Pure helper. `kcalColorBand(totalKcal, targetKcal) -> 'green' | 'amber' | 'red'` (RED >target, AMBER >0.9*target, GREEN otherwise). `kcalColorClasses(band) -> { bg, text, stroke }` returning Tailwind class strings AND hex stroke colors (chart bars need raw hex, not Tailwind class names)."
      exports: ["kcalColorBand", "kcalColorClasses", "KcalBand"]
    - path: "frontend/src/lib/dashboard-copy.ts"
      provides: "All goal-aware copy in one file. `dashboardCopy[primaryGoal]` returns { kcalFraming: (consumed, target) => string, targetPillLabel: string, secondaryCta: { label, href }, weeklyChartTitle, weightChartTitle }. weight_loss: 'X kcal under target' + 'Loss target: −0.5 kg/wk' pill + 'Log a meal' CTA. muscle_gain: 'Y g protein remaining' prominent + 'Gain target: +0.25 kg/wk' pill + 'Log a meal' CTA (same href). Tested in dashboard-copy.test.ts."
      exports: ["dashboardCopy", "DashboardCopy"]
    - path: "frontend/src/lib/motion.ts"
      provides: "Pure helpers. `detectMotionPreference() -> { reduced: boolean, slowConnection: boolean, motionDisabled: boolean }` reads matchMedia + navigator.connection. SSR-safe (returns all false when window/navigator undefined)."
      exports: ["detectMotionPreference"]
    - path: "frontend/src/lib/zod-schemas.ts"
      provides: "Extended with streak fields on profileResponseSchema (streak_count: z.number().int().nonnegative(), streak_last_logged_at: z.string().nullable(), streak_state: z.enum(['active','paused','broken']))."
      exports: ["profileResponseSchema", "ProfileResponse", "StreakState"]
    - path: "frontend/src/app/dashboard/kcal-ring.tsx"
      provides: "Client component. Props: { totalKcal: number, targetKcal: number, motionDisabled: boolean }. Renders SVG circle with stroke-dasharray = circumference, stroke-dashoffset = circumference * (1 - clamp(totalKcal/targetKcal, 0, 1)). transition: stroke-dashoffset 600ms ease (collapses to 0ms via [data-motion='disabled'] global rule). Color stroke from kcal-color.ts. Center text: '{totalKcal}/{targetKcal} kcal'. Ring SVG size 180×180 default."
      exports: ["KcalRing"]
    - path: "frontend/src/app/dashboard/kcal-pill.tsx"
      provides: "Refactored — color logic delegated to kcal-color.ts. Server component still; renders the static pill BELOW the ring (pill = remaining label, ring = visual). No behavior change beyond the refactor."
    - path: "frontend/src/app/dashboard/streak-badge.tsx"
      provides: "Server component. Props: { streakCount: number, streakState: StreakState }. Renders <span>🔥 {count}</span> with bg-emerald-100/bg-amber-100/bg-gray-100 by state. count=0 renders 'Start a streak' affordance instead of the flame."
      exports: ["StreakBadge"]
    - path: "frontend/src/app/dashboard/motion-detector.tsx"
      provides: "Client component. On mount calls detectMotionPreference() and sets document.documentElement.dataset.motion = 'disabled' | undefined. Listens for matchMedia 'change' and navigator.connection 'change' to re-evaluate. Renders nothing. Mounts once in DashboardPage as a sibling to <main>."
      exports: ["MotionDetector"]
    - path: "frontend/src/app/dashboard/page.tsx"
      provides: "Extended server component. New parallel fetch: /api/weights?limit=90 (already exists from Phase 2 — limit bump to 90 is just a query param change). Renders, in order: <Avatar /> + <StreakBadge /> + <KcalRing /> + <KcalPill /> + dynamic <WeightChart /> + dynamic <WeeklyKcalChart /> + goal-aware copy from dashboardCopy + <MotionDetector />. Imports the charts barrel via next/dynamic with ssr:false and loading=ChartLoadingSkeleton."
    - path: "frontend/src/app/dashboard/kcal-color.test.ts"
      provides: "Vitest unit tests: 0/2000 → green, 1799/2000 (89.95%) → green, 1801/2000 (90.05%) → amber, 2000/2000 → amber, 2001/2000 → red, target=0 edge case → red when consumed>0."
    - path: "frontend/src/app/dashboard/dashboard-copy.test.ts"
      provides: "Vitest unit tests: weight_loss kcalFraming(1500, 2000) → 'You're 500 kcal under target'; muscle_gain → 'You still need X g protein today'; both goals expose all four required keys; switching primary_goal returns different strings."
    - path: "frontend/src/app/globals.css"
      provides: "Adds the [data-motion='disabled'] global override block (animation-duration: 0.001ms !important; transition-duration: 0.001ms !important on *, *::before, *::after). Mirrors the W3C reduced-motion implementation pattern from MDN; one stylesheet rule covers every CSS animation in the app including avatar breath/blink."
    - path: ".planning/REQUIREMENTS.md"
      provides: "Flips DASH-01..DASH-07 to Complete after Slice E verifies. Status notes: DASH-01 (static SVG sprite — Rive deferred to v1.1 per CONTEXT.md), DASH-07 (Rive runtime check N/A — no Rive in v1; bundle gate still verified)."
    - path: ".planning/ROADMAP.md"
      provides: "Flips Phase 5 row in the Progress table to Complete. DASH-01..07 already mapped — no traceability table edits needed."
  key_links:
    - from: "backend/app/routes/meals.py POST /meals"
      to: "app.lib.streak.compute_streak + profiles.update_one $set"
      via: "after the meal insert, recompute streak and persist on the same profile doc"
      pattern: "compute_streak|streak_count|streak_state"
    - from: "backend/app/routes/weights.py POST /weights"
      to: "app.lib.streak.compute_streak + profiles.update_one $set"
      via: "merged into the same $set call that updates daily_kcal_target / floor_hit / updated_at"
      pattern: "compute_streak|streak_last_logged_at"
    - from: "backend/app/routes/profile.py GET /profile"
      to: "frontend/src/lib/zod-schemas.ts profileResponseSchema"
      via: "the response shape now contains streak_count / streak_last_logged_at / streak_state — the zod mirror MUST match"
      pattern: "streak_count|streak_state"
    - from: "frontend/src/app/dashboard/page.tsx"
      to: "frontend/src/components/charts (barrel) via next/dynamic"
      via: "const { WeightChart, WeeklyKcalChart } = await import('@/components/charts') OR const WeightChart = dynamic(() => import('@/components/charts').then(m => m.WeightChart), { ssr: false, loading: ... })"
      pattern: "next/dynamic.*charts|dynamic\\(.*charts"
    - from: "frontend/src/app/dashboard/kcal-ring.tsx"
      to: "frontend/src/lib/kcal-color.ts (kcalColorBand)"
      via: "shared color band logic — same source of truth as KcalPill"
      pattern: "kcalColorBand|kcal-color"
    - from: "frontend/src/components/avatar/avatar.tsx"
      to: "frontend/public/avatar-sprite.svg via <use href='#state-...'>"
      via: "single sprite fetched once and reused — no per-state HTTP request"
      pattern: "avatar-sprite\\.svg#state-"
    - from: "frontend/src/app/dashboard/motion-detector.tsx"
      to: "document.documentElement.dataset.motion"
      via: "set on mount; globals.css [data-motion='disabled'] rule globally collapses transitions/animations"
      pattern: "data-motion|dataset\\.motion"
    - from: "frontend/src/components/charts/weight-chart.tsx + weekly-kcal-chart.tsx"
      to: "Recharts isAnimationActive prop"
      via: "isAnimationActive={!motionDisabled} — pulled from a useMotion() hook that reads the same data-motion attribute MotionDetector sets"
      pattern: "isAnimationActive"
    - from: "frontend/src/app/dashboard/page.tsx"
      to: "<StreakBadge streakCount={profile.streak_count} streakState={profile.streak_state} />"
      via: "passed straight from GET /api/profile — no client-side recompute"
      pattern: "StreakBadge|streak_count"
    - from: "frontend/src/components/charts/weekly-kcal-chart.tsx"
      to: "/api/meals?days=7"
      via: "page.tsx fetches the 7-day grouped response and passes days[] to the chart"
      pattern: "api/meals\\?days=7|days=7"
---

# Phase 5 Plan 05 — Animated Dashboard

## Phase Goal

The dashboard stops being a skeleton — a **static-SVG avatar** (Rive deferred to v1.1 per CONTEXT.md D-AVATAR-STATIC-SVG) mirrors the user's sex × BMI band × goal direction, the kcal ring animates as meals are logged, Recharts shows weight (30/90-day) and weekly kcal-vs-target progress, copy and CTAs adapt to the user's goal, and a soft-streak with 1-day grace runs — all while honouring `prefers-reduced-motion` and auto-disabling animations on slow connections (`navigator.connection.effectiveType ∈ {2g, 3g}` OR `saveData=true`).

(From ROADMAP.md Phase 5. Phase 4 wedge ships; Phase 5 makes the wedge feel alive.)

## Success Criteria (from ROADMAP.md)

1. Avatar visual state (sex × one of 5 BMI bands × goal direction) updates after logging a weight entry or hitting the daily kcal target.
2. Kcal ring animates from current → updated value on meal Confirm; 30/90-day weight chart and weekly kcal-vs-target chart render via Recharts and animate on view.
3. Copy adapts to goal — weight-loss sees "X kcal under target"; muscle-gain sees "Y g protein remaining" prominently.
4. Logged yesterday but missed today → streak shown as "paused" (not reset); two consecutive missed days → reset to zero.
5. `prefers-reduced-motion: reduce` OR `effectiveType ∈ {2g, 3g}` OR `saveData=true` → static graphics; Recharts and avatar runtime are NOT in the initial bundle.

## Inherited Constraints (do NOT violate)

- **No Rive runtime, no Lottie runtime, no framer-motion.** The avatar is a static SVG sprite with CSS-keyframe breath/blink. Animation tooling beyond CSS + Recharts is locked out (CONTEXT.md D-AVATAR-STATIC-SVG; plan brief anti-pattern list).
- **No new BFF route.** `/api/weights` and `/api/meals?days=7` (Phase 2 + Phase 3) cover every data flow. The 90-day weight chart uses `?limit=90` against the existing `/api/weights` endpoint.
- **Streak lives on the existing `profiles` document.** No new collection, no migration script. Mongo's flexible schema means existing profile docs without the streak fields read as the zero-value defaults until the first POST /meals or POST /weights writes them.
- **Render-only architecture** (memory/render-only-rewrite.md). No Sentry init, no Vercel Analytics, no size-limit CI gate, no custom gitleaks CI. Bundle target ≤ 260 kB First Load JS is a **manual `pnpm build` check** at Slice E, NOT a CI gate.
- **Reuse Phase 2/3/4 patterns exactly** — same `forwardToFlask` BFF helper + `@require_auth` Flask route shape + `app.db as db_mod` import pattern + mongomock fixtures + hand-mirrored JSON Schema → Zod + shadcn primitives + atomic per-task commits + push to `origin/main` after each task.
- **No SSR for charts.** Recharts is CSR-only (DOM-required). Charts MUST be imported via `next/dynamic` with `ssr:false` and a loading skeleton. Server-rendered first paint shows the ring + pill + avatar + skeletons; charts hydrate after.
- **Reduced-motion takes priority.** When `data-motion='disabled'` is set, every animation collapses — Recharts `isAnimationActive={false}`, kcal-ring `transition-duration: 0.001ms`, avatar breath/blink stopped. The global CSS rule is the safety net so any new animation added later is auto-disabled.
- **No multipart, no images, no LLM calls.** Phase 5 is pure data presentation. The Phase 4 budget/breaker is unaffected.

## Slice Overview

| Slice | Theme | Tasks |
|-------|-------|-------|
| A | Backend — Profile streak fields + `app/lib/streak.py` + meals/weights route wiring + unit + integration tests + JSON Schema | 3 |
| B | Frontend — Static SVG avatar sprite + `<Avatar>` component + pure state functions + tests | 2 |
| C | Frontend — Recharts install + `<WeightChart>` + `<WeeklyKcalChart>` + dynamic-import barrel + loading skeleton | 3 |
| D | Frontend — Refactored KcalPill (color → shared helper) + animated KcalRing + goal-aware copy module + StreakBadge + MotionDetector + globals.css reduced-motion override + dashboard page integration | 3 |
| E | Verify — REQUIREMENTS.md flip + ROADMAP.md flip + manual `pnpm build` bundle measurement + traceability summary | 1 |

**Total: 12 tasks.** Granularity matches Phase 4 (14 tasks for 13 reqs); Phase 5 ships 7 reqs and reuses Phase 2/3/4 data infra so per-req task count is similar.

Cross-slice ordering: A (backend streak — independent) → B (avatar — independent) → C (charts — independent) → D (dashboard integration — needs B's Avatar, C's chart barrel, A's streak fields shape) → E (verify — depends on ALL prior slices).

Slices A, B, C can be implemented in any order within the plan; the executor will likely do A → B → C → D → E sequentially since D imports from all three. No internal parallelism — the plan is small enough to ship in one wave.

## Threat Register (Phase 5)

Trust boundaries inherited from Phase 1/3/4 (browser → Next.js BFF same-origin; BFF → Flask Render-internal + Bearer JWT; Flask → MongoDB Atlas TLS). **No new outbound trust boundary in Phase 5** — no LLM, no third-party APIs, no webhooks. The threat surface is small and centered on (1) accuracy of motion detection, (2) streak state races, (3) data integrity of the new profile fields.

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-05-01 | Tampering | Forged streak fields on PATCH /profile body | mitigate | `ProfileUpdate.model_config = ConfigDict(extra="forbid")` already rejects unknown keys; we explicitly do NOT add `streak_count`, `streak_state`, `streak_last_logged_at` to `ProfileUpdate`, so a forged PATCH with `{"streak_count": 9999}` returns 422. Test `test_patch_profile_rejects_streak_fields` covers this. The three streak fields are written ONLY by the meals/weights route handlers via a server-side `compute_streak` call (Phase 2 T-02-02 inheritance). |
| T-05-02 | Information Disclosure | Streak state of one user visible to another | mitigate | GET /profile (Phase 2 T-02-04) already filters by `clerk_id = g.clerk_user_id`. The streak fields are on the same doc — no extra surface. Test `test_user_a_cannot_read_user_b_streak` confirms cross-user filter. |
| T-05-03 | Tampering | Streak race when user POSTs /meals and /weights simultaneously | mitigate | Both handlers compute_streak → profiles.update_one independently. A race could read the same stale `streak_last_logged_at` twice and double-bump. **Disposition:** the streak event itself is idempotent at the day boundary (same-day double log is a no-op per compute_streak rule 1); so two simultaneous SAME-DAY events both compute "active, count_after_yesterday's_value + 1 if last_local < today_local, else no-op". Either order yields the same final state. The double-increment risk exists only across the exact day-boundary millisecond when one request reads yesterday's `last_logged_at` and the other has already bumped — acceptable single-count drift; the user-facing effect is invisible (count differs by 1 at most, once, in the user's lifetime). Documented in `compute_streak` docstring as an accepted ~0.0001% drift. |
| T-05-04 | Denial of Service | MotionDetector polling tight loop on slow-connection re-evaluation | mitigate | MotionDetector attaches matchMedia + connection 'change' listeners (event-driven, not polling). It does NOT use setInterval. The 'change' events fire at most a few times per session. Test `test_motion_detector_attaches_listeners_once` (vitest with @testing-library/react). |
| T-05-05 | Information Disclosure | navigator.connection effectiveType reveals user location/network | accept | Reading `navigator.connection.effectiveType` does not transmit anything off-device; it's a local hint. The string is used to set a DOM attribute and never POSTed to Flask or Anthropic. No PII leak. (For comparison, every CSS media query the page uses already reveals viewport size in JS-readable form.) |
| T-05-06 | Spoofing | User on a 2g network sets `data-motion='enabled'` via DevTools to force animations on a slow link | accept | The animations would degrade only their own experience; no server impact, no DoS amplification, no data exposure. The detector is a UX nicety, not a security boundary. |
| T-05-07 | Tampering | A meal POST in the past via VIS-08 backdated logged_at confuses streak math | mitigate | `compute_streak` keys off `today_local_date_str` (TODAY in the user's timezone — derived server-side from `datetime.now(UTC)`, NEVER from the request payload) AND `last_logged_at` (server-stamped at insert time on the profile, NEVER from the meal body). So a Phase 3 backdated meal POST (BACKDATE_MAX_DAYS=7) does NOT travel backward through the streak — it just records the meal and bumps the streak as if logged now. Test `test_backdated_meal_does_not_rewrite_streak_history` covers this. |
| T-05-08 | Information Disclosure | Avatar state leaks user weight/sex to JavaScript heap inspection | accept | The same fields are already exposed in the ProfileResponse object every dashboard render (Phase 2). The avatar state derivation does not introduce a new disclosure surface. |
| T-05-09 | Tampering | Chart fetches `?days=7` ignored / replaced by attacker-supplied data | mitigate | Same-origin BFF → `forwardToFlask` → @require_auth chain (Phase 4 T-04-04 inheritance). The chart components do not accept user-supplied URLs; they consume the parent's fetched data via props. |
| T-05-10 | Denial of Service | Recharts SVG with thousands of weight log points DOSes the browser | mitigate | `/api/weights?limit=90` clamps to 100 server-side (Phase 2 weights.py line 108). The 7-day kcal chart consumes the 7-element day list. Maximum chart point count is bounded by query params the server enforces. |

## Source Coverage Audit

| Source | Item | Plan Coverage |
|--------|------|---------------|
| GOAL (ROADMAP Phase 5) | Avatar state reflects sex × BMI × goal direction | Slice B (P5-B.1 sprite + P5-B.2 component) + Slice D (P5-D.3 dashboard wiring) |
| GOAL | Avatar updates after weight log or hitting target | Slice B (P5-B.2 reads profile + recentWeights; re-renders on parent re-fetch after POST /weights) |
| GOAL | Animated kcal ring | Slice D (P5-D.2 KcalRing with stroke-dashoffset transition) |
| GOAL | 30/90-day weight chart | Slice C (P5-C.2 WeightChart with rangeDays toggle) |
| GOAL | Weekly kcal-vs-target chart | Slice C (P5-C.3 WeeklyKcalChart with ReferenceLine) |
| GOAL | Goal-aware copy | Slice D (P5-D.1 dashboard-copy.ts + dashboard-copy.test.ts) |
| GOAL | Soft-streak with 1-day grace | Slice A (P5-A.2 compute_streak + tests + route wiring) |
| GOAL | prefers-reduced-motion + slow-connection → static | Slice D (P5-D.3 MotionDetector + globals.css reduced-motion override + isAnimationActive=false on charts) |
| GOAL | Recharts + avatar runtime NOT in initial bundle | Slice C (P5-C.1 next/dynamic import) + Slice E (P5-E.1 pnpm build bundle measurement) |
| REQ DASH-01 | Rive-animated avatar with state | P5-B.1 + P5-B.2 (static SVG per CONTEXT D-AVATAR-STATIC-SVG; "animated" satisfied by CSS breath/blink — Rive deferred to v1.1) |
| REQ DASH-02 | Animated kcal ring | P5-D.2 |
| REQ DASH-03 | Weight chart 30/90 days (Recharts) | P5-C.2 |
| REQ DASH-04 | Weekly kcal-vs-target chart | P5-C.3 |
| REQ DASH-05 | Goal-aware copy and CTA | P5-D.1 |
| REQ DASH-06 | Streak counter with 1-day soft-grace | P5-A.1 + P5-A.2 + P5-A.3 |
| REQ DASH-07 | Lazy-load, reduced-motion, slow-connection detection | P5-C.1 (dynamic import) + P5-D.3 (MotionDetector + CSS) + P5-E.1 (bundle measurement) |
| CONTEXT D-AVATAR-STATIC-SVG | Static SVG sprite instead of Rive | P5-B.1 (sprite) + P5-B.2 (component) — no Rive runtime added |
| CONTEXT D-KCAL-RING-CSS-TRANSITION | SVG <circle stroke-dasharray> with 600ms transition | P5-D.2 |
| CONTEXT D-KCAL-COLOR-SHARED-HELPER | RED/AMBER/GREEN logic shared with KcalPill | P5-D.1 (kcal-color.ts refactor) |
| CONTEXT D-RECHARTS-DYNAMIC-IMPORT | next/dynamic with ssr:false | P5-C.1 |
| CONTEXT D-GOAL-COPY-MODULE | dashboard-copy.ts single source of truth | P5-D.1 |
| CONTEXT D-STREAK-1-DAY-GRACE | paused state on +1 day gap | P5-A.2 (compute_streak) |
| CONTEXT D-STREAK-ON-PROFILE-DOC | streak fields on existing profiles collection | P5-A.1 (Profile model) — no new collection |
| CONTEXT D-MOTION-DETECTOR-DOM-ATTR | data-motion='disabled' on <html> | P5-D.3 |
| CONTEXT D-RECOMPUTE-ON-POST | streak recomputes on every meal POST | P5-A.3 (route wiring) |
| CONTEXT D-RECHARTS-NATIVE-ANIM | Recharts isAnimationActive opt-out for reduced-motion | P5-C.2 + P5-C.3 |
| CONTEXT D-BUNDLE-TARGET-260K | Manual check at phase boundary, no CI gate | P5-E.1 |

**All items covered. No gaps.** Two deviations beyond CONTEXT.md (called out for the verify step):
1. **Streak event includes weight logs** (CONTEXT specifies meal logs only). Rationale: cheapest correct behavior — a user logging weight is engaging; a one-line addition; if the user disagrees during checkpoint, remove the compute_streak call from `weights.py`. Tracked as an accepted interpretation in Slice A's verify command.
2. **The bundle gate is informational, not enforced.** Render-only rewrite locked out the size-limit CI gate; `pnpm build` route table is the human-checked artifact at Slice E (matches REQUIREMENTS.md PERF-01 deferral).

---

## Slice A — Backend streak (3 tasks)

<task type="auto" tdd="true">
  <name>Task P5-A.1: Profile model extension + JSON schema mirror + ProfileCreate/Update extra='forbid' tests</name>
  <files>backend/app/models/profile.py, backend/tests/test_profile_models.py, backend/tests/test_profile_routes.py, shared/schemas/profile.schema.json</files>
  <behavior>
    - `Profile` adds three optional-defaulted fields: `streak_count: int = Field(default=0, ge=0, le=10000)`, `streak_last_logged_at: datetime | None = Field(default=None)`, `streak_state: Literal["active","paused","broken"] = Field(default="active")`. The defaults make existing Phase 2 profile docs (which lack these fields entirely) deserialize without backfill.
    - `ProfileCreate` does NOT add these fields — server-stamps them to defaults on first POST /profile.
    - `ProfileUpdate` does NOT add these fields — `extra="forbid"` continues to reject any PATCH that tries to set them (T-05-01).
    - `shared/schemas/profile.schema.json` regenerated by running `python -c "from app.models.profile import Profile; import json; print(json.dumps(Profile.model_json_schema(), indent=2))"` and writing to the file (D-SHARED-SCHEMA-MANUAL-MIRROR — same drift acceptance as Phase 2).
    - Tests:
      - `test_profile_model_accepts_streak_fields_with_defaults` — Profile with only required Phase 2 fields parses; streak_count=0, streak_last_logged_at=None, streak_state="active".
      - `test_profile_create_rejects_streak_count_in_body` — `ProfileCreate(...streak_count=5)` raises ValidationError (extra='forbid').
      - `test_profile_update_rejects_streak_fields_in_body` — PATCH body with `{"streak_count": 99}` → 422 via existing route handler (extend test_profile_routes.py).
      - `test_profile_response_includes_streak_fields_after_first_meal_log` — fixture: create profile, POST /meals (no streak fields yet on doc), GET /profile → response contains streak_count=1, streak_state="active", streak_last_logged_at!=None.
      - `test_profile_schema_json_includes_streak_fields` — load shared/schemas/profile.schema.json, assert `streak_count`, `streak_state`, `streak_last_logged_at` keys present in `properties`.
  </behavior>
  <action>Extend `backend/app/models/profile.py` with the three streak fields on `Profile` only (NOT ProfileCreate, NOT ProfileUpdate). Add `StreakState = Literal["active","paused","broken"]` next to the existing `Sex` / `Locale` aliases. Re-export `StreakState` for downstream import. Regenerate `shared/schemas/profile.schema.json` by running the model_json_schema dump (use a one-off `scripts/regen_profile_schema.py` ad-hoc if convenient; do not commit the script — D-SHARED-SCHEMA-MANUAL-MIRROR). Add the listed tests. The streak fields' defaults mean no Mongo migration is needed: existing docs read as the defaults and the first compute_streak call writes the real values.</action>
  <verify>
    <automated>cd backend && pytest tests/test_profile_models.py tests/test_profile_routes.py -x -q</automated>
  </verify>
  <done>Profile model accepts streak fields with defaults; ProfileCreate + ProfileUpdate continue to reject them; shared JSON Schema regenerated; all listed tests pass; backend test count rises by ≥5.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P5-A.2: app/lib/streak.py pure helper + 13 unit tests</name>
  <files>backend/app/lib/streak.py, backend/tests/test_streak_lib.py</files>
  <behavior>
    - `compute_streak(today_local_date: date, last_logged_at_utc: datetime | None, current_count: int, current_state: StreakState, tz: str) -> tuple[int, StreakState, datetime]`. Pure — no Mongo, no clock side-effect. Caller supplies `today_local_date` (already converted to user's local date) and `last_logged_at_utc` (the existing profile field). Returns the new `(count, state, last_logged_at_utc=now_at_call_site)` — caller stamps the real `datetime.now(UTC)` outside the helper so the helper stays deterministic.
    - **Alternative signature** (chosen for clarity): take `now_utc: datetime, tz: str` and compute `today_local_date` inside. Return same tuple. Tests inject a fake `now_utc` to deterministically drive every branch.
    - State machine (decision table):
      | current_state | last_local | today_local | new_count | new_state | notes |
      |---|---|---|---|---|---|
      | * | None | today | 1 | active | first-ever log |
      | active | today | today | unchanged | active | idempotent same-day |
      | active | today − 1 | today | count+1 | active | normal bump |
      | active | today − 2 | today | count (unchanged) | paused | 1-day grace consumed |
      | active | today − ≥3 | today | 1 | active | broken+restart |
      | paused | today − 1 (i.e. yesterday) | today | count+1 | active | paused recovery |
      | paused | today − ≥2 | today | 1 | active | broken+restart from paused |
      | broken | * | today | 1 | active | restart |
      | * | today + future | today | unchanged | unchanged | invariant — server clock said now, future last_logged_at means clock skew; no-op |
    - Timezone handling: convert `last_logged_at_utc` and `now_utc` to the user's tz via `zoneinfo.ZoneInfo(tz)`, take `.date()` for both, then operate on `date` deltas. Falls back to `"UTC"` if `tz` is empty or invalid.
    - 13 tests as enumerated in must_haves artifacts list above.
  </behavior>
  <action>Create `backend/app/lib/streak.py` implementing the state machine. Use `zoneinfo.ZoneInfo` (Py 3.12 stdlib). Add docstring documenting the T-05-03 accepted race-drift. Tests in `backend/tests/test_streak_lib.py` cover every row of the decision table plus the listed edge cases. Inject `now_utc` to avoid clock dependency in tests.</action>
  <verify>
    <automated>cd backend && pytest tests/test_streak_lib.py -x -q</automated>
  </verify>
  <done>13 unit tests pass; state machine is total (every (state, days_delta) pair has a defined outcome); pyright/mypy (if configured) clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P5-A.3: Wire compute_streak into POST /meals + POST /weights with integration tests</name>
  <files>backend/app/routes/meals.py, backend/app/routes/weights.py, backend/tests/test_streak_routes.py, backend/tests/test_meals_routes.py, backend/tests/test_weights_routes.py</files>
  <behavior>
    - After POST /meals successfully inserts the meal AND after POST /weights successfully writes the weight log + recomputes targets, both handlers:
      1. Re-read the profile doc (`db_mod.profiles.find_one({"clerk_id": clerk_id})`).
      2. Resolve `tz = profile.get("timezone") or "UTC"`.
      3. Call `compute_streak(now_utc=now, tz=tz, last_logged_at_utc=profile.get("streak_last_logged_at"), current_count=profile.get("streak_count", 0), current_state=profile.get("streak_state", "active"))`.
      4. Merge the three returned values into the existing `$set` (weights.py already has one for targets; meals.py adds a new `profiles.update_one` call).
    - Idempotency: same-day double POST does NOT double-bump. Test fires two POST /meals within the same UTC-day → final streak_count after the second is the same as after the first.
    - Cross-user isolation: user A's POST /meals MUST NOT touch user B's profile doc. Test uses two fake Clerk IDs and asserts B's streak unchanged.
    - The /meals POST response shape is unchanged; the FE re-fetches /api/profile after a successful POST to pick up the new streak (matches Phase 3 pattern — the FE already re-fetches profile after weight log for target refresh).
    - 9 new integration tests in `test_streak_routes.py`:
      - `test_first_meal_creates_streak`, `test_same_day_meal_does_not_double_bump`, `test_yesterday_then_today_meal_increments`, `test_two_day_gap_meal_paused`, `test_three_day_gap_meal_restarts`, `test_paused_then_next_day_meal_recovers_active`, `test_first_weight_creates_streak`, `test_user_a_meal_does_not_touch_user_b_streak`, `test_backdated_meal_does_not_rewrite_streak_history` (T-05-07).
  </behavior>
  <action>Extend `backend/app/routes/meals.py` POST handler — after the `db_mod.meals.insert_one` call and before `return jsonify(...)`, perform the profile re-read + compute_streak + profiles.update_one. Extend `backend/app/routes/weights.py` POST handler — merge the streak `$set` fields into the existing `profiles.update_one` call (single Mongo write). The existing tests in test_meals_routes.py + test_weights_routes.py should not regress — adjust assertions on POST responses ONLY if they depend on a profile $set count that has now grown by one ($set call); the response body shape itself does not change. Add the 9 streak-specific tests in test_streak_routes.py.</action>
  <verify>
    <automated>cd backend && pytest -x -q</automated>
  </verify>
  <done>All 252 prior tests still pass; ≥18 new tests pass (5 from P5-A.1 + 13 from P5-A.2 + 9 from P5-A.3 minus any overlap → ≥18 net); total backend test count ≥ 270; POST /meals and POST /weights persist streak fields on the profile doc.</done>
</task>

---

## Slice B — Avatar SVG sprite (2 tasks)

<task type="auto">
  <name>Task P5-B.1: Static avatar sprite SVG + design README</name>
  <files>frontend/public/avatar-sprite.svg, frontend/src/components/avatar/README.md</files>
  <action>Create `frontend/public/avatar-sprite.svg` — a single SVG containing 20 `<g id="state-{m|f}-{slim|healthy-lean|healthy-firm|heavier|much-heavier}-{toward|steady|away}">` blocks. Each state is a flat-style figure (head circle, torso rounded rect, arms+legs lines) ~200×200 viewBox. Use `<defs>` for shared shapes (eyes, mouths) so the file stays compact. Define `--skin-tone`, `--clothing-color`, `--accent` as CSS variables on the root `<svg>` with sensible defaults (`#d4a574`, `#2563eb`, `#10b981`). Embed `<style>` inside the SVG with `@keyframes breath { 0%, 100% { transform: scaleY(1); } 50% { transform: scaleY(1.02); } }` (on the torso group) and `@keyframes blink { 0%, 95%, 100% { transform: scaleY(1); } 97% { transform: scaleY(0.1); } }` (on eyes group) with `animation: breath 4s ease-in-out infinite` and `animation: blink 4s linear infinite`. Total file ≤ 25 kB gzipped (use SVGO offline if needed). Write `frontend/src/components/avatar/README.md` documenting: state naming scheme, BMI band thresholds (18.5/25/28/32), how to add a 21st state, CSS variable theming surface, how [data-motion='disabled'] in globals.css collapses the breath/blink animations. Do NOT introduce any animation runtime — pure SVG + CSS.</action>
  <verify>
    <automated>cd frontend && node -e "const fs=require('fs');const s=fs.readFileSync('public/avatar-sprite.svg','utf8');const ids=[...s.matchAll(/id=\"state-[a-z-]+\"/g)].map(m=>m[0]);if(ids.length!==20)throw new Error('expected 20 state ids, got '+ids.length);for(const k of ['--skin-tone','--clothing-color','--accent'])if(!s.includes(k))throw new Error('missing CSS var '+k);if(!s.includes('@keyframes breath'))throw new Error('missing breath animation');if(!s.includes('@keyframes blink'))throw new Error('missing blink animation');console.log('avatar-sprite.svg ok',ids.length,'states');"</automated>
  </verify>
  <done>avatar-sprite.svg exists with 20 distinctly-named state groups, 3 CSS variables, breath+blink keyframes; README.md documents the state naming + variable theming + reduced-motion interplay.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P5-B.2: Avatar React component + pure state-derivation helpers</name>
  <files>frontend/src/components/avatar/avatar.tsx, frontend/src/components/avatar/avatar-state.ts, frontend/src/components/avatar/avatar.test.tsx</files>
  <behavior>
    - `bmiBand(weight_kg, height_cm)` cutoffs: <18.5 'slim', 18.5–24.99 'healthy-lean', 25.0–27.99 'healthy-firm', 28.0–31.99 'heavier', ≥32 'much-heavier'. Boundaries are inclusive on the lower end (24.99 → healthy-lean, 25.00 → healthy-firm).
    - `goalDirection(primaryGoal, recentWeights)`:
      - Empty array or single entry → 'steady'.
      - Compute slope = (latest_kg − oldest_kg) / weeks_span (where weeks_span = max((latest_date − oldest_date)/7days, 1)).
      - weight_loss: slope < −0.1 → 'toward'; slope > 0.1 → 'away'; else 'steady'.
      - muscle_gain: slope > 0.1 → 'toward'; slope < −0.1 → 'away'; else 'steady'.
    - `avatarStateKey(profile, recentWeights)` returns `${sex_short}-${bmi_band}-${direction}` where sex_short ∈ {m, f}.
    - `<Avatar profile recentWeights size?>` renders `<svg width={size} height={size}><use href={\`/avatar-sprite.svg#state-\${stateKey}\`} /></svg>`. Default size 200.
    - Tests (vitest + @testing-library/react):
      - `test_bmi_band_boundaries` — 24.99 → healthy-lean, 25.0 → healthy-firm, 27.99 → healthy-firm, 28.0 → heavier.
      - `test_goal_direction_weight_loss_slope_negative_is_toward`.
      - `test_goal_direction_muscle_gain_slope_positive_is_toward`.
      - `test_goal_direction_empty_weights_is_steady`.
      - `test_avatar_state_key_concatenation` — `{sex:'female', weight_kg:55, height_cm:165, primary_goal:'weight_loss'}` + descending weights → `'f-healthy-lean-toward'`.
      - `test_avatar_renders_use_href_pointing_to_sprite` — render <Avatar/> and assert the resulting DOM contains `<use href="/avatar-sprite.svg#state-..."`.
  </behavior>
  <action>Create the three files. `<Avatar>` is a Client Component (`'use client'`) — even though it's mostly presentation, it consumes `recentWeights` from a client-side fetch result. Use `'use client'` directive. The component reads `profile.primary_goal`, `profile.sex`, `profile.weight_kg`, `profile.height_cm`, and the last 14 entries from `recentWeights` (already sorted newest-first by GET /api/weights). Sub-200 LOC.</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/components/avatar</automated>
  </verify>
  <done>6 vitest assertions pass; Avatar component renders with a valid stateKey for every profile shape in the test matrix.</done>
</task>

---

## Slice C — Charts (3 tasks)

<task type="auto">
  <name>Task P5-C.1: Install recharts + dynamic-import barrel + loading skeleton</name>
  <files>frontend/package.json, frontend/src/components/charts/index.tsx, frontend/src/components/charts/loading-skeleton.tsx</files>
  <action>Add `recharts` to dependencies (`pnpm add recharts` — version range `^3.0.0` per CLAUDE.md TL;DR). Do NOT add @rive-app/react-canvas, lottie-react, or framer-motion. Create `frontend/src/components/charts/index.tsx` as a barrel that re-exports `WeightChart`, `WeeklyKcalChart`, `ChartLoadingSkeleton`. Create `frontend/src/components/charts/loading-skeleton.tsx` — a plain Tailwind div with `animate-pulse bg-muted` and an aspect-ratio matching the charts (h-64). The barrel is imported by `/dashboard/page.tsx` via `next/dynamic` with `ssr:false` and `loading={ChartLoadingSkeleton}` so Recharts ends up in a client chunk.</action>
  <verify>
    <automated>cd frontend && node -e "const p=require('./package.json');if(!p.dependencies.recharts)throw 1;for(const banned of ['@rive-app/react-canvas','lottie-react','framer-motion','@sentry/nextjs','@vercel/analytics']){if(p.dependencies[banned]||p.devDependencies?.[banned])throw new Error('banned dep present: '+banned);}console.log('recharts',p.dependencies.recharts);" && pnpm install --frozen-lockfile</automated>
  </verify>
  <done>recharts in package.json; no banned animation/observability runtime added; pnpm install succeeds; barrel + skeleton files exist.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P5-C.2: WeightChart component (Recharts LineChart, 30/90 toggle)</name>
  <files>frontend/src/components/charts/weight-chart.tsx, frontend/src/components/charts/weight-chart.test.tsx</files>
  <behavior>
    - Props: `{ entries: WeightLogResponse[], rangeDays: 30 | 90, motionDisabled: boolean, onRangeChange?: (r: 30|90) => void }`.
    - Filters `entries` to the last `rangeDays` days from the most recent entry's date.
    - Sorted ascending (oldest left, newest right) for the line.
    - Renders `<ResponsiveContainer width="100%" height={256}><LineChart>...</LineChart></ResponsiveContainer>`.
    - Y-axis tickFormatter: `(v) => v.toFixed(1) + ' kg'`. X-axis tickFormatter: `(d) => d.slice(5)` (MM-DD).
    - Line: `<Line type="monotone" dataKey="kg" stroke="#10b981" strokeWidth={2} isAnimationActive={!motionDisabled} animationDuration={600} />`.
    - Tooltip: `<Tooltip formatter={(v) => [v.toFixed(1)+' kg', 'Weight']} animationDuration={motionDisabled?0:200} />`.
    - Two toggle buttons "30d" / "90d" above the chart; clicking calls `onRangeChange?.(r)`.
    - Empty state: when filtered entries.length === 0, render `<p>Log a weight to see your trend</p>` instead of the chart.
    - Tests:
      - `test_weight_chart_renders_with_30_day_data` — pass 60 entries, assert filtered to last 30 days.
      - `test_weight_chart_empty_state_when_no_entries` — empty array → 'Log a weight to see' string in DOM.
      - `test_weight_chart_disables_animation_when_motion_disabled` — pass motionDisabled=true → inspect <Line> props via test renderer for isAnimationActive=false.
  </behavior>
  <action>Implement the component. Use Recharts' `<LineChart>`, `<Line>`, `<XAxis>`, `<YAxis>`, `<Tooltip>`, `<ResponsiveContainer>`. Map `entries.map(e => ({ kg: e.kg, date: e.logged_at.slice(0,10) }))` into the chart data. The 30/90 toggle is a simple useState within the component if `onRangeChange` is not supplied; otherwise it's controlled by the parent.</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/components/charts/weight-chart</automated>
  </verify>
  <done>3 vitest assertions pass; component renders without console errors for empty + populated + motion-disabled cases.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P5-C.3: WeeklyKcalChart component (Recharts BarChart + target ReferenceLine)</name>
  <files>frontend/src/components/charts/weekly-kcal-chart.tsx, frontend/src/components/charts/weekly-kcal-chart.test.tsx</files>
  <behavior>
    - Props: `{ days: DayMealsResponse[], targetKcal: number, motionDisabled: boolean }`.
    - Backfill: build a 7-element array spanning [today-6, today]; for each day, find matching `days[].date` (YYYY-MM-DD) or default to `{ date, total_kcal: 0 }`.
    - Renders `<BarChart>` with 7 bars; bar color via `kcalColorClasses(kcalColorBand(d.total_kcal, targetKcal)).stroke` (hex string).
    - `<ReferenceLine y={targetKcal} stroke="#64748b" strokeDasharray="3 3" label="Target" />`.
    - `<Bar isAnimationActive={!motionDisabled} animationDuration={600} />`.
    - Y-axis: kcal integer. X-axis: weekday short (Mon/Tue/...) — derive via `new Date(date).toLocaleDateString('en-US', { weekday: 'short' })`.
    - Tests:
      - `test_weekly_kcal_chart_backfills_missing_days` — pass days for only today and 2 days ago, assert chart data length === 7.
      - `test_weekly_kcal_chart_bar_color_red_when_over_target` — day with total_kcal > targetKcal → bar fill hex matches red band.
      - `test_weekly_kcal_chart_disables_animation_when_motion_disabled`.
  </behavior>
  <action>Implement the component. Reuse `kcalColorBand` and `kcalColorClasses` from `frontend/src/lib/kcal-color.ts` (which P5-D.1 creates — order Slice D's first task before this if executor needs strict ordering; alternatively this task can stub the color helpers and Slice D refactors them, but cleanest is C.3 depends on D.1's color helper. Resolution: do P5-D.1 BEFORE P5-C.3 — the slice ordering is suggestive, not strict).</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/components/charts/weekly-kcal-chart</automated>
  </verify>
  <done>3 vitest assertions pass; component handles missing-day backfill correctly; bar colors match target-band logic.</done>
</task>

---

## Slice D — Dashboard integration (3 tasks)

<task type="auto" tdd="true">
  <name>Task P5-D.1: Refactor kcal-color helper + dashboard-copy module + KcalPill refactor + tests</name>
  <files>frontend/src/lib/kcal-color.ts, frontend/src/lib/dashboard-copy.ts, frontend/src/app/dashboard/kcal-pill.tsx, frontend/src/app/dashboard/kcal-color.test.ts, frontend/src/app/dashboard/dashboard-copy.test.ts</files>
  <behavior>
    - `kcal-color.ts`:
      - `kcalColorBand(totalKcal: number, targetKcal: number): 'green' | 'amber' | 'red'`. Rules: target ≤ 0 → 'red' if total > 0 else 'green'; total > target → 'red'; total > 0.9 * target → 'amber'; else 'green'.
      - `kcalColorClasses(band)` returns `{ bg: 'bg-emerald-100', text: 'text-emerald-900', stroke: '#10b981' }` (and amber + red equivalents).
    - `dashboard-copy.ts`:
      - Exports `dashboardCopy: Record<PrimaryGoal, DashboardCopy>` where `DashboardCopy = { kcalFraming: (consumed, target, proteinRemainingG) => string; targetPillLabel: string; secondaryCta: { label: string; href: string }; weeklyChartTitle: string; weightChartTitle: string }`.
      - weight_loss kcalFraming: `consumed < target ? \`You're \${target-consumed} kcal under target\` : \`You're \${consumed-target} kcal over\``.
      - muscle_gain kcalFraming: emphasizes protein when proteinRemainingG !== undefined and > 0: `\`\${proteinRemainingG} g protein remaining\`` else falls back to kcal language.
      - weight_loss.targetPillLabel: `'Loss target: −0.5 kg / week'`. muscle_gain.targetPillLabel: `'Gain target: +0.25 kg / week'`.
      - secondaryCta both goals: `{ label: 'Log a meal', href: '/dashboard' }` (anchor only).
    - `kcal-pill.tsx` refactored to import `kcalColorBand` + `kcalColorClasses` from the new helper. No visual change.
    - Tests:
      - kcal-color tests as enumerated in must_haves artifacts.
      - dashboard-copy tests as enumerated.
  </behavior>
  <action>Extract the RED/AMBER/GREEN logic out of `kcal-pill.tsx` into `kcal-color.ts`. Refactor `kcal-pill.tsx` to use the helper. Create `dashboard-copy.ts` with the goal-aware copy record. Add the two test files. Run existing tests to ensure no regression in KcalPill snapshot behavior (if any).</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/app/dashboard/kcal-color.test.ts src/app/dashboard/dashboard-copy.test.ts</automated>
  </verify>
  <done>kcal-color band logic tested at boundary conditions; dashboard-copy returns distinct strings per goal; KcalPill still renders correctly (existing tests pass).</done>
</task>

<task type="auto">
  <name>Task P5-D.2: KcalRing animated SVG component</name>
  <files>frontend/src/app/dashboard/kcal-ring.tsx, frontend/src/app/dashboard/kcal-ring.test.tsx</files>
  <action>Create `<KcalRing totalKcal targetKcal motionDisabled />` ('use client'). SVG 180×180. Two `<circle cx=90 cy=90 r=80>` — track (gray bg) and progress. Progress circle has `stroke-dasharray={2*Math.PI*80}` and `stroke-dashoffset={2*Math.PI*80 * (1 - Math.min(totalKcal/targetKcal, 1))}`. Inline style `transition: 'stroke-dashoffset 600ms ease'` (collapsed by `[data-motion='disabled']` global CSS rule). Stroke color: `kcalColorClasses(kcalColorBand(...)).stroke`. Center text via `<text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">{totalKcal} / {targetKcal} kcal</text>`. Tests: ring renders the right offset for 50%, 90%, 100%, 120% target ratios; stroke color matches band; component does NOT call any external library beyond React.</action>
  <verify>
    <automated>cd frontend && pnpm vitest run src/app/dashboard/kcal-ring</automated>
  </verify>
  <done>KcalRing renders with stroke-dashoffset computed from totalKcal/targetKcal; transition CSS present; tests pass.</done>
</task>

<task type="auto">
  <name>Task P5-D.3: StreakBadge + MotionDetector + globals.css reduced-motion override + dashboard page integration</name>
  <files>frontend/src/app/dashboard/streak-badge.tsx, frontend/src/app/dashboard/motion-detector.tsx, frontend/src/lib/motion.ts, frontend/src/lib/zod-schemas.ts, frontend/src/app/dashboard/page.tsx, frontend/src/app/globals.css</files>
  <action>
    1. `streak-badge.tsx` (server component): `<StreakBadge streakCount streakState />`. Renders pill with 🔥 + count; state-keyed bg (emerald-100 active, amber-100 paused, gray-100 broken). When streakCount===0, render 'Start a streak' instead of the flame.
    2. `motion-detector.tsx` ('use client'): on mount, call `detectMotionPreference()` and set/unset `document.documentElement.dataset.motion`. Listen for `matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', ...)` and `navigator.connection?.addEventListener('change', ...)`. Clean up on unmount.
    3. `motion.ts`: pure helper `detectMotionPreference()` — SSR-safe (returns all-false when window/navigator undefined).
    4. `zod-schemas.ts`: extend `profileResponseSchema` with `streak_count: z.number().int().nonnegative()`, `streak_last_logged_at: z.string().nullable()`, `streak_state: z.enum(['active','paused','broken'])`.
    5. `globals.css`: append the [data-motion='disabled'] block — `[data-motion="disabled"] *, [data-motion="disabled"] *::before, [data-motion="disabled"] *::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; scroll-behavior: auto !important; }`.
    6. `page.tsx` (server component) integration:
       - Add the `/api/weights?limit=90` fetch in the parallel block (replace `?limit=30`; chart filters down to 30 client-side).
       - Add `/api/meals?days=7` fetch (Phase 3 grouped endpoint — returns the 7-day shape).
       - Pull `dashboardCopy[profile.primary_goal]` and use it for KcalFraming, targetPillLabel, weeklyChartTitle, weightChartTitle.
       - Render order: header → `<Avatar profile recentWeights />` → `<StreakBadge streakCount={profile.streak_count} streakState={profile.streak_state} />` → `<KcalRing totalKcal targetKcal motionDisabled={false} />` (motionDisabled is set on the html element via MotionDetector; the ring reads via CSS, so the prop default is fine) → `<KcalPill />` → goal-aware copy string → `dynamic <WeightChart entries={weights} />` → `dynamic <WeeklyKcalChart days={weekDays.days} targetKcal={profile.daily_kcal_target} />` → existing `<TargetCard>`, `<WeightLogCard>`, `<MealLogIsland>`.
       - Dynamic imports via `next/dynamic`: `const WeightChart = dynamic(() => import('@/components/charts').then(m => m.WeightChart), { ssr: false, loading: () => <ChartLoadingSkeleton /> })` and same for WeeklyKcalChart.
       - Mount `<MotionDetector />` once as a sibling to `<main>`.
  </action>
  <verify>
    <automated>cd frontend && pnpm build 2>&1 | tee /tmp/p5-build.log && pnpm vitest run src/app/dashboard src/lib/motion 2>&1 | tail -20</automated>
  </verify>
  <done>`pnpm build` succeeds; `/dashboard` route appears in build output; existing dashboard tests pass; StreakBadge + MotionDetector render without console errors; MotionDetector sets data-motion attribute on prefers-reduced-motion match (covered by motion.ts unit test).</done>
</task>

---

## Slice E — Verify + traceability (1 task)

<task type="auto">
  <name>Task P5-E.1: Bundle measurement + REQUIREMENTS.md / ROADMAP.md flip + summary</name>
  <files>.planning/REQUIREMENTS.md, .planning/ROADMAP.md</files>
  <action>
    1. Run `cd frontend && pnpm build` and capture the route table. Record `/dashboard` First Load JS in the SUMMARY (target ≤ 260 kB; current baseline 231 kB + ~25 kB Recharts gzipped + ~3 kB inline avatar SVG; if measurement exceeds 260 kB, investigate before flipping requirements).
    2. Verify Recharts is in a dynamic chunk and NOT in the /dashboard server chunk: `pnpm build` output should show a separate chunk containing recharts; alternatively grep the build output for "First Load JS shared by all" + "/dashboard" lines.
    3. Run full backend test suite: `cd backend && pytest -x` — count must be ≥ 270 (252 baseline + 18+ new).
    4. Edit `.planning/REQUIREMENTS.md` — flip DASH-01..DASH-07 from `[ ]` to `[x]`. Status column in Traceability table → "Complete". Add status notes:
       - DASH-01: "Complete — static SVG sprite per CONTEXT.md D-AVATAR-STATIC-SVG; Rive deferred to v1.1."
       - DASH-07: "Complete — Rive runtime check N/A (no Rive in v1); Recharts verified dynamic-imported via pnpm build output; reduced-motion + slow-connection auto-disable via [data-motion='disabled'] global CSS rule."
    5. Edit `.planning/ROADMAP.md` — flip Phase 5 row in the Progress table to Complete + record completion date 2026-05-13.
    6. Manual checkpoint note in plan summary: confirm the **streak-on-weight-log interpretation** (Slice A) matches user intent; if user wants meal-only streak, remove the compute_streak call from `weights.py` and re-run the streak tests.
  </action>
  <verify>
    <automated>cd backend && pytest -x -q 2>&1 | tail -3 && cd ../frontend && pnpm build 2>&1 | grep -E "(/dashboard|First Load|recharts)" | head -10</automated>
  </verify>
  <done>Backend test count ≥ 270; pnpm build succeeds; /dashboard First Load JS ≤ 260 kB; DASH-01..07 flipped to Complete; ROADMAP Phase 5 row flipped to Complete.</done>
</task>

---

## Phase Verification

After all 12 tasks complete:

- **Backend:** `pytest -x` reports ≥ 270 passing, 0 failing.
- **Frontend:** `pnpm vitest run` reports all new test suites passing.
- **Build:** `pnpm build` succeeds; `/dashboard` First Load JS ≤ 260 kB.
- **Bundle invariant:** Recharts does NOT appear in the synchronous /dashboard chunk. Avatar SVG is served from /public (no JS cost on the dashboard chunk; only the small `<svg><use>` consumer code).
- **Reduced motion:** Manually toggle DevTools "Emulate CSS `prefers-reduced-motion: reduce`" → `<html data-motion="disabled">` appears, avatar breath/blink stop, kcal ring transition instantaneous, Recharts bars/lines draw without animation.
- **Slow-connection:** DevTools Network throttling "Slow 3G" → `data-motion="disabled"` set on next mount (Note: DevTools throttling does not necessarily change `navigator.connection.effectiveType`; manual override via DevTools console `Object.defineProperty(navigator.connection, 'effectiveType', { value: '2g' })` then fire a 'change' event on the connection — document in dev workflow).
- **Streak grace:** Manual flow: log a meal today → streak 1 active. Skip a day. Next day log → streak 2 active. Skip 2 days. Next log → streak shown as paused with previous count, then active+1 on next day.
- **Goal-aware copy:** Toggle profile.primary_goal between weight_loss and muscle_gain in /profile; dashboard renders different secondary copy and pill labels.

## Success Criteria (binding)

1. **DASH-01:** Avatar SVG sprite has 20 distinct states; `<Avatar>` resolves stateKey from profile + recent weights; manually verified across 4 randomly-chosen state combinations on `/dashboard`.
2. **DASH-02:** Kcal ring stroke-dashoffset visibly transitions over 600ms on meal Confirm; collapses to 0ms under data-motion='disabled'.
3. **DASH-03 + DASH-04:** Both charts render via Recharts on `/dashboard`; chart bundle is dynamic-imported (verified in `pnpm build` output).
4. **DASH-05:** Manual A/B by toggling primary_goal — copy strings differ between weight_loss and muscle_gain renders.
5. **DASH-06:** Backend test suite includes the 9 streak integration tests + 13 streak lib unit tests; all pass.
6. **DASH-07:** Reduced-motion media query toggle + simulated `effectiveType` change both result in `data-motion='disabled'` on `<html>`; Recharts and avatar runtime are NOT in the initial dashboard bundle (size-budget gate manually verified at Slice E).
7. **Backend tests:** Total ≥ 270 passing.
8. **REQUIREMENTS.md + ROADMAP.md:** DASH-01..07 + Phase 5 row flipped to Complete.

---

*Phase 5 plan written by gsd-planner on 2026-05-13. Goal-backward analysis applied; 12 tasks across 5 slices; 10-row STRIDE register; source coverage audit verifies every ROADMAP + CONTEXT decision lands in a task. No Rive, no Lottie, no framer-motion, no new BFF route, no new Mongo collection.*
