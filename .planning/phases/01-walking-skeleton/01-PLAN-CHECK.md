# Plan Check — Phase 1: Walking Skeleton

**Date:** 2026-05-11
**Plan reviewed:** .planning/phases/01-walking-skeleton/01-PLAN.md (30 tasks across Slices 0/A-J)
**Reviewer:** gsd-plan-checker (goal-backward)
**Verdict:** **PASS-WITH-FLAGS**

---

## Verdict Summary

The plan, if executed verbatim, will achieve all five ROADMAP success criteria and close all thirteen targeted REQ-IDs. Every Phase 1 invariant from PITFALLS.md (M-1, M-5, D-1, S-1, S-2) is encoded as a task acceptance criterion rather than a narrative aside, and the goal-backward "Phase 1 Done When" table at the end of the plan (lines 1211-1228) maps every success criterion and every requirement ID to specific proving tasks. Findings are limited to four FLAGS — operational tightenings, not blockers — and several PASS notes worth preserving.

---

## Success-Criterion Coverage Matrix

| # | Success Criterion | Proving Task(s) | Status |
|---|-------------------|-----------------|--------|
| 1 | Sign in (Clerk email/password OR Google) then land on /dashboard showing email pulled from Atlas through Flask | WS-D.1, WS-D.2, WS-D.3, WS-E.1, WS-E.2, WS-E.3, WS-F.2, WS-F.3, WS-J.1 SC-1 | PROVEN |
| 2 | Sign out from any page; refreshing lands on /sign-in (httpOnly cookie cleared) | WS-D.4 (SignOutButton on /dashboard), WS-J.1 SC-2 | PROVEN |
| 3 | /health returns {ok:true, mongo:"connected"} from Fly.io JNB; static egress IP pinned in Atlas allowlist; 0.0.0.0/0 removed from production | WS-G.1, WS-G.2, WS-G.4, WS-H.1, WS-H.2, WS-H.3, WS-J.1 SC-3 | PROVEN |
| 4 | CI fails when First Load JS > 180 KB gzipped; gitleaks pre-commit blocks a commit containing a Mongo URI | WS-0.4, WS-0.5, WS-A.4, WS-A.5, WS-J.1 SC-4 | PROVEN |
| 5 | Sentry FE + BE and Vercel Analytics + Speed Insights receive >=1 real event; Flask Authorization: Bearer JWT verified networkless on every protected request | WS-B.2, WS-B.4, WS-B.5, WS-I.2, WS-I.3, WS-J.1 SC-5 | PROVEN |

---

## Requirement Coverage

| REQ-ID | Task(s) | Status |
|--------|---------|--------|
| AUTH-01 | WS-D.1, WS-D.2, WS-D.3, WS-F.1, WS-F.2, WS-F.3 | COVERED |
| AUTH-02 | WS-D.1, WS-D.2, WS-D.3 | COVERED |
| AUTH-03 | WS-D.1, WS-D.4 | COVERED |
| AUTH-06 | WS-B.4 (require_auth decorator), WS-E.1 (BFF JWT forward), WS-E.2 (Flask /me), WS-E.3 (/dashboard consumes) | COVERED |
| SEC-01 | WS-0.3 (.gitignore + .env.example), WS-0.4 (gitleaks pre-commit + smoke), WS-0.5 (gitleaks CI workflow) | COVERED |
| SEC-02 | WS-0.1 (rotate password + create least-priv fitgh-app user) | COVERED |
| SEC-03 | WS-B.2 (flask-cors explicit origins, supports_credentials=False), WS-B.5 test_cors.py (preflight from evil origin rejected) | COVERED |
| SEC-04 | WS-B.3 (MongoClient(maxPoolSize=10, tls=True) module-level singleton), WS-B.5 test_db.py, WS-C.2, WS-H.1, WS-H.2 | COVERED |
| OBS-01 | WS-B.2 (BE before_send scrubber drops email/image/kcal keys), WS-B.5 test_sentry_scrubber.py, WS-I.3 (FE beforeSend + smoke tests) | COVERED |
| OBS-02 | WS-I.2 (Vercel Analytics + Speed Insights wired in app/layout.tsx), WS-J.1 SC-5 | COVERED |
| PERF-01 | WS-A.4 (180 KB budget config), WS-A.5 (Three.js bloat smoke-test PR proves the gate fails), WS-0.5 (CI workflow scaffolded) | COVERED |
| DEPLOY-01 | WS-A.1 (Next.js scaffold), WS-I.1 (Vercel connect + env), WS-I.2 (Analytics/Speed Insights enabled) | COVERED |
| DEPLOY-02 | WS-G.1 - WS-G.5 (Dockerfile + fly.toml jnb + secrets + deploy + egress-cost gate), WS-H.1 - WS-H.3 (egress IP + Atlas allowlist) | COVERED |

**Result:** 13 / 13 requirement IDs present in `requirements:` frontmatter AND covered by at least one tasks `REQ-IDs:` field AND a task acceptance criterion. No requirement is silently dropped.

---

## Skeleton Invariants

| Invariant | Where Encoded | Status |
|-----------|---------------|--------|
| Tailwind v4 install path (NOT v3 tailwind.config.js) | Skeleton Invariant #1 (line 274); WS-A.1 acceptance asserts postcss.config.mjs contains @tailwindcss/postcss: {}, globals.css contains @import "tailwindcss", AND test ! -f frontend/tailwind.config.js is in the verify command; WS-A.2 asserts components.json has "config": "" (the v4 marker per Gotcha G1) | PRESENT |
| Clerk Python SDK httpx.Request wrapper quirk (Gotcha G5) | Skeleton Invariant #2 (line 275); WS-B.4 acceptance requires the decorator to construct httpx.Request(method=request.method, url=str(request.url), headers=dict(request.headers)) and pass it to _clerk.authenticate_request(...) verbatim per research section 3.8 | PRESENT |
| Sentry PII scrubber at commit 1 (not retrofitted) | Skeleton Invariant #3 (line 276); WS-B.2 acceptance requires before_send=scrub registered at sentry_sdk.init() in extensions.py; scrub drops request.headers.authorization, user.email, user.username, extra.email, breadcrumb data.image, breadcrumb data.kcal; WS-B.5 test_sentry_scrubber.py asserts the keys are removed | PRESENT |
| PyMongo MongoClient(maxPoolSize=10) module-level singleton (SEC-04) | Skeleton Invariant #4 (line 277); WS-B.3 ships the singleton at module scope; WS-C.2 removes the None-fallback shim so missing MONGODB_URI fails loudly at import; WS-B.5 test_db.py asserts client.options.pool_options.max_pool_size == 10 and tls=True | PRESENT |
| Flask CORS explicit origin allowlist (no wildcard) (SEC-03) | Skeleton Invariant #5 (line 278); WS-B.2 acceptance specifies origins=config.CORS_ALLOWED_ORIGINS, supports_credentials=False, allow_headers=[Content-Type, Authorization]; WS-B.5 test_cors.py asserts an evil-origin preflight is rejected | PRESENT |
| .env-glob gitignored AND gitleaks pre-commit BEFORE any secret-touching commit (SEC-01) | Skeleton Invariant #6 (line 279); slice ordering enforces it: WS-0.3 lands gitignore, WS-0.4 installs gitleaks pre-commit + deliberate-leak smoke test, WS-0.5 lands the CI workflow ALL before Slice C touches the rotated Mongo URI. Execution Notes #1 (line 1257) restates the ordering. | PRESENT |
| size-limit measures App Router First Load JS at 180 KB gate (PERF-01) | Skeleton Invariant #7 (line 280); WS-A.4 ships .size-limit.json with limit: 180 kB and globs targeting .next/static/chunks/app/dashboard plus framework chunks; WS-A.5 flips the CI job from continue-on-error: true to false and verifies failure via the Three.js bloat smoke-test PR | PRESENT |
| Least-privilege Atlas DB user fitgh-app with readWrite@fitgh (NOT atlasAdmin) (SEC-02) | Skeleton Invariant #8 (line 281); WS-0.1 acceptance requires the new user to be readWrite@fitgh ONLY (explicitly NOT atlasAdmin, NOT readWriteAnyDatabase) | PRESENT |
| Atlas password rotation EXPLICITLY a task (STATE.md blocker + SEC-02) | WS-0.1 acceptance: open Atlas Dashboard, Database Access, existing user, Edit Password; set 32-char random password; OLD password invalidated; flagged [BLOCKER, USER ACTION] and checkpoint:human-action so the executor must pause. Slice ordering: WS-C.1 (real Mongo URI in .env.local) depends on WS-0.1. | PRESENT |
| Static egress IP allocated, pinned in Atlas allowlist, 0.0.0.0/0 removed from production (DEPLOY-02) | Skeleton Invariant #9 (line 282); WS-G.5 verifies the 2026 pricing (STATE.md blocker, halt-if-over-$5/mo), WS-H.1 runs fly ips allocate-egress -r jnb, WS-H.2 adds the IPv4/32 entry AND removes 0.0.0.0/0 from production, WS-H.3 re-hits /health to prove the lockdown did not break the connection | PRESENT |
| Sentry FE source-map upload AND BE init both present (OBS-01) | WS-B.2 ships BE sentry_sdk.init with FlaskIntegration + PyMongoIntegration + before_send; WS-I.3 runs pnpm dlx @sentry/wizard@latest -i nextjs --saas which produces instrumentation.ts, sentry.client.config.ts, sentry.edge.config.ts, sentry.server.config.ts AND modifies next.config.js with withSentryConfig (source-map upload). Gotcha G7 (distinct FE/BE DSNs) explicitly verified. | PRESENT |
| Vercel Analytics + Speed Insights installed (OBS-02) | WS-I.2 acceptance: pnpm add @vercel/analytics @vercel/speed-insights; Analytics and SpeedInsights rendered inside body after children; dashboards enabled in Vercel UI; >=1 pageview verified | PRESENT |
| Fly.io jnb, min_machines_running=1 (always-on, no cold start), shared-cpu-1x 512 MB | WS-G.2 fly.toml block (lines 960-982) sets primary_region=jnb, auto_stop_machines=off, min_machines_running=1, [[vm]] size=shared-cpu-1x memory=512mb, plus /health HTTP check; WS-G.4 runs 3x curl over 30 s to verify no cold-start | PRESENT |
| Clerk webhook for user.created creating users Atlas doc (so /dashboard has something to fetch) | WS-F.1 configures Clerk webhook endpoint with user.created + user.deleted events; WS-F.2 ships the BFF svix-verify route; WS-F.3 ships the Flask handler that upserts the users doc on user.created; WS-B.5 test_webhooks.py covers the path with mongomock | PRESENT |

**Result:** 13 / 13 invariants encoded as task acceptance criteria (not just narrative). The Clerk httpx.Request quirk and the Tailwind v4 path are especially well-protected because both have NEGATIVE assertions in the verify command (test ! -f tailwind.config.js).

---

## Dependency Sanity

- WS-C.1 (real Atlas connection) declares Deps: WS-0.1, WS-B.3 rotation precedes real-credential use. CORRECT.
- WS-E.1 (Clerk to Flask boundary) declares Deps: WS-D.4, WS-C.2 Slices B (backend skeleton via C.2) and D (frontend Clerk) both precede E. CORRECT.
- WS-H.1 (egress IP) declares Deps: WS-G.5 and WS-H.2 (Atlas allowlist tightening) declares Deps: WS-H.1 egress IP allocated AND price-verified before Atlas allowlist is locked down. CORRECT.
- WS-J.1 (E2E sign-off) declares Deps: WS-I.3, WS-F.3 Slice I (Vercel + observability) and Slice F (webhook in prod) precede sign-off. CORRECT.
- No circular dependencies detected. Slice ordering (line 1257) explicitly says: Slice 0 -> (A parallel B) -> C -> D -> E -> F -> G -> H -> I -> J.

---

## Out-of-Scope Discipline

Plan Out of Scope block (lines 263-270) explicitly defers:
- Onboarding form, TDEE math, weights, GDPR delete -> Phase 2
- Ghana food table, multi-component meals, mongodump -> Phase 3
- LLM vision, Sonnet 4.6, user_corrections, OBS-03 cost alert -> Phase 4
- Rive .riv, kcal ring, Recharts -> Phase 5
- Exercises, PWA, LICENSES.md -> Phase 6
- Lagos WebPageTest, privacy policy, data-export -> Phase 7
- All v2 features

Zero scope creep detected.

---

## STATE.md Blockers

| Blocker | Disposition |
|---------|-------------|
| Atlas password rotation (M-5) | WS-0.1 with [BLOCKER, USER ACTION] flag, checkpoint:human-action type execution pauses until user confirms. Slice C cannot proceed without it. RESOLVED in plan. |
| Fly.io static egress IP 2026 cost | WS-G.5 (checkpoint:decision) verifies the $3.60/mo Jan 2026 price; halt-condition at $5/mo; STATE.md update is part of acceptance. RESOLVED in plan. |
| Rive designer pipeline (Phase 5) | Explicitly out of scope per line 267; not a Phase 1 task. CORRECTLY DEFERRED. |

---

## Findings

### BLOCK

None.

### FLAG

#### FLAG-1: BACKEND_URL env var missing from top-level .env.example acceptance (severity: warning, dimension: key_links_planned)

WS-E.1 BFF (frontend/src/app/api/me/route.ts) reads process.env.BACKEND_URL, and WS-G.3 sets it as a Fly secret, and WS-I.1 sets it in Vercel env vars but the .env.example acceptance in WS-0.3 (line 390) does NOT list BACKEND_URL (it lists MONGODB_URI, CLERK_-keys, CORS_ALLOWED_ORIGINS, SENTRY_-keys). The frontend-specific .env.local.example in WS-D.2 DOES list it, so the actual development workflow is fine; the gap is the top-level documentation. Suggested fix: add BACKEND_URL= to the WS-0.3 .env.example acceptance list.

#### FLAG-2: Sentry scrubber test does not assert kcal and image bytes removal (severity: warning, dimension: skeleton_invariant_verification)

Skeleton Invariant #3 says the scrubber drops email, image bytes, kcal totals. WS-B.2 acceptance (line 570) names all three: user.email, breadcrumbs.data.image, breadcrumbs.data.kcal. But WS-B.5 test_sentry_scrubber.py (line 635) only asserts removal of request.headers.authorization and user.email it does NOT exercise the kcal or image breadcrumb paths. Phase 1 does not produce kcal/image events yet, so the gap is latent; Phase 4 will discover it the first time vision data appears in an error. Suggested fix: expand the WS-B.5 test fixture to include a breadcrumb with data.kcal and data.image and assert those keys are also removed. Cheap to add now, painful to retrofit after Phase 4.

#### FLAG-3: /dashboard server-side fetch hops through HTTP unnecessarily (severity: warning, dimension: key_links_planned)

WS-E.3 (line 845) fetches /api/me from a server component with cookie header passed through. This works but a same-origin server-side fetch in App Router can be done more cleanly by calling auth() directly + getToken() inline in dashboard/page.tsx and calling Flask directly without the BFF hop. Either approach achieves SC-1; the current one adds a same-process HTTP roundtrip. Not a blocker the verification commands prove the path works but worth a refactor note for the executor (the BFF route still has value for client-side calls in Phase 2+).

#### FLAG-4: Plan hard-codes fitgh.vercel.app as the assigned Vercel domain (severity: warning, dimension: assumption_safety)

WS-D.1, WS-F.1, WS-G.3, WS-I.1, WS-I.2, WS-I.3 all hard-code https://fitgh.vercel.app as the production URL. If Vercel assigns a different default (e.g., fitgh-abc123.vercel.app because fitgh is taken or transformed), the Clerk Domain setup, the CLERK_AUTHORIZED_PARTIES Fly secret, the CORS_ALLOWED_ORIGINS Fly secret, and the Clerk webhook URL all need updating in one cascading edit. Suggested fix: WS-I.1 should capture the actual assigned Vercel URL as its first acceptance step, then explicitly require the executor to back-propagate it into WS-D.1 (Clerk Domain), WS-G.3 (fly secrets set CLERK_AUTHORIZED_PARTIES and CORS_ALLOWED_ORIGINS), and WS-F.1 (Clerk webhook URL). The plan today depends on the URL being available; spell out the back-propagation so the executor does not silently leave the wrong value somewhere.

### PASS Notes

1. **Three-layer defence on the size-limit gate.** WS-A.4 sets the config, WS-A.5 flips the CI to continue-on-error: false AND verifies failure via a deliberate Three.js bloat PR (proving the negative case). More rigorous than the typical "we have a CI gate" claim.
2. **gitleaks given a deliberate-leak smoke test.** WS-0.4 requires the developer to stage a real-looking Mongo URI and confirm the commit is blocked, then revert. Most plans skip negative-case verification.
3. **Honest staging of the DB connection.** Slice B ships a mongo:"stubbed" health response so backend work can proceed in parallel without the rotated Mongo URI; WS-C.2 explicitly REMOVES the None-fallback shim so the production code path fails loudly on missing MONGODB_URI. This is the right way to handle the "real credentials block work" problem without ending up with permanent stub code.
4. **The 404 from /api/me is the verification target for Slice E,** not the 200. The plan explicitly notes (line 809): THIS 404 IS THE PROOF the JWT verification works without it Flask would 401, not 404. Excellent goal-backward thinking the executor cannot trivially declare success on a happy path that depends on Slice Fs webhook.
5. **Clerk Python SDK quirk encoded as a verifiable invariant,** not a comment. WS-B.4 acceptance specifies the exact httpx.Request(method=request.method, url=str(request.url), headers=dict(request.headers)) construction. The single most-likely-to-be-missed gotcha in the entire plan is protected at acceptance level.
6. **Atlas password rotation is checkpoint:human-action AND gates Slice C via Deps: WS-0.1.** Combined with the gitleaks pre-commit going in at WS-0.4 BEFORE any secret-handling commit could run, the M-5 exposed-password loop is fully closed.
7. **min_machines_running=1 and auto_stop_machines=off are both explicitly set in the fly.toml block** no cold-start ambiguity. The 3x curl over 30 s in WS-G.4 verifies it.
8. **Goal-backward verification table (lines 1211-1228) is present and complete.** Every ROADMAP success criterion has named proving tasks; every REQ-ID is either in that table or in the "Additional requirement coverage" block immediately after.

---

## Recommended Action

**PASS-WITH-FLAGS** Executor proceeds with the plan as-written. The four FLAGS above are not blockers; they are operational tightenings that should be folded in either as a Phase 1.x patch during execution (FLAG-1, FLAG-2) or applied opportunistically when the executor reaches the relevant slice (FLAG-3, FLAG-4). None of the four would cause the phase to miss a ROADMAP success criterion if left unaddressed but addressing FLAG-2 now will save a Phase 4 retrofit, and addressing FLAG-4 now will save a debugging session when Vercel assigns an unexpected URL.

Proceed to /gsd-execute-phase 1.

---
*Plan check generated 2026-05-11 by gsd-plan-checker.*
