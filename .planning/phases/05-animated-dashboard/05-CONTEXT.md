# Phase 5: Animated Dashboard — Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — user driving autonomous mode)

<domain>
## Phase Boundary

The dashboard stops being a skeleton. A static-SVG avatar reflects the user's sex × BMI band × goal direction; the kcal ring animates as meals are logged; Recharts shows weight (30/90-day) and weekly kcal-vs-target progress; copy and CTAs adapt to the user's goal; a soft-streak with 1-day grace runs. All honours `prefers-reduced-motion` and auto-disables motion on slow connections.

</domain>

<decisions>
## Implementation Decisions

### Avatar: static SVG sprite (Rive deferred to v1.1)

**Locked deviation from CLAUDE.md stack pick.** Rive runtime + `.riv` file artist (~£200–500) was the canonical choice. Static SVG ships now with zero external dependencies and a smaller bundle. Rive can be revisited in a post-MVP milestone if the design system demands it.

- **Sprite sheet:** one SVG file at `frontend/public/avatar-sprite.svg` containing 20 avatar states (5 BMI bands × 2 sexes × 2 goal-directions). Each state is a `<g id="state-N">` block — referenced via `<use href="#state-N">`. Hand-drawn flat-style, ~15-20kB gzipped total.
- **States:** BMI bands: under-18.5 (slim), 18.5–25 (healthy-lean), 25–28 (healthy-firm), 28–32 (heavier), 32+ (much-heavier). Sexes: male, female. Goal-direction: trending-toward-target / steady / trending-away. Render component computes the state key from `profile.weight_kg + height_cm + sex + primary_goal + recent_weight_log_trend`.
- **CSS animations:** subtle breathing (chest expand) via `@keyframes` + `transform: scale()`; eye-blink every 4s. Wrapped in `@media (prefers-reduced-motion: no-preference)` so reduced-motion users see static.

### Kcal ring

- **SVG `<circle stroke-dasharray>` animation.** When a meal lands → state diff triggers CSS transition from `stroke-dashoffset: old` to `stroke-dashoffset: new` over 600ms.
- **Color bands:** GREEN under target, AMBER 90–100% of target, RED over target. Inherits Phase 3's `KcalPill` color logic — share the helper.
- **Reduced-motion:** transition collapses to 0ms; user sees instant update.

### Charts (Recharts)

- **Install `recharts`** (~80kB minified, ~25kB gzipped); not yet in package.json.
- **Weight chart:** Line chart, 30-day default, toggle to 90-day. Y-axis: weight kg; X-axis: date. Reads from `/api/weights?days=30`.
- **Weekly kcal-vs-target:** Bar chart, last 7 days. Each bar = day's `total_kcal`, target line overlay at `profile.daily_kcal_target`. Reads from `/api/meals?days=7` + computes per-day totals client-side (server already groups by day per Phase 3's `?days=30` endpoint — extend to `?days=7`).
- **Recharts animations:** native fade-in + draw-on-mount; respects `prefers-reduced-motion` via prop.
- **Lazy-load:** `next/dynamic` import for the charts so `/dashboard` First Load JS doesn't balloon. Charts mount client-side after main content paints.

### Goal-aware copy

- Weight-loss user: "X kcal under target" framing, "loss target this week: −0.5 kg" pill.
- Muscle-gain user: "Y g protein remaining" prominently, "gain target this week: +0.25 kg" pill.
- All copy keys live in `frontend/src/lib/dashboard-copy.ts` — single source of truth, easy to localize later.

### Soft-streak with 1-day grace

- **Definition:** A "streak day" is a day where the user logged at least one meal.
- **Soft-streak:** Yesterday missed but day-before-yesterday logged → streak shown as "paused" (e.g., yellow badge), NOT reset. Two consecutive missed days → reset to 0.
- **Stored on profile:** `profiles.streak_count`, `profiles.streak_last_logged_at` (datetime), `profiles.streak_state` (`"active" | "paused" | "broken"`). Recomputed server-side on every meal POST.
- **Backend:** add `app/lib/streak.py` with `compute_streak(user_id, today, last_logged_at, current_count) -> {count, state}` pure helper + unit tests.

### Slow-connection detection

- **`navigator.connection.effectiveType`** check on mount. If `"2g"` or `"3g"` (or `saveData: true`): set `motion-disabled` data attribute on `<html>` → CSS rules disable all transitions/animations site-wide.
- **Reduced-motion:** same data attribute set when `(prefers-reduced-motion: reduce)` matches.

### Bundle budget

- `/dashboard` First Load JS is currently 231 kB (Phase 4 final). Recharts adds ~25 kB gzipped, avatar SVG adds ~3 kB inline. Lazy-loading charts via `next/dynamic` keeps initial paint fast. Target ≤ 260 kB First Load JS — manual check at phase boundary, no CI gate.

</decisions>

<code_context>
## Existing Code Insights

- `frontend/src/app/dashboard/page.tsx` — current server component fetching `/api/profile`, `/api/me`, `/api/meals`. Phase 5 extends with weight + weekly-kcal data sourced from existing endpoints; no new BFF routes needed for charts.
- `frontend/src/app/dashboard/kcal-pill.tsx` (Phase 3) — already has RED/AMBER/GREEN logic. The ring shares this; refactor color logic into `frontend/src/lib/kcal-color.ts` (shared helper).
- `backend/app/routes/meals.py` `GET /meals?days=7` already grouped — reuse for the weekly chart.
- `backend/app/routes/weights.py` `GET /weights` returns history — reuse for the weight chart.
- `backend/app/routes/profile.py` PATCH already recomputes targets — streak field added to the same PATCH/GET response.
- `backend/app/models/profile.py` — extend with `streak_count: int = 0`, `streak_last_logged_at: datetime | None = None`, `streak_state: Literal["active", "paused", "broken"] = "active"`.

</code_context>

<specifics>
## Specific Ideas

- Avatar SVG uses CSS variables for color so the design system can re-theme without re-exporting (skin-tone, clothing-color, accent).
- Streak badge is a small chip near the kcal ring: 🔥 + count, badge colored by `streak_state` (green=active, yellow=paused, gray=broken).
- Weight-chart hover shows the exact value + date in a tooltip; tooltip respects `prefers-reduced-motion` (no slide-in).
- Server-rendered first paint: dashboard renders static placeholder values from server data; charts hydrate client-side. Avoids layout shift.

</specifics>

<deferred>
## Deferred Ideas

- **Rive `.riv` avatar:** v1.1+. Will require an artist; the state-machine interface design from research/SUMMARY.md still applies if revisited.
- **Lottie animations:** never. Rive's role is filled by static SVG; Lottie would be a second animation runtime for no clear win.
- **Confetti / celebration animations on hitting target:** v1.1.
- **Streak heatmap (GitHub-style year view):** v1.1.
- **Detailed macro breakdown chart (carbs/fat/protein over time):** v2 (depends on multi-component schema's nutrient fields, which we have but don't display yet).
- **Push notifications for streak risk:** v2.

</deferred>

---

*Phase: 05-animated-dashboard*
*Context auto-generated: 2026-05-13 (discuss skipped per user-driven autonomous mode)*
