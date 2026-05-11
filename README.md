# FitGH

A responsive, interactive fitness webapp built for Ghanaians at home and in the diaspora. Build a profile, snap a meal photo, see kcal in seconds, follow a workout library — all calibrated against a curated Ghanaian-food kcal table.

**Core value:** Snap a meal, see kcal in seconds, know whether you're hitting your daily target — with food the user actually eats.

## Phase 1 — Walking Skeleton

The current phase is a **vertical-MVP slice** proving the full trust boundary works end-to-end: Clerk auth → Next.js → Flask (Fly.io JNB) → MongoDB Atlas — with CI gates (size-limit at 180 KB First Load JS, gitleaks pre-commit) and observability (Sentry FE + BE, Vercel Analytics + Speed Insights) in place from commit 1.

See [`.planning/phases/01-walking-skeleton/SKELETON.md`](./.planning/phases/01-walking-skeleton/SKELETON.md) for the skeleton contract and [`.planning/phases/01-walking-skeleton/01-PLAN.md`](./.planning/phases/01-walking-skeleton/01-PLAN.md) for the 30-task execution plan.

## Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 15.2.4 + React 19 + TypeScript 5.5+ + Tailwind v4 |
| Components | shadcn/ui (Radix-based) |
| Auth | Clerk (`@clerk/nextjs` ^6.x; networkless JWT verify on Flask via `clerk-backend-api`) |
| Backend | Flask 3.1.3 + Gunicorn + Python 3.12 + Pydantic v2 |
| Database | MongoDB Atlas (PyMongo 4.13+, singleton with `maxPoolSize=10`) |
| Frontend host | Vercel Hobby (`/frontend`) |
| Backend host | Fly.io `jnb` (always-on `shared-cpu-1x` 512 MB + static egress IPv4 pinned in Atlas allowlist) |
| Observability | Sentry FE + BE (PII-scrubbed); Vercel Analytics + Speed Insights |

## Repo Layout

```
.
├── frontend/                # Next.js app (Vercel deploy target)
├── backend/                 # Flask API (Fly.io deploy target)
├── shared/                  # Shared JSON Schema contracts (User, Meal, Food)
├── .planning/               # Phase plans, requirements, research, state
├── .github/workflows/       # CI: frontend, backend, gitleaks
├── .env.example             # Required env vars (no values)
└── README.md
```

## Quick Start (Local Dev)

> Phase 1 is in active scaffolding. Some commands below require slices to have completed; see plan.

### Prerequisites

- Node.js 20 (use `.nvmrc`)
- pnpm 9+
- Python 3.12
- Docker (for backend smoke build + Fly.io deploy)
- Atlas account + Clerk account + Sentry account (see `.env.example` for required keys)

### Setup

```bash
# 1. Clone
git clone <repo-url>
cd Fitness

# 2. Env vars
cp .env.example .env.local           # populate with real values from your password manager
cp .env.example backend/.env         # backend uses backend/.env (gitignored)

# 3. Install hooks (Phase 1 Slice 0)
pip install pre-commit
pre-commit install

# 4. Frontend
cd frontend
pnpm install
pnpm dev                              # http://localhost:3000

# 5. Backend (separate terminal)
cd backend
python -m venv .venv
.venv\Scripts\activate.ps1            # PowerShell on Windows
pip install -r requirements.txt -r requirements-dev.txt
flask --app app:create_app run -p 8000
```

### Verifying the Walking Skeleton

After Phase 1 completes:
- Visit `https://<your-vercel-domain>/sign-up` → sign up with email or Google.
- Land on `/dashboard` → see your email rendered (from MongoDB Atlas, through Flask).
- Visit `https://<your-fly-domain>/health` → returns `{"ok": true, "mongo": "connected"}`.

## Security

- All secrets live in `.env.local` (frontend) and `backend/.env` (backend); both are gitignored.
- `gitleaks` runs as a pre-commit hook AND in CI to block accidental secret commits.
- MongoDB Atlas user `fitgh-app` is `readWrite@fitgh` only (no admin privileges).
- Flask CORS uses an explicit origin allowlist with `supports_credentials=False`.
- Static egress IP pinned in Atlas Network Access; `0.0.0.0/0` removed in production.

## License

Private project. All workout/exercise assets in `shared/exercises/` (Phase 6) are CC-BY-SA (wger) or Unlicense (Free Exercise DB) per `LICENSES.md`.
