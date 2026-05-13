---
phase: 03-meal-log-ghana-table
plan: 03
type: execute
wave: 1
depends_on: []
files_modified:
  # Backend — models + seeds + helpers + db wiring
  - backend/app/models/__init__.py
  - backend/app/models/ghana_food.py
  - backend/app/models/meal.py
  - backend/app/lib/meals.py
  - backend/app/db.py
  - backend/seeds/__init__.py
  - backend/seeds/ghana_foods.json
  - backend/scripts/__init__.py
  - backend/scripts/seed_ghana_foods.py
  - backend/tests/test_meal_models.py
  - backend/tests/test_meal_helpers.py
  - backend/tests/test_ghana_foods_seed.py
  # Backend — routes
  - backend/app/routes/foods.py
  - backend/app/routes/meals.py
  - backend/app/__init__.py
  - backend/tests/conftest.py
  - backend/tests/test_foods_routes.py
  - backend/tests/test_meals_routes.py
  # Shared JSON Schemas
  - shared/schemas/ghana-food.schema.json
  - shared/schemas/meal.schema.json
  # Frontend — Zod + BFF
  - frontend/src/lib/zod-schemas.ts
  - frontend/src/app/api/foods/route.ts
  - frontend/src/app/api/meals/route.ts
  - frontend/src/app/api/meals/[id]/route.ts
  - frontend/middleware.ts
  # Frontend — shadcn primitives + meal-log modal
  - frontend/package.json
  - frontend/src/components/ui/command.tsx
  - frontend/src/components/ui/slider.tsx
  - frontend/src/components/ui/popover.tsx
  - frontend/src/app/dashboard/meal-log-modal.tsx
  - frontend/src/app/dashboard/food-search.tsx
  - frontend/src/app/dashboard/component-chip.tsx
  # Frontend — dashboard integration
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/dashboard/kcal-pill.tsx
  - frontend/src/app/dashboard/todays-meals-list.tsx
  - frontend/src/app/dashboard/log-meal-cta.tsx
  # Frontend — history route
  - frontend/src/app/history/page.tsx
  - frontend/src/app/history/day-group.tsx
  # CI — nightly backup
  - .github/workflows/nightly-backup.yml
  # Traceability
  - .planning/REQUIREMENTS.md
autonomous: true
requirements:
  - LOG-01
  - LOG-02
  - LOG-03
  - LOG-04
  - LOG-05
  - LOG-06
  - LOG-07
  - LOG-08
  - DATA-01

must_haves:
  truths:
    - "A signed-in user can type 'jollof' (or 'banku', 'waakye', 'kenkey', 'kelewele' etc.) into the meal-log search box and pick a dish from the 25-entry Ghana catalogue; results match name + alt_names substring-insensitively and are ranked by relevance"
    - "User can build a single meal as multiple components (e.g. banku + tilapia + shito) each with its own portion slider (10g increments, range 10–800g) defaulting to the dish's first portion_default; running meal total kcal + total protein update live as sliders move"
    - "On Save, the meal is persisted to the meals collection in the day-1 multi-component shape with source='manual', kcal_low/high=null, confidence=null, kcal_point computed server-side as round(kcal_per_100g × portion_g / 100), total_kcal = sum(components.kcal_point), ai_metadata=null"
    - "Dashboard shows today's running kcal-progress pill: 'X / Y kcal • Z remaining' (Y = profile.daily_kcal_target, X = sum of today's meals.total_kcal in user's timezone); pill colour is RED if X > Y, AMBER if X > Y×0.9, GREEN otherwise — no animation (Phase 5)"
    - "Dashboard shows a 'Today's meals' list below the pill — each meal as {logged_at time, component chips, total_kcal} with an Edit button (re-opens the modal pre-filled) and a Delete button (confirm-then-DELETE); both actions refresh the pill + list via router.refresh()"
    - "User can PATCH a logged meal (change components or portion_g) and the server recomputes total_kcal + total_protein_g atomically; DELETE removes the meal and the day's total is recomputed implicitly on next GET"
    - "User can navigate to /history and see the last 30 days grouped by day (each day showing date header + day-total kcal + list of meals); empty days are omitted; server-rendered with no client-side state"
    - "Meal logged_at defaults to now() but the modal allows backdating up to 7 days; backend rejects logged_at older than 7 days or in the future (>5 min skew) with 422"
    - "A GitHub Actions cron workflow (.github/workflows/nightly-backup.yml) runs nightly at 02:00 UTC, executes mongodump against MONGODB_URI_BACKUP, gzips the archive, and uploads it as a GH Actions artifact with 90-day retention"
    - "Free-text component entry (no matched_food_id) is allowed only when the user supplies a manual kcal value; backend persists matched_food_id=null + the user-supplied kcal as kcal_point with source='user_corrected'; default UX always picks a matched food"
  artifacts:
    - path: "backend/app/models/ghana_food.py"
      provides: "Pydantic v2 GhanaFood + PortionDefault models for the read-only ghana_foods catalogue"
      exports: ["GhanaFood", "PortionDefault", "Category", "FoodSource"]
    - path: "backend/app/models/meal.py"
      provides: "Pydantic v2 Component + Meal + MealCreate + MealUpdate models for the multi-component meal shape"
      exports: ["Meal", "MealCreate", "MealUpdate", "Component", "ComponentCreate", "MealSource", "ComponentSource"]
    - path: "backend/app/lib/meals.py"
      provides: "Pure helpers: compute_kcal_for_component(food, portion_g) + compute_protein_for_component + recompute_meal_totals(components)"
      exports: ["compute_kcal_for_component", "compute_protein_for_component", "recompute_meal_totals", "PORTION_MIN_G", "PORTION_MAX_G", "PORTION_STEP_G", "BACKDATE_MAX_DAYS"]
    - path: "backend/seeds/ghana_foods.json"
      provides: "25-entry FAO/INFOODS-sourced Ghana food catalogue — staples, soups, proteins, sides per CONTEXT category coverage"
    - path: "backend/scripts/seed_ghana_foods.py"
      provides: "Idempotent seeder: read JSON, upsert each entry by food_id, log added/updated/unchanged counts, create indexes (food_id unique + name/alt_names text)"
      exports: ["main", "seed"]
    - path: "backend/app/db.py"
      provides: "Extended with ghana_foods + meals collection singletons (same pattern as profiles + weight_logs)"
    - path: "backend/app/routes/foods.py"
      provides: "GET /foods?q=&limit= read-only search over ghana_foods; substring + alt_names match; relevance-ranked; limit 1..25 (default 10)"
      exports: ["bp"]
    - path: "backend/app/routes/meals.py"
      provides: "POST /meals (create), GET /meals?date=YYYY-MM-DD (single day), GET /meals?days=30 (history grouped), PATCH /meals/<id>, DELETE /meals/<id>"
      exports: ["bp"]
    - path: "shared/schemas/ghana-food.schema.json"
      provides: "JSON Schema for GhanaFood — source of truth for FE Zod + BE Pydantic"
    - path: "shared/schemas/meal.schema.json"
      provides: "JSON Schema for Meal — source of truth, includes the day-1 vision fields (kcal_low/high/confidence/ai_metadata) as nullable so Phase 4 fills them without a schema change"
    - path: "frontend/src/lib/zod-schemas.ts"
      provides: "Extended with ghanaFoodSchema, componentCreateSchema, mealCreateSchema, mealUpdateSchema + the GhanaFood/Meal response types"
      exports: ["ghanaFoodSchema", "componentCreateSchema", "mealCreateSchema", "mealUpdateSchema", "MealResponse", "GhanaFoodResponse", "MEAL_SOURCES", "COMPONENT_SOURCES"]
    - path: "frontend/src/app/api/foods/route.ts"
      provides: "BFF GET /api/foods forwarder via forwardToFlask"
    - path: "frontend/src/app/api/meals/route.ts"
      provides: "BFF GET/POST /api/meals forwarder via forwardToFlask"
    - path: "frontend/src/app/api/meals/[id]/route.ts"
      provides: "BFF PATCH/DELETE /api/meals/[id] forwarder via forwardToFlask (path includes the id)"
    - path: "frontend/src/components/ui/command.tsx"
      provides: "shadcn Command primitive (wraps cmdk) for the food-search typeahead"
    - path: "frontend/src/components/ui/slider.tsx"
      provides: "shadcn Slider primitive (wraps @radix-ui/react-slider) for portion sliders"
    - path: "frontend/src/components/ui/popover.tsx"
      provides: "shadcn Popover primitive — used to host the Command search inside the meal-log modal"
    - path: "frontend/src/app/dashboard/meal-log-modal.tsx"
      provides: "Client component — Dialog hosting FoodSearch + Component chips + portion sliders + running total + Save → POST /api/meals; supports edit mode when initial={meal} prop is passed → PATCH /api/meals/[id]"
    - path: "frontend/src/app/dashboard/food-search.tsx"
      provides: "Client component — debounced (200ms) fetch /api/foods?q= via Command primitive; displays name + first portion_default + kcal_per_100g; onSelect emits the matched GhanaFood to the modal"
    - path: "frontend/src/app/dashboard/component-chip.tsx"
      provides: "Client component — single component row: chip with food name + Slider (step=10, min=10, max=800) + live kcal_point + remove button; emits onChange with new portion_g"
    - path: "frontend/src/app/dashboard/kcal-pill.tsx"
      provides: "Server component — 'X / Y kcal • Z remaining' pill; bg colour RED/AMBER/GREEN per X vs Y thresholds (computed in JSX, no client JS)"
    - path: "frontend/src/app/dashboard/todays-meals-list.tsx"
      provides: "Client component — list of today's meals; each row has Edit (opens MealLogModal initial=meal) and Delete (confirm() → DELETE /api/meals/[id] → router.refresh())"
    - path: "frontend/src/app/dashboard/log-meal-cta.tsx"
      provides: "Client component — 'Log meal' button that opens the MealLogModal in create mode"
    - path: "frontend/src/app/dashboard/page.tsx"
      provides: "Extended — also fetches /api/meals?date={today_in_tz} in parallel with profile/weights; passes to KcalPill + TodaysMealsList + LogMealCta"
    - path: "frontend/src/app/history/page.tsx"
      provides: "Server component — fetches /api/meals?days=30 and renders DayGroup per non-empty day, newest first"
    - path: "frontend/src/app/history/day-group.tsx"
      provides: "Server component — date header + total kcal + meals list (re-uses the chip rendering, read-only — no edit/delete on /history)"
    - path: "frontend/middleware.ts"
      provides: "Extended createRouteMatcher to protect /history(.*), /api/foods(.*), /api/meals(.*) in addition to existing entries"
    - path: ".github/workflows/nightly-backup.yml"
      provides: "GH Actions cron (0 2 * * *) + manual workflow_dispatch — installs mongodb-database-tools, runs mongodump --gzip --archive against MONGODB_URI_BACKUP secret, uploads via actions/upload-artifact@v4 with 90-day retention"
  key_links:
    - from: "frontend/src/app/dashboard/page.tsx"
      to: "/api/meals?date={today}"
      via: "server-side fetch with cookie forward (same fetchSameOrigin pattern as profile/weights)"
      pattern: "fetch.*api/meals.*date="
    - from: "frontend/src/app/api/foods/route.ts"
      to: "backend GET /foods"
      via: "forwardToFlask('GET', `/foods${search}`) one-liner"
      pattern: "forwardToFlask.*foods"
    - from: "frontend/src/app/api/meals/route.ts"
      to: "backend POST /meals + GET /meals"
      via: "forwardToFlask one-liners"
      pattern: "forwardToFlask.*meals"
    - from: "frontend/src/app/api/meals/[id]/route.ts"
      to: "backend PATCH/DELETE /meals/<id>"
      via: "forwardToFlask('PATCH'/'DELETE', `/meals/${params.id}`)"
      pattern: "forwardToFlask.*meals/.*\\$\\{"
    - from: "backend/app/routes/meals.py"
      to: "db_mod.meals + db_mod.ghana_foods + app.lib.meals.recompute_meal_totals"
      via: "@require_auth → look up each component's food → compute kcal_point via helper → upsert"
      pattern: "recompute_meal_totals"
    - from: "frontend/src/app/dashboard/meal-log-modal.tsx"
      to: "/api/meals (POST) and /api/meals/[id] (PATCH)"
      via: "RHF + fetch → router.refresh() on success"
      pattern: "fetch.*api/meals.*(POST|PATCH)"
    - from: "backend/scripts/seed_ghana_foods.py"
      to: "db.ghana_foods.update_one + db.ghana_foods.create_index"
      via: "operator-run script — idempotent upsert keyed on food_id + index creation"
      pattern: "create_index.*food_id"
    - from: ".github/workflows/nightly-backup.yml"
      to: "mongodump → actions/upload-artifact"
      via: "cron schedule '0 2 * * *' + MONGODB_URI_BACKUP secret + 90-day retention"
      pattern: "mongodump.*gzip.*archive"
---

# Phase 3 Plan 03 — Manual Meal Log + Ghana Table

## Phase Goal

Without any AI involvement, a user can search the 25-dish Ghana food catalogue, log a meal as one or more components with portion sliders, see today's running total + remaining-kcal pill on the dashboard, and look back through the last 30 days — proving the **multi-component `meals` schema** works end-to-end before vision lands on top of it in Phase 4.

(From ROADMAP.md Phase 3.)

## Success Criteria (from ROADMAP.md)

1. A user can type "jollof" / "banku" / "waakye" into a meal-log search box and pick a dish from the 25-entry Ghana food catalogue, with FAO/INFOODS-sourced kcal/100g and Ghana + diaspora portion defaults visible.
2. A user can log a single meal as **multiple components** — each with its own portion slider showing culturally meaningful defaults ("1 ball of banku ≈ 200 g") — and the meal's total kcal + total protein are computed and displayed.
3. The dashboard shows today's meals as a list with a running daily total and a "remaining kcal" pill (target − consumed); a user can edit or delete a logged meal and the daily total updates.
4. A user can scroll back through at least the last 30 days of meal history grouped by day.
5. A nightly `mongodump` runs against Atlas; the most recent dump is verifiable from the operator side. **Implementation:** GitHub Actions cron + actions-artifact storage (90-day retention) per CONTEXT.md DATA-01 simplification; R2 is deferred (Phase 7 / post-MVP).

## Inherited Constraints (do not violate)

- **Multi-component schema is day 1** (ROADMAP Hard Constraint #3). The `meals` collection persists the FULL shape including `components[].{kcal_low, kcal_high, confidence, source}` and `ai_metadata`; Phase 3 writes `null` into the vision-only slots so Phase 4 fills them without a schema change. **There is no separate `ai_meals` collection.**
- **No AI / image / Anthropic work** — Phase 4 owns the vision pipeline. Phase 3 must NOT import the anthropic SDK, must NOT add an image upload route, must NOT compress images client-side. The only forward-compat touchpoint is the nullable shape.
- **Render-only architecture** (memory/render-only-rewrite.md). No Sentry FE wizard, no Vercel Analytics, no size-limit CI gate, no R2/S3 blob store, no Cloudflare in front. GH Actions artifact storage is the v1 backup target.
- **No `create_index` on module load** (Phase 1 invariant). All indexes live inside the seeder script + a documented operator follow-up in the SUMMARY.
- **Tailwind v4 CSS-first** — no `tailwind.config.js`. New shadcn primitives via `pnpm dlx shadcn@latest add command slider popover` (v4 marker preserved in `components.json`).
- **Reuse Phase 2 patterns exactly** — `forwardToFlask` BFF (frontend/src/lib/api-server.ts), `@require_auth` + `app.db as db_mod` Flask route shape, mongomock fixtures in conftest, JSON Schema generated via `Model.model_json_schema()`, Zod mirror by hand (D-SHARED-SCHEMA-MANUAL-MIRROR), shadcn CLI for new UI primitives, single-page React (no router multi-step), SI units only.
- **Atomic commits + push to origin/main after each task** — Render auto-deploys exercise the changes incrementally (the Phase 1 deploy loop is already wired).

## Slice Overview

| Slice | Theme | Tasks |
|-------|-------|-------|
| A | Backend — models, JSON schemas, seed file, seeder script, kcal helpers, db.py wiring | 5 |
| B | Backend — `/foods` + `/meals` Flask routes (with backdating + free-text edge cases) | 4 |
| C | Frontend — Zod mirror, shadcn primitives (command/slider/popover), MealLogModal + FoodSearch + ComponentChip + BFF forwarders | 3 |
| D | Frontend — Dashboard integration (KcalPill, TodaysMealsList, LogMealCta wiring, page.tsx fetch in parallel) | 3 |
| E | Frontend — `/history` route (30-day server-rendered grouping) | 1 |
| F | CI — `.github/workflows/nightly-backup.yml` + REQUIREMENTS.md traceability flip | 2 |

Total: **18 tasks**. Granularity matches Phase 2 (17 tasks for 9 reqs); Phase 3 is shipping 9 reqs (LOG-01..08 + DATA-01) and threads the day-1 multi-component schema through both stacks plus a CI workflow, hence one more task than Phase 2.

Cross-slice ordering: A → B (needs A) → C (needs A's shared schemas + B's routes) → D (needs C's modal + B's routes) → E (needs B's days=30 endpoint + D's rendering primitives) → F (needs all of A–E for the traceability flip).

## Threat Register (Phase 3)

| Threat ID  | Category               | Component                                                | Disposition | Mitigation Plan |
|------------|------------------------|----------------------------------------------------------|-------------|-----------------|
| T-03-01    | Spoofing               | POST/PATCH/DELETE /meals                                 | mitigate    | All meal routes `@require_auth`-decorated; `user_id` is always `g.clerk_user_id` from the verified JWT, never read from body, query, or path. Test asserts a body `{"user_id": "user_attacker"}` is ignored. |
| T-03-02    | Tampering              | Client-supplied kcal_point on POST/PATCH                 | mitigate    | `MealCreate.Component` accepts only `{food_id, portion_g}` (matched) OR `{name, kcal_point}` (free-text); `kcal_point`, `protein_g_point`, `total_kcal`, `total_protein_g` are NEVER read from a matched-food component — all server-recomputed via `app.lib.meals.compute_kcal_for_component`. Pydantic `extra="forbid"` rejects unknown fields. Test asserts a body with `kcal_point: 99999` on a matched component is overridden. |
| T-03-03    | Information Disclosure | Cross-user meal reads on GET /meals + PATCH/DELETE       | mitigate    | All queries filter by `user_id == g.clerk_user_id`. PATCH/DELETE first `find_one({_id: id, user_id: g.clerk_user_id})` — a 404 is returned (not 403) if the meal belongs to another user, to avoid leaking existence. Test seeds two users' meals and asserts isolation. |
| T-03-04    | Tampering              | logged_at backdating                                     | mitigate    | Backend validator: `logged_at` must be ≤ now + 5 min skew AND ≥ now − 7 days. `BACKDATE_MAX_DAYS = 7` from `app.lib.meals`. 422 on violation. Test covers `logged_at = now + 1h` and `logged_at = now - 8d`. |
| T-03-05    | Denial of Service      | GET /foods?q= unbounded scan                             | mitigate    | `limit` query param clamped to 1..25 (default 10). The `ghana_foods` collection has 25 entries total — a full scan is bounded. Compound the bound with the text index created by the seeder. No external rate limit beyond Flask's default (M0 + maxPoolSize=10 already caps blast radius). |
| T-03-06    | Denial of Service      | GET /meals?days= unbounded range                         | mitigate    | `days` clamped to 1..30 (default 30); `date=` accepts only `YYYY-MM-DD` strings parseable via `datetime.strptime`. Server uses the `(user_id, logged_at)` compound index (operator-created after deploy per the same pattern as Phase 2's `(user_id, logged_at desc)` index on weight_logs). |
| T-03-07    | Tampering              | Forging matched_food_id to a deleted/unknown food        | mitigate    | POST/PATCH path looks up each `food_id` in `ghana_foods` BEFORE write; 422 `unknown_food_id` if any is missing. Test seeds one food + tries to POST with a different `food_id`. |
| T-03-08    | Repudiation            | mongodump backup integrity                               | accept      | GH Actions artifact storage is not encrypted at rest beyond GH's own encryption; archive retention is 90 days. Acceptable for v1 per CONTEXT.md DATA-01. Phase 7 / v2 may add R2 + GPG-encrypted offsite. The workflow run history itself is the audit log. |
| T-03-09    | Information Disclosure | MONGODB_URI in workflow logs                             | mitigate    | The URI is consumed exclusively from the `MONGODB_URI_BACKUP` GH Actions secret (separate from the runtime `MONGODB_URI`); the workflow MUST NOT `echo $MONGODB_URI_BACKUP` and MUST NOT print it via `mongodump --verbose`. GH automatically scrubs secret values from logs, but we don't echo as defence in depth. |

Trust boundaries: unchanged vs Phase 2 — browser → Next.js BFF (same-origin), BFF → Flask (Render-internal + Bearer JWT), Flask → MongoDB Atlas (TLS + scoped role). New surface: GH Actions runner → MongoDB Atlas (read-only mongodump via the `MONGODB_URI_BACKUP` connection string — recommend operator provisions a separate Atlas user with read-only role for this connection; documented in SUMMARY follow-up).

---

## Slice A — Backend models + seed + helpers + db wiring

<task type="auto" tdd="true">
  <name>Task P3-A.1: Pydantic GhanaFood + PortionDefault models + JSON schema</name>
  <files>backend/app/models/__init__.py, backend/app/models/ghana_food.py, shared/schemas/ghana-food.schema.json, backend/tests/test_meal_models.py</files>
  <behavior>
    - `PortionDefault`: `{label: str (1..40 chars), grams: int (1..2000)}`.
    - `GhanaFood`:
      - `food_id: str` matching `^gh-[a-z0-9-]+$` (e.g. `gh-jollof-rice`, `gh-kenkey-ga`).
      - `name: str` (1..80 chars; user-facing English label).
      - `alt_names: list[str]` (0..10 entries; may include INFOODS codes like "WAFCT-09-302" and informal names like "ga kenkey").
      - `kcal_per_100g: float` (0.0..900.0; FAO/INFOODS source value).
      - `protein_g_per_100g: float` (0.0..100.0).
      - `fat_g_per_100g: float` (0.0..100.0).
      - `carbs_g_per_100g: float` (0.0..100.0).
      - `portion_defaults: list[PortionDefault]` (1..6 entries; first is the Ghana-cultural canonical, others are diaspora alternatives).
      - `category: Literal["staple", "soup_stew", "protein", "side_snack"]`.
      - `source: Literal["wafct", "wafct_composite", "usda"]` — `wafct_composite` when the dish is built by summing component WAFCT entries (jollof, waakye).
      - `source_confidence: Literal["high", "medium", "low"]`.
    - `model_config = ConfigDict(extra="forbid")` (forbid unknown fields in the seed JSON — a typo in a field name should fail loading).
    - Per CONTEXT.md "Implementation Decisions" Ghana food catalogue: macro percentages do NOT need to sum to 100 (water/ash/fibre balance) so no cross-field validator on the macros.
    - Tests in `test_meal_models.py` (this file is shared with P3-A.2's Meal model tests):
      - `test_ghana_food_food_id_pattern_rejected_for_uppercase`
      - `test_ghana_food_food_id_pattern_rejected_for_underscores`
      - `test_ghana_food_portion_defaults_must_have_at_least_one`
      - `test_ghana_food_category_enum_rejects_unknown`
      - `test_ghana_food_source_enum_rejects_unknown`
      - `test_ghana_food_extra_field_rejected` (extra="forbid")
      - `test_portion_default_grams_range_rejected_at_zero` (ge=1)
  </behavior>
  <action>
    Create `backend/app/models/ghana_food.py` mirroring the Pydantic v2 idioms used by `backend/app/models/profile.py` (Literal types, `ConfigDict(extra="forbid")`, no Flask/Mongo imports). Export `GhanaFood`, `PortionDefault`, `Category`, `FoodSource` from the module. Re-export from `app.models.__init__` alongside the existing Profile/WeightLog exports.

    Generate the JSON Schema by running `GhanaFood.model_json_schema()` in a one-off Python invocation and writing to `shared/schemas/ghana-food.schema.json`. The `$id` and structure mirror `shared/schemas/profile.schema.json`'s pattern (Phase 2 P2-A.2).

    Per D-SHARED-SCHEMA-MANUAL-MIRROR (inherited from Phase 2): the JSON Schema is the canonical source of truth shared between FE Zod (P3-C.1) and BE Pydantic. We do NOT codegen; the Zod mirror is hand-maintained.

    Write tests FIRST (RED) covering the validator behaviours above, then implement until green. Tests live in `backend/tests/test_meal_models.py` which P3-A.2 also extends.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_meal_models.py -v -k "ghana_food or portion_default"</automated>
  </verify>
  <done>All ~7 ghana_food test cases pass; `shared/schemas/ghana-food.schema.json` exists and validates as JSON; `ruff check backend/app/models/ghana_food.py` is clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P3-A.2: Pydantic Meal + Component + MealCreate + MealUpdate models + JSON schema</name>
  <files>backend/app/models/meal.py, backend/app/models/__init__.py, shared/schemas/meal.schema.json, backend/tests/test_meal_models.py</files>
  <behavior>
    - `Component` (full doc shape stored as embedded sub-document inside `Meal.components`):
      - `name: str` (1..80; user-facing label; for matched foods this is copied from `GhanaFood.name` at write time so future deletions of catalogue entries don't break history).
      - `matched_food_id: str | None` (when null, this is a free-text component — see ComponentCreate logic).
      - `portion_g: int` (10..800; matches the slider range from D-PORTION-SLIDER-RANGE in CONTEXT specifics).
      - `kcal_low: int | None` (vision-only; null in Phase 3 writes).
      - `kcal_high: int | None` (vision-only; null in Phase 3 writes).
      - `kcal_point: int` (canonical; ≥0; server-computed `round(kcal_per_100g × portion_g / 100)` for matched; user-supplied for free-text).
      - `protein_g_point: int` (≥0; server-computed for matched; 0 for free-text since macros are unknown).
      - `confidence: float | None` (vision-only; null in Phase 3 writes).
      - `source: Literal["table", "llm_then_table_rematch", "user_corrected"]` — Phase 3 manual matched = "table"; Phase 3 free-text = "user_corrected"; Phase 4 will introduce "llm_then_table_rematch".
    - `Meal` (full doc shape):
      - `user_id: str` (clerk_id, server-set).
      - `logged_at: datetime` (UTC).
      - `source: Literal["manual", "ai_vision"]` (Phase 3 always "manual").
      - `components: list[Component]` (1..10 entries).
      - `total_kcal: int` (≥0; server = sum of components.kcal_point).
      - `total_protein_g: int` (≥0; server = sum of components.protein_g_point).
      - `ai_metadata: dict | None` — JSON `{model, prompt_hash, image_dims, latency_ms, cost_usd}` shape, but Phase 3 always writes `None`. Schema must accept `None` so Phase 4 has zero migration.
      - `created_at: datetime`, `updated_at: datetime`.
    - `ComponentCreate` (request body item):
      - EITHER `{food_id: str, portion_g: int}` (matched, the common path — server resolves `food_id` against `ghana_foods`, copies `name`, computes kcal/protein).
      - OR `{name: str, portion_g: int, kcal_point: int}` (free-text fallback — user supplies kcal manually).
      - Modelled as a discriminated union OR (simpler) a single model with all optional + a `model_validator(mode="after")` enforcing "exactly one of food_id-mode or kcal_point-mode". `extra="forbid"`. Pick the simpler model + validator pattern (Phase 2 used field_validator successfully; same idiom here).
    - `MealCreate` (POST body):
      - `{logged_at: datetime | None, components: list[ComponentCreate] (1..10)}`. `logged_at=None` means "use server now()"; explicit timestamp is validated against backdate range (T-03-04).
      - `extra="forbid"`. `source`, `total_kcal`, `total_protein_g`, `ai_metadata` are NEVER in the create body.
    - `MealUpdate` (PATCH body):
      - All fields optional: `logged_at?`, `components?` (1..10 entries when provided).
      - `extra="forbid"`. A PATCH that supplies `components` replaces the array entirely (no per-component partial merge — simpler semantics; the FE re-sends the full edited list).
    - Tests (extend `test_meal_models.py`):
      - `test_component_create_matched_path_validates`
      - `test_component_create_free_text_path_validates`
      - `test_component_create_neither_path_rejected_422`
      - `test_component_create_both_paths_rejected_422` (food_id AND kcal_point both set)
      - `test_component_create_portion_g_step_not_enforced_at_model_level` (model accepts any 10..800; 10-step is a UI/route concern)
      - `test_meal_create_rejects_empty_components` (min_length=1)
      - `test_meal_create_rejects_too_many_components` (max_length=10)
      - `test_meal_create_rejects_unknown_field` (extra="forbid", e.g. total_kcal in body)
      - `test_meal_update_components_optional`
      - `test_meal_serializes_ai_metadata_none_as_null` (forward-compat for Phase 4)
  </behavior>
  <action>
    Create `backend/app/models/meal.py` exporting `Meal`, `MealCreate`, `MealUpdate`, `Component`, `ComponentCreate`, `MealSource`, `ComponentSource`. Re-export from `app.models.__init__`.

    For the ComponentCreate "exactly one of" logic, use `@model_validator(mode="after")`:
    ```
    @model_validator(mode="after")
    def _exactly_one_path(self):
        matched = self.food_id is not None
        freetext = self.kcal_point is not None
        if matched == freetext:
            raise ValueError("supply exactly one of food_id or kcal_point")
        return self
    ```
    Free-text path also requires `name` to be present; matched path may omit `name` (server fills from catalogue).

    Generate the JSON Schema via `Meal.model_json_schema()` to `shared/schemas/meal.schema.json`. Critical: confirm the schema serializes `ai_metadata: null` correctly (Pydantic v2 emits `{"anyOf": [{...}, {"type": "null"}]}` for `dict | None`). This is the forward-compat surface for Phase 4.

    Per CONTEXT.md "Multi-component `meals` schema": this IS the day-1 invariant. Component.kcal_low / kcal_high / confidence are persisted as `null` from Phase 3 onwards so Phase 4 fills them with no migration.

    Write tests FIRST (RED) in `backend/tests/test_meal_models.py` (same file as P3-A.1), then implement until green. The two model files share one test file because they're a cohesive domain.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_meal_models.py -v</automated>
  </verify>
  <done>All meal-model test cases pass (combined with P3-A.1 ghana_food tests: ~17 cases total); `shared/schemas/meal.schema.json` exists; ai_metadata appears as a nullable in the generated schema; `ruff check backend/app/models/meal.py` is clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P3-A.3: Kcal helpers + meal-totals recompute (pure functions)</name>
  <files>backend/app/lib/meals.py, backend/tests/test_meal_helpers.py</files>
  <behavior>
    - `PORTION_MIN_G = 10`, `PORTION_MAX_G = 800`, `PORTION_STEP_G = 10`, `BACKDATE_MAX_DAYS = 7`.
    - `compute_kcal_for_component(kcal_per_100g: float, portion_g: int) -> int`:
      - returns `round(kcal_per_100g * portion_g / 100)` using banker's rounding (Python's `round`).
      - Example: 165 kcal/100g × 250 g = 412.5 → rounds to 412 (banker's even). Document this in a comment so reviewers don't think it's a bug.
    - `compute_protein_for_component(protein_g_per_100g: float, portion_g: int) -> int`:
      - same shape, returns integer grams of protein.
    - `recompute_meal_totals(components: list[dict]) -> tuple[int, int]`:
      - Accepts the persisted-shape component dicts (post-resolution from food lookups).
      - Returns `(total_kcal, total_protein_g)` as the sums.
      - Pure — no I/O.
    - Tests in `test_meal_helpers.py`:
      - `test_compute_kcal_known_values` (165 kcal/100g × 250 g → 412)
      - `test_compute_kcal_rounds_half_to_even` (banker's rounding documented)
      - `test_compute_kcal_zero_portion_returns_zero`
      - `test_compute_protein_known_values`
      - `test_recompute_totals_empty_list_returns_zero_zero`
      - `test_recompute_totals_three_components_sums`
      - `test_constants_match_ui_contract` (PORTION_MIN_G==10, MAX==800, STEP==10, BACKDATE==7)
  </behavior>
  <action>
    Create `backend/app/lib/meals.py` as pure Python (only stdlib imports — no Flask, no Mongo, no Pydantic). Per the Phase 2 pattern (`app/lib/tdee.py`), these helpers are imported by both the route module (`app/routes/meals.py`, Task P3-B.2) and by the test suite directly.

    Per D-INTERFACE-FIRST: these constants are also imported by the FE-side `frontend/src/lib/zod-schemas.ts` mirror (P3-C.1) — pin the values now.

    Write tests FIRST (RED), then implement until green.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_meal_helpers.py -v</automated>
  </verify>
  <done>All ~7 test cases pass; `ruff check backend/app/lib/meals.py` is clean; constants exported and importable as `from app.lib.meals import PORTION_MIN_G, ...`.</done>
</task>

<task type="auto">
  <name>Task P3-A.4: Ghana food seed JSON (25 entries) sourced from FAO/INFOODS WAFCT</name>
  <files>backend/seeds/__init__.py, backend/seeds/ghana_foods.json</files>
  <action>
    Create `backend/seeds/__init__.py` (empty package marker — no code).

    Curate `backend/seeds/ghana_foods.json` as a JSON array of 25 GhanaFood-shaped dicts. Per CONTEXT.md "Ghana food catalogue" required coverage:

    **Staples & swallows (7):** `gh-jollof-rice`, `gh-plain-rice`, `gh-banku`, `gh-fufu-cassava-plantain`, `gh-kenkey-ga`, `gh-kenkey-fante`, `gh-waakye`, `gh-tuo-zaafi`. (Note: kenkey-ga vs kenkey-fante are split per CONTEXT specifics — they have different kcal/100g per WAFCT.) That's 8 → drop one less-common staple (tuo zaafi can be kept or move to v2; keep tuo zaafi for northern-Ghana coverage and instead consolidate the two kenkeys to one entry `gh-kenkey` if 25 binds — but the spec calls out the split as a specifically named example, so KEEP both kenkeys and rebalance other categories). Final staples count: **8** (jollof, plain rice, banku, fufu, kenkey-ga, kenkey-fante, waakye, tuo zaafi).

    **Soups & stews (6):** `gh-light-soup`, `gh-groundnut-soup`, `gh-palm-nut-soup`, `gh-kontomire`, `gh-okro-stew`, `gh-shito`.

    **Proteins (5):** `gh-tilapia-grilled` (fried/grilled choice: grilled is the more commonly available value; "fried" can be an alt_name with a comment that the kcal_per_100g entry assumes grilled), `gh-chicken-thigh-grilled`, `gh-beef-stew`, `gh-koobi`, `gh-wele`.

    **Sides & snacks (6):** `gh-kelewele`, `gh-plantain-boiled`, `gh-plantain-fried`, `gh-red-red`, `gh-kosua-nu-meko`, `gh-bofrot`, `gh-koose`. That's 7 — pick 6 by dropping `gh-koose` (or `gh-bofrot`) to land on the 25 total. **Decision: drop `gh-koose`** (it overlaps with bofrot as a fried snack); add koose to a v2 catalogue follow-up. Final snacks count: **6**.

    **Total: 8 + 6 + 5 + 6 = 25.** ✓

    For each entry, populate FAO/INFOODS WAFCT values where directly available (e.g. plain rice, plantain — these have explicit WAFCT entries). Tag `source: "wafct"` and `source_confidence: "high"` for those.

    For composite dishes (jollof rice, waakye, kelewele, red-red, fufu, banku, kontomire, light/groundnut/palm-nut soup, beef stew, kenkey-ga, kenkey-fante, tuo zaafi, shito, bofrot, kosua nu meko), use **WAFCT-component summation** (sum the kcal/100g of the constituent ingredients weighted by typical recipe proportions per the FAO/INFOODS WAFCT documentation; for explicit composite values not in WAFCT, supplement with **USDA SR-Legacy** values for the ingredient). Tag `source: "wafct_composite"` and `source_confidence: "medium"` (or `"low"` for the dishes with the highest recipe variance like shito and red-red).

    For each entry, `alt_names` MUST include at least one informal name (e.g. `["WAFCT-09-302", "ga kenkey"]` for `gh-kenkey-ga`). Use the exact INFOODS code where known; for `wafct_composite` entries omit the code and use informal Twi/Ga/Akan names.

    `portion_defaults` MUST have:
    - The first entry is the **Ghana-cultural canonical portion** (e.g. `{"label": "1 ball of banku", "grams": 200}`; `{"label": "1 dollop of shito", "grams": 30}`; `{"label": "1 plate of jollof", "grams": 350}`; `{"label": "1 medium tilapia", "grams": 250}`).
    - 1..3 additional entries for diaspora alternatives (e.g. `{"label": "1 cup", "grams": 200}`, `{"label": "100 g", "grams": 100}`).

    Categories per entry: `staple` (8), `soup_stew` (6), `protein` (5), `side_snack` (6).

    **Source citations:** at the TOP of the JSON file, include a JSON-comment-equivalent — since JSON has no comments, prepend a 1-key "_meta" object as the FIRST array entry: NO — JSON arrays cannot mix shapes. Instead, document sources in a sibling file: create a one-line comment in `backend/seeds/__init__.py` pointing to the FAO/INFOODS WAFCT URL (`https://www.fao.org/3/i2698b/i2698b.pdf`) and USDA FoodData Central. Document in the eventual SUMMARY.md the per-row provenance (or in a follow-up `backend/seeds/SOURCES.md` — out of scope for the seed JSON itself).

    Validate the file by running `python -c "import json; from app.models.ghana_food import GhanaFood; [GhanaFood.model_validate(e) for e in json.load(open('backend/seeds/ghana_foods.json'))]"` — every entry must parse cleanly. (P3-A.5's seeder script automates this; this task is the curation pass.)

    Per CONTEXT.md specifics: kcal/100g values must be plausible (rice ~130, fufu ~155, jollof ~165, palm-nut soup ~85, fried plantain ~220, kelewele ~250, bofrot ~330 — order-of-magnitude check). If any entry's kcal_per_100g is < 30 or > 600 kcal/100g, double-check the source; the Pydantic range allows 0..900 but biology rejects extreme outliers.

    No tests directly on the JSON contents — P3-A.5's seeder + the model parse step in this task's verify is the structural gate. Numeric accuracy is an editorial concern recorded in the SUMMARY (operator-side: user can adjust values post-launch via the seeder + a re-run; the catalogue is read-only at runtime but the JSON is repo-versioned).
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -c "import json; from app.models.ghana_food import GhanaFood; data = json.load(open('seeds/ghana_foods.json')); assert len(data) == 25, f'expected 25 entries got {len(data)}'; [GhanaFood.model_validate(e) for e in data]; print(f'OK: {len(data)} entries parse cleanly')"</automated>
  </verify>
  <done>`seeds/ghana_foods.json` has 25 valid GhanaFood entries covering all CONTEXT categories; every entry parses against the Pydantic model; the verify command prints "OK: 25 entries parse cleanly"; provenance noted for SUMMARY follow-up.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P3-A.5: Idempotent seeder script + db.py extension + index creation</name>
  <files>backend/scripts/__init__.py, backend/scripts/seed_ghana_foods.py, backend/app/db.py, backend/tests/test_ghana_foods_seed.py</files>
  <behavior>
    - `seed(db, foods: list[dict]) -> dict[str, int]`:
      - Pure-ish (takes a Mongo `Database` handle so it's mongomock-testable).
      - For each food: `db.ghana_foods.update_one({"food_id": food["food_id"]}, {"$set": food}, upsert=True)`.
      - Track counts: `{"added": N, "updated": M, "unchanged": K}` based on `update_one().upserted_id` (added if non-None) vs `update_one().modified_count` (updated if >0) vs (unchanged otherwise).
      - Call `db.ghana_foods.create_index([("food_id", 1)], unique=True, name="food_id_unique")` (idempotent in Mongo when the same options are passed).
      - Call `db.ghana_foods.create_index([("name", "text"), ("alt_names", "text")], name="ghana_foods_text")` for the search route's text-search ranking.
      - **Per the Phase 1 invariant — no `create_index` on module load** — the indexes are created HERE inside the seeder (an operator-invoked one-shot), NOT in `app/db.py` module body.
    - `main()` CLI entry point: reads `MONGODB_URI` from env, opens a `MongoClient`, loads `backend/seeds/ghana_foods.json`, calls `seed()`, prints the counts.
    - Tests in `test_ghana_foods_seed.py`:
      - `test_seed_inserts_25_into_empty_db` (mongomock)
      - `test_seed_is_idempotent_second_run_zero_added` (run twice; assert second run has added=0, unchanged=25)
      - `test_seed_upserts_changed_entry` (modify one entry's kcal_per_100g, re-seed, assert updated=1)
      - `test_seed_creates_indexes` (assert `food_id_unique` and `ghana_foods_text` in `list_indexes()`)
      - `test_seed_rejects_invalid_entry` (insert a bad entry into the JSON-in-memory list, assert Pydantic ValidationError surfaces — but wrap so the test invokes seed() with a pre-validated list since the JSON parse happens in main(), not seed())
    - `app/db.py`: add `ghana_foods: Collection = db["ghana_foods"]` and `meals: Collection = db["meals"]` alongside `profiles` + `weight_logs`. Add index-hint comments matching Phase 2's pattern — `# db.ghana_foods.createIndex({food_id: 1}, {unique: true})` and `# db.meals.createIndex({user_id: 1, logged_at: -1})` — even though the seeder creates `ghana_foods` indexes; the `meals` `(user_id, logged_at)` compound index is operator-side (no seeder for it because the collection starts empty).
  </behavior>
  <action>
    Create `backend/scripts/__init__.py` (empty). Create `backend/scripts/seed_ghana_foods.py` with the `seed()` + `main()` shape above. The seeder uses Pydantic to re-validate each row before upserting (defence-in-depth — catches a hand-edited JSON typo).

    Add the two new collections to `backend/app/db.py` between the existing `weight_logs` line and the EOF, with comments documenting the operator-side index commands (mirroring the Phase 2 pattern).

    The seeder is documented as the canonical mechanism for both initial population AND for catalogue updates (operator edits the JSON, re-runs the script — same flow for a v2 catalogue expansion).

    Write tests FIRST (RED) using the mongomock fixture pattern from `backend/tests/conftest.py` (Phase 1/2 idiom). Then implement.

    SUMMARY follow-up: capture the production-side seeder invocation in the eventual `.planning/phases/03-meal-log-ghana-table/03-SUMMARY.md` — operator runs `cd backend && .venv/Scripts/python.exe -m scripts.seed_ghana_foods` once against production Atlas after this task lands.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_ghana_foods_seed.py -v</automated>
  </verify>
  <done>All ~5 seeder test cases pass; `app/db.py` exposes `ghana_foods` + `meals`; seeder is idempotent (second run reports unchanged=25); both indexes created in mongomock fixture; module-import side effects unchanged (still only MongoClient construction).</done>
</task>

---

## Slice B — Backend routes

<task type="auto" tdd="true">
  <name>Task P3-B.1: Flask /foods route (GET search with ranking)</name>
  <files>backend/app/routes/foods.py, backend/app/__init__.py, backend/tests/conftest.py, backend/tests/test_foods_routes.py</files>
  <behavior>
    - `GET /foods`:
      - `@require_auth` (signed-in users only — catalogue is not public so we don't reveal it to unauthenticated scrapers; bounded blast radius anyway since the JSON is also in git).
      - Query params: `q: str` (optional; empty/missing returns all 25 sorted by name), `limit: int` (default 10, clamped 1..25).
      - If `q` is supplied:
        - First pass: case-insensitive substring match against `name` OR any entry in `alt_names`.
        - Rank: exact `name` match (lowercased) first, then `name.startswith(q.lower())`, then `name.contains(q.lower())`, then `alt_names contains`. Ties broken by alphabetical `name`.
        - Limit to `limit` results.
      - If `q` is empty: return all (up to `limit`) sorted by `name` alphabetical.
      - Response: `200 {"foods": [<GhanaFood JSON>...]}` — same envelope shape as `/weights` (Phase 2).
    - Tests in `test_foods_routes.py` (seeds 4–5 sample foods into mongomock):
      - `test_get_foods_no_query_returns_all`
      - `test_get_foods_substring_match_on_name` (q="banku" finds gh-banku)
      - `test_get_foods_alt_names_match` (q="WAFCT-09-302" finds gh-kenkey-ga)
      - `test_get_foods_ranks_exact_match_first`
      - `test_get_foods_respects_limit_clamp` (limit=99 clamped to 25; limit=0 clamped to 1)
      - `test_get_foods_case_insensitive`
      - `test_get_foods_empty_when_no_match`
      - `test_get_foods_requires_auth_401` (request without JWT mock returns 401)
  </behavior>
  <action>
    Create `backend/app/routes/foods.py` exporting `bp` as a Flask Blueprint, following the EXACT pattern of `backend/app/routes/weights.py` (imports `from app import db as db_mod`, `@require_auth`, `_safe_errors` helper for the rare 422, `_food_to_json` serializer).

    Per the architecture note in `backend/app/routes/profile.py` docstring: import `app.db` as a module reference so tests can monkey-patch `app.db.ghana_foods` and the route handler sees the patched value.

    The ranking step is done in Python (in-memory sort over the small result set) rather than in Mongo — Mongo's text index gives us `$text` scoring but the relevance algorithm above is more tailored to the 25-entry catalogue. Future scale optimisation if needed.

    Register the blueprint in `backend/app/__init__.py` (`from app.routes.foods import bp as foods_bp; app.register_blueprint(foods_bp)`) — same try/except ImportError pattern as Phase 2's conditional `weights_bp` import is NOT needed here because the module is created in this task and is mandatory; just add the unconditional registration alongside `profile_bp`.

    Extend `backend/tests/conftest.py` with a `mongo_ghana_foods` fixture (mongomock, monkey-patches both `app.db.ghana_foods` and `app.routes.foods.db_mod.ghana_foods` — the same dual-binding patch pattern the Phase 1 SUMMARY documented).

    Write tests FIRST (RED), then implement until green. The auth mock is the same `_get_clerk()` monkeypatch pattern from `test_me.py` / `test_profile_routes.py`.

    Per D-INTERFACE-FIRST: this route is consumed by FE `frontend/src/app/dashboard/food-search.tsx` (P3-C.2). Pin the response envelope `{"foods": [...]}` now so the FE doesn't have to re-shape.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_foods_routes.py -v</automated>
  </verify>
  <done>All ~8 test cases pass; route registered in `create_app()`; full backend test suite (`pytest -q`) green.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P3-B.2: Flask POST /meals (create with kcal recompute) + lookup helpers</name>
  <files>backend/app/routes/meals.py, backend/app/__init__.py, backend/tests/conftest.py, backend/tests/test_meals_routes.py</files>
  <behavior>
    - `POST /meals`:
      - `@require_auth`. `user_id = g.clerk_user_id`.
      - Parses body via `MealCreate.model_validate_json(request.data)` (422 on validation failure).
      - Validates `logged_at`: if absent, use `datetime.now(UTC)`. If present, must be `≥ now - BACKDATE_MAX_DAYS days` AND `≤ now + 5 min` (T-03-04). Reject with `422 {"error": "logged_at_out_of_range", "details": {...}}`.
      - For each `ComponentCreate`:
        - **Matched path** (`food_id` provided): `db_mod.ghana_foods.find_one({"food_id": cc.food_id})`; if `None`, return `422 {"error": "unknown_food_id", "details": {"food_id": cc.food_id}}` (T-03-07).
          - Build the persisted Component: `name = food["name"]`, `matched_food_id = cc.food_id`, `portion_g = cc.portion_g`, `kcal_low = None`, `kcal_high = None`, `kcal_point = compute_kcal_for_component(food["kcal_per_100g"], cc.portion_g)`, `protein_g_point = compute_protein_for_component(food["protein_g_per_100g"], cc.portion_g)`, `confidence = None`, `source = "table"`.
        - **Free-text path** (`name + kcal_point` provided, no `food_id`): persisted Component has `matched_food_id = None`, `name = cc.name`, `portion_g = cc.portion_g`, `kcal_point = cc.kcal_point` (user-supplied), `protein_g_point = 0` (unknown), `kcal_low/high/confidence = None`, `source = "user_corrected"`.
      - Compute `total_kcal, total_protein_g = recompute_meal_totals(components)`.
      - Build the full doc: `{user_id, logged_at, source: "manual", components, total_kcal, total_protein_g, ai_metadata: None, created_at = updated_at = now}`. Insert into `db_mod.meals`.
      - Response: `201 {<Meal JSON>}` with `_id` serialized as a string `id`.
    - Tests:
      - `test_post_meal_single_matched_component_persists_and_computes_kcal_point`
      - `test_post_meal_multi_component_sums_totals` (banku 200g + tilapia 250g + shito 30g, asserts total_kcal == sum of expected kcal_points)
      - `test_post_meal_free_text_component_persists_with_user_corrected_source`
      - `test_post_meal_rejects_both_food_id_and_kcal_point_422`
      - `test_post_meal_rejects_neither_food_id_nor_kcal_point_422`
      - `test_post_meal_rejects_unknown_food_id_422` (T-03-07)
      - `test_post_meal_rejects_backdate_older_than_7_days_422` (T-03-04)
      - `test_post_meal_rejects_future_logged_at_422`
      - `test_post_meal_accepts_logged_at_now_minus_5_days`
      - `test_post_meal_ignores_client_supplied_kcal_point_on_matched_component` (T-03-02: body `{food_id, portion_g, kcal_point: 99999}` — since `kcal_point` is not in `ComponentCreate.matched_path`, `extra="forbid"` rejects with 422; ASSERT 422)
      - `test_post_meal_ignores_client_supplied_user_id_body_attacker` (T-03-01: body `{user_id: "user_attacker"}` rejected with 422 by `extra="forbid"` on `MealCreate`)
      - `test_post_meal_stores_ai_metadata_as_null` (forward-compat for Phase 4)
      - `test_post_meal_writes_source_manual`
  </behavior>
  <action>
    Create `backend/app/routes/meals.py` with the POST /meals handler. Same Blueprint pattern as `backend/app/routes/weights.py`. The module hosts ALL meal routes (POST, GET, PATCH, DELETE) — but this task only implements POST and registers the blueprint with a stub for the others (P3-B.3 + P3-B.4 fill them in). Use `bp.post("/meals")` for the POST handler.

    Add a module-level helper `_resolve_component(cc: ComponentCreate) -> dict` that returns the persisted-shape component dict, raising `_UnknownFoodIdError` for the matched-but-missing path. The route catches this and returns 422.

    Register the blueprint in `backend/app/__init__.py` (unconditional, alongside `foods_bp`).

    Extend `backend/tests/conftest.py` with a `mongo_meals` fixture (mongomock dual-binding patch).

    Write tests FIRST (RED). The route uses the mongomock fixtures from conftest + the existing JWT mock pattern. Per CONTEXT.md "Routes": the request body for POST /meals is `{logged_at, components: [{food_id, portion_g}, ...]}` — the test bodies follow this exact shape.

    Per D-INTERFACE-FIRST: the response envelope is the full Meal JSON (Phase 4's vision route will return the SAME shape — that's the day-1 invariant; pin it now).
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_meals_routes.py -v -k "post_meal"</automated>
  </verify>
  <done>All ~13 POST /meals test cases pass; full backend test suite (`pytest -q`) still green.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P3-B.3: Flask GET /meals (single-day + 30-day grouped history)</name>
  <files>backend/app/routes/meals.py, backend/tests/test_meals_routes.py</files>
  <behavior>
    - `GET /meals?date=YYYY-MM-DD` (single-day):
      - `@require_auth`. `user_id = g.clerk_user_id`.
      - Parse `date` param: `datetime.strptime(date_str, "%Y-%m-%d")` interpreted as the user's profile timezone (look up `profiles.find_one({clerk_id: user_id})["timezone"]`). Construct the day range `[date_local_midnight, date_local_midnight + 1d)`, convert to UTC for the Mongo query. If profile is missing or `date_str` is malformed, return `422 {"error": "invalid_date_param"}`.
      - Query: `db_mod.meals.find({"user_id": user_id, "logged_at": {"$gte": start_utc, "$lt": end_utc}}).sort("logged_at", 1)`.
      - Response: `200 {"date": "YYYY-MM-DD", "total_kcal": int, "total_protein_g": int, "meals": [<Meal JSON>...]}`.
    - `GET /meals?days=30` (30-day grouped history):
      - `@require_auth`.
      - Parse `days` (default 30, clamped 1..30). Compute the date range `[today_local - days + 1, today_local]` (inclusive in user's tz).
      - Query all meals in that UTC range for the user (single Mongo query).
      - Group server-side by user-local date (using profile timezone) into `{"date", "total_kcal", "total_protein_g", "meals"}` entries.
      - Skip empty days (per CONTEXT "/history" decision — only render days with meals).
      - Sort days newest-first.
      - Response: `200 {"days": [{"date": "YYYY-MM-DD", "total_kcal": int, "total_protein_g": int, "meals": [<Meal JSON>...]}...]}`.
    - If BOTH `date` and `days` are provided, prefer `date`. If neither, default to `days=30`.
    - Tests:
      - `test_get_meals_date_returns_day_total_and_meals`
      - `test_get_meals_date_isolated_by_user_id` (T-03-03)
      - `test_get_meals_date_uses_profile_timezone_for_day_boundary` (seed two profiles in Africa/Accra vs America/Los_Angeles; assert a meal logged_at 23:30 Accra appears under that date for Accra user, the next day for LA user)
      - `test_get_meals_date_malformed_returns_422`
      - `test_get_meals_date_no_profile_returns_422`
      - `test_get_meals_days_default_30_groups_correctly`
      - `test_get_meals_days_omits_empty_days`
      - `test_get_meals_days_clamps_to_1_30_range`
      - `test_get_meals_days_groups_by_user_local_date_not_utc`
      - `test_get_meals_days_isolated_by_user_id` (T-03-03)
      - `test_get_meals_days_newest_first`
  </behavior>
  <action>
    Extend `backend/app/routes/meals.py` from P3-B.2 — add `bp.get("/meals")` handler that switches on `request.args.get("date")` vs `request.args.get("days")`. Move the day-grouping logic into a private helper `_group_by_local_date(meals: list[dict], tz: str) -> list[dict]`.

    Use Python's `zoneinfo.ZoneInfo` (stdlib, Python 3.12 — already in the project per Phase 1 / Phase 2 setup) for timezone math. Test fixtures use `Africa/Accra` (UTC+0, no DST) and `America/Los_Angeles` (UTC-8 with DST) — cover the DST edge by seeding a meal at a date that straddles a DST transition.

    The day-boundary computation: `start_local = datetime.combine(date_obj, time.min).replace(tzinfo=ZoneInfo(tz))`, then `start_utc = start_local.astimezone(UTC)`. `end_utc = (start_local + timedelta(days=1)).astimezone(UTC)`.

    Per D-MEALS-RANGE-CAP in CONTEXT (implicit via T-03-06): days is clamped server-side; the FE only ever requests `days=30`.

    Write tests FIRST (RED), then implement. The `_group_by_local_date` helper is independently unit-testable in `test_meal_helpers.py` if you choose — but keeping it inside the route module is also fine given it's tightly coupled to the route shape.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_meals_routes.py -v -k "get_meals"</automated>
  </verify>
  <done>All ~11 GET /meals test cases pass; full backend test suite (`pytest -q`) green.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P3-B.4: Flask PATCH + DELETE /meals/&lt;id&gt;</name>
  <files>backend/app/routes/meals.py, backend/tests/test_meals_routes.py</files>
  <behavior>
    - `PATCH /meals/<id>`:
      - `@require_auth`. `user_id = g.clerk_user_id`.
      - Parse `id` as a Mongo ObjectId; return `422 {"error": "invalid_meal_id"}` if not parseable.
      - Pre-flight: `db_mod.meals.find_one({"_id": oid, "user_id": user_id})`. If `None`, return `404 {"error": "meal_not_found"}` (covers both "doesn't exist" and "belongs to another user" without leaking which — T-03-03).
      - Parse body via `MealUpdate.model_validate_json(request.data)` (422 on validation).
      - If `logged_at` is supplied: same backdate validation as POST (T-03-04).
      - If `components` is supplied: same per-component resolution as POST (T-03-07 + T-03-02). Replace `components` entirely (no partial merge — simpler semantics).
      - Recompute `total_kcal` + `total_protein_g` via `recompute_meal_totals`.
      - Update `updated_at = now`.
      - `db_mod.meals.update_one({"_id": oid, "user_id": user_id}, {"$set": set_fields})`.
      - Response: `200 {<Meal JSON>}` (the updated document re-read from Mongo).
    - `DELETE /meals/<id>`:
      - `@require_auth`. Same id-parse + ownership check as PATCH.
      - `db_mod.meals.delete_one({"_id": oid, "user_id": user_id})`.
      - Response: `200 {"ok": true, "deleted_id": "<id>"}`. Idempotent: a second DELETE for the same id returns `404 meal_not_found` (matching the existence-non-leak posture; this is acceptable as the FE has already updated its local state).
    - Tests:
      - `test_patch_meal_components_replaces_array_and_recomputes_totals`
      - `test_patch_meal_logged_at_only_updates_timestamp_keeps_components`
      - `test_patch_meal_rejects_unknown_field_422` (extra="forbid")
      - `test_patch_meal_other_user_returns_404_not_403` (T-03-03)
      - `test_patch_meal_invalid_id_returns_422`
      - `test_patch_meal_backdate_violation_422` (T-03-04)
      - `test_delete_meal_removes_doc`
      - `test_delete_meal_other_user_returns_404`
      - `test_delete_meal_idempotent_second_call_404`
      - `test_delete_meal_invalid_id_422`
  </behavior>
  <action>
    Extend `backend/app/routes/meals.py` with `bp.patch("/meals/<id>")` and `bp.delete("/meals/<id>")` handlers. Reuse `_resolve_component` from P3-B.2 for the PATCH components branch.

    Use `bson.ObjectId` (already in pymongo's dependency tree) for the id parse; catch `bson.errors.InvalidId` and return 422.

    Per D-PATCH-REPLACES-COMPONENTS (CONTEXT decision): a PATCH that supplies `components` replaces the array atomically — no per-component partial merge logic. This keeps the code path short and the contract obvious; the FE always re-sends the full edited components array.

    Write tests FIRST (RED), then implement. The mongomock fixture from P3-B.2 carries over.

    No new env vars, no new dependencies — PATCH and DELETE are pure logic on existing models + helpers.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_meals_routes.py -v</automated>
  </verify>
  <done>All ~10 PATCH/DELETE test cases pass; combined test_meals_routes.py count is ~34 (POST 13 + GET 11 + PATCH 6 + DELETE 4); full backend `pytest -q` is green; total backend pytest count ≥ ~110 (Phase 2 baseline ~81 + ~30 added here).</done>
</task>

---

## Slice C — Frontend Zod + shadcn + MealLogModal + BFFs

<task type="auto">
  <name>Task P3-C.1: Frontend Zod mirror for foods/meals + shadcn primitives (command/slider/popover) + BFF routes</name>
  <files>frontend/src/lib/zod-schemas.ts, frontend/package.json, frontend/src/components/ui/command.tsx, frontend/src/components/ui/slider.tsx, frontend/src/components/ui/popover.tsx, frontend/src/app/api/foods/route.ts, frontend/src/app/api/meals/route.ts, frontend/src/app/api/meals/[id]/route.ts, frontend/middleware.ts</files>
  <action>
    1. **Zod schemas (mirror).** Extend `frontend/src/lib/zod-schemas.ts` — append (do not replace) new exports per D-SHARED-SCHEMA-MANUAL-MIRROR:
       - `CATEGORIES = ["staple", "soup_stew", "protein", "side_snack"] as const` + enum schema.
       - `FOOD_SOURCES = ["wafct", "wafct_composite", "usda"] as const` + enum.
       - `FOOD_SOURCE_CONFIDENCES = ["high", "medium", "low"] as const` + enum.
       - `MEAL_SOURCES = ["manual", "ai_vision"] as const` + enum.
       - `COMPONENT_SOURCES = ["table", "llm_then_table_rematch", "user_corrected"] as const` + enum.
       - `portionDefaultSchema`, `ghanaFoodSchema` (mirror P3-A.1's Pydantic exactly — same ranges, same regex on food_id, alt_names up to 10, portion_defaults 1..6, etc.).
       - `componentCreateMatchedSchema = z.object({food_id: z.string().regex(/^gh-[a-z0-9-]+$/), portion_g: z.number().int().min(10).max(800)})`.
       - `componentCreateFreeTextSchema = z.object({name: z.string().min(1).max(80), portion_g: z.number().int().min(10).max(800), kcal_point: z.number().int().min(0).max(5000)})`.
       - `componentCreateSchema = z.union([componentCreateMatchedSchema, componentCreateFreeTextSchema])` (Zod's discriminated union via `z.union` since there's no single discriminator field).
       - `mealCreateSchema = z.object({logged_at: z.string().datetime().optional(), components: z.array(componentCreateSchema).min(1).max(10)})`.
       - `mealUpdateSchema` — same as mealCreate but all fields optional.
       - Response types: `GhanaFoodResponse`, `ComponentResponse` (with `kcal_low: number | null`, `kcal_high: number | null`, `confidence: number | null`, `source: ComponentSource`), `MealResponse` (with `id: string` mapped from server `_id`, `ai_metadata: MealAiMetadata | null`).
       - `PORTION_MIN_G = 10`, `PORTION_MAX_G = 800`, `PORTION_STEP_G = 10`, `BACKDATE_MAX_DAYS = 7` — duplicated from `backend/app/lib/meals.py` per D-INTERFACE-FIRST (P3-A.3 pinned them).
       - Document the constraint sync table at the top of the new section (matching the existing comment for Profile/WeightLog).

    2. **shadcn primitives.** From `frontend/`, run: `pnpm dlx shadcn@latest add command slider popover`. The CLI pulls in `cmdk`, `@radix-ui/react-slider`, `@radix-ui/react-popover` as transitive deps. Accept them. Three new files land at `frontend/src/components/ui/command.tsx`, `slider.tsx`, `popover.tsx`. Run `pnpm build` to verify no TS errors and capture the new route-table First Load JS for `/dashboard` in the commit message (PERF-01 manual gate). The new primitives are only imported by `/dashboard` (modal) and `/history` — `/sign-in` / `/onboarding` should be unaffected.

    3. **BFF routes** (three one-liners + middleware extension):
       - `frontend/src/app/api/foods/route.ts`: exports `GET` calling `forwardToFlask("GET", `/foods${req.nextUrl.search}`)`. Forward the query string verbatim.
       - `frontend/src/app/api/meals/route.ts`: exports `GET` calling `forwardToFlask("GET", `/meals${req.nextUrl.search}`)` and `POST` calling `forwardToFlask("POST", "/meals", await req.json())`.
       - `frontend/src/app/api/meals/[id]/route.ts`: exports `PATCH` and `DELETE` — both extract `id` from the dynamic segment via `{ params }: { params: Promise<{ id: string }> }` (Next 15 async params), then `forwardToFlask("PATCH", `/meals/${id}`, await req.json())` or `forwardToFlask("DELETE", `/meals/${id}`)` respectively.
       - `frontend/middleware.ts`: extend `createRouteMatcher` to include `/history(.*)`, `/api/foods(.*)`, `/api/meals(.*)` alongside existing entries. The `export const config.matcher` stays unchanged (it already covers `/api/*`).

    Per D-BFF-PATTERN (Phase 2 inheritance): all BFF routes are thin pass-throughs — no auth logic, no body validation, no shape transformation. `forwardToFlask` does everything; the browser never holds the Clerk JWT.

    Per D-INTERFACE-FIRST: the Zod schemas + the BFF routes are the contracts P3-C.2/C.3 and P3-D.1/D.2 consume. Pin them now.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Zod exports added; three shadcn primitives exist; three BFF route files exist; middleware extended; `pnpm build` shows `/api/foods`, `/api/meals`, `/api/meals/[id]`, `/history` in the route table; `/dashboard` First Load JS recorded in commit message (target ≤ 180 kB gzipped manual gate).</done>
</task>

<task type="auto">
  <name>Task P3-C.2: FoodSearch + ComponentChip client components</name>
  <files>frontend/src/app/dashboard/food-search.tsx, frontend/src/app/dashboard/component-chip.tsx</files>
  <action>
    **`food-search.tsx`** — client component. Wraps the shadcn `Command` primitive. Props: `{ onSelect: (food: GhanaFoodResponse) => void }`. Internal state: `query: string`, `results: GhanaFoodResponse[]`, `loading: bool`.

    Behaviour:
    - On query change, debounce 200 ms then `fetch('/api/foods?q=' + encodeURIComponent(query) + '&limit=10', { cache: 'no-store' })`. On 200, `setResults((await res.json()).foods)`. Show a small spinner while loading.
    - Renders the `Command` with `CommandInput` (placeholder "Search: jollof, banku, waakye..."), `CommandList`, and `CommandItem` per result. Each item shows: `name` (bold), `first portion_default.label + grams` (muted small), `kcal_per_100g` (right-aligned).
    - On `CommandItem` select, call `props.onSelect(food)` and reset the query to empty.
    - Per CONTEXT.md specifics: the FIRST entry in `portion_defaults` is the default — show its label inline as a preview.

    **`component-chip.tsx`** — client component. Renders ONE component row inside the meal-log modal. Props:
    ```
    {
      component: ComponentDraft,         // { name, food_id|null, portion_g, kcal_per_100g, protein_g_per_100g, source }
      onChange: (next: ComponentDraft) => void,
      onRemove: () => void,
    }
    ```
    Layout:
    - Row 1: chip with `component.name` + small muted "matched" badge (if `food_id`) or "free-text" badge.
    - Row 2: shadcn `Slider` (min={PORTION_MIN_G}=10, max={PORTION_MAX_G}=800, step={PORTION_STEP_G}=10) bound to `component.portion_g`. On `onValueChange`, emit `onChange({ ...component, portion_g: newValue })`.
    - Row 3: live `kcal_point` preview computed in JSX as `Math.round(component.kcal_per_100g * component.portion_g / 100)` (the FE mirror of P3-A.3's helper — they MUST agree). Below that, "{portion_g} g · {protein_g} g protein".
    - Top-right: small "✕" button calling `onRemove`.

    Per D-MIRRORED-HELPERS (Phase 2 inheritance via P2-B.2's `frontend/src/lib/tdee.ts`): the FE recomputes for preview only. The server is the source of truth on submit (P3-B.2's POST recomputes and persists).

    No tests in this task (purely declarative client components; coverage via P3-F.1's manual smoke).
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Both files exist; FoodSearch debounces queries (verify timing in browser DevTools network panel during smoke); ComponentChip slider step is 10 and range 10..800; `pnpm build` green.</done>
</task>

<task type="auto">
  <name>Task P3-C.3: MealLogModal — create + edit modes</name>
  <files>frontend/src/app/dashboard/meal-log-modal.tsx</files>
  <action>
    `meal-log-modal.tsx` — client component. Wraps the shadcn `Dialog` (already in the repo from Phase 2 P2-B.1). Props:
    ```
    {
      open: boolean,
      onOpenChange: (open: boolean) => void,
      initial?: MealResponse,        // present in edit mode; absent in create
    }
    ```

    Internal state (RHF + zodResolver(mealCreateSchema or mealUpdateSchema based on mode)):
    - `components: ComponentDraft[]` (1..10 entries) — kept as a controlled array via `useFieldArray` from RHF.
    - `logged_at: string | undefined` — input as a `<input type="datetime-local">` defaulting to `new Date().toISOString().slice(0, 16)`. The field is constrained client-side to the backdate window (`min` attribute = today - 7d, `max` = now). Server enforces too (T-03-04).

    Layout (top-down inside the Dialog):
    1. Header: "Log meal" (create) or "Edit meal" (edit).
    2. `<FoodSearch onSelect={(food) => append({ name: food.name, food_id: food.food_id, portion_g: food.portion_defaults[0].grams, kcal_per_100g: food.kcal_per_100g, protein_g_per_100g: food.protein_g_per_100g, source: "table" })} />`.
    3. A "Free-text component" disclosure (collapsed by default) — opens an inline mini-form: `{name, portion_g, kcal_point}` + "Add as free-text" button. Appends a draft with `food_id: null`, `source: "user_corrected"`, `kcal_per_100g: kcal_point * 100 / portion_g` (so the preview math works — we don't persist this, the server uses the user-supplied `kcal_point` directly).
    4. The `components` field array as a vertical list of `<ComponentChip>` rows. Empty state: "Search and add a food above to start logging."
    5. `<input type="datetime-local">` for `logged_at` (collapsed under a "Backdate" disclosure; default visible value = now).
    6. Running totals card: total kcal = sum of `Math.round(c.kcal_per_100g * c.portion_g / 100)` over draft components; total protein analogous. Numeric only — no chart.
    7. Buttons row: "Cancel" (calls `onOpenChange(false)`); "Save" — disabled when `components.length === 0` or RHF `formState.isValid === false`.

    Submit handler:
    - Create mode: `POST /api/meals` with body `{ logged_at, components: components.map(c => c.food_id ? { food_id: c.food_id, portion_g: c.portion_g } : { name: c.name, portion_g: c.portion_g, kcal_point: Math.round(c.kcal_per_100g * c.portion_g / 100) }) }`.
    - Edit mode: `PATCH /api/meals/${initial.id}` with the same body shape.
    - On 201/200: `toast.success("Meal logged")`, call `onOpenChange(false)`, `router.refresh()` (re-fetches the server-rendered dashboard data → KcalPill + TodaysMealsList update).
    - On 422/4xx: parse the error JSON, surface `error` and `details` inline at the top of the modal (not via toast — sticky error so user can fix and retry).

    Edit-mode pre-fill: when `initial` is present, the `useEffect` on mount populates `components` from `initial.components` (mapping each persisted Component back to the ComponentDraft shape — needs a lookup against `/api/foods?q=<name>&limit=1` to recover `kcal_per_100g` for the slider preview, OR cache the food details inline in the persisted Component — **decision: re-fetch via /api/foods on edit-mode open** because the persisted shape doesn't include the full food doc; this keeps Phase 4's "kcal range" surface uncluttered). For free-text components, the kcal_per_100g preview is derived as `kcal_point * 100 / portion_g`.

    Per D-EDIT-REUSES-MODAL (CONTEXT decision implied by the must_have "edit re-opens the modal pre-filled"): one modal component, two modes, no duplicated form code.

    Per D-PATCH-REPLACES-COMPONENTS (P3-B.4): the FE sends the full edited components array; no per-component diff. The PATCH body shape matches POST exactly.

    No tests in this task — coverage via P3-F.1's manual smoke.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`MealLogModal` builds; component compiles in both modes (visually verified next slice); `pnpm build` green; `/dashboard` First Load JS recorded in commit (lazy loading is a Phase 5 concern — Phase 3 ships the modal as a plain client import).</done>
</task>

---

## Slice D — Dashboard integration

<task type="auto">
  <name>Task P3-D.1: KcalPill + TodaysMealsList + LogMealCta dashboard widgets</name>
  <files>frontend/src/app/dashboard/kcal-pill.tsx, frontend/src/app/dashboard/todays-meals-list.tsx, frontend/src/app/dashboard/log-meal-cta.tsx</files>
  <action>
    **`kcal-pill.tsx`** — SERVER component. Props: `{ totalKcal: number, targetKcal: number }`. Renders:
    - A single rounded pill: "&lt;X&gt; / &lt;Y&gt; kcal · &lt;Z&gt; remaining" where Z = Y - X (can be negative; display "over by N kcal" when negative).
    - bg colour computed in JSX (no client JS):
      - `bg-red-100 text-red-900` if X > Y (over target).
      - `bg-amber-100 text-amber-900` if X > Y * 0.9 (within 10% of target).
      - `bg-emerald-100 text-emerald-900` otherwise (under 90% of target).
    - Animation: NONE. Tailwind classes are static; the animated kcal ring is Phase 5 (DASH-02).
    - Numbers are right-aligned with `tabular-nums` font feature for stable layout as values change.

    **`todays-meals-list.tsx`** — CLIENT component (needs the modal + delete confirm). Props: `{ meals: MealResponse[], onEdit: (meal: MealResponse) => void }`. Renders:
    - Empty state: "No meals logged yet today. Tap **Log meal** to add your first one."
    - Each meal as a row: `[time HH:mm] · [chips: component names separated by ' · '] · [total_kcal kcal]` + a right-aligned Edit button + Delete button.
    - Edit click: `props.onEdit(meal)` (parent opens the modal in edit mode).
    - Delete click: `if (confirm('Delete this meal?'))` then `await fetch('/api/meals/' + meal.id, { method: 'DELETE' })`; on 200 → `router.refresh()`; on 404 → toast.error and `router.refresh()` anyway (the meal is gone either way).

    **`log-meal-cta.tsx`** — CLIENT component. Renders a primary "Log meal" button that, on click, sets a local `useState<{open: boolean, initial?: MealResponse}>` and renders `<MealLogModal open={state.open} onOpenChange={(o) => setState(s => ({...s, open: o}))} initial={state.initial} />`. ALSO exposes an `openEdit(meal)` callback so the parent can pass it down to `TodaysMealsList.onEdit`. Wire as:
    ```
    const [open, setOpen] = useState(false);
    const [editTarget, setEditTarget] = useState<MealResponse | undefined>(undefined);
    const openCreate = () => { setEditTarget(undefined); setOpen(true); };
    const openEdit = (m: MealResponse) => { setEditTarget(m); setOpen(true); };
    return (
      <>
        <button onClick={openCreate}>Log meal</button>
        <TodaysMealsList meals={props.meals} onEdit={openEdit} />
        <MealLogModal open={open} onOpenChange={setOpen} initial={editTarget} />
      </>
    );
    ```
    Restructure so this is the SINGLE client component the dashboard page imports — it owns the modal + list + button as one cohesive island. (Rename to `meal-log-island.tsx` if that name is clearer; the must_have artifact list keeps the three filenames for clarity, but a single combined file is acceptable as long as the three exports/responsibilities are present.)

    Per D-NO-ANIMATION-PHASE-3: KcalPill has NO transitions, NO progress bar animation, NO Rive. The colour bands are static class swaps. Phase 5 owns the animated kcal ring.

    No tests — coverage via P3-F.1.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Three components exist; `pnpm build` green; new island component shows in `/dashboard`'s lazy-chunk graph in build output.</done>
</task>

<task type="auto">
  <name>Task P3-D.2: Dashboard page.tsx — fetch today's meals in parallel + wire KcalPill + island</name>
  <files>frontend/src/app/dashboard/page.tsx</files>
  <action>
    Extend `frontend/src/app/dashboard/page.tsx` (Phase 2 version reads `/api/profile` + `/api/weights` in parallel). Add a THIRD parallel fetch: `/api/meals?date=<today_in_user_tz>`.

    Compute `today_in_user_tz` server-side:
    ```
    const tz = profile.timezone; // already in scope after profileRes.json()
    const todayStr = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    // en-CA gives YYYY-MM-DD format directly — no manual padding.
    ```
    Because `today_in_user_tz` depends on `profile.timezone`, the meals fetch happens AFTER profile resolves (not in the initial Promise.all). Two-stage fetch:
    1. `Promise.all([fetchSameOrigin("/api/profile"), fetchSameOrigin("/api/weights?limit=30")])`.
    2. Parse profile → compute `todayStr` → `fetchSameOrigin("/api/meals?date=" + todayStr)`.

    On the meals fetch:
    - 200 → parse to `{date, total_kcal, total_protein_g, meals: MealResponse[]}`.
    - non-200 → render an inline "Could not load today's meals" notice but keep the rest of the page rendered.

    Render layout (between the existing `<WeightLogCard />` and the page footer):
    ```
    <KcalPill totalKcal={today.total_kcal} targetKcal={profile.daily_kcal_target} />
    <MealLogIsland meals={today.meals} />   // hosts LogMealCta + TodaysMealsList + MealLogModal
    <Link href="/history">View 30-day history →</Link>
    ```

    Plus add a top-right nav `<Link href="/history">History</Link>` (alongside existing Profile / Settings / SignOut links).

    Verify the existing Profile + Weights + Sign-out shape is unchanged — Phase 2 wiring must continue to work.

    Per CONTEXT.md "Dashboard integration": pill placement is at the TOP of the dashboard. Reorder if necessary so KcalPill is the FIRST card under the header (above TargetCard and WeightLogCard). The natural Phase 5 evolution: KcalPill → animated kcal ring → TargetCard merge. Phase 3 keeps them separate for incremental visual evolution.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`/dashboard` renders KcalPill + meal-log island + history link; `pnpm build` green; route still in the build's route table; First Load JS recorded in commit message.</done>
</task>

<task type="auto">
  <name>Task P3-D.3: Hook up meal-log refresh signal — router.refresh() chain</name>
  <files>frontend/src/app/dashboard/meal-log-modal.tsx, frontend/src/app/dashboard/todays-meals-list.tsx</files>
  <action>
    This is the wiring task that closes the loop — ensure that **every** create/edit/delete operation triggers `router.refresh()` so the server-rendered KcalPill, TodaysMealsList, and (if visible) the WeightLogCard target re-fetch.

    In `meal-log-modal.tsx` (P3-C.3): the submit handler already calls `router.refresh()` on success per that task's spec. Verify it's wired — if not, add it.

    In `todays-meals-list.tsx` (P3-D.1): the delete handler already calls `router.refresh()` per that task's spec. Verify.

    Additionally:
    - Capture loading state during submit/delete (RHF `formState.isSubmitting` for the modal; a local `useState<boolean>` for delete). Disable buttons while in-flight to prevent double-submits.
    - On 422 from POST/PATCH, parse and display the server's `error` + `details` inline at the top of the modal (do NOT close the modal — the user should fix the input and retry).
    - On 404 from DELETE (stale state — meal already removed in another tab), toast a friendly "This meal was already removed" message and refresh anyway.

    No new files; this task is a pass over the previous two to verify the refresh chain and add the loading-state UX polish. The reason it's a separate task: P3-C.3 and P3-D.1 are written in isolation and the wiring across them is easier to verify (and revert) as one atomic commit.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Create-meal flow: POST 201 → modal closes → `router.refresh()` fires → KcalPill + TodaysMealsList show new meal (verified by manual smoke in P3-F.1). Delete flow: DELETE 200 → list re-renders without the meal. Edit flow: PATCH 200 → list shows updated component chips. Build still green.</done>
</task>

---

## Slice E — History route

<task type="auto">
  <name>Task P3-E.1: /history server-rendered 30-day grouped list</name>
  <files>frontend/src/app/history/page.tsx, frontend/src/app/history/day-group.tsx</files>
  <action>
    **`frontend/src/app/history/page.tsx`** — SERVER component (no client JS).
    - Auth-protected via middleware (added in P3-C.1).
    - Same `fetchSameOrigin` cookie-forwarding pattern as `/dashboard/page.tsx`.
    - Fetches `/api/meals?days=30` → expects `{ days: [{date, total_kcal, total_protein_g, meals: MealResponse[]}, ...] }`.
    - Renders:
      - Header: "Last 30 days".
      - Empty state: "No meals logged yet. Head to the dashboard to log your first meal."
      - Otherwise: vertical list of `<DayGroup>` (one per day, newest first).
      - Footer link: "← Back to dashboard".
    - 401 → `redirect('/sign-in')`. Non-200 (other) → inline error message.

    **`frontend/src/app/history/day-group.tsx`** — SERVER component (no client JS). Props: `{ day: { date: string, total_kcal: number, total_protein_g: number, meals: MealResponse[] } }`.
    Renders:
    - Date header: "2026-05-13 (Mon)" using `Intl.DateTimeFormat` for the weekday.
    - "Total: X kcal · Y g protein".
    - List of meals: each as `[HH:mm] · [chips: component names joined ' · '] · [total_kcal kcal]`.
    - Read-only — no Edit, no Delete buttons (per the must_have "/history... server-rendered with no client-side state"). Users edit/delete from /dashboard's TodaysMealsList only.

    Per D-HISTORY-READ-ONLY (CONTEXT decision implicit in the must_haves): /history is for review, not mutation. Keeps the route a pure server component, no client JS, fast first paint.

    Per LOG-08 success criterion: "user can scroll back through at least the last 30 days of meal history grouped by day" — this task delivers it.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`/history` route exists in build table; renders empty state when no meals; renders DayGroup per non-empty day when meals exist (verified in P3-F.1 manual smoke); `pnpm build` green.</done>
</task>

---

## Slice F — CI nightly backup + traceability

<task type="auto">
  <name>Task P3-F.1: Nightly mongodump GitHub Actions workflow</name>
  <files>.github/workflows/nightly-backup.yml</files>
  <action>
    Create `.github/workflows/nightly-backup.yml` with:

    - Triggers:
      - `schedule: - cron: '0 2 * * *'` (02:00 UTC daily).
      - `workflow_dispatch:` (manual run from the GH UI; useful for one-off backups and the post-deploy smoke).
    - Single job `backup` on `ubuntu-latest`. Concurrency group `nightly-backup` with `cancel-in-progress: false` (sequential nightly runs don't need to cancel each other; but we don't want two simultaneously either).
    - Permissions: `contents: read` only (least privilege).
    - Steps:
      1. Install MongoDB Database Tools: `wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-x86_64-100.10.0.deb && sudo dpkg -i mongodb-database-tools-ubuntu2204-x86_64-100.10.0.deb` (or use the apt source — `wget` is simpler and avoids an apt-key drift). Pin the version explicitly per D-TOOLS-PIN below.
      2. Generate a timestamped archive name: `echo "ARCHIVE=fitgh-backup-$(date -u +'%Y%m%d-%H%M%S').gz" >> $GITHUB_ENV`.
      3. Run `mongodump --uri="${{ secrets.MONGODB_URI_BACKUP }}" --gzip --archive="${ARCHIVE}"`. CRITICAL: do NOT echo the URI; do NOT use `--verbose`. GH's secret-scrubber catches it anyway, but defence in depth (T-03-09).
      4. Print archive size: `ls -lh "${ARCHIVE}"`.
      5. Upload as actions artifact: `actions/upload-artifact@v4` with `name: ${{ env.ARCHIVE }}`, `path: ${{ env.ARCHIVE }}`, `retention-days: 90`, `if-no-files-found: error`, `compression-level: 0` (already gzipped — re-compressing wastes runner CPU).
      6. (Optional) `actions/setup-python@v5` is NOT needed — pure shell. Keep the job minimal.

    Decision points captured:
    - **D-TOOLS-PIN:** Pin `mongodb-database-tools` version `100.10.0` (the latest stable as of phase planning). Bumping is a follow-up; do not auto-update.
    - **D-NO-R2:** Per CONTEXT.md DATA-01, we are NOT uploading to Cloudflare R2 in v1. GH Actions artifact storage (90-day retention, free for public repos / included in GH Free tier for private) is sufficient.
    - **D-SEPARATE-BACKUP-SECRET:** `MONGODB_URI_BACKUP` is a NEW GH Actions secret distinct from the runtime `MONGODB_URI`. Recommend operator provisions a read-only Atlas user for this connection string (defence in depth — a leaked backup secret can only `mongodump`, not write).

    Operator follow-up (documented in SUMMARY.md):
    1. In GH repo Settings → Secrets and variables → Actions, add `MONGODB_URI_BACKUP` = a read-only Atlas connection string (different user from `fitgh-app`).
    2. Trigger one `workflow_dispatch` run after this task lands to verify the workflow succeeds end-to-end against production Atlas (cannot be verified in code review — only via a real run).
    3. Confirm artifact is downloadable from the GH Actions UI and `tar -tzf ${ARCHIVE} | head` lists collections.

    No backend / frontend test for this task — the workflow is GH-side. The verify command checks YAML validity only.
  </action>
  <verify>
    <automated>node -e "require('js-yaml') ? null : null" 2>/dev/null; python -c "import yaml; yaml.safe_load(open('.github/workflows/nightly-backup.yml'))" && echo "YAML OK"</automated>
  </verify>
  <done>`.github/workflows/nightly-backup.yml` exists; YAML parses cleanly; SUMMARY follow-up captures the operator-side secret + first workflow_dispatch run; `MONGODB_URI_BACKUP` recorded as a new GH Actions secret in the project's environment inventory.</done>
</task>

<task type="auto">
  <name>Task P3-F.2: End-to-end smoke + REQUIREMENTS.md traceability flip</name>
  <files>.planning/REQUIREMENTS.md</files>
  <action>
    Manual end-to-end smoke against local Flask + local Next.js (Phase 1 deploy is already live; this is the developer-loop check before merge):

    1. `cd backend && .venv/Scripts/python.exe -m pytest -q` — full suite green; count is ≥ ~110 (Phase 2 baseline ~81 + ghana_food/meal models ~17 + helpers ~7 + seeder ~5 + foods routes ~8 + meals routes ~34 ≈ +71).
    2. `cd backend && .venv/Scripts/python.exe -m scripts.seed_ghana_foods` against a LOCAL Mongo or a development Atlas user — assert prints "added: 25, updated: 0, unchanged: 0" on first run, "added: 0, updated: 0, unchanged: 25" on second run.
    3. `cd frontend && pnpm tsc --noEmit && pnpm build` — green; record `/dashboard` and `/history` First Load JS in commit message.
    4. Start local Flask + local Next.js with real Clerk dev keys + real Atlas creds in `.env.local` (one-time: run the seeder against the dev Atlas).
    5. Sign in as a Phase 2 onboarded user → land on /dashboard → assert KcalPill shows "0 / Y kcal · Y remaining" GREEN.
    6. Click "Log meal" → modal opens → type "jollof" → results appear (debounce check in DevTools network panel) → click `gh-jollof-rice` → component chip appears with portion slider defaulting to "1 plate of jollof / 350 g" → running total updates → click Save.
    7. Modal closes → KcalPill updates to reflect the jollof kcal → TodaysMealsList shows the meal.
    8. Click Edit on the meal → modal reopens pre-filled → change portion to 450 g → Save → list + pill reflect new total.
    9. Click Delete → confirm → meal disappears → pill back to 0.
    10. Log a multi-component meal: banku 200g + tilapia 250g + shito 30g → totals computed → Save → assert all three chips render.
    11. Backdate test: open modal → expand Backdate → set logged_at to yesterday 18:00 → Save → /history → assert yesterday's date group shows the meal.
    12. Backdate boundary: try to set logged_at to 8 days ago → submit → assert 422 error renders inline ("logged_at_out_of_range").
    13. Free-text fallback: open modal → expand "Free-text component" → enter `{name: "Beans on toast", portion_g: 200, kcal_point: 280}` → Add → Save → meal persists with `matched_food_id: null` (verify in mongosh).
    14. Navigate to /history → assert today and yesterday show grouped meals newest-first; empty days are omitted.
    15. Cross-user isolation: in mongosh, manually seed a meal for a fake `user_other` → reload dashboard as the test user → assert that meal does NOT appear (T-03-03).
    16. Pill colour bands: log enough meals to exceed 90% of daily_kcal_target → assert AMBER; exceed 100% → assert RED; delete back below 90% → assert GREEN.
    17. /history empty-state: as a fresh user with no meals, /history renders the empty-state copy.
    18. Manually trigger the nightly-backup workflow via `workflow_dispatch` in the GH UI → assert run succeeds → assert artifact downloadable → `tar -tzf <archive>` lists `fitgh/profiles`, `fitgh/weight_logs`, `fitgh/meals`, `fitgh/ghana_foods`, `fitgh/users`.
    19. `/dashboard` First Load JS recorded; if > 180 kB gzipped, capture in SUMMARY as a manual-gate deviation and open a follow-up (PERF-01 deferred per Phase 1 note — Phase 3 does not regress the manual gate).

    Then update `.planning/REQUIREMENTS.md` traceability table — change `Pending` to `Complete` for LOG-01, LOG-02, LOG-03, LOG-04, LOG-05, LOG-06, LOG-07, LOG-08, DATA-01 (9 IDs total). Per Phase 2's precedent (P2-F.1), do not touch any other IDs even if they happen to be peripherally exercised.

    Per the must_have list: every truth + key_link must pass. If anything fails, capture in the SUMMARY.md (Phase 3 produces one at end-of-phase) as a deviation and fix in a follow-up task BEFORE flipping the requirement to Complete.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest -q && cd ../frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>All 19 smoke steps pass; backend pytest count ≥ ~110; frontend build green; REQUIREMENTS.md updated with 9 IDs marked Complete; SUMMARY notes captured for: provenance of WAFCT vs USDA per food (P3-A.4 follow-up), production seeder run (P3-A.5), operator-side `(user_id, logged_at desc)` index on `meals` (P3-A.5 db.py comment), nightly-backup workflow_dispatch first-run verification (P3-F.1), `MONGODB_URI_BACKUP` GH Actions secret.</done>
</task>

---

## Source Coverage Audit

| Source | Item | Plan Coverage |
|--------|------|---------------|
| GOAL (ROADMAP Phase 3) | 25-dish FAO/INFOODS catalogue search | Slice A (P3-A.1/A.4) + Slice B (P3-B.1) + Slice C (P3-C.2) |
| GOAL | Multi-component meal logging with portion sliders | Slice A (P3-A.2/A.3) + Slice B (P3-B.2) + Slice C (P3-C.2/C.3) |
| GOAL | Today's running kcal total + remaining pill | Slice B (P3-B.3) + Slice D (P3-D.1/D.2) |
| GOAL | Edit / delete a logged meal | Slice B (P3-B.4) + Slice C (P3-C.3) + Slice D (P3-D.1/D.3) |
| GOAL | 30-day history grouped by day | Slice B (P3-B.3) + Slice E (P3-E.1) |
| GOAL | Multi-component schema proven before vision | Slice A (P3-A.2) — kcal_low/high/confidence/ai_metadata persisted as null |
| REQ LOG-01 | Search catalogue by name or alias | P3-A.1 + P3-A.4 + P3-B.1 + P3-C.2 |
| REQ LOG-02 | Log meal as one or multiple components (day-1 schema) | P3-A.2 + P3-B.2 + P3-C.3 |
| REQ LOG-03 | Portion slider with culturally meaningful defaults | P3-A.4 (portion_defaults with Ghana labels) + P3-C.2 (ComponentChip slider) |
| REQ LOG-04 | Total kcal + total protein computed per meal | P3-A.3 (recompute helper) + P3-B.2 (server-side) + P3-C.3 (FE preview) |
| REQ LOG-05 | Today's meals list with running daily total | P3-B.3 (GET /meals?date=) + P3-D.1 (TodaysMealsList) + P3-D.2 |
| REQ LOG-06 | Dashboard "remaining kcal" pill | P3-D.1 (KcalPill) + P3-D.2 (page integration) |
| REQ LOG-07 | Edit or delete a logged meal | P3-B.4 (PATCH/DELETE) + P3-C.3 (edit mode) + P3-D.1/D.3 |
| REQ LOG-08 | View 30-day history grouped by day | P3-B.3 (days=30 endpoint) + P3-E.1 (/history route) |
| REQ DATA-01 | Nightly mongodump backup verifiable from operator side | P3-F.1 (.github/workflows/nightly-backup.yml) |
| CONTEXT D-MULTI-COMPONENT-DAY-1 | day-1 invariant — no ai_meals collection | P3-A.2 (Component shape) + P3-B.2 (POST writes nulls) |
| CONTEXT D-PORTION-SLIDER-RANGE | 10g increments, 10..800g | P3-A.3 (constants) + P3-C.2 (Slider props) |
| CONTEXT D-BACKDATE-7-DAYS | logged_at backdate window | P3-A.3 (BACKDATE_MAX_DAYS) + P3-B.2 (validator) + P3-C.3 (input min/max) |
| CONTEXT D-PROFILE-TIMEZONE-DAY-BOUNDARY | day boundaries in user's profile tz | P3-B.3 (zoneinfo + profile lookup) + P3-D.2 (today_in_user_tz) |
| CONTEXT D-READ-ONLY-CATALOGUE | ghana_foods is read-only at runtime | P3-A.5 (seeder is only writer) + P3-B.1 (no POST /foods) |
| CONTEXT D-INDEXES-NO-MODULE-LOAD | indexes created in seeder, not on import | P3-A.5 (create_index inside seed()) |
| CONTEXT D-NO-ANIMATION-PHASE-3 | static pill, no Rive | P3-D.1 (KcalPill class swap only) |
| CONTEXT D-EDIT-REUSES-MODAL | single modal, two modes | P3-C.3 (initial prop) + P3-D.1 (LogMealCta state) |
| CONTEXT D-DATA-01-GH-ARTIFACTS-NOT-R2 | GH artifact storage suffices for v1 | P3-F.1 (nightly-backup.yml) |
| CONTEXT D-FREE-TEXT-EDGE-CASE | free-text fallback when no /foods match | P3-A.2 (ComponentCreate union) + P3-B.2 (user_corrected source) + P3-C.3 (mini-form) |
| CONTEXT D-PATCH-REPLACES-COMPONENTS | PATCH replaces array atomically | P3-B.4 (no partial merge) + P3-C.3 (FE re-sends full list) |
| CONTEXT D-KENKEY-GA-VS-FANTE | split per WAFCT differences | P3-A.4 (separate gh-kenkey-ga and gh-kenkey-fante entries) |
| CONTEXT D-HISTORY-READ-ONLY | /history has no edit/delete | P3-E.1 (no buttons in DayGroup) |
| CONTEXT D-SHARED-SCHEMA-MANUAL-MIRROR (Phase 2 inheritance) | Hand-maintained Zod + Pydantic | P3-A.1/A.2 (JSON Schema) + P3-C.1 (Zod) |
| CONTEXT D-BFF-PATTERN (Phase 2 inheritance) | forwardToFlask one-liners | P3-C.1 (three BFF routes) |
| CONTEXT D-NO-AI-IN-PHASE-3 | no Anthropic, no image upload | absent across all tasks (verified by reviewing the files_modified list — no `anthropic`, no image-compression, no `/api/meals/scan`) |

**All items covered. No gaps. No deferrals beyond what is already locked in ROADMAP/CONTEXT (Phase 4 vision, Phase 7 R2 backup target).**

## Test Plan

- **Backend pytest count:** Phase 2 baseline ~81 → Phase 3 target ≥ ~110 (concrete projection ≈ 152: ghana_food/meal models ~17 + meal_helpers ~7 + ghana_foods_seed ~5 + foods_routes ~8 + meals_routes ~34 = +71 added).
- **Frontend:** `pnpm tsc --noEmit` + `pnpm build` are the v1 gates (no Jest, no Playwright in Phase 3 — matches Phase 2's posture). Visual + flow verification is the 19-step manual smoke in P3-F.2.
- **No new dev dependencies on test runners** — same toolchain as Phase 2.

## Notes for the Executor

- The Render auto-deploy from Phase 1 is still in force: each commit to `main` triggers redeploys of both `fitgh-web` and `fitgh-api`. No deploy work in Phase 3.
- After P3-A.5 lands (db.py extension) and is deployed, run `cd backend && .venv/Scripts/python.exe -m scripts.seed_ghana_foods` ONCE against the production Atlas to populate `ghana_foods`. Capture in SUMMARY. The catalogue stays in sync between repo and DB via the idempotent seeder; future catalogue edits are: edit JSON → commit → re-run seeder.
- Atlas index for `meals`: create once via mongosh after P3-A.5 deploys — `db.meals.createIndex({user_id: 1, logged_at: -1})`. Mirror Phase 2's operator-side workflow.
- `MONGODB_URI_BACKUP` GH Actions secret must be provisioned by the operator AFTER P3-F.1 lands (otherwise the first scheduled run fails with `unauthorized`). Recommend a separate read-only Atlas user for it.
- No new runtime env vars vs Phase 2 — Phase 3 reuses `MONGODB_URI`, `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_URL`. The only NEW secret is `MONGODB_URI_BACKUP` (GH Actions only, not runtime).
- No Anthropic / vision work in Phase 3. Phase 4 will add `ANTHROPIC_API_KEY`, `LLM_VISION_MODEL`, `LLM_DAILY_USD_CAP`, per the ROADMAP Hard Constraints.
- The day-1 multi-component shape (Component.kcal_low/high/confidence + Meal.ai_metadata as nullable) is the contract Phase 4 fills in. Do NOT alter that shape in Phase 3 even where the nulls look "wasteful" — they are the deliberate forward-compat surface.

## Output

After completion, create `.planning/phases/03-meal-log-ghana-table/03-SUMMARY.md` using the standard Phase template, including:
- Final pytest count and route table First Load JS for `/dashboard` and `/history`.
- Per-row provenance for the 25 ghana_foods entries (WAFCT direct / WAFCT composite / USDA composite — useful for Phase 4's table-rematch quality bar).
- Operator-side actions performed: production seeder run, mongosh `meals` index creation, `MONGODB_URI_BACKUP` secret provisioning, first `workflow_dispatch` of nightly-backup.
- Any deviations from the must_haves + their resolution.
- Phase 4 hand-off notes: the day-1 multi-component shape is in place; vision integration is purely additive (POST /meals/scan + Anthropic SDK + the `source: "ai_vision"` + `ai_metadata` fill-in).
