# ARCHITECTURE

**Project:** FitGH — responsive fitness webapp for Ghanaians (Ghana + diaspora)
**Stack (fixed):** Next.js (App Router, TS) + Flask (Python) + MongoDB Atlas + LLM vision
**Researched:** 2026-05-11
**Overall confidence:** HIGH (Next.js / Flask / MongoDB patterns are well-established; LLM-vision-as-kcal-engine is the novel piece and the largest risk)

---

## Repo Layout

**Recommendation: single monorepo with three top-level directories.**

```
fitgh/
├── frontend/            # Next.js 15 (App Router, TS, Tailwind)
│   ├── app/
│   ├── components/
│   ├── lib/             # API client, auth helpers, types
│   └── package.json
├── backend/             # Flask API service
│   ├── app/
│   │   ├── routes/      # /vision, /meals, /users, /health
│   │   ├── services/    # vision_client, ghana_food_table, tdee
│   │   ├── models/      # pydantic / dataclasses
│   │   └── db.py        # pymongo client
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
├── shared/              # Cross-runtime artefacts
│   ├── schemas/         # JSON Schema for User, Meal, Food, etc.
│   ├── ghana-food-table.json   # source of truth for kcal calibration
│   └── exercise-seed/   # exported wger/ExerciseDB JSON for `exercises` collection
├── .planning/
├── .env.example
├── README.md
└── package.json         # workspace root (pnpm/npm workspaces) — only if frontend tooling needs it
```

**Why monorepo, not two repos:**

1. **Shared contract.** The `User`, `Meal`, and `Food` shapes are referenced by both runtimes. Living in `shared/schemas/` keeps them in lockstep — change a field, both sides break together at PR time (fail-fast), not in production.
2. **Single source of truth for the Ghana food table.** Backend loads it for LLM context; frontend may need it for autocomplete on manual entry. One file, one git history.
3. **Solo build, free tiers.** No team coordination cost. Two repos would force you to keep schema versions in sync across PRs in two histories — overhead with zero upside.
4. **Deployment independence is preserved.** Vercel deploys from `/frontend`, Render/Fly deploys from `/backend`. Both platforms support a subdirectory root — no coupling at the deploy layer.
5. **Cross-cutting tooling.** A single `.env.example`, a single roadmap, a single CI config. Two repos triples your config files.

**When to split:** If the backend ever grows a second consumer (mobile app, public API) with a different release cadence. Not now.

---

## Component Boundaries

### Next.js shell owns

- **All rendering** — App Router server components for SSR, client components for interactivity (forms, charts, animations).
- **Auth UI and session.** Sign-up, sign-in, "forgot password" flows. Holds the session cookie.
- **User-facing routing.** `/onboarding`, `/dashboard`, `/log`, `/workouts/[id]`, etc.
- **BFF (Backend-For-Frontend) layer via Route Handlers** in `app/api/*`. These are thin: validate session, attach a JWT, forward to Flask, shape the response for the UI. Never bypass Flask for kcal-relevant data.
- **Animations** — Lottie/Rive runtime; the canvas/SVG layer for charts.
- **PWA shell** — service worker, manifest, offline fallback, IndexedDB cache for the workout library.
- **Image compression** (client-side, see Data Flow). Before anything leaves the device.

### Flask owns

- **LLM vision integration** — only place an LLM API key is ever held. Single trust boundary for the most expensive external call.
- **Kcal estimation pipeline** — assembles the system prompt (with Ghana food table inlined), calls the vision model, parses the structured response, applies portion calibration, returns `{dish, kcal, protein_g, confidence, source}`.
- **All writes that touch `meals`, `weights`, `users.profile_targets`.** Mutations that affect the user's tracking record go through Flask so business logic (TDEE recompute, daily-cap enforcement, rate limiting) is centralised.
- **TDEE / target derivation** — Mifflin-St Jeor + activity factor + goal delta. One function, one test suite, never duplicated in JS.
- **Rate limiting** on `/vision/estimate` (per-user daily cap to cap LLM spend).
- **Reads of `foods` and `exercises`** when those reads are part of a write workflow. Pure browse-the-workout-library reads can be cached/proxied through the Next.js BFF without Flask in the hot path (see Walking Skeleton notes).

### What Flask does NOT own

- **Rendering.** No Jinja, no server-rendered HTML. Pure JSON API.
- **Session cookies.** Flask is stateless; it verifies a JWT on every request.
- **OAuth dance.** If/when we add Google sign-in, NextAuth handles it; Flask only sees the issued JWT.

### Does Next.js talk to MongoDB directly?

**No. All persistence goes through Flask.** Rationale:

1. **One place to enforce the per-user daily LLM cap.** If Next.js could insert into `meals` directly, an attacker could bypass Flask's rate limiter.
2. **TDEE/target logic lives in one runtime.** Python has the kcal math; we don't reimplement it in TypeScript.
3. **Connection-pool sanity.** Vercel's serverless invocations spawn fresh MongoDB connections; the Atlas free tier has connection limits (500). Routing through a long-lived Flask process keeps connection counts predictable.
4. **Audit trail.** Every mutation has a single chokepoint we can log.

**One narrow exception is acceptable: NextAuth's adapter for the `users` auth-record table** (sessions/accounts collections used by Auth.js itself). NextAuth's MongoDB adapter is well-tested and isolated to auth-only collections. The *application* `users` collection (profile, targets, goals) is still Flask-owned.

---

## Auth Flow

**Pattern: NextAuth.js (Auth.js v5) on Next.js issues a JWT session; Flask verifies the JWT using a shared HS256 secret on every request.**

Concrete libraries:

| Side | Library | Role |
|------|---------|------|
| Next.js | `next-auth@5` (Auth.js) | Sign-in/up UI, session management, JWT signing |
| Next.js | `next-auth/providers/credentials` (v1) → `Google` (v2+) | Email/password to start; OAuth later |
| Next.js | `@auth/mongodb-adapter` | Persists NextAuth-managed accounts/sessions |
| Flask | `pyjwt` | Verifies the HS256-signed JWT |
| Flask | `pymongo` | Reads the `users` collection by `user_id` claim |

**Flow:**

```
1. User submits credentials on Next.js /signin
2. NextAuth Credentials provider validates against the `users` collection
   (password hash check via bcrypt or argon2)
3. NextAuth issues a JWT with claims:
     { sub: user_id, email, iat, exp (1h) }
   signed HS256 with AUTH_SECRET
4. JWT is stored in an httpOnly, Secure, SameSite=Lax cookie
5. On every fetch to Flask:
     - Next.js BFF route handler reads the JWT from cookies
     - Forwards request to Flask with `Authorization: Bearer <jwt>`
6. Flask middleware (a @require_auth decorator):
     - Reads Authorization header
     - jwt.decode(token, AUTH_SECRET, algorithms=["HS256"])
     - Verifies exp, attaches user_id to request context
     - Returns 401 on any failure
```

**Why this pattern over alternatives:**

- **vs Clerk/Auth0:** free, no vendor lock, no per-MAU pricing. Solo build / free-tier constraint.
- **vs database sessions only:** Flask would need to round-trip to Mongo on every request to validate a session ID. JWT verifies offline.
- **vs JWT-only (no NextAuth):** we'd have to hand-roll cookie management, CSRF protection, refresh-token rotation. Reinventing solved problems.

**Refresh strategy:** Short access token (1h) + NextAuth's rolling session (sliding window). Hard sign-out on token expiry; refresh-token rotation can be added in a later phase if friction shows up.

**Secret distribution:** `AUTH_SECRET` is the *same* HS256 secret in `frontend/.env.local` and `backend/.env`. This is the shared trust anchor. Documented in `.env.example`. Rotate by deploying both at once (downtime budget: <30s overlap).

---

## MongoDB Schema

**Conventions:**
- `_id` is `ObjectId` unless noted.
- All collections carry `created_at` and `updated_at` (`Date`, server-set).
- All user-scoped docs carry `user_id: ObjectId` referencing `users._id`.
- Indexes follow the ESR rule (Equality, Sort, Range).

### `users`

```jsonc
{
  _id: ObjectId,
  email: "user@example.com",       // unique, lowercased
  password_hash: "...",            // argon2id or bcrypt; omitted if OAuth-only
  auth_providers: ["credentials"], // ["credentials", "google", ...]

  profile: {
    name: "Akua",
    sex: "F",                      // "M" | "F" — used for Mifflin-St Jeor
    height_cm: 168,
    age: 28,
    timezone: "Africa/Accra",      // IANA tz; used to bucket meals by local day
    locale: "en-GH",               // future-proof for diaspora localisation
    activity_level: "moderate"     // sedentary | light | moderate | active | very_active
  },

  goal: {
    type: "weight_loss",           // "weight_loss" | "muscle_gain"
    target_weight_kg: 62,          // nullable for muscle_gain
    weekly_rate_kg: 0.5,           // for weight_loss; informs deficit
    set_at: ISODate
  },

  targets: {                        // DERIVED — recomputed by Flask on profile change
    bmr_kcal: 1480,                 // Mifflin-St Jeor
    tdee_kcal: 2030,                // bmr * activity_factor
    daily_kcal_target: 1530,        // tdee - deficit (or + surplus)
    daily_protein_g: 110,           // 1.8g/kg for muscle_gain; 1.2g/kg for cut
    computed_at: ISODate
  },

  preferences: {
    retain_meal_images: false,      // privacy — opt-in
    units: "metric"                 // "metric" | "imperial"
  },

  usage: {
    vision_calls_today: 0,          // for daily rate limit
    vision_calls_reset_at: ISODate, // rolling 24h window in user's tz
    total_vision_calls: 0
  },

  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{ email: 1 }` — unique
- `{ "profile.timezone": 1 }` — useful for cron-driven daily-reset jobs

### `meals`

The hot-path collection. Time-series-shaped per user.

```jsonc
{
  _id: ObjectId,
  user_id: ObjectId,

  // What was eaten
  dish_name: "Jollof rice with chicken",
  matched_food_id: ObjectId,        // ref to `foods` if matched; nullable
  kcal: 620,
  macros: {
    protein_g: 32,
    carbs_g: 78,
    fat_g: 18
  },
  portion_g: 350,                   // estimated or user-corrected

  // Provenance
  source: "ai_estimate",            // "ai_estimate" | "user_corrected" | "manual"
  ai_metadata: {                    // present when source involves AI
    model: "claude-sonnet-vision-4.5",
    confidence: 0.74,
    raw_response_ref: "s3://...",   // optional, for QA — only if user opted in
    prompt_version: "v3"
  },

  // When
  consumed_at: ISODate,             // user-asserted meal time (UTC)
  local_date: "2026-05-11",         // YYYY-MM-DD in user's tz — denormalised for fast daily queries
  meal_type: "lunch",               // "breakfast" | "lunch" | "dinner" | "snack" | null

  // Image
  image: {
    storage_key: "meals/<user>/<uuid>.webp", // R2/S3 key; null if user didn't opt in to retention
    thumbnail_key: "meals/<user>/<uuid>_thumb.webp",
    retain_until: ISODate,          // 7-day TTL unless user opts in
    width: 1024,
    height: 1024
  },

  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{ user_id: 1, local_date: -1 }` — primary daily-feed query (the running total)
- `{ user_id: 1, consumed_at: -1 }` — history scroll
- `{ "image.retain_until": 1 }` — TTL index for auto-deleting expired images
- Optional later: `{ user_id: 1, matched_food_id: 1 }` for "your most-logged dishes"

**Why `local_date` is denormalised:** Daily kcal totals are queried 10x per day per active user. Computing the local date on every read (timezone-aware date conversion) is wasteful. Flask sets it once on insert.

### `foods` — Ghana food kcal table

The calibration data. Seeded from `shared/ghana-food-table.json`.

```jsonc
{
  _id: ObjectId,
  name: "Jollof rice",
  aliases: ["jolof", "party jollof", "Ghana jollof"],
  category: "rice_dish",            // "rice_dish" | "soup" | "stew" | "street_food" | "fish" | ...
  origin: "ghana",                  // "ghana" | "west_africa" | "western"

  kcal_per_typical_portion: 550,
  typical_portion_g: 300,
  kcal_per_100g: 183,
  macros_per_100g: {
    protein_g: 4.2,
    carbs_g: 28.5,
    fat_g: 5.1
  },

  source: "Ghana Food Composition Tables (FAO)",
  source_url: "https://...",
  confidence: "high",               // "high" | "medium" | "low" — kcal table quality signal
  notes: "Varies widely; assumes party-style with oil and tomato base",

  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{ name: 1 }`
- `{ aliases: 1 }` — multikey, for fuzzy match
- A text index on `{ name: "text", aliases: "text" }` for autocomplete in manual entry.

### `weights`

```jsonc
{
  _id: ObjectId,
  user_id: ObjectId,
  weight_kg: 73.4,
  recorded_at: ISODate,
  local_date: "2026-05-11",
  source: "manual",                 // "manual" | "scale_import" (future)
  note: "Morning, before breakfast", // optional
  created_at: ISODate
}
```

**Indexes:**
- `{ user_id: 1, recorded_at: -1 }` — chart data
- `{ user_id: 1, local_date: 1 }` — unique per day? No — allow multiple weigh-ins; chart picks first-of-day or daily average.

### `exercises`

Workout-library catalogue. Seeded from wger + ExerciseDB + MuscleWiki.

```jsonc
{
  _id: ObjectId,
  external_id: "wger_345",          // tracks origin for re-sync
  name: "Push-up",
  aliases: ["press-up"],

  target_muscle: "chest",           // primary
  secondary_muscles: ["triceps", "front_delts"],
  equipment: "bodyweight",          // "bodyweight" | "dumbbell" | "barbell" | "machine" | "band" | "kettlebell" | "cable"
  difficulty: "beginner",           // "beginner" | "intermediate" | "advanced"
  movement_pattern: "push",         // "push" | "pull" | "squat" | "hinge" | "carry" | "core"

  media: {
    gif_url: "https://cdn.example/exercises/pushup.gif",
    thumbnail_url: "...",
    youtube_id: "IODxDxX7oi4",      // nullable
    width: 360,
    height: 360,
    bytes: 84000                    // tracked for data-light budgeting
  },

  instructions: ["Place hands shoulder-width...", "Lower until ..."],
  tips: ["Keep core engaged", "..."],

  source: "wger",                   // "wger" | "exercisedb" | "musclewiki" | "youtube_curated"
  license: "CC-BY-SA-4.0",
  attribution: "wger.de",
  source_url: "https://wger.de/en/exercise/345",

  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `{ equipment: 1, target_muscle: 1 }` — main filter query
- `{ target_muscle: 1, difficulty: 1 }`
- `{ name: "text", aliases: "text" }`

### `workouts`

Pre-built plans. Optional in v1, can be hardcoded JSON for Phase 1.

```jsonc
{
  _id: ObjectId,
  name: "Home dumbbell upper-body",
  goal: "muscle_gain",              // "muscle_gain" | "weight_loss" | "general"
  equipment_required: ["dumbbell"], // intersection with user's available equipment
  estimated_duration_min: 35,
  difficulty: "intermediate",

  blocks: [
    {
      name: "Warm-up",
      exercises: [
        { exercise_id: ObjectId, sets: 1, reps: 10, rest_sec: 30 }
      ]
    },
    {
      name: "Main",
      exercises: [
        { exercise_id: ObjectId, sets: 3, reps: 10, rest_sec: 60 },
        { exercise_id: ObjectId, sets: 3, reps: 12, rest_sec: 60 }
      ]
    }
  ],

  curator: "system",                // "system" | "user_xyz" (future user-created plans)
  created_at: ISODate
}
```

**Indexes:**
- `{ goal: 1, equipment_required: 1 }`

### Collections to consider but defer

- `workout_logs` — user's completed-workout history. Add when "track your sets" feature lands; out of MVP per PROJECT.md.
- `user_food_corrections` — denormalised log of every correction the user made, for future ML signal. Add when there's enough volume to be useful.
- `notifications` — push/email tickers. Out of MVP.

---

## Data Flow: Image → Kcal

```
┌───────────────┐
│   User snaps  │
│  meal photo   │
│  (mobile cam) │
└───────┬───────┘
        │ 1. <input type=file capture>
        ▼
┌──────────────────────────────────────────────────────┐
│  Next.js client component                            │
│  - Compress: HEIC/JPEG → WebP, max 1024px, ~80% q    │
│  - Show local preview immediately                    │
│  - browser-image-compression lib                     │
└───────┬──────────────────────────────────────────────┘
        │ 2. POST /api/meals/estimate
        │    multipart/form-data { image: <blob> }
        ▼
┌──────────────────────────────────────────────────────┐
│  Next.js Route Handler (BFF)                         │
│  - Verify NextAuth session                           │
│  - Attach JWT                                        │
│  - Stream image to Flask                             │
└───────┬──────────────────────────────────────────────┘
        │ 3. POST {FLASK_URL}/vision/estimate
        │    Authorization: Bearer <jwt>
        │    multipart { image }
        ▼
┌──────────────────────────────────────────────────────┐
│  Flask /vision/estimate                              │
│  a. Verify JWT (pyjwt)                               │
│  b. Check rate limit (users.usage.vision_calls_today)│
│  c. Build prompt:                                    │
│     system = base_prompt + ghana_food_table.json     │
│     user = [image_bytes, "Identify dish + portion"]  │
│  d. Call LLM vision (Claude/GPT-4V)                  │
│  e. Parse JSON response → {dish, portion_g, kcal,    │
│     macros, confidence}                              │
│  f. Match dish_name against `foods` collection       │
│     (text index) → set matched_food_id               │
│  g. If matched: recompute kcal from foods table      │
│     (LLM gives dish + portion; foods table gives     │
│      kcal/g — table wins on calibrated dishes)       │
│  h. Increment users.usage.vision_calls_today         │
│  i. Optional: write image to R2 with 7-day TTL       │
└───────┬──────────────────────────────────────────────┘
        │ 4. 200 { dish, kcal, macros, confidence,
        │         portion_g, source: "ai_estimate",
        │         suggested_food_id }
        ▼
┌──────────────────────────────────────────────────────┐
│  Next.js — Estimate review screen                    │
│  - Show estimate                                     │
│  - "Looks right?" → confirm                          │
│  - "Wrong dish" → search foods (autocomplete)        │
│  - "Wrong portion" → slider 50g–800g                 │
└───────┬──────────────────────────────────────────────┘
        │ 5. POST /api/meals
        │    { dish_name, kcal, macros, portion_g,
        │      source: "ai_estimate" | "user_corrected",
        │      consumed_at, image_ref }
        ▼
┌──────────────────────────────────────────────────────┐
│  Next.js BFF → Flask POST /meals                     │
│  Flask:                                              │
│  - Compute local_date from user.profile.timezone     │
│  - Insert into `meals` collection                    │
│  - Return updated daily total                        │
└───────┬──────────────────────────────────────────────┘
        │ 6. 200 { meal, daily_total: { kcal, protein_g,
        │         remaining_kcal, target_kcal } }
        ▼
┌──────────────────────────────────────────────────────┐
│  Dashboard — animate kcal ring, update avatar        │
└──────────────────────────────────────────────────────┘
```

### Image transport decision

**Phase 1 (Walking Skeleton): send image bytes through Flask.** Simple, no extra service.
**Phase ≥ 2: switch to signed-URL direct upload to Cloudflare R2.**

| Approach | When | Why |
|----------|------|-----|
| Bytes through Flask | Phase 1, MVP | One fewer service. Free Render dyno can handle low volume. |
| Signed URL → R2, R2 key → Flask | When LLM-vision volume grows | Avoids proxying bytes through the constrained free dyno; egress-free on R2 saves cost; aligns with retention model. |

Either way, the LLM call happens server-side from Flask, not client-side — the API key must never reach the browser.

### Image lifecycle

- **Default:** image is sent to LLM, kcal is extracted, image is deleted within minutes (no `image.storage_key` written to the meal doc).
- **User opt-in (`preferences.retain_meal_images = true`):** image is written to R2 under `meals/<user_id>/<uuid>.webp`, with a TTL index on `image.retain_until` (default 90 days). User can purge anytime.
- **Privacy disclosure:** shown in onboarding and in `/settings/privacy` per PROJECT.md constraint.

---

## Cross-Cutting Concerns

### Error handling — RFC 7807 Problem Details

Both runtimes return errors as:

```json
{
  "type": "https://fitgh.app/errors/rate-limited",
  "title": "Daily vision quota exceeded",
  "status": 429,
  "detail": "You've used 20/20 meal estimates today. Resets at 00:00 Africa/Accra.",
  "code": "VISION_QUOTA_EXCEEDED",
  "instance": "/meals/estimate"
}
```

Frontend has one `ApiError` class that consumes this shape; toast messages and inline form errors derive from `code`. Stops bespoke error handling per endpoint.

### Loading / skeleton UI

- **Server components stream** by default (App Router `loading.tsx` + Suspense boundaries).
- **Skeleton screens** for the dashboard's three main panels (kcal ring, meals list, weight chart) — not spinners.
- **Optimistic updates** for meal logging: insert into local React state immediately on submit; reconcile or revert on server response.

### Offline cache strategy

- **Service worker via `next-pwa` (or its actively-maintained fork `@ducanh2912/next-pwa`)** for Next.js App Router.
- **Caching strategies:**
  - `cache-first` for static exercise media (gifs, thumbnails) — large win on Ghana mobile data.
  - `stale-while-revalidate` for the workout library JSON.
  - `network-first, fall-back-to-cache` for the dashboard.
- **IndexedDB (via `idb`)** for:
  - The full `exercises` collection snapshot (~few MB after image refs are externalised) — read offline, sync on reconnect.
  - Queued meal logs taken offline — replay when connectivity returns.
- **Don't cache LLM-vision responses.** Network-only; if offline, show "Save photo, estimate when online" affordance.

### Rate limiting on `/vision/estimate`

- **Per-user daily cap:** default 20 estimates/day. Tracked in `users.usage.vision_calls_today`, reset at midnight in user's local tz.
- **Global cost circuit-breaker:** an env var `MAX_DAILY_VISION_SPEND_USD`; when crossed, return 503 with a banner explaining "service paused for the day."
- **Burst protection:** Flask-Limiter for 10 req/min/user — protects against accidental double-submits.

### Timezone handling

- **Source of truth:** `users.profile.timezone` (IANA string), captured at sign-up (auto-detected via `Intl.DateTimeFormat().resolvedOptions().timeZone`, user-overridable).
- **Storage rule:** every timestamp in MongoDB is UTC (`ISODate`).
- **Display rule:** `local_date` (YYYY-MM-DD) is computed once at insert time using `zoneinfo` (Python) — this is what "today" means for daily totals.
- **Diaspora moves:** if a user changes timezone (UK → Ghana), past `local_date` values stay frozen (historical truth); new entries use the new tz. No retroactive re-bucketing.

### Secret management

- **`AUTH_SECRET`** — shared HS256 secret across both runtimes. 32+ random bytes.
- **`MONGODB_URI`** — in both `.env` files (frontend needs it only for NextAuth's adapter collections).
- **`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`** — backend only. Frontend never sees these.
- **`R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`** — backend only.
- **`.env.example`** lists every var name with a placeholder. `.env` and `.env.local` are gitignored from the first commit.

---

## Suggested Build Order

Phase boundaries the roadmapper can use directly.

### Phase 1: Walking Skeleton (must come first)

**Goal:** prove every architectural layer talks to every other layer end-to-end. No polish, no completeness.

Single user story: *"I can sign in, see a dashboard with my name on it, and the dashboard fetches data from MongoDB via Flask."*

Includes:
- Monorepo scaffold, `.env.example`, `.env`/`.env.local` gitignored
- Next.js App Router + Tailwind + NextAuth (credentials provider only, one hardcoded test user is fine)
- Flask app with `/health` and `/me` (returns the authenticated user's record)
- MongoDB Atlas connected from both sides; `users` collection with one seeded doc
- JWT round-trip working: NextAuth → cookie → Next.js BFF → `Authorization` header → Flask `pyjwt.decode` → 200 OK
- Vercel + Render deployments live with environment vars set
- A "Sign in → see /dashboard with your email" loop. That's it.

**Justification for being Phase 1 alone:** every later phase depends on the trust boundary between Next.js and Flask working. If JWT verification is broken or env-var distribution is wrong, you'll discover it now (cheap) instead of in Phase 4 (expensive).

### Phase 2: Profile + targets

- Onboarding form (name, sex, height, age, weight, activity, goal)
- Flask `/users/me` PATCH → recompute `targets` (Mifflin-St Jeor + activity factor + goal delta)
- Dashboard displays `daily_kcal_target` and `daily_protein_g`
- `weights` collection write + a basic weight-log endpoint

Parallel-able with Phase 1 fragments: the TDEE service can be unit-tested in Flask before the UI exists.

### Phase 3: Manual meal logging + Ghana food table

- Seed `foods` from `shared/ghana-food-table.json`
- `/foods/search` text-index autocomplete
- "Log a meal manually" UI: pick dish → adjust portion → submit
- `meals` collection write with `source: "manual"`
- Daily-total endpoint: `GET /meals/today` returns `{ meals: [...], total_kcal, remaining_kcal }`
- Dashboard kcal ring animates from manual entries

This is the **first user-valuable slice** even before LLM vision lands. It de-risks the data model and lets you eat your own dogfood.

### Phase 4: LLM vision integration (the core loop)

- Flask `/vision/estimate` route
- Prompt engineering with Ghana food table as system context
- Client-side image compression
- Photo → estimate → review → confirm → meals.insert flow
- Per-user rate limit on `users.usage.vision_calls_today`
- "Correct dish" + "correct portion" flows write `source: "user_corrected"`

The single highest-risk feature; isolating it to its own phase means a discovery (e.g., kcal accuracy is unacceptable) doesn't cascade.

### Phase 5: Workout library

- Seed `exercises` from wger/ExerciseDB exports in `shared/exercise-seed/`
- `/exercises/search` with equipment + muscle filters
- Workout-library UI with filter chips
- `next-pwa` integration + IndexedDB snapshot of `exercises` for offline use

Can run partially in parallel with Phase 4 — different data, different files. The PWA service worker work needs Phase 1's deployed shell to test.

### Phase 6: Animations + polish

- Lottie/Rive avatar + chart animations
- Skeleton UIs everywhere
- Page-weight budget audit (perf budgets per route)

### What can run in parallel after Phase 1

- TDEE service (Flask) ⟂ Onboarding form (Next.js) — they meet at the `/users/me` contract defined in `shared/schemas/`.
- Ghana food table seeding ⟂ Meal logging UI — meet at `/foods/search` shape.
- Exercise seeding ⟂ Workout library UI — meet at `/exercises/search` shape.

**Hard sequence:** Phase 1 → Phase 2 → (Phase 3 || Phase 5) → Phase 4 → Phase 6. Phase 4 specifically waits for Phase 3 because LLM-vision estimation reuses the meal-logging UI plumbing and `foods` matching.

---

## Walking Skeleton

**The thinnest end-to-end slice that lights up every architectural layer.**

```
┌──────────┐   sign in    ┌──────────────┐  jwt cookie  ┌──────────────┐
│ Browser  │ ───────────▶ │   Next.js    │ ───────────▶ │   Browser    │
└──────────┘              │   NextAuth   │              │  on /dashbd  │
                          │  + adapter   │              └──────┬───────┘
                          └──────┬───────┘                     │
                                 │                             │ GET /api/me
                                 ▼                             ▼
                          ┌──────────────┐              ┌──────────────┐
                          │   MongoDB    │              │   Next.js    │
                          │    Atlas     │              │ /api/me BFF  │
                          │ (users coll) │              └──────┬───────┘
                          └──────────────┘                     │
                                                               │ Bearer <jwt>
                                                               ▼
                                                        ┌──────────────┐
                                                        │   Flask      │
                                                        │   /me        │
                                                        │  (pyjwt)     │
                                                        └──────┬───────┘
                                                               │
                                                               ▼
                                                        ┌──────────────┐
                                                        │   MongoDB    │
                                                        │    Atlas     │
                                                        └──────────────┘
```

**Scope (do all of, nothing more):**

1. Monorepo with `/frontend`, `/backend`, `/shared`. `.env.example` checked in; `.env` files gitignored.
2. NextAuth v5 with Credentials provider, MongoDB adapter, JWT session strategy, `AUTH_SECRET` set.
3. One seeded user in `users` (`email`, `password_hash`, minimal profile) — created via a one-off seeding script in `/backend/scripts/seed.py`.
4. Next.js page `/signin` that signs in, and `/dashboard` that calls `GET /api/me`.
5. Next.js route handler `/api/me` that forwards the JWT to Flask `GET /me`.
6. Flask `/me` route protected by a `@require_auth` decorator using `pyjwt`, returning `{ email, profile.name }` from Mongo.
7. Both deployed: Vercel for `/frontend`, Render free dyno for `/backend`. Shared `AUTH_SECRET` in both.
8. `/health` endpoint on Flask returning `{ ok: true, mongo: "connected" }`.

**What it proves:**

- Auth works end-to-end (NextAuth → cookie → BFF → JWT header → Flask).
- The trust boundary is correct (shared secret, no leakage).
- Both runtimes read from the same Mongo cluster.
- Deployment plumbing on free tiers is real (Vercel ↔ Render ↔ Atlas) — no surprise egress, no surprise cold-start blowup.
- `shared/schemas/` is wired into both runtimes for the `User` shape.

**What it explicitly does NOT include:**

- Sign-up. The seed script creates the test user. Self-service signup is Phase 2.
- The Ghana food table (Phase 3).
- LLM vision (Phase 4).
- Animations, charts, anything Lottie/Rive (Phase 6).
- Service worker / PWA (Phase 5).

This is a 1–3 day skeleton. If it takes longer, your architectural assumptions are wrong and you want to know now.

---

## Risks

| Risk | Phase | Mitigation |
|------|-------|------------|
| Render free dyno cold start (~30s) breaks UX | 1, 4 | Accept for Phase 1; add a keep-warm ping (cron-job.org → `/health` every 5 min) once vision lands; migrate to Fly.io paid if it's still bad |
| LLM vision kcal accuracy too low for Ghana dishes | 4 | Calibrate via Ghana food table re-match; user-correction loop; spike the Phase 4 prompt engineering in a separate experiment before committing UI work |
| Image bytes through free dyno hit memory limits | 4 | Compress aggressively client-side (max 1024px, WebP); switch to R2 signed URLs in Phase 5 if any 502s appear |
| Atlas free-tier connection limit (500) | All | Single long-lived Flask process; pool size capped; NextAuth adapter sharing same cluster is fine at MVP scale |
| `AUTH_SECRET` rotation downtime | All | Plan a 2-deploy rotation (deploy backend accepting both old+new secrets, deploy frontend with new, deploy backend dropping old) before first user joins |
| Mongo schema drift between `shared/schemas/` and reality | 2+ | Pydantic models in Flask + Zod in Next.js, both generated from `shared/schemas/*.json`; CI fails if either drifts |
| Ghana food table coverage gaps | 3, 4 | Track LLM-returned dish names not in `foods`; add weekly review step; community sourcing post-PMF |
| Timezone bugs (diaspora users crossing midnight) | 3 | `local_date` denormalised at write time, never recomputed; test with users in UTC-8 and UTC+0 in Phase 2 |

---

## Sources

- [Compound Indexes — MongoDB Docs](https://www.mongodb.com/docs/manual/core/indexes/index-types/index-compound/) — confirms ESR rule used in the indexing recommendations.
- [Performance Best Practices: Indexing — MongoDB](https://www.mongodb.com/company/blog/performance-best-practices-indexing) — index-on-frequent-query-fields guidance.
- [NextAuth.js Getting Started](https://next-auth.js.org/getting-started/example) — confirms JWT strategy + Credentials provider as v5 pattern.
- [How to implement JWT authentication with Next.js 14 App Router and external API — vercel/next.js Discussion #87276](https://github.com/vercel/next.js/discussions/87276) — confirms the Next.js → external Flask JWT-forwarding pattern.
- [PyJWT documentation](https://pyjwt.readthedocs.io/en/latest/) — `jwt.decode(token, secret, algorithms=["HS256"])` is the verification pattern.
- [Using JWTs in Python Flask REST Framework — AppSignal](https://blog.appsignal.com/2025/04/30/using-jwts-in-python-flask-rest-framework.html) — Flask `@require_auth` decorator pattern.
- [Building an Offline-First Next.js 15 App with App Router — vercel/next.js Discussion #82498](https://github.com/vercel/next.js/discussions/82498) — confirms IndexedDB + service worker pattern for App Router.
- [Build a Next.js 16 PWA with true offline support — LogRocket](https://blog.logrocket.com/nextjs-16-pwa-offline-support/) — workbox caching strategies (cache-first, stale-while-revalidate).
- [Presigned URLs — Cloudflare R2 docs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/) — confirms direct-upload pattern for Phase 5 image-storage migration.
- [Storing user generated content — Cloudflare Reference Architecture](https://developers.cloudflare.com/reference-architecture/diagrams/storage/storing-user-generated-content/) — egress-free upload pattern.
- [RFC 7807 Problem Details](https://datatracker.ietf.org/doc/html/rfc7807) — standard JSON error shape.

Confidence levels:
- **HIGH** on stack patterns (NextAuth + PyJWT, Mongo indexing, monorepo layout) — multiple authoritative sources.
- **HIGH** on collection schemas — derived directly from PROJECT.md requirements, no external uncertainty.
- **MEDIUM** on the in-context Ghana-food-table calibration approach — pattern works for LLMs in general; FitGH-specific accuracy is a Phase 4 unknown that the build order explicitly de-risks.
- **MEDIUM** on free-tier deployment viability (Render cold starts in particular) — flagged in Risks.
