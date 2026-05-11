# Walking Skeleton — FitGH

**Phase:** 1
**Generated:** 2026-05-11

## Capability Proven End-to-End

> A signed-in user can sign in via Clerk-hosted UI, land on `/dashboard`, and see their email — fetched from MongoDB Atlas through Flask (Fly.io JNB) over an authenticated `GET /api/me` round-trip that the Next.js BFF forwards as `Authorization: Bearer <Clerk JWT>` to Flask, which verifies the JWT networkless.

This is the smallest user-visible slice that exercises **every** trust boundary FitGH will lean on for every later phase. No feature work, no Ghana food table, no vision, no charts.

## Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend framework | Next.js 15.2.4 (App Router) + React 19 + TypeScript 5.5+ | App Router + async request APIs; React 19 required by Next 15; TS for safety on the Clerk + BFF boundary. |
| CSS | Tailwind v4 + `@tailwindcss/postcss` | ~70% smaller production CSS than v3 — data-light is a hard constraint, not a finishing touch. |
| Component library | shadcn/ui (Radix-based, copy-paste) — `button`, `card`, `form`, `input`, `label`, `dialog`, `sheet`, `tabs`, `toast`, `chart` scaffolded in Phase 1 | Zero runtime weight beyond what we import; first-class Tailwind v4 + React 19 support. |
| Animation runtime (placeholder) | `@rive-app/react-canvas` ^4.x (no `.riv` file yet) | Scaffold the `<Avatar />` component with a static SVG placeholder; real Rive file lands Phase 5. |
| Auth | **Clerk** (`@clerk/nextjs` on FE, `clerk-backend-api` on BE) | 50k MAU free tier; pre-built UI; networkless JWT verify on Flask via `clerk.authenticate_request()` against the cached JWKS public key. |
| Backend framework | Flask 3.1.3 + Gunicorn 25.1.x + Python 3.12 + Pydantic v2 | Locked stack. Pin Python at 3.12; Gunicorn with `--workers 2 --threads 4 --timeout 60`. |
| MongoDB driver | PyMongo 4.13+ (no ODM) + Pydantic v2 schemas | Motor deprecated May 2026; PyMongo's `MongoClient` is thread-safe; one **module-level singleton** with `maxPoolSize=10`. |
| Database | MongoDB Atlas M0 (existing `cluster0.pcd3g.mongodb.net`) — Flask only | Vercel serverless never imports `mongodb`. All DB access through Flask. **Atlas DB password rotated** (it was exposed in chat) before any deploy; new DB user is **least-privilege** (no admin). |
| Frontend host | Vercel Hobby, deploy from `/frontend` | Free tier; Vercel Analytics + Speed Insights built-in. |
| Backend host | **Fly.io**, `primary_region = "jnb"`, always-on `shared-cpu-1x` 512 MB + **static egress IP** pinned in Atlas allowlist | Closer to Accra (~80–150 ms vs Render us-east ~190 ms); no cold start; ~$5–8/mo. Static egress IP add-on price verified during setup (fall back to `0.0.0.0/0` + strong password in dev only if > $5/mo). |
| Observability | Sentry FE (`@sentry/nextjs` ^9.x) + Sentry BE (`sentry-sdk[flask]` ^2.x) + Vercel Analytics + Vercel Speed Insights | Free tiers; first errors land here, not in production logs. PII scrubber configured to drop email + image bytes + kcal totals from error context. |
| Secrets | `.env*` gitignored from commit 1; `gitleaks` pre-commit hook installed before any commit | The Mongo password rotation is binary — once exposed, rotate. |
| CI bundle gate | `size-limit` configured to fail at First Load JS > **180 KB gzipped** on the dashboard route | The data-light constraint is enforced from Phase 1, not bolted on at the end. |
| Repo layout | Single monorepo with `/frontend`, `/backend`, `/shared` + pnpm workspace root | Shared `User`/`Meal`/`Food` contracts in `shared/schemas/`; independent Vercel + Fly deploys. |

## Stack Touched in Phase 1

- [x] **Project scaffold** — `pnpm create next-app fitgh --typescript --tailwind --app --eslint --use-pnpm`; `shadcn@latest init`; `/backend` Python 3.12 venv with `flask`, `gunicorn`, `flask-cors`, `pymongo`, `pydantic`, `clerk-backend-api`, `python-dotenv`, `sentry-sdk[flask]`; `/shared/schemas/` with stub JSON Schema for `User`.
- [x] **Routing** — Next.js `/sign-in`, `/sign-up` (Clerk-hosted), `/dashboard` (App Router server component); Next.js Route Handler `/api/me` (BFF); Flask `/health`, `/me`.
- [x] **Database** — One seeded `users` document (`{clerk_id, email, profile.name}`); a real **read** (Flask `/me` → `db.users.find_one({"clerk_id": auth.sub})`) and a real **write** (Clerk webhook on `user.created` inserts the `users` doc).
- [x] **UI** — Clerk's `<SignIn/>` / `<SignUp/>` components on `/sign-in` and `/sign-up`; `/dashboard` server component calls `/api/me` and renders `{user.email}` + a placeholder `<Avatar />`.
- [x] **Deployment** — Vercel `/frontend` deploy live with `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` + `CLERK_SECRET_KEY` + `FLASK_URL` env vars; Fly.io `/backend` deploy live in `jnb` with `MONGODB_URI`, `CLERK_SECRET_KEY` (for JWKS), `CLERK_AUTHORIZED_PARTIES`, `SENTRY_DSN_BACKEND` secrets; **static egress IP** pinned in Atlas allowlist; `/health` returns `{ok: true, mongo: "connected"}` from production.

## Out of Scope (Deferred to Later Slices)

These are deliberate non-shipments in Phase 1. Listing them here so future phases do not re-litigate Phase 1's minimalism.

- Onboarding form, Mifflin-St Jeor TDEE math, weights collection — Phase 2.
- Ghana food table seed, `foods` collection, `/foods/search`, manual meal logging UI, multi-component `meals` schema, daily-total endpoint, "remaining kcal" pill, `mongodump` cron — Phase 3.
- LLM vision integration (`anthropic` SDK, Sonnet 4.6, prompt caching), `browser-image-compression`, `/vision/estimate`, component chips, inline correction, per-user 8/day cap, global $/day breaker, `user_corrections` collection — Phase 4.
- Rive `.riv` file, kcal ring animation, Recharts weight + weekly-kcal charts, goal-aware home, soft-streak — Phase 5.
- `exercises` seed, `/exercises/search` filters, WebP poster → tap-load WebM, `next-pwa`, IndexedDB offline cache, `LICENSES.md` — Phase 6.
- Lagos WebPageTest, real privacy policy, data-export endpoint, account-delete cascade refinement, health-claim copy audit, Anthropic spend cap, golden-set re-run — Phase 7.
- All v2 features (image history on R2, wearables, expanded catalogue, push notifications, friends, payments, localisation).

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions (Next.js 15 + Flask 3.1.3 + MongoDB Atlas + Clerk + Fly.io JNB).

- **Phase 2:** A new user can finish onboarding in ≤3 screens and see their daily kcal target + (if muscle-gain) protein target on the dashboard; can edit profile and log a weight; can delete their account.
- **Phase 3:** A user can log a meal as one or more components from the 25-dish Ghana catalogue and see today's running total + remaining-kcal pill.
- **Phase 4:** A user can snap a photo, see each visible component as a chip with a kcal range, correct inline, and confirm — while per-user and global cost ceilings hold.
- **Phase 5:** The dashboard avatar, kcal ring, weight chart, weekly chart, and streak counter animate — goal-aware copy and reduced-motion / slow-connection auto-disable both work.
- **Phase 6:** A user can browse + filter 80–120 exercises, install the PWA, and use the workout library fully offline.
- **Phase 7:** Real Ghana p75 latency validated from Lagos WebPageTest, privacy policy + data-export + delete-account all live in production, health-claim copy audited, production deploy launched.

## Phase 1 Acceptance Checklist (mirrors ROADMAP.md success criteria)

1. [ ] Sign in via Clerk-hosted UI → land on `/dashboard` showing email from Atlas through Flask (end-to-end).
2. [ ] Sign out from any page; refresh after sign-out lands on sign-in (httpOnly cookie cleared).
3. [ ] `/health` returns `{ok: true, mongo: "connected"}` from Fly.io JNB; static egress IP pinned in Atlas allowlist (no `0.0.0.0/0` in production).
4. [ ] CI PR that pushes First Load JS > 180 KB gzipped fails the build; gitleaks pre-commit blocks a commit containing a Mongo URI.
5. [ ] Sentry (FE + BE) and Vercel Analytics + Speed Insights have received at least one real event from the deployed app; Flask `clerk.authenticate_request()` verifies the JWT networkless on every protected request (no per-request call to Clerk API).
