---
phase: 05-animated-dashboard
plan: 05
subsystem: dashboard
tags: [dashboard, charts, avatar, streak, motion, recharts, svg]
dependency_graph:
  requires:
    - Phase 2 — profiles collection (clerk_id, primary_goal, daily_kcal_target, timezone)
    - Phase 2 — POST /weights (target recompute hook)
    - Phase 3 — GET /meals?days=N grouped response
    - Phase 3 — KcalPill server component
    - Phase 4 — dashboard scaffold (SnapMealCta, ScanSheet)
  provides:
    - app.lib.streak.compute_streak — pure soft-streak state machine
    - StreakState Literal alias on Profile model
    - frontend/public/avatar-sprite.svg — 20-state SVG sprite
    - frontend/src/components/avatar/* — Avatar component + state helpers
    - frontend/src/components/charts/* — WeightChart + WeeklyKcalChart + barrel
    - frontend/src/lib/kcal-color.ts — shared RED/AMBER/GREEN band logic
    - frontend/src/lib/dashboard-copy.ts — goal-aware copy module
    - frontend/src/lib/motion.ts — reduced-motion + slow-connection detector
    - frontend/src/app/dashboard/kcal-ring.tsx — animated SVG ring
    - frontend/src/app/dashboard/streak-badge.tsx — soft-streak pill
    - frontend/src/app/dashboard/motion-detector.tsx — data-motion attr controller
    - frontend/src/app/dashboard/charts-island.tsx — Recharts client island
    - [data-motion='disabled'] global CSS rule
    - vitest + @testing-library/react infra (first frontend test runner)
  affects:
    - profiles collection: streak_count / streak_state / streak_last_logged_at fields
    - shared/schemas/profile.schema.json: mirror of streak fields
    - POST /meals + POST /weights: both now persist streak alongside their primary work
    - /dashboard page: complete UX overhaul, server-rendered shell + client charts
tech_stack:
  added:
    - recharts ^3.8.1 (charts)
    - vitest ^4.1.6 (test runner)
    - @testing-library/react ^16.3.2
    - @testing-library/jest-dom ^6.9.1
    - @vitejs/plugin-react ^6.0.1
    - jsdom ^29.1.1
  patterns:
    - Pure-helper state machine (compute_streak) + integration tests
    - Server/client island split for Recharts (Next 15 ssr:false constraint)
    - data-motion='disabled' DOM attribute as global motion kill-switch
    - Avatar state-key fallback chain when sprite is missing an exact combo
key_files:
  created:
    - backend/app/lib/streak.py
    - backend/tests/test_streak_lib.py
    - backend/tests/test_streak_routes.py
    - frontend/public/avatar-sprite.svg
    - frontend/src/components/avatar/avatar.tsx
    - frontend/src/components/avatar/avatar-state.ts
    - frontend/src/components/avatar/avatar.test.tsx
    - frontend/src/components/avatar/README.md
    - frontend/src/components/charts/index.tsx
    - frontend/src/components/charts/weight-chart.tsx
    - frontend/src/components/charts/weight-chart.test.tsx
    - frontend/src/components/charts/weekly-kcal-chart.tsx
    - frontend/src/components/charts/weekly-kcal-chart.test.tsx
    - frontend/src/components/charts/loading-skeleton.tsx
    - frontend/src/lib/kcal-color.ts
    - frontend/src/lib/dashboard-copy.ts
    - frontend/src/lib/motion.ts
    - frontend/src/lib/motion.test.ts
    - frontend/src/app/dashboard/kcal-ring.tsx
    - frontend/src/app/dashboard/kcal-ring.test.tsx
    - frontend/src/app/dashboard/streak-badge.tsx
    - frontend/src/app/dashboard/motion-detector.tsx
    - frontend/src/app/dashboard/charts-island.tsx
    - frontend/src/app/dashboard/kcal-color.test.ts
    - frontend/src/app/dashboard/dashboard-copy.test.ts
    - frontend/vitest.config.ts
    - frontend/vitest.setup.ts
  modified:
    - backend/app/models/profile.py (streak fields + StreakState alias)
    - backend/app/routes/profile.py (streak defaults on first create; preserve on resubmit)
    - backend/app/routes/meals.py (compute_streak after meal insert)
    - backend/app/routes/weights.py (compute_streak merged into target $set)
    - backend/tests/test_profile_models.py (+14 streak tests)
    - backend/tests/test_profile_routes.py (+6 streak route tests)
    - shared/schemas/profile.schema.json (streak fields mirror)
    - frontend/src/lib/zod-schemas.ts (PrimaryGoal type alias; profileResponseSchema)
    - frontend/src/app/dashboard/page.tsx (full integration)
    - frontend/src/app/dashboard/kcal-pill.tsx (delegates to kcal-color helper)
    - frontend/src/app/globals.css ([data-motion='disabled'] override)
    - frontend/package.json (recharts + vitest deps + test scripts)
    - .planning/REQUIREMENTS.md (DASH-01..07 -> Complete)
    - .planning/ROADMAP.md (Phase 5 -> Complete 2026-05-13)
decisions:
  - "Plan deviation: weight logs count as streak events alongside meals (CONTEXT.md specified meal-only). Cheapest correct behavior to keep streak responsive on rest days. Documented; trivially reversed by removing compute_streak call from weights.py POST handler."
  - "Plan deviation: backdated meal POST does NOT rewrite streak history (T-05-07). compute_streak uses server-now in user-tz, NOT meal.logged_at."
  - "Next 15 forbids next/dynamic(ssr:false) in Server Components — introduced ChartsIsland client wrapper so dashboard server page can lazy-load Recharts."
  - "Race acceptance T-05-03: concurrent POST /meals + POST /weights may double-bump streak by at most 1 in a user's lifetime. Documented in compute_streak docstring; no profile-doc locking."
  - "260 kB First Load JS target is informational, not CI-enforced (per Render-only rewrite — PERF-01 deferral inherited)."
metrics:
  duration: ~1h 30min
  tasks_completed: 12
  tasks_total: 12
  backend_tests_before: 252
  backend_tests_after: 292
  backend_tests_added: 40
  frontend_tests_before: 0
  frontend_tests_after: 77
  frontend_tests_added: 77
  dashboard_first_load_js_kb: 234
  dashboard_first_load_js_target_kb: 260
  completed_date: 2026-05-13
---

# Phase 5 Plan 05: Animated Dashboard Summary

**One-liner:** Soft-streak (1-day grace) + 20-state SVG avatar + animated kcal ring + Recharts weight/weekly charts + goal-aware copy, all wrapped in a `[data-motion='disabled']` global motion kill-switch driven by `prefers-reduced-motion` and `navigator.connection`.

---

## What landed

### Slice A — Backend streak (3 tasks)

- **P5-A.1** `46c9a15`: Profile model gains `streak_count` (int 0..10000), `streak_last_logged_at` (datetime|null), `streak_state` (Literal `active`|`paused`|`broken`). ProfileCreate / ProfileUpdate keep `extra="forbid"` and do NOT expose these fields (T-05-01). `shared/schemas/profile.schema.json` regenerated. POST /profile stamps defaults on first create and preserves streak across re-submit during onboarding edits. 14 new tests.
- **P5-A.2** `85e4de7`: `app/lib/streak.py` pure helper. Full state machine; 14 unit tests including Africa/Accra day boundary, Europe/London 2026-03-29 DST skip, sub-second precision, and clock-skew (future last_logged_at). T-05-03 race acceptance documented.
- **P5-A.3** `0a16be5`: Wired into both POST /meals (after insert, server-now, NOT meal.logged_at — T-05-07) and POST /weights (merged into the existing target-recompute `$set`). 10 integration tests covering all state transitions, cross-user isolation, weight-streak parity, and backdate non-rewrite.

Backend test count: **252 → 292 (+40)**. All 252 prior tests still pass; 1 skipped (live Anthropic test, unchanged).

### Slice B — Avatar (2 tasks)

- **P5-B.1** `ec45299`: `public/avatar-sprite.svg` — 20 `<g id="state-...">` blocks composed from 5 body silhouettes + 2 heads + 3 direction arrow defs. CSS variables `--skin-tone`, `--clothing-color`, `--accent` on the sprite root. `@keyframes breath` + `@keyframes blink` defined with `@media (prefers-reduced-motion: reduce)` fallback. ~8 kB raw / ~2 kB gzipped (budget 25 kB). README documents state naming, BMI cutoffs, theming.
- **P5-B.2** `b5f2e10`: `<Avatar>` client component + pure helpers (`bmiBand`, `weightSlopeKgPerWeek`, `goalDirection`, `avatarStateKey`, `SHIPPED_STATES`). Fallback chain maps unshipped state keys to nearest shipped sprite. Vitest + @testing-library/react infra also landed here (first frontend test runner; required by D.2..D.3 tests too). 21 vitest cases.

### Slice C — Charts (3 tasks)

- **P5-C.1** `ee501c9`: `recharts ^3.8.1` installed. Barrel + ChartLoadingSkeleton + stubs for WeightChart/WeeklyKcalChart so the chunk-boundary contract holds until C.2/C.3 land. No banned animation/observability deps added.
- **P5-C.2** `5fe4f8f`: `<WeightChart>` Recharts LineChart in a ResponsiveContainer. 30/90 toggle (uncontrolled by default; controllable via `onRangeChange`). Empty state. `isAnimationActive={!motionDisabled}` + tooltip duration both honour motion preference. 7 vitest cases.
- **P5-C.3** `613ae19`: `<WeeklyKcalChart>` Recharts BarChart with backfilled 7-day window so the x-axis stays at 7 bars regardless of input gaps. Per-bar fill via `kcalColorBand` (P5-D.1 helper) so colours match KcalRing + KcalPill exactly. `<ReferenceLine>` for target. 5 vitest cases.

### Slice D — Dashboard integration (3 tasks)

- **P5-D.1** `c6759ab`: `kcal-color.ts` (shared band logic + hex strokes) + `dashboard-copy.ts` (goal-aware framing strings) + KcalPill refactored to use the helper. 26 vitest cases.
- **P5-D.2** `1a56d96`: `<KcalRing>` 180x180 SVG with stroke-dasharray + dashoffset animation (600ms ease; collapses to 0ms when motionDisabled). 10 vitest cases including 0%/50%/just-over-90%/100%/120% dashoffset math.
- **P5-D.3** `f9e6325`: All-in integration. `<MotionDetector>` toggles `<html data-motion="disabled">` on prefers-reduced-motion / saveData / 2g-3g connection. `<StreakBadge>` server pill (emerald/amber/gray + "Start a streak" affordance). `<ChartsIsland>` client wrapper that lazy-loads Recharts via `next/dynamic(ssr:false)` (Next 15 disallows ssr:false in Server Components — island pattern is the workaround). `globals.css` appended with the global `[data-motion='disabled']` motion kill rule. `page.tsx` rewritten to fetch `/api/weights?limit=90` + `/api/meals?days=7` in parallel, render Avatar + StreakBadge + KcalRing + goal framing + charts island + existing cards. 8 motion-detector vitest cases.

### Slice E — Verify (1 task — this commit)

- **P5-E.1** (this commit): REQUIREMENTS.md DASH-01..07 flipped to Complete with status notes for DASH-01 (static SVG sprite — Rive deferred) and DASH-07 (Rive runtime check N/A). ROADMAP.md Phase 5 row + checklist item flipped to Complete (2026-05-13).

---

## Verification (binding)

- `cd backend && pytest -x -q` → **292 passed, 1 skipped** (was 252; +40).
- `cd frontend && pnpm vitest run` → **77 passed, 0 failed** (was 0; +77 from scratch).
- `cd frontend && pnpm build` → green; `/dashboard` First Load JS = **234 kB** (target ≤ 260 kB; baseline 231 kB + ~3 kB for the avatar wrapper + kcal ring + island wrapper).
- Recharts in a separate dynamic chunk (`9814.2331437cf5f9b48f.js`, ~390 kB raw, ~25-30 kB gzipped). NOT in the dashboard's First Load JS budget.
- `grep -r "@rive-app\|lottie-react\|lottie-web\|framer-motion\|@sentry/nextjs\|@vercel/analytics" frontend/src/` → **no matches**. No banned imports landed.

---

## Planner-risk resolutions

1. **Streak race on concurrent POST /meals + POST /weights** (planner-flagged): Accepted as ≤1-count drift over a user's lifetime. Documented in `app/lib/streak.compute_streak` docstring (T-05-03). No profile-doc locking; same-day double log is idempotent, so the only drift case is the exact day-boundary millisecond — bounded and invisible to the user.
2. **Bundle budget overshoot risk** (planner-flagged): Did not trigger. /dashboard First Load JS = 234 kB, well under 260 kB target. Recharts tree-shaking via `import { LineChart, Bar, ... } from "recharts"` (named imports, not barrel) was already the pattern; no further trimming needed. If a future delta pushes us close, the next lever is to lazy-load the avatar SVG `<use>` consumer too.
3. **DevTools throttling doesn't change `navigator.connection.effectiveType`**: Operator smoke instructions noted in the Operator Follow-ups section below. Manual override is required for in-browser testing.

---

## Deviations from Plan

### [Rule 2 - Missing critical functionality] None auto-fixed

The plan was substantially complete; no Rule 1/2/3 deviations triggered during execution.

### Planner-acknowledged interpretation beyond CONTEXT.md

- **Weight logs count as streak events** (in addition to meals). CONTEXT.md D-STREAK-1-DAY-GRACE specifies meal logs only; the planner accepted this as a one-line addition for responsiveness on rest days. Disable by removing the `compute_streak` call from `backend/app/routes/weights.py`.
- **Backdated meal POSTs do NOT rewrite streak history**. The streak uses `now_utc = datetime.now(UTC)`, not the meal's `logged_at`. Documented as T-05-07 mitigation.
- **260 kB bundle gate is informational only**, not CI-enforced. Inherited from PERF-01 deferral (memory/render-only-rewrite.md).

### Plan-noted infra deviation absorbed into Slice B

The plan assumed vitest was available but the frontend had no test runner. Setting up vitest + @testing-library/react + jsdom + @vitejs/plugin-react landed as part of P5-B.2 (Rule 3 — blocking issue auto-fix). Total: 7 dev-dependencies added; first frontend test runner in the project; 77 tests now run on each `pnpm test`.

### Plan-noted ordering subtlety

The plan suggests Slice C → D ordering but P5-C.3 imports from P5-D.1's `kcal-color.ts`. We executed in the planner-recommended-when-strict order: A.1 → A.2 → A.3 → B.1 → B.2 → C.1 (stubs for C.2/C.3) → D.1 → C.2 → C.3 → D.2 → D.3 → E.1.

### Next 15 ssr:false constraint

The plan's verbatim snippet had `dynamic(() => import("@/components/charts").then(m => m.WeightChart), { ssr: false, ... })` directly in the server `page.tsx`. Next 15 forbids this. Solution: introduced `frontend/src/app/dashboard/charts-island.tsx` as a `"use client"` wrapper that owns the dynamic imports. The page imports the island as a plain component. Net effect on the bundle is identical — Recharts still lives in a client-only dynamic chunk.

---

## Auth gates

None encountered.

---

## Known Stubs

None. WeightChart and WeeklyKcalChart stubs introduced in P5-C.1 were replaced by real implementations in P5-C.2 + P5-C.3 within the same plan execution.

---

## Threat Flags

No new threat surface beyond the planned register. All 10 threats in the plan's STRIDE table are mitigated or explicitly accepted per disposition.

---

## Operator Follow-ups

1. **Atlas indexes for new profile fields**: NOT required. The streak fields live on the existing `profiles` document; the primary query already uses the `clerk_id` unique index. No new compound index is needed because all profile reads/writes are keyed on `clerk_id`.
2. **Manual smoke test for slow-connection auto-disable**: DevTools Network Throttling does NOT change `navigator.connection.effectiveType`. To verify the `MotionDetector` slow-connection branch in a real browser:
   ```js
   // In DevTools console on /dashboard:
   Object.defineProperty(navigator.connection, 'effectiveType', { value: '2g', configurable: true });
   navigator.connection.dispatchEvent(new Event('change'));
   // Then check:
   document.documentElement.dataset.motion; // 'disabled'
   ```
   The `prefers-reduced-motion` branch IS testable via DevTools → Rendering → Emulate CSS media feature `prefers-reduced-motion: reduce`.
3. **Render auto-deploy on push to main**: Both fitgh-api (backend) and fitgh-web (frontend) should auto-rebuild on the merge. Verify after the next push that the Render dashboard shows green deploys; the /dashboard route on production should show the new ring + avatar + charts.
4. **No env vars added** in this phase. No `.env.example` updates required.

---

## Self-Check: PASSED

- 20 state ids in `frontend/public/avatar-sprite.svg`: FOUND (verified by the plan's check-script).
- All 11 commits present in `git log --oneline c3fa42c..HEAD`: FOUND.
- Backend test count ≥ 270 (target): 292 PASS.
- Frontend build green; /dashboard First Load JS ≤ 260 kB: 234 kB PASS.
- No banned imports in frontend/src: PASS.
- DASH-01..07 flipped to Complete in REQUIREMENTS.md + ROADMAP.md: PASS.

---

## Commits in this plan

| Task | Hash | Type | Description |
|------|------|------|-------------|
| P5-A.1 | `46c9a15` | feat | Profile streak fields + JSON schema mirror |
| P5-A.2 | `85e4de7` | feat | app/lib/streak.py pure helper + 14 unit tests |
| P5-A.3 | `0a16be5` | feat | wire compute_streak into POST /meals + /weights |
| P5-B.1 | `ec45299` | feat | static avatar sprite SVG + design README |
| P5-B.2 | `b5f2e10` | feat | Avatar component + state helpers + vitest infra |
| P5-C.1 | `ee501c9` | chore | install recharts + chart barrel + skeleton |
| P5-D.1 | `c6759ab` | refactor | kcal-color helper + dashboard-copy module |
| P5-C.2 | `5fe4f8f` | feat | WeightChart (Recharts LineChart 30/90 toggle) |
| P5-C.3 | `613ae19` | feat | WeeklyKcalChart (BarChart + target overlay) |
| P5-D.2 | `1a56d96` | feat | KcalRing animated SVG component |
| P5-D.3 | `f9e6325` | feat | dashboard integration — StreakBadge, MotionDetector, charts |
| P5-E.1 | (this commit) | docs | SUMMARY + REQUIREMENTS + ROADMAP flips |
