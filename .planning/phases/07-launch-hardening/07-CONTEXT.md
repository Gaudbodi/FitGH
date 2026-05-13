# Phase 7: Launch Hardening — Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — user driving autonomous mode)

<domain>
## Phase Boundary

Verify, document, and harden everything that separates "demoable" from "safely launchable." Ghana-edge latency measurement, real privacy policy (no stub), data-export + working account-delete, health-claim copy audit, Anthropic spend alerts, golden-set re-run on the production model pin, **and the Phase 6 carry-over: Lighthouse mobile ≥ 90 on `/workouts`**.

</domain>

<decisions>
## Implementation Decisions

### Phase 6 carry-over — Lighthouse mobile on `/workouts` (PERF-03)

Cold Lighthouse score on `/workouts` is 51–53/100 because the root `app/layout.tsx` wraps everything in `ClerkProvider`, which pulls in `accounts.dev` (~312 kB) + 1.8 s main-thread time. `/workouts` is a public route that doesn't need Clerk at all.

**Fix:** split the App Router into route groups:
- `frontend/src/app/(public)/` — `/workouts`, `/workouts/[id]`, `/privacy`, `/`, `/sign-in`, `/sign-up`. Layout has NO ClerkProvider (Clerk's sign-in/up components self-bootstrap).
- `frontend/src/app/(authed)/` — `/dashboard`, `/profile`, `/settings`, `/onboarding`, `/history`. Layout owns `ClerkProvider`.
- Root `layout.tsx` becomes the bare shell (HTML + body + Tailwind + footer).

Target: `/workouts` Performance ≥ 90 mobile post-fix. Verify with the operator Lighthouse command from Phase 6 SUMMARY.

### Real privacy policy (LEGAL-01)

Replace `frontend/src/app/privacy/page.tsx` (Phase 2 stub) with a real privacy policy. Auto-generated from a template covering:

1. **What we collect** — Clerk identity (email, OAuth tokens); profile (name, sex, height, weight, age); meals + components + portions; weight logs; meal photos (transient — see §3); user_corrections.
2. **What we don't keep** — meal images: bytes sent to Anthropic Claude Sonnet 4.6, then discarded server-side (no GridFS, no R2, no logs).
3. **Sub-processors** — explicit list with what each gets: **Anthropic (Claude Sonnet 4.6)** receives base64 meal images for kcal estimation; **Clerk** holds authentication identity; **MongoDB Atlas** holds profile + meals + weight logs; **Render** hosts the application + ephemeral logs; **GitHub Actions** runs the nightly mongodump backup (encrypted artifact, 90-day retention).
4. **User rights (GDPR-style)** — export via /api/account/export, delete via Settings → Delete Account (already shipped Phase 2).
5. **Contact** — `francisyiryel@gmail.com` (or a generic `privacy@…` if a domain is acquired).
6. **Last updated** — 2026-05-13.

**Disclaimer in the page header:** "This privacy policy is provided in good faith but has not been reviewed by counsel. Review with a lawyer before commercial launch."

### Data export endpoint (LEGAL-02)

New Flask route `GET /me/export` (and BFF `/api/account/export`) that streams a JSON archive of:
- profile (full doc)
- weight_logs (all entries)
- meals (all entries with components)
- user_corrections (all entries)
- vision_usage (counts only, no images obviously)

Content-Type: `application/json`. Filename: `fitgh-export-{clerk_id}-{date}.json`. No pagination — even for power users this is ≤10 MB.

Add a "Download my data" button to `/settings` (between the profile-edit link and the delete-account button).

### Health-claim copy audit (LEGAL-03)

- **Forbidden phrases:** "will help you lose weight", "achieves your goal", "guaranteed results", "medical advice", "treats" + any disease/condition name.
- **Required disclaimer location:** onboarding consent screen + footer of every page: "FitGH is a fitness tracking tool, not medical advice. Consult a qualified clinician for health decisions."
- **Audit method:** grep across `frontend/src/**/*.{ts,tsx}`, `backend/app/**/*.py`, and `.planning/` (the planning prose doesn't ship but we want consistency). Manual review of any matches. Disclaimer added if absent.

### Anthropic spend hard cap (PERF-04 + carry-over from Phase 4)

Phase 4 shipped the per-user 8/day cap + global $/day breaker via `VISION_DAILY_CAP_USD` env var. Phase 7 adds:
- **Anthropic console-side cap:** operator follow-up — set a monthly spend ceiling in the Anthropic console.
- **Email/webhook alert:** the existing `COST_ALERT_WEBHOOK_URL` already fires at `$/DAU/day > $0.05`. Document the recommended Discord/Slack webhook URL in `.env.example`.
- **STATUS doc update:** mention current cost at deploy time so the operator has a benchmark.

### Golden-set re-run (carry-over from Phase 4)

Phase 4 left a `backend/tests/golden_set/` placeholder. Phase 7 SHOULD:
- Add 10–30 reference photos of Ghanaian dishes (jollof, banku, waakye, etc.) sourced from public-domain food photography or AI-generated (note the source in a manifest).
- Tag each with expected components + kcal range from the Phase 3 Ghana food table.
- `pytest -m golden` runs them all gated on `RUN_GOLDEN=1`.
- Report: MAPE (mean absolute percentage error) on total kcal, dish-name accuracy.
- **Target from ROADMAP:** MAPE < 25%.

**Realistically achievable in this phase:** 10 placeholder entries + the harness. Real photos + curation is a v1.1 operator task. Mark the runner as PASS/FAIL by golden-set entry count + harness functional.

### WebPageTest Lagos (PERF-04)

Operator-side. Document the test URL (https://www.webpagetest.org/) + the location selection (Lagos, Nigeria — Chrome — 4G profile). Run against the Render production URL post-Phase-7-deploy and record p75 TTFB in SUMMARY. **If > 2 s, document the Cloudflare-in-front fallback** but DON'T implement it (per the 2026-05-12 rewrite — defer until measurement justifies).

### Working tree sweep

Several CONTEXT.md / PLAN.md files from Phases 2–6 are still untracked per the Phase 6 SUMMARY. The Phase 6 close-commit `76bc079` claimed to sweep them — verify and finalize.

</decisions>

<code_context>
## Existing Code Insights

- `frontend/src/app/layout.tsx` — currently has ClerkProvider wrapping everything. Phase 7 splits into route groups.
- `frontend/src/app/privacy/page.tsx` — Phase 2 stub; replace.
- `frontend/src/app/settings/page.tsx` — Phase 2; add "Download my data" button.
- `backend/app/routes/me.py` — has DELETE handler from Phase 2. Add `GET /me/export`.
- `frontend/src/app/api/account/` — has DELETE BFF; add export route.
- `backend/tests/golden_set/` — Phase 4 placeholder.

</code_context>

<specifics>
## Specific Ideas

- Privacy policy uses plain language ("we" / "you"); avoid legalese. Sections numbered for navigation. Render with Tailwind prose classes for readability.
- Data export JSON: pretty-printed (`indent=2`) for human readability; include a `_export_metadata` field with `export_date`, `app_version` (git short SHA), and `processor_versions`.
- Health-claim audit: write a Python script `scripts/audit_copy.py` that greps and emits findings to stdout. Re-runnable per release.
- Golden-set harness: `backend/tests/test_golden_vision.py` with `pytest.mark.skipif(not os.getenv("RUN_GOLDEN"), reason="…")`. Each entry: `{photo_path, expected_components: [{name, kcal_range}], notes}`.

</specifics>

<deferred>
## Deferred Ideas

- **Cloudflare-in-front:** only if Lagos WebPageTest p75 TTFB > 2 s. Defer until measurement justifies.
- **Lawyer-reviewed privacy policy:** v1.1 operator action.
- **Custom domain (fitgh.com):** v1.1 operator action; `*.onrender.com` is acceptable for soft launch.
- **Real golden-set with 30 curated photos:** v1.1 operator + Ghanaian-user contribution.
- **Lighthouse Accessibility 100/100:** v1.1 (94/100 currently is acceptable for soft launch).
- **Anthropic enterprise/volume pricing renegotiation:** post-1000-DAU.

</deferred>

---

*Phase: 07-launch-hardening*
*Context auto-generated: 2026-05-13 (discuss skipped per user-driven autonomous mode)*
