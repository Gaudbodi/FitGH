# Phase 1 Research: Walking Skeleton — FitGH

**Date:** 2026-05-11
**Phase goal:** *Prove the entire trust boundary end-to-end — a Clerk-authenticated user can sign in, land on `/dashboard`, and see their email rendered from a record fetched by Next.js → Flask → MongoDB Atlas. Every supporting platform concern (deploy, secrets, CI, observability, network) wired correctly from day one. No feature work.* (from ROADMAP.md)
**Stack already locked in research/SUMMARY.md:** Next.js 15 (App Router) + Tailwind v4 + shadcn/ui on Vercel; Flask 3.1.3 + PyMongo 4.x + Clerk Python SDK on Fly.io `jnb`; MongoDB Atlas M0; Clerk auth; Sentry + Vercel Analytics observability.
**Confidence:** **HIGH** overall. MEDIUM on a handful of 2026-current version pins and on the Fly.io static-egress-IP billing model (changed in Jan 2026 — flagged below).
**Domain:** Multi-tier platform plumbing — TypeScript/React frontend, Python/Flask backend, managed Mongo, hosted auth, two PaaS deploys, CI gates.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | Sign-up with email/password OR Google OAuth via Clerk | Sections 3 (Clerk Next.js scaffold), 6 (Clerk dashboard config) |
| AUTH-02 | Session persists across browser refresh (Clerk httpOnly cookie) | Section 3 (ClerkProvider + middleware; cookie is default behaviour) |
| AUTH-03 | User can sign out from any page | Section 3 (`<UserButton />` from `@clerk/nextjs` in root layout) |
| AUTH-06 | Clerk session JWT verified networkless by Flask on every protected request | Section 3 (Flask `authenticate_request` decorator using `clerk-backend-api` 5.0.6) |
| SEC-01 | All secrets in `.env.local` / Fly.io secrets; `.env*` gitignored; gitleaks pre-commit hook from commit 1 | Sections 10 (gitleaks pre-commit) + 11 (gitleaks CI workflow) |
| SEC-02 | Exposed MongoDB password rotated before deploy; least-privilege Atlas DB user (no admin) | Section 5 (Atlas least-priv user + rotation procedure) |
| SEC-03 | Flask CORS configured with explicit origin allowlist (no `*` + credentials) | Section 4 (Flask CORS setup with explicit origins + `Authorization` in allow_headers) |
| SEC-04 | Flask uses a singleton `MongoClient` with `maxPoolSize=10` | Section 4 (`db.py` module-level singleton recipe) |
| OBS-01 | Sentry captures FE + BE errors; no PII / image data / kcal totals in error context | Section 8 (FE `instrumentation.ts` + BE `before_send` scrubber recipe) |
| OBS-02 | Vercel Analytics + Speed Insights wired on the Vercel free tier | Section 7 (`@vercel/analytics` + `@vercel/speed-insights` install + root-layout placement) |
| PERF-01 | First Load JS ≤ 180 KB gzipped per route — enforced by CI bundle-size gate from Phase 1 | Section 9 (`size-limit` + `@size-limit/preset-app` config + GitHub Action) |
| DEPLOY-01 | Frontend deploys to Vercel from `/frontend` (App Router) | Section 7 (Vercel "Root Directory" + monorepo settings) |
| DEPLOY-02 | Backend deploys to Fly.io in `jnb` region with always-on `shared-cpu-1x` 512 MB + static egress IP pinned in Atlas allowlist | Section 6 (`fly.toml` + Dockerfile + `fly ips allocate-egress` + Atlas pinning) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Frontend stack locked:** Next.js (App Router) + TypeScript + Tailwind. Rive/Lottie for animation (Rive `.riv` not in Phase 1 — placeholder only).
- **Backend stack locked:** Python (Flask).
- **DB locked:** MongoDB Atlas, existing cluster `cluster0.pcd3g.mongodb.net`. Connection string MUST live only in `.env.local` and the backend env.
- **Secrets:** `.env.local` and `.env` gitignored from project start. `.env.example` documents required vars without values.
- **Privacy:** Food images sent to LLM provider must be disclosed (not relevant to Phase 1 — no vision yet, but Sentry scrubber must already drop image bytes).
- **Solo build, free tiers preferred.**
- **GSD workflow enforcement:** No edits outside `/gsd-*` commands.

---

## Summary

Phase 1 is **all platform plumbing, zero product feature** — twelve concrete sub-recipes that produce a Vercel-hosted Next.js shell, a Fly.io JNB-region Flask service, a least-privilege Atlas user, Clerk-driven auth, two-sided Sentry coverage, Vercel Analytics + Speed Insights, a 180 KB First Load JS CI gate, and a gitleaks pre-commit hook — wired end-to-end so a signed-in user sees their email round-trip through Atlas.

**Primary recommendation:** Use the locked Next.js 15.2.4 / Tailwind v4 / Flask 3.1.3 stack as-is. Two version pins from the project-level research are stale and should be bumped: **`@sentry/nextjs` is at 10.51.0 (not 9.x)** and **`sentry-sdk` Python is at 2.53.0** — pin to `^10` and `^2.53` respectively. The Fly.io static egress IP product was reorganised in **November 2025** into "app-scoped egress IPs" with billing starting **Jan 1, 2026** at **$3.60/mo per IPv4** (IPv6 free). The legacy `fly ips allocate-v4 --shared` command is replaced by `fly ips allocate-egress`. Adopt the monorepo as **plain directories without pnpm workspaces** — only `/frontend` is JS, so workspaces add complexity for zero gain. Run `pnpm` inside `/frontend` exclusively; Vercel's "Root Directory = frontend" handles the deploy. Use a custom Clerk catch-all sign-in / sign-up page (`app/sign-in/[[...sign-in]]/page.tsx`) over Clerk-hosted UI to keep the bundle measurement honest (the dashboard route's First Load JS is what PERF-01 gates, not Clerk's hosted domain). Cap `<MongoClient(maxPoolSize=10)>` and pin the Sentry FE/BE scrubbers from day one (OBS-01 expressly bans email/kcal/image-bytes in error context).

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Sign-in / sign-up UI | Browser / Client (Next.js client component) | Clerk SaaS (hosts JWKS, OAuth providers) | `<SignIn />` / `<SignUp />` are React client components from `@clerk/nextjs`; Clerk SaaS does OAuth + email/password + session issuance. |
| Session cookie issuance + storage | Frontend Server (Next.js middleware) | Clerk SaaS | `clerkMiddleware()` injects `__session` httpOnly cookie on the response; browser stores it. Flask never reads cookies. |
| Identity propagation (browser → API) | Frontend Server (Next.js Route Handler `/api/me`) | API / Backend (Flask) | Route Handler reads Clerk session via `auth()`, mints a short-lived JWT via `getToken()`, forwards as `Authorization: Bearer <jwt>` to Flask. |
| JWT verification (networkless) | API / Backend (Flask middleware) | — | `clerk-backend-api` 5.0.6 verifies JWT against cached JWKS public key — no per-request call to Clerk API. |
| User record write on sign-up | API / Backend (Flask webhook handler) | Database (MongoDB Atlas) | Clerk webhook on `user.created` (svix-signed) → Flask `/webhooks/clerk` → `users.insert_one({clerk_id, email})`. |
| User record read on `/dashboard` | API / Backend (Flask) | Database (MongoDB Atlas) | Flask `/me` route reads `users.find_one({clerk_id: auth.sub})` via singleton `MongoClient`. |
| Static asset delivery | CDN / Static (Vercel edge) | — | Next.js shipped via Vercel's CDN. |
| Error capture (frontend) | Browser / Client (Sentry client SDK) | Sentry SaaS | `@sentry/nextjs` auto-wires client + server + edge in Next.js 15+ via `instrumentation.ts`. |
| Error capture (backend) | API / Backend (Flask Sentry integration) | Sentry SaaS | `sentry-sdk[flask]` with `FlaskIntegration()` autocaptures unhandled exceptions and request-scoped breadcrumbs. |
| Performance telemetry (RUM) | Browser / Client (Vercel beacon) | Vercel Hobby plan | `@vercel/analytics` + `@vercel/speed-insights` ship beacons to Vercel from the browser; no server-side wiring. |
| Bundle-size enforcement | CI (GitHub Actions) | — | `size-limit` reads `.next/static/chunks/app/**/*.js` after `next build` and fails the job above 180 KB gzipped. |
| Secret scanning | Developer workstation + CI | — | `gitleaks` pre-commit hook (Python `pre-commit` framework) on every commit; PR check in GitHub Actions for full-history scan. |

---

## Standard Stack

### Core (Frontend)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `next` | **15.2.4** (locked in STACK.md) | App Router, SSR, route handlers | `[CITED: nextjs.org/blog]` Next.js 16 (released Oct 2025) is current latest at 16.2.6, but locked stack says stay on 15.2.4. **Rationale to confirm:** Next.js 15.5.14 final on 15.x branch was March 2026; LTS security support ends Oct 2026. **Recommendation:** Stay on 15.2.4 for Phase 1 per locked decision; revisit at Phase 7 hardening. `[CITED: https://nextjs.org/docs/app/guides/upgrading/version-16]` |
| `react` / `react-dom` | **19.x** | UI runtime | Required by Next 15. `[CITED: shadcn install docs]` |
| `typescript` | **^5.5** | Type safety | Required for Zod + RHF inference (Phase 2+); fine for Phase 1's narrow surface. `[VERIFIED: STACK.md lock]` |
| `tailwindcss` | **^4.2** (latest is 4.2.4, Apr 2026) | CSS framework | `[VERIFIED: web search Apr 2026]` Tailwind v4.1 EOL'd 2026-02-18; v4.2 is current. Locked stack says "v4 (4.0.x)" — bump pin to `^4.2`. |
| `@tailwindcss/postcss` | **^4.2** (matches tailwindcss) | PostCSS plugin for Next.js | `[CITED: tailwindcss.com/docs/installation/using-postcss]` Required for Next.js; the "zero-config" Vite story doesn't apply here. |
| `@clerk/nextjs` | **^6.x** (latest stable as of May 2026; STACK.md says "5.x" — verify on install) | Auth (FE) | `[CITED: clerk.com/docs/nextjs/getting-started/quickstart]` Provides `<ClerkProvider>`, `<SignIn/>`, `<SignUp/>`, `<UserButton/>`, `clerkMiddleware()`, `auth()`. |
| `@vercel/analytics` | **^1.5+** | Page-view + custom-event RUM | `[CITED: vercel.com/docs/analytics/quickstart]` Free on Hobby. |
| `@vercel/speed-insights` | **^1.2+** | Web Vitals beacon | `[CITED: vercel.com/docs/speed-insights/quickstart]` Free on Hobby. |
| `@sentry/nextjs` | **^10** (latest 10.51.0, May 2026 — STACK.md says ^9 which is stale) | Errors + traces (FE + edge + server) | `[VERIFIED: npm registry web search 2026-05]` Auto-wires `instrumentation.ts` `onRequestError`. |
| `lucide-react` | **^0.460+** | Icons | shadcn dependency. |
| `class-variance-authority`, `clsx`, `tailwind-merge` | latest | shadcn className stack | Pulled by shadcn `init`. |

### Core (Backend)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `flask` | **3.1.3** | Web framework | `[VERIFIED: locked STACK.md]` |
| Python | **3.12.x** | Runtime | Flask 3.1 tested on 3.12; pinned via Dockerfile + `.python-version`. |
| `gunicorn` | **^25.1** | WSGI server | Standard prod server; Phase 1 health endpoint needs nothing fancier. |
| `flask-cors` | **^5.0** | CORS to Vercel origin | `[CITED: flask-cors.readthedocs.io]` |
| `pymongo` | **^4.17** (latest is 4.17, Apr 2026 — STACK.md says ^4.13 which is fine but bump) | MongoDB driver | `[VERIFIED: web search 2026]` 4.13+ deprecated Motor; 4.17 is current. **Recommendation: pin `pymongo>=4.13,<5`** to stay forward-compatible. |
| `pydantic` | **^2.9** | Request/response schema | Locked. |
| `clerk-backend-api` | **^5.0.6** | Networkless JWT verify | `[VERIFIED: pypi.org/project/clerk-backend-api]` Released 2026-03-19. Requires Python ≥3.10. |
| `svix` | **^1.30+** | Webhook signature verification | `[CITED: svix.com guides]` Clerk webhooks are svix-signed. |
| `python-dotenv` | **^1.0** | Local-dev env loading | Fly.io uses `fly secrets` in prod (no `.env` in container). |
| `sentry-sdk[flask]` | **^2.53** (latest 2.53.0 — STACK.md says ^2.x which is fine) | Errors + traces (BE) | `[VERIFIED: pypi web search 2026]` `FlaskIntegration()` auto-enabled if flask is in deps. |
| `gthread` | — (worker class) | Gunicorn config | Use `-k gthread --threads 4`; Phase 4 vision endpoint will need this — set it now. |

### Supporting (CI + tooling)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `size-limit` + `@size-limit/preset-app` | latest (11.x) | Bundle gate | `[CITED: github.com/ai/size-limit]` Runs after `next build` against `.next/static/chunks/app/**/*.js`. |
| `pre-commit` (Python) | latest | Local git hook framework | `[CITED: pre-commit.com]` Drives gitleaks hook. |
| `gitleaks` | **v8.21+** (via `gitleaks/gitleaks-action@v2` in CI) | Secret scanning | `[CITED: github.com/gitleaks/gitleaks]` `.gitleaks.toml` opt-in allowlist. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| **Plain monorepo with pnpm in `/frontend` only** | pnpm workspaces + `pnpm-workspace.yaml` | Workspaces save time when ≥2 JS packages share deps. Here only `/frontend` is JS — workspaces add a `pnpm-workspace.yaml`, a root `package.json`, and require Vercel "Include source files outside Root Directory" to be enabled. **For this project, NO workspaces.** `[ASSUMED]` — re-evaluate if Phase 5's Rive workflow adds a sibling `/design` package. |
| **Clerk hosted UI** (`<SignIn routing="path" />` pointing at `accounts.clerk.dev`) | Custom in-repo catch-all pages | Hosted UI = no React weight, but the user lives off-domain during sign-in which (a) complicates Vercel Analytics attribution and (b) makes the PERF-01 bundle gate easier (it only measures `/dashboard`). **Pick custom catch-all routes anyway** — same bundle (`<SignIn />` is the React component either way) and same domain story. `[CITED: clerk.com/docs/nextjs/guides/development/custom-sign-in-or-up-page]` |
| **`size-limit`** | `next-bundle-analyzer` for budget | Bundle analyzer is for *investigation*, not *enforcement* — it has no CI exit code. `size-limit` is the standard for failing PRs. `[ASSUMED]` |
| **Render or Railway for backend** | Fly.io JNB | Locked. Fly.io JNB beats Render us-east on RTT to Accra and has app-scoped static egress IPs. |
| **NextAuth / Better Auth** | Clerk | Locked. |
| **Tailwind v3** | Tailwind v4 | Locked — v4 is mandatory for data-light. |

**Installation (Phase 1, frontend):**
```bash
# in repo root
mkdir frontend && cd frontend
pnpm create next-app@latest . --typescript --tailwind --app --eslint --src-dir --import-alias "@/*" --use-pnpm --turbopack
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button card avatar sonner
pnpm add @clerk/nextjs @vercel/analytics @vercel/speed-insights @sentry/nextjs
pnpm add -D size-limit @size-limit/preset-app
```

**Installation (Phase 1, backend):**
```bash
mkdir backend && cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# bash: source .venv/bin/activate
pip install "flask>=3.1,<4" "gunicorn>=25.1" "flask-cors>=5" \
  "pymongo>=4.13,<5" "pydantic>=2.9,<3" \
  "clerk-backend-api>=5.0.6" "svix>=1.30" \
  "python-dotenv>=1.0" "sentry-sdk[flask]>=2.53"
pip freeze > requirements.txt
```

**Version verification done in research:**

| Package | STACK.md pin | Verified 2026-05 latest | Recommended Phase 1 pin |
|---------|--------------|--------------------------|--------------------------|
| `next` | 15.2.4 | 16.2.6 | **15.2.4** (locked) |
| `tailwindcss` | 4.0.x | 4.2.4 | `^4.2` |
| `@sentry/nextjs` | ^9.x | 10.51.0 | **`^10`** (bump from STACK.md) |
| `sentry-sdk` | ^2.x | 2.53.0 | `^2.53` |
| `pymongo` | ^4.13 | 4.17 | `>=4.13,<5` |
| `clerk-backend-api` | "latest" | 5.0.6 | `^5.0.6` |

Sources: [Next.js 16 upgrade](https://nextjs.org/docs/app/guides/upgrading/version-16), [Tailwind 4.2 release](https://tailwindcss.com/blog), [@sentry/nextjs npm](https://www.npmjs.com/package/@sentry/nextjs), [sentry-sdk PyPI](https://pypi.org/project/sentry-sdk/), [PyMongo 4.17 release](https://pymongo.readthedocs.io/en/stable/changelog.html), [clerk-backend-api PyPI](https://pypi.org/project/clerk-backend-api/).

---

## Architecture Patterns

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│ Browser (mid-tier Android, Ghana 4G)                                  │
│  - Clerk session __session cookie (httpOnly, Secure, SameSite=Lax)    │
│  - Vercel Analytics + Speed Insights beacons                          │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Vercel CDN  →  Next.js 15 (Vercel runtime)  [Root Dir = /frontend]    │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ middleware.ts  — clerkMiddleware() runs on every matched path │    │
│  │ ── public:  /sign-in(.*), /sign-up(.*), /api/webhooks/clerk   │    │
│  │ ── protected: everything else  (auth.protect())               │    │
│  └───────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────┐  ┌──────────────────────────────────────┐   │
│  │ app/dashboard/page   │  │ app/api/me/route.ts  (BFF)           │   │
│  │ (server component)   │──▶  - const {getToken} = await auth()   │   │
│  │ fetch('/api/me')     │  │  - fetch(FLASK_URL+'/me', {           │   │
│  │ render {email}       │  │      headers:{Authorization:`Bearer  │   │
│  └──────────────────────┘  │      ${await getToken()}`}})         │   │
│                            └──────────┬──────────────────────────┘   │
│  ┌──────────────────────┐              │                              │
│  │ app/api/webhooks/    │              │                              │
│  │   clerk/route.ts     │              │                              │
│  │ (forwards to Flask)  │              │                              │
│  └──────────┬───────────┘              │                              │
└─────────────┼──────────────────────────┼──────────────────────────────┘
              │ POST (svix-signed)       │ Authorization: Bearer <JWT>
              ▼                          ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Fly.io  (region=jnb, shared-cpu-1x 512MB, always-on)                  │
│  Static egress IP:  X.X.X.X    (pinned in Atlas allowlist)            │
│                                                                        │
│  Gunicorn → Flask 3.1.3                                                │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ app/__init__.py:create_app()                                 │     │
│  │  - flask_cors.CORS(app, origins=[FE_ORIGIN], supports_       │     │
│  │      credentials=False, allow_headers=['Authorization',      │     │
│  │      'Content-Type'])                                        │     │
│  │  - sentry_sdk.init(dsn, integrations=[FlaskIntegration()],   │     │
│  │      before_send=scrub, send_default_pii=False)              │     │
│  │  - db.py imports a module-level MongoClient                  │     │
│  │  - register_blueprint(health_bp), (me_bp), (webhooks_bp)     │     │
│  └──────────────────────────────────────────────────────────────┘     │
│  Routes:                                                               │
│   GET  /health           → {ok:true, mongo:"connected"}               │
│   GET  /me   (@require_auth) → {email}     ← read users               │
│   POST /webhooks/clerk   (svix verify)  ← user.created → insert users │
└──────────────────────────────────────────────┬─────────────────────────┘
                                               │ TLS, X.X.X.X allowed
                                               ▼
                                ┌──────────────────────────────────┐
                                │ MongoDB Atlas M0 (cluster0.…)    │
                                │  fitgh DB                        │
                                │  users:                          │
                                │   { clerk_id:str unique,         │
                                │     email:str unique,            │
                                │     created_at, updated_at }     │
                                │  user: fitgh-app  (readWrite     │
                                │     scoped to fitgh db only)     │
                                └──────────────────────────────────┘

Out-of-band:
  Clerk SaaS → POST /api/webhooks/clerk on user.created  (svix-signed)
  Sentry SaaS ← errors from FE (browser+server) and BE (Flask)
  GitHub Actions ← every PR runs frontend.yml + backend.yml + gitleaks.yml
```

### Recommended Project Structure

```
fitgh/
├── .github/
│   └── workflows/
│       ├── frontend.yml           # lint, typecheck, build, size-limit
│       ├── backend.yml            # ruff, pytest, build docker
│       └── gitleaks.yml           # full-history scan on PR
├── .pre-commit-config.yaml        # gitleaks local hook
├── .gitleaks.toml                 # allowlist .env.example
├── .gitignore                     # .env*, .venv/, node_modules/, .next/
├── .env.example                   # documents required vars
├── CLAUDE.md
├── README.md
├── LICENSES.md                    # stub for Phase 6 (workout asset attribution)
├── .planning/                     # already exists
├── frontend/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── next.config.ts             # Sentry wrapper
│   ├── postcss.config.mjs         # @tailwindcss/postcss
│   ├── tsconfig.json
│   ├── components.json            # shadcn
│   ├── instrumentation.ts         # Sentry register() + onRequestError
│   ├── sentry.server.config.ts
│   ├── sentry.edge.config.ts
│   ├── sentry.client.config.ts    # imported in instrumentation-client.ts
│   ├── middleware.ts              # clerkMiddleware
│   ├── .size-limit.json
│   └── src/
│       ├── app/
│       │   ├── layout.tsx         # <ClerkProvider><Analytics/><SpeedInsights/>
│       │   ├── globals.css        # @import "tailwindcss"; @theme { ... }
│       │   ├── page.tsx           # marketing landing → "Sign in" link
│       │   ├── sign-in/[[...sign-in]]/page.tsx
│       │   ├── sign-up/[[...sign-up]]/page.tsx
│       │   ├── dashboard/page.tsx # server component, fetch /api/me
│       │   └── api/
│       │       ├── me/route.ts            # BFF → Flask /me
│       │       └── webhooks/clerk/route.ts # svix-signed → forward to Flask
│       ├── components/
│       │   └── ui/                # button, card, avatar (shadcn)
│       ├── lib/
│       │   ├── flask-client.ts    # typed fetch wrapper, auto-attaches JWT
│       │   └── env.ts             # zod-validated process.env
│       └── hooks/
├── backend/
│   ├── pyproject.toml             # OR requirements.txt — see decision
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .python-version            # 3.12
│   ├── Dockerfile
│   ├── fly.toml
│   ├── .dockerignore
│   ├── app/
│   │   ├── __init__.py            # create_app()
│   │   ├── config.py              # env vars
│   │   ├── db.py                  # module-level MongoClient singleton
│   │   ├── extensions.py          # sentry_init, cors_init
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth.py            # @require_auth decorator (Clerk JWT verify)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py          # /health
│   │   │   ├── me.py              # /me
│   │   │   └── webhooks.py        # /webhooks/clerk
│   │   ├── services/              # (empty in Phase 1)
│   │   └── models/                # Pydantic User model
│   ├── scripts/
│   │   └── seed_user.py           # one-off seed if needed
│   └── tests/
│       ├── conftest.py            # flask test client fixture
│       ├── test_health.py
│       ├── test_me.py
│       └── test_webhooks.py
└── shared/
    └── schemas/
        └── user.json              # JSON Schema for User (stub for Phase 2)
```

### Pattern 1: BFF (Backend-For-Frontend) JWT forwarding

**What:** Next.js Route Handler reads the Clerk session, mints a short-lived session JWT via `auth().getToken()`, and forwards the request to Flask with `Authorization: Bearer <jwt>`. The browser never holds the JWT — Clerk's session cookie is the only client-side credential.

**When to use:** Every API call from a Next.js client component or server component that needs Flask data.

**Example (`app/api/me/route.ts`):**
```typescript
// Source: clerk.com/docs/nextjs/reference/components/clerk-provider + STACK.md
import { auth } from "@clerk/nextjs/server";

export async function GET() {
  const { userId, getToken } = await auth();
  if (!userId) return new Response("Unauthorized", { status: 401 });

  const token = await getToken(); // Clerk session JWT, ~60s TTL
  const flaskRes = await fetch(`${process.env.BACKEND_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!flaskRes.ok) return new Response("Upstream error", { status: 502 });
  return Response.json(await flaskRes.json());
}
```

### Pattern 2: Networkless Clerk JWT verification in Flask

**What:** `clerk-backend-api`'s `authenticate_request()` verifies the JWT signature against the cached JWKS public key — no per-request call to Clerk API. Latency: ~0.5ms after first call (JWKS cached for 1h).

**When to use:** As a decorator on every protected Flask route.

**Example (`app/middleware/auth.py`):**
```python
# Source: github.com/clerk/clerk-sdk-python README
import os
from functools import wraps
from flask import request, g, jsonify
from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions

_clerk = Clerk(bearer_auth=os.environ["CLERK_SECRET_KEY"])
_authorized_parties = os.environ["CLERK_AUTHORIZED_PARTIES"].split(",")

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # clerk-backend-api accepts httpx.Request; Flask's request has the same
        # attrs needed (.url, .headers, .method) — pass-through works in practice.
        # Recommended canonical form: build an httpx.Request from flask's request.
        import httpx
        httpx_req = httpx.Request(
            method=request.method,
            url=request.url,
            headers=dict(request.headers),
        )
        state = _clerk.authenticate_request(
            httpx_req,
            AuthenticateRequestOptions(authorized_parties=_authorized_parties),
        )
        if not state.is_signed_in:
            return jsonify({"error": "unauthorized"}), 401
        g.clerk_user_id = state.payload["sub"]
        return f(*args, **kwargs)
    return wrapper
```

### Pattern 3: PyMongo singleton (one client per process)

**What:** A module-level `MongoClient` shared by every Flask request handler in the process. Pymongo's client is thread-safe and internally pooled; `maxPoolSize=10` caps connections at 10 per Gunicorn worker, so 2 workers × 10 = 20 connections, well within Atlas M0's 500 limit.

**Example (`app/db.py`):**
```python
# Source: pymongo.readthedocs.io/en/stable/faq.html#how-does-connection-pooling-work-in-pymongo
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

_client = MongoClient(
    os.environ["MONGODB_URI"],
    maxPoolSize=10,
    serverSelectionTimeoutMS=5000,
    tls=True,
    server_api=ServerApi("1"),
)
db = _client.fitgh
users = db.users
# eager-fail at startup if Atlas unreachable:
_client.admin.command("ping")
```

### Anti-Patterns to Avoid

- **`MongoClient(uri)` inside a route handler.** Spawns a fresh pool per request → connection storm. (Pitfall **M-2**.)
- **Wildcard CORS with credentials.** `CORS(app, origins="*", supports_credentials=True)` is invalid per spec; some impls silently weaken security. Use an explicit list. (SEC-03.)
- **Reading `request.headers["X-User-Id"]` for identity.** Anyone can fake it. Use the `@require_auth` decorator. (Pitfall **S-1**.)
- **Storing Clerk JWT in localStorage on the browser.** Clerk uses an httpOnly cookie by design; never copy the token client-side.
- **Allowing `0.0.0.0/0` in Atlas allowlist in production.** Acceptable in dev only with a strong DB password. (Pitfall **M-1**; SEC-04 demands the static egress IP.)
- **Tailwind v4 with `tailwind.config.js`.** v4 is CSS-first; configure via `@theme` in `globals.css`. A v3-style JS config will silently fail to apply.
- **Forgetting `.next/` in `.gitignore`.** Vercel builds will commit stale artifacts that pollute size-limit measurements.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| User sign-in / sign-up UI | Custom forms + bcrypt + cookie code | `<SignIn/>` + `<SignUp/>` from `@clerk/nextjs` | OAuth dance, password reset, MFA, passkeys are all solved problems with 100+ edge cases. Clerk's 50k-MAU free tier covers any v1 ceiling. |
| JWT verification on Flask | `pyjwt` + manual JWKS fetch + caching | `clerk-backend-api`'s `authenticate_request()` | Caches JWKS, validates `iss`/`aud`/`exp`/`nbf`/authorized_parties, handles key rotation. |
| Webhook signature verification | Custom HMAC | `svix` Python SDK | Clerk uses svix; the SDK handles timestamp tolerance + replay prevention. |
| MongoDB connection pool | Custom retry / backoff / pool management | PyMongo's built-in `MongoClient` with `maxPoolSize` | Battle-tested driver; module-level singleton is the documented pattern. |
| Error capture | Custom log shipping | Sentry SDKs (FE + BE) | Releases, source maps, breadcrumbs, sampling — all free-tier covered. |
| CORS | Manual response headers | `flask-cors` | Preflight handling, header allowlist, credentials math. |
| Bundle size budget enforcement | Custom CI script parsing `next build` output | `size-limit` + `size-limit-action` | Posts PR comments with diff; gzip-aware; preset for App Router. |
| Secret scanning | Custom regex grep | `gitleaks` via `pre-commit` | Curated 60+ rule pack covers Mongo URIs, Clerk keys, AWS, Stripe, etc. |
| Fly.io healthcheck loop | Manual cron pinging `/health` | `[[http_service.checks]]` in `fly.toml` | Built-in; ties into Fly's machine lifecycle (auto-restart on N consecutive failures). |
| Vercel RUM beacon | Custom Web Vitals reporter | `@vercel/analytics` + `@vercel/speed-insights` | Free on Hobby; one-line install. |

**Key insight:** Phase 1 is a *plumbing phase* — every line of hand-rolled auth, CORS, or Mongo wiring is a future bug. Lean on the SaaS+SDK stack. The only original code in this phase is glue (one Flask `__init__.py`, one decorator, one route handler, one BFF route, three React server components).

---

## Per-Section Recipes

### 1. Monorepo Setup

**Recommendation:** **Plain monorepo, no pnpm workspaces.** Only `/frontend` is JavaScript; `/backend` is Python; `/shared` is JSON-only. Workspaces would buy nothing here and force Vercel's "Include source files outside Root Directory" toggle, plus a root `package.json` no one needs. Re-evaluate only if Phase 5 introduces a sibling JS package (e.g., a Rive runtime fork).

`[ASSUMED]` — verify with the user during planning. Bypass condition: if the team prefers a single `pnpm install` from the repo root for editor tooling, switch to workspaces and accept the Vercel toggle.

**Root files (concrete):**

`.gitignore`:
```gitignore
# Node
node_modules/
.next/
.turbo/
pnpm-debug.log

# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Env
.env
.env.local
.env.*.local
!.env.example

# Build / OS
dist/
build/
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/

# Fly
fly.toml.bak
```

`.env.example` (committed):
```bash
# === Clerk ===
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/dashboard
CLERK_WEBHOOK_SECRET=whsec_...

# === Backend wiring ===
BACKEND_URL=http://localhost:8080

# === Flask (backend/.env.local; never commit) ===
MONGODB_URI=mongodb+srv://fitgh-app:<password>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://fitgh.vercel.app
CLERK_SECRET_KEY=sk_test_...
CLERK_AUTHORIZED_PARTIES=http://localhost:3000,https://fitgh.vercel.app
CLERK_WEBHOOK_SECRET=whsec_...

# === Observability (set in Vercel + Fly secrets in prod) ===
NEXT_PUBLIC_SENTRY_DSN=https://...@o.../...
SENTRY_DSN_BACKEND=https://...@o.../...
SENTRY_ORG=fitgh
SENTRY_PROJECT_FE=fitgh-frontend
SENTRY_PROJECT_BE=fitgh-backend
SENTRY_AUTH_TOKEN=sntrys_...
```

`.nvmrc`:
```
20
```

`README.md` (top-level — short, points to `.planning/`):
```md
# FitGH

See `.planning/PROJECT.md` and `.planning/ROADMAP.md`.

## Local dev

```bash
# Frontend
cd frontend && pnpm install && pnpm dev

# Backend
cd backend && python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# bash:    source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --port 8080
```
```

**Confidence:** **HIGH** on "no workspaces" recommendation given current scope. MEDIUM on `.nvmrc=20` — Next 15 supports Node 18+, but pnpm and `@sentry/nextjs` 10 are happiest on Node 20.

---

### 2. Next.js 15 + Tailwind v4 + shadcn/ui Scaffold

**Single command (from inside `fitgh/`):**
```bash
mkdir frontend && cd frontend
pnpm create next-app@latest . \
  --typescript \
  --tailwind \
  --app \
  --eslint \
  --src-dir \
  --import-alias "@/*" \
  --use-pnpm \
  --turbopack
```

When the create-next-app wizard asks the questions interactively (the flags above pass them all non-interactively), confirm: App Router=Yes, Turbopack=Yes (default Next 15.2+), Tailwind=Yes, src=Yes, ESLint=Yes.

**What it produces** (verified against shadcn/ui Next.js install docs):
- `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`
- `tsconfig.json` with `"@/*"` alias
- `next.config.ts`
- `postcss.config.mjs` with `@tailwindcss/postcss` (Tailwind v4)
- `eslint.config.mjs`
- `.gitignore` — extend with the root `.gitignore` patterns above

**Tailwind v4 — sanity check `postcss.config.mjs`:**
```js
// Source: tailwindcss.com/docs/installation/using-postcss
const config = {
  plugins: { "@tailwindcss/postcss": {} },
};
export default config;
```

**`globals.css` (Tailwind v4 CSS-first config):**
```css
/* Source: tailwindcss.com/blog/tailwindcss-v4 */
@import "tailwindcss";

@theme {
  --color-brand-50: #f0fdf4;
  --color-brand-500: #22c55e;
  --color-brand-700: #15803d;
  --font-display: "Inter", ui-sans-serif, system-ui, sans-serif;
}

/* shadcn/ui base layer is injected by `shadcn init` */
```

**shadcn/ui init (after `create-next-app`):**
```bash
pnpm dlx shadcn@latest init
# Pick: style=Default (or New York), base color=Zinc, CSS variables=Yes
pnpm dlx shadcn@latest add button card avatar sonner
```

Phase 1 components to add: `button`, `card`, `avatar`, `sonner` (toast). Defer `form`, `input`, `label`, `dialog`, `sheet`, `tabs`, `chart` to Phase 2 (forms) / Phase 5 (charts) — keeping the Phase 1 bundle as light as possible for PERF-01.

**`components.json` (produced by shadcn init; verify it points at Tailwind v4):**
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  }
}
```

**Smoke test:**
```bash
pnpm dev
# visit http://localhost:3000 → should see the default Next.js page
# add a <Button>Test</Button> from @/components/ui/button to verify shadcn
```

**Confidence:** **HIGH** — verified against shadcn/ui official docs and Tailwind v4 install guide.

**Sources:** [shadcn/ui Next.js install (2026)](https://ui.shadcn.com/docs/installation/next), [Tailwind v4 PostCSS install](https://tailwindcss.com/docs/installation/using-postcss), [Tailwind v4 launch blog](https://tailwindcss.com/blog/tailwindcss-v4).

---

### 3. Clerk — FE + BE Integration

#### 3.1 Install (frontend)

```bash
cd frontend
pnpm add @clerk/nextjs
```

#### 3.2 `.env.local` (frontend)

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/dashboard
CLERK_WEBHOOK_SECRET=whsec_...
BACKEND_URL=http://localhost:8080
```

#### 3.3 `middleware.ts` (project root, NOT inside `src/`)

```typescript
// Source: clerk.com/docs/reference/nextjs/clerk-middleware
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks/clerk", // Clerk hits this with svix-signed payloads
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals & all static files unless found in search params
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
```

#### 3.4 `app/layout.tsx`

```tsx
// Source: clerk.com/docs/nextjs/reference/components/clerk-provider
import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitGH",
  description: "Snap a meal, see kcal in seconds.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          {children}
          <Analytics />
          <SpeedInsights />
        </body>
      </html>
    </ClerkProvider>
  );
}
```

#### 3.5 Catch-all sign-in and sign-up pages

`src/app/sign-in/[[...sign-in]]/page.tsx`:
```tsx
import { SignIn } from "@clerk/nextjs";
export default function Page() {
  return (
    <main className="grid min-h-dvh place-items-center p-6">
      <SignIn />
    </main>
  );
}
```

`src/app/sign-up/[[...sign-up]]/page.tsx`:
```tsx
import { SignUp } from "@clerk/nextjs";
export default function Page() {
  return (
    <main className="grid min-h-dvh place-items-center p-6">
      <SignUp />
    </main>
  );
}
```

Why optional catch-all (`[[...sign-in]]`): Clerk inserts multi-step flows (email verification, MFA, password reset) under the same path; catch-all routes match them all without manual sub-routes.

#### 3.6 `/dashboard` server component

`src/app/dashboard/page.tsx`:
```tsx
import { auth } from "@clerk/nextjs/server";
import { UserButton } from "@clerk/nextjs";
import { redirect } from "next/navigation";

async function getMe() {
  const { getToken } = await auth();
  const token = await getToken();
  const res = await fetch(`${process.env.BACKEND_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Flask /me returned ${res.status}`);
  return res.json() as Promise<{ email: string }>;
}

export default async function DashboardPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");
  const me = await getMe();
  return (
    <main className="mx-auto max-w-2xl p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">FitGH</h1>
        <UserButton />
      </header>
      <section className="mt-8">
        <p className="text-sm text-zinc-500">Signed in as</p>
        <p className="text-lg">{me.email}</p>
      </section>
    </main>
  );
}
```

#### 3.7 BFF route handler (alternative if you prefer fetching from a client component)

`src/app/api/me/route.ts`:
```typescript
import { auth } from "@clerk/nextjs/server";

export async function GET() {
  const { userId, getToken } = await auth();
  if (!userId) return new Response("Unauthorized", { status: 401 });
  const token = await getToken();
  const res = await fetch(`${process.env.BACKEND_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  return new Response(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
```

#### 3.8 Flask side — install & decorator

```bash
cd backend
pip install "clerk-backend-api>=5.0.6"
```

`backend/app/middleware/auth.py`:
```python
# Source: github.com/clerk/clerk-sdk-python README + STACK.md
import os
from functools import wraps
import httpx
from flask import request, g, jsonify
from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions

_clerk = Clerk(bearer_auth=os.environ["CLERK_SECRET_KEY"])
_authorized_parties = [p.strip() for p in os.environ["CLERK_AUTHORIZED_PARTIES"].split(",")]

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        httpx_req = httpx.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
        )
        state = _clerk.authenticate_request(
            httpx_req,
            AuthenticateRequestOptions(authorized_parties=_authorized_parties),
        )
        if not state.is_signed_in:
            return jsonify({"error": "unauthorized", "reason": state.reason}), 401
        g.clerk_user_id = state.payload.get("sub")
        return f(*args, **kwargs)
    return wrapper
```

`backend/app/routes/me.py`:
```python
from flask import Blueprint, g, jsonify
from app.db import users
from app.middleware.auth import require_auth

bp = Blueprint("me", __name__)

@bp.get("/me")
@require_auth
def get_me():
    user = users.find_one({"clerk_id": g.clerk_user_id})
    if not user:
        return jsonify({"error": "user_not_found"}), 404
    return jsonify({"email": user["email"]})
```

#### 3.9 Clerk webhook handler (creates Mongo user record)

In Clerk dashboard → Webhooks → "Add endpoint" → URL: `https://fitgh.vercel.app/api/webhooks/clerk` → events: `user.created`, `user.deleted`. Copy the **signing secret** to `CLERK_WEBHOOK_SECRET`.

**Decision: forward through Next.js BFF or hit Flask directly?**

**Recommendation: Next.js Route Handler forwards to Flask.** Two reasons:
1. Vercel handles TLS termination + DDoS edge for free; pointing Clerk straight at Fly works but exposes the Fly hostname to the public webhook URL.
2. Easier to test locally with `vercel dev` than with `flask run`.

`src/app/api/webhooks/clerk/route.ts`:
```typescript
// Source: clerk.com/docs/guides/development/webhooks/syncing
import { Webhook } from "svix";

export async function POST(req: Request) {
  const secret = process.env.CLERK_WEBHOOK_SECRET!;
  const headers = {
    "svix-id": req.headers.get("svix-id")!,
    "svix-timestamp": req.headers.get("svix-timestamp")!,
    "svix-signature": req.headers.get("svix-signature")!,
  };
  const body = await req.text();

  let evt: { type: string; data: Record<string, unknown> };
  try {
    evt = new Webhook(secret).verify(body, headers) as typeof evt;
  } catch {
    return new Response("Invalid signature", { status: 400 });
  }

  // Forward verified event to Flask
  const res = await fetch(`${process.env.BACKEND_URL}/webhooks/clerk`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-clerk-verified": "true" },
    body: JSON.stringify(evt),
  });
  return new Response(null, { status: res.ok ? 200 : 502 });
}
```

```bash
cd frontend && pnpm add svix
```

`backend/app/routes/webhooks.py`:
```python
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.db import users

bp = Blueprint("webhooks", __name__)

@bp.post("/webhooks/clerk")
def clerk_webhook():
    # Next.js already svix-verified. Confirm header is present.
    if request.headers.get("x-clerk-verified") != "true":
        return jsonify({"error": "unverified"}), 400

    evt = request.get_json()
    evt_type = evt.get("type")
    data = evt.get("data", {})

    if evt_type == "user.created":
        clerk_id = data["id"]
        email = data["email_addresses"][0]["email_address"] if data.get("email_addresses") else None
        now = datetime.now(timezone.utc)
        users.update_one(
            {"clerk_id": clerk_id},
            {
                "$setOnInsert": {
                    "clerk_id": clerk_id,
                    "email": email,
                    "created_at": now,
                },
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
        return jsonify({"ok": True}), 201

    if evt_type == "user.deleted":
        users.delete_one({"clerk_id": data["id"]})
        return jsonify({"ok": True}), 200

    return jsonify({"ignored": evt_type}), 200
```

#### 3.10 Clerk dashboard configuration checklist (Phase 1)

In the Clerk dashboard:
1. **Application** → Settings → Application name = "FitGH" — keep Development + Production instances separate.
2. **Authentication** → Email, Password — enable. **OAuth** → Google — enable, leave other providers off.
3. **Sessions** → Session lifetime: default 7 days; **Single session per user: off** (allow mobile + desktop).
4. **Paths** → Sign-in URL = `/sign-in`, Sign-up URL = `/sign-up`, After sign-in URL = `/dashboard`, After sign-up URL = `/dashboard`.
5. **Domains** → Add `fitgh.vercel.app` to authorized parties for production; `localhost:3000` for dev.
6. **JWT templates** — **NOT NEEDED in Phase 1.** Default Clerk session JWT carries `sub` (Clerk user id) which is all we use.
7. **Webhooks** → endpoint = `https://fitgh.vercel.app/api/webhooks/clerk`, events = `user.created`, `user.deleted`. Copy signing secret.

**Confidence:** **HIGH** — Clerk patterns verified against official docs.

**Sources:** [Clerk Next.js quickstart](https://clerk.com/docs/nextjs/getting-started/quickstart), [clerkMiddleware reference](https://clerk.com/docs/reference/nextjs/clerk-middleware), [custom sign-in page](https://clerk.com/docs/nextjs/guides/development/custom-sign-in-or-up-page), [Clerk Python SDK README](https://github.com/clerk/clerk-sdk-python), [Clerk webhooks syncing](https://clerk.com/docs/guides/development/webhooks/syncing).

---

### 4. Flask 3.1 Backend

#### 4.1 Project layout (recap)

```
backend/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .python-version       (3.12.7)
├── Dockerfile
├── fly.toml
├── .dockerignore
├── app/
│   ├── __init__.py       # create_app() factory
│   ├── config.py
│   ├── db.py             # singleton MongoClient
│   ├── extensions.py     # cors_init, sentry_init
│   ├── middleware/auth.py
│   ├── routes/{health,me,webhooks}.py
│   └── models/user.py
└── tests/
```

#### 4.2 `pyproject.toml` vs `requirements.txt`

**Recommendation: `requirements.txt` (+ `requirements-dev.txt`) for Phase 1, add `pyproject.toml` in Phase 3 when the package grows.**

Reasons:
- Fly.io's default buildpack and `python:3.12-slim` Docker images both consume `requirements.txt` natively.
- No publishable package; no lockfile dance with Poetry/uv adds value here.
- Phase 3 (when Flask grows real services) is when `pyproject.toml` (PEP 621) earns its keep for `ruff`, `pytest`, `mypy` config.

`requirements.txt`:
```
flask>=3.1,<4
gunicorn>=25.1
flask-cors>=5
pymongo>=4.13,<5
pydantic>=2.9,<3
clerk-backend-api>=5.0.6
svix>=1.30
python-dotenv>=1.0
sentry-sdk[flask]>=2.53
```

`requirements-dev.txt`:
```
-r requirements.txt
pytest>=8
pytest-flask>=1.3
ruff>=0.6
mypy>=1.10
mongomock>=4.2
respx>=0.21    # mock httpx (for testing Clerk JWT verification offline)
```

#### 4.3 App factory (`app/__init__.py`)

```python
# Source: flask.palletsprojects.com (factory pattern) + STACK.md
import os
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config["CORS_ORIGINS"] = [
        o.strip() for o in os.environ["CORS_ALLOWED_ORIGINS"].split(",")
    ]

    # Sentry (must be initialised before flask app creation if possible,
    # but FlaskIntegration() auto-patches when init runs after app creation too)
    from app.extensions import sentry_init
    sentry_init()

    # CORS: explicit origins, no wildcard with credentials
    CORS(
        app,
        resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,   # we use Authorization bearer; no cookies
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    )

    # Eager-fail on Mongo unreachable so /health surface is honest
    from app.db import client as _mongo  # noqa: F401 — imports trigger ping

    from app.routes import health, me, webhooks
    app.register_blueprint(health.bp)
    app.register_blueprint(me.bp)
    app.register_blueprint(webhooks.bp)

    return app
```

#### 4.4 `app/db.py` — singleton MongoClient

```python
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

client = MongoClient(
    os.environ["MONGODB_URI"],
    maxPoolSize=10,
    serverSelectionTimeoutMS=5000,
    tls=True,
    server_api=ServerApi("1"),
)
db = client.fitgh
users = db.users

# Index management — idempotent; safe to call on every boot
users.create_index("clerk_id", unique=True)
users.create_index("email", unique=True)

# Verify connectivity at import time so /health is honest
client.admin.command("ping")
```

#### 4.5 `app/extensions.py` — Sentry init with PII scrubber

```python
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.pymongo import PyMongoIntegration

_PII_KEYS = {"email", "image_bytes", "kcal", "kcal_total", "daily_total"}

def _scrub(event, _hint):
    # 1. Drop default user identity entirely (no email, no IP).
    event.pop("user", None)

    # 2. Strip known sensitive keys from request data and breadcrumbs.
    if "request" in event:
        for section in ("data", "query_string", "headers", "cookies"):
            v = event["request"].get(section)
            if isinstance(v, dict):
                for k in list(v.keys()):
                    if k.lower() in _PII_KEYS:
                        v[k] = "[Scrubbed]"

    for crumb in event.get("breadcrumbs", {}).get("values", []) or []:
        data = crumb.get("data")
        if isinstance(data, dict):
            for k in list(data.keys()):
                if k.lower() in _PII_KEYS:
                    data[k] = "[Scrubbed]"
    return event

def sentry_init():
    dsn = os.environ.get("SENTRY_DSN_BACKEND")
    if not dsn:
        return  # skip in local dev unless explicitly set
    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration(), PyMongoIntegration()],
        send_default_pii=False,
        traces_sample_rate=0.1,
        before_send=_scrub,
        release=os.environ.get("FLY_IMAGE_REF", "dev"),
        environment=os.environ.get("FLY_APP_NAME", "dev"),
    )
```

#### 4.6 `/health` route

```python
# app/routes/health.py
from flask import Blueprint, jsonify
from app.db import client

bp = Blueprint("health", __name__)

@bp.get("/health")
def health():
    try:
        client.admin.command("ping")
        return jsonify({"ok": True, "mongo": "connected"}), 200
    except Exception as exc:
        return jsonify({"ok": False, "mongo": "down", "error": str(exc)}), 503
```

#### 4.7 Gunicorn command (Fly.io)

```bash
gunicorn 'app:create_app()' \
  --bind 0.0.0.0:8080 \
  --workers 2 \
  --threads 4 \
  --worker-class gthread \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
```

`--workers 2` × `--threads 4` × `maxPoolSize=10` = at most 80 simultaneous request slots / 20 Mongo connections per container — well within Atlas M0's 500-connection cap.

`--timeout 60` — Phase 1 only needs ~5s, but Phase 4 vision endpoint will need ≥30s. Set high now to avoid forgetting.

#### 4.8 Local dev runner

```bash
cd backend && source .venv/bin/activate
export FLASK_APP="app:create_app()"
export FLASK_DEBUG=1
flask run --port 8080
```

**Confidence:** **HIGH** — well-trodden Flask 3.1 factory pattern + verified Sentry scrubber syntax.

**Sources:** [PyMongo singleton FAQ](https://pymongo.readthedocs.io/en/stable/faq.html), [Sentry Flask integration](https://docs.sentry.io/platforms/python/integrations/flask/), [Sentry sensitive data scrubbing](https://docs.sentry.io/platforms/python/guides/flask/data-management/sensitive-data/), [Flask-CORS docs](https://flask-cors.readthedocs.io/).

---

### 5. MongoDB Atlas — Phase 1

#### 5.1 Rotate the exposed password (FIRST — SEC-02 is a launch blocker)

In Atlas UI → Cluster0 → Database Access:

1. Locate the existing user that owns the leaked password (likely the default `fitgh-admin` or similar created during initial Atlas setup).
2. Click **Edit** → **Edit Password** → click **Autogenerate Secure Password** → click **Copy** → click **Update User**.
3. **Do not paste the password into chat or commit it.**
4. Either:
   - **Recommended:** Delete this user entirely and create a fresh least-privilege user (see 5.2).
   - **Or:** Keep the user but immediately scope its role down per 5.2.

#### 5.2 Create a least-privilege application user

Atlas UI → Database Access → **Add New Database User**:

| Field | Value |
|-------|-------|
| Authentication method | Password |
| Username | `fitgh-app` |
| Password | (autogenerated, store in 1Password / Fly secrets only) |
| Database User Privileges | **Built-in role:** `readWrite` — **scoped to specific database** `fitgh` |
| Resources | Cluster0 → Database = `fitgh` |
| Restrict access to specific clusters/projects | Cluster0 only |

**Do NOT pick `atlasAdmin` or `dbAdmin`.** `readWrite@fitgh` is the entire required surface.

Verify the user can:
- `find`, `insert`, `update`, `delete`, `createIndex` against `fitgh.*`

And **cannot**:
- Read/write any other database
- Modify cluster settings
- Read Atlas audit logs

CLI equivalent (Atlas CLI):
```bash
atlas dbusers create \
  --username fitgh-app \
  --password "$(openssl rand -base64 24)" \
  --role readWrite@fitgh \
  --projectId <project-id>
```

#### 5.3 IP allowlist — pinning Fly.io's static egress IP

Atlas UI → Network Access → **Add IP Address**.

After Section 6 has provisioned the static egress IP (e.g., `137.66.27.45`), add it here as a `/32`:

```
137.66.27.45/32   Comment: Fly.io jnb fitgh-api
```

Add a second entry only if a second machine in a different region is later spun up.

For local dev, **temporarily** add your home IP (use "Add Current IP") with a comment + expiry date. **Do not** leave `0.0.0.0/0` in production.

#### 5.4 Connection string format (post-rotation)

```
mongodb+srv://fitgh-app:<URL-encoded-password>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority&appName=fitgh-api
```

The trailing `appName=fitgh-api` shows up in Atlas Performance Advisor and aids debugging.

#### 5.5 First-run seeding (one-off)

Phase 1 doesn't strictly need seed data — the Clerk webhook creates the first user on first sign-up. If you want to test `/me` against a pre-existing record before wiring webhooks, run:

`backend/scripts/seed_user.py`:
```python
import os
from datetime import datetime, timezone
from pymongo import MongoClient

client = MongoClient(os.environ["MONGODB_URI"])
client.fitgh.users.update_one(
    {"clerk_id": "user_test_seed"},
    {"$setOnInsert": {
        "clerk_id": "user_test_seed",
        "email": "test@example.com",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }},
    upsert=True,
)
print("Seeded.")
```

**Confidence:** **HIGH** — verified against Atlas docs.

**Sources:** [Atlas user roles](https://www.mongodb.com/docs/atlas/reference/user-roles/), [Atlas least-privilege patterns 2026](https://oneuptime.com/blog/post/2026-03-31-mongodb-atlas-access-roles-permissions/view), [Atlas free cluster limits](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/).

---

### 6. Fly.io — JNB Deploy

#### 6.1 Install Fly CLI

```bash
# macOS
brew install flyctl
# Linux
curl -L https://fly.io/install.sh | sh
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

fly auth login
```

#### 6.2 `fly.toml` (place in `backend/`)

```toml
# fly.toml app configuration file for FitGH backend
# Generated, then trimmed to Phase 1 needs.
app = "fitgh-api"
primary_region = "jnb"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"
  PYTHONUNBUFFERED = "1"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "off"          # always-on per DEPLOY-02
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  protocol = "http"
  timeout = "5s"

[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"
  cpus = 1

[processes]
  app = "gunicorn 'app:create_app()' --bind 0.0.0.0:8080 --workers 2 --threads 4 --worker-class gthread --timeout 60 --access-logfile - --error-logfile -"
```

#### 6.3 `Dockerfile` (place in `backend/`)

```dockerfile
# Source: github.com/fly-apps/hello-gunicorn-flask (adapted for Python 3.12)
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build deps only if any package needs compilation; keep slim.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

# Non-root user for security
RUN useradd --create-home --shell /bin/bash flask
USER flask

EXPOSE 8080

CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--worker-class", "gthread", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
```

`.dockerignore`:
```
.venv/
__pycache__/
*.pyc
tests/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
.env.*
fly.toml.bak
```

**Recommendation:** Single-stage `python:3.12-slim`. Multi-stage would shave ~30 MB but not enough to matter on Fly.io. Distroless adds complexity (no shell for `fly ssh console`).

#### 6.4 Launch and deploy

```bash
cd backend
# Initialize Fly app (no detect — we have our own fly.toml + Dockerfile)
fly launch --no-deploy --copy-config --name fitgh-api --region jnb --org personal

# Set secrets BEFORE first deploy so the app boots cleanly
fly secrets set \
  MONGODB_URI="mongodb+srv://fitgh-app:<password>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority&appName=fitgh-api" \
  CLERK_SECRET_KEY="sk_live_..." \
  CLERK_AUTHORIZED_PARTIES="https://fitgh.vercel.app" \
  CLERK_WEBHOOK_SECRET="whsec_..." \
  CORS_ALLOWED_ORIGINS="https://fitgh.vercel.app" \
  SENTRY_DSN_BACKEND="https://...@o.../..."

fly deploy
```

#### 6.5 Allocate the static egress IP

Verified 2026 command (note: the old `fly ips allocate-v4 --shared` flow was replaced):

```bash
# Allocate one app-scoped egress IPv4 in jnb (free IPv6 included)
fly ips allocate-egress --app fitgh-api -r jnb

# View it
fly ips list
```

**Cost (verified 2026-05):** **$3.60/mo per app-scoped IPv4** (IPv6 free). Billing started Jan 1, 2026; the November 2025 beta period was free.

`[CITED: https://community.fly.io/t/billing-for-app-scoped-egress-ips-starts-jan-1-2026/26686]`
`[CITED: https://fly.io/docs/networking/egress-ips/]`

If $3.60/mo is unacceptable, fallback is `0.0.0.0/0` in Atlas allowlist + strong DB password + `tls=True` — **explicitly noted as dev-only** in PROJECT.md and SEC-04, so this MUST be revisited before opening prod sign-ups.

#### 6.6 Pin the IP in Atlas

```bash
# Capture the egress IPv4 from `fly ips list`
EGRESS_IP=$(fly ips list --json | jq -r '.[] | select(.Type=="egress" and .Region=="jnb") | .Address')
echo "Add to Atlas allowlist: $EGRESS_IP/32"
```

Then Atlas UI → Network Access → Add IP Address → `<EGRESS_IP>/32` with comment `Fly.io jnb fitgh-api`.

#### 6.7 Verify

```bash
fly status              # Machine should be "started", region jnb
curl https://fitgh-api.fly.dev/health
# expect: {"ok":true,"mongo":"connected"}
fly logs                # Watch for cold-start errors
```

#### 6.8 Future deploys via CI

For Phase 1, manual `fly deploy` is acceptable. A `deploy-backend.yml` workflow that runs `superfly/flyctl-actions@v1` on push-to-main is a Phase 7 hardening item (token in `FLY_API_TOKEN` GitHub secret).

**Confidence:** **HIGH** on Fly commands. **MEDIUM** on long-term `jnb` capacity — it's been a "regular" region for years but verify on `fly platform regions` that it accepts new apps right now.

**Sources:** [Fly.io egress IPs docs](https://fly.io/docs/networking/egress-ips/), [App-scoped egress IP billing 2026](https://community.fly.io/t/billing-for-app-scoped-egress-ips-starts-jan-1-2026/26686), [Fly pricing](https://fly.io/docs/about/pricing/), [Fly health checks](https://fly.io/docs/reference/health-checks/), [hello-gunicorn-flask example](https://github.com/fly-apps/hello-gunicorn-flask).

---

### 7. Vercel Monorepo Deploy

#### 7.1 Project import settings

In Vercel dashboard → **Add New** → **Project** → import the GitHub repo. On the configure screen:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Next.js (auto-detected from `frontend/package.json`) |
| **Root Directory** | `frontend` |
| **Include source files outside of the Root Directory** | **No** (we don't have a workspace root; `shared/` files are read at runtime through git, not at build time in v1) |
| **Build Command** | `pnpm build` (default) |
| **Output Directory** | `.next` (default) |
| **Install Command** | `pnpm install` (default — pnpm auto-detected from `pnpm-lock.yaml`) |
| **Development Command** | `pnpm dev` |
| **Node.js Version** | 20.x |

#### 7.2 pnpm detection

Vercel detects pnpm automatically when `frontend/pnpm-lock.yaml` exists. Make sure to commit the lockfile.

#### 7.3 Environment variables (Vercel dashboard → Settings → Environment Variables)

Set for **Production** and **Preview** (different values per environment is fine):

| Name | Value | Scope |
|------|-------|-------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_live_...` (prod) / `pk_test_...` (preview) | Production + Preview |
| `CLERK_SECRET_KEY` | `sk_live_...` (prod) / `sk_test_...` (preview) | Production + Preview |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/sign-in` | All |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/sign-up` | All |
| `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL` | `/dashboard` | All |
| `NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL` | `/dashboard` | All |
| `CLERK_WEBHOOK_SECRET` | `whsec_...` | Production |
| `BACKEND_URL` | `https://fitgh-api.fly.dev` (prod) / `https://fitgh-api-preview.fly.dev` (preview) | Production + Preview |
| `NEXT_PUBLIC_SENTRY_DSN` | `https://...@o.../...` (FE DSN) | All |
| `SENTRY_AUTH_TOKEN` | `sntrys_...` (for source-map upload) | All |
| `SENTRY_ORG` | `fitgh` | All |
| `SENTRY_PROJECT_FE` | `fitgh-frontend` | All |

For local dev, mirror these in `frontend/.env.local` (gitignored).

#### 7.4 Preview deploy on PR

Vercel does this by default for every PR. No extra config — every PR gets a `https://fitgh-git-<branch>-<team>.vercel.app` preview. **Note:** Clerk requires the preview origin in authorized parties — easiest workaround is to use Clerk **Development** instance for previews and **Production** instance only for `main`.

#### 7.5 Vercel Analytics + Speed Insights install

```bash
cd frontend
pnpm add @vercel/analytics @vercel/speed-insights
```

Add to `app/layout.tsx` (already shown in Section 3.4):
```tsx
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
// inside <body>:
<Analytics />
<SpeedInsights />
```

Both are no-ops in development; they ship telemetry only on `vercel.app` and custom domains.

Finally: in Vercel dashboard → project → **Analytics** tab → enable. **Speed Insights** tab → enable. Both are free on Hobby.

**Confidence:** **HIGH**.

**Sources:** [Vercel monorepo docs](https://vercel.com/docs/monorepos), [Vercel Analytics quickstart](https://vercel.com/docs/analytics/quickstart), [Speed Insights quickstart](https://vercel.com/docs/speed-insights/quickstart).

---

### 8. Sentry FE + BE

#### 8.1 Frontend install

```bash
cd frontend
pnpm add @sentry/nextjs
pnpm dlx @sentry/wizard@latest -i nextjs --saas
```

The wizard creates: `instrumentation.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`, `instrumentation-client.ts`, wraps `next.config.ts` with `withSentryConfig`, and prompts for the DSN + auth token.

#### 8.2 `instrumentation.ts` (root of `frontend/`, NOT `src/`)

```typescript
// Source: docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/
import * as Sentry from "@sentry/nextjs";

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}

export const onRequestError = Sentry.captureRequestError;
```

#### 8.3 `sentry.server.config.ts`

```typescript
import * as Sentry from "@sentry/nextjs";

const PII_KEYS = new Set(["email", "image_bytes", "kcal", "kcal_total"]);

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  sendDefaultPii: false,
  beforeSend(event) {
    // strip user identity entirely
    if (event.user) delete event.user;

    // scrub request data
    if (event.request?.data && typeof event.request.data === "object") {
      for (const k of Object.keys(event.request.data as Record<string, unknown>)) {
        if (PII_KEYS.has(k.toLowerCase())) {
          (event.request.data as Record<string, unknown>)[k] = "[Scrubbed]";
        }
      }
    }
    return event;
  },
});
```

`sentry.client.config.ts` and `sentry.edge.config.ts` follow the same shape but with `tracesSampleRate: 0.05` on the client to keep traces cheap.

#### 8.4 `next.config.ts` wrap

```typescript
// Source: docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/
import { withSentryConfig } from "@sentry/nextjs";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ...
};

export default withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT_FE,
  silent: !process.env.CI,
  widenClientFileUpload: true,
  hideSourceMaps: true,           // remove source maps from client bundle
  disableLogger: true,            // tree-shake Sentry's logger statements
  automaticVercelMonitors: false, // not needed Phase 1
});
```

#### 8.5 Backend Sentry — already shown in Section 4.5

Recap of the `before_send` scrubber for OBS-01 compliance:
- Drops `event.user` entirely (no email, no IP, no username).
- Replaces values for keys in `{email, image_bytes, kcal, kcal_total, daily_total}` with `[Scrubbed]` across request data and breadcrumbs.
- `send_default_pii=False` is the master switch.

#### 8.6 Free tier limits (verified 2026-05)

| Plan | Errors/mo | Performance events/mo | Replays/mo |
|------|-----------|------------------------|------------|
| **Developer (free)** | 5,000 | 10,000 | 50 |

`[CITED: https://nurbak.com/en/blog/sentry-pricing/]` — Verify on the [Sentry pricing page](https://sentry.io/pricing/) at sign-up; free tier numbers periodically change.

Phase 1 will burn ~0 errors/mo. The free tier becomes a constraint only after Phase 4 launches to a seed cohort.

**Confidence:** **HIGH** on FE/BE code; **MEDIUM** on the exact free-tier quotas (verify in Sentry dashboard at signup).

**Sources:** [Sentry Next.js docs](https://docs.sentry.io/platforms/javascript/guides/nextjs/), [Manual setup](https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/), [Flask sensitive data scrubbing](https://docs.sentry.io/platforms/python/guides/flask/data-management/sensitive-data/), [Sentry options reference](https://docs.sentry.io/platforms/python/configuration/options/).

---

### 9. CI Bundle-Size Gate (PERF-01)

#### 9.1 Tool choice

| Tool | Verdict |
|------|---------|
| **`size-limit` + `@size-limit/preset-app`** | **WINNER** — gzip-aware, CI-enforced exit code, free GitHub Action posts PR diff comments, supports App Router by globbing chunk files. |
| `@next/bundle-analyzer` | Investigation only — no enforcement. Add later if size-limit flags an issue and you need to drill in. |
| `@bundle-stats/cli` | Heavier; designed for multi-app monorepos. Overkill. |

#### 9.2 Install

```bash
cd frontend
pnpm add -D size-limit @size-limit/preset-app
```

#### 9.3 `.size-limit.json` (in `frontend/`)

The PERF-01 requirement is "First Load JS ≤ 180 KB gzipped per route." Next.js App Router emits per-route chunks in `.next/static/chunks/app/<route>/page-<hash>.js` plus shared chunks under `.next/static/chunks/`. The most reliable measure is to bound the **total** of shared + per-route chunks for each route. Concretely:

```json
[
  {
    "name": "App Shell (shared chunks)",
    "path": [
      ".next/static/chunks/main-*.js",
      ".next/static/chunks/framework-*.js",
      ".next/static/chunks/webpack-*.js",
      ".next/static/chunks/polyfills-*.js"
    ],
    "limit": "90 kB",
    "gzip": true
  },
  {
    "name": "Route: /dashboard (First Load JS)",
    "path": [
      ".next/static/chunks/app/layout-*.js",
      ".next/static/chunks/app/dashboard/page-*.js"
    ],
    "limit": "180 kB",
    "gzip": true
  },
  {
    "name": "Route: /sign-in (First Load JS)",
    "path": [
      ".next/static/chunks/app/layout-*.js",
      ".next/static/chunks/app/sign-in/[[...sign-in]]/page-*.js"
    ],
    "limit": "180 kB",
    "gzip": true
  }
]
```

> **Note:** Next.js's reported "First Load JS" combines shared chunks + the route's own bundle. `size-limit`'s glob approach approximates this — the most rigorous alternative is to parse `next build`'s stdout (it emits a table). For Phase 1, the glob approach is correct enough to **fail** when bundles balloon.

#### 9.4 `package.json` scripts

```json
{
  "scripts": {
    "size": "size-limit",
    "size:why": "size-limit --why"
  },
  "size-limit": [],
  "// size-limit": "see .size-limit.json"
}
```

#### 9.5 GitHub Action (`frontend.yml`) — see Section 11 below

`andresz1/size-limit-action@v1` posts a PR comment with the bundle diff and fails the job if any entry exceeds its limit. Specifically:

```yaml
- name: Check First Load JS budget
  uses: andresz1/size-limit-action@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    directory: frontend
    package_manager: pnpm
    build_script: build
```

**Confidence:** **MEDIUM-HIGH** — `size-limit` is the standard, but the *exact* glob mapping to Next.js App Router's "First Load JS" metric needs validation in the first CI run. **Add a verification step in the plan:** run `next build`, inspect the printed bundle table, then tune the globs to match within ±5 kB before committing the budget.

**Sources:** [size-limit GitHub](https://github.com/ai/size-limit), [size-limit-action](https://github.com/andresz1/size-limit-action), [Next.js bundle monitoring patterns 2026](https://sujaykundu.com/articles/automating-nextjs-bundle-size-monitoring).

---

### 10. gitleaks Pre-commit (SEC-01)

#### 10.1 Install `pre-commit` framework

```bash
# Once globally (or in the repo's tooling venv)
pip install pre-commit
# Or via system package manager: brew install pre-commit / scoop install pre-commit
```

#### 10.2 `.pre-commit-config.yaml` (repo root)

```yaml
# Source: github.com/gitleaks/gitleaks/.pre-commit-hooks.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # Bonus: catch common issues cheaply
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-json
      - id: detect-private-key
```

#### 10.3 `.gitleaks.toml` (repo root) — extend default rules with project allowlist

```toml
# Source: github.com/gitleaks/gitleaks (config reference)
# Inherit the default rule set
[extend]
useDefault = true

[allowlist]
description = "FitGH project allowlist — example values and lockfiles"
paths = [
  '''(.*\.)?env\.example$''',
  '''pnpm-lock\.yaml$''',
  '''package-lock\.json$''',
  '''requirements.*\.txt$''',
  '''\.planning/''',
  '''shared/schemas/'''
]
regexes = [
  # Common placeholder patterns
  '''pk_test_[A-Za-z0-9]+''',
  '''sk_test_[A-Za-z0-9]+''',
  '''whsec_[A-Za-z0-9]+''',
  '''mongodb\+srv://.*:<password>@''',
  '''sntrys_test_''',
  '''https://.*@o\d+\.ingest\.sentry\.io/''',  # public DSNs are not secrets
]
```

#### 10.4 Install hooks into the working repo

```bash
pre-commit install
# also install for commit-msg if you want lint there in the future
# pre-commit install --hook-type commit-msg

# Verify it works
pre-commit run --all-files
```

#### 10.5 Smoke test — try to commit a fake Mongo URI

```bash
echo "MONGODB_URI=mongodb+srv://admin:realpassword@cluster.example.net/db" > /tmp/leak.txt
cp /tmp/leak.txt frontend/.env.local
git add -f frontend/.env.local
git commit -m "test: deliberate leak (should fail pre-commit)"
# Expected: gitleaks blocks the commit with "Finding: MongoDB connection string"
rm frontend/.env.local
```

**Confidence:** **HIGH**.

**Sources:** [gitleaks GitHub](https://github.com/gitleaks/gitleaks), [pre-commit-hooks.yaml in gitleaks](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml), [gitleaks pre-commit 2026 guide](https://www.d4b.dev/blog/2026-02-01-gitleaks-pre-commit-hook/).

---

### 11. GitHub Actions for CI

#### 11.1 `.github/workflows/frontend.yml`

```yaml
name: frontend
on:
  push:
    branches: [main]
    paths:
      - "frontend/**"
      - ".github/workflows/frontend.yml"
  pull_request:
    paths:
      - "frontend/**"
      - ".github/workflows/frontend.yml"

defaults:
  run:
    working-directory: frontend

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 10
          run_install: false

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          cache-dependency-path: frontend/pnpm-lock.yaml

      - run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Typecheck
        run: pnpm exec tsc --noEmit

      - name: Build
        env:
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: pk_test_placeholder
          CLERK_SECRET_KEY: sk_test_placeholder
          BACKEND_URL: http://localhost:8080
          NEXT_PUBLIC_SENTRY_DSN: https://placeholder@o0.ingest.sentry.io/0
        run: pnpm build

  size-limit:
    runs-on: ubuntu-latest
    needs: [] # parallel with ci
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 10 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          cache-dependency-path: frontend/pnpm-lock.yaml
      - uses: andresz1/size-limit-action@v1
        env:
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: pk_test_placeholder
          CLERK_SECRET_KEY: sk_test_placeholder
          BACKEND_URL: http://localhost:8080
          NEXT_PUBLIC_SENTRY_DSN: https://placeholder@o0.ingest.sentry.io/0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          directory: frontend
          package_manager: pnpm
          build_script: build
```

#### 11.2 `.github/workflows/backend.yml`

```yaml
name: backend
on:
  push:
    branches: [main]
    paths:
      - "backend/**"
      - ".github/workflows/backend.yml"
  pull_request:
    paths:
      - "backend/**"
      - ".github/workflows/backend.yml"

defaults:
  run:
    working-directory: backend

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements-dev.txt

      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Ruff
        run: ruff check .

      - name: Pytest
        env:
          # Real connection not needed — tests use mongomock + offline JWT
          MONGODB_URI: "mongomock://localhost/fitgh"
          CLERK_SECRET_KEY: "sk_test_placeholder"
          CLERK_AUTHORIZED_PARTIES: "http://localhost:3000"
          CORS_ALLOWED_ORIGINS: "http://localhost:3000"
        run: pytest -x --cov=app

      - name: Build Docker image (smoke)
        run: docker build -t fitgh-api:ci .
```

#### 11.3 `.github/workflows/gitleaks.yml`

```yaml
name: gitleaks
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # full history for PR scans
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # No GITLEAKS_LICENSE needed for public repos; private repos may need one
          # GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

> **Heads-up for private repos:** `gitleaks-action@v2` requires a (free) license key for repos in orgs with > 25 members. For solo / small projects this isn't a concern, but verify by attempting the first PR. Fallback: install the gitleaks binary directly via curl in the workflow.

#### 11.4 Branch protection

Once green builds are confirmed, in GitHub → Settings → Branches → Protect `main`:
- Require status checks: `frontend / ci`, `frontend / size-limit`, `backend / ci`, `gitleaks / scan`.
- Require PR review (optional for solo; recommended).

**Confidence:** **HIGH** on workflow shape; **MEDIUM** on the exact size-limit thresholds (will need one PR to tune the globs against `next build` output).

**Sources:** [pnpm/action-setup](https://github.com/pnpm/action-setup), [actions/setup-node caching](https://github.blog/changelog/2021-09-07-github-actions-setup-node-supports-dependency-caching-for-projects-with-monorepo-and-pnpm-package-manager/), [gitleaks-action](https://github.com/gitleaks/gitleaks-action), [size-limit-action](https://github.com/andresz1/size-limit-action).

---

### 12. DNS / Hostnames for Phase 1

**Recommendation: ship on default platform hostnames in Phase 1; defer custom domain to Phase 7.**

| Resource | Hostname (v1) | Notes |
|----------|---------------|-------|
| Frontend | `https://fitgh.vercel.app` | Free, auto-issued cert. |
| Frontend (PR previews) | `https://fitgh-git-<branch>-<team>.vercel.app` | Auto-generated per PR; Clerk dev instance allowlists `*.vercel.app`. |
| Backend | `https://fitgh-api.fly.dev` | Free, auto-issued cert. |

**`fitgh.app` registration:** **Skip in Phase 1** — adds a $10–15/yr cost and a DNS-management chore; Vercel + Fly default hostnames are sufficient for the Walking Skeleton scope. Buying the domain *early* makes sense only if marketing pages launch ahead of Phase 7 (they won't per the roadmap).

**CORS allowlist values (Phase 1):**
- Production: `https://fitgh.vercel.app`
- Local dev: `http://localhost:3000`

These two strings appear in three places that **must match exactly**:
1. Flask `CORS_ALLOWED_ORIGINS` env var.
2. Clerk `CLERK_AUTHORIZED_PARTIES` env var (Flask side).
3. Clerk dashboard → Domains.

**Confidence:** **HIGH**.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework (FE) | `Vitest` 2.x (lighter than Jest; first-class TS) — Phase 1 may also use **Playwright** for one e2e |
| Framework (BE) | `pytest` 8.x + `pytest-flask` |
| Config file (FE) | `frontend/vitest.config.ts` — **Wave 0** |
| Config file (BE) | `backend/pyproject.toml` `[tool.pytest.ini_options]` — **Wave 0** |
| Quick run command (BE) | `cd backend && pytest -x` |
| Quick run command (FE) | `cd frontend && pnpm vitest run` |
| Full suite command | `pnpm --filter frontend test && cd ../backend && pytest --cov=app` |

> **Recommendation:** Phase 1's automated test surface is small and high-leverage. Spend Wave 0 on:
> - `tests/test_health.py` — boots Flask app, asserts `{ok:true, mongo:"connected"}` against a mongomock fixture.
> - `tests/test_me.py` — verifies the `@require_auth` decorator with a mocked Clerk SDK; checks 401 on missing JWT and 200 + `{email}` on a valid one.
> - `tests/test_webhooks.py` — POST a fake `user.created` event, assert insert into mongomock `users`.
> - Frontend tests are deferred to Phase 2 when forms appear; Phase 1's only React code is server-component glue.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| AUTH-01 | Sign-up with email or Google OAuth via Clerk | manual (Clerk hosts OAuth dance) | — | n/a |
| AUTH-02 | Session persists across refresh (Clerk cookie) | manual | — | n/a |
| AUTH-03 | Sign-out clears cookie | manual | — | n/a |
| AUTH-06 | Flask verifies JWT networkless on every protected request | unit | `pytest backend/tests/test_me.py -x` | ❌ Wave 0 |
| SEC-01 | gitleaks blocks Mongo URI commit | smoke (CI) | `pre-commit run --all-files` + `gitleaks/gitleaks-action@v2` | ❌ Wave 0 (.pre-commit-config.yaml) |
| SEC-02 | Atlas user has `readWrite@fitgh` only (no admin) | manual (Atlas UI) | — | n/a |
| SEC-03 | Flask CORS rejects unauthorized origins | unit | `pytest backend/tests/test_cors.py -x` | ❌ Wave 0 |
| SEC-04 | `MongoClient(maxPoolSize=10)` singleton | unit (import-time assertion) | `pytest backend/tests/test_db.py -x` | ❌ Wave 0 |
| OBS-01 | Sentry FE+BE scrubbers drop email/image/kcal | unit (BE) + manual review (FE) | `pytest backend/tests/test_sentry_scrubber.py -x` | ❌ Wave 0 |
| OBS-02 | Vercel Analytics + Speed Insights receive events | manual (Vercel dashboard) | — | n/a |
| PERF-01 | First Load JS ≤ 180 KB gzipped | smoke (CI) | `pnpm size` (via `size-limit-action`) | ❌ Wave 0 (`.size-limit.json`) |
| DEPLOY-01 | Frontend deploys to Vercel from `/frontend` | smoke | Vercel build log | manual |
| DEPLOY-02 | Backend on Fly.io `jnb` + static egress IP | smoke | `fly status` + `fly ips list` + Atlas allowlist check | manual |

### Sampling Rate

- **Per task commit:** `pytest -x` (backend) or `pnpm vitest run` (frontend) — <30s.
- **Per wave merge:** full pytest + Vitest + `size-limit`.
- **Phase gate:** Full CI green + manual sign-off on AUTH-01/02/03/06 from a real Clerk sign-in flow + Sentry receives a deliberate test error from both FE and BE.

### Wave 0 Gaps

- [ ] `backend/pyproject.toml` `[tool.pytest.ini_options]` + `[tool.ruff]` blocks
- [ ] `backend/tests/conftest.py` — Flask app factory fixture + mongomock fixture + Clerk mock fixture
- [ ] `backend/tests/test_health.py`
- [ ] `backend/tests/test_me.py`
- [ ] `backend/tests/test_webhooks.py`
- [ ] `backend/tests/test_cors.py`
- [ ] `backend/tests/test_db.py`
- [ ] `backend/tests/test_sentry_scrubber.py`
- [ ] `frontend/vitest.config.ts` (minimal, defer real tests to Phase 2)
- [ ] `.size-limit.json` in `frontend/`
- [ ] `.pre-commit-config.yaml` + `.gitleaks.toml` in repo root
- [ ] `.github/workflows/{frontend,backend,gitleaks}.yml`

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | **YES** | Clerk (delegated; covers password complexity, MFA, OAuth, session lifetime). |
| V3 Session Management | **YES** | Clerk `__session` httpOnly + Secure + SameSite=Lax cookie. |
| V4 Access Control | **YES** | `@require_auth` decorator on every protected Flask route; route matcher in `clerkMiddleware()`. |
| V5 Input Validation | **YES (partial Phase 1)** | Pydantic v2 schemas for webhook payloads; Phase 2 expands for profile/onboarding. |
| V6 Cryptography | **YES (delegated)** | TLS via Vercel + Fly + Atlas. JWT signing/verification delegated to Clerk. **Never hand-roll.** |
| V7 Error Handling | **YES** | Sentry `before_send` scrubber drops PII (OBS-01). |
| V8 Data Protection | **YES** | All secrets in env vars (Fly secrets + Vercel env vars); never logged. |
| V9 Communications | **YES** | `force_https = true` in `fly.toml`; Vercel HTTPS-only; Atlas TLS-only. |
| V10 Malicious Code | partial | gitleaks for secret leaks; `pnpm audit` / `pip-audit` deferred to Phase 7 hardening. |
| V13 API & Web Service | **YES** | CORS explicit allowlist; no `*` with credentials; svix-verified webhooks. |

### Known Threat Patterns for {Next.js + Flask + MongoDB} stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Forged identity header (`X-User-Id`) | Spoofing | Never read identity from arbitrary headers; only via `@require_auth` → Clerk JWT. |
| MongoDB injection via unsafe query construction | Tampering | Use PyMongo's typed query API (`find_one({"clerk_id": id})`); never string-build queries. |
| Connection-string leak in git | Information Disclosure | `.env*` gitignored + gitleaks pre-commit + Atlas password rotated (SEC-01, SEC-02). |
| Cost attack on Flask (DDoS) | Denial of Service | Phase 1: rely on Fly.io's edge + Cloudflare-in-front deferred to Phase 7. Phase 4 adds rate limiting. |
| Cross-origin token theft via wildcard CORS | Information Disclosure | Explicit origin allowlist (SEC-03). |
| Forged Clerk webhook | Spoofing | `svix.Webhook(secret).verify(body, headers)` on every webhook request. |
| MongoDB connection pool exhaustion | DoS (self-inflicted) | Singleton `MongoClient(maxPoolSize=10)` (SEC-04 + M-2 pitfall). |
| Session fixation | Spoofing | Clerk rotates sessions on sign-in/out automatically. |
| Source-map leak revealing server code | Information Disclosure | `hideSourceMaps: true` in `withSentryConfig`. |

---

## Environment Availability

> Phase 1 has external dependencies (Fly CLI, Atlas account, Clerk account, Vercel account, Sentry account). The dev workstation also needs Node and Python.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend dev + CI | `[ASSUMED]` — pin via `.nvmrc=20` | 20.x | n/a |
| pnpm | Frontend dev + CI | `[ASSUMED]` — install `npm i -g pnpm@10` | 10.x | `npm` works but lockfile diverges |
| Python | Backend dev | `[ASSUMED]` — Python 3.12 via system or `pyenv` | 3.12 | n/a |
| Docker (local) | Optional for Fly build (Fly runs in cloud) | `[ASSUMED]` | latest | Fly builds remotely; local Docker is for smoke tests only |
| `fly` CLI | Backend deploy | install per Section 6.1 | latest | n/a |
| Atlas account | DB | existing (cluster `cluster0.pcd3g.mongodb.net`) | M0 free | n/a |
| Clerk account | Auth | needs **Development** instance + **Production** instance | latest | n/a |
| Vercel account | Frontend host | needs Hobby plan | — | n/a |
| Sentry account | Errors | needs free Developer plan | — | n/a |
| GitHub repo | CI + git | `[ASSUMED]` already created | — | n/a |
| `pre-commit` | Local git hook | `pip install pre-commit` | latest | git native hooks (more brittle) |

**Missing dependencies with no fallback:** None — all are SaaS sign-ups + local tooling installs that the developer can complete in <1 hour.

**Missing dependencies with fallback:** None blocking.

> **`[ASSUMED]` tags above:** confirmed by the developer (`francisyiryel@gmail.com`) before kickoff. The planner should add a "Wave 0: dev environment verification" task with a one-liner checking each tool's `--version`.

---

## Phase 1 Gotchas

### G1. Tailwind v4 + shadcn/ui + Next.js 15 footguns

- **What:** v4 is CSS-first (`@theme` in `globals.css`); v3 patterns (`tailwind.config.js`) silently fail to apply.
- **Why it bites:** Many shadcn/ui blog tutorials still show v3 patterns. Copy-pasting one creates a project where dark mode partly works and custom colors don't.
- **Prevention:** `create-next-app@latest` (Next 15.2.4) ships v4 by default. After `shadcn init`, verify `components.json` shows `"tailwind": {"config": ""}` (empty string, NOT a path to `tailwind.config.js`). All custom design tokens go in `globals.css` under `@theme`.

### G2. pnpm + Vercel monorepo "Root Directory" gotcha

- **What:** With Root Directory = `frontend`, Vercel only reads files under `frontend/`. Files in `shared/` or repo root won't be available to the build unless "Include source files outside Root Directory" is on.
- **Why it bites:** Phase 1 doesn't need `shared/` at build time, but Phase 3 imports `shared/ghana-food-table.json` into Flask (fine, separate deploy) AND if Phase 3 ever imports it into Next.js for autocomplete, you'll hit this.
- **Prevention:** For Phase 1, keep "Include source files outside" **off**. Plan Phase 3 to load Ghana table via Flask API, not import.

### G3. Fly.io static egress IP — pricing changed Jan 1, 2026

- **What:** Old `fly ips allocate-v4 --shared` flow is being phased out in favour of app-scoped `fly ips allocate-egress`. Billing for app-scoped egress IPs started Jan 1, 2026 at $3.60/mo per IPv4.
- **Why it bites:** Tutorials from 2024–2025 still describe the legacy flow; the cost section may be missing entirely.
- **Prevention:** Use the 2026 command (Section 6.5). Budget $3.60/mo per region. If $3.60/mo is a deal-breaker, use `0.0.0.0/0` in Atlas + strong password in dev only — but the SEC-04 requirement explicitly demands pinning the static IP in prod, so this isn't optional.

### G4. Fly.io `jnb` cold-start behaviour

- **What:** `auto_stop_machines = "off"` + `min_machines_running = 1` keeps one machine warm; the first request after deploy still pays a ~3–5s boot cost.
- **Why it bites:** A demo to the user starts cold and looks slow.
- **Prevention:** Run a warm-up `curl https://fitgh-api.fly.dev/health` after every deploy in the deploy script. Phase 7 may revisit a cron-job.org keep-warm if Phase 4's vision endpoint cold-starts hurt.

### G5. Clerk + Flask compatibility quirks

- **What:** `clerk-backend-api`'s `authenticate_request()` accepts an `httpx.Request` (not Flask's `request`). Pass a constructed httpx Request as shown in Section 3.8.
- **Why it bites:** Pretending Flask's `request` quacks like httpx works for some attributes but breaks on `.url` being a `werkzeug.Request.url` (string) vs httpx's `URL` object. Cleanest fix: explicitly construct an `httpx.Request`.
- **Prevention:** Use the Section 3.8 wrapper exactly. Write a unit test (`tests/test_me.py`) that asserts 401 on missing JWT and 200 on a valid one (mock the JWKS endpoint with `respx`).

### G6. PyMongo 4.x — what else is deprecated besides Motor?

- **What:** PyMongo 4.17 (Apr 2026) deprecated `bson.son.SON.has_key()`, `iterkeys()`, `itervalues()` (removed in 5.0). Motor is fully deprecated since May 2026.
- **Why it bites:** A `son.has_key('field')` call from an old tutorial passes type-check but throws DeprecationWarning today and will fail in PyMongo 5.0.
- **Prevention:** Use `'field' in son_doc` and `.keys()`/`.values()`. Pin `pymongo>=4.13,<5`. Don't add Motor.

### G7. Sentry source-map upload — different DSNs FE vs BE

- **What:** Frontend uses one Sentry project + DSN (`fitgh-frontend`); backend uses another (`fitgh-backend`). The `SENTRY_AUTH_TOKEN` is shared but the org/project must be set distinctly. Source-map upload via the Next.js plugin only applies to the FE project.
- **Why it bites:** Pointing both FE and BE at the same DSN merges error streams in confusing ways.
- **Prevention:** Two distinct projects in Sentry; two distinct env vars; assert in CI that `SENTRY_PROJECT_FE != SENTRY_PROJECT_BE`.

### G8. size-limit measuring App Router routes

- **What:** Next.js's printed "First Load JS" per route is the union of shared chunks + the route's own chunks. `size-limit`'s glob is an approximation.
- **Why it bites:** The first PR may flag size-limit at 175 KB while `next build` says 178 KB — close enough but mildly confusing.
- **Prevention:** After the first successful `next build`, screenshot the bundle table, then tune the globs in `.size-limit.json` so each limit matches Next.js's reported number within ±5 KB. Lock the budget at **180 kB** (the requirement) and let size-limit fail when the approximation crosses.

### G9. gitleaks false positives

- **What:** Lockfiles (`pnpm-lock.yaml`, `requirements.txt`) sometimes embed integrity hashes that look like secret patterns. `.env.example` with placeholder `pk_test_xxx` triggers Clerk-key regex.
- **Why it bites:** Developer disables the hook in frustration.
- **Prevention:** The `.gitleaks.toml` allowlist (Section 10.3) pre-excludes lockfiles, `.planning/`, and common placeholder patterns. Verify with `pre-commit run --all-files` on a clean tree — should pass with zero findings before merging the hook setup PR.

### G10. Static egress IP shared vs dedicated — naming confusion

- **What:** Fly.io's pricing page distinguishes "shared IPs" (free IPv4 used by anycast routing for incoming traffic) from "app-scoped egress IPs" (used as the *source* IP of outbound traffic — what Atlas allowlists need). These are different products.
- **Why it bites:** Reading "shared IPs are free" and thinking that covers Atlas allowlisting → outbound traffic exits via Fly's NAT range → wrong IP arrives at Atlas → connection rejected.
- **Prevention:** Use `fly ips allocate-egress` (Section 6.5). Verify by `curl --connect-to ifconfig.me:443:<IP> https://ifconfig.me` from `fly ssh console` — the returned IP must match the allocated egress IP.

### G11. Clerk webhook `__session` cookie not available

- **What:** Webhooks are server-to-server; `auth()` returns null inside `/api/webhooks/clerk/route.ts`. The route MUST be excluded from `clerkMiddleware()` protection (it is, in Section 3.3 via `isPublicRoute`).
- **Why it bites:** If the webhook path is left protected, Clerk's own webhook gets 401'd back, and signups silently fail to create Mongo records.
- **Prevention:** Verify by running `curl -X POST https://fitgh.vercel.app/api/webhooks/clerk -d '{}'` without auth — should return 400 (invalid signature), NOT 401 (unauthorized). 400 = good, route is reachable.

### G12. `BACKEND_URL` mismatch between Vercel preview and Fly prod

- **What:** Vercel preview deploys use the production `BACKEND_URL` env unless you set a different one in the Preview scope.
- **Why it bites:** A preview PR's test sign-in writes to the production Atlas database via the production Flask.
- **Prevention:** Either:
  1. Deploy a `fitgh-api-preview` Fly app from a `preview` branch and point Vercel previews at it (preferred), OR
  2. Accept that previews share prod for Phase 1 and add a banner. The first option costs $3.60/mo extra for the preview machine + IP; skip until Phase 7.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | "Use plain monorepo (no pnpm workspaces) because only `/frontend` is JS" | 1 | If user prefers a single `pnpm install` from repo root for editor tooling, switch to workspaces. Low-risk pivot — adds `pnpm-workspace.yaml` + root `package.json`. |
| A2 | "Skip Sentry source-map upload for backend (Python doesn't need it)" | 8 | None — Python tracebacks self-resolve. |
| A3 | "Defer `fitgh.app` domain purchase to Phase 7" | 12 | If user wants marketing site sooner, register early; non-blocking for Walking Skeleton. |
| A4 | "`.nvmrc` = 20" | 1 | If pnpm 10 requires Node 22+, bump. Verified pnpm 10 works on Node 18+, so 20 is safe. |
| A5 | "Custom Clerk catch-all pages, not hosted UI" | 3 | Hosted UI works too; trades bundle weight for off-domain UX. Either is acceptable. |
| A6 | "Forward Clerk webhooks through Next.js BFF (not direct to Flask)" | 3.9 | Direct-to-Flask also works; BFF simplifies local dev with `vercel dev`. |
| A7 | "Vercel preview deploys share production Atlas + Flask in Phase 1" | G12 | A preview signup writes to prod DB. Acceptable for solo build; tighten in Phase 7. |
| A8 | "size-limit glob approximates Next.js's 'First Load JS' within ±5 KB" | 9 | First CI run needs a tuning PR. Plan a Wave 1 verification step. |
| A9 | "Phase 1 doesn't need frontend Vitest tests beyond a minimal config" | Validation | Phase 1's React surface is server-component glue; no business logic to test. Phase 2 onboarding forms will need Vitest properly. |
| A10 | "Fly.io `jnb` region is available for new apps as of May 2026" | 6 | Verify with `fly platform regions` before launch. JNB has been GA for years; very low risk. |

---

## Open Questions

1. **Is the existing Atlas cluster's tier truly M0, or has it been promoted?**
   - What we know: STACK.md says M0 free.
   - What's unclear: Phase 4 may need M10 ($57/mo) before 500 DAU; check the current Atlas dashboard to confirm tier before pinning the static IP.
   - Recommendation: Add a Wave 0 task — "Verify Atlas cluster tier and apply the rotated password."

2. **Should Phase 1 use a single Clerk instance (Development) for both local + preview + prod, or split Development from Production now?**
   - What we know: Clerk separates Development (test keys, `pk_test_…`) from Production (live keys, `pk_live_…`). Production requires a registered domain.
   - What's unclear: For a Walking Skeleton without `fitgh.app` domain, Production instance can still be configured against `fitgh.vercel.app` if Clerk allows it (it does — the production instance accepts any HTTPS domain you authorise).
   - Recommendation: **Use Development instance for local + preview, Production for the `fitgh.vercel.app` deploy.** Set both up in Phase 1.

3. **`fitgh-api-preview` Fly app for Vercel preview deploys — Phase 1 or Phase 7?**
   - What we know: Without it, preview signups hit prod Atlas (G12).
   - What's unclear: How often previews will be deployed in Phase 1 (probably <5).
   - Recommendation: **Defer to Phase 7.** Phase 1 has zero real users; preview signups touching prod Atlas is acceptable for now.

4. **Should the Clerk webhook live on Next.js Vercel route or directly on Fly?**
   - What we know: Next.js BFF route is recommended in Section 3.9 (TLS termination + svix verify on Vercel edge).
   - What's unclear: A direct-to-Flask webhook is simpler but exposes Fly hostname to the public.
   - Recommendation: Stick with BFF forwarding — `[ASSUMED]` correct; verify during discuss-phase.

5. **`pyproject.toml` adoption — Phase 1 or Phase 3?**
   - What we know: Phase 1 only needs `requirements.txt` + `requirements-dev.txt`. `pyproject.toml` adds value for tool config (ruff, pytest, mypy).
   - What's unclear: Whether the planner wants to introduce `pyproject.toml` now.
   - Recommendation: **Defer to Phase 3** unless the user/planner wants it sooner. Cost of adding later is ~30 min.

6. **Is Pre-Phase-0 (Ghana food table) actually starting in parallel with Phase 1?**
   - What we know: SUMMARY.md mentions "Data prep (parallel with Phase 1)" but the ROADMAP.md only has Phases 1–7.
   - What's unclear: Whether data-prep is its own GSD phase or just a side track.
   - Recommendation: **Skip for Phase 1.** Phase 1 explicitly excludes the Ghana table per SKELETON.md scope.

---

## Tasks Implied (For Planner)

A bullet inventory grouped by vertical slice — the planner can lift these into atomic tasks in PLAN.md files.

### Slice A: Repo + secret hygiene (DEPLOY-01 setup, SEC-01, SEC-02)

- Initialise the repo's `.gitignore`, `.env.example`, `.nvmrc`, top-level `README.md`.
- Create `.pre-commit-config.yaml` + `.gitleaks.toml` and run `pre-commit install` locally; verify with a deliberate-leak smoke test.
- Rotate the exposed Atlas password (UI clicks; do not commit new password).
- Create the `fitgh-app` Atlas user with `readWrite@fitgh` only (NOT atlasAdmin); record the new connection string in the password manager.
- Verify Atlas Network Access has dev IP allowlisted; remove `0.0.0.0/0` if present.

### Slice B: Frontend scaffold (DEPLOY-01, PERF-01)

- Run `pnpm create next-app@latest` with the locked flags (Section 2).
- `pnpm dlx shadcn@latest init` + add `button`, `card`, `avatar`, `sonner`.
- Confirm Tailwind v4 + shadcn setup by adding `<Button>Test</Button>` to root page.
- Author `app/sign-in/[[...sign-in]]/page.tsx` and `app/sign-up/[[...sign-up]]/page.tsx`.
- Author `app/dashboard/page.tsx` (server component, fetches Flask `/me`).
- Author `app/api/me/route.ts` (BFF; verifies Clerk session, forwards JWT).
- Author `app/api/webhooks/clerk/route.ts` (svix verify, forwards to Flask).
- Add `middleware.ts` with `clerkMiddleware()` + `createRouteMatcher`.
- Wrap `app/layout.tsx` in `<ClerkProvider>`; add `<Analytics />` + `<SpeedInsights />`.
- Install `size-limit` + `@size-limit/preset-app`; author `.size-limit.json`; tune globs after first `next build`.

### Slice C: Clerk SaaS setup (AUTH-01, AUTH-02, AUTH-03, AUTH-06)

- Create Clerk Development + Production application instances.
- Enable Email/Password + Google OAuth in each instance.
- Set Paths (sign-in/up URLs) + Domains (`localhost:3000`, `fitgh.vercel.app`) in each.
- Configure webhook endpoint → `https://fitgh.vercel.app/api/webhooks/clerk` → events `user.created` + `user.deleted`; copy `CLERK_WEBHOOK_SECRET`.
- Store `pk_test_` / `pk_live_` / `sk_test_` / `sk_live_` / `whsec_` securely.

### Slice D: Backend scaffold (AUTH-06, SEC-03, SEC-04, OBS-01)

- Create `backend/`, Python 3.12 venv, `requirements.txt` + `requirements-dev.txt`.
- Author `app/__init__.py` (factory pattern), `app/config.py`, `app/db.py` (singleton MongoClient with `maxPoolSize=10`, `tls=True`, `serverSelectionTimeoutMS=5000`).
- Author `app/extensions.py` Sentry init with `before_send` PII scrubber.
- Author `app/middleware/auth.py` with `@require_auth` decorator.
- Author `app/routes/health.py`, `app/routes/me.py`, `app/routes/webhooks.py`.
- Wire `flask-cors` with explicit origins (`CORS_ALLOWED_ORIGINS` env var), `supports_credentials=False`, `allow_headers=['Content-Type', 'Authorization']`.
- Write Wave 0 tests: `tests/test_health.py`, `tests/test_me.py`, `tests/test_webhooks.py`, `tests/test_cors.py`, `tests/test_db.py`, `tests/test_sentry_scrubber.py`.

### Slice E: Fly.io deploy (DEPLOY-02)

- Author `Dockerfile`, `.dockerignore`, `fly.toml` (region=jnb, always-on, healthcheck on `/health`).
- `fly launch --no-deploy --copy-config --name fitgh-api --region jnb`.
- `fly secrets set` for all backend env vars (Section 6.4).
- `fly deploy` and verify `curl https://fitgh-api.fly.dev/health` returns `{ok:true, mongo:"connected"}`.
- `fly ips allocate-egress -r jnb` → capture the IPv4.
- Atlas → Network Access → add the egress IPv4 with `/32` mask; remove dev `0.0.0.0/0` from prod path.
- Verify `curl https://fitgh-api.fly.dev/health` still works (Mongo allowlist accepts the egress IP).

### Slice F: Vercel deploy (DEPLOY-01)

- Connect GitHub repo to Vercel; set Root Directory = `frontend`, Node version = 20.
- Set Production + Preview env vars (Section 7.3).
- Trigger first deploy from `main`; verify `fitgh.vercel.app` loads.
- Visit `/sign-up`, complete sign-up flow with email; verify webhook fires and Mongo `users` doc is created.
- Visit `/dashboard`; verify email round-trips end-to-end.
- Verify Vercel Analytics + Speed Insights show at least one pageview in the dashboard.

### Slice G: Observability wiring (OBS-01, OBS-02)

- Create Sentry FE project (`fitgh-frontend`) + BE project (`fitgh-backend`); copy DSNs + auth token.
- Run `pnpm dlx @sentry/wizard@latest -i nextjs --saas` from `frontend/`; verify `instrumentation.ts` exists.
- Add the `before_send` PII scrubber to both FE configs (Section 8.3) and BE config (Section 4.5).
- Deliberately throw an error in Flask `/me` (temporarily); verify Sentry receives it with email scrubbed.
- Repeat for FE: temporary `throw new Error('boom')` in `/dashboard`; verify Sentry FE captures it with no user email.

### Slice H: CI (PERF-01, SEC-01)

- Author `.github/workflows/frontend.yml` (lint, typecheck, build, size-limit).
- Author `.github/workflows/backend.yml` (ruff, pytest, docker build smoke).
- Author `.github/workflows/gitleaks.yml`.
- Open a deliberate-leak PR (with a committed fake Mongo URI) to verify gitleaks blocks merge.
- Open a deliberate-bundle-bloat PR (adds an unused 200 KB dep) to verify size-limit fails the PR.
- Configure branch protection on `main` to require all three workflow status checks.

### Slice I: End-to-end smoke (acceptance criteria)

- Real user signs up via Clerk on `fitgh.vercel.app` → lands on `/dashboard` showing their email pulled from Atlas through Flask.
- Sign out → refresh → lands on `/sign-in`.
- `curl https://fitgh-api.fly.dev/health` → `{ok:true, mongo:"connected"}`.
- Atlas Network Access shows the Fly egress IPv4 pinned; no `0.0.0.0/0`.
- A PR that pushes First Load JS above 180 KB fails the build.
- A commit containing a Mongo URI is blocked by the local gitleaks pre-commit hook AND by the CI gitleaks workflow.
- Sentry FE + BE each received at least one real error event with no PII in the scrubbed context.
- Vercel Analytics + Speed Insights show events from the deployed app.

---

## State of the Art

| Old Approach | Current Approach (2026) | When Changed | Impact |
|--------------|--------------------------|--------------|--------|
| Tailwind v3 with `tailwind.config.js` | Tailwind v4 CSS-first config via `@theme` in `globals.css` | v4 GA (Jan 2025); v4.1 (Mar 2025); v4.2 (Feb 2026) | Different setup; smaller CSS bundles; copy-paste of v3 tutorials silently fails. |
| Motor for async MongoDB | PyMongo 4.13+ with built-in `AsyncMongoClient` | Motor deprecation announced ~May 2026 | Don't add Motor to new projects; sync `MongoClient` is fine for Flask. |
| Fly.io `fly ips allocate-v4 --shared` for incoming + egress | `fly ips allocate-egress` for outbound IPs (app-scoped) | Late 2025 / Jan 1 2026 billing | New command; explicit pricing ($3.60/mo per IPv4). |
| NextAuth.js v4 / v5 | Clerk (per FitGH stack lock) | n/a (lock decision) | Drop hand-rolled cookie+CSRF code; gain MFA/OAuth/passkeys for free. |
| Sentry `@sentry/nextjs` v8 (manual `sentry.client.config.js`) | `@sentry/nextjs` v10 with `instrumentation.ts` `onRequestError` | v8→v10 release cadence; Next.js 15 introduced `onRequestError` | Source-map upload via `withSentryConfig`; runtime hook via `instrumentation.ts`. |

**Deprecated/outdated:**
- Motor for async MongoDB (use PyMongo's `AsyncMongoClient`).
- `tailwind.config.js` for Tailwind v4 (use `@theme`).
- `_app.tsx` / `_document.tsx` (Pages Router) for new projects (use App Router).
- `pyjwt` + manual JWKS fetch for Clerk JWT verification (use `clerk-backend-api`).

---

## Sources

### Primary (HIGH confidence)
- [Clerk Next.js quickstart (App Router)](https://clerk.com/docs/nextjs/getting-started/quickstart) — install + middleware + provider + sign-in route conventions
- [clerkMiddleware() reference](https://clerk.com/docs/reference/nextjs/clerk-middleware) — `createRouteMatcher` + `auth.protect()` pattern
- [Clerk custom sign-in page](https://clerk.com/docs/nextjs/guides/development/custom-sign-in-or-up-page) — `[[...sign-in]]` catch-all
- [Clerk Python SDK README](https://github.com/clerk/clerk-sdk-python) — `authenticate_request()` + `AuthenticateRequestOptions`
- [Clerk webhooks syncing guide](https://clerk.com/docs/guides/development/webhooks/syncing) — `user.created` payload shape
- [Fly.io egress IPs docs](https://fly.io/docs/networking/egress-ips/) — `fly ips allocate-egress` command
- [Fly.io billing for app-scoped egress IPs starts Jan 1, 2026](https://community.fly.io/t/billing-for-app-scoped-egress-ips-starts-jan-1-2026/26686) — $3.60/mo IPv4 confirmation
- [Fly.io health checks](https://fly.io/docs/reference/health-checks/) — `[[http_service.checks]]` shape
- [Fly.io hello-gunicorn-flask reference Dockerfile](https://github.com/fly-apps/hello-gunicorn-flask) — Python image + Gunicorn baseline
- [shadcn/ui Next.js install](https://ui.shadcn.com/docs/installation/next) — `create-next-app` flags + `shadcn init`
- [Tailwind CSS v4 launch blog](https://tailwindcss.com/blog/tailwindcss-v4) — `@theme` + `@tailwindcss/postcss`
- [Tailwind v4 PostCSS install](https://tailwindcss.com/docs/installation/using-postcss) — Next.js wiring
- [Sentry Next.js manual setup](https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/) — `instrumentation.ts` + `withSentryConfig`
- [Sentry Flask sensitive data scrubbing](https://docs.sentry.io/platforms/python/guides/flask/data-management/sensitive-data/) — `before_send` hook + `send_default_pii`
- [PyMongo singleton FAQ](https://pymongo.readthedocs.io/en/stable/faq.html) — connection pooling guidance
- [PyMongo 4.17 changelog](https://pymongo.readthedocs.io/en/stable/changelog.html) — current 4.x deprecations
- [MongoDB Atlas user roles](https://www.mongodb.com/docs/atlas/reference/user-roles/) — least-privilege `readWrite@<db>` role
- [Atlas free cluster limits](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/) — 512 MB / 500 connections / no backups
- [gitleaks GitHub](https://github.com/gitleaks/gitleaks) — config schema + rules
- [gitleaks pre-commit-hooks.yaml](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml) — pre-commit framework integration
- [pnpm/action-setup](https://github.com/pnpm/action-setup) — GitHub Actions cache
- [Vercel monorepo docs](https://vercel.com/docs/monorepos) — Root Directory + monorepo settings
- [Vercel Analytics quickstart](https://vercel.com/docs/analytics/quickstart) — `@vercel/analytics` install
- [Vercel Speed Insights quickstart](https://vercel.com/docs/speed-insights/quickstart) — `@vercel/speed-insights` install
- [Flask-CORS docs](https://flask-cors.readthedocs.io/) — `supports_credentials` + `allow_headers`
- [Svix Flask webhook guide](https://www.svix.com/guides/receiving/receive-webhooks-with-python-flask/) — `Webhook(secret).verify(...)` pattern
- [Fly.io app-scoped egress IP recommendation](https://community.fly.io/t/static-egress-ips-for-machines/22004) — app-scoped vs machine-scoped

### Secondary (MEDIUM confidence)
- [Next.js 15.2.4 latest stable note (Mar 2026)](https://www.abhs.in/blog/nextjs-current-version-march-2026-stable-release-whats-new) — verified locked-stack pick
- [Next.js 16 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16) — context on why 15.2.4 stays locked
- [Sentry pricing 2026](https://nurbak.com/en/blog/sentry-pricing/) — free tier limits
- [Render vs Fly.io vs Railway 2026](https://techsy.io/en/blog/railway-vs-render-vs-fly-io) — Fly cold-start + region argument
- [size-limit Next.js monitoring pattern](https://sujaykundu.com/articles/automating-nextjs-bundle-size-monitoring) — App Router glob conventions
- [size-limit-action](https://github.com/andresz1/size-limit-action) — PR-comment + CI gating
- [gitleaks 2026 local pre-commit guide](https://www.d4b.dev/blog/2026-02-01-gitleaks-pre-commit-hook/) — config patterns
- [Tailwind 4.2 release news (Apr 2026)](https://eosl.date/eol/product/tailwind-css/) — v4.2.4 current

### Tertiary (LOW confidence — flagged for verification)
- Specific `@sentry/nextjs` 10.51.0 SDK quotas for free tier — confirm at Sentry signup
- Exact Vercel preview deploy behaviour with Clerk Production-instance domain restrictions — verify during first preview deploy
- `andresz1/size-limit-action@v1` behaviour with monorepo `directory: frontend` — verify on first PR
- `pnpm` exact compatible Node version range for v10 — verified anecdotally to work on Node 18+; `[ASSUMED]`

---

## Metadata

**Confidence breakdown:**
- **Standard stack:** **HIGH** — every package version verified against npm/PyPI in May 2026.
- **Architecture:** **HIGH** — patterns are direct adaptations of locked decisions in `research/SUMMARY.md` + `ARCHITECTURE.md`.
- **Pitfalls:** **HIGH** — 12 gotchas catalogued from official docs + 2026-current community posts.
- **Fly.io static egress pricing:** **MEDIUM-HIGH** — verified the Jan 1, 2026 billing start and $3.60/mo per IPv4; verify the exact account billing model on the developer's first allocation.
- **size-limit App Router globs:** **MEDIUM** — approximation that needs one PR to tune against `next build` output.
- **CI workflow shape:** **HIGH** — standard pnpm + setup-python patterns; will run green on first attempt.

**Research date:** 2026-05-11
**Valid until:** 2026-08-11 (3-month window; revisit if any locked package has a major version bump or Fly.io changes egress IP pricing).
