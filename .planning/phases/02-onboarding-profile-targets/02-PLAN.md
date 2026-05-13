---
phase: 02-onboarding-profile-targets
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  # Backend
  - backend/app/lib/__init__.py
  - backend/app/lib/tdee.py
  - backend/app/models/__init__.py
  - backend/app/models/profile.py
  - backend/app/models/weight_log.py
  - backend/app/db.py
  - backend/app/routes/profile.py
  - backend/app/routes/weights.py
  - backend/app/routes/me.py
  - backend/app/middleware/auth.py
  - backend/app/__init__.py
  - backend/tests/test_tdee.py
  - backend/tests/test_profile_routes.py
  - backend/tests/test_weights_routes.py
  - backend/tests/test_delete_account.py
  - backend/tests/conftest.py
  - backend/requirements.txt
  # Shared
  - shared/schemas/profile.schema.json
  - shared/schemas/weight-log.schema.json
  # Frontend — forms infra
  - frontend/package.json
  - frontend/src/lib/zod-schemas.ts
  - frontend/src/lib/tdee.ts
  - frontend/src/components/forms/rhf-input.tsx
  - frontend/src/components/forms/rhf-select.tsx
  - frontend/src/components/forms/rhf-radio-group.tsx
  - frontend/src/components/ui/input.tsx
  - frontend/src/components/ui/label.tsx
  - frontend/src/components/ui/radio-group.tsx
  - frontend/src/components/ui/select.tsx
  - frontend/src/components/ui/checkbox.tsx
  - frontend/src/components/ui/dialog.tsx
  # Frontend — onboarding
  - frontend/src/app/onboarding/page.tsx
  - frontend/src/app/onboarding/onboarding-flow.tsx
  - frontend/src/app/onboarding/steps/identity-step.tsx
  - frontend/src/app/onboarding/steps/body-goal-step.tsx
  - frontend/src/app/onboarding/steps/privacy-step.tsx
  - frontend/src/app/api/profile/route.ts
  - frontend/src/app/api/weights/route.ts
  - frontend/src/app/api/account/route.ts
  - frontend/src/lib/api-server.ts
  # Frontend — profile / dashboard / weights / settings / privacy
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/dashboard/weight-log-card.tsx
  - frontend/src/app/dashboard/target-card.tsx
  - frontend/src/app/profile/page.tsx
  - frontend/src/app/profile/profile-form.tsx
  - frontend/src/app/settings/page.tsx
  - frontend/src/app/settings/delete-account-button.tsx
  - frontend/src/app/privacy/page.tsx
  - frontend/middleware.ts
  # Traceability
  - .planning/REQUIREMENTS.md
autonomous: true
requirements:
  - AUTH-04
  - AUTH-05
  - PROF-01
  - PROF-02
  - PROF-03
  - PROF-04
  - PROF-05
  - PROF-06
  - PROF-07

must_haves:
  truths:
    - "A signed-in user without a profile is redirected from /dashboard to /onboarding"
    - "User completes 3-screen onboarding (identity / body+goal / privacy+timezone) and a profile is persisted in MongoDB profiles collection keyed on clerk_id"
    - "On finishing onboarding, dashboard shows daily_kcal_target computed via Mifflin-St Jeor BMR x activity factor +/- (deficit|surplus)"
    - "1200 kcal female / 1500 kcal male floor enforced; clinician disclaimer renders only when floor was hit"
    - "Muscle-gain users see a daily_protein_g_target = round(weight_kg * 1.6) displayed prominently; weight-loss users do not see the protein card"
    - "Privacy disclosure naming Anthropic (Claude Sonnet 4.6) as meal-image processor appears on screen 3 and is gated by a required consent checkbox before onboarding can finish; privacy_consent_at is timestamped on the profile doc"
    - "/privacy stub page is reachable, names Anthropic + Clerk + MongoDB Atlas + Render, and is linked from the consent screen and a global footer"
    - "User can edit any profile field on /profile and the kcal+protein targets recompute on save"
    - "User can log a weight on /dashboard; entries persist in weight_logs collection with (user_id, kg, logged_at); history list shows latest 30 entries newest-first"
    - "User can click Delete account in /settings, confirm in a modal, and the cascade deletes profile + weight_logs + users record server-side AND calls Clerk users.delete() via the Python SDK; user is signed out and lands on /sign-in"
  artifacts:
    - path: "backend/app/lib/tdee.py"
      provides: "Mifflin-St Jeor BMR + TDEE + floor + protein-target pure functions"
      exports: ["bmr_mifflin_st_jeor", "tdee", "daily_kcal_target", "daily_protein_g_target", "ACTIVITY_FACTORS", "KCAL_FLOORS"]
    - path: "backend/app/models/profile.py"
      provides: "Pydantic v2 Profile model + ProfileCreate + ProfileUpdate + serialization helpers"
      exports: ["Profile", "ProfileCreate", "ProfileUpdate", "Sex", "Locale", "ActivityLevel", "PrimaryGoal"]
    - path: "backend/app/models/weight_log.py"
      provides: "Pydantic v2 WeightLog model"
      exports: ["WeightLog", "WeightLogCreate"]
    - path: "backend/app/routes/profile.py"
      provides: "GET /profile (404 if absent), POST /profile (create), PATCH /profile (update); recomputes targets on every write"
      exports: ["bp"]
    - path: "backend/app/routes/weights.py"
      provides: "POST /weights (log entry), GET /weights (history newest-first, limit 30)"
      exports: ["bp"]
    - path: "backend/app/routes/me.py"
      provides: "Extended with DELETE /me cascade — removes profile + weight_logs + users record, then clerk.users.delete()"
      exports: ["bp"]
    - path: "shared/schemas/profile.schema.json"
      provides: "JSON Schema for the Profile contract — shared between FE Zod and BE Pydantic"
    - path: "shared/schemas/weight-log.schema.json"
      provides: "JSON Schema for the WeightLog contract"
    - path: "frontend/src/lib/zod-schemas.ts"
      provides: "Zod schemas matching backend Pydantic shapes (Profile, ProfileUpdate, WeightLog)"
      exports: ["profileCreateSchema", "profileUpdateSchema", "weightLogSchema"]
    - path: "frontend/src/lib/tdee.ts"
      provides: "Client-side TDEE preview during onboarding/edit (mirrors backend tdee.py exactly)"
      exports: ["bmrMifflinStJeor", "tdee", "dailyKcalTarget", "dailyProteinGTarget"]
    - path: "frontend/src/app/onboarding/page.tsx"
      provides: "/onboarding route — server component that redirects to /dashboard if profile already exists, otherwise renders <OnboardingFlow/>"
    - path: "frontend/src/app/onboarding/onboarding-flow.tsx"
      provides: "Client component — single-page 3-step conditional render driven by RHF state; submits to /api/profile on finish"
    - path: "frontend/src/app/api/profile/route.ts"
      provides: "BFF GET/POST/PATCH forwarder to Flask /profile (attaches Clerk Bearer JWT, same pattern as /api/me)"
    - path: "frontend/src/app/api/weights/route.ts"
      provides: "BFF GET/POST forwarder to Flask /weights"
    - path: "frontend/src/app/api/account/route.ts"
      provides: "BFF DELETE forwarder to Flask DELETE /me; on success signs the Clerk session out via the Clerk server SDK"
    - path: "frontend/src/app/profile/page.tsx"
      provides: "/profile edit page (server component fetches profile, client form mutates)"
    - path: "frontend/src/app/dashboard/page.tsx"
      provides: "Replaces Phase 1 placeholder — fetches /api/profile; if 404 redirects to /onboarding; otherwise renders TargetCard + WeightLogCard + recent weights list"
    - path: "frontend/src/app/settings/page.tsx"
      provides: "/settings route with delete-account button + modal"
    - path: "frontend/src/app/privacy/page.tsx"
      provides: "/privacy stub naming Anthropic + Clerk + MongoDB Atlas + Render"
    - path: "frontend/middleware.ts"
      provides: "Extended createRouteMatcher to protect /onboarding(.*) /profile(.*) /settings(.*) /api/profile(.*) /api/weights(.*) /api/account(.*) in addition to existing /dashboard(.*) and /api/me(.*)"
  key_links:
    - from: "frontend/src/app/dashboard/page.tsx"
      to: "/api/profile"
      via: "server-side fetch with cookie forward (same pattern as /api/me in dashboard/page.tsx)"
      pattern: "fetch.*api/profile"
    - from: "frontend/src/app/api/profile/route.ts"
      to: "backend /profile"
      via: "auth().getToken() -> Bearer to ${NEXT_PUBLIC_API_URL}/profile"
      pattern: "fetch.*\\${apiUrl}/profile"
    - from: "backend/app/routes/profile.py"
      to: "app.db.db.profiles + app.lib.tdee.daily_kcal_target"
      via: "require_auth -> Profile.from_request -> compute targets -> upsert by clerk_id"
      pattern: "@require_auth"
    - from: "frontend/src/app/onboarding/onboarding-flow.tsx"
      to: "/api/profile (POST)"
      via: "RHF handleSubmit -> fetch POST -> router.push('/dashboard')"
      pattern: "fetch.*api/profile.*POST"
    - from: "frontend/src/app/settings/delete-account-button.tsx"
      to: "/api/account (DELETE)"
      via: "confirm modal -> fetch DELETE -> Clerk signOut() -> redirect /sign-in"
      pattern: "fetch.*api/account.*DELETE"
    - from: "backend/app/routes/me.py (DELETE /me handler)"
      to: "clerk_backend_api Clerk.users.delete()"
      via: "After Mongo cascade succeeds, call _get_clerk().users.delete(user_id=g.clerk_user_id); both must succeed or the route returns 500 and STATE rolls back"
      pattern: "users\\.delete\\("
---

# Phase 2 Plan 02 — Onboarding + Profile + Targets

## Phase Goal

A new user can finish a ≤3-screen onboarding in under 60 seconds, leaves with a daily kcal target (and protein target if muscle-gain) shown on the dashboard, can log their weight, edit their profile later, and has signed an explicit consent that meal photos will be sent to an LLM vision provider — plus a working account-deletion path.

(From ROADMAP.md Phase 2.)

## Success Criteria (from ROADMAP.md)

1. New user completes onboarding in ≤3 screens — captures name, sex, height_cm, weight_kg, age, timezone, locale (Ghana / diaspora), activity_level, primary_goal — and lands on /dashboard with a daily kcal target visible.
2. Dashboard kcal target = Mifflin-St Jeor BMR × activity factor − 500 (weight loss) OR + 250 (muscle gain), with a 1200 female / 1500 male floor and a clinician disclaimer when the floor is hit; muscle-gain users additionally see a protein target of 1.6 g/kg bodyweight.
3. User can edit any profile field after onboarding and targets recompute on save; user can log a weight entry and history is viewable.
4. Sign-up flow shows a privacy disclosure naming Anthropic (Claude Sonnet 4.6) as the meal-image processor before the user can finish onboarding; disclosure links to a stub /privacy page.
5. User can hit Delete account in /settings; Flask + Clerk cascade-delete all FitGH data (profile, weight_logs, users record, plus the Clerk auth record via SDK — no webhook); user is signed out and lands on /sign-in.

## Inherited Constraints (do not violate)

- **Render-only architecture** (memory/render-only-rewrite.md). No Sentry FE wizard, no Vercel Analytics, no Vercel Speed Insights, no Fly.io, no size-limit CI gate, no custom gitleaks CI rules, no Atlas IP-pinning, no Clerk twin instances. Phase 2 inherits Phase 1's deployment shape exactly.
- **Sync-on-demand pattern**: do NOT add Clerk webhooks. Profile create is driven by the explicit onboarding form POST; user delete is driven by the explicit /api/account DELETE.
- **SI units only** — cm, kg. No imperial conversion.
- **No AI in Phase 2** — no Anthropic SDK calls, no foods collection, no meal logging. Phase 4 owns vision; Phase 3 owns manual meal logging. Phase 2's only AI-related artifact is the privacy disclosure copy.
- **No animation work** — Phase 5 owns the Rive avatar and animated kcal ring. Phase 2 ships a STATIC dashboard with kcal as a number + a Tailwind progress bar placeholder.
- **Tailwind v4 CSS-first** — no `tailwind.config.js`. New shadcn primitives are added via `pnpm dlx shadcn@latest add <component>` (the repo already has `components.json` with the v4 marker).

## Slice Overview

| Slice | Theme | Tasks |
|-------|-------|-------|
| A | Backend schemas, TDEE math, routes (profile + weights + cascade-delete) | 5 |
| B | Frontend forms infrastructure (RHF + Zod + shadcn primitives + shared TS schemas) | 3 |
| C | Onboarding flow + dashboard redirect | 3 |
| D | Profile edit + weight log on dashboard + BFF forwarders | 3 |
| E | Privacy page + Settings + Delete-account cascade | 2 |
| F | End-to-end verification + traceability update | 1 |

Total: **17 tasks**. Granularity is fine-grained because Phase 2 is shipping nine PROF + AUTH requirements end-to-end across both stacks. Each slice is internally ordered; cross-slice ordering is A → B (independent) → C (needs A + B) → D (needs A + B + C) → E (needs A + B for the cascade route + delete modal) → F.

## Threat Register (Phase 2)

| Threat ID  | Category               | Component                                  | Disposition | Mitigation Plan |
|------------|------------------------|--------------------------------------------|-------------|-----------------|
| T-02-01    | Spoofing               | DELETE /me cascade endpoint                | mitigate    | Endpoint is `@require_auth`-decorated; uses `g.clerk_user_id` from the verified JWT only; never reads a user_id from request body or query string. Backend test asserts a forged-body `clerk_id` is ignored. |
| T-02-02    | Tampering              | Profile PATCH                              | mitigate    | Pydantic `ProfileUpdate` is the request schema; `clerk_id`, `created_at`, `privacy_consent_at`, `daily_kcal_target`, `daily_protein_g_target` are EXCLUDED from the update model — the client cannot set them. Backend test asserts a PATCH with `{clerk_id: "user_attacker"}` returns 422 or silently ignores the field. |
| T-02-03    | Repudiation            | Privacy consent                            | mitigate    | `privacy_consent_at` (UTC timestamp) is stamped server-side at profile creation when `privacy_consent === true`; cannot be set or cleared by a subsequent PATCH. Functions as a minimal v1 GDPR audit; the full audit log is deferred to Phase 7 LEGAL-01. |
| T-02-04    | Information Disclosure | Profile + weight_logs cross-user reads     | mitigate    | All profile/weights queries filter by `g.clerk_user_id` from the JWT. Backend test signs JWT for user A, queries weight_logs, asserts no docs for user B leak even when DB contains both. |
| T-02-05    | Denial of Service      | Weight log endpoint                        | accept      | No rate limit beyond Flask's default. M0 cluster + maxPoolSize=10 from Phase 1 SEC-04 already caps blast radius; a single user spamming POST /weights writes small docs (≤200 B each). Real rate-limiting deferred to Phase 7 hardening. |
| T-02-06    | Elevation of Privilege | Delete-account Clerk SDK call              | mitigate    | The Clerk `users.delete(user_id=...)` call MUST use `g.clerk_user_id` from the verified JWT — never from a request body. Even on the privileged path (clerk-backend-api running with `sk_live_`), the SDK is constrained by the JWT-derived id. Defence in depth: if the Mongo cascade fails, the Clerk delete is NOT attempted. |
| T-02-07    | Tampering              | TDEE recompute                             | mitigate    | `daily_kcal_target` + `daily_protein_g_target` are NEVER accepted from the request; they are computed server-side from `(sex, height_cm, weight_kg, age, activity_level, primary_goal)` on every write. Backend test asserts a POST body with `daily_kcal_target: 10000` is overridden by the server-computed value. |
| T-02-08    | Information Disclosure | Privacy disclosure must precede onboarding finish | mitigate    | The consent checkbox is wired to RHF's `disabled` on the submit button (FE), AND the backend rejects POST /profile with HTTP 422 when `privacy_consent !== true` (BE). Both layers are needed because FE-only enforcement is bypassable via direct API call. |

Trust boundaries: browser → Next.js BFF (same-origin, no cross-origin), BFF → Flask (Render-internal, Bearer JWT), Flask → MongoDB Atlas (TLS, scoped role), Flask → Clerk (clerk-backend-api SDK, secret in env). No new trust boundaries vs Phase 1.

---

## Slice A — Backend schemas + TDEE + routes

<task type="auto" tdd="true">
  <name>Task P2-A.1: TDEE pure functions + unit tests (Mifflin-St Jeor, activity factors, floors, protein target)</name>
  <files>backend/app/lib/__init__.py, backend/app/lib/tdee.py, backend/tests/test_tdee.py</files>
  <behavior>
    - `bmr_mifflin_st_jeor(sex, weight_kg, height_cm, age)` returns float:
      - Male: 10*kg + 6.25*cm - 5*age + 5 (e.g. male, 70kg, 175cm, 30y -> 1648.75)
      - Female: 10*kg + 6.25*cm - 5*age - 161 (e.g. female, 60kg, 165cm, 28y -> 1351.25)
    - `ACTIVITY_FACTORS = {"sedentary": 1.2, "lightly_active": 1.375, "moderately_active": 1.55, "very_active": 1.725, "extra_active": 1.9}`
    - `tdee(bmr, activity_level)` returns `bmr * ACTIVITY_FACTORS[activity_level]`
    - `daily_kcal_target(sex, weight_kg, height_cm, age, activity_level, primary_goal)` returns `{ kcal_target: int (rounded), floor_hit: bool }`:
      - weight_loss: TDEE - 500
      - muscle_gain: TDEE + 250
      - Apply floor: `KCAL_FLOORS = {"male": 1500, "female": 1200}`; if result < floor, return floor and set `floor_hit=True`
      - Round half-up to integer kcal
    - `daily_protein_g_target(weight_kg, primary_goal)` returns `round(weight_kg * 1.6)` ONLY when `primary_goal == "muscle_gain"`, else `None`
    - Test cases (MUST cover, all in test_tdee.py):
      - `test_bmr_male_known_value`, `test_bmr_female_known_value`
      - `test_tdee_all_five_activity_levels_have_correct_factor`
      - `test_target_weight_loss_subtracts_500`
      - `test_target_muscle_gain_adds_250`
      - `test_floor_kicks_in_for_small_sedentary_female` (e.g. female, 45kg, 155cm, 65y, sedentary, weight_loss -> 1200 + floor_hit=True)
      - `test_floor_kicks_in_for_small_sedentary_male`
      - `test_floor_not_hit_for_typical_male` (e.g. male, 80kg, 180cm, 30y, moderately_active, weight_loss -> floor_hit=False)
      - `test_protein_target_only_for_muscle_gain` (weight_loss returns None)
      - `test_protein_target_rounds` (70kg -> 112)
      - `test_invalid_activity_level_raises_value_error`
      - `test_invalid_primary_goal_raises_value_error`
      - `test_invalid_sex_raises_value_error`
  </behavior>
  <action>
    Create `backend/app/lib/__init__.py` (empty namespace module). Implement `backend/app/lib/tdee.py` as pure Python with no Flask/Mongo imports — only the standard library. Export constants `ACTIVITY_FACTORS`, `KCAL_FLOORS` so the test file and routes can import them. Use Python `Literal` types for `sex: Literal["male", "female"]`, `activity_level: Literal[<5 levels>]`, `primary_goal: Literal["weight_loss", "muscle_gain"]` so type errors surface during pytest's import-time checks. Per D-TDEE-FORMULA in 02-CONTEXT.md, the formula must be Mifflin-St Jeor exactly (not Harris-Benedict, not Katch-McArdle).

    Write tests FIRST in `backend/tests/test_tdee.py` (RED), then implement `tdee.py` until green. The test file should import via `from app.lib.tdee import ...`.

    Per D-INTERFACE-FIRST: this module is the contract that `backend/app/routes/profile.py` (Task P2-A.4) consumes. Pin the public exports listed above; the routes will import only those names.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_tdee.py -v</automated>
  </verify>
  <done>All ~12 test cases pass; `ruff check backend/app/lib backend/tests/test_tdee.py` is clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P2-A.2: Pydantic Profile + WeightLog models, JSON schema generation, db.py extension</name>
  <files>backend/app/models/__init__.py, backend/app/models/profile.py, backend/app/models/weight_log.py, backend/app/db.py, shared/schemas/profile.schema.json, shared/schemas/weight-log.schema.json, backend/tests/test_profile_models.py</files>
  <behavior>
    - `Profile` (full doc shape stored in Mongo):
      - `clerk_id: str` (matches `^user_[a-zA-Z0-9]+$`)
      - `name: str` (1..80 chars)
      - `sex: Literal["male", "female"]`
      - `height_cm: int` (100..230)
      - `weight_kg: float` (30.0..300.0)
      - `age: int` (13..100)
      - `timezone: str` (IANA, e.g. "Africa/Accra"; validated as non-empty)
      - `locale: Literal["ghana", "diaspora"]` (per D-LOCALE-BUCKETS: single diaspora bucket in v1, no country picker)
      - `activity_level: Literal[<5>]`
      - `primary_goal: Literal["weight_loss", "muscle_gain"]`
      - `daily_kcal_target: int` (server-computed)
      - `daily_protein_g_target: int | None` (None for weight-loss users)
      - `floor_hit: bool` (whether the kcal floor clamped the target — drives the clinician disclaimer)
      - `privacy_consent_at: datetime` (UTC, required at create)
      - `created_at: datetime`, `updated_at: datetime`
    - `ProfileCreate` (POST body): everything from Profile EXCEPT clerk_id, daily_kcal_target, daily_protein_g_target, floor_hit, privacy_consent_at, created_at, updated_at. Adds `privacy_consent: bool` (must be True; validator rejects False).
    - `ProfileUpdate` (PATCH body): all fields from ProfileCreate as Optional, EXCLUDING `privacy_consent` (consent cannot be re-toggled). Pydantic `model_config = {"extra": "forbid"}` so unknown fields (e.g. `clerk_id`, `daily_kcal_target`) raise 422.
    - `WeightLog`: `user_id: str` (clerk_id, server-set), `kg: float` (20..400), `logged_at: datetime` (server-set UTC).
    - `WeightLogCreate` (POST body): `kg: float` only.
    - All models use Pydantic v2 (`field_validator`, `model_config`); datetime fields serialize as ISO-8601 UTC.
    - Tests in `test_profile_models.py`:
      - `test_profile_create_rejects_consent_false`
      - `test_profile_update_rejects_unknown_field` (extra="forbid")
      - `test_profile_update_rejects_clerk_id_field`
      - `test_profile_update_rejects_daily_kcal_target_field`
      - `test_height_out_of_range_rejected`
      - `test_weight_out_of_range_rejected`
      - `test_age_out_of_range_rejected`
      - `test_invalid_sex_rejected`
      - `test_invalid_locale_rejected`
      - `test_weight_log_kg_range`
  </behavior>
  <action>
    Create `backend/app/models/__init__.py` and the two model files. Use Pydantic v2 idioms exactly (already in requirements.txt at >=2.9,<3). Generate the JSON Schemas by running `Profile.model_json_schema()` in a one-off script and writing the result to `shared/schemas/profile.schema.json` (and same for weight-log). The `$id` should mirror `shared/schemas/user.schema.json`'s pattern.

    Extend `backend/app/db.py`: add `profiles: Collection = db["profiles"]` and `weight_logs: Collection = db["weight_logs"]` as new module-level singletons (same pattern as the existing `users` line). Add an index hint comment for `weight_logs` on `(user_id, logged_at)` — actual index creation is deferred to a one-off operator script (do not add an `ensure_index` call in module load per the Phase 1 pattern of no side effects on import).

    Per D-STORAGE-NEW-COLLECTIONS: do NOT mutate the existing `users` collection schema — the email/clerk_id pair stays in `users`, profile lives in the new `profiles` collection for separation of identity vs body data.

    Write tests FIRST (RED) covering the validator behaviors above, then implement until green.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_profile_models.py -v</automated>
  </verify>
  <done>All ~10 test cases pass; `shared/schemas/profile.schema.json` and `shared/schemas/weight-log.schema.json` exist and validate as JSON; `ruff check backend/app/models` is clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P2-A.3: Flask /profile routes (GET 404-if-missing / POST create / PATCH update) with server-side target recompute</name>
  <files>backend/app/routes/profile.py, backend/app/__init__.py, backend/tests/conftest.py, backend/tests/test_profile_routes.py</files>
  <behavior>
    - `GET /profile`:
      - `@require_auth`
      - Looks up `profiles.find_one({clerk_id: g.clerk_user_id})`
      - Returns `200 {<full Profile JSON>}` when found
      - Returns `404 {"error": "profile_not_found"}` when missing (frontend uses this to redirect onboarding)
    - `POST /profile`:
      - `@require_auth`
      - Parses body via `ProfileCreate.model_validate_json(request.data)` (returns 422 on validation failure including `privacy_consent !== true`)
      - Server-computes `daily_kcal_target`, `daily_protein_g_target`, `floor_hit` via `app.lib.tdee.daily_kcal_target` + `daily_protein_g_target`
      - Stamps `clerk_id = g.clerk_user_id`, `privacy_consent_at = datetime.now(UTC)`, `created_at = updated_at = now`
      - Upserts into `profiles` keyed on `clerk_id` (so re-POST acts as an idempotent recreate — useful for onboarding retries)
      - Returns `201 {<full Profile JSON>}`
    - `PATCH /profile`:
      - `@require_auth`
      - Parses body via `ProfileUpdate.model_validate_json(request.data)` (returns 422 on unknown field per `extra="forbid"`)
      - Loads existing profile (404 if absent)
      - Merges only the provided fields into the existing doc
      - Recomputes targets server-side (do NOT trust any kcal target from the client; T-02-07)
      - Updates `updated_at`
      - Returns `200 {<full Profile JSON>}`
    - Backend tests in `test_profile_routes.py`:
      - `test_get_profile_404_when_absent`
      - `test_get_profile_returns_doc`
      - `test_post_profile_creates_and_computes_targets`
      - `test_post_profile_rejects_consent_false_422`
      - `test_post_profile_ignores_client_supplied_kcal_target` (T-02-07: send `daily_kcal_target: 10000` in body, assert server overrides with the computed value)
      - `test_post_profile_floor_hit_sets_disclaimer_flag`
      - `test_post_profile_muscle_gain_computes_protein_target`
      - `test_post_profile_weight_loss_protein_target_none`
      - `test_patch_profile_recomputes_targets_on_weight_change`
      - `test_patch_profile_rejects_unknown_field_422` (T-02-02: send `clerk_id: "user_attacker"`)
      - `test_patch_profile_404_when_no_profile`
      - `test_profile_isolated_by_clerk_id` (T-02-04: two profiles in DB, JWT for user A returns only A's doc)
  </behavior>
  <action>
    Per D-ROUTE-LAYOUT in 02-CONTEXT.md: keep `/profile` as a separate route module from `/me` (cleaner schema separation). Create `backend/app/routes/profile.py` exporting `bp` as a Flask Blueprint. Register it in `backend/app/__init__.py` alongside the existing `health_bp` and `me_bp` registrations.

    Use `mongomock` fixtures in `conftest.py` (already established Phase 1 pattern — see `backend/tests/test_me.py`'s `mongo_users` fixture). Extend `conftest.py` with `mongo_profiles` and `mongo_weight_logs` fixtures monkey-patching both `app.db` AND each route's module-level binding (this is the Phase 1 pattern from "Backend test pattern" in 01-SUMMARY.md key-decisions — Python copies references at import time so both bindings must be patched).

    For JWT mocking in tests, reuse the existing pattern that intercepts `_get_clerk()` and seeds `g.clerk_user_id` (look at how `test_me.py` does this).

    Write tests FIRST (RED), then implement the route until green.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_profile_routes.py -v</automated>
  </verify>
  <done>All ~12 test cases pass; route registered in `create_app()`; previously-passing tests still pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P2-A.4: Flask /weights routes (POST log / GET history)</name>
  <files>backend/app/routes/weights.py, backend/app/__init__.py, backend/tests/test_weights_routes.py</files>
  <behavior>
    - `POST /weights`:
      - `@require_auth`
      - Parses body via `WeightLogCreate.model_validate_json(request.data)`
      - Inserts `{user_id: g.clerk_user_id, kg: <body.kg>, logged_at: datetime.now(UTC)}`
      - ALSO updates the user's profile `weight_kg` AND recomputes `daily_kcal_target` + `daily_protein_g_target` (so the dashboard target reflects the latest weight). If no profile exists, returns `409 {"error": "no_profile"}` (frontend should redirect to onboarding).
      - Returns `201 {<WeightLog JSON>}`
    - `GET /weights`:
      - `@require_auth`
      - Query param `limit` (default 30, max 100)
      - Returns `200 {entries: [<WeightLog JSON>...] }` newest-first by `logged_at`
      - Filtered by `user_id = g.clerk_user_id` (T-02-04)
    - Tests:
      - `test_post_weight_inserts_and_updates_profile_target`
      - `test_post_weight_409_when_no_profile`
      - `test_post_weight_rejects_kg_out_of_range_422`
      - `test_get_weights_returns_history_newest_first`
      - `test_get_weights_respects_limit_param`
      - `test_get_weights_isolated_by_user_id`
  </behavior>
  <action>
    Create `backend/app/routes/weights.py`. Register `weights_bp` in `create_app()`. The "POST also recomputes profile target" rule is required to make PROF-04 + PROF-07 mesh — without it the dashboard would show a stale kcal target after a weight log entry. Per the goal-backward must_have "user can log a new weight... and the entry is persisted (history viewable)", combined with PROF-04 "system computes daily kcal target", the recompute on weight-log is the only way to honour both simultaneously. The alternative (require user to also go to /profile and re-save) violates the ≤3-screen UX promise.

    Use the same mongomock fixture pattern as P2-A.3.

    Write tests FIRST (RED), then implement until green.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_weights_routes.py -v</automated>
  </verify>
  <done>All ~6 test cases pass; route registered; full backend test suite (`pytest -q`) green.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P2-A.5: DELETE /me cascade (profile + weights + users + Clerk SDK delete)</name>
  <files>backend/app/routes/me.py, backend/tests/test_delete_account.py, backend/requirements.txt</files>
  <behavior>
    - `DELETE /me`:
      - `@require_auth`
      - Begins a best-effort cascade:
        1. `weight_logs.delete_many({"user_id": g.clerk_user_id})` — captures count for response
        2. `profiles.delete_one({"clerk_id": g.clerk_user_id})`
        3. `users.delete_one({"clerk_id": g.clerk_user_id})`
        4. `_get_clerk().users.delete(user_id=g.clerk_user_id)` (clerk-backend-api 5.0.6 — verify the exact method signature against installed SDK; per D-CLERK-SDK-DELETE the call site MUST use the JWT-derived id)
      - If steps 1-3 succeed but step 4 fails, the Mongo data is gone but the Clerk account remains; return `502 {"error": "clerk_delete_failed", "mongo_deleted": true}` and the FE shows "Your FitGH data was deleted, but auth deletion failed — contact support."
      - If step 4 succeeds, return `200 {"ok": true, "deleted": {weight_logs: N, profile: 0|1, user: 0|1, clerk: true}}`
      - The endpoint is idempotent: calling it twice when the user is already deleted returns success the second time (Mongo deletes are no-ops; the Clerk call needs to handle "user not found" gracefully — wrap in try/except matching the clerk-backend-api error class for not-found and treat as success).
    - Tests:
      - `test_delete_me_cascades_mongo_collections` (uses mongomock; seeds profile + 2 weights + user; asserts all 3 cleared)
      - `test_delete_me_calls_clerk_sdk_users_delete` (mocks `_get_clerk().users.delete` and asserts called with `user_id=g.clerk_user_id`)
      - `test_delete_me_uses_jwt_user_id_not_body` (T-02-01: POST body `{clerk_id: "user_attacker"}` is ignored; only the JWT-bound id is deleted)
      - `test_delete_me_idempotent_when_already_deleted`
      - `test_delete_me_returns_502_when_clerk_call_fails` (mocks clerk SDK to raise; asserts mongo data still deleted; asserts response status)
  </behavior>
  <action>
    Extend the existing `backend/app/routes/me.py` to add the DELETE handler. Do NOT create a separate `/account` or `/delete-account` route — DELETE /me is the REST-idiomatic shape and lets the BFF wrapper stay a thin pass-through.

    Verify `clerk-backend-api>=5.0.6` (already in requirements.txt) exposes `Clerk.users.delete(user_id=...)`. If the SDK shape has drifted, the task may need to use `clerk.users.delete_user(user_id)` instead — implement whichever matches, and pin the exact version in requirements.txt with a `# Required: users.delete API surface` comment.

    Write tests FIRST. The test for the SDK call uses `monkeypatch.setattr("app.middleware.auth._get_clerk", lambda: MagicMock(users=MagicMock(delete=MagicMock(return_value=None))))` pattern.

    Per D-NO-WEBHOOKS in 02-CONTEXT.md and project memory render-only-rewrite: this is the ONLY path that deletes a Clerk user. We are NOT adding a `user.deleted` webhook handler. The synchronous SDK call is the contract.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_delete_account.py tests/test_me.py -v</automated>
  </verify>
  <done>All 5 new tests pass; existing `test_me.py` still passes; total backend pytest count is ≥25 (Phase 1 baseline 22 + new TDEE ~12 + models ~10 + profile routes ~12 + weights ~6 + delete ~5 = ~67 total).</done>
</task>

---

## Slice B — Frontend forms infrastructure

<task type="auto">
  <name>Task P2-B.1: Install RHF + Zod + resolvers; add shadcn primitives (input/label/radio-group/select/checkbox/dialog)</name>
  <files>frontend/package.json, frontend/src/components/ui/input.tsx, frontend/src/components/ui/label.tsx, frontend/src/components/ui/radio-group.tsx, frontend/src/components/ui/select.tsx, frontend/src/components/ui/checkbox.tsx, frontend/src/components/ui/dialog.tsx</files>
  <action>
    From `frontend/` run (in order, each as its own pnpm invocation):

    1. `pnpm add react-hook-form@^7.60 zod@^3.25 @hookform/resolvers@^5.1` — matches the versions locked in CLAUDE.md "Forms" row.
    2. `pnpm dlx shadcn@latest add input label radio-group select checkbox dialog` — adds the six new primitives via the shadcn CLI; this respects the existing `components.json` v4 config (tailwind.config="" marker preserved). The CLI may also pull in `@radix-ui/react-radio-group`, `@radix-ui/react-select`, `@radix-ui/react-checkbox`, `@radix-ui/react-dialog`, `@radix-ui/react-label` as transitive deps — accept them.

    Run `pnpm build` afterwards to confirm:
    - No TypeScript errors.
    - `/dashboard` First Load JS stays within manual budget (≤180 kB gzipped target from PERF-01, currently 133.3 kB) — record the new measurement in the commit message. RHF + Zod are NOT imported by `/dashboard` directly (they are only imported by onboarding/profile pages), so any delta should be near zero.

    Do NOT introduce any other shadcn primitive in this task (badge, tooltip, progress, etc.) — keep the surface minimal; future tasks add specific ones if and only if they are needed.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`pnpm-lock.yaml` includes the three new deps; six shadcn UI files exist; `pnpm build` is green; `/dashboard` First Load JS recorded in commit message.</done>
</task>

<task type="auto">
  <name>Task P2-B.2: Shared Zod schemas + TS TDEE mirror in frontend/src/lib</name>
  <files>frontend/src/lib/zod-schemas.ts, frontend/src/lib/tdee.ts</files>
  <action>
    Create `frontend/src/lib/zod-schemas.ts` mirroring the Pydantic shapes from Task P2-A.2 — same field names, same constraints (height 100..230, weight 30..300, age 13..100, kg 20..400, etc.), same enum values (sex, locale, activity_level, primary_goal). Export `profileCreateSchema`, `profileUpdateSchema`, `weightLogSchema` plus `z.infer<typeof ...>` types. Add a comment block at the top citing `shared/schemas/profile.schema.json` and `shared/schemas/weight-log.schema.json` as the source of truth — per D-SHARED-SCHEMA-MANUAL-MIRROR in 02-CONTEXT.md, we are mirroring by hand for v1 rather than codegen (defer codegen until a third stack joins).

    Create `frontend/src/lib/tdee.ts` as the client-side preview function. It mirrors `backend/app/lib/tdee.py` EXACTLY — same constants `ACTIVITY_FACTORS`, `KCAL_FLOORS`, same rounding behaviour, same protein formula. Used for the "your daily target is X kcal" preview on screen 2 of onboarding and on the /profile edit page. The displayed number on /dashboard always comes from the server response, not from this function — the client function is preview-only and is recomputed on every keystroke for UX.

    Export `bmrMifflinStJeor`, `tdee`, `dailyKcalTarget`, `dailyProteinGTarget` with TS types matching the Python `Literal` types.

    No tests in this task — the math is verified server-side in P2-A.1, and any client/server divergence will surface in the P2-F.1 smoke test (the displayed preview should match the post-save target).
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit</automated>
  </verify>
  <done>Both files exist, export the named functions, and `pnpm tsc --noEmit` is clean.</done>
</task>

<task type="auto">
  <name>Task P2-B.3: RHF-bound shadcn wrappers (Input, Select, RadioGroup) for use across onboarding + profile</name>
  <files>frontend/src/components/forms/rhf-input.tsx, frontend/src/components/forms/rhf-select.tsx, frontend/src/components/forms/rhf-radio-group.tsx</files>
  <action>
    Create three thin wrappers that take an RHF `Control<T>` plus a `name: FieldPath<T>` and render the shadcn primitive bound via `Controller`. Each component:
    - `RhfInput`: text/number input with label, error message under it, `aria-invalid` set from `fieldState.invalid`. Props: `{ control, name, label, type, placeholder, suffix? }`. The `suffix` slot shows units (e.g. "cm", "kg").
    - `RhfSelect`: shadcn Select with `<option>` array prop `{ value, label }[]`.
    - `RhfRadioGroup`: shadcn RadioGroup with `{ value, label }[]`.

    These are the ONLY form-binding abstractions Phase 2 needs. Do NOT add a generic `Form` component or copy in `shadcn/form` from the gallery — that adds the entire `react-hook-form` re-export indirection layer for marginal benefit on three forms. Inline simplicity > premature abstraction.

    Per D-INTERFACE-FIRST: these three components are consumed by `onboarding-flow.tsx` (P2-C.1) and `profile-form.tsx` (P2-D.1) — pin their props now so the consumers don't have to round-trip.

    No tests — purely declarative wrappers; visual + integration coverage comes via P2-F.1.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Three components exist; `pnpm build` green.</done>
</task>

---

## Slice C — Onboarding flow + dashboard redirect

<task type="auto">
  <name>Task P2-C.1: /onboarding page + 3-step single-page conditional render</name>
  <files>frontend/src/app/onboarding/page.tsx, frontend/src/app/onboarding/onboarding-flow.tsx, frontend/src/app/onboarding/steps/identity-step.tsx, frontend/src/app/onboarding/steps/body-goal-step.tsx, frontend/src/app/onboarding/steps/privacy-step.tsx, frontend/middleware.ts</files>
  <action>
    Server component `frontend/src/app/onboarding/page.tsx`:
    - Calls `fetch(/api/profile)` server-side with the inbound cookie forwarded (same pattern as `frontend/src/app/dashboard/page.tsx` from Phase 1, lines 28-37).
    - If response is 200 → `redirect("/dashboard")` (user already onboarded).
    - If 401 → `redirect("/sign-in")`.
    - Otherwise (404 / 503) → renders `<OnboardingFlow/>`.

    Client component `onboarding-flow.tsx`:
    - Uses RHF with `profileCreateSchema` as the resolver.
    - `useState<0 | 1 | 2>` for the active step index. NOT React Router multi-step — per D-NO-ROUTER-MULTISTEP, single-page conditional render so back/forward feels instant.
    - Renders one of `<IdentityStep>` / `<BodyGoalStep>` / `<PrivacyStep>` based on the index.
    - Step 1 (Identity): name (text), sex (radio: male/female), age (number 13..100), locale (radio: ghana/diaspora). "Next" button enabled only when `formState.isValid` for these fields (use RHF's `trigger(fields)` on click).
    - Step 2 (Body & Goal): height_cm (number 100..230, suffix cm), weight_kg (number 30..300, step 0.1, suffix kg), activity_level (select with 5 labels — sedentary / lightly active / moderately active / very active / extra active), primary_goal (radio: weight_loss / muscle_gain). Below the form: a LIVE preview card showing `dailyKcalTarget(...)` from `frontend/src/lib/tdee.ts` recomputed on every change via `watch()` — "Your estimated daily target: 2,150 kcal" with the floor disclaimer when applicable. "Next" enabled only when valid.
    - Step 3 (Privacy & Finish): timezone (auto-detect via `Intl.DateTimeFormat().resolvedOptions().timeZone`, override via select of IANA timezones — at minimum Africa/Accra, Europe/London, America/New_York, America/Los_Angeles; render as a free-text input fallback). A disclosure card naming "Anthropic (Claude Sonnet 4.6)" as the meal-image processor with a link to `/privacy`. A required `<Checkbox name="privacy_consent">` ("I understand and consent"). Submit button enabled only when consent is checked AND form is valid.
    - On submit: `POST /api/profile` with the form values; on 201 → `router.push("/dashboard")`; on error → render the error message inline (do not redirect, do not retry automatically).
    - The 3 step files (`identity-step.tsx`, `body-goal-step.tsx`, `privacy-step.tsx`) each receive `{ control, errors, watch? }` as props from the flow component.

    Per D-PRIVACY-DISCLOSURE-PROCESSORS: the disclosure copy MUST name "Anthropic (Claude Sonnet 4.6)" specifically (not just "an LLM provider"). Phase 4 will tighten this further if needed; Phase 2's job is to satisfy AUTH-05.

    Per D-FLOOR-DISCLAIMER-COPY: when the live preview shows a floored kcal value, the disclaimer text is "FitGH is a fitness tracking tool, not medical advice. Targets below {floor} kcal/day are clamped; consult a clinician before pursuing aggressive deficits."

    Extend `frontend/middleware.ts` — add `/onboarding(.*)`, `/profile(.*)`, `/settings(.*)`, `/api/profile(.*)`, `/api/weights(.*)`, `/api/account(.*)` to the `createRouteMatcher` list alongside existing entries. Do not change the `export const config` matcher — it already runs on `/api/*` and excludes static assets.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`/onboarding` builds; route renders 3 conditional steps; "Next" gating works per RHF validation; submit POSTs to `/api/profile`; middleware protects the new routes; `pnpm build` green with the new route in the table.</done>
</task>

<task type="auto">
  <name>Task P2-C.2: BFF /api/profile route (GET + POST + PATCH forwarder)</name>
  <files>frontend/src/app/api/profile/route.ts, frontend/src/lib/api-server.ts</files>
  <action>
    First, refactor the small fetch-Flask-with-Bearer-JWT helper out of `frontend/src/app/api/me/route.ts` into `frontend/src/lib/api-server.ts` as `forwardToFlask(method: string, path: string, body?: unknown): Promise<NextResponse>`:
    - Reads `auth()` from `@clerk/nextjs/server`, returns 401 if `!userId || !token`.
    - Reads `process.env.NEXT_PUBLIC_API_URL`, returns 503 `api_url_not_configured` if absent.
    - Forwards the call with `Authorization: Bearer <token>`, `Content-Type: application/json` (when body), `cache: 'no-store'`.
    - Proxies the upstream status + body through unchanged.
    - Sets `export const dynamic = "force-dynamic"` for any route consuming this helper.

    Update `frontend/src/app/api/me/route.ts` to use the helper (the behaviour stays identical).

    Create `frontend/src/app/api/profile/route.ts` exporting `GET`, `POST`, `PATCH` handlers — each is a one-liner calling `forwardToFlask(...)`. Per the existing api/me pattern (lines 22-53 of frontend/src/app/api/me/route.ts), do NOT re-implement auth here — trust the helper.

    Per D-BFF-PATTERN: the BFF stays a thin pass-through; the browser never holds the Clerk JWT.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Helper exists; `/api/me`, `/api/profile` use it; route table in `pnpm build` shows `/api/profile` as a dynamic route.</done>
</task>

<task type="auto">
  <name>Task P2-C.3: /dashboard rewrites — profile-or-redirect + target card</name>
  <files>frontend/src/app/dashboard/page.tsx, frontend/src/app/dashboard/target-card.tsx</files>
  <action>
    Rewrite `frontend/src/app/dashboard/page.tsx`:
    - Still a server component.
    - Calls `fetch(${origin}/api/profile, { headers: { cookie: ... } })` (same pattern as the existing `/api/me` call in lines 28-37 of the Phase 1 file).
    - If 401 → `redirect("/sign-in")`.
    - If 404 → `redirect("/onboarding")` (this is the Phase 2 redirect-if-no-profile gate).
    - If 200 → renders the new layout: header with sign-out, `<TargetCard profile={profile} />`, weight-log card (P2-D.2), recent-weights list (P2-D.2).
    - Drop the old "Phase 1 walking skeleton" placeholder copy.

    Create `frontend/src/app/dashboard/target-card.tsx`:
    - Server component (no interactivity).
    - Displays `daily_kcal_target` as a large numeric ("2,150 kcal/day").
    - If `floor_hit === true` renders the clinician disclaimer text (per D-FLOOR-DISCLAIMER-COPY).
    - If `primary_goal === "muscle_gain"` renders a second card with `daily_protein_g_target` ("112 g protein").
    - If `primary_goal === "weight_loss"` does NOT render the protein card (per the must_have "weight-loss users do not see the protein card").
    - Includes a small Tailwind-styled progress placeholder div (static — Phase 5 makes it dynamic Rive ring).

    Footer (component-inline or in `layout.tsx`, your call): one line linking to `/privacy`.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`/dashboard` build is green; manual route check in `pnpm build` shows no significant First Load JS regression (record measurement in commit); page redirects correctly when profile is absent (verified end-to-end in P2-F.1).</done>
</task>

---

## Slice D — Profile edit + weight log

<task type="auto">
  <name>Task P2-D.1: /profile edit page</name>
  <files>frontend/src/app/profile/page.tsx, frontend/src/app/profile/profile-form.tsx</files>
  <action>
    Server component `frontend/src/app/profile/page.tsx`:
    - Fetches `/api/profile`; if 404 → `redirect("/onboarding")`; if 401 → `redirect("/sign-in")`; otherwise renders `<ProfileForm initial={profile} />`.

    Client component `profile-form.tsx`:
    - Reuses `RhfInput`, `RhfSelect`, `RhfRadioGroup` from P2-B.3.
    - RHF + `zodResolver(profileUpdateSchema)`.
    - `defaultValues` from the `initial` prop.
    - All onboarding fields are editable EXCEPT `privacy_consent` (not in `profileUpdateSchema`) and `clerk_id` (server-only).
    - Live target preview card (same `dailyKcalTarget` from `lib/tdee.ts`) under the form, updated on every keystroke via `watch()`.
    - "Save changes" button → PATCH /api/profile → on 200 render a success toast (sonner is already in the project from Phase 1) and refresh the displayed numbers.
    - Cancel button → `router.back()`.

    Per D-EDIT-REUSES-COMPONENTS: same building blocks as onboarding, single form on one page (no step gating in edit mode).
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`/profile` builds; form renders pre-filled; PATCH wired; preview number recomputes on input.</done>
</task>

<task type="auto">
  <name>Task P2-D.2: Dashboard weight-log card + history list + BFF /api/weights</name>
  <files>frontend/src/app/dashboard/weight-log-card.tsx, frontend/src/app/dashboard/page.tsx, frontend/src/app/api/weights/route.ts</files>
  <action>
    Create `frontend/src/app/api/weights/route.ts` exporting `GET` and `POST`, both via `forwardToFlask(...)` from `frontend/src/lib/api-server.ts`.

    Create `frontend/src/app/dashboard/weight-log-card.tsx` as a client component:
    - Receives `recentWeights: WeightLog[]` as a prop (server-fetched).
    - Renders a single numeric input (kg, step 0.1) + "Log" button. Submit → POST /api/weights → on success, calls `router.refresh()` to re-fetch the server component data (so the new target reflects the updated weight, per the P2-A.4 server-side recompute).
    - Below the input, shows the most recent 7 entries as a simple list ("75.4 kg on 2026-05-13 09:24"). A "View all" link reveals up to 30 (toggle local state — no separate route needed for v1).

    Update `frontend/src/app/dashboard/page.tsx`:
    - Also fetch `/api/weights?limit=30` server-side in parallel with `/api/profile` (use `Promise.all`).
    - Pass the result to `<WeightLogCard recentWeights={entries} />`.

    Per D-WEIGHTLOG-ON-DASHBOARD: the entry input lives on /dashboard (not /profile) so daily logging is one click away. This honours PROF-07 ("user can log a weight entry") and the must_have "User can log a weight on /dashboard".
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Dashboard renders weight log card + history; `/api/weights` route shows in build table; POSTing a weight triggers `router.refresh()` and the target card updates.</done>
</task>

<task type="auto">
  <name>Task P2-D.3: BFF /api/account DELETE (forward + post-success signOut)</name>
  <files>frontend/src/app/api/account/route.ts</files>
  <action>
    Create `frontend/src/app/api/account/route.ts` exporting a `DELETE` handler:
    - Calls `forwardToFlask("DELETE", "/me")`.
    - Returns whatever Flask returned (200 / 502 / 401).
    - The handler does NOT call Clerk's `signOut()` server-side here — the client component triggers `await clerk.signOut()` after seeing the 200 response (clearer separation; the BFF stays a forwarder). The Clerk auth record deletion is server-side in Flask (P2-A.5); the *session cookie* clear happens in the browser.

    Per D-DELETE-CASCADE-SHAPE: a single round-trip is enough — Flask deletes the Clerk user via SDK + Mongo data; the client signs out locally. No webhook involved.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Route exists; build green; `/api/account` shows in route table as a dynamic DELETE route.</done>
</task>

---

## Slice E — Privacy + delete account UI

<task type="auto">
  <name>Task P2-E.1: /privacy stub page</name>
  <files>frontend/src/app/privacy/page.tsx</files>
  <action>
    Static server component at `frontend/src/app/privacy/page.tsx`. Plain prose (Tailwind typography) covering:
    - Heading: "FitGH Privacy Disclosure — v1 (stub)".
    - One paragraph stating this is a stub and the full policy is in Phase 7.
    - A "Data Processors" section listing FOUR processors with one-line descriptions:
      - Anthropic (Claude Sonnet 4.6) — meal photos sent to the vision model for kcal estimation (Phase 4 onwards; not active yet in Phase 2).
      - Clerk — authentication identity, email, sign-in methods.
      - MongoDB Atlas — profile, weight history, meal logs (when added in Phase 3).
      - Render — hosting for the frontend and backend.
    - A "What we don't do" section:
      - We do NOT retain meal images server-side beyond the time needed to call the LLM (this becomes true in Phase 4; Phase 2 has no images yet, but the policy stance is stated now).
      - We do NOT share your data with advertisers.
    - A link back to `/dashboard` and to `mailto:` for data requests (placeholder address).

    Per AUTH-05 success criterion: this page must be linked from onboarding screen 3 AND from a footer reachable on every page. The onboarding link is already wired in P2-C.1; the global footer link is added in `frontend/src/app/layout.tsx` (one-line edit) within this task.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`/privacy` renders the four named processors; footer link reaches it from every page; build is green.</done>
</task>

<task type="auto">
  <name>Task P2-E.2: /settings page + delete-account modal cascade</name>
  <files>frontend/src/app/settings/page.tsx, frontend/src/app/settings/delete-account-button.tsx</files>
  <action>
    Server component `frontend/src/app/settings/page.tsx`:
    - Auth-protected via middleware.ts (added in P2-C.1).
    - Renders a small heading + the `<DeleteAccountButton/>` client component. No other settings in v1.

    Client component `delete-account-button.tsx`:
    - Renders a "Delete account" destructive-variant button.
    - Click → opens a shadcn `<Dialog>` confirmation modal: "This will permanently delete your FitGH profile, weight history, and Clerk account. This cannot be undone."
    - The Dialog has a typed confirmation input (user must type "DELETE" to enable the destructive button) — defence-in-depth UX against accidental clicks.
    - On confirm: `await fetch("/api/account", { method: "DELETE" })`. If response 200 → `await clerkClient.signOut()` (or `useClerk().signOut()` from `@clerk/nextjs`) → `router.push("/sign-in")`. If 502 (clerk_delete_failed) → show an inline error "Your data was deleted, but auth deletion failed — contact support@fitgh.app" and DO NOT sign the user out (they should still be able to retry from this page).

    Per the must_have "user is signed out and lands on /sign-in", the signOut → push("/sign-in") chain is the success path.

    No automated test for this modal in this plan — coverage comes via P2-F.1 end-to-end smoke (the alternative would be Playwright, which is a bigger Phase 6/7 investment).
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`/settings` builds; modal renders; the typed-confirmation gate works; cascade-delete and signOut wired.</done>
</task>

---

## Slice F — Verification + traceability

<task type="auto">
  <name>Task P2-F.1: End-to-end local smoke + REQUIREMENTS.md traceability update</name>
  <files>.planning/REQUIREMENTS.md</files>
  <action>
    Manual end-to-end smoke against local Flask + local Next.js (Phase 1 already deployed on Render; this is a developer-loop check, not a production check):

    1. `cd backend && .venv/Scripts/python.exe -m pytest -q` — full suite green; count is ≥25 (target post-Phase-2: ~67 per P2-A.5's done criterion).
    2. `cd frontend && pnpm build` — green; record route table in commit message; manual check that `/dashboard` First Load JS is still ≤180 kB gzipped (PERF-01 manual gate per Phase 1's deferral note).
    3. `cd frontend && pnpm tsc --noEmit` — clean.
    4. Start local Flask (`python -m flask --app app:create_app run -p 8000`) and local Next.js (`pnpm dev`). Real Clerk dev keys + real Atlas creds in `.env.local`.
    5. Sign up a fresh user → land on /dashboard → assert auto-redirect to /onboarding (profile is missing).
    6. Complete 3 screens of onboarding (identity → body+goal → privacy with consent) → submit → assert landing on /dashboard with kcal target visible.
    7. Verify floor disclaimer renders when entering small-female / sedentary / weight-loss combo (e.g. female / 45 kg / 155 cm / 65 y / sedentary / weight_loss).
    8. Verify muscle_gain primary_goal renders the protein-target card; switch via /profile to weight_loss → save → protein card disappears.
    9. Log a weight on /dashboard → see history list update; assert the displayed kcal target reflects the new weight (server-side recompute on POST /weights from P2-A.4).
    10. Edit one profile field (e.g. activity_level sedentary → moderately_active) → save → assert target recomputed.
    11. Navigate to /privacy → verify the four processors are listed (Anthropic, Clerk, MongoDB Atlas, Render).
    12. Navigate to /settings → click Delete account → type "DELETE" → confirm → assert redirected to /sign-in → assert Atlas `profiles`, `weight_logs`, `users` for the test clerk_id are empty (mongosh check) → assert the Clerk dashboard shows the user removed.

    Then update `.planning/REQUIREMENTS.md` traceability table — change `Pending` to `Complete` for AUTH-04, AUTH-05, PROF-01, PROF-02, PROF-03, PROF-04, PROF-05, PROF-06, PROF-07 (9 IDs total). Do NOT mark anything else; even if Phase 1's deferred IDs (OBS-01, SEC-01 etc.) happen to be touched, they stay as `Deferred` per the 2026-05-12 rewrite.

    Per the must_have list, every item should pass the manual check. If anything fails, capture in the SUMMARY.md (Phase 2 will produce one at end-of-phase) as a deviation and fix in a follow-up task before marking the requirement Complete.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest -q && cd ../frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>All 12 manual smoke steps pass; backend pytest count ≥25; frontend build green; REQUIREMENTS.md updated with 9 IDs marked Complete.</done>
</task>

---

## Source Coverage Audit

| Source | Item | Plan Coverage |
|--------|------|---------------|
| GOAL (ROADMAP Phase 2) | ≤3-screen onboarding under 60s, daily target visible | Slice C (P2-C.1 / P2-C.3) |
| GOAL | Edit profile post-onboarding | Slice D (P2-D.1) |
| GOAL | Weight log + history | Slice A (P2-A.4) + Slice D (P2-D.2) |
| GOAL | Privacy consent before onboarding finishes | Slice C (P2-C.1) + Slice E (P2-E.1) |
| GOAL | Account deletion path | Slice A (P2-A.5) + Slice D (P2-D.3) + Slice E (P2-E.2) |
| REQ | AUTH-04 (delete account cascade GDPR) | P2-A.5 + P2-D.3 + P2-E.2 |
| REQ | AUTH-05 (privacy disclosure at sign-up; LLM provider named) | P2-C.1 + P2-E.1 |
| REQ | PROF-01 (≤3-screen onboarding capturing 9 fields) | P2-A.2 + P2-A.3 + P2-C.1 |
| REQ | PROF-02 (primary_goal select) | P2-A.2 + P2-C.1 |
| REQ | PROF-03 (BMR via Mifflin-St Jeor + TDEE via activity factor) | P2-A.1 |
| REQ | PROF-04 (kcal target with floor + disclaimer) | P2-A.1 + P2-A.3 + P2-C.3 |
| REQ | PROF-05 (protein target 1.6 g/kg for muscle gain) | P2-A.1 + P2-C.3 |
| REQ | PROF-06 (edit profile, targets recompute) | P2-A.3 + P2-D.1 |
| REQ | PROF-07 (log weight, history persisted) | P2-A.4 + P2-D.2 |
| CONTEXT D-NO-ROUTER-MULTISTEP | Single-page conditional render | P2-C.1 |
| CONTEXT D-NO-WEBHOOKS | DELETE /me cascade via SDK | P2-A.5 |
| CONTEXT D-SHARED-SCHEMA-MANUAL-MIRROR | Manual Zod mirror, no codegen | P2-B.2 |
| CONTEXT D-LOCALE-BUCKETS | Single diaspora bucket, no country picker | P2-A.2 + P2-C.1 |
| CONTEXT D-STORAGE-NEW-COLLECTIONS | Separate profiles + weight_logs collections | P2-A.2 |
| CONTEXT D-PRIVACY-DISCLOSURE-PROCESSORS | Name Anthropic + Clerk + Atlas + Render | P2-C.1 + P2-E.1 |
| CONTEXT D-EDIT-REUSES-COMPONENTS | Same RHF components in /profile and /onboarding | P2-D.1 |

**All items covered. No gaps. No deferrals beyond those already locked in ROADMAP (Phases 3+).**

## Test Plan

- **Backend pytest count:** Phase 1 baseline 22 → Phase 2 target ≥25 (concrete projection ≈67: TDEE ~12 + models ~10 + profile routes ~12 + weights ~6 + delete ~5 + Phase 1 retained 22).
- **Frontend:** `pnpm tsc --noEmit` + `pnpm build` are the v1 gates (no Jest yet; no Playwright). Visual + flow verification is the manual smoke in P2-F.1.
- **Manual smoke (12 steps in P2-F.1)** is the success-criteria check; it must pass before requirements are marked Complete.

## Notes for the Executor

- The Render auto-deploy from Phase 1 is still in force: `git push main` will redeploy both frontend and backend after each commit. There is no need to "deploy Phase 2"; the existing `render.yaml` already covers both services. If a Phase 2 commit fails Render's build (e.g. a Pydantic import error in `app/__init__.py`), the rollback is automatic per Phase 1's setup.
- Atlas indexes for `weight_logs` and `profiles` are NOT created in code (no `ensure_index` on module load — Phase 1 pattern). After P2-A.4 lands, create them once via `mongosh` against the production cluster: `db.weight_logs.createIndex({user_id: 1, logged_at: -1})` and `db.profiles.createIndex({clerk_id: 1}, {unique: true})`. Capture in the eventual SUMMARY.md as an operator-side action.
- The `CLERK_AUTHORIZED_PARTIES` env var is already set per Phase 1's `.env.example`; no change needed for Phase 2.
- Phase 2 does NOT add any new env vars vs Phase 1.

## Output

After completion, create `.planning/phases/02-onboarding-profile-targets/02-SUMMARY.md` using the standard Phase template, including the deviations encountered, the actual final pytest count, the actual `/dashboard` First Load JS measurement, and the operator-side index creation as a follow-up.
