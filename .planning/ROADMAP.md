# Roadmap: FitGH

**Mode:** Vertical MVP (PROJECT_MODE=mvp)
**Granularity:** standard (5–8 phases)
**Created:** 2026-05-11
**Phases:** 7

## Overview

FitGH ships in seven vertical slices, each delivering an end-to-end user capability. The hard sequence is dictated by the wedge: a Walking Skeleton proves the Clerk → Flask → Atlas trust boundary first; profile + targets give every later phase a number to hit; manual meal logging lands the multi-component `meals` schema *before* vision so the schema is correct from day 1; the image → kcal core loop ships next because food is the wedge; the animated dashboard makes progress tangible; the workout library + PWA arrive last among feature phases (and only after the kcal loop ships to a seed cohort); launch hardening closes the loop with real Ghana-edge latency measurement, privacy policy, and health-claim audit.

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (e.g., 2.1, 2.2): Urgent insertions if needed (marked `INSERTED`)

## Phases

- [ ] **Phase 1: Walking Skeleton** - End-to-end Clerk auth + Flask + MongoDB Atlas on Fly.io JNB + Vercel, with CI bundle gate, gitleaks, Sentry, and static egress IP
- [ ] **Phase 2: Onboarding + Profile + Targets** - 3-screen onboarding, Mifflin-St Jeor TDEE, weight log, target on dashboard skeleton, privacy disclosure, GDPR delete-account
- [ ] **Phase 3: Manual Meal Log + Ghana Table** - 25-dish FAO/INFOODS catalogue, search, multi-component meal schema, daily total, remaining-kcal pill, nightly mongodump
- [ ] **Phase 4: Image -> Kcal Core Loop** - Client compression, Sonnet 4.6 with cached system + Ghana table + components tool-use, table re-match, component chips, inline correction, per-user cap + global $/day breaker
- [ ] **Phase 5: Animated Dashboard** - Rive avatar state-machine, animated kcal ring, Recharts weight + weekly-kcal charts, goal-aware home, soft-streak with 1-day grace
- [ ] **Phase 6: Workout Library + PWA** - 80–120 curated exercises, search + equipment filter, WebP poster -> tap-load WebM, next-pwa + IndexedDB offline cache, attribution
- [ ] **Phase 7: Launch Hardening** - Lagos WebPageTest, real privacy policy, data export + account-delete flows, health-claim copy audit, Anthropic spend alerts, golden-set re-run, production deploy

## Phase Details

### Phase 1: Walking Skeleton
**Goal:** Prove the entire trust boundary end-to-end — a Clerk-authenticated user can hit a `/dashboard` page that fetches their record from Flask, which reads it from MongoDB Atlas — with every supporting platform concern (deploy, secrets, CI, observability, network) wired correctly from day one.
**Mode:** mvp
**Depends on:** Nothing (first phase)
**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-06, SEC-01, SEC-02, SEC-03, SEC-04, OBS-01, OBS-02, PERF-01, DEPLOY-01, DEPLOY-02
**Success Criteria** (what must be TRUE):
  1. A user can sign in via Clerk-hosted UI (email/password OR Google) and land on `/dashboard` showing their email pulled from MongoDB Atlas through Flask — page renders end-to-end with no shortcuts.
  2. A user can sign out from any page; refreshing after sign-out lands them on the sign-in screen (httpOnly session cookie cleared).
  3. The Flask `/health` endpoint returns `{ok: true, mongo: "connected"}` from the Fly.io JNB machine, and the static egress IP is pinned in the Atlas allowlist (no `0.0.0.0/0` in production config).
  4. A CI pull request that pushes First Load JS above 180 KB gzipped on the dashboard route fails the build; a commit that contains a Mongo URI is blocked by the gitleaks pre-commit hook.
  5. Sentry (frontend + backend) and Vercel Analytics + Speed Insights receive at least one real event from the deployed app, and the Flask `Authorization: Bearer <jwt>` path is verified networkless on every protected request.
**Plans:** TBD
**Skeleton spec:** `.planning/phases/01-walking-skeleton/SKELETON.md`

### Phase 2: Onboarding + Profile + Targets
**Goal:** A new user can finish a ≤3-screen onboarding in under 60 seconds, leaves with a daily kcal target (and protein target if muscle-gain) shown on the dashboard, can log their weight, edit their profile later, and has signed an explicit consent that meal photos will be sent to an LLM vision provider — plus a working account-deletion path.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** AUTH-04, AUTH-05, PROF-01, PROF-02, PROF-03, PROF-04, PROF-05, PROF-06, PROF-07
**Success Criteria** (what must be TRUE):
  1. A new user completes onboarding in ≤3 screens — capturing name, sex, height, weight, age, timezone, locale (Ghana / diaspora), activity level, and primary goal (weight loss OR muscle gain) — and lands on the dashboard with a daily kcal target visible.
  2. The kcal target on the dashboard equals Mifflin-St Jeor BMR × activity factor − deficit (or + surplus), with a 1200 kcal female / 1500 kcal male floor and a "consult a clinician" disclaimer when the floor is hit; muscle-gain users additionally see a protein target of 1.6 g/kg bodyweight.
  3. A user can edit any profile field after onboarding and the displayed targets recompute on save; a user can log a new weight entry and the entry is persisted (history viewable).
  4. The sign-up flow displays a privacy disclosure naming Anthropic (Claude) as the meal-image processor before the user can finish onboarding; the disclosure links to a stub privacy policy.
  5. A user can hit "Delete account" in settings and Clerk + Flask cascade-delete all their FitGH data (profile, weights — no meals yet) via a Clerk webhook, with a confirmation screen.
**Plans:** TBD

### Phase 3: Manual Meal Log + Ghana Table
**Goal:** Without any AI involvement, a user can search the 25-dish Ghana food catalogue, log a meal as one or more components with portion sliders, see today's running total + remaining kcal pill on the dashboard, and look back through the last 30 days — proving the multi-component `meals` schema works end-to-end before vision lands on top of it.
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** LOG-01, LOG-02, LOG-03, LOG-04, LOG-05, LOG-06, LOG-07, LOG-08, DATA-01
**Success Criteria** (what must be TRUE):
  1. A user can type "jollof" (or "banku", "waakye", etc.) into a meal-log search box and pick a dish from the 25-entry Ghana food catalogue, with FAO/INFOODS-sourced kcal/100g and Ghana + diaspora portion defaults visible.
  2. A user can log a single meal as **multiple components** (e.g., banku + tilapia + shito) — each with its own portion slider showing culturally meaningful defaults ("1 ball of banku ≈ 200 g") — and the meal's total kcal + total protein are computed and displayed.
  3. The dashboard shows today's meals as a list with a running daily total and a "remaining kcal" pill (target − consumed); a user can edit or delete a logged meal and the daily total updates.
  4. A user can scroll back through at least the last 30 days of meal history grouped by day.
  5. A nightly `mongodump` runs against Atlas and uploads the encrypted dump to Cloudflare R2 (or equivalent), with the most recent dump verifiable from the operator side.
**Plans:** TBD

### Phase 4: Image -> Kcal Core Loop
**Goal:** A user can snap a photo of their plate from the dashboard, see each visible component identified separately as tap-to-edit chips with kcal ranges within ~5 seconds, correct the dish or portion inline if wrong, and have the confirmed meal persist via the same multi-component schema as Phase 3 — while every request enforces the per-user 8/day cap and the global $/day circuit breaker, and no image bytes are retained server-side.
**Mode:** mvp
**Depends on:** Phase 3
**Requirements:** VIS-01, VIS-02, VIS-03, VIS-04, VIS-05, VIS-06, VIS-07, VIS-08, VIS-09, VIS-10, VIS-11, VIS-12, OBS-03
**Success Criteria** (what must be TRUE):
  1. A user can capture or upload a meal photo from the dashboard, the image is compressed client-side (≤1024 px long edge, ≤0.5 MB, JPEG q=0.85), and within ~5 seconds the user sees each component (e.g., "jollof rice", "chicken thigh", "salad") identified separately, each with its own kcal range (low/high) and a total range — never a single point estimate.
  2. Each component is presented as a tap-to-edit chip — the user can change the dish name via Ghana-table autocomplete, adjust the portion slider, or remove the component entirely, and the total kcal recomputes; user corrections are persisted to `user_corrections` and bias defaults on the user's next scan.
  3. On confirm, the meal is saved via the **same multi-component schema** as a manually logged meal (no separate `ai_meals` collection), with kcal recomputed via Ghana-table re-match (`kcal_per_100g × portion_g_locale`, table wins over LLM kcal).
  4. After 8 vision calls in a day a user sees a friendly message and is offered the manual-entry path; when the global $/day spend exceeds the configured cap, all users see a "Service paused for the day, please log manually" banner and the manual path still works.
  5. Backend logs and Atlas data confirm that no image bytes are retained server-side after the vision call (only `(components, total_kcal, timestamp, user_id, ai_metadata)` is written); a Sentry alert fires when $/DAU/day crosses $0.05.
**Plans:** TBD
**UI hint:** yes

### Phase 5: Animated Dashboard
**Goal:** The dashboard stops being a skeleton — a Rive-animated avatar mirrors the user's sex × BMI band × goal direction, the kcal ring animates as meals are logged, a Recharts weight chart and weekly kcal-vs-target chart show real progress, copy and CTAs adapt to the user's goal, and a soft-streak with 1-day grace runs — all while honouring `prefers-reduced-motion` and auto-disabling animations on slow connections.
**Mode:** mvp
**Depends on:** Phase 4
**Requirements:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07
**Success Criteria** (what must be TRUE):
  1. On the dashboard, a user sees an animated avatar whose visual state (sex × one of 5 BMI bands × goal direction) updates after logging a weight entry or hitting their daily kcal target.
  2. The kcal ring animates from current → updated value as soon as a meal is confirmed; a 30-day / 90-day weight chart and a weekly kcal-vs-target chart render using Recharts and animate on view.
  3. Dashboard copy adapts to the user's goal — a weight-loss user sees "X kcal under target" framing while a muscle-gain user sees "Y g protein remaining" prominently.
  4. A user who logged a meal yesterday but missed today still has their streak displayed as "paused" (not reset); two consecutive missed days resets to zero.
  5. A user with `prefers-reduced-motion: reduce` set, or on a connection where `navigator.connection.effectiveType` is `2g`/`3g`, sees static graphics instead of animations — and the Rive runtime + `.riv` JSON are not in the initial bundle (verified by bundle analyser).
**Plans:** TBD
**UI hint:** yes

### Phase 6: Workout Library + PWA
**Goal:** A user can browse 80–120 curated exercises (sourced from Free Exercise DB Unlicense + wger CC-BY-SA), filter by equipment (defaulting to none + dumbbells) and target muscle, see a tiny WebP poster on the list view and tap to load the animated WebM — and install FitGH as a PWA that works offline for the workout library and queues meal logs taken on flaky connections.
**Mode:** mvp
**Depends on:** Phase 4 (kcal loop must ship to seed cohort first; workouts are gated by the wedge)
**Requirements:** WORK-01, WORK-02, WORK-03, WORK-04, WORK-05, WORK-06, WORK-07, WORK-08, PERF-02, PERF-03
**Success Criteria** (what must be TRUE):
  1. A user can browse 80–120 curated exercises and filter them by equipment (none / dumbbells / resistance bands / pull-up bar / kettlebell / barbell) and by target muscle (chest / back / legs / shoulders / arms / core / glutes / full-body); the equipment filter defaults to `none` + `dumbbells` on first open.
  2. Each exercise card shows a WebP poster ≤30 KB; tapping the poster loads the animated WebM/GIF on demand. An exercise detail page shows instructions, target muscle, equipment, and an optional curated YouTube embed using the lite-youtube-embed pattern (~3 KB placeholder).
  3. A footer attribution credits both sources ("Exercise data from wger.de (CC-BY-SA 4.0) and Free Exercise DB (Unlicense)"); a `LICENSES.md` lives in the repo root.
  4. A user can install FitGH as a PWA from a mid-tier Android browser, and after installation the workout library renders fully offline (service worker cache-first for media, IndexedDB snapshot of the `exercises` collection); a meal logged while offline replays automatically on reconnect.
  5. Lighthouse mobile performance ≥ 90 on the workout-library route on simulated mid-tier Android (Moto G Power, Slow 4G), and above-fold image weight ≤ 100 KB per route is enforced in CI.
**Plans:** TBD
**UI hint:** yes

### Phase 7: Launch Hardening
**Goal:** Verify, document, and harden everything that makes the difference between "demoable" and "safely launchable" — real Ghana-edge latency measured from Lagos, a real privacy policy live (naming Anthropic as a sub-processor), working data-export and account-delete endpoints, health-claim copy audited so FitGH is "fitness tracking" not "medical advice," Anthropic spend alerts wired, and the vision golden-set re-run on the production model pin before production deploy.
**Mode:** mvp
**Depends on:** Phase 6
**Requirements:** PERF-04, LEGAL-01, LEGAL-02, LEGAL-03
**Success Criteria** (what must be TRUE):
  1. A WebPageTest run from the Lagos node against the production deploy reports p75 TTFB ≤ 2 s on the dashboard route; if not, a Cloudflare-in-front decision is documented and the fix lands before launch.
  2. A live `/privacy` page exists naming Anthropic (Claude Sonnet 4.6) as the meal-image sub-processor and lists every other data processor (Clerk, MongoDB Atlas, Fly.io, Vercel, Sentry, Cloudflare R2); the policy is linked from onboarding, the footer, and the consent screen.
  3. A user can hit a "Download all my data" button in settings and receive a JSON export of their profile, weights, and meals; the account-delete flow shipped in Phase 2 still works end-to-end against production data.
  4. A health-claim copy audit pass has run across onboarding, dashboard, target-display, and marketing copy — no "will help you lose weight" / "achieves your goal" language remains; the standard disclaimer ("FitGH is a fitness tracking tool, not medical advice…") appears in onboarding and the footer.
  5. The frozen 30-photo vision golden set has been re-run on the env-pinned model (`LLM_VISION_MODEL=claude-sonnet-4-6`) and reports <25% MAPE; Anthropic console has a hard monthly spend cap set; the production deploy is live and the launch checklist is signed off.
**Plans:** TBD
**UI hint:** yes

## Progress

**Execution Order:** Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7. Phase 6 is **not** allowed to start before Phase 4 ships to a seed cohort (research invariant: food loop before workouts).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Walking Skeleton | 0/TBD | Not started | - |
| 2. Onboarding + Profile + Targets | 0/TBD | Not started | - |
| 3. Manual Meal Log + Ghana Table | 0/TBD | Not started | - |
| 4. Image -> Kcal Core Loop | 0/TBD | Not started | - |
| 5. Animated Dashboard | 0/TBD | Not started | - |
| 6. Workout Library + PWA | 0/TBD | Not started | - |
| 7. Launch Hardening | 0/TBD | Not started | - |

## Traceability — Requirement → Phase Mapping

All v1 requirement IDs listed in REQUIREMENTS.md are mapped to exactly one phase. Categories: AUTH (6), PROF (7), LOG (8), VIS (12), DASH (7), WORK (8), PERF (4), OBS (3), SEC (4), DATA (1), LEGAL (3), DEPLOY (2) = 65 IDs total. (REQUIREMENTS.md previously stated "60 total" — re-enumerated during roadmap mapping and corrected to 65 in the canonical REQUIREMENTS.md Coverage block.)

| Requirement | Category | Phase | Status |
|-------------|----------|-------|--------|
| AUTH-01 | Authentication | Phase 1 | Pending |
| AUTH-02 | Authentication | Phase 1 | Pending |
| AUTH-03 | Authentication | Phase 1 | Pending |
| AUTH-04 | Authentication | Phase 2 | Pending |
| AUTH-05 | Authentication | Phase 2 | Pending |
| AUTH-06 | Authentication | Phase 1 | Pending |
| PROF-01 | Profile & Targets | Phase 2 | Pending |
| PROF-02 | Profile & Targets | Phase 2 | Pending |
| PROF-03 | Profile & Targets | Phase 2 | Pending |
| PROF-04 | Profile & Targets | Phase 2 | Pending |
| PROF-05 | Profile & Targets | Phase 2 | Pending |
| PROF-06 | Profile & Targets | Phase 2 | Pending |
| PROF-07 | Profile & Targets | Phase 2 | Pending |
| LOG-01 | Manual Meal Logging | Phase 3 | Pending |
| LOG-02 | Manual Meal Logging | Phase 3 | Pending |
| LOG-03 | Manual Meal Logging | Phase 3 | Pending |
| LOG-04 | Manual Meal Logging | Phase 3 | Pending |
| LOG-05 | Manual Meal Logging | Phase 3 | Pending |
| LOG-06 | Manual Meal Logging | Phase 3 | Pending |
| LOG-07 | Manual Meal Logging | Phase 3 | Pending |
| LOG-08 | Manual Meal Logging | Phase 3 | Pending |
| VIS-01 | Food Image → Kcal | Phase 4 | Pending |
| VIS-02 | Food Image → Kcal | Phase 4 | Pending |
| VIS-03 | Food Image → Kcal | Phase 4 | Pending |
| VIS-04 | Food Image → Kcal | Phase 4 | Pending |
| VIS-05 | Food Image → Kcal | Phase 4 | Pending |
| VIS-06 | Food Image → Kcal | Phase 4 | Pending |
| VIS-07 | Food Image → Kcal | Phase 4 | Pending |
| VIS-08 | Food Image → Kcal | Phase 4 | Pending |
| VIS-09 | Food Image → Kcal | Phase 4 | Pending |
| VIS-10 | Food Image → Kcal | Phase 4 | Pending |
| VIS-11 | Food Image → Kcal | Phase 4 | Pending |
| VIS-12 | Food Image → Kcal | Phase 4 | Pending |
| DASH-01 | Animated Dashboard | Phase 5 | Pending |
| DASH-02 | Animated Dashboard | Phase 5 | Pending |
| DASH-03 | Animated Dashboard | Phase 5 | Pending |
| DASH-04 | Animated Dashboard | Phase 5 | Pending |
| DASH-05 | Animated Dashboard | Phase 5 | Pending |
| DASH-06 | Animated Dashboard | Phase 5 | Pending |
| DASH-07 | Animated Dashboard | Phase 5 | Pending |
| WORK-01 | Workout Library | Phase 6 | Pending |
| WORK-02 | Workout Library | Phase 6 | Pending |
| WORK-03 | Workout Library | Phase 6 | Pending |
| WORK-04 | Workout Library | Phase 6 | Pending |
| WORK-05 | Workout Library | Phase 6 | Pending |
| WORK-06 | Workout Library | Phase 6 | Pending |
| WORK-07 | Workout Library | Phase 6 | Pending |
| WORK-08 | Workout Library | Phase 6 | Pending |
| PERF-01 | Performance | Phase 1 | Pending |
| PERF-02 | Performance | Phase 6 | Pending |
| PERF-03 | Performance | Phase 6 | Pending |
| PERF-04 | Performance | Phase 7 | Pending |
| OBS-01 | Observability | Phase 1 | Pending |
| OBS-02 | Observability | Phase 1 | Pending |
| OBS-03 | Observability | Phase 4 | Pending |
| SEC-01 | Security | Phase 1 | Pending |
| SEC-02 | Security | Phase 1 | Pending |
| SEC-03 | Security | Phase 1 | Pending |
| SEC-04 | Security | Phase 1 | Pending |
| DATA-01 | Data | Phase 3 | Pending |
| LEGAL-01 | Legal | Phase 7 | Pending |
| LEGAL-02 | Legal | Phase 7 | Pending |
| LEGAL-03 | Legal | Phase 7 | Pending |
| DEPLOY-01 | Deployment | Phase 1 | Pending |
| DEPLOY-02 | Deployment | Phase 1 | Pending |

**Coverage:** 65/65 v1 requirements mapped, 0 orphans, 0 duplicates.

## Hard Constraints from Research (enforced across phases)

These are non-negotiable invariants the planner and verifier MUST hold every phase to:

1. **Walking Skeleton is Phase 1.** Every later phase depends on the trust boundary.
2. **Food loop ships before workouts.** Phase 6 is gated on Phase 4 reaching production.
3. **Multi-component `meals` schema from Phase 3.** Single `dish_name` is forbidden — `components: [{name, matched_food_id, portion_g, kcal_low, kcal_high, kcal_point, confidence, source}]` is the day-1 shape.
4. **No image storage in v1.** Compress client-side → POST to Flask → vision call → discard bytes. R2 / opt-in history is deferred to post-MVP.
5. **Stack is locked** (see research/SUMMARY.md "Locked Stack Decisions"). Do not propose alternatives without an explicit `/gsd-research-phase` pass.
6. **Pin the model** (`LLM_VISION_MODEL=claude-sonnet-4-6`) and re-run the 30-photo golden set on any model bump.
7. **Bundle gate from Phase 1.** First Load JS ≤ 180 KB gzipped per route — enforced in CI from commit 1, not at the end.
8. **gitleaks pre-commit + rotated Atlas password** before any Phase 1 deploy.

## Research Flags

Per research/SUMMARY.md "Needs `/gsd-research-phase`":
- **Phase 4** — Sonnet 4.6 prompt engineering + golden-set construction (novel)
- **Phase 5** — Rive state-machine design + designer availability (decide pipeline by end of Phase 2)
- **Phase 7** — Real Ghana p75 latency unverified

Standard patterns, skip deeper research: Phase 1, 2, 3, 6.

---
*Roadmap created: 2026-05-11 by the gsd-roadmapper agent.*
