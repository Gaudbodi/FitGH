---
phase: 01-walking-skeleton
plan: 01
type: execute
wave: 1
depends_on: []
mode: mvp
walking_skeleton: true
autonomous: false
requirements:
  - AUTH-01
  - AUTH-02
  - AUTH-03
  - AUTH-06
  - SEC-01
  - SEC-02
  - SEC-03
  - SEC-04
  - OBS-01
  - OBS-02
  - PERF-01
  - DEPLOY-01
  - DEPLOY-02
slices:
  - "0: Foundation (secret hygiene, repo scaffold, CI shells)"
  - "A: Frontend skeleton (Next.js + Tailwind v4 + shadcn/ui + size-limit)"
  - "B: Backend skeleton (Flask + Sentry + PyMongo singleton stub)"
  - "C: MongoDB Atlas (password rotation + least-priv user + /health connected)"
  - "D: Clerk FE (provider, middleware, sign-in/up, sign-out)"
  - "E: Clerk -> Flask trust boundary (require_auth, /me, BFF /api/me)"
  - "F: Clerk webhook -> user.created -> Mongo users doc"
  - "G: Fly.io deploy (Dockerfile, fly.toml jnb, secrets)"
  - "H: Static egress IP + Atlas allowlist tightening"
  - "I: Vercel deploy + Analytics + Speed Insights"
  - "J: E2E smoke + sign-off"
files_modified:
  - .gitignore
  - .env.example
  - .nvmrc
  - README.md
  - .pre-commit-config.yaml
  - .gitleaks.toml
  - .github/workflows/frontend.yml
  - .github/workflows/backend.yml
  - .github/workflows/gitleaks.yml
  - frontend/package.json
  - frontend/.size-limit.json
  - frontend/middleware.ts
  - frontend/src/app/layout.tsx
  - frontend/src/app/page.tsx
  - frontend/src/app/sign-in/[[...sign-in]]/page.tsx
  - frontend/src/app/sign-up/[[...sign-up]]/page.tsx
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/api/me/route.ts
  - frontend/src/app/api/webhooks/clerk/route.ts
  - frontend/src/components/sign-out-button.tsx
  - frontend/instrumentation.ts
  - frontend/sentry.client.config.ts
  - frontend/sentry.edge.config.ts
  - frontend/sentry.server.config.ts
  - frontend/next.config.js
  - backend/requirements.txt
  - backend/requirements-dev.txt
  - backend/app/__init__.py
  - backend/app/config.py
  - backend/app/db.py
  - backend/app/extensions.py
  - backend/app/middleware/auth.py
  - backend/app/routes/health.py
  - backend/app/routes/me.py
  - backend/app/routes/webhooks.py
  - backend/tests/test_health.py
  - backend/tests/test_me.py
  - backend/tests/test_webhooks.py
  - backend/tests/test_cors.py
  - backend/tests/test_db.py
  - backend/tests/test_sentry_scrubber.py
  - backend/Dockerfile
  - backend/.dockerignore
  - backend/fly.toml
  - backend/gunicorn.conf.py
  - shared/schemas/user.schema.json
user_setup:
  - service: mongodb-atlas
    why: "Rotate exposed password (STATE.md blocker); create least-priv readWrite@fitgh user; verify cluster tier; pin Fly egress IPv4 in Network Access"
    env_vars:
      - name: MONGODB_URI
        source: "Atlas Dashboard -> Database -> Connect -> Drivers (with NEW rotated fitgh-app user)"
    dashboard_config:
      - task: "Rotate cluster admin password (exposed in chat per PITFALLS M-5)"
        location: "Atlas Dashboard -> Database Access -> existing user -> Edit -> Edit Password"
      - task: "Create least-priv user fitgh-app with role readWrite@fitgh (NOT atlasAdmin)"
        location: "Atlas Dashboard -> Database Access -> Add New Database User"
      - task: "After Slice H: add Fly egress IPv4 /32 to Network Access; remove 0.0.0.0/0 from production"
        location: "Atlas Dashboard -> Network Access -> IP Access List"
      - task: "Verify cluster tier is M0 (free); record tier in STATE.md if different"
        location: "Atlas Dashboard -> Database -> cluster0.pcd3g.mongodb.net -> Tier"
  - service: clerk
    why: "Auth provider (AUTH-01, AUTH-02, AUTH-03, AUTH-06); create Development + Production instances; configure email/password + Google OAuth; configure webhook for user.created/user.deleted"
    env_vars:
      - name: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
        source: "Clerk Dashboard -> API Keys -> Publishable key (pk_test_... for Dev, pk_live_... for Prod)"
      - name: CLERK_SECRET_KEY
        source: "Clerk Dashboard -> API Keys -> Secret key (sk_test_... for Dev, sk_live_... for Prod)"
      - name: CLERK_WEBHOOK_SECRET
        source: "Clerk Dashboard -> Webhooks -> endpoint -> Signing Secret (whsec_...)"
      - name: CLERK_AUTHORIZED_PARTIES
        source: "Comma-separated list of allowed origins; for Phase 1: 'http://localhost:3000,https://fitgh.vercel.app'"
    dashboard_config:
      - task: "Create Development + Production application instances named 'FitGH'"
        location: "Clerk Dashboard -> Create Application"
      - task: "Enable Email/Password + Google OAuth in BOTH instances; leave other providers off"
        location: "Clerk Dashboard -> User & Authentication -> Email, Phone, Username + Social Connections"
      - task: "Paths: Sign-in URL=/sign-in, Sign-up URL=/sign-up, After sign-in URL=/dashboard, After sign-up URL=/dashboard"
        location: "Clerk Dashboard -> Customization -> Paths"
      - task: "Domains: add http://localhost:3000 to Dev instance; add https://fitgh.vercel.app to Production instance"
        location: "Clerk Dashboard -> Domains"
      - task: "Add webhook endpoint: https://fitgh.vercel.app/api/webhooks/clerk -> events user.created + user.deleted; copy whsec_"
        location: "Clerk Dashboard -> Webhooks -> Add Endpoint"
  - service: fly.io
    why: "Backend host (DEPLOY-02); always-on shared-cpu-1x 512MB in jnb region; static egress IPv4 ($3.60/mo per IP from Jan 2026) for Atlas allowlist pinning"
    env_vars:
      - name: FLY_API_TOKEN
        source: "Fly.io Dashboard -> Personal Access Tokens -> Create (for CI later; Phase 1 uses local flyctl auth)"
    dashboard_config:
      - task: "Run flyctl auth signup or flyctl auth login locally (browser-based)"
        location: "Terminal: 'flyctl auth login' opens browser"
      - task: "Verify billing is configured (egress IP $3.60/mo requires a card on file even on Hobby trial)"
        location: "Fly.io Dashboard -> Organization -> Billing"
      - task: "After Slice G deploys: run 'fly ips allocate-egress -r jnb' and capture the IPv4; if cost > $5/mo, halt and discuss fallback"
        location: "Terminal: 'fly ips allocate-egress'"
  - service: sentry
    why: "Error capture FE + BE (OBS-01) with PII scrubbing"
    env_vars:
      - name: NEXT_PUBLIC_SENTRY_DSN
        source: "Sentry Dashboard -> Projects -> fitgh-frontend -> Settings -> Client Keys (DSN)"
      - name: SENTRY_DSN_BACKEND
        source: "Sentry Dashboard -> Projects -> fitgh-backend -> Settings -> Client Keys (DSN)"
      - name: SENTRY_AUTH_TOKEN
        source: "Sentry Dashboard -> Settings -> Auth Tokens -> Create (org-scoped for source-map upload)"
    dashboard_config:
      - task: "Create two projects: 'fitgh-frontend' (platform: Next.js) and 'fitgh-backend' (platform: Python Flask)"
        location: "Sentry Dashboard -> Create Project"
      - task: "Verify free tier is sufficient (5k errors/month) for Phase 1 smoke; upgrade only if Phase 4 vision needs it"
        location: "Sentry Dashboard -> Settings -> Subscription"
  - service: vercel
    why: "Frontend host (DEPLOY-01); Analytics + Speed Insights free on Hobby tier"
    env_vars:
      - name: BACKEND_URL
        source: "Set in Vercel Project Settings -> Environment Variables; value is the Fly.io app URL (https://fitgh-api.fly.dev)"
    dashboard_config:
      - task: "Connect GitHub repo to Vercel; set Root Directory = 'frontend', Framework = Next.js, Node = 20"
        location: "Vercel Dashboard -> Add New Project -> Import Git Repository"
      - task: "Set Production + Preview env vars: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY, CLERK_WEBHOOK_SECRET, BACKEND_URL, NEXT_PUBLIC_SENTRY_DSN, SENTRY_AUTH_TOKEN"
        location: "Vercel Dashboard -> Project -> Settings -> Environment Variables"
      - task: "Enable Analytics + Speed Insights in project settings (free tier)"
        location: "Vercel Dashboard -> Project -> Analytics tab + Speed Insights tab"

must_haves:
  truths:
    - "A signed-up user can complete email/password OR Google OAuth via Clerk and land on /dashboard showing their email from MongoDB Atlas through Flask."
    - "A user can sign out from /dashboard; refreshing after sign-out lands them on /sign-in (httpOnly __session cookie cleared)."
    - "Flask /health returns {ok:true, mongo:'connected'} from the Fly.io jnb machine in production."
    - "Atlas Network Access lists the Fly.io static egress IPv4 (/32) and does NOT contain 0.0.0.0/0 in production."
    - "A CI PR that pushes First Load JS above 180 KB gzipped on /dashboard fails the size-limit job."
    - "A commit containing a Mongo URI is blocked by gitleaks (locally via pre-commit AND in CI workflow)."
    - "Sentry FE and BE have each received at least one real error event with email/PII scrubbed from context."
    - "Vercel Analytics and Speed Insights show at least one pageview from the deployed app."
    - "Flask uses clerk.authenticate_request() (networkless via cached JWKS) on every protected request — no per-request call to Clerk API."
  artifacts:
    - path: "frontend/src/app/dashboard/page.tsx"
      provides: "Authenticated server component rendering user email from /api/me"
      contains: "fetch.*api/me"
    - path: "frontend/src/app/api/me/route.ts"
      provides: "BFF route that verifies Clerk session, mints JWT via getToken(), forwards Authorization: Bearer to Flask"
      contains: "getToken|Bearer"
    - path: "frontend/src/app/api/webhooks/clerk/route.ts"
      provides: "Svix-verified Clerk webhook forwarder to Flask"
      contains: "svix|Webhook"
    - path: "frontend/middleware.ts"
      provides: "clerkMiddleware with public routes for sign-in/up and webhook; protects everything else"
      contains: "clerkMiddleware|createRouteMatcher"
    - path: "backend/app/db.py"
      provides: "Module-level singleton MongoClient with maxPoolSize=10, tls=True"
      contains: "MongoClient|maxPoolSize"
    - path: "backend/app/middleware/auth.py"
      provides: "@require_auth decorator using clerk-backend-api networkless verify"
      contains: "authenticate_request|require_auth"
    - path: "backend/app/routes/health.py"
      provides: "GET /health returning {ok:true, mongo:'connected'}"
      contains: "mongo.*connected"
    - path: "backend/app/routes/me.py"
      provides: "GET /me returning {email} from users.find_one({clerk_id:...})"
      contains: "find_one"
    - path: "backend/app/routes/webhooks.py"
      provides: "POST /webhooks/clerk handling user.created (upsert) and user.deleted"
      contains: "user\\.created|upsert"
    - path: "backend/app/extensions.py"
      provides: "Sentry init with before_send PII scrubber"
      contains: "before_send|sentry_sdk\\.init"
    - path: "backend/fly.toml"
      provides: "Fly.io app config: region=jnb, always-on, /health check"
      contains: "primary_region.*jnb|min_machines_running"
    - path: ".pre-commit-config.yaml"
      provides: "Local gitleaks pre-commit hook"
      contains: "gitleaks"
    - path: ".gitleaks.toml"
      provides: "Allowlist for lockfiles + .planning + placeholder patterns"
      contains: "allowlist"
    - path: ".github/workflows/gitleaks.yml"
      provides: "CI gitleaks workflow blocking PRs with secrets"
      contains: "gitleaks/gitleaks-action"
    - path: ".github/workflows/frontend.yml"
      provides: "CI: lint + typecheck + build + size-limit gate at 180 KB"
      contains: "size-limit"
    - path: ".github/workflows/backend.yml"
      provides: "CI: ruff + pytest + docker build smoke"
      contains: "pytest"
    - path: "frontend/.size-limit.json"
      provides: "Bundle gate config: First Load JS <=180 KB gzipped per route"
      contains: "180"
    - path: ".env.example"
      provides: "Documented required env vars without secret values"
      contains: "MONGODB_URI|CLERK_SECRET_KEY"
  key_links:
    - from: "frontend/src/app/dashboard/page.tsx"
      to: "frontend/src/app/api/me/route.ts"
      via: "server-side fetch('/api/me') in App Router"
      pattern: "fetch.*api/me"
    - from: "frontend/src/app/api/me/route.ts"
      to: "backend Flask /me"
      via: "fetch with Authorization: Bearer <Clerk JWT> from getToken()"
      pattern: "Authorization.*Bearer"
    - from: "backend/app/middleware/auth.py"
      to: "Clerk JWKS (cached, networkless)"
      via: "clerk.authenticate_request(httpx_req, AuthenticateRequestOptions(authorized_parties=...))"
      pattern: "authenticate_request"
    - from: "backend/app/routes/me.py"
      to: "MongoDB users collection"
      via: "users.find_one({clerk_id: g.clerk_user_id})"
      pattern: "users\\.find_one"
    - from: "frontend/src/app/api/webhooks/clerk/route.ts"
      to: "backend Flask /webhooks/clerk"
      via: "svix-verified POST forwarded with x-clerk-verified: true header"
      pattern: "x-clerk-verified"
    - from: "Fly.io static egress IPv4"
      to: "MongoDB Atlas Network Access allowlist"
      via: "Atlas /32 entry; 0.0.0.0/0 removed from production"
      pattern: "Atlas Network Access -> IP Access List"
---

# Phase 1: Walking Skeleton — FitGH

## Phase Goal (User Story)

**As a** new FitGH user, **I want to** sign in via Clerk (email/password or Google) and see my email rendered on /dashboard from a record in MongoDB Atlas (fetched through Flask), **so that** I have proof the entire trust boundary — auth, session forwarding, networkless JWT verify, DB read, secret hygiene, deploy plumbing, observability, and bundle-size budget — works end-to-end before any feature work is built on top of it.

## Mode

**Vertical MVP + Walking Skeleton.** Each slice ships an independently verifiable, user-or-operator-observable outcome on top of the previous slice. No horizontal layering. The skeleton itself IS the slice for Phase 1; later phases (2–7) build vertical features on top of this skeleton without altering its architectural decisions.

## Out of Scope (encoded explicitly so subsequent phases don't re-litigate)

- Onboarding form, Mifflin-St Jeor TDEE math, weights collection, GDPR delete-account, AUTH-04, AUTH-05 → **Phase 2**.
- Ghana food table seed, `foods` collection, `/foods/search`, manual meal logging UI, multi-component `meals` schema, daily-total endpoint, "remaining kcal" pill, `mongodump` cron → **Phase 3**.
- LLM vision integration (`anthropic` SDK, Sonnet 4.6, prompt caching), `browser-image-compression`, `/vision/estimate`, component chips, inline correction, per-user 8/day cap, global $/day breaker, `user_corrections` collection, `OBS-03` cost alert → **Phase 4**.
- Rive `.riv` file, kcal ring animation, Recharts weight + weekly-kcal charts, goal-aware home, soft-streak — **Phase 5**. (Rive designer pipeline decision tracked as STATE.md blocker; not a Phase 1 task.)
- `exercises` seed, `/exercises/search` filters, WebP poster → tap-load WebM, `next-pwa`, IndexedDB offline cache, `LICENSES.md` → **Phase 6**.
- Lagos WebPageTest, real privacy policy, data-export endpoint, account-delete cascade refinement, health-claim copy audit, Anthropic spend cap, golden-set re-run → **Phase 7**.
- All v2 features (image history on R2, wearables, expanded catalogue, push notifications, friends, payments, localisation).

## Skeleton Invariants (the plan MUST encode all of these)

1. **Tailwind v4 (not v3) install path.** `@tailwindcss/postcss` + `@theme` in `globals.css`, NOT a `tailwind.config.js`. See Gotcha G1.
2. **Clerk Python SDK quirk:** `clerk-backend-api`'s `authenticate_request()` requires an `httpx.Request`, NOT Flask's `request`. The `@require_auth` wrapper constructs an httpx.Request explicitly. See Gotcha G5 + research §3.8.
3. **Sentry PII scrubbers present at commit 1**, not retrofitted (OBS-01). `before_send` drops email, image bytes, kcal totals from error context on both FE and BE.
4. **PyMongo singleton with `maxPoolSize=10`** from commit 1 (SEC-04). One `MongoClient` at module level; never inside route handlers.
5. **Flask CORS explicit origin allowlist** (SEC-03). `supports_credentials=False`; `allow_headers=['Content-Type', 'Authorization']`; origins from `CORS_ALLOWED_ORIGINS` env var.
6. **`.env*` in `.gitignore`** (already done) + `gitleaks` pre-commit installed BEFORE any other commit that could leak secrets — Slice 0 must finish before Slice C touches the rotated MongoDB password.
7. **`size-limit` budget = 180 KB** First Load JS gzipped on the dashboard route, enforced in CI from the first PR.
8. **Atlas least-priv user `fitgh-app` with `readWrite@fitgh` role**, NOT `atlasAdmin` (SEC-02).
9. **Static egress IPv4 pinned in Atlas allowlist; `0.0.0.0/0` removed from production** (DEPLOY-02). If $3.60/mo cost > $5/mo limit, halt and discuss before bypassing.
10. **Custom Clerk catch-all pages** (`app/sign-in/[[...sign-in]]/page.tsx`), NOT hosted UI. Keeps users on `fitgh.vercel.app` for clean Vercel Analytics attribution.

---

## Execution Context

@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md

## Context References

@.planning/PROJECT.md
@.planning/REQUIREMENTS.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/research/SUMMARY.md
@.planning/research/STACK.md
@.planning/research/ARCHITECTURE.md
@.planning/research/PITFALLS.md
@.planning/phases/01-walking-skeleton/SKELETON.md
@.planning/phases/01-walking-skeleton/01-RESEARCH.md

---

## Trust Boundaries (Threat Model)

| Boundary | Description |
|----------|-------------|
| Browser → Vercel Next.js | Clerk session cookie (httpOnly, Secure, SameSite=Lax) crosses this boundary; arbitrary input crosses on all routes. |
| Vercel Next.js → Flask (Fly.io) | Bearer JWT minted by `getToken()` from Clerk session; Authorization header forwarded; no cookies cross. |
| Clerk SaaS → Vercel `/api/webhooks/clerk` | Svix-signed webhook payloads; signature MUST verify before forwarding to Flask. |
| Vercel Next.js → Flask `/webhooks/clerk` | Internal trust hop after svix verify; uses `x-clerk-verified: true` header; Flask checks header but the real trust anchor is the svix verify in BFF. |
| Flask (Fly.io) → MongoDB Atlas | TLS PyMongo connection; only the Fly egress IPv4 is allowlisted in production; SCRAM auth with rotated password. |
| Flask → Clerk JWKS | One-time fetch + in-memory cache; networkless after first request via `clerk-backend-api`. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-01 | Spoofing | Flask `/me`, `/webhooks/clerk` | mitigate | `@require_auth` runs `clerk.authenticate_request()` on every `/me` request; webhook handler returns 400 if `x-clerk-verified` header absent AND Next.js BFF verifies svix signature before forwarding. |
| T-01-02 | Tampering | Clerk webhook payload | mitigate | Svix signature verification in `/api/webhooks/clerk/route.ts` before any DB write; 400 on signature failure. |
| T-01-03 | Repudiation | User actions | accept | Phase 1 has no audit-log requirement; revisit in Phase 7 for production. |
| T-01-04 | Information disclosure | Mongo connection string | mitigate | `.env*` in `.gitignore`; gitleaks pre-commit + CI; least-priv `readWrite@fitgh` user (not atlasAdmin); rotated password (SEC-02). |
| T-01-05 | Information disclosure | Sentry error context (email, PII) | mitigate | `before_send` PII scrubber on FE + BE drops `request.headers.authorization`, `user.email`, `extra.email` before send. |
| T-01-06 | Information disclosure | Atlas accepting 0.0.0.0/0 in production | mitigate | After Slice G ships, Slice H pins Fly egress IPv4 in Atlas Network Access and removes 0.0.0.0/0 from production allowlist. |
| T-01-07 | Denial of service | Flask `/me`, `/webhooks/clerk` | accept | Phase 1 has no rate limiting; Fly.io has DDoS protection at the platform level; Phase 4 adds Flask-Limiter for `/vision/estimate`. |
| T-01-08 | Denial of service | Mongo connection storm | mitigate | PyMongo singleton with `maxPoolSize=10` (SEC-04); never instantiate `MongoClient` per request. |
| T-01-09 | Elevation of privilege | Atlas admin via leaked creds | mitigate | `fitgh-app` user is `readWrite@fitgh` only; cannot create users, drop dbs, or read other databases. |
| T-01-10 | Elevation of privilege | Unverified `Authorization` header | mitigate | Flask `@require_auth` MUST verify via `clerk-backend-api`; reject any route reading `request.headers["X-User-Id"]` directly (no such code exists in Phase 1). |
| T-01-11 | Spoofing | CORS misconfig | mitigate | `flask-cors` with explicit `origins=[CORS_ALLOWED_ORIGINS env list]`; `supports_credentials=False`; no `*` origin. |
| T-01-12 | Tampering | size-limit bypass | mitigate | CI workflow on `main` branch protection requires size-limit + gitleaks + backend status checks to pass before merge. |

---

## Tasks

Tasks are atomic. Each has a single observable outcome. Slice 0 must complete first; Slices A and B may proceed in parallel after Slice 0; Slices C–J are sequential by design (each gates on the previous slice's verifiable outcome).

---

### Slice 0: Foundation (must precede all other slices)

This slice closes the STATE.md blocker around the exposed Atlas password, installs gitleaks BEFORE any other commit could leak the new password, and lays down the empty repo scaffold + CI workflow shells. No app code yet.

#### WS-0.1 — Rotate exposed MongoDB Atlas password [BLOCKER, USER ACTION]

- **Slice:** 0
- **Goal:** Eliminate the exposed-in-chat password risk per PITFALLS M-5 and STATE.md blocker; create a least-priv `fitgh-app` Atlas user.
- **Files:** (none — Atlas dashboard work)
- **Deps:** —
- **Acceptance:**
  - User opens Atlas Dashboard → Database Access → existing user → Edit → Edit Password; sets a new ≥32-char random password (use 1Password or `openssl rand -base64 32`).
  - User creates a NEW Database User named `fitgh-app` with role `readWrite@fitgh` ONLY (NOT atlasAdmin, NOT readWriteAnyDatabase).
  - New connection string `mongodb+srv://fitgh-app:<password>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority&appName=fitgh-api` recorded in the user's password manager.
  - The OLD password is invalidated/rotated (cannot be reused).
  - User confirms in-chat with a redacted snippet of the new URI (showing `mongodb+srv://fitgh-app:***@cluster0...`) — DO NOT paste the actual password into chat.
- **REQ-IDs:** SEC-02
- **Commit message:** (no commit — user action; recorded in STATE.md after completion)
- **Estimated complexity:** S
- **Type:** `checkpoint:human-action`
- **Verify (automated):** N/A — this is the one truly-manual step. After user confirms, Slice C's `/health` check is the automated proof the new credential works.

#### WS-0.2 — Verify Atlas cluster tier and 2026 billing model [USER ACTION]

- **Slice:** 0
- **Goal:** Close Open Question #1 from RESEARCH (is the cluster truly M0 or has it been promoted?); confirm billing won't surprise when we pin the egress IP.
- **Files:** (none — Atlas dashboard + Fly billing page work)
- **Deps:** WS-0.1
- **Acceptance:**
  - User confirms Atlas cluster tier (M0/M2/M10) and records it in STATE.md blockers section.
  - User confirms Fly.io billing is configured (a card is on file) — required for `fly ips allocate-egress` even on Hobby trial.
  - If cluster tier is not M0, user updates the connection-limit assumption (SEC-04 still uses `maxPoolSize=10` regardless; safe default).
- **REQ-IDs:** SEC-04 (informational)
- **Commit message:** (no commit — user action)
- **Estimated complexity:** S
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** N/A — operator confirmation only.

#### WS-0.3 — Repo scaffold: .gitignore, .env.example, .nvmrc, README

- **Slice:** 0
- **Goal:** Create the minimal repo file set that all subsequent slices depend on; lock the .env-exclusion at commit 1.
- **Files:** `.gitignore`, `.env.example`, `.nvmrc`, `README.md`
- **Deps:** —
- **Acceptance:**
  - `.gitignore` contains: `.env`, `.env.local`, `.env.*.local`, `node_modules/`, `.next/`, `dist/`, `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`, `*.log`, `frontend/.next/`, `backend/.venv/`.
  - `git check-ignore .env.local` returns exit 0 (confirming `.env.local` is ignored).
  - `.env.example` lists EVERY env var required by the project WITHOUT values: `MONGODB_URI`, `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_WEBHOOK_SECRET`, `CLERK_AUTHORIZED_PARTIES`, `BACKEND_URL`, `CORS_ALLOWED_ORIGINS`, `SENTRY_DSN_BACKEND`, `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_AUTH_TOKEN`. Placeholder format `KEY=` (empty) or `KEY=<from-clerk-dashboard>`.
  - `.nvmrc` contains `20` (Node 20 LTS).
  - `README.md` has: project name, one-line description, quick-start (clone → `cp .env.example .env.local` → `pnpm install` → `pnpm dev`), and a "Phase 1 = Walking Skeleton" callout linking to `.planning/phases/01-walking-skeleton/SKELETON.md`.
- **REQ-IDs:** SEC-01
- **Commit message:** `chore(repo): initial scaffold (gitignore, env.example, nvmrc, README)`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `git check-ignore .env.local && test -f .env.example && test -f .nvmrc && grep -q 'MONGODB_URI' .env.example`

#### WS-0.4 — Install gitleaks pre-commit + .gitleaks.toml allowlist

- **Slice:** 0
- **Goal:** Block ANY future commit containing secrets (Mongo URIs, Clerk keys, Sentry DSNs, generic high-entropy tokens) at the local hook level. Per Gotcha G9, the allowlist pre-excludes lockfiles, `.planning/`, and `.env.example` placeholder patterns.
- **Files:** `.pre-commit-config.yaml`, `.gitleaks.toml`
- **Deps:** WS-0.3
- **Acceptance:**
  - `.pre-commit-config.yaml` references `gitleaks/gitleaks` repo at v8.21+ with hook `id: gitleaks`.
  - `.gitleaks.toml` `[extend]` from default rules; `[allowlist]` excludes paths: `^pnpm-lock\.yaml$`, `^backend/requirements\.txt$`, `^backend/requirements-dev\.txt$`, `^\.planning/`, `^\.env\.example$`. Allowlist also excludes regex `pk_test_xxx`, `sk_test_xxx`, `whsec_xxx`, `<from-clerk-dashboard>`.
  - Developer runs `pre-commit install` locally; `pre-commit run --all-files` on clean tree returns 0 findings.
  - Deliberate-leak smoke test: developer creates a scratch file containing `mongodb+srv://user:realpassword@cluster0.pcd3g.mongodb.net/test`, stages it, attempts to commit → commit is BLOCKED by gitleaks with a clear error. Developer reverts the scratch file. Record success in commit message body.
- **REQ-IDs:** SEC-01
- **Commit message:** `chore(security): install gitleaks pre-commit hook + allowlist`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `pre-commit run gitleaks --all-files` exits 0 on the committed tree; manual smoke test in acceptance.

#### WS-0.5 — Create CI workflow shells (frontend / backend / gitleaks)

- **Slice:** 0
- **Goal:** Land the three GitHub Actions workflow files with skeleton jobs so subsequent slices fail fast in CI as they add real content. Workflows trigger on push + pull_request to `main`.
- **Files:** `.github/workflows/frontend.yml`, `.github/workflows/backend.yml`, `.github/workflows/gitleaks.yml`
- **Deps:** WS-0.3
- **Acceptance:**
  - `frontend.yml`: jobs `lint-typecheck-build` + `size-limit` (the size-limit job is `continue-on-error: true` until Slice A wires it real, then flipped to false). Uses `pnpm/action-setup@v4`, `actions/setup-node@v4` with `node-version-file: .nvmrc`. `working-directory: frontend`.
  - `backend.yml`: jobs `lint-test` (ruff + pytest) + `docker-build-smoke`. Uses `actions/setup-python@v5` with `python-version: 3.12`. `working-directory: backend`. Each job is `continue-on-error: true` until Slice B/D wires the real targets, then flipped.
  - `gitleaks.yml`: single job `secret-scan` running `gitleaks/gitleaks-action@v2` against the full repo with `fetch-depth: 0`. NOT `continue-on-error` — fail PRs from day 1.
  - All three workflows pass on the first push (because the jobs are still stubs).
- **REQ-IDs:** PERF-01, SEC-01
- **Commit message:** `ci: scaffold frontend/backend/gitleaks workflows`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** Push the commit to a branch; GitHub Actions runs all three workflows green. `gh run list --branch <branch> --limit 3` shows three successful workflows.

---

### Slice A: Frontend skeleton (Next.js 15 + Tailwind v4 + shadcn/ui + size-limit gate proven)

This slice scaffolds the frontend and proves the size-limit CI gate works against a real `next build`. No Clerk yet; just the `/dashboard` route renders a "loading…" placeholder.

#### WS-A.1 — Scaffold Next.js 15.2.4 with Tailwind v4 + pnpm

- **Slice:** A
- **Goal:** Get a working `pnpm dev` server with Tailwind v4 (CSS-first, NOT v3 with `tailwind.config.js`).
- **Files:** `frontend/package.json`, `frontend/next.config.js`, `frontend/postcss.config.mjs`, `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/app/globals.css`, `frontend/tsconfig.json`, `frontend/.eslintrc.json` (or flat config), `frontend/.gitignore`
- **Deps:** WS-0.3, WS-0.4 (pre-commit must be installed before this commit lands)
- **Acceptance:**
  - Run from repo root: `mkdir frontend && cd frontend && pnpm create next-app@latest . --typescript --tailwind --app --eslint --src-dir --import-alias "@/*" --use-pnpm --turbopack`. Accept default for any prompts that come up.
  - `frontend/package.json` pins `next: "15.2.4"` (downgrade if create-next-app installed newer; `pnpm add next@15.2.4 -E`).
  - `frontend/components.json` does NOT yet exist (shadcn comes next).
  - Verify v4 setup: `frontend/postcss.config.mjs` contains `'@tailwindcss/postcss': {}` (NOT `tailwindcss: {}`). NO `tailwind.config.js` file exists. `globals.css` contains `@import "tailwindcss"` (v4 syntax).
  - `pnpm install` succeeds; `pnpm dev` starts on port 3000; visiting `http://localhost:3000` shows the default Next.js landing page.
  - `pnpm build` succeeds without errors.
- **REQ-IDs:** DEPLOY-01, PERF-01
- **Commit message:** `feat(frontend): scaffold Next.js 15.2.4 + Tailwind v4 with pnpm`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `cd frontend && pnpm build` exits 0; `grep -q '"next": "15.2.4"' frontend/package.json`; `test ! -f frontend/tailwind.config.js` (must not exist for v4).

#### WS-A.2 — Add shadcn/ui (button, card, avatar, sonner) + verify v4 wiring

- **Slice:** A
- **Goal:** Install the shadcn primitives we'll use across all phases; confirm v4-compatible setup per Gotcha G1.
- **Files:** `frontend/components.json`, `frontend/src/components/ui/button.tsx`, `frontend/src/components/ui/card.tsx`, `frontend/src/components/ui/avatar.tsx`, `frontend/src/components/ui/sonner.tsx`, `frontend/src/lib/utils.ts`, `frontend/src/app/globals.css` (theme tokens added)
- **Deps:** WS-A.1
- **Acceptance:**
  - Run `cd frontend && pnpm dlx shadcn@latest init` — accept default style ("New York" or "Default"), base color "slate", CSS variables = yes.
  - Verify `components.json` shows `"tailwind": { "config": "" }` (empty string, NOT a path) — this is the v4 marker per Gotcha G1.
  - `pnpm dlx shadcn@latest add button card avatar sonner` — adds the four components into `frontend/src/components/ui/`.
  - Replace `frontend/src/app/page.tsx` with a minimal page rendering `<Button>Test</Button>` and `<Card>Hello FitGH</Card>`; verify `pnpm dev` shows them styled correctly with dark mode toggle working via `prefers-color-scheme`.
- **REQ-IDs:** DEPLOY-01
- **Commit message:** `feat(frontend): add shadcn/ui primitives (button, card, avatar, sonner)`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd frontend && pnpm build` exits 0; `grep -q '"config": ""' frontend/components.json`; `test -f frontend/src/components/ui/button.tsx`.

#### WS-A.3 — Author placeholder /dashboard route + base layout

- **Slice:** A
- **Goal:** Create the `/dashboard` route as a server component that will eventually fetch `/api/me`; for now it renders a "loading…" placeholder. This is the bundle that size-limit will guard.
- **Files:** `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/layout.tsx` (update with proper metadata)
- **Deps:** WS-A.2
- **Acceptance:**
  - `frontend/src/app/dashboard/page.tsx` is a server component (no `"use client"`). Renders `<Card><h1>FitGH Dashboard</h1><p>Loading your account…</p><Avatar /* placeholder */ /></Card>`. Avatar is a static SVG placeholder (no Rive runtime yet).
  - `frontend/src/app/layout.tsx` sets `<html lang="en">`, `<body>`, and includes a font setup via `next/font/google` for Inter (subset: latin only) to control caching.
  - `pnpm build` reports the `/dashboard` route's First Load JS in the table. Capture the number for Slice WS-A.5's size-limit tuning.
- **REQ-IDs:** DEPLOY-01
- **Commit message:** `feat(frontend): add placeholder /dashboard route + base layout with Inter font`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd frontend && pnpm build 2>&1 | grep -E '/dashboard.*[0-9]+\s*kB'` — captures the printed First Load JS.

#### WS-A.4 — Install size-limit + author .size-limit.json with 180 KB budget

- **Slice:** A
- **Goal:** Set up the bundle gate that enforces PERF-01 (First Load JS ≤ 180 KB gzipped). Per Gotcha G8, the glob is an approximation; we'll tune after the first build but lock the budget at 180 KB.
- **Files:** `frontend/package.json` (devDep + scripts), `frontend/.size-limit.json`
- **Deps:** WS-A.3
- **Acceptance:**
  - `cd frontend && pnpm add -D size-limit @size-limit/preset-app`.
  - `frontend/.size-limit.json` contains a `/dashboard` entry: `{ "name": "Dashboard route", "path": [".next/static/chunks/app/dashboard/**/*.js", ".next/static/chunks/main-*.js", ".next/static/chunks/framework-*.js"], "limit": "180 kB" }` (note: size-limit uses gzipped by default with preset-app).
  - `frontend/package.json` adds `"size": "size-limit"` script.
  - `cd frontend && pnpm build && pnpm size` runs to completion. If it reports the dashboard route's bundle EXCEEDS 180 KB, this is a blocker — open WS-A.5 to investigate (likely caused by accidental client component or eager Rive import).
  - If it reports ≤ 180 KB, capture the exact number in the commit body for the next slice.
- **REQ-IDs:** PERF-01
- **Commit message:** `feat(frontend): add size-limit bundle gate at 180 KB First Load JS`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd frontend && pnpm build && pnpm size` exits 0 AND prints `Size limit: 180 kB` with current size below it.

#### WS-A.5 — Wire size-limit into CI; deliberate-bloat smoke test

- **Slice:** A
- **Goal:** Flip the size-limit job in `frontend.yml` from `continue-on-error: true` to false; prove the gate fails a PR by deliberately bloating the bundle past 180 KB and asserting the build fails.
- **Files:** `.github/workflows/frontend.yml`
- **Deps:** WS-A.4
- **Acceptance:**
  - Update `.github/workflows/frontend.yml`: the `size-limit` job runs `cd frontend && pnpm install --frozen-lockfile && pnpm build && pnpm size`. `continue-on-error: false`.
  - Also add `andresz1/size-limit-action@v1` as the actual gating step with `directory: frontend` and `package_manager: pnpm` — it posts a comment on the PR with the bundle delta.
  - **Smoke test (on a throwaway branch, NOT merged):** open a PR that adds `import 'three'` and `pnpm add three` (Three.js is ~600 KB). Confirm the `size-limit` CI job fails with "Size limit has been exceeded for dashboard". Close the smoke-test PR without merging.
  - Record the smoke-test PR URL in the commit body for traceability.
- **REQ-IDs:** PERF-01
- **Commit message:** `ci(frontend): enforce size-limit 180 KB gate (smoke-tested with Three.js bloat)`
- **Estimated complexity:** M
- **Type:** `checkpoint:human-verify` (smoke-test PR requires human to push the bloat branch and verify failure)
- **Verify (automated):** `gh run list --workflow frontend.yml --branch <smoke-branch> --limit 1` shows `failure`; `gh run list --workflow frontend.yml --branch main --limit 1` shows `success`.

---

### Slice B: Backend skeleton (Flask 3.1 + Sentry init with scrubber + PyMongo singleton stub)

This slice scaffolds Flask with the production patterns from commit 1 (singleton MongoClient, Sentry with PII scrubber, CORS allowlist) but does NOT yet connect to real Mongo. `/health` returns `{ok:true, mongo:"stubbed"}` until Slice C wires the real connection. This decouples Slice B (can ship without Atlas) from the blocker on WS-0.1.

#### WS-B.1 — Backend project layout + requirements.txt

- **Slice:** B
- **Goal:** Create the `/backend` directory with locked package versions and a Python 3.12 venv.
- **Files:** `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/.python-version`, `backend/.gitignore`
- **Deps:** WS-0.3 (gitignore root ignores `backend/.venv/`)
- **Acceptance:**
  - `backend/.python-version` contains `3.12`.
  - `backend/requirements.txt` pins (matching research §Standard Stack verified versions):
    ```
    flask>=3.1,<4
    gunicorn>=25.1
    flask-cors>=5.0
    pymongo>=4.13,<5
    pydantic>=2.9,<3
    clerk-backend-api>=5.0.6
    svix>=1.30
    python-dotenv>=1.0
    sentry-sdk[flask]>=2.53
    httpx>=0.27
    ```
  - `backend/requirements-dev.txt` adds: `pytest>=8.0`, `pytest-cov>=5.0`, `ruff>=0.5`, `respx>=0.21` (for mocking httpx in Clerk tests), `mongomock>=4.1` (for mocking PyMongo in unit tests).
  - `cd backend && python -m venv .venv && .venv\Scripts\activate.ps1 && pip install -r requirements.txt -r requirements-dev.txt` succeeds (Windows shell per env note).
  - `backend/.gitignore` (or root) excludes `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`.
- **REQ-IDs:** —
- **Commit message:** `feat(backend): scaffold Python 3.12 venv + pinned requirements`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd backend && python -c "import flask, pymongo, pydantic, clerk_backend_api, sentry_sdk, svix; print('ok')"` prints `ok`.

#### WS-B.2 — Flask app factory + config + extensions (Sentry with PII scrubber)

- **Slice:** B
- **Goal:** Create the Flask factory pattern with Sentry initialised at construction time (NOT retrofitted later). The `before_send` scrubber drops PII from error context per OBS-01.
- **Files:** `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/extensions.py`
- **Deps:** WS-B.1
- **Acceptance:**
  - `backend/app/config.py` reads from env: `MONGODB_URI`, `CLERK_SECRET_KEY`, `CLERK_AUTHORIZED_PARTIES` (csv → list), `CORS_ALLOWED_ORIGINS` (csv → list), `SENTRY_DSN_BACKEND`, `FLASK_ENV` (default `production`). Raises on startup if any required var is missing (fail-loud, NOT fail-on-first-request).
  - `backend/app/extensions.py` has `init_sentry(app)` that calls `sentry_sdk.init(dsn=..., integrations=[FlaskIntegration(), PyMongoIntegration()], send_default_pii=False, before_send=scrub)`. The `scrub` function drops keys: `request.headers.authorization`, `user.email`, `user.username`, `extra.email`, `extra.user_id`, `breadcrumbs.*.data.image`, `breadcrumbs.*.data.kcal`. Returns the event with those keys removed; returns `None` if the event itself looks like a webhook payload (which may contain email).
  - `backend/app/__init__.py` has `create_app()` returning a `Flask` instance with: Sentry initialised first, `flask-cors` configured with explicit `origins=config.CORS_ALLOWED_ORIGINS`, `supports_credentials=False`, `allow_headers=['Content-Type', 'Authorization']`. Blueprints registered (health, me, webhooks) — empty Blueprints OK for now; routes come next.
  - `cd backend && FLASK_APP=app:create_app flask routes` lists at least `/health` (which will be added in WS-B.3).
- **REQ-IDs:** SEC-03, OBS-01
- **Commit message:** `feat(backend): Flask app factory with Sentry PII scrubber + CORS allowlist`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `cd backend && pytest tests/test_sentry_scrubber.py -x` (test file created in WS-B.5).

#### WS-B.3 — PyMongo singleton (db.py) + /health endpoint returning stubbed status

- **Slice:** B
- **Goal:** Module-level `MongoClient` singleton with `maxPoolSize=10` (SEC-04) and a `/health` endpoint. At this slice the DB isn't really connected yet (no Atlas creds), so `/health` reports `mongo: "stubbed"`. Slice C will swap it to a real ping.
- **Files:** `backend/app/db.py`, `backend/app/routes/health.py`, `backend/app/__init__.py` (register health blueprint)
- **Deps:** WS-B.2
- **Acceptance:**
  - `backend/app/db.py` has, at module level:
    ```python
    from pymongo import MongoClient
    import os
    _mongo_uri = os.environ.get("MONGODB_URI")
    client = MongoClient(_mongo_uri, maxPoolSize=10, tls=True, serverSelectionTimeoutMS=5000) if _mongo_uri else None
    db = client["fitgh"] if client else None
    users = db["users"] if db is not None else None
    ```
    The `if _mongo_uri else None` shim allows the module to import without crashing when MONGODB_URI is not set (Slice B is pre-Atlas). Slice C will remove the shim.
  - `backend/app/routes/health.py` exposes `GET /health`. If `client is None`: return `{"ok": True, "mongo": "stubbed"}`. Otherwise: `client.admin.command("ping")` (1-second timeout) and return `{"ok": True, "mongo": "connected"}` on success, `{"ok": False, "mongo": "error", "detail": str(e)}` on failure.
  - `cd backend && FLASK_APP=app:create_app flask run` starts on port 8000; `curl http://localhost:8000/health` returns `{"ok": true, "mongo": "stubbed"}` (because MONGODB_URI not yet set).
- **REQ-IDs:** SEC-04
- **Commit message:** `feat(backend): PyMongo singleton (maxPoolSize=10) + /health stub`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd backend && pytest tests/test_health.py -x` (test created in WS-B.5) AND `curl http://localhost:8000/health` returns 200 with `"ok": true`.

#### WS-B.4 — Author middleware/auth.py (require_auth decorator) + empty /me + /webhooks/clerk stubs

- **Slice:** B
- **Goal:** Lay down the Clerk JWT verify wrapper EXACTLY as research §3.8 specifies — the httpx.Request quirk (Gotcha G5) is encoded from commit 1, not discovered in Slice E.
- **Files:** `backend/app/middleware/auth.py`, `backend/app/middleware/__init__.py`, `backend/app/routes/me.py`, `backend/app/routes/webhooks.py`, `backend/app/__init__.py` (register both blueprints)
- **Deps:** WS-B.3
- **Acceptance:**
  - `backend/app/middleware/auth.py` exactly matches research §3.8: imports `httpx`, `from flask import request, g, jsonify`, `from clerk_backend_api import Clerk`, `from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions`. Module-level `_clerk = Clerk(bearer_auth=os.environ["CLERK_SECRET_KEY"])`. The `require_auth` decorator constructs `httpx.Request(method=request.method, url=str(request.url), headers=dict(request.headers))` and calls `_clerk.authenticate_request(httpx_req, AuthenticateRequestOptions(authorized_parties=_authorized_parties))`. Returns 401 with `{"error": "unauthorized", "reason": state.reason}` if not signed in; otherwise sets `g.clerk_user_id = state.payload.get("sub")` and calls the wrapped function.
  - `backend/app/routes/me.py` has `@bp.get("/me") @require_auth def get_me(): user = users.find_one({"clerk_id": g.clerk_user_id}); return ...` (return 404 if user not found, 200 with `{"email": user["email"]}` if found). For Slice B (no real Mongo), the route returns 503 with `{"error": "db_not_configured"}` when `users is None` — gated behind the import. Slice C flips it.
  - `backend/app/routes/webhooks.py` has the route from research §3.9 (svix-pre-verified by Next.js BFF; checks `x-clerk-verified: true` header). For Slice B, the route is reachable but writes are gated behind `users is not None`; otherwise returns 503.
  - Module imports succeed even when `CLERK_SECRET_KEY` is unset (deferred check OR set a dev stub in tests).
- **REQ-IDs:** AUTH-06, SEC-04
- **Commit message:** `feat(backend): require_auth decorator + /me + /webhooks/clerk stubs`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `cd backend && pytest tests/test_me.py tests/test_webhooks.py -x` (tests created in WS-B.5).

#### WS-B.5 — Wave 0 tests: health, me, webhooks, cors, db, sentry scrubber

- **Slice:** B
- **Goal:** Write the tests that Slices B-D will be verified against. These tests are the executable spec; per Nyquist, every `<verify>` in this plan must have an automated command, and pytest is that command.
- **Files:** `backend/tests/__init__.py`, `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_me.py`, `backend/tests/test_webhooks.py`, `backend/tests/test_cors.py`, `backend/tests/test_db.py`, `backend/tests/test_sentry_scrubber.py`, `backend/pytest.ini`
- **Deps:** WS-B.4
- **Acceptance:**
  - `backend/pytest.ini` sets `testpaths = tests`, `addopts = -ra --strict-markers`.
  - `tests/conftest.py` provides a `client` fixture wrapping `create_app()` with env vars stubbed (CLERK_SECRET_KEY=`sk_test_stub`, CLERK_AUTHORIZED_PARTIES=`http://localhost:3000`, CORS_ALLOWED_ORIGINS=`http://localhost:3000`, MONGODB_URI unset → stubbed mode).
  - `test_health.py`: asserts `GET /health` returns 200 with `{"ok": True, "mongo": "stubbed"}` when MONGODB_URI is unset; asserts 200 with `mongo: "connected"` when patched with a mock `MongoClient` whose `.admin.command("ping")` succeeds.
  - `test_me.py`: (a) asserts `GET /me` with NO Authorization header returns 401; (b) asserts `GET /me` with a fake `Authorization: Bearer xxx` returns 401 (clerk-backend-api rejects the bad JWT — use `respx` to mock the JWKS endpoint with a known key, then construct a valid JWT signed with that key for the 200 test); (c) asserts `GET /me` with a VALID JWT but no matching user in Mongo returns 404 (when Mongo is mocked); (d) asserts 200 with `{"email": "user@example.com"}` when valid JWT + user exists.
  - `test_webhooks.py`: asserts `POST /webhooks/clerk` WITHOUT `x-clerk-verified: true` returns 400; with header but invalid JSON returns 400; with valid `user.created` event upserts a user record (using mongomock).
  - `test_cors.py`: asserts an OPTIONS preflight from `Origin: http://localhost:3000` returns the correct `Access-Control-Allow-Origin` header (echoes the allowed origin, NOT `*`); asserts an OPTIONS preflight from `Origin: http://evil.example.com` returns 403 or omits the ACAO header.
  - `test_db.py`: asserts `db.py` exports a `MongoClient` configured with `maxPoolSize=10` (use `client.options.pool_options.max_pool_size == 10`) and `tls=True`.
  - `test_sentry_scrubber.py`: invokes the `scrub` function from `extensions.py` with a synthetic event containing `{"request": {"headers": {"authorization": "Bearer xxx"}}, "user": {"email": "u@example.com"}}` and asserts the returned event has those keys removed.
  - `cd backend && pytest -x` runs all six tests; all pass.
- **REQ-IDs:** AUTH-06, SEC-03, SEC-04, OBS-01
- **Commit message:** `test(backend): Wave 0 tests for health, me, webhooks, cors, db, sentry scrubber`
- **Estimated complexity:** L
- **Type:** `auto` `tdd="true"`
- **Verify (automated):** `cd backend && pytest -x` exits 0; `pytest --collect-only` shows ≥ 12 tests collected.

#### WS-B.6 — Wire backend.yml CI: ruff + pytest + docker build smoke

- **Slice:** B
- **Goal:** Flip backend.yml jobs from `continue-on-error: true` to false; prove tests run green in CI.
- **Files:** `.github/workflows/backend.yml`, `backend/pyproject.toml` (ruff config), `backend/Dockerfile` (will be filled in Slice G but a minimal one for the smoke job lands here)
- **Deps:** WS-B.5
- **Acceptance:**
  - `backend/pyproject.toml` has a `[tool.ruff]` section with `line-length = 100`, `target-version = "py312"`, and a select of `["E", "F", "I", "B", "UP"]`.
  - `.github/workflows/backend.yml` `lint-test` job runs `cd backend && pip install -r requirements.txt -r requirements-dev.txt && ruff check . && pytest -x`. `continue-on-error: false`.
  - `docker-build-smoke` job runs `cd backend && docker build -t fitgh-api:smoke .` — uses a minimal Dockerfile (Slice G replaces it with the real one). For this slice, the Dockerfile is the bare minimum: `FROM python:3.12-slim`, install requirements, copy app, default command runs gunicorn. `continue-on-error: false`.
  - Push to a feature branch; both jobs run green.
- **REQ-IDs:** —
- **Commit message:** `ci(backend): enforce ruff + pytest + docker build smoke`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `gh run list --workflow backend.yml --branch <branch> --limit 1` shows `success`.

---

### Slice C: MongoDB Atlas connection (real /health connected)

This slice flips `/health` from `mongo: "stubbed"` to `mongo: "connected"` by setting `MONGODB_URI` locally using the rotated password from WS-0.1. Atlas still has dev IP allowlist (or `0.0.0.0/0`); Slice H tightens this to the Fly egress IP.

#### WS-C.1 — Set MONGODB_URI locally (developer workstation .env) + verify /health connected

- **Slice:** C
- **Goal:** Use the new rotated credentials from WS-0.1 to connect Flask to Atlas; `/health` returns `mongo: "connected"` from the developer's machine.
- **Files:** (none committed — `.env.local` is gitignored)
- **Deps:** WS-0.1, WS-B.3
- **Acceptance:**
  - Developer creates `backend/.env.local` (or `backend/.env`) with `MONGODB_URI=mongodb+srv://fitgh-app:<rotated-password>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority&appName=fitgh-api`. Confirm `git status` does NOT show this file as untracked (it's gitignored).
  - Developer adds Atlas dev allowlist entry: their current IPv4 (Atlas → Network Access → "Add Current IP Address"). Confirm 0.0.0.0/0 IS NOT in the dev allowlist either (use only the dev IP; Slice H locks down production).
  - Run `cd backend && python -m flask --app app:create_app run -p 8000`. `curl http://localhost:8000/health` returns `{"ok": true, "mongo": "connected"}`.
  - Run `cd backend && pytest tests/test_health.py -x` — passes (the stubbed test still passes because the mock fixture is independent).
- **REQ-IDs:** SEC-02, SEC-04
- **Commit message:** (no commit — env values are not committed)
- **Estimated complexity:** S
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** `curl http://localhost:8000/health | grep -q '"mongo": "connected"'`.

#### WS-C.2 — Remove db.py shim: MongoClient is required, no None fallback

- **Slice:** C
- **Goal:** Now that Mongo is real, remove the `if _mongo_uri else None` shim in `db.py`; missing MONGODB_URI must fail loudly on app startup.
- **Files:** `backend/app/db.py`, `backend/tests/conftest.py` (update fixture to set MONGODB_URI to a mongomock-backed URI), `backend/tests/test_db.py` (update to assert startup raises on missing URI)
- **Deps:** WS-C.1
- **Acceptance:**
  - `backend/app/db.py` at module import: `MONGODB_URI = os.environ["MONGODB_URI"]` (raises KeyError if missing). `client = MongoClient(MONGODB_URI, maxPoolSize=10, tls=True, serverSelectionTimeoutMS=5000)`. `db = client["fitgh"]`. `users = db["users"]`.
  - `tests/conftest.py` sets `MONGODB_URI` via `monkeypatch.setenv` BEFORE the app is imported in the fixture; uses a mongomock URI (`mongodb://localhost:27017/fitgh-test`) or `mongomock` patching.
  - `test_db.py` adds a test asserting `ImportError` or `KeyError` raised when MONGODB_URI is absent at module load (use `pytest.raises` with `monkeypatch.delenv("MONGODB_URI", raising=False)` and `importlib.reload(db)`).
  - `cd backend && pytest -x` passes all tests.
- **REQ-IDs:** SEC-04
- **Commit message:** `refactor(backend): require MONGODB_URI at module import (no None fallback)`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd backend && pytest -x` exits 0.

---

### Slice D: Clerk frontend integration (ClerkProvider, middleware, sign-in/up, sign-out)

This slice wires Clerk on the frontend ONLY. The user can sign up, sign in, sign out — but `/dashboard` is still a placeholder showing the Clerk user object directly (no Flask call yet). Slice E adds the trust boundary to Flask.

#### WS-D.1 — Configure Clerk SaaS (Dev + Prod instances) [USER ACTION]

- **Slice:** D
- **Goal:** Create the two Clerk instances and configure them per research §3.10. This is dashboard work; Claude can't do it via CLI.
- **Files:** (none committed)
- **Deps:** —
- **Acceptance:**
  - User creates Clerk Development instance named "FitGH" — captures `pk_test_...` and `sk_test_...`.
  - User creates Clerk Production instance named "FitGH" — captures `pk_live_...` and `sk_live_...` (production keys won't be used until WS-I.2 Vercel deploy).
  - In BOTH instances: enable Email/Password + Google OAuth; leave all other providers OFF.
  - In BOTH: set Paths = `/sign-in`, `/sign-up`, after-sign-in = `/dashboard`, after-sign-up = `/dashboard`.
  - In Dev: add Domain `http://localhost:3000`. In Prod: add Domain `https://fitgh.vercel.app` (the URL Vercel will assign in Slice I).
  - User does NOT yet configure the Webhook endpoint — that happens in WS-F.1 after the webhook route is deployed.
  - User stores `pk_test_`, `sk_test_`, `pk_live_`, `sk_live_` in a password manager.
- **REQ-IDs:** AUTH-01, AUTH-02, AUTH-03
- **Commit message:** (no commit — dashboard work)
- **Estimated complexity:** M
- **Type:** `checkpoint:human-action`
- **Verify (automated):** N/A — operator confirmation in chat that all five Clerk dashboard items are configured.

#### WS-D.2 — Install @clerk/nextjs + add middleware.ts + wrap layout in ClerkProvider

- **Slice:** D
- **Goal:** Wire Clerk into the Next.js app: middleware protects routes, `<ClerkProvider>` injects context, env vars are loaded from `.env.local`.
- **Files:** `frontend/package.json`, `frontend/middleware.ts`, `frontend/src/app/layout.tsx`, `frontend/.env.local.example` (Phase 1 convention: a per-app example)
- **Deps:** WS-A.3, WS-D.1
- **Acceptance:**
  - `cd frontend && pnpm add @clerk/nextjs` (research §Core Frontend says ^6.x; verify on install — research §3 says STACK.md "5.x" is stale, "^6" is latest May 2026).
  - `frontend/.env.local.example` documents `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx`, `CLERK_SECRET_KEY=sk_test_xxx`, `CLERK_WEBHOOK_SECRET=<set-after-webhook-configured>`, `BACKEND_URL=http://localhost:8000` (note: top-level `.env.example` already has these; this is the frontend-specific subset for convenience).
  - Developer creates `frontend/.env.local` with `pk_test_` and `sk_test_` from WS-D.1 (gitignored).
  - `frontend/middleware.ts` exports `clerkMiddleware()` with `createRouteMatcher` distinguishing public routes (`'/sign-in(.*)'`, `'/sign-up(.*)'`, `'/api/webhooks/clerk'`) from protected (everything else, which calls `auth.protect()`). Config has `matcher: ['/((?!_next|[^?]*\\.[a-z]+).*)', '/(api|trpc)(.*)']`.
  - `frontend/src/app/layout.tsx` wraps `<body>` content in `<ClerkProvider>{children}</ClerkProvider>`; imports `ClerkProvider` from `@clerk/nextjs`.
  - `pnpm dev` starts; visiting `http://localhost:3000` (now requires sign-in via middleware) redirects to `/sign-in` — but `/sign-in` page doesn't exist yet, so a 404 is expected. WS-D.3 fixes this.
- **REQ-IDs:** AUTH-01, AUTH-02
- **Commit message:** `feat(frontend): add @clerk/nextjs middleware + ClerkProvider`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `cd frontend && pnpm build` succeeds; `curl http://localhost:3000/` returns a redirect to `/sign-in` (302 with Location header).

#### WS-D.3 — Custom sign-in / sign-up catch-all pages

- **Slice:** D
- **Goal:** Author the custom Clerk pages (per research §3 Alternatives Considered — custom catch-all, NOT hosted UI).
- **Files:** `frontend/src/app/sign-in/[[...sign-in]]/page.tsx`, `frontend/src/app/sign-up/[[...sign-up]]/page.tsx`
- **Deps:** WS-D.2
- **Acceptance:**
  - `sign-in/[[...sign-in]]/page.tsx` exports a server component rendering `<SignIn />` from `@clerk/nextjs` centered on the page with `min-h-screen flex items-center justify-center`.
  - `sign-up/[[...sign-up]]/page.tsx` does the same with `<SignUp />`.
  - Both are server components (no `"use client"`); Clerk's `<SignIn />` / `<SignUp />` are themselves client components imported from the package.
  - `pnpm dev`; visit `http://localhost:3000/` → redirected to `/sign-in` → Clerk-rendered form appears with Google + email options.
  - Sign up with a real email (yours: francisyiryel@gmail.com OR a throwaway). Verify the email confirmation flow. After confirming, you land on `/dashboard` (placeholder from WS-A.3) — and you ARE signed in (the Clerk user object is in scope).
- **REQ-IDs:** AUTH-01, AUTH-02
- **Commit message:** `feat(frontend): add custom Clerk sign-in / sign-up catch-all pages`
- **Estimated complexity:** S
- **Type:** `checkpoint:human-verify` (requires a real Clerk sign-up to confirm flow)
- **Verify (automated):** `cd frontend && pnpm build` succeeds AND user confirms sign-up flow lands on /dashboard.

#### WS-D.4 — Add sign-out button to /dashboard

- **Slice:** D
- **Goal:** Cover AUTH-03 — user can sign out from /dashboard; refreshing lands on /sign-in.
- **Files:** `frontend/src/components/sign-out-button.tsx`, `frontend/src/app/dashboard/page.tsx`
- **Deps:** WS-D.3
- **Acceptance:**
  - `frontend/src/components/sign-out-button.tsx` is a client component (`"use client"`) using `<SignOutButton>` from `@clerk/nextjs` wrapping a shadcn `<Button variant="outline">Sign out</Button>`. After sign-out it redirects to `/sign-in`.
  - `frontend/src/app/dashboard/page.tsx` updated to render the sign-out button. Still server-component shell; sign-out is the only client-side island.
  - `pnpm dev`; sign in; visit `/dashboard`; click Sign out → redirected to `/sign-in`. Refresh the browser → stays on `/sign-in` (cookie cleared).
- **REQ-IDs:** AUTH-03
- **Commit message:** `feat(frontend): add sign-out button to /dashboard`
- **Estimated complexity:** S
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** Manual: sign out, refresh, confirm /sign-in is shown.

---

### Slice E: Clerk → Flask trust boundary (require_auth, /me, BFF /api/me)

This slice wires the cross-runtime trust boundary. The BFF mints a JWT via `getToken()`, forwards it as `Authorization: Bearer`; Flask `@require_auth` verifies networkless; `/me` returns the email. Crucially, at this point Mongo doesn't yet have a user record (that comes in Slice F via webhook), so `/me` returns 404. The slice is verifiable by checking the 404 response carries the correct shape.

#### WS-E.1 — BFF: src/app/api/me/route.ts forwards JWT to Flask /me

- **Slice:** E
- **Goal:** Implement the BFF pattern from research §Pattern 1 — read Clerk session via `auth()`, mint short-lived JWT via `getToken()`, forward to Flask.
- **Files:** `frontend/src/app/api/me/route.ts`
- **Deps:** WS-D.4, WS-C.2
- **Acceptance:**
  - `frontend/src/app/api/me/route.ts` exports `async function GET(req: Request)`:
    ```typescript
    import { auth } from "@clerk/nextjs/server";
    export async function GET() {
      const { userId, getToken } = await auth();
      if (!userId) return new Response("Unauthorized", { status: 401 });
      const token = await getToken();
      if (!token) return new Response("No token", { status: 401 });
      const res = await fetch(`${process.env.BACKEND_URL}/me`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      const body = await res.text();
      return new Response(body, { status: res.status, headers: { "Content-Type": "application/json" } });
    }
    ```
  - Developer sets `BACKEND_URL=http://localhost:8000` in `frontend/.env.local`.
  - `pnpm dev` (frontend) + `flask run` (backend) running concurrently. Sign in. Visit `http://localhost:3000/api/me` directly in browser → expect a JSON response from Flask. Since the user record doesn't exist yet, Flask returns 404 `{"error": "user_not_found"}`. **THIS 404 IS THE PROOF the JWT verification works** — without it Flask would 401, not 404.
- **REQ-IDs:** AUTH-06
- **Commit message:** `feat(frontend): add BFF /api/me forwarding Clerk JWT to Flask`
- **Estimated complexity:** M
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** While signed in, `curl --cookie "$(cat session.txt)" http://localhost:3000/api/me` returns 404 with `user_not_found` (the body proves Flask verified the JWT).

#### WS-E.2 — Flask /me wires through to MongoDB users collection

- **Slice:** E
- **Goal:** Flask `/me` does a real `users.find_one({"clerk_id": g.clerk_user_id})`; returns `{"email": user["email"]}` on hit, 404 on miss.
- **Files:** `backend/app/routes/me.py`, `backend/tests/test_me.py` (update integration test)
- **Deps:** WS-E.1, WS-C.2
- **Acceptance:**
  - `backend/app/routes/me.py` matches research §3.8 exactly: imports `users` from `app.db`; the route returns `jsonify({"email": user["email"]}), 200` when found, `jsonify({"error": "user_not_found"}), 404` when not found.
  - `tests/test_me.py` integration test: with a valid JWT and a Mongo record matching `clerk_id`, returns 200 with `{"email": "..."}`; without the Mongo record, returns 404.
  - Manual sanity (post-WS-F.2 when webhook creates the record): visit `/dashboard` → see your email rendered.
- **REQ-IDs:** AUTH-06
- **Commit message:** `feat(backend): /me reads users.find_one({clerk_id}) from Mongo`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd backend && pytest tests/test_me.py -x` passes both the 200 and 404 cases.

#### WS-E.3 — /dashboard fetches /api/me and renders email

- **Slice:** E
- **Goal:** Server component on `/dashboard` calls the BFF `/api/me` and renders the email. If the response is 404 (no user record yet, before webhook fires), show "Setting up your account…". After Slice F's webhook lands, this becomes the success state.
- **Files:** `frontend/src/app/dashboard/page.tsx`
- **Deps:** WS-E.1
- **Acceptance:**
  - `frontend/src/app/dashboard/page.tsx` (server component) does:
    ```typescript
    import { headers } from "next/headers";
    export default async function Dashboard() {
      const h = await headers();
      const res = await fetch(`${process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'}/api/me`, {
        headers: { cookie: h.get("cookie") ?? "" },
        cache: "no-store",
      });
      if (res.status === 404) return <Card>Setting up your account…</Card>;
      if (!res.ok) return <Card>Unable to load profile</Card>;
      const { email } = await res.json();
      return <Card><h1>FitGH</h1><p>Signed in as {email}</p><SignOutButton /></Card>;
    }
    ```
  - Sign-in flow: sign up → land on `/dashboard` → "Setting up your account…" (because webhook hasn't run yet OR Phase 1 lab hasn't deployed webhook yet — Slice F fixes this).
  - After Slice F: same flow → "Signed in as francisyiryel@gmail.com".
- **REQ-IDs:** AUTH-06
- **Commit message:** `feat(frontend): /dashboard fetches /api/me and renders email`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd frontend && pnpm build` succeeds; manual confirmation in WS-J.

---

### Slice F: Clerk webhook → user.created → Mongo users doc

This slice closes the loop: on sign-up, Clerk fires a `user.created` webhook; Next.js BFF verifies the svix signature and forwards to Flask; Flask upserts a `users` doc; the next `/dashboard` load shows the email.

#### WS-F.1 — Configure Clerk webhook endpoint in Clerk dashboard [USER ACTION, AFTER WS-I.1 DEPLOY]

- **Slice:** F
- **Goal:** Tell Clerk to fire webhooks at `https://fitgh.vercel.app/api/webhooks/clerk`. **Order note:** the webhook URL must be a real public URL, so this task technically waits for WS-I.1 Vercel preview deploy. For local dev, use a temporary `ngrok` tunnel and a SEPARATE Clerk Development instance webhook pointing at the tunnel URL.
- **Files:** (none committed)
- **Deps:** WS-D.1, WS-I.1 (for prod URL) OR ngrok (for local testing)
- **Acceptance:**
  - User opens Clerk Dashboard → Webhooks → Add Endpoint.
  - Endpoint URL: `https://fitgh.vercel.app/api/webhooks/clerk` (after WS-I.1; for local-only smoke, use `https://<your-ngrok>.ngrok.io/api/webhooks/clerk` against the Dev Clerk instance).
  - Events selected: `user.created` AND `user.deleted` (Phase 1 doesn't yet handle `user.updated`).
  - User copies the Signing Secret (whsec_...) into a password manager AND into `.env.local` as `CLERK_WEBHOOK_SECRET` (locally) and into Vercel env vars (after WS-I.1).
- **REQ-IDs:** AUTH-01
- **Commit message:** (no commit)
- **Estimated complexity:** S
- **Type:** `checkpoint:human-action`
- **Verify (automated):** N/A — operator confirmation that webhook endpoint is registered with whsec_ stored.

#### WS-F.2 — BFF /api/webhooks/clerk: svix verify + forward to Flask

- **Slice:** F
- **Goal:** Implement research §3.9 exactly — svix verify the inbound payload, forward verified events to Flask with `x-clerk-verified: true` header.
- **Files:** `frontend/src/app/api/webhooks/clerk/route.ts`, `frontend/package.json` (add svix dep)
- **Deps:** WS-D.2
- **Acceptance:**
  - `cd frontend && pnpm add svix`.
  - `frontend/src/app/api/webhooks/clerk/route.ts` matches research §3.9 source: reads `svix-id`, `svix-timestamp`, `svix-signature` headers; `new Webhook(process.env.CLERK_WEBHOOK_SECRET!).verify(body, headers)`; on success forwards to `${BACKEND_URL}/webhooks/clerk` with `x-clerk-verified: true`.
  - Smoke test per Gotcha G11: `curl -X POST https://localhost:3000/api/webhooks/clerk -d '{}'` returns 400 (invalid signature) — NOT 401 (which would indicate the middleware is incorrectly protecting the webhook route).
- **REQ-IDs:** AUTH-01
- **Commit message:** `feat(frontend): BFF /api/webhooks/clerk with svix verify`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `curl -X POST http://localhost:3000/api/webhooks/clerk -d '{}' -H "Content-Type: application/json"` returns HTTP 400 (signature missing/invalid), NOT 401.

#### WS-F.3 — Flask /webhooks/clerk: upsert on user.created, delete on user.deleted

- **Slice:** F
- **Goal:** Flask `/webhooks/clerk` matches research §3.9 backend handler. Checks `x-clerk-verified: true`; on `user.created`, upserts the `users` doc with `clerk_id`, `email`, timestamps; on `user.deleted`, deletes the doc.
- **Files:** `backend/app/routes/webhooks.py`, `backend/tests/test_webhooks.py`
- **Deps:** WS-F.2, WS-C.2
- **Acceptance:**
  - `backend/app/routes/webhooks.py` matches research §3.9 source.
  - `tests/test_webhooks.py` integration test: POSTing a `user.created` event with `x-clerk-verified: true` creates a `users` doc in mongomock; POSTing a `user.deleted` event removes it.
  - End-to-end manual: sign up a new user via `/sign-up`. Clerk fires webhook to Vercel BFF → svix verify → forward to Flask → Mongo `users` doc is created. Refresh `/dashboard` → "Signed in as <your-email>" appears.
- **REQ-IDs:** AUTH-01
- **Commit message:** `feat(backend): /webhooks/clerk upserts users on user.created`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `cd backend && pytest tests/test_webhooks.py -x` passes; manual end-to-end in WS-J.

---

### Slice G: Fly.io deploy (Dockerfile, fly.toml jnb, secrets, deploy)

This slice deploys Flask to Fly.io's `jnb` region. Atlas allowlist still permits the developer's IP (or `0.0.0.0/0`); Slice H tightens to the egress IP. Per STATE.md blocker, this slice has a halt-condition if egress IP cost > $5/mo.

#### WS-G.1 — Author Dockerfile + .dockerignore + gunicorn.conf.py

- **Slice:** G
- **Goal:** Production-grade Dockerfile per research §6 (Python 3.12 slim, gunicorn with `--workers 2 --threads 4 --timeout 60`).
- **Files:** `backend/Dockerfile`, `backend/.dockerignore`, `backend/gunicorn.conf.py`
- **Deps:** WS-B.6 (smoke Dockerfile already exists; this replaces it with the real one)
- **Acceptance:**
  - `backend/Dockerfile`:
    ```dockerfile
    FROM python:3.12-slim AS base
    WORKDIR /app
    RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY app/ ./app/
    COPY gunicorn.conf.py .
    EXPOSE 8000
    CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:create_app()"]
    ```
  - `backend/gunicorn.conf.py`: `bind = "0.0.0.0:8000"`, `workers = 2`, `threads = 4`, `worker_class = "gthread"`, `timeout = 60`, `accesslog = "-"`, `errorlog = "-"`.
  - `backend/.dockerignore`: excludes `.venv/`, `__pycache__/`, `*.pyc`, `tests/`, `.pytest_cache/`, `.ruff_cache/`, `.env*`, `.git/`.
  - `cd backend && docker build -t fitgh-api:dev .` succeeds.
  - `docker run --rm -p 8000:8000 -e MONGODB_URI=... -e CLERK_SECRET_KEY=sk_test_... -e CLERK_AUTHORIZED_PARTIES=http://localhost:3000 -e CORS_ALLOWED_ORIGINS=http://localhost:3000 fitgh-api:dev` starts; `curl http://localhost:8000/health` returns `mongo: connected`.
- **REQ-IDs:** DEPLOY-02
- **Commit message:** `feat(backend): production Dockerfile + gunicorn config`
- **Estimated complexity:** M
- **Type:** `auto`
- **Verify (automated):** `cd backend && docker build -t fitgh-api:test .` exits 0.

#### WS-G.2 — Author fly.toml (jnb, always-on, /health check)

- **Slice:** G
- **Goal:** Fly.io config per research §6 + SKELETON.md: `primary_region = "jnb"`, always-on machine, `/health` HTTP check.
- **Files:** `backend/fly.toml`
- **Deps:** WS-G.1
- **Acceptance:**
  - `backend/fly.toml`:
    ```toml
    app = "fitgh-api"
    primary_region = "jnb"
    [build]
    [env]
      PORT = "8000"
    [http_service]
      internal_port = 8000
      force_https = true
      auto_stop_machines = "off"
      auto_start_machines = true
      min_machines_running = 1
      processes = ["app"]
      [[http_service.checks]]
        grace_period = "10s"
        interval = "30s"
        method = "GET"
        timeout = "5s"
        path = "/health"
    [[vm]]
      size = "shared-cpu-1x"
      memory = "512mb"
    ```
  - File validates: `cd backend && fly config validate` (requires flyctl installed locally).
- **REQ-IDs:** DEPLOY-02
- **Commit message:** `feat(backend): fly.toml for jnb always-on shared-cpu-1x with /health check`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `cd backend && fly config validate` exits 0.

#### WS-G.3 — fly launch (no deploy) + fly secrets set [USER ACTION needed for flyctl auth]

- **Slice:** G
- **Goal:** Create the Fly app shell and set production secrets.
- **Files:** (none committed; secrets set via flyctl)
- **Deps:** WS-G.2, WS-0.2 (Fly billing configured)
- **Acceptance:**
  - User has run `flyctl auth login` (browser-based).
  - `cd backend && fly launch --no-deploy --copy-config --name fitgh-api --region jnb --org personal` — accepts existing fly.toml; does not deploy.
  - Set secrets via:
    ```
    fly secrets set \
      MONGODB_URI="<rotated-uri-from-ws-0.1>" \
      CLERK_SECRET_KEY="<sk_test_... or sk_live_...>" \
      CLERK_AUTHORIZED_PARTIES="https://fitgh.vercel.app" \
      CORS_ALLOWED_ORIGINS="https://fitgh.vercel.app" \
      SENTRY_DSN_BACKEND="<from-sentry-ws-g.5>" \
      FLASK_ENV="production" \
      --app fitgh-api --stage
    ```
    (The `--stage` flag stages secrets without triggering a deploy; they apply on next `fly deploy`.) For Phase 1, use the Production Clerk keys (`sk_live_`) AND CLERK_AUTHORIZED_PARTIES set to the Vercel URL (which doesn't exist yet — but Clerk's authorized_parties just needs to match `aud` on the JWT, so this is fine pre-Vercel).
  - `fly secrets list --app fitgh-api` shows all 6 secrets present.
- **REQ-IDs:** DEPLOY-02
- **Commit message:** (no commit — flyctl operations)
- **Estimated complexity:** M
- **Type:** `checkpoint:human-action`
- **Verify (automated):** `fly secrets list --app fitgh-api | grep -c '^[A-Z_]\+'` is ≥ 6.

#### WS-G.4 — fly deploy + verify /health from production

- **Slice:** G
- **Goal:** First production deploy; confirm `/health` returns `mongo: connected` from `fitgh-api.fly.dev`.
- **Files:** (none committed)
- **Deps:** WS-G.3
- **Acceptance:**
  - `cd backend && fly deploy --app fitgh-api`. Deploy completes; `fly status --app fitgh-api` shows 1 machine running in `jnb`.
  - **Atlas Network Access still has `0.0.0.0/0` OR dev IP** at this point — that's fine for now. Slice H tightens.
  - `curl https://fitgh-api.fly.dev/health` returns `{"ok": true, "mongo": "connected"}`.
  - Run `curl https://fitgh-api.fly.dev/health` 3 times in a row over 30 seconds to confirm the always-on machine doesn't cold-start between requests (per Gotcha G4, the first post-deploy request may be slow; subsequent should be <500ms).
- **REQ-IDs:** DEPLOY-02
- **Commit message:** (no commit)
- **Estimated complexity:** S
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** `curl -s https://fitgh-api.fly.dev/health | grep -q '"mongo": "connected"'` exits 0.

#### WS-G.5 — Verify Fly.io static egress IP pricing [USER ACTION, STATE.md BLOCKER]

- **Slice:** G
- **Goal:** Close the STATE.md blocker on egress IP cost. Per research §G3, app-scoped egress IPv4 is $3.60/mo as of Jan 1, 2026. If actual cost > $5/mo on the developer's account, halt and discuss the fallback (`0.0.0.0/0` + strong password as dev-only) before proceeding to WS-H.
- **Files:** (none committed; STATE.md may be updated to record the verified price)
- **Deps:** WS-G.4
- **Acceptance:**
  - User runs `fly platform regions | grep jnb` to confirm jnb is available (per Assumption A10).
  - User visits Fly.io billing page; confirms the egress-IP add-on listing shows $3.60/mo per IPv4 in their account's currency.
  - If price > $5/mo: STOP. Open a discussion with the user; possible decisions are (a) accept the higher cost, (b) defer egress IP to Phase 7 and run with `0.0.0.0/0` + 32-char password in Phase 1, (c) regionswap.
  - If price ≤ $5/mo: confirm in chat "Egress IP price verified at $X.XX/mo — proceeding to WS-H".
  - Update STATE.md blocker section: "Static egress IP cost on Fly.io 2026 — VERIFIED at $X.XX/mo as of YYYY-MM-DD".
- **REQ-IDs:** DEPLOY-02
- **Commit message:** `docs(state): record verified Fly.io egress IP cost`
- **Estimated complexity:** S
- **Type:** `checkpoint:decision`
- **Verify (automated):** N/A — operator decision.

---

### Slice H: Static egress IP + Atlas allowlist tightening (production lockdown)

#### WS-H.1 — fly ips allocate-egress -r jnb; capture IPv4

- **Slice:** H
- **Goal:** Allocate the static egress IPv4 in `jnb`. Per Gotcha G10, this is the OUTBOUND source IP — `fly ips list` shows shared IPs (free, for incoming); the egress IP is a separate product.
- **Files:** (none committed; IP recorded in chat)
- **Deps:** WS-G.5
- **Acceptance:**
  - `cd backend && fly ips allocate-egress -r jnb --app fitgh-api` runs successfully; captures the IPv4 address.
  - `fly ips list --app fitgh-api` shows TWO entries: a shared IP (for incoming traffic) AND the new app-scoped IPv4 egress (with type `Egress`).
  - User records the egress IP in a password manager (or commits it to STATE.md if non-sensitive; egress IPs are NOT secret).
  - Verify per Gotcha G10: `fly ssh console --app fitgh-api` then inside the machine `curl --resolve ifconfig.me:443:<egress-IP> https://ifconfig.me` — the returned IP must match the allocated egress IP. (Caveat: ifconfig.me may not be resolvable from the Fly machine; alternative is `curl https://ifconfig.me` from the Fly machine and check the source IP recorded.) If verification proves a different IP, halt and debug Gotcha G10 (shared vs dedicated confusion).
- **REQ-IDs:** SEC-04, DEPLOY-02
- **Commit message:** (no commit — Fly operation)
- **Estimated complexity:** M
- **Type:** `checkpoint:human-action`
- **Verify (automated):** `fly ips list --app fitgh-api --json | python -c "import sys, json; data = json.load(sys.stdin); assert any(ip.get('Type') == 'Egress' for ip in data), 'No egress IP found'"`.

#### WS-H.2 — Atlas: add egress IPv4 /32 to Network Access; remove 0.0.0.0/0 from production [USER ACTION]

- **Slice:** H
- **Goal:** Pin the Fly egress IP in Atlas allowlist; remove the wildcard. After this, ONLY the Fly egress IP can connect to Atlas in production. Dev IPs remain (for developer workstation access).
- **Files:** (none committed)
- **Deps:** WS-H.1
- **Acceptance:**
  - User opens Atlas Dashboard → Network Access → IP Access List.
  - Adds entry: IP `<egress-IPv4>/32` with comment "Fly.io jnb egress (production)".
  - Removes entry `0.0.0.0/0` if present (it shouldn't be at this point per WS-C.1; but if it is, remove it).
  - Dev IPs remain (developer's home/office IP) so local Flask can still connect.
  - User confirms entries in chat: "Atlas allowlist now contains: <dev-IP>, <fly-egress-IP>; NO 0.0.0.0/0".
- **REQ-IDs:** SEC-04, DEPLOY-02
- **Commit message:** (no commit)
- **Estimated complexity:** S
- **Type:** `checkpoint:human-action`
- **Verify (automated):** N/A — operator confirmation.

#### WS-H.3 — Re-verify /health from Fly machine after allowlist change

- **Slice:** H
- **Goal:** Prove the Fly egress IP is correctly pinned by re-hitting `/health`. If the IP allocation is wrong, Mongo will reject the connection and `/health` returns `mongo: error`.
- **Files:** (none committed)
- **Deps:** WS-H.2
- **Acceptance:**
  - `curl https://fitgh-api.fly.dev/health` returns `{"ok": true, "mongo": "connected"}` AFTER the allowlist change.
  - If it returns `mongo: error` or times out, the egress IP allocation is broken — debug per Gotcha G10 before proceeding.
- **REQ-IDs:** DEPLOY-02
- **Commit message:** (no commit)
- **Estimated complexity:** S
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** `curl -s --max-time 10 https://fitgh-api.fly.dev/health | grep -q '"mongo": "connected"'`.

---

### Slice I: Vercel deploy + Analytics + Speed Insights

#### WS-I.1 — Connect GitHub repo to Vercel; set env vars; first deploy

- **Slice:** I
- **Goal:** First Vercel deploy of `/frontend` to `fitgh.vercel.app`; production env vars set.
- **Files:** (none committed; Vercel dashboard work)
- **Deps:** WS-A.5, WS-D.3, WS-G.4 (BACKEND_URL needs Fly to be live)
- **Acceptance:**
  - User connects GitHub repo to Vercel; selects framework "Next.js"; sets Root Directory = `frontend`; Node version = 20.
  - Sets Production env vars: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...`, `CLERK_SECRET_KEY=sk_live_...`, `CLERK_WEBHOOK_SECRET=whsec_...` (filled in WS-F.1), `BACKEND_URL=https://fitgh-api.fly.dev`, `NEXT_PUBLIC_SENTRY_DSN=<placeholder until WS-I.3>`, `SENTRY_AUTH_TOKEN=<placeholder until WS-I.3>`, `NEXT_PUBLIC_APP_URL=https://fitgh.vercel.app`.
  - Sets Preview env vars: SAME as Production for Phase 1 per Gotcha G12 Assumption A7 (preview signups acceptable to touch prod Atlas in Phase 1; tighten in Phase 7).
  - Trigger first deploy by pushing to `main` (or "Deploy" button). Deploy succeeds; `https://fitgh.vercel.app/` loads (redirects to `/sign-in`).
- **REQ-IDs:** DEPLOY-01
- **Commit message:** (no commit — Vercel dashboard work)
- **Estimated complexity:** M
- **Type:** `checkpoint:human-action`
- **Verify (automated):** `curl -sI https://fitgh.vercel.app/ | grep -E '^location: /sign-in'` (or equivalent depending on middleware redirect behaviour).

#### WS-I.2 — Add Vercel Analytics + Speed Insights to app/layout

- **Slice:** I
- **Goal:** Wire `<Analytics />` and `<SpeedInsights />` into `app/layout.tsx` (OBS-02). Free on Hobby plan.
- **Files:** `frontend/package.json` (deps), `frontend/src/app/layout.tsx`
- **Deps:** WS-I.1
- **Acceptance:**
  - `cd frontend && pnpm add @vercel/analytics @vercel/speed-insights`.
  - `frontend/src/app/layout.tsx`: imports `<Analytics />` from `@vercel/analytics/next` and `<SpeedInsights />` from `@vercel/speed-insights/next`; renders them as siblings inside `<body>`, AFTER `{children}`, inside the `<ClerkProvider>`.
  - Vercel dashboard → Analytics tab is enabled; Speed Insights tab is enabled.
  - Redeploy via push to main; after deploy, visit `https://fitgh.vercel.app/` (signed in) → `/dashboard` → wait 30 seconds → Vercel Analytics dashboard shows ≥1 pageview.
- **REQ-IDs:** OBS-02
- **Commit message:** `feat(frontend): add Vercel Analytics + Speed Insights`
- **Estimated complexity:** S
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** Manual — confirm Vercel Analytics dashboard shows a pageview event after visiting the deployed app.

#### WS-I.3 — Run Sentry wizard (FE) + add backend Sentry DSN; trigger smoke errors

- **Slice:** I
- **Goal:** Wire Sentry FE via `pnpm dlx @sentry/wizard@latest -i nextjs --saas` (research §G7) AND verify backend Sentry already configured from WS-B.2. Trigger deliberate errors on FE + BE and confirm Sentry receives them with PII scrubbed.
- **Files:** `frontend/instrumentation.ts`, `frontend/sentry.client.config.ts`, `frontend/sentry.edge.config.ts`, `frontend/sentry.server.config.ts`, `frontend/next.config.js` (wizard adds `withSentryConfig`), Vercel env var `NEXT_PUBLIC_SENTRY_DSN` + `SENTRY_AUTH_TOKEN` (set in dashboard)
- **Deps:** WS-I.2
- **Acceptance:**
  - User creates two Sentry projects: `fitgh-frontend` (Next.js) and `fitgh-backend` (Python Flask). Captures DSNs + an org auth token.
  - User sets `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_AUTH_TOKEN` in Vercel env vars (Production + Preview).
  - User runs `cd frontend && pnpm dlx @sentry/wizard@latest -i nextjs --saas` — accepts the auth token; wizard creates `instrumentation.ts`, `sentry.client.config.ts`, `sentry.edge.config.ts`, `sentry.server.config.ts`, modifies `next.config.js`.
  - The four Sentry config files each set `beforeSend` to strip PII: drops `user.email`, `user.id`, any breadcrumb with `category: 'auth'` having `data.email`. The `tunnelRoute` may be configured to bypass ad-blockers if desired (optional Phase 1).
  - **FE smoke test:** Add a `throw new Error('FE smoke test for Sentry')` to a temporary throwaway page; deploy; visit; confirm Sentry FE project receives the event with `user.email` MISSING from the event payload. Revert the throw, redeploy.
  - **BE smoke test:** Add `raise RuntimeError('BE smoke test for Sentry')` to a temporary endpoint in Flask (e.g., add a `/_sentry_smoke` route); deploy via `fly deploy`; `curl https://fitgh-api.fly.dev/_sentry_smoke`; confirm Sentry BE project receives the event with `request.headers.authorization` scrubbed AND `user.email` MISSING. Revert and redeploy.
  - Per Gotcha G7: confirm `SENTRY_PROJECT_FE != SENTRY_PROJECT_BE` (different project slugs in Sentry).
- **REQ-IDs:** OBS-01
- **Commit message:** `feat(observability): wire Sentry FE wizard + verify BE; smoke-test PII scrubbers`
- **Estimated complexity:** L
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** After smoke tests run, query Sentry API or visually check the Sentry dashboard for two events: one in `fitgh-frontend`, one in `fitgh-backend`, both with no email/PII in the scrubbed event payload.

---

### Slice J: E2E smoke + sign-off

#### WS-J.1 — End-to-end manual smoke test on deployed app

- **Slice:** J
- **Goal:** Walk through every ROADMAP success criterion against the deployed app. This is the final go/no-go gate for Phase 1.
- **Files:** `.planning/phases/01-walking-skeleton/01-PHASE1-SIGNOFF.md` (created at the end of this task)
- **Deps:** WS-I.3, WS-F.3 (webhook live in prod)
- **Acceptance:**
  - **SC-1 (AUTH-01, AUTH-02, AUTH-06):** Visit `https://fitgh.vercel.app/` → redirected to `/sign-in` → sign up with email/password OR Google OAuth → land on `/dashboard` showing the user's email rendered from Atlas through Flask. Take a screenshot.
  - **SC-2 (AUTH-03):** Click Sign out on `/dashboard` → redirected to `/sign-in`. Refresh browser → still on `/sign-in` (cookie cleared).
  - **SC-3 (DEPLOY-02, SEC-04):** `curl https://fitgh-api.fly.dev/health` → `{"ok": true, "mongo": "connected"}`. Confirm Atlas Network Access shows the Fly egress IPv4 pinned and does NOT contain `0.0.0.0/0`.
  - **SC-4 (PERF-01, SEC-01):** Confirm WS-A.5 smoke-test PR (the Three.js bloat) fails CI on `size-limit`. Confirm gitleaks blocks a local commit containing a fake Mongo URI: developer creates a temporary file with `mongodb+srv://test:realsecret@cluster0.pcd3g.mongodb.net/test`, attempts `git commit` → blocked. Revert.
  - **SC-5 (OBS-01, OBS-02, AUTH-06):** Confirm Sentry FE + BE smoke events from WS-I.3 are visible in the Sentry UI (PII scrubbed). Confirm Vercel Analytics shows ≥1 pageview AND Speed Insights shows ≥1 Web Vital sample. Confirm Flask logs show `authenticate_request` succeeded networkless (no outbound HTTPS to Clerk per request — should only see the JWKS fetch once at process startup).
  - Author `01-PHASE1-SIGNOFF.md` with 5 checkmarks AND screenshots/log-extracts referenced.
- **REQ-IDs:** AUTH-01, AUTH-02, AUTH-03, AUTH-06, SEC-01, SEC-02, SEC-03, SEC-04, OBS-01, OBS-02, PERF-01, DEPLOY-01, DEPLOY-02
- **Commit message:** `docs(phase-01): Phase 1 Walking Skeleton sign-off`
- **Estimated complexity:** L
- **Type:** `checkpoint:human-verify`
- **Verify (automated):** Each SC has its own automated sub-check:
  ```
  curl -s https://fitgh-api.fly.dev/health | grep -q '"mongo": "connected"'
  curl -sI https://fitgh.vercel.app/sign-in | grep -q '200'
  gh run list --workflow frontend.yml --branch <bloat-smoke-branch> --limit 1 | grep -q failure
  ```

#### WS-J.2 — Update ROADMAP + STATE.md; mark Phase 1 complete

- **Slice:** J
- **Goal:** Close the loop on phase-level docs.
- **Files:** `.planning/ROADMAP.md`, `.planning/STATE.md`
- **Deps:** WS-J.1
- **Acceptance:**
  - `.planning/ROADMAP.md` Phase 1 entry: checkbox flipped `[x]`; "Plans: 1/1 complete" updated.
  - `.planning/STATE.md`: Current Position updated to "Phase 2 ready"; blockers section updated (Mongo password rotation closed; static egress IP cost recorded; Rive designer pipeline still open per its Phase 5 ownership).
  - Both files committed.
- **REQ-IDs:** —
- **Commit message:** `docs(phase-01): mark Phase 1 complete in ROADMAP + STATE`
- **Estimated complexity:** S
- **Type:** `auto`
- **Verify (automated):** `grep -q '^\- \[x\] \*\*Phase 1' .planning/ROADMAP.md`.

---

## Phase 1 Done When (Goal-Backward Verification Map)

Each ROADMAP success criterion maps to the specific task(s) whose acceptance criteria prove it. No criterion is left without a task.

| ROADMAP Success Criterion | Proving Task(s) | Requirement IDs Closed |
|---------------------------|------------------|------------------------|
| SC-1: User signs in via Clerk-hosted UI (email/password OR Google) and lands on /dashboard showing their email pulled from Atlas through Flask. | WS-D.3 (sign-up flow), WS-E.1 (BFF mints JWT), WS-E.2 (Flask /me reads Mongo), WS-E.3 (/dashboard renders email), WS-F.3 (webhook creates user), WS-J.1 SC-1 verification | AUTH-01, AUTH-02, AUTH-06 |
| SC-2: User can sign out from any page; refreshing after sign-out lands on /sign-in (httpOnly cookie cleared). | WS-D.4 (sign-out button), WS-J.1 SC-2 verification | AUTH-03 |
| SC-3: Flask /health returns {ok:true, mongo:"connected"} from Fly.io JNB; static egress IP pinned in Atlas allowlist (no 0.0.0.0/0 in production). | WS-G.4 (initial deploy /health), WS-H.1 (egress IP allocated), WS-H.2 (Atlas allowlist locked down), WS-H.3 (post-lockdown /health verify), WS-J.1 SC-3 verification | DEPLOY-02, SEC-04 |
| SC-4: CI PR pushing First Load JS > 180 KB fails the build; commit containing a Mongo URI is blocked by gitleaks pre-commit. | WS-A.4 (size-limit config), WS-A.5 (size-limit CI smoke-tested with bloat PR), WS-0.4 (gitleaks pre-commit installed + smoke-tested), WS-0.5 (gitleaks CI workflow), WS-J.1 SC-4 verification | PERF-01, SEC-01 |
| SC-5: Sentry (FE+BE) and Vercel Analytics + Speed Insights receive ≥1 real event from deployed app; Flask Authorization: Bearer JWT verified networkless on every protected request. | WS-B.2 (Sentry BE init with scrubber), WS-I.2 (Vercel Analytics + Speed Insights), WS-I.3 (Sentry wizard + smoke), WS-B.4 + WS-E.2 (require_auth via clerk-backend-api networkless), WS-J.1 SC-5 verification | OBS-01, OBS-02, AUTH-06 |

**Additional requirement coverage (not in SC-1..5 but in `requirements_targeted`):**
- SEC-02 (Atlas password rotated, least-priv user): WS-0.1
- SEC-03 (Flask CORS explicit allowlist): WS-B.2, WS-B.5 `test_cors.py`
- DEPLOY-01 (Frontend deploys to Vercel from /frontend): WS-I.1, WS-I.2

**No requirement ID is left without a task. ✓**

---

## Coverage Audit

**GOAL coverage (ROADMAP Phase 1 success criteria):** All 5 SCs mapped above. ✓

**REQ coverage (13 IDs in `requirements_targeted`):** All 13 IDs cited in the table above and in individual task `REQ-IDs:` fields. ✓

**RESEARCH coverage (01-RESEARCH.md "Tasks Implied" Slices A-I):**
- Slice A (Repo + secret hygiene): WS-0.1 to WS-0.5 ✓
- Slice B (Frontend scaffold): WS-A.1 to WS-A.5 + WS-D.2 (middleware + ClerkProvider lives in this plan's Slice D for vertical-slice ordering) ✓
- Slice C (Clerk SaaS setup): WS-D.1 + WS-F.1 ✓
- Slice D (Backend scaffold): WS-B.1 to WS-B.6 ✓
- Slice E (Fly.io deploy): WS-G.1 to WS-G.5 + WS-H.1 to WS-H.3 ✓
- Slice F (Vercel deploy): WS-I.1 to WS-I.2 ✓
- Slice G (Observability wiring): WS-I.3 ✓
- Slice H (CI): WS-0.5 + WS-A.5 + WS-B.6 ✓
- Slice I (End-to-end smoke): WS-J.1 to WS-J.2 ✓

**CONTEXT coverage:** No CONTEXT.md exists for this phase (no `/gsd-discuss-phase` was run). The locked decisions come from STATE.md and PROJECT.md "Key Decisions" + research/SUMMARY.md "Locked Stack Decisions" — all honoured (Clerk auth, Fly.io jnb always-on, static egress IP, gitleaks pre-commit, size-limit 180 KB gate, PyMongo singleton, Sentry PII scrubber).

**Gaps:** None. No items moved to "deferred" beyond what's already in Out of Scope. No PHASE SPLIT RECOMMENDED.

---

## Execution Notes for the Executor

1. **Slices have hard ordering when noted.** Slice 0 must complete before any other slice runs (esp. WS-0.4 gitleaks before WS-C.1 which handles real Mongo URIs in `.env.local`). Slices A and B may run in parallel after Slice 0. Slices C through J are sequential.
2. **Use the Write tool for ALL file creation.** Never `Bash(cat << 'EOF')`. Per the critical rules.
3. **When a task touches the Clerk Python SDK, copy the wrapper from research §3.8 EXACTLY.** The `httpx.Request` quirk is non-obvious and not documented in casual blog posts.
4. **When a task touches Tailwind, ensure `tailwind.config.js` does NOT exist.** v4 is CSS-first; if create-next-app or shadcn somehow generates one, delete it and verify `components.json` has `"config": ""`.
5. **`checkpoint:human-action` tasks REQUIRE the user to perform dashboard work.** Pause execution and clearly list what the user must do; resume only after explicit "done" confirmation.
6. **`checkpoint:human-verify` tasks REQUIRE the user to confirm an observable outcome.** Run the automation first; then pause for confirmation.
7. **All `<verify>` automation commands must be runnable on Windows PowerShell.** The environment is Windows 11; use forward-slashes or quoted paths where ambiguity exists.
8. **If WS-G.5 reveals egress IP cost > $5/mo:** STOP and discuss with the user. Do not silently flip to `0.0.0.0/0` — per STATE.md blocker, this is a documented decision point.

---

## Success Criteria (Plan-Level)

This plan is COMPLETE when:

- [ ] All 30 tasks (WS-0.1 through WS-J.2) have their acceptance criteria met.
- [ ] All 13 requirement IDs (AUTH-01, AUTH-02, AUTH-03, AUTH-06, SEC-01, SEC-02, SEC-03, SEC-04, OBS-01, OBS-02, PERF-01, DEPLOY-01, DEPLOY-02) are demonstrably closed via task acceptance.
- [ ] `.planning/phases/01-walking-skeleton/01-PHASE1-SIGNOFF.md` exists with 5 checkmarks and references.
- [ ] `.planning/ROADMAP.md` Phase 1 is `[x]` checked.
- [ ] `.planning/STATE.md` Current Position updated to "Phase 2 ready" with blockers properly closed.
- [ ] All CI workflows on `main` are green: `frontend.yml`, `backend.yml`, `gitleaks.yml`.
- [ ] Branch protection on `main` requires all three workflows to pass before merge (configured via GitHub Settings → Branches).

---

## Output

After phase completion, create `.planning/phases/01-walking-skeleton/01-walking-skeleton-01-SUMMARY.md` per the GSD summary template, capturing:
- What shipped (the 5 SC outcomes)
- What changed in architecture (versus research recommendations — any deviations)
- Patterns established (PyMongo singleton, Clerk httpx wrapper, Sentry scrubber, BFF JWT forward, svix webhook pattern, size-limit at 180 KB, gitleaks workflow)
- Decisions made during execution (recorded for future phases)
- Cost recorded (Fly.io egress IP price, Clerk free tier confirmed, Sentry free tier confirmed)
- Open items rolling forward (Rive designer pipeline → Phase 5; Lagos WebPageTest → Phase 7; nightly mongodump → Phase 3)
