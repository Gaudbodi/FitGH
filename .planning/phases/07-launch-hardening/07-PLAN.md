---
phase: 07-launch-hardening
plan: 07
type: execute
wave: 1
depends_on: []
files_modified:
  # Slice A — Lighthouse fix (PERF-03 carry-over)
  - frontend/src/app/layout.tsx
  - frontend/src/app/(public)/layout.tsx
  - frontend/src/app/(authed)/layout.tsx
  - .planning/phases/07-launch-hardening/lighthouse-postfix.md
  # Slice B — Privacy policy
  - frontend/src/app/privacy/page.tsx
  - frontend/src/app/settings/page.tsx
  # Slice C — Data export
  - backend/app/routes/me.py
  - backend/tests/test_me_export.py
  - frontend/src/app/api/account/export/route.ts
  - frontend/src/app/settings/page.tsx
  - frontend/src/app/settings/download-data-button.tsx
  # Slice D — Copy audit + golden set
  - scripts/audit_copy.py
  - scripts/README-audit-copy.md
  - backend/tests/golden_set/test_golden_vision.py
  - backend/tests/golden_set/manifest.json
  - backend/tests/golden_set/photos/01-jollof-with-chicken.jpg
  - backend/tests/golden_set/photos/02-banku-tilapia-shito.jpg
  - backend/tests/golden_set/photos/03-waakye.jpg
  - backend/tests/golden_set/photos/04-fufu-light-soup.jpg
  - backend/tests/golden_set/photos/05-kelewele.jpg
  - backend/tests/golden_set/photos/06-red-red.jpg
  - backend/tests/golden_set/photos/07-kontomire-stew.jpg
  - backend/tests/golden_set/photos/08-omotuo-groundnut-soup.jpg
  - backend/tests/golden_set/photos/09-tuo-zaafi.jpg
  - backend/tests/golden_set/photos/10-kenkey-fried-fish.jpg
  - .planning/phases/07-launch-hardening/golden-set-result.md
  # Slice E — Operator instructions + traceability
  - LAUNCH.md
  - .env.example
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/STATE.md
  - .planning/phases/07-launch-hardening/07-SUMMARY.md
autonomous: true
requirements:
  - PERF-03
  - PERF-04
  - LEGAL-01
  - LEGAL-02
  - LEGAL-03

must_haves:
  truths:
    - "Visiting /workouts on Render (or any public route — /, /privacy, /sign-in, /sign-up, /workouts/[id]) does NOT load the Clerk client SDK at all; the ClerkProvider only mounts inside the (authed) route-group layout, so public-route HTML transfers no accounts.dev script and emits no Clerk-related third-party blocking time (PERF-03)"
    - "Lighthouse mobile re-run on /workouts post-deploy is recorded in .planning/phases/07-launch-hardening/lighthouse-postfix.md with Performance / Accessibility / Best Practices scores and the four core metrics (FCP / LCP / TBT / TTI); Performance target ≥ 90 is documented; if not hit, the residual bottleneck is named and a v1.1 mitigation is proposed (PERF-03 — target documented, not hard-blocked)"
    - "WebPageTest Lagos p75 TTFB on /dashboard is documented in 07-SUMMARY.md as an operator follow-up run, with the exact wptlocation= URL parameter and 4G profile selection; the recorded p75 TTFB ≤ 2 s OR a Cloudflare-in-front fallback is documented (NOT implemented) (PERF-04)"
    - "GET /privacy renders a real privacy policy (no 'stub' header) numbering sections 1–6: what we collect, what we don't keep, sub-processors (Anthropic Claude Sonnet 4.6 / Clerk / MongoDB Atlas / Render / GitHub Actions backup — NOT Cloudflare R2; R2 is not used in v1.0), user rights (export + delete), contact email francisyiryel@gmail.com, last-updated date; a 'not reviewed by counsel' disclaimer renders prominently in the header (LEGAL-01)"
    - "The /privacy page is linked from (a) the global footer in (public)/layout.tsx AND (authed)/layout.tsx, (b) onboarding screen 3 (Phase 2 already links to /privacy — verify still works after route-group split), (c) /settings as a 'Privacy policy' link (LEGAL-01)"
    - "Flask GET /me/export returns 200 with Content-Type application/json and a JSON body containing user / profile / weight_logs / meals / user_corrections / vision_usage arrays plus a _export_metadata object {export_date, app_version (git short SHA from FITGH_GIT_SHA env or 'unknown'), schema_version: 1}; @require_auth enforces JWT; the route reads user_id ONLY from g.clerk_user_id (NEVER from request body or query) (LEGAL-02)"
    - "BFF /api/account/export forwards GET to Flask /me/export via the existing forwardToFlask helper and sets Content-Disposition: attachment; filename=\"fitgh-export-{clerk_id}-{YYYY-MM-DD}.json\" so the browser downloads the file rather than rendering it (LEGAL-02)"
    - "/settings shows a 'Download my data' button between the (existing) profile-edit area and the (existing) delete-account button; clicking it fetches /api/account/export with credentials, triggers a browser download via Blob + createObjectURL + anchor click, and shows a Sonner toast on success/failure (LEGAL-02)"
    - "scripts/audit_copy.py greps frontend/src/**/*.{ts,tsx,md} + backend/app/**/*.py for forbidden phrases ('will help you lose weight', 'achieves your goal', 'guaranteed results', 'medical advice' EXCEPT inside the disclaimer string, 'treats <disease>') AND asserts the standard disclaimer 'FitGH is a fitness tracking tool, not medical advice. Consult a qualified clinician for health decisions.' is present in the (public)/layout.tsx footer AND on onboarding screen 3; prints findings to stdout with file:line context; exits 0 on clean / 1 on findings (LEGAL-03)"
    - "scripts/audit_copy.py has been executed in this phase; all findings are either fixed (forbidden phrase rewritten) or documented in 07-SUMMARY.md as accepted (e.g. the word 'guaranteed' inside a third-party Free Exercise DB licence text is documented and exempted by file-allowlist) (LEGAL-03)"
    - "backend/tests/golden_set/test_golden_vision.py runs under pytest with @pytest.mark.skipif(os.environ.get('RUN_GOLDEN_SET') != '1', ...) so CI default is SKIP; with RUN_GOLDEN_SET=1 and ANTHROPIC_API_KEY set it iterates the 10 manifest entries, calls the production vision pipeline (Anthropic Sonnet 4.6 via app.lib.vision), and asserts MAPE < 25 % AND dish-name accuracy ≥ 70 % aggregated across entries — failures print per-entry diagnostics to stdout but do NOT block phase close per PROJECT.md (the v1.0 deliverable is the harness + 10 entries, not the < 25 % MAPE outcome) (PERF-04 + LEGAL-02 traceability)"
    - "backend/tests/golden_set/manifest.json lists 10 Ghana-dish photo entries; each entry has {photo: relative path under photos/, source: 'placeholder' | 'public-domain' | 'ai-generated', expected_components: [{name: matches the ghana_foods catalogue, kcal_low: int, kcal_high: int}], expected_total_kcal_low: int, expected_total_kcal_high: int, notes: string}; the 10 photos cover jollof / banku / waakye / fufu / kelewele / red-red / kontomire / omotuo / tuo-zaafi / kenkey to span the 25-dish catalogue's headline entries"
    - "The 10 photo files exist under backend/tests/golden_set/photos/ as JPEGs; for v1.0 they MAY be 1-pixel placeholder JPEGs generated by Pillow with a colour-coded label baked in (acceptable per CONTEXT.md 'Realistically achievable: 10 placeholder entries + harness'); the manifest.source field for each entry records 'placeholder' so a future operator pass knows which photos to replace with real Ghana-food imagery"
    - "Golden set has been executed at least once in this phase with mocked Anthropic (when ANTHROPIC_API_KEY is unset, the harness uses a deterministic fake that returns each entry's expected total_kcal±5%); the result is recorded in .planning/phases/07-launch-hardening/golden-set-result.md with per-entry MAPE + dish accuracy + aggregate MAPE; with the deterministic fake MAPE < 25 % passes by construction — real-Anthropic re-run is an operator follow-up post-deploy"
    - "LAUNCH.md at the repo root documents the four operator-side launch steps: (1) Anthropic console hard monthly spend cap (~$200 v1, link to the console), (2) set COST_ALERT_WEBHOOK_URL Discord/Slack URL (cite where the existing Phase 4 webhook fires), (3) WebPageTest Lagos run instructions with the exact URL + 4G profile selection + which TTFB column to read for p75, (4) golden-set real-Anthropic re-run instructions (RUN_GOLDEN_SET=1 ANTHROPIC_API_KEY=… pytest backend/tests/golden_set)"
    - ".env.example documents COST_ALERT_WEBHOOK_URL with a comment referencing the $/DAU/day > $0.05 single-fire latch from Phase 4 (OBS-03)"
    - "Working-tree sweep complete: git status (excluding GEMINI.md which is operator-owned) shows zero leftover untracked .planning/ artifacts at phase close; all CONTEXT.md / PLAN.md / SUMMARY.md from prior phases that were untracked are either committed in the phase-close commit or documented in 07-SUMMARY.md with a one-line reason for exclusion"
    - "07-SUMMARY.md exists with the standard frontmatter (phase / plan / subsystem / tags / dependency-graph / tech-stack / key-files / key-decisions / requirements-completed / metrics) and lists PERF-03 + PERF-04 + LEGAL-01 + LEGAL-02 + LEGAL-03 in requirements-completed; .planning/REQUIREMENTS.md flips PERF-03 + PERF-04 + LEGAL-01/02/03 to Complete in BOTH the v1 section AND the Traceability section; .planning/ROADMAP.md marks Phase 7 row Complete; .planning/STATE.md updates progress to 7/7 phases complete"
    - "Backend pytest count is ≥ 296 (≥ 4 new tests across test_me_export.py: 200 happy path + empty-account path + missing-auth 401 + cross-user-isolation); frontend vitest count is unchanged at 100 (no new frontend tests this phase — download button is a thin wrapper, settings copy audit is a script not a vitest) OR rises by 1 if a vitest assertion is added for the download-data-button click handler"
    - "Anti-patterns NOT introduced: NO Cloudflare-in-front wiring (only documented as a fallback), NO custom-domain config, NO @sentry/nextjs / @sentry-sdk re-introduction, NO @vercel/analytics, NO size-limit CI gate, NO gitleaks CI custom rules — every absence is verified by a final grep across the diff before committing"

  artifacts:
    - path: "frontend/src/app/layout.tsx"
      provides: "Stripped root layout — bare HTML shell. Only owns: <html lang='en'><body class='…'>, Inter font variable, ServicePausedBanner (server component — no Clerk dependency), Toaster, the global <footer>, and the children slot. NO ClerkProvider. NO RegisterSW / OfflineIndicator / InstallPrompt (those are auth-aware enough to move to (authed)/layout.tsx since they only matter for signed-in users posting meals). The footer renders the Free Exercise DB attribution + /privacy link + the standard health disclaimer string from LEGAL-03."
      exports: ["RootLayout (default)"]
    - path: "frontend/src/app/(public)/layout.tsx"
      provides: "Layout for the (public) route group. Wraps children in a <main> shell with no auth context. Hosts /, /workouts, /workouts/[id], /privacy, /sign-in, /sign-up. NO ClerkProvider — Clerk's <SignIn /> and <SignUp /> components self-bootstrap from the publishable key env var. Renders just `{children}`; the global footer + ServicePausedBanner are in the root layout above. This is the architectural fix for PERF-03."
      exports: ["PublicLayout (default)"]
    - path: "frontend/src/app/(authed)/layout.tsx"
      provides: "Layout for the (authed) route group. Wraps children in <ClerkProvider> (which reads NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY / CLERK_SECRET_KEY from env). Mounts RegisterSW + OfflineIndicator + InstallPrompt inside the ClerkProvider tree so they can call useUser() if needed. Hosts /dashboard, /profile, /settings, /onboarding, /history. middleware.ts already gates these as protected — no behavioural change, just relocation."
      exports: ["AuthedLayout (default)"]
    - path: ".planning/phases/07-launch-hardening/lighthouse-postfix.md"
      provides: "Manual Lighthouse mobile re-run report for /workouts after the ClerkProvider relocation deploy. Captures cold + warm Performance / Accessibility / Best Practices, the four core metrics (FCP / LCP / TBT / TTI), and the third-party blocking time (which should now be ≈0 ms for accounts.dev). If Performance ≥ 90, declare PERF-03 Complete; if 70–89, document the residual bottleneck (likely Render free-tier document latency) and propose v1.1 mitigation (Render Starter or Cloudflare-in-front) without blocking phase close."
      exports: []
    - path: "frontend/src/app/privacy/page.tsx"
      provides: "Real privacy policy. Server component. Tailwind `prose prose-sm md:prose-base` wrapper for readability. Sections numbered 1–6 per CONTEXT.md template: (1) What we collect, (2) What we don't keep, (3) Sub-processors (Anthropic Claude Sonnet 4.6 + Clerk + MongoDB Atlas + Render + GitHub Actions for nightly backups; do NOT mention Cloudflare R2 — DATA-01 currently uses GH Actions artifact storage with 90-day retention), (4) User rights (export via /api/account/export + delete via /settings), (5) Contact (francisyiryel@gmail.com), (6) Last updated 2026-05-13. The header carries an amber-bordered disclaimer card: 'This privacy policy is provided in good faith but has not been reviewed by counsel. Review with a lawyer before commercial launch.' Anchor links at the top for in-page navigation. Replaces the entire Phase 2 stub body."
      exports: ["PrivacyPage (default)", "metadata"]
    - path: "frontend/src/app/settings/page.tsx"
      provides: "Modified to add a 'Data' section between the existing header and 'Danger zone'. The Data section contains: (a) a <Link href='/privacy'>Privacy policy</Link>, (b) the new <DownloadDataButton /> client component. The existing DeleteAccountButton remains in the Danger zone unchanged."
      exports: ["SettingsPage (default)", "dynamic"]
    - path: "frontend/src/app/settings/download-data-button.tsx"
      provides: "Client component. Renders a primary button 'Download my data (JSON)'. On click: fetch('/api/account/export', { credentials: 'same-origin' }) → on 200 read response.blob() + the Content-Disposition filename → create object URL + anchor.click() to trigger browser download → revoke URL after 1 s → toast.success('Your data has started downloading.'). On non-200: toast.error('Could not export your data. Please try again later.'). Disables the button while the request is in flight; uses an aria-busy attribute for accessibility."
      exports: ["DownloadDataButton (default)"]
    - path: "backend/app/routes/me.py"
      provides: "Adds a new @bp.get('/me/export') handler decorated with @require_auth. Reads g.clerk_user_id (T-07-01: never from body/query). Queries: users.find_one({clerk_id}), profiles.find_one({clerk_id}), weight_logs.find({user_id}).sort('logged_at', -1) → list, meals.find({user_id}).sort('logged_at', -1) → list, user_corrections.find({user_id}).sort('corrected_at', -1) → list, vision_usage.find({user_id}) → list (counts only, no body content). Serializes ObjectId via str() + datetimes via .isoformat(). Wraps everything in {_export_metadata: {export_date: iso, app_version: os.environ.get('FITGH_GIT_SHA', 'unknown'), schema_version: 1}, user: …, profile: …, weight_logs: […], meals: […], user_corrections: […], vision_usage: […]}. Returns jsonify(…) with response.headers['Content-Type'] = 'application/json'. The DELETE handler from Phase 2 is preserved verbatim."
      exports: ["bp", "get_me_export"]
    - path: "backend/tests/test_me_export.py"
      provides: "pytest module with ≥ 4 tests using the existing conftest.py fixtures (test_client + mock_clerk_jwt). (1) test_export_happy_path: seed 1 user + 1 profile + 2 weight_logs + 2 meals + 1 user_correction + 1 vision_usage; GET /me/export → 200; assert all six arrays + _export_metadata present; assert ObjectIds are strings + datetimes are ISO. (2) test_export_empty_account: seed only the user doc; GET /me/export → 200; weight_logs/meals/user_corrections/vision_usage are [] (not null). (3) test_export_unauth: GET /me/export without bearer → 401. (4) test_export_cross_user_isolation: seed user A + user B with distinct weight_logs; GET /me/export as user A; assert NO user B data leaks (T-07-01 mitigation test)."
      exports: []
    - path: "frontend/src/app/api/account/export/route.ts"
      provides: "BFF route handler. `export const dynamic = 'force-dynamic';`. `export async function GET()` calls forwardToFlask('GET', '/me/export') and then mutates the response by adding `Content-Disposition: attachment; filename=\"fitgh-export-{clerk_id}-{YYYY-MM-DD}.json\"`. The clerk_id is read from auth() (server-side Clerk helper); the date is new Date().toISOString().slice(0, 10). If forwardToFlask returns non-2xx, pass it through unchanged (no Content-Disposition added)."
      exports: ["GET", "dynamic"]
    - path: "scripts/audit_copy.py"
      provides: "Python 3.12 script. argparse: --root (default '.'), --strict (exit 1 on findings vs default exit 0 with summary). Scans frontend/src/**/*.{ts,tsx}, frontend/src/**/*.md, backend/app/**/*.py, .planning/**/*.md against a FORBIDDEN list and a REQUIRED list. FORBIDDEN: case-insensitive regex for 'will help you lose weight', 'achieves your goal', 'guaranteed results', 'medical advice' (with allowlist: file path == 'frontend/src/app/(public)/layout.tsx' AND line contains 'not medical advice' — that's the disclaimer itself), 'treats <disease>'. REQUIRED: the exact disclaimer string 'FitGH is a fitness tracking tool, not medical advice. Consult a qualified clinician for health decisions.' must appear in BOTH (a) the (public)/layout.tsx footer (or in a shared <HealthDisclaimer/> component imported there) AND (b) one of frontend/src/app/onboarding/screen-3*.tsx OR consent-step*.tsx. Prints findings as `path:line: <category> <match>`. Exits 0 unless --strict and findings exist."
      exports: []
    - path: "scripts/README-audit-copy.md"
      provides: "How-to: `python scripts/audit_copy.py` (smoke) or `python scripts/audit_copy.py --strict` (CI gate when one's added in v1.1). Lists the forbidden phrases and the required disclaimer string. Notes the LICENSES.md / vendor file allowlist."
      exports: []
    - path: "backend/tests/golden_set/test_golden_vision.py"
      provides: "pytest module. Top-level skipif: @pytest.mark.skipif(os.environ.get('RUN_GOLDEN_SET') != '1', reason='Set RUN_GOLDEN_SET=1 to run')`. Loads manifest.json; for each entry: opens photo bytes; if ANTHROPIC_API_KEY is set, calls app.lib.vision.analyze_meal(image_bytes, …) directly (bypasses the Flask route — pure library function); else uses a deterministic fake (`_fake_vision_response(entry)` returns the expected total ±5 % deterministically so the harness self-tests). Computes per-entry MAPE = abs(predicted_total - expected_midpoint) / expected_midpoint * 100 and dish-name accuracy (predicted dish name fuzzy-matches any expected_component.name via difflib.SequenceMatcher ≥ 0.7). Aggregates: mean MAPE across 10 entries, dish accuracy rate. Asserts MAPE < 25 % AND dish accuracy ≥ 70 % — but per CONTEXT.md these are documented targets, not phase blockers; the test prints diagnostics on failure and pytest --tb=short shows the gap. Reports a markdown summary to stdout that the executor pastes into golden-set-result.md."
      exports: []
    - path: "backend/tests/golden_set/manifest.json"
      provides: "JSON array of 10 entries. Schema per entry: {id: 'NN-slug', photo: 'photos/NN-slug.jpg', source: 'placeholder', expected_components: [{name: matches ghana_foods catalogue, kcal_low: int, kcal_high: int}], expected_total_kcal_low: int, expected_total_kcal_high: int, notes: optional}. Coverage of the 10 entries: 01-jollof-with-chicken, 02-banku-tilapia-shito, 03-waakye, 04-fufu-light-soup, 05-kelewele, 06-red-red, 07-kontomire-stew, 08-omotuo-groundnut-soup, 09-tuo-zaafi, 10-kenkey-fried-fish — each one resolvable against the Phase 3 25-dish Ghana table."
      exports: []
    - path: "backend/tests/golden_set/photos/01-jollof-with-chicken.jpg"
      provides: "Placeholder JPEG (≥1 px, ≤10 KB) generated by Pillow with the dish name baked in as a coloured rectangle + text overlay so the file is a valid JPEG that the harness can `open(path, 'rb').read()` without crashing. v1.1 operator replaces these with real Ghanaian-food photography."
      exports: []
    - path: "backend/tests/golden_set/photos/02-banku-tilapia-shito.jpg"
      provides: "Placeholder JPEG (same shape as 01). Banku + tilapia + shito components."
      exports: []
    - path: "backend/tests/golden_set/photos/03-waakye.jpg"
      provides: "Placeholder JPEG. Waakye (rice + beans) component."
      exports: []
    - path: "backend/tests/golden_set/photos/04-fufu-light-soup.jpg"
      provides: "Placeholder JPEG. Fufu + light soup components."
      exports: []
    - path: "backend/tests/golden_set/photos/05-kelewele.jpg"
      provides: "Placeholder JPEG. Kelewele component."
      exports: []
    - path: "backend/tests/golden_set/photos/06-red-red.jpg"
      provides: "Placeholder JPEG. Red-red (bean stew + fried plantain) components."
      exports: []
    - path: "backend/tests/golden_set/photos/07-kontomire-stew.jpg"
      provides: "Placeholder JPEG. Kontomire stew component."
      exports: []
    - path: "backend/tests/golden_set/photos/08-omotuo-groundnut-soup.jpg"
      provides: "Placeholder JPEG. Omotuo + groundnut soup components."
      exports: []
    - path: "backend/tests/golden_set/photos/09-tuo-zaafi.jpg"
      provides: "Placeholder JPEG. Tuo zaafi (TZ) component."
      exports: []
    - path: "backend/tests/golden_set/photos/10-kenkey-fried-fish.jpg"
      provides: "Placeholder JPEG. Kenkey + fried fish + pepper components."
      exports: []
    - path: ".planning/phases/07-launch-hardening/golden-set-result.md"
      provides: "Captured stdout from the in-phase golden-set run (deterministic fake mode). Per-entry table: id / expected_kcal / predicted_kcal / MAPE / dish_accuracy. Aggregate: mean MAPE / aggregate dish accuracy. Records that real-Anthropic re-run is the operator follow-up in LAUNCH.md."
      exports: []
    - path: "LAUNCH.md"
      provides: "Repo-root operator runbook for production launch. Sections: (1) Pre-launch checklist (Atlas backup verified, COST_ALERT_WEBHOOK_URL set, all .env.example vars filled, Clerk Production keys in Render), (2) Anthropic spend cap — link to https://console.anthropic.com/settings/limits + recommended monthly cap $200 for soft launch, (3) WebPageTest Lagos instructions: visit https://www.webpagetest.org/, paste the Render production /dashboard URL, location 'Lagos, Nigeria (gp-chrome) — Chrome — 4G profile', read p75 TTFB from the median run's Document TTFB column, record in 07-SUMMARY.md; if > 2 s, document the Cloudflare-in-front fallback (Cloudflare proxied DNS pointing at the Render *.onrender.com origin) but do NOT implement it during this phase, (4) Cost-alert webhook setup: create a Discord channel + webhook URL OR a Slack incoming webhook + paste into Render env COST_ALERT_WEBHOOK_URL; Phase 4's POST {content: '…'} payload is Discord/Slack-compatible, (5) Real-Anthropic golden-set re-run: `cd backend && RUN_GOLDEN_SET=1 ANTHROPIC_API_KEY=sk-… pytest tests/golden_set/ -s` — expected cost ≈ $0.05 for 10 placeholder photos (real photos in v1.1 raise this to ≈$0.15). NO custom-domain steps (deferred), NO Sentry steps (dropped), NO Cloudflare R2 steps (using GH Actions artifact storage)."
      exports: []
    - path: ".env.example"
      provides: "Updated to document COST_ALERT_WEBHOOK_URL — a single line: `COST_ALERT_WEBHOOK_URL=` with a comment '# Discord/Slack incoming-webhook URL for the $/DAU/day > $0.05 cost alert (Phase 4 OBS-03 — falls back to WARN log if unset).' If FITGH_GIT_SHA is not already listed, add it: `FITGH_GIT_SHA=` with comment '# Render injects this automatically as RENDER_GIT_COMMIT; map via render.yaml or set to the short SHA for /me/export _export_metadata.app_version.'"
      exports: []
    - path: ".planning/REQUIREMENTS.md"
      provides: "Flips in BOTH the v1 section AND the Traceability table: PERF-03 (was Carry-over) → Complete (with note 'ClerkProvider relocated to (authed) route group; Lighthouse re-measured 2026-05-13'); PERF-04 → Complete (with note 'WebPageTest Lagos operator instructions in LAUNCH.md + p75 TTFB recorded in 07-SUMMARY.md'); LEGAL-01 → Complete; LEGAL-02 → Complete; LEGAL-03 → Complete. Updates 'Last updated' line at the bottom."
      exports: []
    - path: ".planning/ROADMAP.md"
      provides: "Phase 7 row in the Progress table: 1/1 Complete (2026-05-13). Phase 7 details block: each Success Criterion flipped to its actual outcome (cite lighthouse-postfix.md, /privacy live, /api/account/export shipped, copy audit clean, golden-set harness + 10 placeholder entries). Traceability table flips PERF-03 / PERF-04 / LEGAL-01 / LEGAL-02 / LEGAL-03 to Complete with the phase tag."
      exports: []
    - path: ".planning/STATE.md"
      provides: "Updates milestone to 'v1.0 complete'. status → 'Phase 7 (Launch Hardening) complete. All 7 phases shipped. PERF-03 (ClerkProvider relocation) + PERF-04 (WebPageTest Lagos) + LEGAL-01/02/03 (privacy + export + copy audit) closed. Backend tests N → ≥296; frontend tests 100 (unchanged or +1). FitGH v1.0 ready for production launch.' stopped_at → '2026-05-13 — v1.0 milestone complete; awaiting operator launch steps in LAUNCH.md.' progress.completed_phases → 7, percent → 100."
      exports: []
    - path: ".planning/phases/07-launch-hardening/07-SUMMARY.md"
      provides: "Phase close artifact. Standard frontmatter (phase / plan / subsystem='launch-hardening' / tags=[lighthouse, route-groups, clerk, privacy-policy, data-export, golden-set, copy-audit, launch] / dependency-graph requires=[phase-6 ClerkProvider mount, phase-2 settings page, phase-4 vision lib + cost-alert webhook, phase-3 ghana_foods + meals schema] / provides=[(public) + (authed) route groups, real /privacy, /me/export + BFF, copy-audit script, golden-set harness + 10 entries, LAUNCH.md operator runbook] / affects=[]). Body: Accomplishments per slice, Task Commits, Measurements (Lighthouse before/after, WebPageTest Lagos p75 TTFB, golden-set MAPE), Decisions Made, Deviations from Plan, Threat-Register Resolutions (T-07-01..03), Issues Encountered, Operator Follow-ups (matches LAUNCH.md), Next Phase Readiness ('v1.0 milestone closed — next is operator launch + post-launch monitoring; v1.1 backlog enumerated'). requirements-completed: [PERF-03, PERF-04, LEGAL-01, LEGAL-02, LEGAL-03]."
      exports: []

  key_links:
    - from: "frontend/src/app/(public)/layout.tsx"
      to: "frontend/src/app/workouts/page.tsx"
      via: "App Router route-group resolution"
      pattern: "no ClerkProvider in the ancestor chain"
    - from: "frontend/src/app/(authed)/layout.tsx"
      to: "frontend/src/app/dashboard/page.tsx"
      via: "App Router route-group resolution; ClerkProvider wraps children"
      pattern: "ClerkProvider"
    - from: "frontend/src/app/settings/download-data-button.tsx"
      to: "frontend/src/app/api/account/export/route.ts"
      via: "fetch('/api/account/export', { credentials: 'same-origin' })"
      pattern: "fetch.*api/account/export"
    - from: "frontend/src/app/api/account/export/route.ts"
      to: "backend/app/routes/me.py GET /me/export"
      via: "forwardToFlask('GET', '/me/export')"
      pattern: "forwardToFlask.*me/export"
    - from: "backend/app/routes/me.py GET /me/export"
      to: "backend/app/db.py collections (users, profiles, weight_logs, meals, user_corrections, vision_usage)"
      via: "PyMongo find_one / find query"
      pattern: "g\\.clerk_user_id"
    - from: "scripts/audit_copy.py"
      to: "frontend/src/app/(public)/layout.tsx footer"
      via: "regex match for the standard disclaimer string"
      pattern: "FitGH is a fitness tracking tool, not medical advice"
    - from: "backend/tests/golden_set/test_golden_vision.py"
      to: "backend/app/lib/vision.py analyze_meal"
      via: "direct import + call when ANTHROPIC_API_KEY is set"
      pattern: "from app.lib.vision import"
---

<objective>
Close out FitGH v1.0 by hardening the gap between "demoable" and "safely launchable": fix the Phase 6 carry-over Lighthouse mobile bottleneck (relocate ClerkProvider out of the root layout via route groups), ship a real privacy policy naming every sub-processor, add a working data-export endpoint, audit health-claim copy, run the vision golden-set harness against 10 placeholder Ghana-dish entries on the env-pinned `claude-sonnet-4-6` model, document Anthropic spend-cap + WebPageTest-Lagos + cost-alert webhook operator steps in LAUNCH.md, sweep any leftover untracked planning artifacts, and finalize REQUIREMENTS / ROADMAP / STATE / 07-SUMMARY traceability so all 7 phases mark Complete.

Purpose: This is the last v1.0 milestone phase. Every Success Criterion in ROADMAP Phase 7 traces back to one of five slices below. Closing this phase puts FitGH at 7/7 phases shipped and 65/65 v1 requirements complete (with Phase 1 carry-overs absorbed elsewhere). The user-perceived deliverable is a launchable product with a real privacy story, a working "download my data" button, and a measured Ghana-edge latency story.

Output: Real /privacy page, /me/export + BFF + UI button, route-group restructure that eliminates Clerk from public-route hot paths, copy-audit script + golden-set harness + 10 placeholder photos, LAUNCH.md runbook, 07-SUMMARY.md + REQUIREMENTS/ROADMAP/STATE flips. Backend tests rise from 292 to ≥296.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/STATE.md
@.planning/phases/07-launch-hardening/07-CONTEXT.md
@.planning/phases/06-workout-library-pwa/06-SUMMARY.md
@frontend/src/app/layout.tsx
@frontend/src/app/privacy/page.tsx
@frontend/src/app/settings/page.tsx
@frontend/src/app/api/account/route.ts
@backend/app/routes/me.py
@backend/app/db.py
@backend/tests/golden_set/README.md
@frontend/middleware.ts

<interfaces>
<!-- Key contracts the executor needs. Extracted from the Phase 1–6 codebase. -->
<!-- Executor uses these directly — no extra exploration required. -->

From `backend/app/middleware/auth.py` (Phase 1, used unchanged):
- `@require_auth` decorator sets `g.clerk_user_id` (string) and `g.clerk_email` (string|None) from the verified Clerk JWT. Routes MUST read user identity ONLY from `g`, never from request body/query.
- `_get_clerk()` returns a memoized `clerk_backend_api.Clerk` SDK client for cases that need the Clerk REST API.

From `backend/app/db.py` (Phase 1–4, all collections module-level):
- Available collections for /me/export: `users`, `profiles`, `weight_logs`, `meals`, `user_corrections`, `vision_usage`. (Also: `ghana_foods`, `system_state` — DO NOT include in export; `ghana_foods` is public catalogue, `system_state` is operator-side.)
- Filter convention: `users` + `profiles` use `clerk_id`; `weight_logs` + `meals` + `user_corrections` + `vision_usage` use `user_id` (which equals the clerk_id).

From `backend/app/routes/me.py` (Phase 1 + 2):
- Existing `@bp.get('/me')` and `@bp.delete('/me')` both use `@require_auth` + `g.clerk_user_id`. The new `GET /me/export` follows the same shape — add it in the same Blueprint `bp`.

From `frontend/src/lib/api-server.ts` (Phase 2):
- `forwardToFlask(method: 'GET' | 'POST' | 'DELETE' | 'PATCH' | 'PUT', path: string, body?: BodyInit): Promise<Response>` — the BFF helper that attaches the Clerk session JWT as a Bearer token and forwards to `${FLASK_INTERNAL_URL}${path}`. Used by every existing /api/* BFF route.

From `frontend/src/app/api/account/route.ts` (Phase 2):
- `export const dynamic = "force-dynamic"` + `export async function DELETE() { return forwardToFlask("DELETE", "/me"); }` — the shape /api/account/export/route.ts mirrors for GET, with the added Content-Disposition header mutation.

From `frontend/middleware.ts` (Phase 1 + 6):
- `clerkMiddleware` with a `isProtectedRoute` matcher. After the route-group split: `/(authed)/*` resolves to paths like `/dashboard` etc., so the existing `isProtectedRoute` list (which already names `/dashboard`, `/onboarding`, `/profile`, `/settings`, `/history`) needs NO modification — route groups don't change URL paths. The `/workouts` + `/workouts/[id]` + `/privacy` + `/sign-in` + `/sign-up` + `/` paths stay public.

From `backend/app/lib/vision.py` (Phase 4):
- `analyze_meal(image_bytes: bytes, user_corrections_context: list | None = None) -> VisionResponse` — the pure library function the golden-set harness calls directly (bypasses Flask routing). The env-pinned model comes from `LLM_VISION_MODEL=claude-sonnet-4-6`. When `ANTHROPIC_API_KEY` is unset, the harness uses a deterministic fake (do NOT mock `analyze_meal` itself — provide a `_fake_vision_response(entry: dict) -> VisionResponse` helper inside the test module that the harness selects when no API key is present).

From `backend/tests/conftest.py` (Phase 1+ established pattern):
- `test_client` fixture: `Flask` test client with `MONGODB_URI` pointed at a per-test mongomock or test database.
- `mock_clerk_jwt(user_id: str, email: str | None = None)` fixture/helper: returns a `dict` with the Authorization header value that passes `@require_auth` checks. Used by every existing `/me`-style test (see `test_me.py`, `test_delete_account.py`).

From `frontend/src/components/ui/sonner.tsx` + `sonner` package (Phase 5):
- `import { toast } from 'sonner'` → `toast.success('...')` + `toast.error('...')`. Used by DownloadDataButton for user feedback.
</interfaces>

<route_group_migration_notes>
<!-- Critical executor guidance for Slice A. -->

When moving files into `(public)` / `(authed)` route groups, the URL paths DO NOT change — Next.js App Router strips the parenthesized segment from the URL.

Current `frontend/src/app/` layout:
```
src/app/
  layout.tsx            ← root, currently has ClerkProvider
  page.tsx              ← /
  dashboard/page.tsx    ← /dashboard (authed)
  onboarding/...        ← /onboarding (authed)
  profile/...           ← /profile (authed)
  settings/...          ← /settings (authed)
  history/...           ← /history (authed)
  privacy/page.tsx      ← /privacy (public)
  workouts/page.tsx     ← /workouts (public)
  workouts/[id]/...     ← /workouts/[id] (public)
  sign-in/page.tsx      ← /sign-in (public)
  sign-up/page.tsx      ← /sign-up (public)
  api/...               ← API routes (untouched)
```

Target layout:
```
src/app/
  layout.tsx            ← bare HTML shell + footer; NO ClerkProvider
  (public)/
    layout.tsx          ← passthrough; no ClerkProvider
    page.tsx            ← /
    privacy/page.tsx    ← /privacy
    workouts/page.tsx   ← /workouts
    workouts/[id]/...   ← /workouts/[id]
    sign-in/page.tsx    ← /sign-in
    sign-up/page.tsx    ← /sign-up
  (authed)/
    layout.tsx          ← ClerkProvider + RegisterSW + OfflineIndicator + InstallPrompt
    dashboard/...
    onboarding/...
    profile/...
    settings/...
    history/...
  api/...               ← untouched
```

The move is a literal `git mv` of each top-level page directory; verify imports inside those pages don't use relative paths that traverse via the now-different ancestor (e.g. `../../components/...` becomes `../../../components/...`). Prefer adjusting to the `@/components/...` alias which Phase 1 already configured.

After move: `pnpm build` MUST succeed AND emit the same number of routes (108 pages). The First Load JS for `/workouts` MUST drop (Clerk SDK no longer in the chunk).
</route_group_migration_notes>
</context>

<tasks>

<!-- ============================================================ -->
<!-- SLICE A — Lighthouse fix (PERF-03 carry-over)                -->
<!-- ============================================================ -->

<task type="auto">
  <name>Task P7-A.1: Split App Router into (public) and (authed) route groups; relocate ClerkProvider</name>
  <files>frontend/src/app/layout.tsx, frontend/src/app/(public)/layout.tsx, frontend/src/app/(authed)/layout.tsx, frontend/src/app/(public)/page.tsx, frontend/src/app/(public)/privacy/page.tsx, frontend/src/app/(public)/workouts/page.tsx, frontend/src/app/(public)/workouts/[id]/page.tsx, frontend/src/app/(public)/workouts/[id]/not-found.tsx, frontend/src/app/(public)/sign-in/page.tsx, frontend/src/app/(public)/sign-up/page.tsx, frontend/src/app/(authed)/dashboard/page.tsx, frontend/src/app/(authed)/onboarding/**, frontend/src/app/(authed)/profile/**, frontend/src/app/(authed)/settings/**, frontend/src/app/(authed)/history/**</files>
  <action>Per the route_group_migration_notes block: `git mv` each top-level page directory into either `(public)/` or `(authed)/`. Root `layout.tsx` becomes a bare HTML+body shell that hosts ONLY the Inter font variable, ServicePausedBanner, the global footer (Free Exercise DB attribution + /privacy link + the standard disclaimer string 'FitGH is a fitness tracking tool, not medical advice. Consult a qualified clinician for health decisions.' — this is the LEGAL-03 disclaimer footer placement), Toaster, and `{children}`. NO ClerkProvider; NO PWA primitives. Create `frontend/src/app/(public)/layout.tsx` as a passthrough returning `{children}` (no ClerkProvider). Create `frontend/src/app/(authed)/layout.tsx` that wraps `{children}` in `<ClerkProvider>` and mounts RegisterSW + OfflineIndicator + InstallPrompt inside the ClerkProvider tree (those PWA primitives only matter for signed-in users posting meals). Walk every moved page and fix relative imports — prefer the `@/components/...` and `@/lib/...` aliases (already configured in Phase 1's tsconfig.json) over `../../...` to make future moves cheap. middleware.ts requires NO changes — route groups do not affect URL paths, so `isProtectedRoute` still matches /dashboard, /onboarding, /profile, /settings, /history exactly as before. Verify `pnpm build` succeeds AND emits 108 routes AND the /workouts First Load JS column drops by ≥ 100 kB versus the pre-move build (Clerk SDK ~312 kB transferred, ~100 kB gzipped is the expected drop).</action>
  <verify>
    <automated>cd frontend && pnpm build 2>&1 | tee /tmp/p7a1-build.log && grep -E '(public)|(authed)' /tmp/p7a1-build.log || echo "ROUTE GROUPS INVISIBLE IN BUILD OUTPUT (expected — route group syntax strips from URL, but presence is confirmed by directory listing)" && ls frontend/src/app/\(public\) frontend/src/app/\(authed\) && grep -L "ClerkProvider" frontend/src/app/layout.tsx && grep -l "ClerkProvider" frontend/src/app/\(authed\)/layout.tsx && grep -c "○ /workouts" /tmp/p7a1-build.log</automated>
  </verify>
  <done>frontend/src/app/layout.tsx contains no `ClerkProvider` import; frontend/src/app/(authed)/layout.tsx imports + wraps with `ClerkProvider`; frontend/src/app/(public)/layout.tsx is a passthrough; `pnpm build` succeeds; route count is 108 (or 109 if /manifest.webmanifest is recounted); /workouts First Load JS drops measurably versus the pre-move build (record the before/after in lighthouse-postfix.md in P7-A.2).</done>
</task>

<task type="auto">
  <name>Task P7-A.2: Re-run Lighthouse mobile on /workouts post-deploy; document score and gap-analysis</name>
  <files>.planning/phases/07-launch-hardening/lighthouse-postfix.md</files>
  <action>After P7-A.1's Render redeploy completes (5–10 min after `git push`), run `npx lighthouse https://fitgh-web.onrender.com/workouts --form-factor=mobile --throttling-method=devtools --output=json --output-path=./lighthouse-workouts-postfix.json --chrome-flags="--headless=new --no-sandbox --disable-gpu" --only-categories=performance,accessibility,best-practices --quiet` twice (cold + warm). If the Render deploy is still in flight or the executor cannot reach the production URL, run Lighthouse against `http://localhost:3000/workouts` after `pnpm build && pnpm start` and clearly note in the document that the production URL re-run is an operator follow-up. Create `.planning/phases/07-launch-hardening/lighthouse-postfix.md` capturing: (a) cold + warm Performance / Accessibility / Best Practices scores; (b) the four core metrics (FCP / LCP / TBT / TTI) for each run; (c) the third-party blocking time number (should now be ≈0 ms for accounts.dev — verify by checking the lighthouse JSON `audits.third-party-summary.details.items` for any clerk-related domain); (d) gap analysis: if Performance ≥ 90, declare PERF-03 Complete; if 70–89, name the residual bottleneck (likely Render free-tier 600 ms TTFB OR React 19 hydration cost) and propose a v1.1 mitigation (upgrade Render to Starter for $7/mo OR put Cloudflare in front per PERF-04 deferred branch) WITHOUT blocking phase close per CONTEXT.md ('don't block phase close'). Record the pre/post First Load JS for /workouts from the P7-A.1 build log (expected drop ~100 kB gzipped).</action>
  <verify>
    <automated>test -f .planning/phases/07-launch-hardening/lighthouse-postfix.md && grep -E "Performance" .planning/phases/07-launch-hardening/lighthouse-postfix.md | grep -v '^#' | wc -l | awk '$1 >= 2 {print "OK: ≥2 Performance lines"} $1 < 2 {print "FAIL: need cold+warm Performance scores"; exit 1}'</automated>
  </verify>
  <done>lighthouse-postfix.md exists with cold+warm scores, all four core metrics, third-party blocking-time check, and a PERF-03 disposition statement (Complete OR gap-analysis-with-v1.1-mitigation).</done>
</task>

<!-- ============================================================ -->
<!-- SLICE B — Real privacy policy (LEGAL-01)                     -->
<!-- ============================================================ -->

<task type="auto">
  <name>Task P7-B.1: Replace /privacy stub with real privacy policy; verify cross-page links</name>
  <files>frontend/src/app/(public)/privacy/page.tsx, frontend/src/app/(public)/layout.tsx, frontend/src/app/(authed)/settings/page.tsx</files>
  <action>Per CONTEXT.md §LEGAL-01 template, rewrite `frontend/src/app/(public)/privacy/page.tsx` (the file moved into (public) by P7-A.1; if for any reason it stayed at `frontend/src/app/privacy/page.tsx` because the executor preserved the original path, this task targets THAT file — either way, ONE privacy page lives at the URL /privacy). Remove the 'v1 (stub)' header. Use Tailwind `prose prose-sm md:prose-base` wrapper. Sections numbered 1–6: (1) What we collect — Clerk identity (email + OAuth tokens), profile (name + sex + height + weight + age + timezone + locale + activity level + goal), meals + components + portions, weight logs, meal photos (transient — see §2), user_corrections; (2) What we don't keep — meal images: bytes sent to Anthropic Claude Sonnet 4.6 then discarded server-side (no GridFS, no R2, no logs); (3) Sub-processors with explicit data flow: **Anthropic (Claude Sonnet 4.6)** receives base64 meal images for kcal estimation, **Clerk** holds authentication identity (email + OAuth tokens), **MongoDB Atlas** holds profile + meals + weight logs, **Render** hosts the application + ephemeral logs, **GitHub Actions** runs the nightly mongodump backup (encrypted artifact, 90-day retention per DATA-01) — DO NOT mention Cloudflare R2 (not used in v1.0); (4) User rights — export via the 'Download my data' button in /settings (link to /settings) which hits /api/account/export, delete via /settings 'Delete account' (existing Phase 2 flow); (5) Contact — francisyiryel@gmail.com; (6) Last updated — 2026-05-13. The page header MUST carry an amber-bordered disclaimer card with text 'This privacy policy is provided in good faith but has not been reviewed by counsel. Review with a lawyer before commercial launch.' Add anchor links at the top of the page jumping to §1..§6. Verify (eyeball + grep) that the global footer in `(public)/layout.tsx` (or wherever it ended up after P7-A.1; the root layout owns the footer per A.1) still links to /privacy. Verify the existing onboarding screen 3 (Phase 2 — likely `frontend/src/app/(authed)/onboarding/screen-3.tsx` or similar) still links to /privacy after the route-group move. Add a 'Privacy policy' link in `(authed)/settings/page.tsx` in a new 'Data' section above the existing Danger zone — this is the third LEGAL-01 link target.</action>
  <verify>
    <automated>grep -E "Last updated.*2026-05-13" frontend/src/app/\(public\)/privacy/page.tsx && grep "not been reviewed by counsel" frontend/src/app/\(public\)/privacy/page.tsx && grep -c "Anthropic\|Clerk\|MongoDB Atlas\|Render\|GitHub Actions" frontend/src/app/\(public\)/privacy/page.tsx | awk '$1 >= 5 {print "OK"} $1 < 5 {print "FAIL: need all 5 sub-processors"; exit 1}' && grep -L "Cloudflare R2" frontend/src/app/\(public\)/privacy/page.tsx && grep "/privacy" frontend/src/app/layout.tsx && grep "/privacy" frontend/src/app/\(authed\)/settings/page.tsx</automated>
  </verify>
  <done>/privacy renders the real policy; disclaimer present; all 5 sub-processors named; no Cloudflare R2 mention; /privacy linked from root layout footer + /settings + onboarding screen 3 (verified live by `pnpm build && pnpm start` smoke test before phase close).</done>
</task>

<!-- ============================================================ -->
<!-- SLICE C — Data export (LEGAL-02)                             -->
<!-- ============================================================ -->

<task type="auto" tdd="true">
  <name>Task P7-C.1: Flask GET /me/export — multi-collection JSON archive with _export_metadata</name>
  <files>backend/app/routes/me.py, backend/tests/test_me_export.py</files>
  <behavior>
    - test_export_happy_path: seeded with 1 user + 1 profile + 2 weight_logs + 2 meals + 1 user_correction + 1 vision_usage doc; GET /me/export with valid bearer JWT → 200; response JSON contains keys [_export_metadata, user, profile, weight_logs, meals, user_corrections, vision_usage]; all arrays carry the seeded counts; all ObjectIds serialize to strings; all datetimes serialize to ISO 8601 strings; _export_metadata = {export_date: iso, app_version: 'unknown' OR a sha string, schema_version: 1}.
    - test_export_empty_account: seeded with only the user doc; GET /me/export → 200; weight_logs / meals / user_corrections / vision_usage are all `[]` (empty arrays, not null/missing); profile is `null` or missing-key (executor decides — document the choice in the test).
    - test_export_unauth: GET /me/export with NO Authorization header → 401.
    - test_export_cross_user_isolation: seed user A (clerk_id='user_A') + user B (clerk_id='user_B') each with 1 weight_log + 1 meal; GET /me/export with bearer for user A; assert response contains user_A data ONLY (no user_B clerk_id / user_id values anywhere in the response JSON). Mitigates T-07-01.
  </behavior>
  <action>Write tests FIRST per the tdd="true" gate. Use the existing `backend/tests/conftest.py` fixtures (`test_client`, `mock_clerk_jwt`) — match the pattern in `backend/tests/test_me.py` and `backend/tests/test_delete_account.py`. Then in `backend/app/routes/me.py`, add `@bp.get('/me/export')` decorated with `@require_auth`. Read `clerk_id = g.clerk_user_id` (NEVER from request). Query: users.find_one({'clerk_id': clerk_id}), profiles.find_one({'clerk_id': clerk_id}), weight_logs.find({'user_id': clerk_id}).sort('logged_at', -1) → list, meals.find({'user_id': clerk_id}).sort('logged_at', -1) → list, user_corrections.find({'user_id': clerk_id}).sort('corrected_at', -1) → list, vision_usage.find({'user_id': clerk_id}) → list. Write a small `_serialize(doc)` helper that walks the dict and converts `bson.ObjectId` → `str(_)` and `datetime` → `_.isoformat()`. Build the response: `{'_export_metadata': {'export_date': datetime.now(UTC).isoformat(), 'app_version': os.environ.get('FITGH_GIT_SHA', 'unknown'), 'schema_version': 1}, 'user': _serialize(user), 'profile': _serialize(profile), 'weight_logs': [_serialize(d) for d in weight_logs], 'meals': [_serialize(d) for d in meals], 'user_corrections': [_serialize(d) for d in user_corrections], 'vision_usage': [_serialize(d) for d in vision_usage]}`. Return `jsonify(payload)` — Flask sets Content-Type: application/json automatically. NO pagination (CONTEXT.md says ≤10 MB even for power users is fine).</action>
  <verify>
    <automated>cd backend && pytest tests/test_me_export.py -x -v 2>&1 | tail -30</automated>
  </verify>
  <done>All 4 tests pass; total backend pytest count rises from 292 → ≥ 296; the /me/export route returns the documented shape; no user-id leakage path through request body or query.</done>
</task>

<task type="auto">
  <name>Task P7-C.2: BFF /api/account/export route — forward + set Content-Disposition attachment header</name>
  <files>frontend/src/app/api/account/export/route.ts</files>
  <action>Create `frontend/src/app/api/account/export/route.ts`. `export const dynamic = 'force-dynamic'`. `export async function GET()`: call `const upstream = await forwardToFlask('GET', '/me/export')`. If `!upstream.ok` return `upstream` unchanged. Otherwise, read `clerk_id` via Clerk's server helper `const { userId } = await auth()` (already in scope per Phase 2 patterns; if it returns null, return `upstream` unchanged so the auth error surfaces). Compute `const date = new Date().toISOString().slice(0, 10)` (YYYY-MM-DD). Read upstream body as a stream or buffer and return a new `Response(upstream.body, { status: 200, headers: { 'Content-Type': 'application/json', 'Content-Disposition': `attachment; filename="fitgh-export-${userId}-${date}.json"` } })`. Mirror the shape of `frontend/src/app/api/account/route.ts` (DELETE handler) for everything else.</action>
  <verify>
    <automated>test -f frontend/src/app/api/account/export/route.ts && grep -E "Content-Disposition" frontend/src/app/api/account/export/route.ts && grep -E "forwardToFlask.*GET.*me/export" frontend/src/app/api/account/export/route.ts && cd frontend && pnpm build 2>&1 | grep -E "api/account/export" | head -1</automated>
  </verify>
  <done>The BFF route exists, builds, and emits `attachment; filename=` Content-Disposition; the file resolves at the URL /api/account/export per `pnpm build`'s route table.</done>
</task>

<task type="auto">
  <name>Task P7-C.3: Settings 'Download my data' button — client component + UI placement</name>
  <files>frontend/src/app/(authed)/settings/page.tsx, frontend/src/app/(authed)/settings/download-data-button.tsx</files>
  <action>Create `frontend/src/app/(authed)/settings/download-data-button.tsx` as `'use client'`. Default-export `<DownloadDataButton/>`. Component holds an `isLoading` state (useState false). On click: setIsLoading(true) → fetch('/api/account/export', { method: 'GET', credentials: 'same-origin' }) → if !response.ok throw → const blob = await response.blob() → derive filename: read response.headers.get('Content-Disposition') and parse `filename="…"`, fallback to `fitgh-export-${new Date().toISOString().slice(0,10)}.json` → const url = URL.createObjectURL(blob) → create temporary `<a>` with `download=filename` + `href=url` + click() → URL.revokeObjectURL after 1 s → toast.success('Your data has started downloading.'). Catch: toast.error('Could not export your data. Please try again later.'). Finally: setIsLoading(false). Render the button as `<Button variant='outline' onClick={handleClick} disabled={isLoading} aria-busy={isLoading}>{isLoading ? 'Preparing…' : 'Download my data (JSON)'}</Button>`. Then modify `frontend/src/app/(authed)/settings/page.tsx` — insert a new `<section>` between the page header and the 'Danger zone' section with `<h2>Data</h2>` containing (a) `<Link href='/privacy'>Privacy policy</Link>` and (b) `<DownloadDataButton/>`. Keep the existing Danger zone + DeleteAccountButton untouched.</action>
  <verify>
    <automated>test -f frontend/src/app/\(authed\)/settings/download-data-button.tsx && grep -E "fetch.*api/account/export" frontend/src/app/\(authed\)/settings/download-data-button.tsx && grep -E "DownloadDataButton" frontend/src/app/\(authed\)/settings/page.tsx && grep -E "/privacy" frontend/src/app/\(authed\)/settings/page.tsx && cd frontend && pnpm build 2>&1 | grep -E "settings" | head -1</automated>
  </verify>
  <done>Settings page renders Privacy policy link + Download my data button between the header and Danger zone; click triggers a browser download via Blob + anchor.click; toast feedback on success/failure; build green.</done>
</task>

<!-- ============================================================ -->
<!-- SLICE D — Copy audit + golden set (LEGAL-03 + PERF-04 traceability) -->
<!-- ============================================================ -->

<task type="auto">
  <name>Task P7-D.1: scripts/audit_copy.py — forbidden-phrase + required-disclaimer audit; run + fix findings</name>
  <files>scripts/audit_copy.py, scripts/README-audit-copy.md, frontend/src/app/layout.tsx (if disclaimer absent)</files>
  <action>Create `scripts/audit_copy.py` per the must_haves artifact spec. Python 3.12 + argparse (no external deps — pure stdlib glob + re). FORBIDDEN regex list (case-insensitive): `r"will help you lose weight"`, `r"achieves your goal"`, `r"guaranteed results"`, `r"\bmedical advice\b"` (with allowlist: file path ENDS WITH `(public)/layout.tsx` OR `(authed)/layout.tsx` AND line contains 'not medical advice'), `r"\btreats\b\s+(diabetes|obesity|hypertension|cancer|disease)"`. Scan globs: `frontend/src/**/*.ts`, `frontend/src/**/*.tsx`, `frontend/src/**/*.md`, `backend/app/**/*.py`. Vendor allowlist (skip): paths containing `node_modules/`, `.next/`, `public/exercises/`, `LICENSES.md`. REQUIRED disclaimer regex: `r"FitGH is a fitness tracking tool, not medical advice\. Consult a qualified clinician for health decisions\."` — must appear in BOTH (a) `frontend/src/app/layout.tsx` (the root footer location per P7-A.1) OR `frontend/src/app/(public)/layout.tsx` AND (b) at least one of `frontend/src/app/(authed)/onboarding/**/*.tsx`. Print findings as `path:line: <FORBIDDEN|MISSING_REQUIRED> <description>`. Exit 0 unless `--strict` and findings exist (then exit 1). Create `scripts/README-audit-copy.md` documenting usage + the forbidden + required strings. Run the script (`python scripts/audit_copy.py`) and for each finding: fix the FORBIDDEN match in source by rewriting to compliant copy (e.g. 'will help you lose weight' → 'is designed to support your weight-tracking goals'); if a REQUIRED disclaimer is missing from the root layout footer, ADD it inline as a small `<p className='text-[10px] text-muted-foreground/70 w-full text-center pt-1'>` element inside the existing footer — Phase 6 already established the footer string layout. Re-run the script after edits to confirm clean.</action>
  <verify>
    <automated>python scripts/audit_copy.py --strict && test -f scripts/README-audit-copy.md && grep "FitGH is a fitness tracking tool" frontend/src/app/layout.tsx</automated>
  </verify>
  <done>scripts/audit_copy.py exits 0 in `--strict` mode; README-audit-copy.md exists; the standard disclaimer is in the root layout footer; any findings produced by the first script run are either fixed in-source or documented in 07-SUMMARY.md with a one-line accept reason.</done>
</task>

<task type="auto">
  <name>Task P7-D.2: Golden-set harness — 10 Ghana-dish manifest + placeholder photos + skipif-gated pytest</name>
  <files>backend/tests/golden_set/test_golden_vision.py, backend/tests/golden_set/manifest.json, backend/tests/golden_set/photos/01-jollof-with-chicken.jpg, backend/tests/golden_set/photos/02-banku-tilapia-shito.jpg, backend/tests/golden_set/photos/03-waakye.jpg, backend/tests/golden_set/photos/04-fufu-light-soup.jpg, backend/tests/golden_set/photos/05-kelewele.jpg, backend/tests/golden_set/photos/06-red-red.jpg, backend/tests/golden_set/photos/07-kontomire-stew.jpg, backend/tests/golden_set/photos/08-omotuo-groundnut-soup.jpg, backend/tests/golden_set/photos/09-tuo-zaafi.jpg, backend/tests/golden_set/photos/10-kenkey-fried-fish.jpg</files>
  <action>Create `backend/tests/golden_set/manifest.json` with the 10-entry array per the must_haves artifact spec — each entry has `id` ('NN-slug'), `photo` ('photos/NN-slug.jpg'), `source: 'placeholder'`, `expected_components: [{name, kcal_low, kcal_high}]` (names MUST resolve against the Phase 3 ghana_foods catalogue — refer to `backend/scripts/seed_ghana_foods.py` or the existing data to pick valid names), `expected_total_kcal_low`, `expected_total_kcal_high`, and an optional `notes` field. Use the Phase 3 Ghana table portion defaults for the kcal ranges (e.g. jollof + chicken ≈ 650–900 kcal range). Generate the 10 placeholder JPEGs via Pillow: for each entry write a tiny script-style inline generation (e.g. `Image.new('RGB', (64, 64), color=(R, G, B))` then `.save(path, 'JPEG', quality=70)`) so each photo is a valid JPEG. Put the generation logic inside a `conftest.py` `session`-scoped fixture OR a one-shot helper invoked in this task if the binary commit is preferred — pick whichever is simpler; the deliverable is that 10 valid JPEGs exist on disk and the harness can `open(path, 'rb').read()` them. Create `backend/tests/golden_set/test_golden_vision.py` with the top-level `@pytest.mark.skipif(os.environ.get('RUN_GOLDEN_SET') != '1', reason='Set RUN_GOLDEN_SET=1 to run')` decorator on a single test function `test_golden_set()`. Inside: load manifest.json; iterate entries; for each, read photo bytes, call `_call_vision(entry, photo_bytes)` — when `os.environ.get('ANTHROPIC_API_KEY')` is set the helper calls `app.lib.vision.analyze_meal(photo_bytes)`, else it returns `_fake_vision_response(entry)` (a deterministic fake that returns `VisionResponse` with total_kcal = midpoint(expected_total_kcal_low, expected_total_kcal_high) and a component list mirroring expected_components). Compute per-entry MAPE = abs(predicted_total - midpoint) / midpoint * 100 and dish accuracy via difflib.SequenceMatcher ratio ≥ 0.7 against any expected_component.name. Aggregate. Print a markdown table to stdout. Assert mean MAPE < 25 % AND aggregate dish accuracy ≥ 0.7 — but wrap the asserts in soft logging-then-assert so a failure clearly identifies which entries missed. Update `backend/tests/golden_set/README.md` to reflect that the harness is live (Phase 7) — remove the 'this directory is intentionally empty' line.</action>
  <verify>
    <automated>cd backend && ls tests/golden_set/photos/*.jpg 2>&1 | wc -l | awk '$1 >= 10 {print "OK: 10 photos"} $1 < 10 {print "FAIL: need 10 photos"; exit 1}' && test -f tests/golden_set/manifest.json && test -f tests/golden_set/test_golden_vision.py && pytest tests/golden_set/test_golden_vision.py -v 2>&1 | tail -5 && RUN_GOLDEN_SET=1 pytest tests/golden_set/test_golden_vision.py -v 2>&1 | tail -10</automated>
  </verify>
  <done>10 placeholder JPEGs on disk under photos/; manifest.json validates against the documented schema; pytest collects test_golden_vision.py as SKIPPED by default; with RUN_GOLDEN_SET=1 (and no ANTHROPIC_API_KEY) the deterministic fake runs and the assertions pass; backend pytest count is unaffected by the default-skip behaviour (≥ 296 from P7-C.1 still holds).</done>
</task>

<task type="auto">
  <name>Task P7-D.3: Run golden set in deterministic-fake mode and record result</name>
  <files>.planning/phases/07-launch-hardening/golden-set-result.md</files>
  <action>Run `cd backend && RUN_GOLDEN_SET=1 pytest tests/golden_set/test_golden_vision.py -s -v 2>&1 | tee /tmp/golden-set.log`. Capture the stdout markdown table. Create `.planning/phases/07-launch-hardening/golden-set-result.md` with: (a) the per-entry table (id / expected_kcal_midpoint / predicted_kcal / MAPE / dish_accuracy), (b) the aggregate (mean MAPE / mean dish accuracy), (c) a 'Run mode' line stating 'deterministic fake (ANTHROPIC_API_KEY unset)' so the document is unambiguous, (d) a 'Next step' line stating 'Real-Anthropic re-run is an operator follow-up post-deploy — see LAUNCH.md §5.' Per CONTEXT.md the < 25 % MAPE target is documented but not a phase blocker; with the deterministic fake it passes by construction (the fake returns the midpoint exactly), which validates the harness shape rather than vision-model accuracy.</action>
  <verify>
    <automated>test -f .planning/phases/07-launch-hardening/golden-set-result.md && grep -E "MAPE" .planning/phases/07-launch-hardening/golden-set-result.md && grep -E "deterministic fake" .planning/phases/07-launch-hardening/golden-set-result.md</automated>
  </verify>
  <done>golden-set-result.md captures the in-phase fake-mode run; the MAPE table is recorded; the operator-follow-up note for real-Anthropic re-run is captured.</done>
</task>

<!-- ============================================================ -->
<!-- SLICE E — Operator instructions + traceability               -->
<!-- ============================================================ -->

<task type="auto">
  <name>Task P7-E.1: LAUNCH.md + .env.example — operator runbook for spend cap, WebPageTest, cost-alert webhook</name>
  <files>LAUNCH.md, .env.example</files>
  <action>Create `LAUNCH.md` at the repo root with the 5-section runbook per the must_haves artifact spec: (1) Pre-launch checklist — confirm Atlas backup verified (DATA-01 — GH Actions nightly mongodump), COST_ALERT_WEBHOOK_URL set, all .env.example vars filled, Clerk Production keys in Render env; (2) Anthropic spend cap — link https://console.anthropic.com/settings/limits, recommended monthly cap $200 for soft launch (per the cost table in CLAUDE.md: ~$36/mo at 100 DAU × 3 meals/day, so $200 is a 5× headroom); (3) WebPageTest Lagos instructions — URL https://www.webpagetest.org/, paste the Render production /dashboard URL, location 'Lagos, Nigeria — Chrome — 4G profile', read p75 TTFB from the median run's `Document TTFB` column, record in 07-SUMMARY.md; if > 2 s, document the Cloudflare-in-front fallback (proxied DNS pointing at fitgh-web.onrender.com) but DO NOT implement during this phase per the 2026-05-12 rewrite; (4) Cost-alert webhook setup — create a Discord channel + webhook OR Slack incoming webhook + set in Render env COST_ALERT_WEBHOOK_URL (Phase 4's payload shape is Discord/Slack-compatible); (5) Real-Anthropic golden-set re-run — `cd backend && RUN_GOLDEN_SET=1 ANTHROPIC_API_KEY=sk-… pytest tests/golden_set/ -s` — expected cost ≈ $0.05 for 10 placeholder photos (v1.1 real photos raise to ≈ $0.15). Append explicit NON-steps at the bottom: NO custom-domain setup (deferred), NO Sentry steps (dropped), NO Cloudflare R2 setup (using GH Actions artifact storage). Then update `.env.example` per the must_haves artifact spec — add `COST_ALERT_WEBHOOK_URL=` with the OBS-03 reference comment, and add `FITGH_GIT_SHA=` if absent with the /me/export _export_metadata reference comment.</action>
  <verify>
    <automated>test -f LAUNCH.md && grep -E "WebPageTest" LAUNCH.md && grep -E "COST_ALERT_WEBHOOK_URL" LAUNCH.md && grep -E "Anthropic" LAUNCH.md && grep -E "RUN_GOLDEN_SET" LAUNCH.md && grep -E "COST_ALERT_WEBHOOK_URL" .env.example</automated>
  </verify>
  <done>LAUNCH.md exists with all 5 sections + the NON-steps appendix; .env.example documents COST_ALERT_WEBHOOK_URL + FITGH_GIT_SHA.</done>
</task>

<task type="auto">
  <name>Task P7-E.2: Working-tree sweep — stage leftover phase artifacts</name>
  <files>(any leftover untracked .planning/phases/*/*.md files surfaced by git status)</files>
  <action>Run `git status --short` from the repo root. Inventory every untracked file (excluding the operator-owned `GEMINI.md`). For each untracked file under `.planning/phases/*/` — including the current Phase 7 artifacts (07-CONTEXT.md, 07-PLAN.md, 07-SUMMARY.md when present, plus golden-set-result.md, lighthouse-postfix.md) AND any leftover CONTEXT.md / PLAN.md / SUMMARY.md from Phases 2–6 that the Phase 6 close-commit didn't catch — `git add` it so it joins the phase-close commit. DO NOT add files outside `.planning/`, `frontend/`, `backend/`, `scripts/`, `LAUNCH.md`, or `.env.example`. DO NOT add `GEMINI.md` (operator-owned per current repo state). After staging, run `git status --short` again and confirm the only remaining untracked file is `GEMINI.md` (if it still exists). Record any files NOT added in 07-SUMMARY.md's 'Working-tree sweep' subsection with a one-line reason (e.g. 'GEMINI.md — operator-owned, intentionally untracked').</action>
  <verify>
    <automated>git status --short 2>&1 | grep '^??' | grep -v '^?? GEMINI.md$' | wc -l | awk '$1 == 0 {print "OK: tree clean"} $1 > 0 {print "FAIL: leftover untracked files (excluding GEMINI.md)"; exit 1}'</automated>
  </verify>
  <done>git status --short shows zero untracked files except GEMINI.md; all Phase 7 artifacts + any leftover prior-phase artifacts are staged for the phase-close commit.</done>
</task>

<task type="auto">
  <name>Task P7-E.3: Phase close — 07-SUMMARY.md + REQUIREMENTS / ROADMAP / STATE traceability</name>
  <files>.planning/phases/07-launch-hardening/07-SUMMARY.md, .planning/REQUIREMENTS.md, .planning/ROADMAP.md, .planning/STATE.md</files>
  <action>Write `.planning/phases/07-launch-hardening/07-SUMMARY.md` matching the Phase 6 SUMMARY shape (frontmatter + body per the must_haves artifact spec). Capture per-slice Accomplishments, Task Commits (gather the actual commit shas from `git log --oneline` for tasks A.1..E.3), Measurements (Lighthouse before/after from lighthouse-postfix.md; WebPageTest Lagos p75 TTFB if the executor ran it, else mark as 'Operator follow-up — see LAUNCH.md §3'; golden-set MAPE from golden-set-result.md; backend pytest count 292 → ≥ 296; frontend vitest unchanged 100 OR +1), Decisions Made (route-group migration, GitHub Actions artifact storage instead of R2 in privacy policy text, placeholder JPEGs OK for v1.0 per CONTEXT.md), Deviations from Plan (whatever surfaced), Threat-Register Resolutions (T-07-01..03 — see threat_model block below), Issues Encountered, Operator Follow-ups (mirrors LAUNCH.md), Next Phase Readiness ('v1.0 milestone closed; all 7 phases shipped; next is operator launch + post-launch monitoring; v1.1 backlog: real-Anthropic golden-set re-run, real Ghana-food photography for the golden set, Rive avatar from DASH-01 deferral, animated WebM + curated YouTube embed from WORK-05/06 deferral, Cloudflare-in-front IF WebPageTest Lagos p75 > 2 s, custom domain'). Frontmatter `requirements-completed: [PERF-03, PERF-04, LEGAL-01, LEGAL-02, LEGAL-03]`. Then flip `.planning/REQUIREMENTS.md`: in BOTH the v1 section AND the Traceability table, PERF-03 → Complete (was Carry-over) with note 'ClerkProvider relocated to (authed) route group via Phase 7; Lighthouse mobile re-measured — see lighthouse-postfix.md'; PERF-04 → Complete with note 'WebPageTest Lagos operator instructions in LAUNCH.md §3; p75 TTFB recorded in 07-SUMMARY.md Measurements section'; LEGAL-01 / LEGAL-02 / LEGAL-03 → Complete with Phase 7 attribution. Update the 'Last updated' line at the bottom of REQUIREMENTS.md. Flip `.planning/ROADMAP.md`: Phase 7 row in the Progress table → 1/1 Complete (2026-05-13); Phase 7 details block → each SC flipped to actual outcome; Traceability table flips for PERF-03/04 + LEGAL-01/02/03 to Complete. Update `.planning/STATE.md`: milestone 'v1.0 complete'; status reflects all 7 phases shipped; progress.completed_phases → 7; progress.percent → 100.</action>
  <verify>
    <automated>test -f .planning/phases/07-launch-hardening/07-SUMMARY.md && grep -E "requirements-completed.*PERF-03.*PERF-04.*LEGAL-01.*LEGAL-02.*LEGAL-03" .planning/phases/07-launch-hardening/07-SUMMARY.md && grep -E "PERF-03.*Complete" .planning/REQUIREMENTS.md && grep -E "LEGAL-01.*Complete" .planning/REQUIREMENTS.md && grep -E "Phase 7.*Complete\|7/7" .planning/ROADMAP.md && grep -E "completed_phases: 7" .planning/STATE.md && grep -E "percent: 100" .planning/STATE.md</automated>
  </verify>
  <done>07-SUMMARY.md exists with the 5 requirements listed; REQUIREMENTS.md flips all 5 to Complete in both sections; ROADMAP.md marks Phase 7 Complete + traceability flips; STATE.md reflects 7/7 phases at 100%.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries (new in Phase 7)

| Boundary | Description |
|----------|-------------|
| browser → BFF /api/account/export | Authenticated user requests a JSON archive of their personal data (profile + meals + weights + corrections + vision usage). The request crosses from the browser into the Next.js BFF; Clerk session cookie authenticates. |
| BFF → Flask /me/export | The BFF forwards as Bearer JWT to Flask. Flask reads `g.clerk_user_id` (JWT-derived, NEVER from request body/query). The boundary check is the same as Phase 1's `@require_auth` decorator. |
| build-time → ingest of placeholder JPEGs | New on-disk binary content under `backend/tests/golden_set/photos/`. Pillow-generated, not externally sourced — no third-party-bytes risk for v1.0 placeholders. (Real photos in v1.1 inherit the Phase 6 T-06-08 mitigation — Pillow re-encode at ingest.) |
| operator → Anthropic console / Discord webhook | Operator sets the spend cap + webhook URL out-of-band. The webhook URL is a secret stored in Render env (COST_ALERT_WEBHOOK_URL); leaking it lets an attacker spam the operator's Discord channel — moderate impact. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-07-01 | Spoofing / Information Disclosure | /me/export endpoint — attacker provides forged or mismatched user identity to dump another user's data | mitigate | The route reads identity ONLY from `g.clerk_user_id`, which is set by `@require_auth` from a verified Clerk JWT — never from request body or query. `test_export_cross_user_isolation` in P7-C.1 explicitly seeds user A + user B and asserts the response for user A contains zero user_B identifiers. This is the same trust-anchor pattern as DELETE /me (Phase 2 T-02-01 / T-02-06). |
| T-07-02 | Tampering / Repudiation | Privacy policy gets out of date — a future sub-processor change (e.g. adding R2 for opt-in image history in v2) is not reflected, exposing the operator to GDPR claims | accept-with-process | Last-updated date is rendered on the page (§6). The disclaimer 'not been reviewed by counsel' is shown in the header — sets user expectation. LAUNCH.md §1 includes a 'verify /privacy reflects current data flows' line in the pre-launch checklist. Procedural mitigation: any code-level change introducing a new sub-processor MUST also update /privacy in the same PR (documented in 07-SUMMARY.md's Operator Follow-ups). |
| T-07-03 | Tampering | Copy-audit script drift — a future commit reintroduces a forbidden health claim and the audit isn't re-run | accept-with-process | Phase 7 does NOT add a CI gate (per CLAUDE.md anti-patterns — Render-only rewrite drops CI gates beyond pytest + pnpm build at deploy time). Mitigation is procedural: scripts/README-audit-copy.md documents `python scripts/audit_copy.py --strict` as a pre-launch step in LAUNCH.md §1. v1.1 may promote this to a CI gate once a real regression motivates it. Accepted for v1.0 launch. |
| T-07-04 | Information Disclosure | /me/export response is large enough to consume a metered Ghana connection — adversarial user repeatedly hits the endpoint to burn the operator's bandwidth | accept | CONTEXT.md states "≤10 MB even for power users". Render egress on the Starter tier is unmetered; even at 1000 DAU each pulling an export daily, the bandwidth is ≈10 GB/day — well within typical limits. No rate limit added in v1.0. Document the upper bound in 07-SUMMARY.md so a v1.1 rate limit decision has a starting point. |
| T-07-05 | Tampering | Placeholder golden-set JPEGs ship to the repo as binary blobs that a malicious contributor could swap for an exploit payload | accept | The placeholder JPEGs are 64×64 solid-colour Pillow outputs (kilobytes each); they are reviewed in the same PR that ships them; they live ONLY in `backend/tests/golden_set/photos/` and are not served by Flask or Next.js. The `RUN_GOLDEN_SET=1` gate keeps them out of any default execution path. v1.1 real photos inherit the Phase 6 T-06-08 mitigation. |
| T-07-06 | Denial of Service | Route-group migration in P7-A.1 accidentally breaks a public route's middleware match and renders /workouts behind auth | mitigate | Route groups don't change URL paths — middleware.ts `isProtectedRoute` matches by path, not by file location. P7-A.1's `pnpm build` smoke + the existing P6-D.1 public-route comment block in middleware.ts is the trust anchor. P7-A.1 verify-block grep confirms /workouts builds as `○` (static) not `ƒ` (dynamic). Manual smoke: after deploy, `curl -I https://fitgh-web.onrender.com/workouts` returns 200, not a 307 redirect to /sign-in. |
</threat_model>

<verification>
End-of-phase checks (run by the executor before the phase-close commit):

1. **`cd backend && pytest` → 292 + new tests** — expect ≥ 296 (4 from test_me_export.py); the golden-set test is SKIPPED by default and does not contribute.
2. **`cd backend && RUN_GOLDEN_SET=1 pytest tests/golden_set/test_golden_vision.py -v` → PASSED in deterministic-fake mode**.
3. **`cd frontend && pnpm build` → 108 routes, includes /(public)/* and /(authed)/* paths under unchanged URLs**.
4. **`cd frontend && pnpm test` → 100/100 (or 101/101 if a download-button test added)**.
5. **`python scripts/audit_copy.py --strict` → exit 0**.
6. **`git status --short` → only GEMINI.md remains untracked**.
7. **`grep -L "ClerkProvider" frontend/src/app/layout.tsx` succeeds** (root layout no longer mounts Clerk).
8. **`curl -I http://localhost:3000/workouts` after `pnpm start` → 200** (route stays public after move).
9. **`grep "Last updated.*2026-05-13" frontend/src/app/(public)/privacy/page.tsx` succeeds**.
10. **`grep "Content-Disposition" frontend/src/app/api/account/export/route.ts` succeeds**.
11. **Manual /api/account/export smoke test:** start `pnpm start`, sign in via Clerk Dev keys, visit /settings, click 'Download my data' → confirm a JSON file downloads with filename matching `fitgh-export-<clerk_id>-<YYYY-MM-DD>.json` and a payload containing _export_metadata + the six arrays.
12. **Anti-pattern grep before commit:** `grep -r "from @sentry" frontend/src backend/app` returns empty; `grep -r "@vercel/analytics" frontend` returns empty; `grep -r "cloudflare" --include='*.ts' --include='*.tsx' --include='*.py' frontend/src backend/app` returns empty.
</verification>

<success_criteria>
Phase close criteria (all must hold):

- **PERF-03:** /workouts public route renders WITHOUT loading the Clerk SDK; lighthouse-postfix.md exists with cold+warm Performance / Accessibility / Best Practices scores; if Performance ≥ 90 declare Complete, else document residual bottleneck + v1.1 mitigation without blocking phase close.
- **PERF-04:** LAUNCH.md §3 documents the WebPageTest Lagos run command + the p75 TTFB pass criterion (≤ 2 s) + the Cloudflare-in-front fallback if it fails; 07-SUMMARY.md Measurements either records the executor's WebPageTest run OR marks it as an operator follow-up (CONTEXT.md allows either).
- **LEGAL-01:** Real /privacy page renders all 6 sections; disclaimer header present; 5 sub-processors named (Anthropic / Clerk / Atlas / Render / GitHub Actions — NOT R2); linked from root footer + /settings + onboarding screen 3.
- **LEGAL-02:** GET /me/export returns 200 with the 6 arrays + _export_metadata; BFF sets Content-Disposition: attachment; UI button in /settings triggers a browser download with the correct filename; cross-user-isolation test passes.
- **LEGAL-03:** scripts/audit_copy.py runs clean in --strict mode; the standard disclaimer is in the root layout footer AND in onboarding screen 3.
- **Golden set:** 10 placeholder JPEGs + manifest.json + skipif-gated test_golden_vision.py exist; deterministic-fake mode passes < 25 % MAPE assertion; result recorded in golden-set-result.md.
- **Operator runbook:** LAUNCH.md at repo root with 5 sections + NON-steps; .env.example documents COST_ALERT_WEBHOOK_URL + FITGH_GIT_SHA.
- **Working-tree sweep:** git status shows only GEMINI.md untracked.
- **Traceability:** 07-SUMMARY.md exists with requirements-completed = [PERF-03, PERF-04, LEGAL-01, LEGAL-02, LEGAL-03]; REQUIREMENTS.md + ROADMAP.md flip all 5 to Complete; STATE.md milestone = v1.0 complete; progress 7/7 phases.
- **Backend pytest:** count is ≥ 296 (was 292; +4 from test_me_export.py).
- **Anti-patterns absent:** no Cloudflare-in-front wiring, no custom-domain config, no Sentry re-add, no Vercel Analytics, no size-limit CI gate, no gitleaks CI rules — verified by anti-pattern grep before phase-close commit.
</success_criteria>

<output>
After completion, create `.planning/phases/07-launch-hardening/07-SUMMARY.md` (Task P7-E.3) and commit per the standard phase-close convention. The commit message body lists the 5 requirements completed and references this PLAN.md.
</output>
