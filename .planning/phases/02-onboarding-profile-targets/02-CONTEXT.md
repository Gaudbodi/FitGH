# Phase 2: Onboarding + Profile + Targets — Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — user is driving autonomous mode)

<domain>
## Phase Boundary

A new user finishes a ≤3-screen onboarding in under 60 seconds, leaves with a daily kcal target (and protein target if muscle-gain) shown on the dashboard, can log their weight, edit their profile later, and has signed an explicit consent that meal photos will be sent to an LLM vision provider — plus a working account-deletion path.

Inherits Phase 1's Render-only architecture: Next.js BFF + Flask backend on Render, MongoDB Atlas, Clerk single test instance, no Sentry, no Vercel Analytics, no size-limit CI gate.

</domain>

<decisions>
## Implementation Decisions

### Onboarding flow (3 screens)
- **Screen 1 — Identity:** name, sex (male/female — required for BMR formula), age, locale (Ghana / diaspora).
- **Screen 2 — Body & goal:** height (cm), weight (kg), activity level (5 Mifflin-St Jeor levels), primary goal (weight loss / muscle gain).
- **Screen 3 — Privacy & finish:** timezone (auto-detect with manual override), privacy disclosure naming Anthropic (Claude Sonnet 4.6) as the future meal-image sub-processor, consent checkbox required to finish.

### TDEE calculation
- **Mifflin-St Jeor BMR**, then × activity factor:
  - 1.2 (sedentary), 1.375 (lightly active), 1.55 (moderately active), 1.725 (very active), 1.9 (extra active).
- **Weight loss deficit:** 500 kcal/day default (gives ~0.5 kg/wk loss — sustainable).
- **Muscle gain surplus:** 250 kcal/day default.
- **Hard floors:** 1200 kcal female / 1500 kcal male; display "consult a clinician" disclaimer when the floor is hit.
- **Protein target (muscle gain only):** 1.6 g/kg bodyweight, displayed prominently.

### Storage
- New collection: `profiles` keyed on `clerk_id`, holds name, sex, height_cm, weight_kg (latest), age, locale, timezone, activity_level, primary_goal, daily_kcal_target, daily_protein_g_target, privacy_consent_at, created_at, updated_at.
- New collection: `weight_logs` — one doc per weight entry `{user_id, kg, logged_at}`. Indexed on `user_id + logged_at`.
- Update `users` collection: nothing new (the email/clerk_id pair stays in users; profile lives in profiles for separation of identity vs body data).

### Edit profile + weight log
- `/profile` page reuses onboarding form components.
- "Edit" toggle on each section; recompute kcal target on save.
- Weight-log entry on the dashboard (single number input + "Log" button). History viewable below.

### Privacy disclosure
- A stub `/privacy` page in Next.js naming Anthropic as the meal-image sub-processor, plus Clerk, MongoDB Atlas, Render as data processors.
- Linked from screen 3 of onboarding and from a footer.
- Real Privacy Policy copy is Phase 7 work.

### Account deletion
- Settings page → "Delete account" button → confirmation modal → calls Flask `DELETE /me` (which deletes profile + weight_logs + users record) → calls Clerk's `users.delete()` to remove the auth record → signs the user out.
- No Clerk webhooks (those were dropped in Phase 1 Slice E.1) — synchronous Flask + Clerk SDK cascade.

### UI shape
- Existing shadcn/ui primitives + Tailwind v4. Form library: **React Hook Form 7.x + Zod 3.x + @hookform/resolvers/zod** (already in the project plan; install if not already).
- 3 screens render as a single page with conditional rendering (no router-level multi-step) so the back/forward feel is instant.

### Animation deferral
- Phase 5 owns the Rive avatar + animated kcal ring. Phase 2 ships a STATIC dashboard with the kcal target visible as a number + a basic progress placeholder.

</decisions>

<code_context>
## Existing Code Insights

- `backend/app/middleware/auth.py` stashes `g.clerk_user_id` and `g.clerk_email` from JWT claims. Phase 2 routes use `@require_auth` and read those.
- `backend/app/routes/me.py` already implements sync-on-demand upsert into `users`. Phase 2 can extend this with profile join, or add a separate `/profile` route — the latter keeps schemas clean.
- `frontend/middleware.ts` wires Clerk's `clerkMiddleware` with `createRouteMatcher`. Phase 2 needs to protect `/onboarding`, `/profile`, `/settings` routes.
- `frontend/src/app/dashboard/page.tsx` is currently a server component that calls `/api/me`. Phase 2 expands it to: redirect to `/onboarding` if profile is missing, otherwise show kcal target + weight-log input.
- No `forms/` directory yet — RHF + Zod patterns need establishing.
- `shared/schemas/user.schema.json` exists for the User contract. Phase 2 adds `profile.schema.json` and `weight-log.schema.json`.

</code_context>

<specifics>
## Specific Ideas

- Conditional protein-target display: only render the protein-grams card when `primary_goal == "muscle_gain"`. Weight-loss users see kcal target only.
- Mifflin-St Jeor must use SI units throughout — height in cm, weight in kg. No imperial conversion. Even diaspora users on the Ghana app accept cm/kg (this is consistent with how Ghanaian gyms operate).
- Locale field captures "Ghana" or "diaspora-{country}" — defer the diaspora-country picker if it adds complexity; "diaspora" as a single bucket is fine for v1.
- The privacy consent boolean stamps `privacy_consent_at` with a timestamp on the profile doc, not a separate audit log. Sufficient for v1 GDPR posture.

</specifics>

<deferred>
## Deferred Ideas

- Email verification on sign-up (Clerk handles this if enabled; do not add a separate UI flow).
- Multi-step wizard with progress bar — single page with conditional rendering is simpler.
- Reminders to log weight ("you haven't logged in 3 days") — Phase 5 or later.
- Imperial unit toggle (lbs/inches) — defer to a future post-v1 milestone.
- Account export ("download my data") — that's Phase 7 (LEGAL-02).

</deferred>

---

*Phase: 02-onboarding-profile-targets*
*Context auto-generated: 2026-05-13 (discuss skipped per user-driven autonomous mode)*
