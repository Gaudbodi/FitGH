# Requirements: FitGH

**Defined:** 2026-05-11
**Core Value:** Snap a meal, see kcal in seconds, know whether you're hitting your daily target — with food the user actually eats.

## v1 Requirements

### Authentication & Account

- [ ] **AUTH-01**: User can sign up with email + password OR Google OAuth via Clerk
- [ ] **AUTH-02**: User session persists across browser refresh (Clerk httpOnly session cookie)
- [ ] **AUTH-03**: User can sign out from any page
- [ ] **AUTH-04**: User can delete their account, cascading deletion of all FitGH data (GDPR)
- [ ] **AUTH-05**: Privacy disclosure shown at sign-up; food images sent to LLM provider is named in policy
- [ ] **AUTH-06**: Clerk session JWT verified networkless by Flask on every protected request

### Profile & Targets

- [ ] **PROF-01**: User can complete a ≤3-screen onboarding capturing name, sex, height (cm), weight (kg), age, timezone, locale (Ghana / diaspora), activity level
- [ ] **PROF-02**: User can select primary goal: weight loss OR muscle gain (one only; switchable later)
- [ ] **PROF-03**: System computes BMR via Mifflin-St Jeor and TDEE via activity factor
- [ ] **PROF-04**: System computes daily kcal target (TDEE − deficit for weight loss; TDEE + surplus for muscle gain) with hard floor (1200 kcal female / 1500 kcal male) + disclaimer
- [ ] **PROF-05**: System computes daily protein target (1.6 g/kg bodyweight) for muscle-gain users
- [ ] **PROF-06**: User can edit profile fields after onboarding; targets recompute on save
- [ ] **PROF-07**: User can log a weight entry; weight history persisted

### Manual Meal Logging

- [ ] **LOG-01**: User can search the Ghana food catalogue (25 dishes v1) by name or alias (jollof, banku, waakye, etc.)
- [ ] **LOG-02**: User can log a meal manually as one OR multiple components (multi-component schema from day 1)
- [ ] **LOG-03**: User can set portion per component using a slider with culturally meaningful defaults ("1 ball of banku ≈ 200 g")
- [ ] **LOG-04**: System computes total kcal + total protein for a logged meal
- [ ] **LOG-05**: User can view today's meals as a list with running daily total
- [ ] **LOG-06**: Dashboard shows "remaining kcal" pill (target − consumed)
- [ ] **LOG-07**: User can edit or delete a logged meal
- [ ] **LOG-08**: User can view history of meals by day (last 30 days minimum)

### Food Image → Kcal (Core Loop)

- [ ] **VIS-01**: User can capture or upload a meal photo from the dashboard
- [ ] **VIS-02**: Image is compressed client-side (max 1024 px long edge, ≤0.5 MB, JPEG q=0.85) before upload
- [ ] **VIS-03**: Backend identifies each visible component on the plate (multi-component output, not single dish)
- [ ] **VIS-04**: Backend returns kcal range (low/high) per component + total with confidence band
- [ ] **VIS-05**: Backend re-matches identified component names to the `foods` catalogue and uses the table's `kcal_per_100g × portion_g_locale` to recompute (table wins over LLM kcal)
- [ ] **VIS-06**: User sees components as tap-to-edit chips with portion sliders before saving
- [ ] **VIS-07**: User can correct dish name (autocomplete over the Ghana catalogue) and portion before confirming
- [ ] **VIS-08**: Corrections are persisted to `user_corrections` and bias defaults on subsequent scans
- [ ] **VIS-09**: Per-user vision-call quota enforced (default 8/day) with clear messaging when exhausted
- [ ] **VIS-10**: Global daily LLM cost circuit breaker; users see a friendly fallback to manual entry if hit
- [ ] **VIS-11**: Meal image bytes are NOT retained server-side after the vision call (privacy + cost)
- [ ] **VIS-12**: Confirmed meal is persisted via the same multi-component schema as manual entries

### Animated Dashboard

- [ ] **DASH-01**: Dashboard shows a Rive-animated avatar whose state reflects sex, BMI band, and goal direction
- [ ] **DASH-02**: Dashboard shows an animated kcal ring (consumed vs target)
- [ ] **DASH-03**: Dashboard shows an animated weight-over-time chart (Recharts) for last 30/90 days
- [ ] **DASH-04**: Dashboard shows a weekly kcal-vs-target chart
- [ ] **DASH-05**: Dashboard adapts copy and CTA to the user's goal (e.g. "X kcal under target" for cut, "X g protein remaining" for bulk)
- [ ] **DASH-06**: Streak counter with a 1-day soft-grace mechanic (one missed day doesn't reset)
- [ ] **DASH-07**: Rive runtime + JSON are lazy-loaded; `prefers-reduced-motion` disables animations; auto-disable on slow connections (`navigator.connection.effectiveType` = `2g`/`3g`)

### Workout Library

- [ ] **WORK-01**: User can browse an exercise catalogue of 80–120 curated exercises
- [ ] **WORK-02**: User can filter by equipment (none / dumbbells / resistance bands / pull-up bar / kettlebell / barbell)
- [ ] **WORK-03**: User can filter by target muscle (chest, back, legs, shoulders, arms, core, glutes, full-body)
- [ ] **WORK-04**: Equipment filter defaults to `none` + `dumbbells` on first open
- [ ] **WORK-05**: Each exercise shows a WebP poster (≤30 KB); user taps to load the animated WebM/GIF
- [ ] **WORK-06**: Exercise detail page shows instructions, target muscle, equipment, an optional curated YouTube embed using lite-youtube-embed pattern
- [ ] **WORK-07**: All assets attributed in a `LICENSES.md` + visible footer credit (wger CC-BY-SA + Free Exercise DB Unlicense)
- [ ] **WORK-08**: Workout library is installable as a PWA and works offline (workout media cached cache-first via service worker + IndexedDB)

### Cross-Cutting / Non-Functional

- [ ] **PERF-01**: First Load JS ≤ 180 KB gzipped per route (enforced by CI bundle-size gate from Phase 1)
- [ ] **PERF-02**: Above-fold image budget ≤ 100 KB per route
- [ ] **PERF-03**: Lighthouse mobile performance ≥ 90 on simulated mid-tier Android (Moto G Power, Slow 4G)
- [ ] **PERF-04**: Real Ghana p75 TTFB measured from Lagos via WebPageTest before launch; gate launch on ≤ 2 s
- [ ] **OBS-01**: Sentry captures frontend + backend errors with user privacy (no PII, no image data, no kcal totals in error context)
- [ ] **OBS-02**: Vercel Analytics + Speed Insights track real-user perf on Vercel free tier
- [ ] **OBS-03**: Sentry alert at $/DAU/day > $0.05 on the LLM cost metric
- [ ] **SEC-01**: All secrets in `.env.local` / Fly.io secrets; `.env*` gitignored; `gitleaks` pre-commit hook in repo from Phase 1
- [ ] **SEC-02**: Exposed MongoDB password rotated before Phase 1 deploy; least-privilege Atlas DB user (no admin)
- [ ] **SEC-03**: Flask CORS configured with explicit origin allowlist (no `*` + credentials)
- [ ] **SEC-04**: Flask uses a singleton `MongoClient` with `maxPoolSize=10` to respect M0 connection limits
- [ ] **DATA-01**: Daily `mongodump` to Cloudflare R2 / similar; Atlas M0 has no native backups
- [ ] **LEGAL-01**: Privacy policy live at launch, naming LLM-vision provider as a sub-processor
- [ ] **LEGAL-02**: User can export all their data on request (account → data export endpoint)
- [ ] **LEGAL-03**: Health-claim language audit: app is "fitness tracking," not "medical advice"; copy reviewed pre-launch
- [ ] **DEPLOY-01**: Frontend deploys to Vercel from `/frontend` (App Router)
- [ ] **DEPLOY-02**: Backend deploys to Fly.io in `jnb` region with always-on `shared-cpu-1x` 512 MB + static egress IP pinned in Atlas allowlist

## v2 Requirements

### Image History & Storage

- **HIST-01**: User can opt in to retain meal photos for 90 days
- **HIST-02**: Photos stored on Cloudflare R2 via signed URLs; not on MongoDB GridFS
- **HIST-03**: User can delete any retained photo individually

### Wearables & Integrations

- **WEAR-01**: Apple Health import (kcal burned, weight)
- **WEAR-02**: Google Fit import
- **WEAR-03**: Step counter from device sensors (PWA fallback)

### Expanded Catalogue

- **CAT-01**: Ghana food table expanded from 25 → 50+ dishes, curated from real "unknown" reports
- **CAT-02**: Exercise catalogue expanded with workout plans (multi-exercise sessions, sets/reps)
- **CAT-03**: User can build and save custom workouts

### Engagement

- **ENG-01**: Push notifications for streaks / meal reminders
- **ENG-02**: Friends list + private leaderboards (NOT a public social feed)
- **ENG-03**: Multi-day meal planner

### Monetisation

- **MON-01**: Paid tier unlocks unlimited vision scans + premium workouts (Paystack for Ghana; Stripe for diaspora)
- **MON-02**: Entitlements via Clerk metadata + Flask middleware

### Localisation

- **LOC-01**: Twi UI localisation
- **LOC-02**: Ga + Ewe (post-Twi)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Social feed (public posts, likes, comments) | Not the wedge; engagement-trap; community-moderation cost; not why users come |
| Scraping Pinterest / Instagram / deluxesupps for workout videos | Breaches ToS + creator copyright; legal blocker; not negotiable |
| Self-trained food-vision model | Too costly for v1; LLM vision + Ghana table is faster + evolves with model updates; revisit only if accuracy / cost demands it |
| Native mobile apps (iOS / Android) | PWA covers v1; native is post-MVP if engagement justifies it |
| Barcode scanner | Ghana foods aren't packaged like Western foods; not the wedge |
| Recipe builder | Too complex for v1; cookbook content out of scope |
| Water / sleep / mood / period tracking | Scope creep; not core to the kcal loop |
| Coach / 1-on-1 expert chat | Not in scope; not the wedge |
| Workout timers / rep counters / structured sessions | Library v1 is browsable reference; structured sessions are v2 |
| Push notifications (v1) | PWA support inconsistent on iOS; defer to v2 with native fallback |
| Multi-user accounts (family plans) | Not the wedge |
| Restaurant menus | Out of v1 scope; users log what they eat |
| Micronutrient tracking (vitamins / minerals) | Macros only in v1 |
| Twi / Ga / Ewe localisation (v1) | English suffices for v1; localisation deferred to v2 once retention is proven |
| Payments / subscriptions / freemium gating | Free at v1; monetise only after PMF signal |
| Storing meal images by default | Privacy + Atlas free-tier storage; opt-in retention is a v2 feature |

## Traceability

Empty — populated by the roadmapper in the next step.

| Requirement | Phase | Status |
|-------------|-------|--------|
| _to be filled by ROADMAP.md_ | | |

**Coverage:**
- v1 requirements: 60 total
- Mapped to phases: 0 (roadmapper will fill)
- Unmapped: 60 ⚠️ (expected until roadmap runs)

---
*Requirements defined: 2026-05-11*
*Last updated: 2026-05-11 after initial definition*
