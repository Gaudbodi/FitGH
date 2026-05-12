---
phase: 01-walking-skeleton
plan: 01
type: execute
wave: 1
depends_on: []
mode: mvp
walking_skeleton: true
autonomous: false
replan_of: "01-PLAN.md @ 2026-05-11 (Vercel + Fly.io + Clerk-twin shape — deprecated by 2026-05-12 rewrite)"
requirements:
  - AUTH-01
  - AUTH-02
  - AUTH-03
  - AUTH-06
  - SEC-04
  - DEPLOY-01
  - DEPLOY-02
deferred_requirements_from_phase:
  - SEC-01  # custom gitleaks CI rules -> local pre-commit only (kept), no CI job
  - SEC-02  # Atlas IP-allowlist tightening -> 0.0.0.0/0 + 32-char password + scoped role accepted for MVP
  - SEC-03  # Flask CORS hardening -> same-origin via Next.js BFF (no cross-origin to Flask)
  - OBS-01  # Sentry FE/BE -> deferred until a real bug surfaces
  - OBS-02  # Vercel Analytics -> dropped (no Vercel)
  - PERF-01 # size-limit 180 KB CI gate -> manual check at phase boundaries
slices:
  - "0: Cleanup the old shape (delete Fly/Vercel/Sentry/size-limit/gitleaks-CI artefacts)"
  - "A: User dashboard checkpoints (Atlas user, Render account + GitHub link, Clerk single Production instance)"
  - "B: render.yaml + build wiring (two web services from one repo, push-to-deploy)"
  - "C: Simplify CI (one workflow, pytest + pnpm build in parallel)"
  - "D: Frontend auth + dashboard (ClerkProvider, middleware, sign-in/up, /api/me BFF, /dashboard fetch)"
  - "E: Backend trim + sync-on-demand /me (drop webhook, conditional Sentry init, upsert user on first /me)"
  - "F: Deploy + end-to-end verify (push main, sign-up on Render URL, /health mongo:connected, sign-out)"
  - "G: Docs + spec cleanup (SKELETON.md, REQUIREMENTS.md traceability, research/SUMMARY.md amendment)"
files_modified:
  # Deleted
  - backend/Dockerfile  # DELETE — Render uses Python buildpack
  - backend/.dockerignore  # DELETE — no Docker
  - backend/app/routes/webhooks.py  # DELETE — sync-on-demand replaces webhook
  - backend/tests/test_webhooks.py  # DELETE
  - frontend/.size-limit.json  # DELETE — size-limit gate dropped
  - .github/workflows/gitleaks.yml  # DELETE — local pre-commit only
  - .github/workflows/frontend.yml  # DELETE — replaced by ci.yml
  - .github/workflows/backend.yml  # DELETE — replaced by ci.yml
  # Modified
  - .env.example
  - frontend/package.json  # drop size-limit deps + "size" script
  - frontend/src/app/layout.tsx  # wrap in ClerkProvider
  - frontend/src/app/page.tsx  # add sign-in CTA / redirect
  - frontend/src/app/dashboard/page.tsx  # server component fetching /api/me
  - backend/app/__init__.py  # drop webhooks blueprint registration
  - backend/app/config.py  # drop CLERK_WEBHOOK_SECRET; relax CORS_ALLOWED_ORIGINS validation
  - backend/app/routes/me.py  # remove dead `users is None` branch; add sync-on-demand upsert
  - backend/tests/conftest.py  # drop SENTRY_DSN_BACKEND delenv (already), drop webhook env stubs
  - backend/tests/test_me.py  # remove db_not_configured test; add sync-on-demand test
  - backend/requirements.txt  # drop svix (webhook gone)
  - .planning/phases/01-walking-skeleton/SKELETON.md  # rewrite for Render-only shape
  - .planning/REQUIREMENTS.md  # mark SEC-01/02/03 OBS-01/02 PERF-01 as Deferred (2026-05-12 rewrite)
  - .planning/research/SUMMARY.md  # Locked Stack Decisions amendment block
  # Created
  - render.yaml
  - .github/workflows/ci.yml
  - frontend/middleware.ts
  - frontend/src/app/sign-in/[[...sign-in]]/page.tsx
  - frontend/src/app/sign-up/[[...sign-up]]/page.tsx
  - frontend/src/app/api/me/route.ts
  - frontend/src/components/sign-out-button.tsx
  - backend/tests/test_sentry_init_conditional.py
user_setup:
  - service: mongodb-atlas
    why: "Reuse the `fitgh-app` readWrite@fitgh user (already created per STATE.md). RELAX Network Access to `0.0.0.0/0` (Render egress IPs not pinnable on free/Starter). Confirm the existing rotated password is still in your password manager. SEC-04 stays satisfied via maxPoolSize=10 + tls=True at the singleton."
    env_vars:
      - name: MONGODB_URI
        source: "Existing fitgh-app connection string from your password manager (mongodb+srv://fitgh-app:<password>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority&appName=fitgh-api)"
    dashboard_config:
      - task: "Network Access -> IP Access List -> Add `0.0.0.0/0` (Allow Access From Anywhere). Confirm `fitgh-app` user still has password + readWrite@fitgh role."
        location: "Atlas Dashboard -> Network Access"
  - service: render
    why: "Single platform deploy. Both services build from the GitHub repo on `git push main`."
    env_vars:
      - name: RENDER_API_URL
        source: "After services are created, Render assigns URLs like https://fitgh-api.onrender.com and https://fitgh-web.onrender.com — back-propagate to NEXT_PUBLIC_API_URL and CLERK_AUTHORIZED_PARTIES."
    dashboard_config:
      - task: "Create Render account at https://dashboard.render.com (free; sign in with GitHub for repo access)."
        location: "Render Dashboard"
      - task: "Connect GitHub account; grant access to the FitGH repository (or all repos)."
        location: "Render Dashboard -> Account Settings -> GitHub"
      - task: "Render Blueprint flow: New + -> Blueprint -> select repo -> Render reads render.yaml -> approve `fitgh-api` (Python web service, Starter $7/mo for no cold starts) and `fitgh-web` (Node web service, Free)."
        location: "Render Dashboard -> New + -> Blueprint"
      - task: "After the Blueprint provisions, set the secrets in each service's Environment tab (MONGODB_URI, CLERK_SECRET_KEY, CLERK_AUTHORIZED_PARTIES on fitgh-api; CLERK_SECRET_KEY, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, NEXT_PUBLIC_API_URL on fitgh-web). Use Render's `sync: false` env-vars from render.yaml as the prompt."
        location: "Render Dashboard -> fitgh-api / fitgh-web -> Environment"
  - service: clerk
    why: "Single Production instance for both localhost dev and the Render deploy (one application, two authorized origins). Drops the Dev+Prod twin from the old plan."
    env_vars:
      - name: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
        source: "Clerk Dashboard -> API Keys -> Publishable key (pk_live_...)"
      - name: CLERK_SECRET_KEY
        source: "Clerk Dashboard -> API Keys -> Secret key (sk_live_...)"
    dashboard_config:
      - task: "Create a SINGLE Clerk application named `FitGH`. Skip the Dev/Prod split."
        location: "Clerk Dashboard -> Create Application"
      - task: "Enable Email/Password + Google OAuth. Leave other providers off."
        location: "Clerk Dashboard -> User & Authentication"
      - task: "Add BOTH origins to Authorized Origins: `http://localhost:3000` AND `https://fitgh-web.onrender.com` (or the Render-assigned URL)."
        location: "Clerk Dashboard -> Domains / Authorized Origins"
      - task: "Set Paths: sign-in `/sign-in`, sign-up `/sign-up`, after sign-in `/dashboard`, after sign-up `/dashboard`."
        location: "Clerk Dashboard -> Paths"

must_haves:
  truths:
    - "User can sign up via Clerk on the Render-hosted Next.js frontend"
    - "User can sign in via Clerk (email/password OR Google) on the Render-hosted Next.js frontend"
    - "After sign-in user lands on /dashboard and sees their email pulled from MongoDB Atlas via Flask"
    - "User can sign out; refreshing after sign-out lands on the sign-in screen"
    - "Flask /health on the Render fitgh-api service returns {ok:true, mongo:'connected'}"
    - "git push main triggers Render auto-deploys of both fitgh-web and fitgh-api in parallel"
    - "CI runs pytest (backend) and pnpm build (frontend) on every PR / push to main"
  artifacts:
    - path: render.yaml
      provides: "Both web services declared from one repo (Render Blueprint)"
      contains: "fitgh-api"
    - path: .github/workflows/ci.yml
      provides: "Single CI workflow with backend + frontend jobs"
      contains: "pytest"
    - path: frontend/middleware.ts
      provides: "Clerk auth middleware protecting /dashboard and /api/me"
      contains: "clerkMiddleware"
    - path: frontend/src/app/sign-in/[[...sign-in]]/page.tsx
      provides: "Clerk-hosted sign-in route"
      contains: "SignIn"
    - path: frontend/src/app/sign-up/[[...sign-up]]/page.tsx
      provides: "Clerk-hosted sign-up route"
      contains: "SignUp"
    - path: frontend/src/app/api/me/route.ts
      provides: "BFF route forwarding Clerk JWT to Flask /me (same-origin to the browser)"
      contains: "auth()"
    - path: frontend/src/app/dashboard/page.tsx
      provides: "Server component reading /api/me and rendering email"
      contains: "email"
    - path: backend/app/routes/me.py
      provides: "Authenticated /me endpoint with sync-on-demand upsert"
      contains: "g.clerk_user_id"
  key_links:
    - from: "frontend/middleware.ts"
      to: "@clerk/nextjs/server"
      via: "clerkMiddleware()"
      pattern: "clerkMiddleware"
    - from: "frontend/src/app/api/me/route.ts"
      to: "Flask /me"
      via: "fetch with Authorization: Bearer <Clerk JWT>"
      pattern: "Bearer"
    - from: "frontend/src/app/dashboard/page.tsx"
      to: "/api/me"
      via: "server-side fetch"
      pattern: "fetch.*api/me"
    - from: "backend/app/routes/me.py"
      to: "MongoDB users collection"
      via: "users.find_one + users.update_one (sync-on-demand upsert if missing)"
      pattern: "find_one|update_one"
    - from: "render.yaml"
      to: "GitHub repo"
      via: "Render Blueprint auto-deploy on push to main"
      pattern: "branch: main"
---

# Phase 1 Plan 01: Walking Skeleton (Render-only rewrite — 2026-05-12)

> This plan **replaces** the previous Phase 1 plan (Vercel + Fly.io + Clerk-twin + four CI gates), which was deprecated by the 2026-05-12 deployment-simplification rewrite. The autonomous file work already on master (Slice 0/A/B file portions, 22 backend tests, shared User JSON schema) is **kept** unless explicitly removed in Slice 0 below. Reference: `memory/render-only-rewrite.md`, `STATE.md` (2026-05-12 entry), `ROADMAP.md` Phase 1 section.

## Goal (from ROADMAP.md)

Prove the trust boundary end-to-end on Render — a Clerk-authenticated user signs in on the Render-hosted Next.js frontend, the BFF calls Flask on Render's Python web service, Flask reads the user from MongoDB Atlas, and the dashboard renders their email — all from a single `git push main` auto-deploy. One CI gate (`pytest` + `pnpm build` at deploy time), one platform (Render), three SaaS dashboard checkpoints (Atlas user, Render account, Clerk Production instance).

## User Story

**As a** Ghanaian (home or diaspora) signing up for FitGH, **I want to** create an account on the production site and land on a dashboard that knows who I am, **so that** every later feature (profile, targets, meal logging, vision) can hang off a proven auth + DB round-trip.

## Success Criteria (from ROADMAP.md — verbatim)

1. A user signs up + signs in via the Clerk Production instance (email/password OR Google) on the Render-hosted Next.js frontend, and lands on `/dashboard` showing their email pulled from MongoDB Atlas through Flask — page renders end-to-end with no shortcuts.
2. A user can sign out from any page; refreshing after sign-out lands them on the sign-in screen (Clerk session cleared).
3. The Flask `/health` endpoint returns `{ok: true, mongo: "connected"}` from the Render Starter web service, against MongoDB Atlas M0 with a `0.0.0.0/0` allowlist + 32-char password + scoped `readWrite@fitgh` role.
4. A `git push main` triggers Render auto-deploys of both web services in parallel; the backend build runs `pytest` and the frontend build runs `pnpm build` — failures halt the deploy and the previous version stays live.
5. Three SaaS dashboard checkpoints complete Phase 1 setup: (a) Atlas `fitgh-app` user with rotated password, (b) Render account linked to the GitHub repo with `fitgh-web` + `fitgh-api` services configured, (c) Clerk Production instance with the Render URL + `localhost:3000` in authorized origins. No Fly.io, no Vercel, no Sentry FE/BE wizards, no static egress IPv4 add-on, no custom gitleaks CI rules, no size-limit CI gate.

## What's already on master (DO NOT re-scaffold)

The 15 commits from the partial execution remain valid and form the base of this replan. Specifically:
- Repo scaffold: `.gitignore`, `.nvmrc`, `README.md`, `.pre-commit-config.yaml`, `.gitleaks.toml` (KEEP — used as **local** pre-commit only).
- Frontend: `frontend/package.json` (pinned to next 15.2.4 / React 19 / Tailwind v4), shadcn primitives (button/card/avatar/sonner), Inter font, `globals.css`, `layout.tsx`, placeholder `dashboard/page.tsx`.
- Backend: Flask app factory (`__init__.py`), `config.py`, `db.py` (MONGODB_URI mandatory — shim already removed), `extensions.py` (Sentry scrubber present, conditional init), `middleware/auth.py` (@require_auth with Gotcha G5 httpx.Request wrapper), `routes/health.py`, `routes/me.py`, `routes/webhooks.py` (to be deleted in Slice E), 22 tests, `requirements.txt`, `pyproject.toml`, `pytest.ini`.
- Shared: `shared/schemas/user.schema.json`.

The cleanup in Slice 0 below targets only the artefacts whose intent was the deprecated shape.

---

# Slices

## Slice 0 — Cleanup the old shape

Remove every file whose purpose was the deprecated Fly.io / Vercel / Sentry-wizard / size-limit / gitleaks-CI shape. The local gitleaks pre-commit is kept (still useful as a developer guardrail); only the CI job is dropped.

### WS-0.1 — Delete Fly.io / Docker / size-limit / gitleaks-CI artefacts

**Type:** `chore`
**Files affected:**
- DELETE `backend/Dockerfile`
- DELETE `backend/.dockerignore`
- DELETE `frontend/.size-limit.json`
- DELETE `.github/workflows/gitleaks.yml`
- DELETE `.github/workflows/frontend.yml`
- DELETE `.github/workflows/backend.yml`
- MODIFY `frontend/package.json` — remove `"size": "size-limit"` script; remove `"size-limit"` and `"@size-limit/preset-app"` from `devDependencies`; re-run `pnpm install` so `pnpm-lock.yaml` is regenerated cleanly.

**Action:** Verify each path exists with `Glob` before deleting. For each delete, use the appropriate file-delete tool (Bash `rm` is acceptable here since these are git-tracked deletions). After the package.json edit, run `cd frontend && pnpm install` to update the lockfile.

Do NOT touch `.pre-commit-config.yaml` or `.gitleaks.toml` — the local pre-commit gate remains in force; only the CI job goes away.

**Acceptance:**
- `Glob` for `backend/Dockerfile`, `backend/.dockerignore`, `frontend/.size-limit.json`, `.github/workflows/{gitleaks,frontend,backend}.yml` returns empty.
- `grep -n '"size"\|size-limit' frontend/package.json` returns zero hits.
- `cd frontend && pnpm install --frozen-lockfile=false && pnpm build` succeeds.

**Expected commit message:** `chore(phase-01): drop Fly/Docker/size-limit/gitleaks-CI artefacts (2026-05-12 rewrite)`

**Depends on:** none

---

### WS-0.2 — Trim `.env.example` and drop server-side webhook envs

**Type:** `chore`
**Files affected:**
- MODIFY `.env.example`

**Action:** Rewrite `.env.example` to the new minimal surface. Remove `SENTRY_DSN_BACKEND`, `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_AUTH_TOKEN`, `CLERK_WEBHOOK_SECRET`, `CORS_ALLOWED_ORIGINS`, `BACKEND_URL`, `NEXT_PUBLIC_APP_URL`. Keep `MONGODB_URI`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `CLERK_AUTHORIZED_PARTIES`, `FLASK_ENV`. Add `NEXT_PUBLIC_API_URL` (the BFF reads this to call Flask — `http://localhost:8000` locally, the Render fitgh-api URL in production). Document each var with a one-line comment indicating where it comes from (Atlas / Clerk dashboard / Render env tab).

**Acceptance:**
- `cat .env.example` shows only the five-key set above plus `NEXT_PUBLIC_API_URL` and `FLASK_ENV`.
- No occurrence of `SENTRY`, `WEBHOOK`, `CORS_ALLOWED`, `VERCEL` in the file.

**Expected commit message:** `chore(phase-01): trim .env.example to Render-only surface`

**Depends on:** WS-0.1

---

## Slice A — User dashboard checkpoints (3 SaaS-only)

The three Success-Criterion-5 checkpoints. **WS-A.1 is mostly a verify** (the Atlas user was created on 2026-05-11 per STATE.md decisions); only the network-access relaxation is new.

### WS-A.1 — Atlas: relax allowlist to 0.0.0.0/0 + verify fitgh-app user

**Type:** `checkpoint:human-action`
**Files affected:** none (external dashboard work)

**What user must do:**
1. Sign in to https://cloud.mongodb.com/.
2. **Database Access** — verify the `fitgh-app` user exists with role `readWrite@fitgh` (NOT atlasAdmin, NOT readWriteAnyDatabase). If the password is no longer in your password manager, rotate now and capture the new ≥32-char password.
3. **Network Access -> IP Access List -> Add IP Address -> Allow Access From Anywhere (`0.0.0.0/0`)**. Confirm the entry shows `0.0.0.0/0`. (This relaxes the dev-IP-only rule from the old WS-0.1 — Render web services don't have pinnable egress IPs on the free / Starter tier.)
4. Open **Database -> Connect -> Drivers** and copy the new connection string. It should look like `mongodb+srv://fitgh-app:<password>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority&appName=fitgh-api`. Store only in your password manager.

**Confirmation phrase (paste in chat, redacted):** `Atlas: fitgh-app verified with readWrite@fitgh, allowlist relaxed to 0.0.0.0/0, MONGODB_URI captured in password manager.`

**Acceptance:**
- User pastes the confirmation phrase.
- Allowlist entry `0.0.0.0/0` is present in Atlas Network Access.

**Expected commit message:** none (no file change)

**Depends on:** WS-0.2

---

### WS-A.2 — Render: account + GitHub link

**Type:** `checkpoint:human-action`
**Files affected:** none

**What user must do:**
1. Sign up for Render at https://dashboard.render.com (sign in with GitHub for repo access; this is the easiest path).
2. **Account Settings -> GitHub** — connect the account; grant access either to the FitGH repository or "All repositories" (account-wide grant is fine for a solo build).
3. **Do NOT create services yet** — Slice B writes the `render.yaml` Blueprint that creates them automatically. Just confirm the GitHub repo is visible from Render's "New +" menu.

**Confirmation phrase (paste in chat):** `Render: account linked to GitHub; FitGH repo visible from New + -> Blueprint.`

**Acceptance:**
- User pastes the confirmation phrase.

**Expected commit message:** none

**Depends on:** WS-A.1

---

### WS-A.3 — Clerk: single Production instance + dual origins

**Type:** `checkpoint:human-action`
**Files affected:** none (capture env values for later)

**What user must do:**
1. Sign in to https://dashboard.clerk.com/.
2. **Create application** -> name `FitGH`. Single instance — not Dev/Prod twin. Authentication providers: enable **Email/Password** and **Google OAuth**; leave others OFF.
3. **Paths**: sign-in `/sign-in`, sign-up `/sign-up`, after-sign-in `/dashboard`, after-sign-up `/dashboard`.
4. **Domains / Authorized Origins**: add BOTH `http://localhost:3000` AND the Render frontend URL (you can use `https://fitgh-web.onrender.com` as a placeholder for now and update post-WS-F.1 if Render assigns a different slug).
5. **API Keys** — copy the **Publishable Key** (`pk_live_...`) and **Secret Key** (`sk_live_...`). Store in your password manager.

**Confirmation phrase (paste in chat):** `Clerk: single FitGH instance created, both origins (localhost:3000 + Render URL) added, pk_live_ + sk_live_ captured in password manager.`

**Acceptance:**
- User pastes the confirmation phrase.

**Expected commit message:** none

**Depends on:** WS-A.2

---

## Slice B — render.yaml + build wiring

### WS-B.1 — Create `render.yaml` Blueprint at repo root

**Type:** `code`
**Files affected:**
- CREATE `render.yaml`

**Action:** Author a Render Blueprint declaring two web services from one repo. Service `fitgh-api`: `rootDir: backend`, `env: python`, `runtime: python-3.12`, `buildCommand: pip install -r requirements.txt`, `startCommand: gunicorn 'app:create_app()' --workers 2 --threads 4 --timeout 60 --bind 0.0.0.0:$PORT`, `plan: starter` (the $7/mo Starter tier avoids cold-start latency on the snap-meal loop in Phase 4 — locked in now so it's not a Phase 4 surprise), `healthCheckPath: /health`, `autoDeploy: true`, `branch: main`. Service `fitgh-web`: `rootDir: frontend`, `env: node`, `buildCommand: corepack enable && corepack prepare pnpm@10 --activate && pnpm install --frozen-lockfile && pnpm build`, `startCommand: pnpm start`, `plan: free` (acceptable for the frontend in Phase 1 — Phase 7 can upgrade if Ghana p75 latency demands it), `autoDeploy: true`, `branch: main`. Each service declares its env-var contract via `envVars` entries with `sync: false` so Render prompts the user to paste secrets at Blueprint provision time. Backend env: `MONGODB_URI`, `CLERK_SECRET_KEY`, `CLERK_AUTHORIZED_PARTIES`, `FLASK_ENV=production`, `PYTHON_VERSION=3.12.7`. Frontend env: `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_URL` (will be set to the `fitgh-api` Render URL once provisioned — Render's `fromService` directive can interpolate this), `NODE_VERSION=20`.

Do NOT include a Dockerfile reference — Render's Python buildpack handles Python services from a `requirements.txt` automatically (the Dockerfile was deleted in WS-0.1).

**Acceptance:**
- `render.yaml` exists at repo root.
- `grep -c 'fitgh-api\|fitgh-web' render.yaml` returns at least 2.
- `grep -c 'sync: false' render.yaml` is at least 5 (one per secret env var across both services).
- A YAML parser (`python -c "import yaml; yaml.safe_load(open('render.yaml'))"`) accepts the file without error.

**Expected commit message:** `feat(phase-01): add render.yaml Blueprint for fitgh-api + fitgh-web`

**Depends on:** WS-0.2

---

## Slice C — Simplify CI

### WS-C.1 — Single `ci.yml` workflow (pytest + pnpm build in parallel)

**Type:** `ci`
**Files affected:**
- CREATE `.github/workflows/ci.yml`

**Action:** One workflow with two parallel jobs. Triggers: `on: { push: { branches: [main] }, pull_request: { branches: [main] } }`. Job `backend`: `defaults.run.working-directory: backend`, sets up Python 3.12 via `actions/setup-python@v5` with `cache: pip` and `cache-dependency-path: backend/requirements*.txt`, installs `requirements.txt + requirements-dev.txt`, runs `ruff check .` then `pytest -x --cov=app --cov-report=term-missing`. Job `frontend`: `defaults.run.working-directory: frontend`, sets up pnpm via `pnpm/action-setup@v4` with `version: 10`, Node 20 via `actions/setup-node@v4` with `node-version-file: .nvmrc` and `cache: pnpm`, runs `pnpm install --frozen-lockfile` then `pnpm lint` then `pnpm tsc --noEmit` then `pnpm build`. Both jobs `continue-on-error: false`. No size-limit step. No docker-build-smoke step. No gitleaks step. (Pre-commit hooks still run gitleaks locally — see `.pre-commit-config.yaml`.)

**Acceptance:**
- `.github/workflows/ci.yml` parses as valid YAML.
- `grep -c '^  backend:\|^  frontend:' .github/workflows/ci.yml` returns 2 (two jobs).
- No occurrence of `size-limit`, `gitleaks`, `docker build` in the file.
- Locally: `cd backend && .venv/Scripts/python.exe -m pytest -q` still reports 22 - 4 = **18 passing** (the 4 test_webhooks.py tests will be removed in Slice E; until then pytest passes 22). After Slice E lands the count is 18 + 2 new sentry-init-conditional tests = 20.

**Expected commit message:** `ci(phase-01): replace three workflows with single ci.yml (pytest + pnpm build)`

**Depends on:** WS-0.1

---

## Slice D — Frontend auth + dashboard

### WS-D.1 — Install Clerk + wire ClerkProvider + middleware

**Type:** `code`
**Files affected:**
- MODIFY `frontend/package.json` (add `@clerk/nextjs@^5`)
- MODIFY `frontend/src/app/layout.tsx` (wrap children in `<ClerkProvider>`)
- CREATE `frontend/middleware.ts`

**Action:** `cd frontend && pnpm add @clerk/nextjs` (latest 5.x — confirm `pnpm-lock.yaml` updates). In `layout.tsx`, wrap `<html lang="en">` with `<ClerkProvider>` (default props are fine — environment variables `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` flow automatically). Create `frontend/middleware.ts` using `clerkMiddleware` from `@clerk/nextjs/server`: protect `/dashboard(.*)` and `/api/me`, leave `/`, `/sign-in(.*)`, `/sign-up(.*)` public. Export a `config` object with the standard `matcher` that runs middleware on all paths except `_next` static + image-optim. Reference: the Clerk Next.js App Router quick-start pattern as of Clerk 5.x.

**Acceptance:**
- `pnpm install --frozen-lockfile` (after edit) succeeds.
- `frontend/middleware.ts` exports `default` from `clerkMiddleware(...)` and a `config` with `matcher`.
- `cd frontend && pnpm build` succeeds.
- `grep -n 'ClerkProvider' frontend/src/app/layout.tsx` returns a hit.

**Expected commit message:** `feat(phase-01): wire Clerk provider + middleware`

**Depends on:** WS-C.1

---

### WS-D.2 — Sign-in + Sign-up routes (Clerk-hosted UI)

**Type:** `code`
**Files affected:**
- CREATE `frontend/src/app/sign-in/[[...sign-in]]/page.tsx`
- CREATE `frontend/src/app/sign-up/[[...sign-up]]/page.tsx`
- MODIFY `frontend/src/app/page.tsx` (replace the placeholder home with a "Sign in to FitGH" CTA linking to `/sign-in`, OR redirect signed-in users to `/dashboard`)

**Action:** Use Clerk's `<SignIn />` and `<SignUp />` components (client components — add `"use client"` directive). Each page renders the component centered in a `<main>` element with the shadcn Card primitive optionally framing it. The home page (`page.tsx`) becomes a small landing: a card with project name + tagline + two buttons (Sign in / Sign up) linking to the respective routes. Do NOT add additional styling complexity — Clerk's default appearance is acceptable for Phase 1; Phase 5 will theme.

**Acceptance:**
- `cd frontend && pnpm build` succeeds with the new routes in the route table.
- `frontend/src/app/sign-in/[[...sign-in]]/page.tsx` exports a default React component that renders `<SignIn />`.
- Same for `sign-up`.
- Visiting `http://localhost:3000/sign-in` in `pnpm dev` shows the Clerk-hosted sign-in widget (verified locally after WS-F.0).

**Expected commit message:** `feat(phase-01): add /sign-in and /sign-up Clerk routes`

**Depends on:** WS-D.1

---

### WS-D.3 — BFF route `/api/me` + dashboard fetch

**Type:** `code`
**Files affected:**
- CREATE `frontend/src/app/api/me/route.ts`
- MODIFY `frontend/src/app/dashboard/page.tsx`
- CREATE `frontend/src/components/sign-out-button.tsx`

**Action:** **`route.ts`** — Server-side Route Handler exporting `async function GET(req: NextRequest)`. Use `auth()` from `@clerk/nextjs/server` to get the userId AND `await auth().getToken()` to fetch the session JWT. If no auth, return `Response.json({error:'unauthorized'}, {status:401})`. Otherwise `fetch(`${process.env.NEXT_PUBLIC_API_URL}/me`, { headers: { Authorization: `Bearer ${token}` }, cache: 'no-store' })` and proxy the response body and status back to the caller. Add `export const dynamic = 'force-dynamic'` so Next.js never tries to cache a per-user response.

**`dashboard/page.tsx`** — Refit from placeholder to server component that calls the BFF: build the absolute URL via `headers()` (Next.js 15 App Router pattern — `const h = await headers(); const proto = h.get('x-forwarded-proto') ?? 'http'; const host = h.get('host');` then `fetch(`${proto}://${host}/api/me`, { headers: { cookie: h.get('cookie') ?? '' }, cache: 'no-store' })`). If 401, redirect to `/sign-in` via `redirect('/sign-in')`. Otherwise read `{email}` from the JSON body and render it inside the existing shadcn Card with a `<SignOutButton />` next to the email. Keep the avatar placeholder.

**`sign-out-button.tsx`** — Client component (`"use client"`) using `<SignOutButton />` from `@clerk/nextjs` wrapping a shadcn `<Button>` labeled "Sign out". After sign-out Clerk redirects to `/sign-in` (Clerk handles this via its `redirectUrl` prop — set to `/sign-in`).

**Acceptance:**
- `cd frontend && pnpm build` succeeds; route table includes `/api/me`, `/dashboard`, `/sign-in`, `/sign-up`.
- `grep -n 'Bearer' frontend/src/app/api/me/route.ts` returns a hit (Bearer JWT forwarding wired).
- `grep -n "fetch.*api/me" frontend/src/app/dashboard/page.tsx` returns a hit.
- `grep -n 'SignOutButton\|@clerk/nextjs' frontend/src/components/sign-out-button.tsx` returns at least 2 hits.
- Note: full end-to-end verification (sign-up + email rendered) happens in WS-F.1; local `pnpm dev` may show 401 from `/api/me` until `NEXT_PUBLIC_API_URL` is set in `.env.local`.

**Expected commit message:** `feat(phase-01): BFF /api/me + /dashboard fetch + sign-out`

**Depends on:** WS-D.2

---

## Slice E — Backend trim + sync-on-demand `/me`

### WS-E.1 — Delete webhook route + test; drop blueprint registration + svix dep

**Type:** `chore`
**Files affected:**
- DELETE `backend/app/routes/webhooks.py`
- DELETE `backend/tests/test_webhooks.py`
- MODIFY `backend/app/__init__.py` (drop `from app.routes.webhooks import bp as webhooks_bp` + `app.register_blueprint(webhooks_bp)`)
- MODIFY `backend/requirements.txt` (remove the `svix>=1.30` line)
- MODIFY `backend/tests/conftest.py` (no env-stub change strictly required; if there's a webhook-specific stub, drop it — current conftest.py has none, so this is a no-op but keep an eye on it)

**Action:** Webhooks are dropped from the architecture; sync-on-demand replaces them (WS-E.2). After this task, `pytest` should report `22 - 4 = 18` passing (the four `test_webhooks` tests vanish with the file).

**Acceptance:**
- `Glob` for `backend/app/routes/webhooks.py` and `backend/tests/test_webhooks.py` returns empty.
- `grep -n 'webhooks' backend/app/__init__.py` returns zero hits.
- `grep -n 'svix' backend/requirements.txt` returns zero hits.
- `cd backend && .venv/Scripts/python.exe -m pytest -q` reports 18 passing (no failures, no errors).

**Expected commit message:** `chore(phase-01): drop Clerk webhook route + svix dep (sync-on-demand replaces)`

**Depends on:** WS-D.3

---

### WS-E.2 — `/me` sync-on-demand upsert + remove dead `users is None` branch

**Type:** `code` (with `tdd="true"` — see `<behavior>` below)
**Files affected:**
- MODIFY `backend/app/routes/me.py`
- MODIFY `backend/tests/test_me.py`

**Behavior (write tests first):**
- Test 1: When the user is authenticated and a `users` doc exists for `clerk_user_id`, `/me` returns `200 {email: <existing-email>}` (mongomock-backed).
- Test 2: When the user is authenticated and NO `users` doc exists, `/me` upserts a new doc with `{clerk_id, email: <from-JWT-claim>, created_at, updated_at}` and returns `200 {email: <from-JWT-claim>}`. Verify the doc exists in mongomock after the call.
- Test 3 (kept): `/me` without an Authorization header returns 401 with `{error: 'unauthorized', reason: <str>}`.
- Test 4 (kept): `/me` with an invalid bearer token returns 401.
- REMOVE the existing `test_me_returns_503_when_db_not_configured` test — that branch is being deleted (db.py shim is already gone; `users` is always a real `Collection`).

**Action:** Rewrite `me.py`. Drop the `if users is None: return 503` branch entirely (dead code — `db.py` raises `KeyError` at import if `MONGODB_URI` is unset, so `users` is never None). When `users.find_one({"clerk_id": g.clerk_user_id})` returns `None`, perform an upsert from the JWT claims: read `g.clerk_user_id` and email from the Clerk session (the existing middleware sets `g.clerk_user_id`; we also need email — extend the middleware to set `g.clerk_email = state.payload.get('email')` if present, OR fall back to calling `Clerk(...).users.get(g.clerk_user_id).email_addresses[0].email_address` only on the missing-user path so steady-state requests stay networkless). Document the design tradeoff inline: the email is needed for the dashboard render, and pulling it from Clerk's session JWT is fine if Clerk includes it in the token claims by default (most Clerk applications do); if not, the SDK fetch on the missing-user path adds one HTTPS hop the first time only, which is acceptable.

Sync-on-demand pattern: `users.update_one({"clerk_id": ...}, {"$setOnInsert": {"clerk_id": ..., "email": ..., "created_at": now}, "$set": {"updated_at": now}}, upsert=True)` then re-read.

**Acceptance:**
- All 4 listed tests pass (Tests 1, 2, 3, 4); old 503 test is removed.
- `cd backend && .venv/Scripts/python.exe -m pytest -q backend/tests/test_me.py -v` reports 4 passing.
- `grep -n 'db_not_configured' backend/app/routes/me.py` returns zero hits.
- `grep -n 'users is None' backend/app/routes/me.py` returns zero hits.

**Expected commit message:** `feat(phase-01): /me sync-on-demand upsert; remove dead db_not_configured branch`

**Depends on:** WS-E.1

---

### WS-E.3 — Make Sentry init explicit-conditional + add test

**Type:** `code` (with `tdd="true"`)
**Files affected:**
- MODIFY `backend/app/extensions.py` (already conditional; keep the early-return — the change is mostly documentary + a test)
- CREATE `backend/tests/test_sentry_init_conditional.py`

**Behavior (write test first):**
- Test 1: With `SENTRY_DSN_BACKEND` unset, `init_sentry(Config())` is a no-op (does NOT call `sentry_sdk.init`). Use `unittest.mock.patch` on `sentry_sdk.init` to assert it was not called.
- Test 2: With `SENTRY_DSN_BACKEND=https://stub@sentry.io/12345`, `init_sentry(cfg)` calls `sentry_sdk.init` once with `before_send=scrub` in the kwargs.

**Action:** The existing `extensions.py` already has the `if not cfg.SENTRY_DSN_BACKEND: return` guard. Add a comment block at the top of `init_sentry` documenting that Sentry is OPTIONAL in Phase 1 (deferred OBS-01 per the 2026-05-12 rewrite) — the scrubber code stays in place so re-enabling is one env-var away. Add the test. The existing `test_sentry_scrubber.py` (7 cases) is preserved as-is and continues to assert the scrubber contract for the day Sentry comes back.

**Acceptance:**
- `cd backend && pytest -q backend/tests/test_sentry_init_conditional.py -v` reports 2 passing.
- Full suite still green: 18 (post-WS-E.1) - 1 (removed 503 test) + 2 (sentry-init) + 1 (E.2 net: added 2 new, kept 2 — actually +1 net) = **20 passing**.

Net test count math: started 22, removed 4 webhook tests + 1 db_not_configured test = 17, added 2 sync-on-demand tests = 19, added 2 sentry-init tests = **21** passing. (Rough — exact number depends on whether the `test_me_with_invalid_bearer_returns_401` test is kept; assume yes.)

**Expected commit message:** `test(phase-01): assert Sentry init is conditional on SENTRY_DSN_BACKEND`

**Depends on:** WS-E.2

---

### WS-E.4 — Relax `Config.validate()` for CORS_ALLOWED_ORIGINS + CLERK_WEBHOOK_SECRET

**Type:** `code`
**Files affected:**
- MODIFY `backend/app/config.py`

**Action:** In `Config.validate()` (the production check), remove `CORS_ALLOWED_ORIGINS` from the `missing` list — under Render the BFF and Flask are different hostnames but the browser only ever calls the BFF (same-origin), so Flask doesn't need to whitelist any cross-origin browser. Keep the `flask-cors` wiring in `__init__.py` but allow `cfg.CORS_ALLOWED_ORIGINS` to be an empty list at runtime (Flask-CORS will then reject all cross-origin browser calls, which is the intended behavior — the BFF calls Flask from a Render-internal hop). Drop `CLERK_WEBHOOK_SECRET` from the dataclass (no longer used after WS-E.1).

If existing tests in `test_cors.py` rely on a populated allowlist, keep them — they test the `flask-cors` behavior when an allowlist IS set, which is still a valid production posture if the user later adds a non-BFF caller.

**Acceptance:**
- `grep -n 'CLERK_WEBHOOK_SECRET' backend/app/config.py` returns zero hits.
- `cd backend && pytest -q` shows the full suite passing (~21 tests).
- `Config(FLASK_ENV='production', CLERK_SECRET_KEY='x', CLERK_AUTHORIZED_PARTIES=['x'], MONGODB_URI='x').validate()` succeeds without setting CORS_ALLOWED_ORIGINS (verify by adding a one-off test or by `python -c` smoke).

**Expected commit message:** `refactor(phase-01): drop CLERK_WEBHOOK_SECRET; CORS allowlist optional (BFF same-origin)`

**Depends on:** WS-E.3

---

## Slice F — Deploy + end-to-end verify

### WS-F.0 — Local end-to-end smoke before pushing

**Type:** `checkpoint:human-verify`
**Files affected:** none (verification step)

**What user must do:**
1. Create `backend/.env` (gitignored — confirm `git status` does NOT list it) with `MONGODB_URI=<from WS-A.1>`, `CLERK_SECRET_KEY=<sk_live_... from WS-A.3>`, `CLERK_AUTHORIZED_PARTIES=http://localhost:3000`, `FLASK_ENV=development`.
2. Create `frontend/.env.local` (gitignored) with `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<pk_live_... from WS-A.3>`, `CLERK_SECRET_KEY=<sk_live_...>`, `NEXT_PUBLIC_API_URL=http://localhost:8000`.
3. Two terminals:
   - **Backend:** `cd backend && .\.venv\Scripts\Activate.ps1; python -m flask --app app:create_app run -p 8000`
   - **Frontend:** `cd frontend && pnpm dev` (Turbopack on port 3000)
4. In a browser at `http://localhost:3000`: click Sign up, create a test account (use a real or burner email), Clerk redirects to `/dashboard`, the dashboard fetches `/api/me` -> Flask `/me` -> Atlas, you see your email rendered. Click Sign out, refresh, you land on `/sign-in`.
5. Also verify `curl http://localhost:8000/health` returns `{"ok": true, "mongo": "connected"}`.

**Confirmation phrase:** `Local E2E green: signed up, saw email on /dashboard, signed out, /health returns mongo:connected.`

**Acceptance:**
- User pastes the confirmation phrase.
- A test user was created in Clerk + a matching `users` doc landed in Atlas (verify via Atlas Data Explorer).

**Expected commit message:** none

**Depends on:** WS-E.4

---

### WS-F.1 — Push to main; provision Render Blueprint; capture URLs

**Type:** `checkpoint:human-action`
**Files affected:** none

**What user must do:**
1. **Push:** `git push origin main` (assumes the remote is configured; if not, `git remote add origin <github-repo-url> && git push -u origin main`).
2. In Render: **New + -> Blueprint -> select the FitGH repo**. Render reads `render.yaml`, lists `fitgh-api` (Starter $7/mo) + `fitgh-web` (Free), and prompts for the `sync: false` env vars. Paste:
   - `fitgh-api`: `MONGODB_URI`, `CLERK_SECRET_KEY`, `CLERK_AUTHORIZED_PARTIES` (set to `https://<frontend-render-url>` once you know it — for now paste a placeholder, Render lets you edit later).
   - `fitgh-web`: `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_URL` (set to the `fitgh-api` Render URL — visible immediately after provision).
3. Wait for first deploy. Both services should turn green within ~5 minutes (backend build runs `pip install` + Python buildpack starts gunicorn; frontend build runs `pnpm install --frozen-lockfile && pnpm build` + Node starts `pnpm start`).
4. Once `fitgh-web` is live, return to the **Clerk dashboard** and update **Authorized Origins** with the actual `fitgh-web` URL (the placeholder from WS-A.3 was a guess). Same for `fitgh-api`'s `CLERK_AUTHORIZED_PARTIES` env var.
5. Verify CI: open the PR (or push commit) page on GitHub — the `ci.yml` workflow should show `backend` and `frontend` jobs running in parallel.

**Confirmation phrase:** `Render: both services green; fitgh-web URL = <url>, fitgh-api URL = <url>; Clerk origins updated; CI workflow green.`

**Acceptance:**
- User pastes the confirmation phrase with actual URLs.
- `https://<fitgh-api-url>/health` returns `{"ok": true, "mongo": "connected"}` (verify in chat by running `curl` from your machine).
- The `ci.yml` workflow shows a green check on the latest commit.

**Expected commit message:** none

**Depends on:** WS-F.0

---

### WS-F.2 — End-to-end sign-off on the deployed app

**Type:** `checkpoint:human-verify`
**Files affected:** none (final acceptance gate)

**What user must do:**
1. Open `https://<fitgh-web-url>` in a browser.
2. Click **Sign up** -> create an account (use a separate test email from the local-smoke account in WS-F.0).
3. Confirm: redirected to `/dashboard`, email is rendered.
4. Click **Sign out**.
5. Refresh — you should land on `/sign-in`.
6. Click **Sign in** with the same credentials -> back on `/dashboard` with email.
7. Verify in Atlas Data Explorer that a `users` doc exists for this clerk_id.
8. Verify `curl https://<fitgh-api-url>/health` returns `{"ok": true, "mongo": "connected"}`.

**Confirmation phrase:** `Phase 1 E2E PASSED on deployed app: signup -> email rendered -> sign-out -> sign-in works; users doc in Atlas; /health green.`

**Acceptance:**
- User pastes the confirmation phrase.
- All five Success Criteria from ROADMAP.md Phase 1 are satisfied — verify each one in writing before moving on to Slice G.

**Expected commit message:** none

**Depends on:** WS-F.1

---

## Slice G — Docs + spec cleanup

### WS-G.1 — Rewrite `SKELETON.md` for the Render-only shape

**Type:** `docs`
**Files affected:**
- MODIFY `.planning/phases/01-walking-skeleton/SKELETON.md`

**Action:** The existing SKELETON.md describes the Fly.io + Vercel + Clerk-twin architecture. Rewrite the **Architectural Decisions** table: Frontend host = Render (Node web service, Free), Backend host = Render (Python web service, Starter), CI = single `ci.yml` (pytest + pnpm build), Observability = "deferred OBS-01 — Sentry scrubber code in place but disabled until SENTRY_DSN_BACKEND is set", Secrets = "Render env vars (`sync: false` per render.yaml); local pre-commit gitleaks (no CI job)". Drop the "Static egress IP pinned in Atlas allowlist" row; replace with "Atlas allowlist `0.0.0.0/0` + 32-char password + scoped readWrite@fitgh user". Update the **Capability Proven End-to-End** narrative to remove the Fly.io JNB reference. Update the **Stack Touched in Phase 1** "Deployment" bullet. Re-write the **Phase 1 Acceptance Checklist** at the bottom to match the new five ROADMAP success criteria verbatim. Use the template at `$HOME/.claude/get-shit-done/references/skeleton-template.md` as the shape reference, but you are editing the existing file in place.

**Acceptance:**
- `grep -n 'Fly\.io\|Vercel\|jnb\|egress IP\|size-limit\|Sentry FE' .planning/phases/01-walking-skeleton/SKELETON.md` returns zero hits.
- `grep -n 'Render' .planning/phases/01-walking-skeleton/SKELETON.md` returns at least 5 hits.
- The five Acceptance Checklist items match the ROADMAP Phase 1 Success Criteria verbatim.

**Expected commit message:** `docs(phase-01): rewrite SKELETON.md for Render-only architecture`

**Depends on:** WS-F.2

---

### WS-G.2 — Update REQUIREMENTS.md traceability table + research/SUMMARY.md amendment

**Type:** `docs`
**Files affected:**
- MODIFY `.planning/REQUIREMENTS.md`
- MODIFY `.planning/research/SUMMARY.md`

**Action:** In `REQUIREMENTS.md`, find the traceability table (or the per-requirement status block) and mark these requirements as `Deferred (2026-05-12 rewrite — see ROADMAP.md Phase 1 note + memory/render-only-rewrite.md)`: **SEC-01**, **SEC-02**, **SEC-03**, **OBS-01**, **OBS-02**, **PERF-01**. Mark **DEPLOY-01** and **DEPLOY-02** as `In progress (Render)`. Mark **AUTH-01/02/03/06** and **SEC-04** as `Phase 1 closing on Render deploy`.

In `research/SUMMARY.md`, add a new section near the top of the "Locked Stack Decisions" block titled **`Stack amendment 2026-05-12: Render-only deploy`**. Inside, summarize the swap: out = Vercel + Fly.io + Clerk-twin + four-CI-gates + Sentry-wizard; in = Render single-platform + Clerk single Production + one CI workflow. List the requirement deferrals (SEC-01/02/03, OBS-01/02, PERF-01) and the rationale (operational complexity > user value at solo-build scale). Cross-link to `memory/render-only-rewrite.md`. Do NOT delete or modify the original "Locked Stack Decisions" entries — they remain a record of what we considered and chose against in v1.

**Acceptance:**
- `grep -n 'Deferred (2026-05-12' .planning/REQUIREMENTS.md` returns at least 6 hits.
- `grep -n 'Stack amendment 2026-05-12' .planning/research/SUMMARY.md` returns a hit.
- Both files render cleanly (no broken markdown — check by reading the diff).

**Expected commit message:** `docs(phase-01): mark deferrals in REQUIREMENTS.md + Stack amendment in research SUMMARY`

**Depends on:** WS-G.1

---

# Threat Model (trimmed)

## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| browser -> Next.js BFF | TLS-terminated at Render edge; same-origin from the browser's POV (Render assigns one hostname per service, but the browser only ever calls `fitgh-web`). |
| Next.js BFF -> Flask | Render-internal hop, with `Authorization: Bearer <Clerk JWT>` set by the BFF. Flask verifies the JWT networkless via clerk-backend-api against the cached JWKS. |
| Flask -> Atlas | TLS to `cluster0.pcd3g.mongodb.net` via PyMongo singleton (`tls=True`, `maxPoolSize=10`). |

## STRIDE Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-01 | Spoofing | `/dashboard` route | mitigate | Clerk middleware (`middleware.ts`) requires a session before render — unauthenticated requests redirect to `/sign-in`. |
| T-01-02 | Spoofing | Flask `/me` | mitigate | `@require_auth` verifies the Clerk JWT networkless (Gotcha G5 httpx.Request wrapper). |
| T-01-03 | Tampering | BFF -> Flask hop | mitigate | The BFF reads `await auth().getToken()` directly from the verified session; the browser never sees or sets the JWT, so it cannot be tampered in transit (TLS to Render + same-origin to the BFF). |
| T-01-04 | Info disclosure (Mongo URI leak) | repo | accept | Default gitleaks ruleset misses MongoDB URIs; the custom rules in `.gitleaks.toml` cover this via the LOCAL pre-commit hook. The CI gitleaks job is dropped (2026-05-12 rewrite) — risk re-rated as acceptable given the local pre-commit + Render env-var isolation. Re-enable CI rule if a real leak occurs. |
| T-01-05 | Info disclosure (Sentry PII) | extensions.py | mitigate | Scrubber present at `sentry_sdk.init()` (drops Authorization header, user.email/username/id, extra.email/user_id, breadcrumbs[].data.image/kcal/email). 7 unit tests assert the contract. Sentry currently OFF by default — re-enabling is one env-var away and the contract is enforced from commit 1. |
| T-01-06 | Repudiation | n/a Phase 1 | accept | Out of scope; no audit log required for Phase 1. |
| T-01-07 | DoS (cluster connection storm) | db.py | mitigate | `MongoClient(..., maxPoolSize=10)` enforced at module-scope singleton; tested via `test_db_singleton_uses_max_pool_size_10_and_tls`. |
| T-01-08 | DoS (open Atlas allowlist) | Atlas | accept | `0.0.0.0/0` allowlist accepted for MVP — defense is the 32-char `fitgh-app` password + `readWrite@fitgh` (no admin) + TLS-only. Re-evaluate if a Render egress-IP allowlist becomes available on a tier we use. |
| T-01-09 | Elevation of privilege (Mongo user) | Atlas | mitigate | `fitgh-app` is `readWrite@fitgh` only — cannot read other databases, cannot drop the cluster. |
| T-01-10 | Elevation of privilege (unverified Clerk header) | Flask | mitigate | Flask never trusts `X-User-Id` or any forwarded header; the trust anchor is `@require_auth` running Clerk's verifier on every protected route. |

## Threats from the old plan that are now MOOT or RE-RATED

- T-01-04 (Mongo URI in git): re-rated `accept` — local pre-commit still blocks it; no CI gate. Acceptable because the user owns local commits and the `.gitleaks.toml` rules ship with the repo.
- (Old) T-01-08 connection storm: still mitigated (SEC-04 is retained).
- (Old) T-01-11 CORS misconfig: BFF same-origin removes the cross-origin browser path; Flask-CORS allowlist is still wired but no longer load-bearing — tests in `test_cors.py` continue to assert the never-`*`-with-credentials posture.

---

# Test Plan

## Tests retained from the partial execution

After Slice E lands, the suite contains:

| Test file | Tests | What's tested |
|-----------|-------|---------------|
| `test_health.py` | 2 | Connected + error paths of `/health` |
| `test_me.py` | 4 | 401 no-auth, 401 bad-bearer, 200 with existing user (NEW), 200 with sync-on-demand upsert (NEW) |
| `test_cors.py` | as-existing | CORS allowlist never `*`-with-credentials (still valid posture) |
| `test_db.py` | 2 | maxPoolSize=10 + tls=True; KeyError when MONGODB_URI unset |
| `test_sentry_scrubber.py` | 7 | Scrubber redaction contract (Authorization, user.email, breadcrumbs.data.{image,kcal,email}) |
| `test_sentry_init_conditional.py` | 2 | NEW — init is no-op when DSN unset; calls `sentry_sdk.init` with `before_send=scrub` when DSN set |

**Removed:** `test_webhooks.py` (4 tests; webhook route gone), `test_me.py::test_me_returns_503_when_db_not_configured` (db_not_configured branch gone).

**Expected total:** ~21 backend tests passing after the full plan executes.

## Frontend tests (not added in Phase 1)

`pnpm build` succeeding is the only frontend gate in this plan — full type-check via `pnpm tsc --noEmit` runs in CI. Phase 2 (onboarding forms) is where Vitest / Playwright land.

## Smoke tests at deploy time

- `render.yaml` parse smoke: `python -c "import yaml; yaml.safe_load(open('render.yaml'))"` (runs locally before push).
- Render's own healthcheck (`healthCheckPath: /health`) is the deploy-time gate — if `/health` returns non-200 within Render's healthcheck window, the deploy is marked failed and the previous version stays live (satisfies Success Criterion 4).

---

# Estimated Duration

- **Executor work** (Claude, all `code`/`chore`/`ci`/`docs`/`test` tasks above): **~4-5 hours**.
- **User dashboard time** (Slice A WS-A.1/2/3 + Slice F WS-F.0/1/2): **~60-90 minutes** spread across Atlas (5 min), Render (20-40 min including first deploy wait), Clerk (10 min), plus E2E verification (~20 min).
- **Total wall-clock to Phase 1 sign-off:** ~6-7 hours.

---

# Self-Check (Planner)

Before declaring this plan ready for the checker:

- [x] Every locked decision in the ROADMAP Phase 1 entry has a task: AUTH-01/02/03 (WS-D.1/D.2), AUTH-06 (WS-D.3 + WS-E.2), SEC-04 (already on master, asserted by `test_db.py`), DEPLOY-01 (WS-B.1 + WS-F.1 for the frontend service), DEPLOY-02 (WS-B.1 + WS-F.1 for the backend service).
- [x] No task touches Fly.io, Vercel, Sentry-wizard, size-limit, gitleaks-CI, Cloudflare, or static egress IP.
- [x] No task re-scaffolds files already on master (Flask factory, db.py, middleware/auth.py, shadcn primitives, Tailwind v4 setup, 22 backend tests — only modifications + deletions where required).
- [x] User-checkpoint tasks include exact dashboard steps, env vars to capture, and an explicit confirmation phrase.
- [x] Threat register is trimmed (T-01-04 re-rated, T-01-08 re-rated; old T-01-11 mooted).
- [x] Every must-have artifact has a creation/modification task.
- [x] User Setup Required section in 01-SUMMARY.md will need rewriting at sign-off — that's a Slice G follow-up the executor handles when WS-G.1/G.2 land.
