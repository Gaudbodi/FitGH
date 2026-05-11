# RESEARCH SUMMARY — FitGH

**Project:** Responsive PWA fitness tracker for Ghanaians (in-Ghana + diaspora).
**Wedge:** *Snap a meal, see kcal in seconds, calibrated to food the user actually eats* (jollof, banku, waakye, fufu, kelewele, kontomire, red red, kenkey, tilapia…).
**Synthesised:** 2026-05-11 from STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md.

This document is the single load-bearing read for the roadmapper. Full detail lives in the four source files.

---

## Locked Stack Decisions

| Concern | Pick | Version pin | Phase first used |
|---------|------|-------------|------------------|
| Frontend framework | Next.js 15 (App Router) + React 19 + TypeScript | `next@15.2.4`, `react@19.x`, `typescript@5.5+` | Phase 1 |
| CSS | Tailwind v4 + `@tailwindcss/postcss` | `tailwindcss@4.0.x` | Phase 1 |
| Component library | shadcn/ui (Radix-based, copy-paste) | CLI v4 (Mar 2026) | Phase 1 |
| Forms + validation | React Hook Form + Zod + `@hookform/resolvers` | `react-hook-form@7.60.x`, `zod@3.25.x` | Phase 2 |
| Charts | Recharts v3 (via shadcn/ui charts) | `recharts@3.x` | Phase 5 |
| Animation runtime | **Rive** (`@rive-app/react-canvas`) | `^4.x` | Scaffolded Phase 1, real `.riv` Phase 5 |
| Image compression (client) | `browser-image-compression` | `^2.0.x` | Phase 4 |
| Auth | **Clerk** (`@clerk/nextjs` on FE, `clerk-backend-api` on BE) | latest 5.x | Phase 2 |
| Backend framework | Flask 3.1.3 + Gunicorn 25.1.x + Python 3.12 | pinned | Phase 3 |
| Backend schema validation | Pydantic v2 | `^2.9.x` | Phase 3 |
| MongoDB driver | PyMongo (no ODM) — Flask only | `pymongo@4.13+` | Phase 3 |
| Vision provider | **Claude Sonnet 4.6** via `anthropic` Python SDK | `claude-sonnet-4-6` | Phase 4 |
| DB | MongoDB Atlas M0 (existing `cluster0.pcd3g.mongodb.net`) | free tier | Phase 1 |
| Frontend host | Vercel Hobby | — | Phase 1 |
| Backend host | **Fly.io**, `primary_region = "jnb"`, always-on `shared-cpu-1x` 512 MB + static egress IP | ~$3–5/mo + IP add-on | Phase 3 |
| Image storage | **None in v1** — compress client-side, POST to Flask, discard after vision call | — | Phase 4 |
| CORS | `flask-cors` with explicit origin list (no `*` + credentials) | `^5.0.x` | Phase 3 |
| Observability | Sentry free tier (FE + BE) + Vercel Analytics + Vercel Speed Insights | Sentry `^9.x` FE / `^2.x` BE | Phase 1 (FE), Phase 3 (BE) |
| Package manager | pnpm (workspace root) | — | Phase 1 |

**Rejected (do not reopen):** Next.js 16, Vite, Tailwind v3, MUI/Chakra, NextAuth v5, Better Auth, Supabase Auth, hand-rolled JWT, MongoEngine/uMongo/Beanie, GPT-4o (v1), Claude Opus 4.7 (v1), Render free dyno, Railway, Cloudinary/UploadThing (v1), MongoDB GridFS for images, `mongodb` driver in Next.js.

---

## Architecture Skeleton

### Repo layout — single monorepo, three top-level directories

```
fitgh/
├── frontend/            # Next.js 15 App Router (TS, Tailwind v4, shadcn/ui)
│   ├── app/             # routes
│   ├── components/
│   ├── lib/             # API client, Clerk helpers, types
│   └── package.json
├── backend/             # Flask API service
│   ├── app/
│   │   ├── routes/      # /vision, /meals, /users, /weights, /exercises, /health
│   │   ├── services/    # vision_client, ghana_food_table, tdee, rate_limit
│   │   ├── models/      # Pydantic v2 schemas
│   │   └── db.py        # one MongoClient, module-level singleton
│   ├── scripts/         # seed.py, mongodump cron helpers
│   ├── tests/
│   └── requirements.txt
├── shared/
│   ├── schemas/         # JSON Schema for User, Meal, Food, Exercise
│   ├── ghana-food-table.json   # source of truth (25 entries v1)
│   └── exercise-seed/   # Free Exercise DB curated JSON
├── .planning/
├── .env.example
└── README.md
```

**Why monorepo:** shared schema between Next.js (Zod) and Flask (Pydantic) generated from `shared/schemas/`; single source of truth for the Ghana food table; deploys remain independent (Vercel from `/frontend`, Fly.io from `/backend`).

### Component boundaries

**Next.js owns:** all rendering (SSR + client components), Clerk auth UI + session cookie, user-facing routing, BFF layer in `app/api/*` (thin: verify Clerk session → forward JWT to Flask), Rive runtime, Recharts client components, PWA shell + service worker + IndexedDB cache, client-side image compression.

**Flask owns:** **100% of MongoDB access** (no Mongo driver in Next.js), LLM vision integration (only place the Anthropic API key lives), kcal estimation pipeline (system prompt assembly, Sonnet 4.6 call, response parsing, Ghana-table re-match, multi-component sum), TDEE/target math (Mifflin-St Jeor + activity factor + goal delta), all writes to `meals`/`weights`/`users.profile_targets`, per-user daily vision rate limit, global $/day circuit breaker, reads of `foods` + `exercises` in write workflows.

**Flask does NOT own:** rendering, session cookies, OAuth dance (Clerk handles all of it).

### Auth flow — Clerk + Flask verify

```
1. User signs up / signs in via <SignUp/> or <SignIn/> on Next.js (Clerk-hosted UI).
2. Clerk issues a session JWT, stored in `__session` httpOnly cookie.
3. Next.js Route Handler (BFF) reads JWT and forwards to Flask in
   `Authorization: Bearer <jwt>`.
4. Flask middleware calls
   `clerk.authenticate_request(request, AuthenticateRequestOptions(authorized_parties=["https://fitgh.vercel.app"]))`
   — networkless JWT verification against Clerk's public key (no per-request API call).
5. Flask uses `auth_state.payload.sub` as the Clerk user_id; joins to `users` collection
   on `users.clerk_id`.
6. 401 on any verification failure. No route handler reads identity from arbitrary headers.
```

**Why Clerk over NextAuth (resolution of researcher disagreement):** 50k MAU free covers any plausible v1 ceiling; solo build cannot afford to hand-roll 2FA / passkeys / OAuth dance / password reset flows; networkless JWT verification keeps Flask stateless; revisit only if monetisation forces self-hosted later.

### MongoDB collections (names + key fields)

All collections carry `created_at`, `updated_at`, and (where user-scoped) `user_id: ObjectId`. Timestamps UTC; `local_date` (`YYYY-MM-DD`) denormalised at write time using `users.profile.timezone`. ESR rule for compound indexes.

| Collection | Key fields | Primary indexes |
|------------|------------|-----------------|
| `users` | `clerk_id` (unique), `email`, `profile {name, sex, height_cm, age, timezone, locale, activity_level}`, `goal {type, target_weight_kg, weekly_rate_kg}`, `targets {bmr_kcal, tdee_kcal, daily_kcal_target, daily_protein_g, computed_at}` (derived), `preferences {retain_meal_images: false, units}`, `usage {vision_calls_today, vision_calls_reset_at}` | `{clerk_id:1}` unique, `{email:1}` unique |
| `meals` | `user_id`, `components: [{name, matched_food_id, portion_g, kcal, macros, confidence, source:"ai"\|"user"}]` (**multi-component schema — pitfall G-4**), `total_kcal`, `total_protein_g`, `source: "ai_estimate"\|"user_corrected"\|"manual"`, `ai_metadata {model, prompt_version, confidence}`, `consumed_at`, `local_date`, `meal_type` | `{user_id:1, local_date:-1}` (daily totals), `{user_id:1, consumed_at:-1}` (history) |
| `foods` | `name`, `aliases[]`, `category`, `origin`, `kcal_per_100g`, `typical_portion_g_ghana`, `typical_portion_g_diaspora`, `macros_per_100g`, `source`, `source_confidence` | `{name:1}`, multikey `{aliases:1}`, text `{name, aliases}` |
| `weights` | `user_id`, `weight_kg`, `recorded_at`, `local_date`, `source:"manual"`, `note?` | `{user_id:1, recorded_at:-1}` |
| `exercises` | `external_id`, `name`, `target_muscle`, `secondary_muscles[]`, `equipment`, `difficulty`, `movement_pattern`, `media {gif_url, thumbnail_url, webm_url?, youtube_id?, bytes}`, `instructions[]`, `source`, `license`, `attribution` | `{equipment:1, target_muscle:1}`, text `{name, aliases}` |
| `user_corrections` | `user_id`, `original_dish`, `corrected_dish`, `correction_count` | `{user_id:1, original_dish:1}` |
| `workouts` (optional v1) | `name`, `goal`, `equipment_required[]`, `blocks[]` | `{goal:1, equipment_required:1}` |

**Deferred:** `workout_logs`, `notifications`. `ghana_kcal_table` lives as static JSON in `shared/` v1; promoted to a collection only when admin UI or D-8 cross-user aggregation lands.

**Atlas IP allowlist (resolved):** Fly.io static egress IP (~$2–3/mo add-on) pinned in Atlas allowlist. `0.0.0.0/0` only in local dev with strong DB password + TLS only.

### Kcal loop data flow (the wedge)

```
User snaps photo
  └─▶ Next.js client: browser-image-compression
        (maxSizeMB=0.5, maxWidthOrHeight=1024, useWebWorker, JPEG q=0.85)
  └─▶ POST /api/meals/estimate (multipart) to Next.js BFF
  └─▶ BFF verifies Clerk session → forwards JWT → POST {FLASK}/vision/estimate
  └─▶ Flask /vision/estimate:
        a. Clerk JWT verify (networkless)
        b. Rate limit: users.usage.vision_calls_today < 8/day
        c. Global $/day circuit breaker (MAX_DAILY_VISION_SPEND_USD)
        d. Build prompt: cached system (base instructions + 25-dish Ghana table
           + components schema) + user image
        e. Sonnet 4.6 with temperature=0, max_tokens=400, tool_use JSON schema:
             { components: [{name, portion_g, kcal_low, kcal_high, kcal_point,
                             confidence, visible: bool}], assumed_components: [] }
        f. Re-match each component name → foods text-index → recompute
           kcal from foods.kcal_per_100g × portion_g (table wins)
        g. Increment users.usage.vision_calls_today
        h. Discard image bytes (no R2, no GridFS in v1)
  └─▶ 200 { components, total_kcal_low, total_kcal_high, confidence,
            daily_total_so_far }
  └─▶ Review screen: components as chips (tap to remove / edit portion),
        kcal range not point, "Looks right?" → confirm
  └─▶ POST /api/meals (confirmed or corrected) → Flask /meals → insert with
        local_date from timezone; if corrected, upsert user_corrections
  └─▶ Dashboard animates kcal ring + Rive avatar + remaining-kcal pill
```

**Image transport:** v1 bytes-through-Flask on always-on Fly.io machine. Migrate to signed-URL → R2 only when meal-image history opt-in lands (Phase 8+).

### Walking Skeleton scope (Phase 1, 1–3 days)

Single user story: *"I can sign in with Clerk, see `/dashboard` that fetches my profile from Flask, which reads it from Atlas."*

Includes:
1. Monorepo scaffold; `.env.example` checked in; `.env` / `.env.local` gitignored; `gitleaks` pre-commit hook installed.
2. Next.js 15 + Tailwind v4 + shadcn/ui init + Clerk `<SignIn/>`/`<SignUp/>`.
3. Flask 3.1.3 + Gunicorn + `clerk-backend-api` middleware (`@require_auth`).
4. MongoDB Atlas connected from Flask only (module-level `MongoClient` singleton, `maxPoolSize=10`); seed one `users` doc.
5. `/health` returning `{ok:true, mongo:"connected"}`.
6. `GET /api/me` BFF → forwards Clerk JWT → Flask `GET /me` → returns `{email, profile.name}`.
7. Vercel deploy `/frontend`; Fly.io deploy `/backend` to `jnb`; all platform secrets set.
8. Static egress IP on Fly.io pinned in Atlas allowlist.

**Explicitly NOT in the skeleton:** Ghana food table, LLM vision, Rive avatar, charts, PWA service worker, onboarding form, kcal target math.

---

## Feature Priorities

### Table stakes (v1 must-have)

| ID | Feature | Complexity | Phase |
|----|---------|------------|-------|
| TS-1 | Account + profile (Clerk-backed) | S | 2 |
| TS-2 | Daily kcal target (Mifflin-St Jeor) | S | 2 |
| TS-3 | Daily protein target (muscle_gain only) | S | 2 |
| TS-4 | Daily intake log + remaining pill | M | 3 |
| TS-5 | Weight log + history | S | 2 |
| TS-6 | History view | S | 3 |
| TS-7 | Animated progress chart (Recharts) | M | 5 |
| TS-8 | Weekly streak with 1-day soft grace | S | 5 |
| TS-9 | Exercise library (80–120 curated) | M | 6 |
| TS-10 | Search + equipment filter | S | 6 |
| TS-11 | Mobile-first responsive UI | M | 1, continuous |
| TS-12 | Food image → kcal (CORE LOOP) | L | 4 |
| TS-13 | Correct dish + portion inline | M | 4 |
| TS-14 | Manual meal entry | S | 3 |
| TS-15 | Privacy disclosure + policy link | S | 2, pre-launch |

### Differentiators (the wedge)

| ID | Differentiator | Phase |
|----|----------------|-------|
| D-1 | Curated 25-dish Ghana food kcal table (expanded post-launch from "unknown" reports) | 0 → 3 |
| D-2 | Sonnet 4.6 vision calibrated against Ghana table via cached system prompt | 4 |
| D-3 | Rive state-machine avatar (sex × BMI band × goal direction) | 5 |
| D-4 | Equipment filter default `none` + `dumbbells` | 6 |
| D-5 | Data-light delivery (PWA, ≤180 KB First Load JS gzipped, Lighthouse ≥90 on mid-tier Android) | continuous from 1 |
| D-6 | Diaspora-aware portion phrasing ("1 ball of banku (~200 g)") | 3 + 4 |
| D-7 | Goal-aware home screen | 5 |
| D-8 | Per-user correction feedback loop | 4 |

### Anti-features (v1 explicit no's)

Social feed, wearables, payments, native apps, Pinterest/IG scraping, self-trained vision model, barcode scanner, recipe builder, water/sleep/mood/period tracking, coach features, workout video player with timers, push notifications, multi-user accounts, restaurant menus, micronutrient tracking, Twi/Ga/Ewe localisation. (Full mapping in FEATURES.md AF-1 to AF-16.)

### Ghana food v1 cut (25 dishes named)

**Resolution: 25 for v1**, not the 50 in FEATURES.md. Pareto: covers ~80% of daily Accra eating; remainder curated post-launch from real "unknown" reports.

Locked list for `shared/ghana-food-table.json` v1:

1. Jollof rice (plain)
2. Jollof rice with chicken
3. Waakye (plain)
4. Waakye full (gari + egg + fish)
5. Banku (1 ball)
6. Kenkey (Ga, 1 ball)
7. Fufu (1 serving)
8. Plain rice (white, 1 cup cooked)
9. Tuo zaafi (1 ball)
10. Omo tuo (rice balls)
11. Palm nut soup (abenkwan)
12. Groundnut soup (with chicken)
13. Light soup (fish or meat)
14. Kontomire stew (palaver sauce)
15. Red red (bean stew + plantain)
16. Grilled tilapia (1 whole medium)
17. Fried tilapia (1 whole medium)
18. Chicken stew piece
19. Kelewele (spicy fried plantain)
20. Fried plantain (kaakro / tatale)
21. Boiled plantain
22. Yam (boiled)
23. Yam chips (fried)
24. Koko (Hausa millet porridge) + koose (bean cake)
25. Shito (pepper sauce, condiment)

Each entry stores: `{id, name, aliases[], region, meal_type, portion_description, kcal_per_100g, typical_portion_g_ghana, typical_portion_g_diaspora, kcal_low, kcal_high, kcal_default, protein_g, source_url, source_confidence}`. Source priority: FAO/INFOODS West Africa 2019 → PMC4864731 → recipe panels → USDA proxy for cross-cultural ingredients.

### Workout asset sources (decision)

**Primary: Free Exercise DB (yuhonas) — Unlicense (public domain).** ~800 exercises, JPG (smaller than GIFs), local JSON.
**Fallback: wger (CC-BY-SA 3.0)** for breadth gaps. Attribution required in footer.
**Reject for v1:** ExerciseDB, MuscleWiki (non-commercial-only), exrx.net, GIPHY.

**v1 catalogue size:** 80–120 curated (8 muscle groups × ~12 exercises; biased toward bodyweight + dumbbells).
**Media:** WebP poster ~30 KB → tap-to-load WebM. YouTube via lite-youtube-embed pattern (~3 KB placeholder, not 600 KB iframe). Footer: "Exercise data from wger.de (CC-BY-SA 4.0) and Free Exercise DB (Unlicense)." `LICENSES.md` in repo root.

---

## Top 5 Pitfalls + Mitigations

| # | Pitfall | Mitigation (what the phase must build in) | Phase |
|---|---------|-------------------------------------------|-------|
| 1 | **G-4. Multi-dish plate schema** — single-`dish_name` field misses 40–60% of meal energy on the typical Ghanaian plate. | Ship `meals.components: [{name, portion_g, kcal_low, kcal_high, kcal_point, confidence, visible}]` from day 1; LLM prompt asks for *each visible component separately*; UI shows chips the user can tap-to-remove (recomputes total). | 3 (schema), 4 (UI) |
| 2 | **V-3. LLM cost balloon** — 1000 DAU × 3 meals × $0.014 = ~$42/day unmonetised. | (a) Anthropic prompt caching for system + 25-dish table (~90% input-cost cut); (b) client resize to 1024 px long edge; (c) `max_tokens: 400`; (d) per-user 8 calls/day cap tracked in `users.usage`; (e) global `MAX_DAILY_VISION_SPEND_USD` circuit breaker → 503 + banner; (f) Sentry alert at $/DAU/day > $0.05. | 4 |
| 3 | **M-3. Don't store meal images anywhere by default** — GridFS burns 512 MB M0 in week 1; violates privacy stance. | v1: send to Sonnet → store only `(components, total_kcal, timestamp, user_id)` → discard bytes. Opt-in image history deferred to Phase 8+ on Cloudflare R2. | 4 |
| 4 | **G-2. Ghana food table built on Western databases** — USDA "jollof 220 kcal/cup" is wrong-direction (real meals 700–900 kcal). | Build 25-dish table from FAO/INFOODS West Africa 2019 + PMC4864731, not MyFitnessPal. Each entry: `typical_portion_g_ghana` AND `typical_portion_g_diaspora`; LLM prompt biases by `users.profile.locale`. | 0 (data prep), before 4 |
| 5 | **V-7. No user-correction loop → trust collapses in 5 days** — users tolerate ~30% error if they can correct in one tap. | Inline correction (kcal editable in place, dish editable via Ghana-table autocomplete, portion as horizontal slider); store every correction in `user_corrections`; on next photo bias defaults from prior corrections. **Non-negotiable for v1.** | 4 |

**Honorable mentions:** M-5 (gitleaks, rotate exposed Mongo password, least-privilege DB user), S-2 (LLM image consent + named-processor privacy policy), D-1 (`size-limit` CI gate from Phase 1), D-3 (WebP+WebM workout media), L-2 (`LICENSES.md` + footer attribution before workouts ship), L-3 (privacy policy + delete-account flow before launch).

---

## Suggested Build Order (Phase Skeleton)

**Invariants:** Walking Skeleton precedes everything (every later phase depends on the trust boundary); food loop ships *before* workouts (PROJECT.md core value sentence is food, not workouts; PITFALLS B-6).

| # | Phase | What it delivers | Features | Pitfalls enforced |
|---|-------|------------------|----------|-------------------|
| 0 | **Data prep (parallel with Phase 1)** | `shared/ghana-food-table.json` (25 entries, FAO/INFOODS), `shared/schemas/*`, `shared/exercise-seed/*` (curated to 80–120) | D-1 catalogue, workout source | G-2, B-1, L-2 (LICENSES.md draft) |
| 1 | **Walking Skeleton** | Monorepo + Clerk + Flask + Atlas + Fly.io `jnb` + Vercel + Sentry + Vercel Analytics + bundle-size CI gate + gitleaks + static egress IP | (none user-facing) | M-1, M-5, D-1, S-1 |
| 2 | **Onboarding + profile + targets** | Clerk sign-up, 3-screen onboarding, Flask `/users/me` PATCH → Mifflin-St Jeor, `weights` collection, dashboard skeleton with target | TS-1, TS-2, TS-3, TS-5, TS-15 | U-1 (≤3 screens, ≤60 s), L-4 (1200/1500 kcal floor + disclaimer), S-2 |
| 3 | **Manual meal log + Ghana table seeded** | Seed `foods`, `/foods/search`, manual meal UI, **multi-component `meals` schema from day 1**, daily-total endpoint, kcal pill | TS-4, TS-6, TS-14, D-6 | **G-4** (components schema), G-2, M-2 (singleton MongoClient) |
| 4 | **The kcal loop (CORE WEDGE)** | `browser-image-compression`, multipart POST, Sonnet 4.6 with cached system + 25-dish table + components schema (temp=0, max_tokens=400, tool_use), Ghana-table re-match, components-as-chips review, inline correction → `user_corrections`, per-user cap, global $/day breaker, image discarded | TS-12, TS-13, D-2, D-6, D-8 | V-1 to V-7, G-1, G-4, M-3, S-2, S-3, S-4, L-3 |
| 5 | **Animated dashboard** | Rive `.riv` avatar with state-machine inputs, Recharts via shadcn/ui charts, goal-aware home, soft-streak with 1-day grace | TS-7, TS-8, D-3, D-7 | D-2 (Rive lazy via fetch + SW; `prefers-reduced-motion`; auto-disable on slow connection via `navigator.connection.effectiveType`), U-5, B-5, V-4 (model pin + golden set) |
| 6 | **Workout library** | Seed `exercises`, `/exercises/search` with filters, library UI defaulting to `none` + `dumbbells`, `next-pwa` + IndexedDB offline | TS-9, TS-10, D-4, D-5 | D-3 (WebP poster + tap-to-load WebM), D-4 (SW + IDB), L-1, L-2, U-3 ("Today's workout" 5–8, not flat list) |
| 7 | **Data-light pass + launch hardening** | Lighthouse audit via Lagos WebPageTest, per-route page-weight verification, font subsetting, image audit, real privacy policy live, delete-account + data-export endpoints, health-claim language audit, Anthropic spend alerts, golden-set re-run | D-5 | D-1, D-5, L-3, L-4, B-4 |
| 8 (deferred) | **Optional: opt-in meal-image history** | Cloudflare R2, signed-URL upload, 90-day TTL, settings toggle | (post-MVP) | M-3 (no v1 storage) |

**Research flags for the roadmapper:**
- **Needs `/gsd-research-phase`:** Phase 4 (prompt engineering + golden-set construction is novel), Phase 5 (Rive state-machine design + designer availability), Phase 7 (real Ghana p75 latency unverified).
- **Standard patterns, skip deeper research:** Phase 1, 2, 3, 6.

**Parallelisation:** Phase 0 begins during Phase 1. After 1, TDEE service (Flask) ⟂ Onboarding form (Next.js). After 3, exercise seeding (Phase 6 prep) can run partial-parallel with Phase 4. **Hard sequence:** 1 → 2 → 3 → 4 → 5 → 6 → 7. Phase 6 is *not* allowed to start before Phase 4 ships to seed cohort.

---

## Cross-Cutting Resolved Decisions

| # | Question | Researchers' positions | **Resolution** |
|---|----------|------------------------|----------------|
| 1 | Backend host | ARCHITECTURE: Render. STACK: Fly.io JNB. PITFALLS: Render cold start fatal. | **Fly.io, `primary_region = "jnb"`, always-on `shared-cpu-1x` 512 MB, static egress IP add-on.** Closer to Ghana (~80–150 ms vs Render us-east ~190 ms), no cold start, Docker control, pairs with Atlas allowlist via static IP. ~$5–8/mo. Re-evaluate region (`lhr`) post-launch. |
| 2 | Animation runtime | ARCHITECTURE: silent. FEATURES: Rive. STACK: Rive. | **Rive.** State-machine is the differentiator; `.riv` 50–80% smaller than Lottie JSON; canvas runtime ~50 KB vs Lottie ~150 KB. Lazy-loaded via `next/dynamic`, JSON fetched not imported, `prefers-reduced-motion` honoured. **Open: designer pipeline** — contract a Rive artist (~£200–500) OR ship static SVG in v1, animate v1.1. Decide before Phase 5. |
| 3 | Vision provider | STACK: Sonnet 4.6. FEATURES: defers (abstract behind interface). PITFALLS: defers, focuses on mitigations. | **Claude Sonnet 4.6 for v1.** Best context-injected-table adherence (Ghana table IS the differentiator). ~$0.004/image with prompt caching. **Phase-4 spike budgeted:** comparison run vs GPT-4o on 30-photo golden set; if GPT-4o MAPE within 5% and cost lower, abstract behind `VisionProvider` interface and swap. Pin model in env (`LLM_VISION_MODEL=claude-sonnet-4-6`); golden-set re-run on any version bump (V-4). |
| 4 | Auth | ARCHITECTURE: NextAuth v5 + PyJWT. STACK: Clerk + `clerk-backend-api`. | **Clerk.** 50k MAU free, pre-built UI with Google + Apple + email OTP, networkless JWT verify on Flask, no hand-rolled cookie/CSRF/refresh-token work. Revisit only if monetisation forces self-hosted. The architecture flow in ARCHITECTURE.md holds — substitute Clerk for NextAuth in steps 1–3. |
| 5 | Image storage v1 | All four converge: no cloud blob in v1. | **Locked: client-side compress → multipart POST to Flask → temp memory buffer → Anthropic API → discard.** No R2, no GridFS, no Cloudinary in v1. Persist only `(components, total_kcal, timestamp, user_id)`. Opt-in history on Cloudflare R2 deferred to Phase 8+. Matches PROJECT.md privacy stance. |
| 6 | Ghana food table size | FEATURES: 50. PITFALLS: cap at 25 for v1. | **25 for v1.** Covers ~80% of daily Accra eating; remaining 25 curated post-launch from real "unknown" reports (B-1: don't perfect before shipping). 25-dish list locked above. |

---

## Risks Roadmapper Must Surface

| Risk | First phase | What to do |
|------|-------------|------------|
| **Ghana edge latency unknown** | 1 → 7 | Smoke-test from Lagos node on WebPageTest after Phase 1 deploy. If p75 TTFB > 2 s, evaluate Cloudflare in front of Vercel in Phase 7. |
| **Rive designer pipeline** | 1 → 5 | Decide by end of Phase 2: contract Rive artist, ship static SVG and animate v1.1, or re-scope to 2D morph. Don't enter Phase 5 unresolved. |
| **Vision cost ceiling** | 4 | Sentry alert at $/DAU/day > $0.05 *and* absolute monthly cap on Anthropic console. Re-evaluate model at 100 DAU (V-3, V-4). |
| **MongoDB Atlas free-tier limits** (512 MB, 500 connections, no backups) | all; bites earliest if anyone stores images | Single MongoClient (M-2), no image storage (M-3), nightly `mongodump` → R2 (M-4). Migrate to M10 ($57/mo) before 500 DAU. |
| **Multi-component plate schema** | 3 | Get `meals.components: []` right at Phase 3; refactor cost grows exponentially after Phase 4. Single-`dish_name` shortcut = launch blocker. |
| **Model version drift** (V-4) | 4 onward | Pin `LLM_VISION_MODEL`; maintain frozen 30-photo golden set; require <15% MAPE drift on any model bump; announce in-app. |
| **Free-tier viability under load** | 7 → launch | Cloud cost projection at 100 / 1000 / 10 000 DAU built into Phase 7; paid-migration triggers documented. |

---

## Open Questions Deferred to Phase Research

1. **Rive designer pipeline / avatar visual style** — *Phase 5 spike.* 10 visual states (5 BMI bands × 2 sexes). Decide before Phase 5 starts.
2. **PWA implementation** — *Phase 6 spike.* `next-pwa` vs `@ducanh2912/next-pwa` vs hand-rolled Workbox. Caching strategies: cache-first exercise media, stale-while-revalidate workout library, network-first dashboard.
3. **Workout asset hosting** — *Phase 6 decision.* Vercel static CDN vs Cloudflare R2 (free egress). Likely R2 if total > Vercel free bandwidth.
4. **Vision provider golden-set comparison** — *Phase 4 spike.* Build 30-photo golden Ghana meal set; run Sonnet 4.6 vs GPT-4o; abstract behind `VisionProvider` interface for swappability.
5. **Ghana table — JSON vs Mongo collection promotion threshold** — *Phase 3 decision.* Static JSON v1; promote to `foods` Mongo collection when admin UI lands or D-8 cross-user aggregation ships.
6. **Static egress IP cost on Fly.io 2026** — *Phase 1 verify.* If > $5/mo, fall back to `0.0.0.0/0` + strong DB password in dev temporarily.
7. **PWA install prompt timing** — *Phase 6 decision.* Recommended: prompt after ≥3 meals logged.
8. **Image-budget exact CI thresholds** — *Phase 1 set.* Recommended: First Load JS ≤ 180 KB gzipped, above-fold images ≤ 100 KB, total above-fold ≤ 500 KB, Lighthouse perf ≥ 90 on simulated mid-tier Android.
9. **Streak grace mechanic** — *Phase 5 decision.* Recommended: 1-day soft pause-before-reset.
10. **Clerk webhooks for user-deletion / GDPR cascade** — *Phase 2 decision.* Cascade-delete Mongo records on Clerk account deletion via webhook.

---

## Confidence Assessment

| Area | Confidence | Why |
|------|------------|-----|
| Stack | **HIGH** | All picks have authoritative sources. Cost estimates MEDIUM (Sonnet pricing verified; DAU-level extrapolation depends on user behaviour). |
| Architecture | **HIGH** | Patterns well-trod (Clerk JWT-forwarding works identically to the NextAuth flow described; PyMongo singleton documented; multi-component meal schema informed by wedge analysis). |
| Features | **MEDIUM-HIGH** | Table stakes + anti-features HIGH. Ghana kcal numbers MEDIUM (FAO/INFOODS bands, not per-household — bands not point estimates). |
| Pitfalls | **HIGH** | Top 5 backed by peer-reviewed (MDPI portion-error study) or official docs (Atlas free-tier, Anthropic pricing). Mitigations concrete and phase-mapped. |
| **Overall** | **HIGH** | Largest residual uncertainty: Phase 4 prompt-engineering accuracy on real Ghana meals — explicitly de-risked by isolating the loop to its own phase with a golden-set release gate (<25% MAPE). |
