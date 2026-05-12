# Plan Check: Phase 01 (Replan 2026-05-12)

**Plan reviewed:** .planning/phases/01-walking-skeleton/01-PLAN.md (replan_of: 2026-05-11 plan)
**Reviewer:** gsd-plan-checker (goal-backward, post-error resume)
**Date:** 2026-05-12
**Replaces:** the May-11 PASS-WITH-FLAGS check for the deprecated Vercel+Fly+Clerk-twin plan.

## Verdict: PASS-WITH-FLAGS

The replanned 18-task, 7-slice plan delivers all five ROADMAP Phase 1 Success Criteria. Every forbidden re-introduction is absent. Every "do-not-rescaffold" file from the master partial-execution is correctly handled as MODIFY/DELETE (never CREATE). Tests will hold. Three operational FLAGs (sync-on-demand JWT email source, Clerk origins ordering, Render Free OOM risk) are real but each has a stated mitigation already in the plan or is below the bar of blocking execution. Two MEDIUM cleanups (test-count drift, CI pnpm-lint script-existence) should be folded in during execution. Proceed.

---

## Goal-backward analysis

**SC-1 -- Sign up / sign in via Clerk Production on Render-hosted Next.js; lands on /dashboard showing email from Atlas via Flask.** Covered end-to-end. WS-A.3 sets up the single Clerk Production instance with Email/Password + Google OAuth, dual authorized origins (localhost:3000 + Render URL), and the correct sign-in/sign-up/after-sign-in paths. WS-D.1 installs @clerk/nextjs version 5, wires ClerkProvider in layout.tsx, and creates middleware.ts protecting /dashboard(.*) + /api/me. WS-D.2 ships SignIn / SignUp route segments. WS-D.3 ships the BFF /api/me that calls auth().getToken() and forwards Authorization: Bearer JWT to Flask, plus the dashboard server component that reads /api/me and renders the email. WS-E.2 ships /me with sync-on-demand upsert against the Mongo users collection. WS-F.0 (local smoke) and WS-F.2 (deployed sign-off) verify the full chain. Email source for the upsert is the one weak link -- see FLAG-1 below.

**SC-2 -- Sign-out works.** Covered. WS-D.3 creates frontend/src/components/sign-out-button.tsx as a client component using SignOutButton from @clerk/nextjs with redirectUrl set to /sign-in. The button is mounted in dashboard/page.tsx. WS-F.0 step 4 and WS-F.2 steps 4-5 both verify: sign out, refresh, land on /sign-in. The middleware (WS-D.1) protects /dashboard, so a refresh after sign-out triggers the redirect cleanly.

**SC-3 -- Flask /health returns mongo:connected from Render against Atlas M0 with 0.0.0.0/0 + 32-char password + scoped readWrite@fitgh.** Covered. The /health handler already on master returns ok+mongo and is gated by client.admin.command(ping). WS-A.1 relaxes Atlas allowlist to 0.0.0.0/0 and verifies the fitgh-app user is readWrite@fitgh (not atlasAdmin). WS-B.1 declares healthCheckPath:/health on the fitgh-api Render service. WS-F.1 step 3 and WS-F.2 step 8 require curl to fitgh-api/health to return ok:true mongo:connected. The PyMongo singleton (maxPoolSize=10, tls=True) is already on master per db.py and asserted by test_db.py -- SEC-04 is preserved.

**SC-4 -- git push main auto-deploys both services; pytest + pnpm build are the gates; failures halt deploy.** Covered. WS-B.1 render.yaml declares autoDeploy:true and branch:main on both services. WS-C.1 ci.yml runs pytest (backend job, with pytest -x --cov) and pnpm build (frontend job) on push to main and PRs. Render healthCheckPath:/health rolls the deploy back on failure -- explicitly called out in the Test Plan smoke-tests section. The build commands themselves are the gates: backend pip install -r requirements.txt then gunicorn; frontend pnpm install --frozen-lockfile then pnpm build. If pnpm build errors (e.g., type error in dashboard/page.tsx), Render aborts the deploy and keeps the previous version live. Covered correctly. See MEDIUM-2 for one CI-step caveat.

**SC-5 -- Three SaaS checkpoints only. No Fly, no Vercel, no Sentry, no size-limit, no custom gitleaks CI.** Covered. The three checkpoint:human-action tasks are WS-A.1 (Atlas), WS-A.2 (Render), WS-A.3 (Clerk). Slice 0 (WS-0.1) explicitly DELETEs backend/Dockerfile, backend/.dockerignore, frontend/.size-limit.json, .github/workflows/gitleaks.yml, .github/workflows/frontend.yml, .github/workflows/backend.yml, plus the size-limit deps and the size script from package.json. The deferred_requirements_from_phase frontmatter explicitly carries SEC-01, SEC-02, SEC-03, OBS-01, OBS-02, PERF-01. No Fly/Vercel/Sentry-wizard/static-egress-IP/Cloudflare-in-front re-introductions anywhere in the plan body or env surface. The local gitleaks pre-commit (.pre-commit-config.yaml and .gitleaks.toml) is correctly KEPT -- only the CI job is deleted.

---

## Findings

### HIGH (block execution)

None.

### MEDIUM (fix before executing)

**MEDIUM-1: Test-count math in WS-C.1 / WS-E.1 / WS-E.3 is off by one (drift from SUMMARY.md 22 claim).** Current master baseline is **21 passing tests** (verified: backend/.venv/Scripts/python.exe -m pytest backend/tests -q returns 21 passed), not 22 as the plan and SUMMARY.md claim. Test breakdown on master: test_health 2, test_me 3, test_db 2, test_cors 2, test_sentry_scrubber 7, test_webhooks 5 = **21**. Plan WS-E.1 says 22 - 4 = 18 passing after webhook deletion; actual will be 21 - 5 = **16**. WS-E.2 removes 1 (test_me_returns_503_when_db_not_configured) and adds 2 -> 17. WS-E.3 adds 2 -> **19**. The plan's final target of ~21 is wrong by ~2; the correct expected total post-Slice E is **19**. Fix: when executing, treat 19 (not 21) as the green-pass-target after Slice E, and update the WS-E.3 acceptance note in flight.

**MEDIUM-2: WS-C.1 ci.yml runs pnpm lint but the SC-4 wording is pytest + pnpm build are the gates.** frontend/package.json has lint set to next lint (verified). The plan CI step list is pnpm install -> pnpm lint -> pnpm tsc --noEmit -> pnpm build. SC-4 names only pytest + pnpm build. Two consequences: (a) next lint is deprecated as of Next 15.x and may emit warnings -- acceptable; (b) pnpm tsc --noEmit will surface type errors that pnpm build would also catch, so it is redundant-but-defensive. No correctness issue, but the executor should be ready for the CI run to fail on a lint nit that does not fail pnpm build. Recommend: leave both, since failing earlier is cheaper than waiting for next build, but document the wider gate surface in the WS-C.1 commit message.

**MEDIUM-3: WS-E.2 acceptance lists Tests 1-4 but does not assert the existing-doc upsert is a no-op on email/created_at.** The plan describes Test 1 as user is authenticated and a users doc exists for clerk_user_id, /me returns 200 email:existing-email (mongomock-backed) -- that is the existing-doc happy path. What is missing from the explicit tests pass block is an assertion that the setOnInsert block is a no-op when the doc exists (i.e., updated_at may move but created_at and email do not change on re-call). Not strictly required for SC-1, but the sync-on-demand semantic is exactly the kind of thing that silently drifts in Phase 2 when profile-edit lands. Recommend folding this into Test 1 during execution. Not blocking.

**MEDIUM-4: WS-E.4 plan text says remove CORS_ALLOWED_ORIGINS from the missing list in Config.validate(), which is correct, but also implies CLERK_WEBHOOK_SECRET is in validate() -- it is NOT.** Cross-checked backend/app/config.py: CLERK_WEBHOOK_SECRET is a dataclass field (default empty string) but is NOT in the missing list inside validate(). So removing it from the dataclass is a pure structural cleanup, not a validate-list change. The plan acceptance grep -n CLERK_WEBHOOK_SECRET backend/app/config.py returns zero hits -- correct. No risk; the medium is just to call out that the plan framing slightly overstates the validate() change. The dataclass-field deletion is the only change needed. Cosmetic.

### LOW (FYI -- optional fix)

**LOW-1: WS-D.3 builds the absolute URL inside dashboard/page.tsx via headers() + x-forwarded-proto + host.** This pattern is the canonical Next.js 15 App Router approach for same-origin server-side fetch, but it does add a network hop (BFF, then Flask) on a page that is already a server component and could call Flask directly with the verified Clerk JWT (the WS-D.3 acceptance even notes this). The plan retains the BFF hop on the (correct) reasoning that the BFF route has value for client-side calls in Phase 2+ (onboarding form, weight log). Same as the May-11 FLAG-3 -- same disposition: leave as-is.

**LOW-2: WS-G.1 SKELETON.md rewrite is gated on WS-F.2 completion.** The dependency is correct (do not rewrite the spec until the deploy is proven), but the executor will be mid-execution when WS-F.2 runs, which means the SKELETON.md rewrite is a late task in a long autonomous chain. If wall-clock fatigue is a concern, allow WS-G.1 to run in parallel with WS-F.0/F.1 since none of those touch SKELETON.md. Optional reordering only.

**LOW-3: WS-A.3 asks the user to add https://fitgh-web.onrender.com as a placeholder Clerk authorized origin, then update post-WS-F.1.** This is fine but worth noting: Render free tier sometimes hands out name-random.onrender.com if the slug is taken. The plan WS-F.1 step 4 explicitly says update Authorized Origins with the actual fitgh-web URL, which closes the loop. Pre-existing FLAG-4 disposition matches. Low risk.

**LOW-4: The .env.example will not contain BACKEND_URL after WS-0.2.** Old May-11 FLAG-1 is mooted because the replan renamed it to NEXT_PUBLIC_API_URL and explicitly lists it in WS-0.2 acceptance. No action needed.

---

## Three flagged risks -- verdict on each

### 1. Sync-on-demand email source -- FLAG, not block

The plan acknowledges this directly in WS-E.2: the email is needed for the dashboard render, and pulling it from Clerk session JWT is fine if Clerk includes it in the token claims by default (most Clerk applications do); if not, the SDK fetch on the missing-user path adds one HTTPS hop the first time only. This is a real risk and the mitigation is real: Clerk default JWT template does NOT include email as a top-level claim -- only sub (user id), sid, iat, exp, and a few session metadata fields. To get email, you either (a) customize the JWT template in the Clerk dashboard to include user.primary_email_address as a claim, OR (b) call Clerk(secret).users.get(user_id) on the missing-user path. The plan supports both paths inline. **Recommendation during execution:** customize the Clerk JWT template at WS-A.3 time to add email as a custom claim (adds about 30 seconds to the dashboard checklist, removes one HTTPS hop and one failure mode forever). Document the choice in decisions made on commit. Not blocking the plan as-written -- the SDK-fetch fallback works.

### 2. Clerk origins chicken-and-egg -- FLAG, not block

Real and called out. WS-A.3 places a placeholder origin (https://fitgh-web.onrender.com); WS-F.1 step 4 reconciles it post-deploy. If Render assigns a different slug, the user must manually update Clerk and the CLERK_AUTHORIZED_PARTIES Flask env-var. The plan handles both. The one thing not explicit: if Clerk authorized-origins list does NOT include the actual Render URL when the user first visits the deployed app, **Clerk middleware will hard-redirect to the Clerk-hosted error page, NOT to /sign-in**, and the user will see This domain is not authorized -- not a friendly experience. Mitigation: prepend WS-F.1 step 4 ahead of step 5 (CI verify) so origins are correct *before* the deployed-app smoke test. **Recommendation:** swap WS-F.1 step ordering -- capture Render URL -> update Clerk + Flask env-var -> THEN do CI verify and end-to-end test. Not blocking.

### 3. Render Free OOM risk -- FLAG, not block

Render Free tier for the Node service is 512 MB RAM. Next.js 15 + React 19 + Tailwind v4 + shadcn primitives + Clerk middleware compiles to a relatively heavy server. pnpm build itself peaks at around 700 MB in CI but Render build step happens in a separate container with more headroom (1 GB free). The runtime footprint of pnpm start for this app size is typically 150-250 MB -- under the 512 MB ceiling. Risk surfaces only if Phase 2+ (RHF + Zod + Recharts dynamic imports) inflates the bundle. **The plan locks Backend on Starter (7 USD/mo, no cold start) specifically because of Phase 4 latency.** Frontend on Free is the right call for Phase 1 -- the OOM risk is theoretical for this surface and can be promoted to Starter later if Phase 5 (Rive runtime) tips it over. Not blocking. Document in decisions on commit.

---

## Forbidden re-introductions check: PASS

Scanned the plan body, frontmatter, env surface, and must_haves for the forbidden tokens:

- Fly.io -> 0 hits in plan body (one historical reference in deprecation note frontmatter, which is correct -- replan_of: field). PASS.
- fly.toml / flyctl / JNB -> 0 hits. PASS.
- Static egress IP -> 0 hits. PASS.
- Cloudflare -> 0 hits. PASS.
- Sentry FE wizard / @sentry/nextjs / @sentry/wizard / instrumentation.ts -> 0 hits. The plan explicitly keeps extensions.py Sentry scrubber code in place but documents it as OPTIONAL (WS-E.3) -- that is NOT a re-introduction, it is code stays disabled, contract preserved. PASS.
- Vercel Analytics / Vercel Speed Insights / @vercel/analytics / @vercel/speed-insights -> 0 hits. PASS.
- size-limit -> multiple hits -- every single hit is in a DELETE context (DELETE frontend/.size-limit.json, remove size:size-limit script, remove size-limit and @size-limit/preset-app from devDependencies, etc.). PASS.
- Custom gitleaks CI job -> DELETE .github/workflows/gitleaks.yml in WS-0.1, with explicit Do NOT touch .pre-commit-config.yaml or .gitleaks.toml note. Local pre-commit kept; CI job dropped. PASS.

## Forbidden re-scaffolding check: PASS

Cross-referenced 01-SUMMARY.md files already on master list against the plan files_modified frontmatter:

- Flask app factory (backend/app/__init__.py) -> plan says MODIFY (drop webhooks blueprint registration). Correct.
- PyMongo singleton (backend/app/db.py) -> not in plan files_modified at all. Correctly left alone (shim already removed per STATE.md WS-C.2 verified 2026-05-11). PASS.
- Clerk middleware (backend/app/middleware/auth.py) -> not in plan files_modified. Plan WS-E.2 acceptance notes the email-claim consideration without modifying the file. Implicit modification is possible if the executor decides to set g.clerk_email -- that is still MODIFY, not CREATE. PASS.
- Frontend Tailwind v4 setup (frontend/postcss.config.mjs, globals.css, no tailwind.config.js) -> not in plan files_modified. Correctly preserved. PASS.
- shadcn primitives (frontend/src/components/ui/button,card,avatar,sonner) -> not in plan files_modified. Correctly preserved. PASS.
- 22 backend tests -> plan MODIFIES test_me.py, conftest.py; DELETES test_webhooks.py; CREATES test_sentry_init_conditional.py. All accounted for; the remaining files (test_health.py, test_cors.py, test_db.py, test_sentry_scrubber.py) are left alone. PASS.
- shared/schemas/user.schema.json -> not in plan files_modified. Correctly preserved. PASS.

The .env.example is in files_modified as MODIFY (not CREATE) -- correct.
backend/app/config.py is MODIFY (drop CLERK_WEBHOOK_SECRET, relax CORS validate) -- correct.
backend/app/routes/me.py is MODIFY -- correct.

## Test coverage check: PASS (with MEDIUM-1 numerical note)

Five Success Criteria mapped to specific tasks:

| SC | Proving tasks (replan) | Status |
|----|-----------------------|--------|
| 1 | WS-A.3, WS-D.1, WS-D.2, WS-D.3, WS-E.2, WS-F.0, WS-F.2 | COVERED |
| 2 | WS-D.3 (SignOutButton), WS-F.0 step 4, WS-F.2 steps 4-5 | COVERED |
| 3 | WS-A.1 (Atlas), WS-B.1 (healthCheckPath), WS-F.1 step 3, WS-F.2 step 8 | COVERED |
| 4 | WS-B.1 (autoDeploy:true), WS-C.1 (ci.yml pytest + pnpm build), WS-F.1 step 5 | COVERED |
| 5 | WS-A.1, WS-A.2, WS-A.3 (three checkpoints); WS-0.1 (deletes Fly/size-limit/gitleaks-CI); WS-E.3 (Sentry stays optional) | COVERED |

Every requirement in requirements frontmatter (AUTH-01/02/03/06, SEC-04, DEPLOY-01/02) has a proving task. Every deferred_requirements_from_phase entry (SEC-01/02/03, OBS-01/02, PERF-01) has both a frontmatter declaration AND a follow-up doc update (WS-G.2). No requirement is silently dropped.

Backend test expectations: plan claims around 21 final; correct count is **around 19**. See MEDIUM-1. Test coverage itself (what behaviors are exercised) is correct: existing-user happy path, missing-user upsert, no-auth 401, bad-bearer 401, Sentry init conditional both branches. CORS tests preserved as-is per WS-E.4 reasoning (still-valid posture).

---

## Recommended next step

Commit the plan and proceed to execution. Two in-flight fixes for the executor:

1. Treat the post-Slice E backend test count target as **19**, not 21 (MEDIUM-1).
2. At WS-F.1, reorder step 4 (update Clerk origins and Flask CLERK_AUTHORIZED_PARTIES) BEFORE step 5 (CI green check) so the deployed app first visit does not hit Clerk This domain is not authorized error page (Risk #2).

The three explicitly flagged risks (sync-on-demand email source, Clerk origins ordering, Render Free OOM) are real but each is either mitigated in-plan (option-A inline) or below the bar for blocking execution. The Phase 1 wedge -- Clerk to BFF to Flask to Atlas -- will close on a single git push main to Render with this plan.

---
*Plan check generated 2026-05-12 by gsd-plan-checker (post-error resume).*
