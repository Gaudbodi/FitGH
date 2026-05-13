# Phase 3: Manual Meal Log + Ghana Table — Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — user is driving autonomous mode)

<domain>
## Phase Boundary

Without any AI involvement, a user can search a 25-dish Ghana food catalogue, log a meal as one or more components with portion sliders, see today's running total + remaining-kcal pill on the dashboard, and look back through the last 30 days — proving the **multi-component `meals` schema** works end-to-end before vision lands on top of it in Phase 4.

This is a deliberate hard sequence: the multi-component schema must be the day-1 shape so Phase 4's vision pipeline writes into the same collection rather than a parallel `ai_meals` collection.

</domain>

<decisions>
## Implementation Decisions

### Ghana food catalogue (25 entries)

The planner sources kcal/100g and macros from the **FAO/INFOODS West African Food Composition Table (WAFCT)**. If exact INFOODS values are unavailable for a dish (composite dishes often aren't), the planner uses USDA + WAFCT-component summation with the source field tagged accordingly. Required coverage (planner can extend or substitute up to 25):

**Staples & swallows:** jollof rice, plain rice, banku, fufu (cassava+plantain), kenkey (ga/fante), waakye, tuo zaafi.
**Soups & stews:** light soup, groundnut soup, palm-nut soup, kontomire (palaver sauce), okro stew, shito (sauce).
**Proteins:** tilapia (fried/grilled), chicken thigh (grilled), beef stew, koobi (salted tilapia), wele (cow skin).
**Sides & snacks:** kelewele, plantain (boiled/fried), red-red (beans + plantain), kosua nu meko (eggs in shito), bofrot, koose.

Each entry: `{food_id, name, alt_names[], kcal_per_100g, protein_g_per_100g, fat_g_per_100g, carbs_g_per_100g, portion_defaults: {label, grams}[], category, source, source_confidence}`. `portion_defaults` carry the Ghana cultural units — `{label: "1 ball of banku", grams: 200}`, `{label: "1 dollop of shito", grams: 30}`, etc.

Ship as a static seed file `backend/seeds/ghana_foods.json` loaded into the `ghana_foods` collection via a one-shot seeder script that's idempotent on `food_id`. The collection is read-only at runtime.

### Multi-component `meals` schema (day-1 invariant)

```
{
  _id, user_id, logged_at, source: "manual" | "ai_vision",
  components: [
    {
      name: str,                  # editable display name
      matched_food_id: str | null,# null if free-text (rare; manual is always matched in Phase 3)
      portion_g: int,
      kcal_low: int | null,       # null in Phase 3; vision sets these
      kcal_high: int | null,
      kcal_point: int,            # canonical: table.kcal_per_100g × portion_g / 100, rounded
      protein_g_point: int,
      confidence: float | null,   # null in Phase 3; vision sets
      source: "table" | "llm_then_table_rematch" | "user_corrected"
    }
  ],
  total_kcal: int,                # sum of components[].kcal_point
  total_protein_g: int,
  ai_metadata: null | { model, prompt_hash, image_dims, latency_ms, cost_usd }
}
```

Phase 3 only writes `source: "manual"` with `kcal_low/high = null`, `confidence = null`. Phase 4 fills the AI fields.

### Routes

- `GET /foods?q=jollof&limit=10` — substring + alt_names match, returns up to 10 ranked by relevance.
- `POST /meals` — body has `{logged_at, components: [{food_id, portion_g}]}`. Backend looks up each food, computes `kcal_point` + `protein_g_point` via `kcal_per_100g × portion_g / 100`, persists.
- `GET /meals?date=YYYY-MM-DD` — single-day fetch.
- `GET /meals?days=30` — last 30 days, grouped by day server-side; returns `{date, total_kcal, total_protein_g, meals: [...]}[]`.
- `PATCH /meals/{id}` — edit components or portion_g (recompute totals).
- `DELETE /meals/{id}` — delete a meal and recompute its day's total.

### Dashboard integration

- Top of dashboard adds a **kcal-progress pill**: `"X / Y kcal • Z remaining"` where Y = `daily_kcal_target` and X = today's `sum(meals.total_kcal)`. Pill is RED if X > Y, AMBER if X > Y×0.9, GREEN otherwise. Animation deferred to Phase 5.
- A **"Log meal" button** that opens a side-panel or modal with: search box (typeahead via `/foods?q=`), selected components shown as chips with portion sliders (10g increments, range 10–800g), running meal total, "Save" button.
- A **"Today's meals" list** below: each meal as `{time, components shown as chips, total_kcal}` with tap-to-edit + swipe/X-button-to-delete.
- A **"History" link** to `/history` showing last 30 days as a vertical list grouped by day.

### Mongo indexes

- `ghana_foods.food_id` — unique.
- `ghana_foods.name` + `ghana_foods.alt_names` — text index for search.
- `meals.user_id + logged_at` — compound, descending logged_at for fast day-range queries.

### DATA-01 (nightly backup)

ROADMAP SC-5 mentions a nightly mongodump + R2 upload. For the MVP, **simplify to a GitHub Actions cron job** that runs `mongodump --uri=$MONGODB_URI --gzip --archive=...` nightly at 02:00 UTC and uploads the artifact to GitHub's actions-artifact storage (free, 90-day retention). The `MONGODB_URI` is a GitHub Actions secret. No Cloudflare R2 setup needed for v1. If the user later wants offsite encrypted storage, that's a small follow-up.

### Frontend tech

Reuse Phase 2's RHF + Zod + shadcn primitives. Add `cmdk` (or shadcn's `Command` primitive) for the typeahead search box. Use Tailwind v4 utility classes throughout. No new dependencies if avoidable.

</decisions>

<code_context>
## Existing Code Insights

- **Backend:** Flask blueprint pattern established. `backend/app/routes/profile.py` + `weights.py` are the canonical examples. New routes follow the same shape: blueprint at module top, `@require_auth` decorator on each route, Pydantic model for body validation, `_safe_errors()` helper for 422 responses.
- **DB singleton:** `backend/app/db.py` exposes `db` and adds collections via `db["name"]`. Phase 3 adds `meals` and `ghana_foods` collections there.
- **TDEE helper:** `backend/app/lib/tdee.py` lives at `app/lib/`. Phase 3's kcal-computation helpers (`compute_kcal_for_component`, `recompute_meal_totals`) live in `app/lib/meals.py` for symmetry.
- **Frontend BFF pattern:** `frontend/src/lib/api-server.ts` exposes `forwardToFlask(req, path, opts)` — Phase 3's `/api/meals` and `/api/foods` routes are one-liners using it.
- **Form patterns:** RHF + Zod + shadcn wrappers at `frontend/src/components/forms/rhf-*.tsx`. Reuse them.
- **Dashboard:** `frontend/src/app/dashboard/page.tsx` already fetches `/api/profile` and `/api/me`. Phase 3 adds `/api/meals?date=today` and renders the kcal-progress pill + "Today's meals" list + "Log meal" CTA.

</code_context>

<specifics>
## Specific Ideas

- The 25 dishes should disambiguate between styles where it matters: "kenkey (ga)" vs "kenkey (fante)" have different kcal/100g per FAO/INFOODS. Use the exact INFOODS code in `alt_names` for verifiability (`alt_names: ["WAFCT-09-302", "ga kenkey"]`).
- Portion sliders default to the FIRST entry in `portion_defaults[]` (the most common Ghanaian portion). Diaspora users can override.
- The dashboard kcal pill uses the user's *most recent* `daily_kcal_target` from their profile — not a snapshot at meal-log time. If they edit their profile mid-day, the pill recomputes on next page load.
- Free-text component entry is allowed in Phase 3 only if the user types a name with no `/foods` match — the component is saved with `matched_food_id: null` and `kcal_point` requires the user to also enter a kcal value manually. This is an edge case; default UX always picks a matched food.
- Meal "logged_at" defaults to `now`, but the modal lets the user backdate within the last 7 days (e.g., logging yesterday's dinner this morning). Backdating past 7 days is intentionally blocked.

</specifics>

<deferred>
## Deferred Ideas

- **Image upload + LLM vision:** Phase 4 territory.
- **Cloudflare R2 backup target:** v2; GitHub Actions artifact storage suffices for v1.
- **Macros UI beyond protein:** v2. Phase 3 stores `protein_g_per_100g`, `fat_g_per_100g`, `carbs_g_per_100g` but only displays kcal + protein.
- **Custom user-created foods:** v2. Phase 3 is read-only against the static `ghana_foods` collection.
- **Barcode scan:** v2.
- **Recipes (compose a meal once, log it as a template):** v2.

</deferred>

---

*Phase: 03-meal-log-ghana-table*
*Context auto-generated: 2026-05-13 (discuss skipped per user-driven autonomous mode)*
