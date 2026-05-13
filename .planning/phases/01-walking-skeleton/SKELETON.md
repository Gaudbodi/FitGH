# Walking Skeleton — FitGH

**Phase:** 1
**Generated:** 2026-05-11
**Revised:** 2026-05-13 (Render-only rewrite supersedes the original Fly.io + Vercel + Clerk-twin shape)

## Capability Proven End-to-End

> A signed-up user signs in via Clerk's Production instance on the Render-hosted Next.js frontend, lands on `/dashboard`, and sees their email — fetched from MongoDB Atlas through Flask on Render's Python web service. The Next.js BFF (`/api/me`) forwards the verified Clerk session JWT as `Authorization: Bearer <token>` to Flask, which verifies the JWT networkless via `clerk-backend-api` and reads the `users` document from Atlas. On a brand-new user's first `/me` call the document is upserted on demand (sync-on-demand replaces the Clerk svix webhook the original plan called for).

This is the smallest user-visible slice that exercises **every** trust boundary FitGH will lean on for every later phase. No feature work, no Ghana food table, no vision, no charts.

## Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend framework | Next.js 15.2.4 (App Router) + React 19 + TypeScript 5.x | App Router + async request APIs; React 19 required by Next 15; TS for safety on the Clerk + BFF boundary. |
| CSS | Tailwind v4 + `@tailwindcss/postcss` | ~70% smaller production CSS than v3 — data-light is a hard constraint, not a finishing touch. |
| Component library | shadcn/ui (Radix-based, copy-paste) — `button`, `card`, `avatar`, `sonner` scaffolded in Phase 1 | Zero runtime weight beyond what we import; first-class Tailwind v4 + React 19 support. |
| Animation runtime (placeholder) | `@rive-app/react-canvas` ^4.x (no `.riv` file yet) | Scaffold the `<Avatar />` component with a static SVG placeholder; real Rive file lands Phase 5. |
| Auth | **Clerk single Production instance** (`@clerk/nextjs` ^6 on FE, `clerk-backend-api` 5.x on BE) — both `http://localhost:3000` and the Render `fitgh-web` URL in Authorized Origins | 50k MAU free tier; one application, two authorized origins (drops the Dev+Prod twin the original plan called for). Pre-built UI; networkless JWT verify on Flask via `clerk.authenticate_request()` against the cached JWKS public key. |
| Backend framework | Flask 3.1.3 + Gunicorn ^25.1 + Python 3.12 + Pydantic v2 | Locked stack. Pin Python at 3.12 via Render's `PYTHON_VERSION` env var; Gunicorn with `--workers 2 --threads 4 --timeout 60`. |
| MongoDB driver | PyMongo 4.13+ (no ODM) + Pydantic v2 schemas | Motor deprecated May 2026; PyMongo's `MongoClient` is thread-safe; one **module-level singleton** with `maxPoolSize=10` (SEC-04). |
| Database | MongoDB Atlas M0 (existing `cluster0.pcd3g.mongodb.net`) — Flask only | Next.js never imports `mongodb`. All DB access through Flask. **Atlas DB password rotated** (the original was exposed in chat) before any deploy; **`fitgh-app`** is a least-privilege `readWrite@fitgh` user (no admin, no cluster drop). **Network Access: `0.0.0.0/0`** — Render egress IPs aren't pinnable on Free/Starter; defense is the 32-char password + scoped role + TLS-only. |
| User-creation pattern | **Sync-on-demand inside `/me`** | Replaces the deprecated `user.created` Clerk webhook. The user document is upserted lazily the first time the signed-in user hits `/me`. No webhook endpoint to host, no svix signature path. |
| Frontend host | **Render Free** (`fitgh-web` Node web service from `/frontend`) | Single platform deploy. Free tier acceptable for Phase 1; Phase 7 may upgrade if Ghana p75 latency demands it. |
| Backend host | **Render Starter** (`fitgh-api` Python web service from `/backend`) — $7/mo for always-on, no cold starts | Phase 4 (LLM vision) cannot tolerate Render Free's 30–60 s cold start on the meal-snap loop; lock Starter in now so it isn't a Phase 4 surprise. |
| Deploy mechanism | `render.yaml` Blueprint at repo root + `git push main` auto-deploy on both services in parallel | One commit, both services rebuilt. Render's `healthCheckPath: /health` rolls failed backend deploys back automatically. |
| Observability | **Deferred (OBS-01)** — Sentry scrubber code present in `app/extensions.py` and unit-tested (`test_sentry_scrubber.py` 7 cases + `test_sentry_init_conditional.py` 2 cases), but `sentry_sdk.init` is a no-op until `SENTRY_DSN_BACKEND` is set | Re-enabling Sentry is one env-var away. The PII scrubber contract holds from commit 1 so OBS-01 doesn't have to be retrofitted. |
| Secrets | `.env*` gitignored from commit 1; local `gitleaks` pre-commit hook (custom MongoDB / Clerk / Sentry rules); **no CI gitleaks job** (deferred SEC-01) | Local pre-commit blocks the dangerous commits; user owns the local repo. Render env vars (`sync: false` per `render.yaml`) hold real secrets in production. |
| CI gates | One workflow (`.github/workflows/ci.yml`) — backend `ruff` + `pytest` and frontend `pnpm lint` + `pnpm tsc --noEmit` + `pnpm build` in parallel | No size-limit gate, no docker-build smoke. Render itself re-runs the build inside its container; CI is the cheap pre-flight gate. |
| Repo layout | Single monorepo with `/frontend`, `/backend`, `/shared` | Shared `User`/`Meal`/`Food` contracts in `shared/schemas/`; both services deploy from one repo via `render.yaml`. |

## Stack Touched in Phase 1

- [x] **Project scaffold** — `pnpm create next-app fitgh --typescript --tailwind --app --eslint --use-pnpm`; `shadcn@latest init`; `/backend` Python 3.12 venv with `flask`, `gunicorn`, `flask-cors`, `pymongo`, `pydantic`, `clerk-backend-api`, `python-dotenv`, `sentry-sdk[flask]`; `/shared/schemas/` with stub JSON Schema for `User`.
- [x] **Routing** — Next.js `/sign-in`, `/sign-up` (Clerk-hosted), `/` (landing with CTAs), `/dashboard` (server component fetching `/api/me`); Next.js Route Handler `/api/me` (BFF, forwards Clerk JWT to Flask); Flask `/health`, `/me`.
- [x] **Database** — A `users` document with `{clerk_id, email, created_at, updated_at}` lands on the first `/me` call (sync-on-demand `$setOnInsert` upsert); a real **read** (Flask `/me` → `users.find_one({clerk_id})`) and a real **write** (the upsert).
- [x] **UI** — Clerk's `<SignIn/>` / `<SignUp/>` components on `/sign-in` and `/sign-up`; `/dashboard` server component calls `/api/me` and renders `{user.email}` + a placeholder `<Avatar />` + a `<SignOutButton>` (Clerk client component) that redirects to `/sign-in` on click.
- [x] **Deployment** — Render Blueprint provisions both services from one repo on `git push main`. Backend: `pip install -r requirements.txt`; Gunicorn; Render-assigned URL; secrets (`MONGODB_URI`, `CLERK_SECRET_KEY`, `CLERK_AUTHORIZED_PARTIES`) supplied as `sync: false` env vars. Frontend: `corepack enable && pnpm install --frozen-lockfile && pnpm build && pnpm start`; secrets (`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`) supplied; `NEXT_PUBLIC_API_URL` wired via Render's `fromService` directive so it auto-resolves to the `fitgh-api` URL. `/health` returns `{ok: true, mongo: "connected"}` from production.

## Out of Scope (Deferred to Later Slices)

These are deliberate non-shipments in Phase 1. Listing them here so future phases do not re-litigate Phase 1's minimalism.

- Onboarding form, Mifflin-St Jeor TDEE math, weights collection — Phase 2.
- Ghana food table seed, `foods` collection, `/foods/search`, manual meal logging UI, multi-component `meals` schema, daily-total endpoint, "remaining kcal" pill, `mongodump` cron — Phase 3.
- LLM vision integration (`anthropic` SDK, Sonnet 4.6, prompt caching), `browser-image-compression`, `/vision/estimate`, component chips, inline correction, per-user 8/day cap, global $/day breaker, `user_corrections` collection — Phase 4.
- Rive `.riv` file, kcal ring animation, Recharts weight + weekly-kcal charts, goal-aware home, soft-streak — Phase 5.
- `exercises` seed, `/exercises/search` filters, WebP poster → tap-load WebM, `next-pwa`, IndexedDB offline cache, `LICENSES.md` — Phase 6.
- Lagos WebPageTest, real privacy policy, data-export endpoint, account-delete cascade refinement, health-claim copy audit, Anthropic spend cap, golden-set re-run — Phase 7.
- All v2 features (image history on Cloudflare R2, wearables, expanded catalogue, push notifications, friends, payments, localisation).

## Deferred Within Phase 1 (2026-05-12 rewrite)

These were in the original Phase 1 plan and were dropped in the Render-only rewrite. Each has a re-engagement path documented in `memory/render-only-rewrite.md`.

- **SEC-01** — Custom gitleaks CI rules. Re-engage by re-adding `.github/workflows/gitleaks.yml`. Local pre-commit gate remains in force.
- **SEC-02** — Atlas IP-allowlist tightening. Re-engage by replacing `0.0.0.0/0` with the Render egress IP block once Render exposes pinnable egress on a tier we use.
- **SEC-03** — Flask CORS hardening. Re-engage by populating `CORS_ALLOWED_ORIGINS` (still wired in `__init__.py`); the BFF same-origin posture mooted the cross-origin browser path in v1.
- **OBS-01** — Sentry FE + BE. Re-engage by setting `SENTRY_DSN_BACKEND` (backend; init no-ops without it) and running the Sentry Next.js wizard (frontend; not yet scaffolded). The scrubber contract is enforced from commit 1.
- **OBS-02** — Vercel Analytics. Dropped (no Vercel). If Render adds an analytics product worth integrating, Phase 6 or 7 can pick it up.
- **PERF-01** — size-limit 180 kB CI gate. Re-engage by re-adding `frontend/.size-limit.json` + a CI step. Manual check at phase boundaries (`pnpm build` route table) is the v1 posture.

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions (Next.js 15 + Flask 3.1.3 + MongoDB Atlas + Clerk + Render).

- **Phase 2:** A new user can finish onboarding in ≤3 screens and see their daily kcal target + (if muscle-gain) protein target on the dashboard; can edit profile and log a weight; can delete their account.
- **Phase 3:** A user can log a meal as one or more components from the 25-dish Ghana catalogue and see today's running total + remaining-kcal pill.
- **Phase 4:** A user can snap a photo, see each visible component as a chip with a kcal range, correct inline, and confirm — while per-user and global cost ceilings hold.
- **Phase 5:** The dashboard avatar, kcal ring, weight chart, weekly chart, and streak counter animate — goal-aware copy and reduced-motion / slow-connection auto-disable both work.
- **Phase 6:** A user can browse + filter 80–120 exercises, install the PWA, and use the workout library fully offline.
- **Phase 7:** Real Ghana p75 latency validated from Lagos WebPageTest, privacy policy + data-export + delete-account all live in production, health-claim copy audited, production deploy launched.

## Phase 1 Acceptance Checklist (mirrors ROADMAP.md Phase 1 Success Criteria — verbatim)

1. [ ] A user signs up + signs in via the Clerk Production instance (email/password OR Google) on the Render-hosted Next.js frontend, and lands on `/dashboard` showing their email pulled from MongoDB Atlas through Flask — page renders end-to-end with no shortcuts.
2. [ ] A user can sign out from any page; refreshing after sign-out lands them on the sign-in screen (Clerk session cleared).
3. [ ] The Flask `/health` endpoint returns `{ok: true, mongo: "connected"}` from the Render Starter web service, against MongoDB Atlas M0 with a `0.0.0.0/0` allowlist + 32-char password + scoped `readWrite@fitgh` role.
4. [ ] A `git push main` triggers Render auto-deploys of both web services in parallel; the backend build runs `pytest` and the frontend build runs `pnpm build` — failures halt the deploy and the previous version stays live.
5. [ ] Three SaaS dashboard checkpoints complete Phase 1 setup: (a) Atlas `fitgh-app` user with rotated password, (b) Render account linked to the GitHub repo with `fitgh-web` + `fitgh-api` services configured, (c) Clerk Production instance with the Render URL + `localhost:3000` in authorized origins. No Fly.io, no Vercel, no Sentry FE/BE wizards, no static egress IPv4 add-on, no custom gitleaks CI rules, no size-limit CI gate.
