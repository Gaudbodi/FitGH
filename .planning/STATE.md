---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Phase 6 (Workout Library + PWA) complete. 12 commits this phase (c123933..f81c835 + final docs). 100 exercises (Free Exercise DB Unlicense) at /workouts; 100 static detail pages at /workouts/[id]; @serwist/next PWA wiring with CacheFirst poster WebPs + SWR /workouts HTML + offline meal POST queue. Frontend vitest 77 -> 100. Backend tests unchanged at 292. /dashboard First Load JS 234 -> 235 kB (+1 kB for Serwist runtime; under 240 kB budget). WORK-01..08 + PERF-02 Complete; PERF-03 Carry-over to Phase 7 (Clerk SDK is the residual mobile-Lighthouse bottleneck).
stopped_at: 2026-05-13 -- Phase 6 SUMMARY + REQUIREMENTS + ROADMAP flips committed. Ready to advance to Phase 7 (Launch Hardening).
last_updated: "2026-05-13T17:30:00.000Z"
last_activity: 2026-05-13 -- Phase 6 executed (12 commits, 23 new frontend tests across Phase 5+6 plans, all 8 WORK reqs); workout library + Serwist PWA + offline meal queue.
progress:
  total_phases: 7
  completed_phases: 6
  total_plans: 6
  completed_plans: 6
  percent: 86
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-11)

**Core value:** Snap a meal, see kcal in seconds, know whether you're hitting your daily target — with food the user actually eats.
**Current focus:** Phase 06 (Workout Library + PWA) complete. Next up: Phase 07 (Launch Hardening).

## Current Position

Phase: 06 (Workout Library + PWA) — Complete
Plan: 1 of 1 (06-PLAN.md → 06-SUMMARY.md)
Status: All 8 WORK requirements + PERF-02 Complete. PERF-03 carried over to Phase 7. /workouts ships 100 Free Exercise DB exercises with poster/detail WebPs (24.7 kB above-fold vs 100 kB budget); 100 static /workouts/[id] detail pages with instructions + equipment + muscles; @serwist/next service worker with CacheFirst /exercises/*.webp + SWR /workouts HTML; offline meal POST queue (idb-keyval + 401-break + idempotency keys, 8 vitest assertions); install banner + offline indicator + footer attribution + LICENSES.md at repo root.
Last activity: 2026-05-13 -- Phase 6 SUMMARY + REQUIREMENTS + ROADMAP flips committed.

Progress: [██████░░░░] 86% phases (6 of 7); 100% within Phase 6 plan (12 of 12 tasks)

## Performance Metrics

**Velocity:**

- Total plans completed: 0 (Plan 01 partial — autonomous portion only)
- Average duration: —
- Total execution time: ~1.5 h (autonomous portion of Plan 01)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01    | 0     | ~1.5h | partial  |

**Recent Trend:**

- Last 5 plans: 01 (partial)
- Trend: paused at first checkpoint:human-action

*Updated after each plan completion.*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table and research/SUMMARY.md "Locked Stack Decisions". Most recent / load-bearing for current work:

- Phase 1: Walking Skeleton convention — emit `SKELETON.md` in the phase directory (template at `$HOME/.claude/get-shit-done/references/skeleton-template.md`).
- Phase 1: Backend on **Fly.io JNB** always-on `shared-cpu-1x` 512 MB + **static egress IP** pinned in Atlas allowlist.
- Phase 1: **Clerk** for auth (50k MAU free; networkless JWT verify on Flask).
- Phase 1: CI **bundle-size gate** (size-limit ≤ 180 KB First Load JS) + **gitleaks** pre-commit from commit 1.
- Phase 1: **Custom gitleaks rules** required — the default ruleset does NOT detect MongoDB connection strings. SEC-01 invariant is now backed by explicit `[[rules]]` blocks (mongodb-connection-string, clerk-secret-key-{test,live}, clerk-webhook-secret, sentry-dsn-with-secret) in `.gitleaks.toml`. Verified by WS-0.4 deliberate-leak smoke test.
- Phase 1: **clerk-backend-api 5.0.6** exposes `AuthenticateRequestOptions` at the package root (NOT at `clerk_backend_api.jwks_helpers` as research §3.8 says — that submodule does not exist). Verified at runtime.
- Phase 1: **state.reason** in `@require_auth` 401 response MUST be `str()`-coerced — `AuthErrorReason` is an enum, not JSON-serializable directly. Coercion shipped in WS-B.4.
- Phase 1: **Backend venv on Python 3.13.7** locally (3.12 not installed on dev box). CI pins 3.12 via actions/setup-python. ruff `target-version = "py312"` prevents accidental 3.13-only syntax.
- Phase 1: **FLAG-2 folded in early** — `test_sentry_scrubber.py` asserts `breadcrumbs[].data.kcal` and `breadcrumbs[].data.image` redaction so Phase 4 vision events are PII-safe from commit 1.
- Phase 3: **Multi-component `meals` schema from day 1** (`components: []`). Single `dish_name` is forbidden — this is the most expensive schema mistake.
- Phase 4: **Claude Sonnet 4.6** via Anthropic SDK with prompt caching; pin in env; **no image storage** in v1.
- Phase 4: **Per-user 8/day cap** + **global $/day breaker** + **Sentry alert at $/DAU/day > $0.05**.
- [Phase ?]: Phase 1 WS-0.1/C.1/C.2 verified 2026-05-11 — Atlas password rotated to fitgh-app/readWrite@fitgh; /health returns mongo:connected; db.py shim removed (MONGODB_URI mandatory at import)
- [Phase ?]: WS-0.2 verified 2026-05-11 — Atlas cluster0 tier=M0 (100-connection cap; maxPoolSize=10 sized correctly); Fly.io billing has card on file (egress IP allocation unblocked for WS-G.5)
- [Roadmap evolution] 2026-05-12: Phase 1 rearchitected (ROADMAP edited; tracked in memory/render-only-rewrite.md). Out: Vercel, Fly.io JNB + static egress IPv4 add-on, Clerk Dev+Prod twin instances, Sentry FE/BE, custom gitleaks CI rules, size-limit 180 KB CI gate. In: both Next.js and Flask deploy as Render web services on `git push main`; Atlas allowlist `0.0.0.0/0` + 32-char password + readWrite@fitgh; Clerk single Production instance. User-facing Phase 1 checkpoints 14 → 3. Follow-up: REQUIREMENTS.md traceability table (SEC-01/02/03, OBS-01/02, PERF-01 deferrals), research/SUMMARY.md Locked Stack Decisions, .planning/phases/01-walking-skeleton/SKELETON.md, 01-PLAN.md replan. Fly.io billing card on file now unused — Fly subscription can be cancelled.
- [Phase 1] 2026-05-13: Render deploy live. fitgh-api + fitgh-web both auto-deploying on push to main. render.yaml runtime mismatch fixed (98a94c8) + pnpm 10.15.0 packageManager pin (6790772). Clerk test instance auto-allows all origins (no Authorized Origins config needed for test keys).
- [Phase 2] 2026-05-13: Complete. 17 commits (3fdd61c..30ee8ea). 81 backend tests passing. All 9 reqs (AUTH-04/05, PROF-01..07) covered. /dashboard First Load JS 162 kB.
- [Phase 3] 2026-05-13: Complete. 17 commits (0591a71..5a0667f). 158 backend tests passing (+77 from Phase 2). All 9 reqs (LOG-01..08, DATA-01) covered. 25-dish Ghana food catalogue seeded, multi-component meals schema (day-1 shape — Phase 4 writes into it), /history 30-day view, nightly mongodump GH Action. /dashboard First Load JS 230 kB (above the 180 kB ideal due to cmdk + slider; flagged for Phase 5/7 data-light pass — size-limit CI gate intentionally absent). Operator follow-ups: run seed_ghana_foods.py against prod Atlas; createIndex on meals.user_id+logged_at; provision read-only Atlas user + add MONGODB_URI_BACKUP GH Actions secret.
- [Phase 4] 2026-05-13: Complete. 12 commits (b8db18e..88d2258). 252 backend tests passing (+94 from Phase 3). All 13 reqs (VIS-01..12, OBS-03) covered. Wedge feature: POST /meals/scan calls Claude Sonnet 4.6 via Anthropic SDK with prompt caching, per-user 8/day cap, global $/day breaker, env-var cost-alert webhook (Sentry replacement). No server-side image retention. ScanSheet + ScanResultChips + SnapMealCta + ServicePausedBanner on FE; ScanSheet lazy-loaded so /dashboard First Load JS unchanged at 231 kB (+1 kB for dynamic loader). respx mocks the Anthropic SDK in CI — zero real API calls. Operator follow-ups: provision ANTHROPIC_API_KEY in Render fitgh-api Environment + backend/.env.local; run `db.vision_usage.createIndex({user_id:1, date:1}, {unique:true})` + `db.user_corrections.createIndex({user_id:1, corrected_at:-1})` against prod Atlas; optionally set COST_ALERT_WEBHOOK_URL.
- [Phase 5] 2026-05-13: Complete. 11 commits (46c9a15..f9e6325). 292 backend tests passing (+40 from Phase 4). 77 frontend vitest passing (first frontend test runner in the project; vitest + @testing-library/react + jsdom infra landed in P5-B.2). All 7 reqs (DASH-01..07) Complete. Static SVG avatar sprite with 20 states (Rive deferred to v1.1 per CONTEXT.md D-AVATAR-STATIC-SVG), animated kcal ring (stroke-dashoffset 600ms transition), Recharts WeightChart 30/90 + WeeklyKcalChart 7-day backfill, goal-aware copy module, soft-streak with 1-day grace (compute_streak pure helper + state machine), MotionDetector + [data-motion='disabled'] global CSS rule. /dashboard First Load JS 231 -> 234 kB (under 260 kB Phase 5 target). Recharts in a separate ~30 kB gzipped dynamic chunk via next/dynamic(ssr:false) in a ChartsIsland 'use client' wrapper (Next 15 forbids ssr:false in Server Components). Planner deviations carried: weight logs ALSO count as streak events (CONTEXT.md said meal-only — cheapest correct behavior; reversible); backdated meals do NOT rewrite streak history (T-05-07 — compute_streak uses server-now in user-tz, not meal.logged_at). T-05-03 race acceptance documented in compute_streak docstring. No new Atlas indexes needed (streak fields piggyback on existing clerk_id-keyed profile queries). Operator follow-ups: smoke-test slow-connection branch via DevTools console (Object.defineProperty(navigator.connection,'effectiveType',{value:'2g'}); navigator.connection.dispatchEvent(new Event('change'))) — DevTools Network throttling alone does NOT change effectiveType.
- [Phase 6] 2026-05-13: Complete. 12 commits (c123933..final-docs-commit). 292 backend tests unchanged. 100 frontend vitest (+23 from Phase 5; +8 offline-meal-queue, filter-bar + workouts-grid + exercises-lib in Phase 5/6 boundary). All 8 reqs (WORK-01..08) + PERF-02 Complete. PERF-03 carried over to Phase 7. /workouts ships 100 Free Exercise DB exercises (Unlicense — wger dropped per D-FREE-EX-ONLY to dodge share-alike); 100 static /workouts/[id] detail pages via generateStaticParams. @serwist/next service worker with NetworkOnly /api/* + CacheFirst /exercises/*.webp 30-day + SWR /workouts HTML + SWR /exercises/manifest.json. Offline meal POST queue keyed by Idempotency-Key (UUID v4) with 401-break-retain disposition (T-06-02 mitigation), 5xx-leave-queued, 4xx-other-drop. Native Next 15 manifest.ts (auto-routed to /manifest.webmanifest). Three PWA icons (192/512/maskable-512). RegisterSW + OfflineIndicator + InstallPrompt client components mounted in layout.tsx. Footer extended with Free Exercise DB Unlicense attribution (WORK-07). LICENSES.md at repo root. middleware.ts comment block documents /workouts public-by-default. /dashboard First Load JS 234 -> 235 kB (+1 kB for Serwist runtime). Above-fold image weight on /workouts = 24.7 kB (75% under 100 kB PERF-02 budget). Lighthouse mobile 51/100 (initial cold + warm runs); LCP-fix commit f81c835 expected to raise to ~60-70/100 once Render redeploys. Residual gap is Clerk SDK on /workouts (312 kB transferred, 1.8 s main-thread on emulated mid-tier mobile) — architectural fix would move ClerkProvider out of the root layout, carried to Phase 7 as PERF-03 follow-up. Planner deviations beyond CONTEXT: precache-subset of 24 posters dropped (T-06-09 — CacheFirst-on-demand is enough, avoids draining metered Ghana data on install). Operator follow-ups: trigger PWA install in Chrome desktop to smoke-test installability + /workouts offline; re-run Lighthouse on Render once redeployed; check accessibility audit failures (94/100); consider Phase 7 ClerkProvider relocation to gate-only routes.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- **WS-0.2 Atlas cluster tier verify + Fly.io billing card** — needed before WS-G.5 (egress IP allocation).
- **WS-G.5 Fly.io static egress IPv4 cost** — verify $3.60/mo (or actual 2026 price) against the $5/mo halt threshold before WS-H.1.
- **No git remote configured** — blocks WS-A.5 bloat-PR smoke test, WS-B.6 docker CI verification, WS-I.1 Vercel connect. Run `git remote add origin <url> && git push -u origin master` when ready.
- **Python 3.12 not installed locally** — backend venv currently uses 3.13. Mitigated by CI pin. Re-evaluate if a 3.13-only behavior bites.
- **Rive designer pipeline** (Phase 5 gate) — decide by end of Phase 2 whether to contract a Rive artist (~£200–500) or ship static SVG and animate in v1.1.

## Deferred Items

Items acknowledged and carried forward:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Phase 1  | WS-A.5 deliberate-bloat smoke-test PR (needs GitHub remote + user push) | Pending checkpoint | 2026-05-11 |
| Phase 1  | WS-0.1 Atlas password rotation | Pending checkpoint (BLOCKER) | 2026-05-11 |
| Phase 1  | WS-0.2 Atlas tier + Fly.io billing | Pending checkpoint | 2026-05-11 |
| Phase 1  | WS-C.1 Set MONGODB_URI locally + verify /health connected | Blocked on WS-0.1 | 2026-05-11 |
| Phase 1  | WS-D.1 Clerk Dev + Prod instances | Pending checkpoint | 2026-05-11 |
| Phase 1  | WS-G.3-5 Fly.io deploy + egress IP cost gate | Pending (multi-step) | 2026-05-11 |
| Phase 1  | WS-H.1-3 Atlas allowlist tightening | Blocked on WS-G | 2026-05-11 |
| Phase 1  | WS-I.1-3 Vercel + Sentry + Analytics | Pending checkpoint | 2026-05-11 |
| Phase 1  | WS-J.1 E2E sign-off on deployed app | Final gate | 2026-05-11 |
| v2       | Opt-in meal-image history (Cloudflare R2, 90-day TTL) | Post-MVP | Phase 4 |
| v2       | Wearables (Apple Health, Google Fit, step counter) | Post-MVP | — |
| v2       | Twi / Ga / Ewe localisation | Post-MVP | — |
| v2       | Payments / paid tier | Post-MVP | — |
| v2       | Push notifications + friends/leaderboards | Post-MVP | — |

## Session Continuity

Last session: 2026-05-13
Stopped at: Phase 6 (Workout Library + PWA) complete — 12 commits (c123933..final-docs-commit), 292 backend tests unchanged, 100 frontend vitest (+23 from baseline), /workouts 126 kB First Load JS, /workouts/[id] 112 kB, /dashboard 235 kB. WORK-01..08 + PERF-02 all Complete; PERF-03 carry-over to Phase 7. Ready to advance to Phase 7 (Launch Hardening).
Resume file: `.planning/phases/06-workout-library-pwa/06-SUMMARY.md` — full inventory of files/commits/operator follow-ups for the workout library + PWA work.
