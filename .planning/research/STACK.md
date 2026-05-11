# Stack Research — FitGH

**Domain:** Responsive PWA fitness tracker (Ghanaian-food calorie tracking + LLM vision + animated dashboard)
**Researched:** 2026-05-11
**Confidence:** HIGH on user-locked choices and main supplements; MEDIUM on edge-Africa CDN claims and per-image vision cost (verify with live pilot).

---

## TL;DR — One-Line Picks

| Concern | Pick | Phase |
|---------|------|-------|
| Frontend shell | Next.js 15.2.x + React 19 + TypeScript 5.5+ + Tailwind v4 | Phase 1 |
| Component library | shadcn/ui (Radix + Tailwind) | Phase 1 |
| Forms | React Hook Form 7.60.x + Zod 3.25.x + `@hookform/resolvers` 5.1.x | Phase 2 (onboarding) |
| Charts | Recharts v3 (via shadcn/ui charts) | Phase 5 (dashboard) |
| Animation runtime | Rive (`@rive-app/react-canvas` ^4.x) | Phase 5 (avatar); Phase 1 scaffold a placeholder |
| Backend framework | Flask 3.1.3 + Gunicorn 25.1.x + Python 3.12 | Phase 3 |
| MongoDB ODM (Python) | PyMongo 4.13+ (no ODM); thin dataclass + Pydantic v2 schemas | Phase 3 |
| MongoDB driver (Next.js) | **None** — Flask owns all DB access | n/a (architectural call, see below) |
| Vision model | **Claude Sonnet 4.6** (`claude-sonnet-4-6`) via `anthropic` Python SDK | Phase 4 |
| Auth | Clerk (free tier 50k MAU) — Flask verifies JWT via `clerk-backend-api` | Phase 2 |
| Image upload | Client-side compression with `browser-image-compression`, then POST as multipart to Flask. **No cloud blob store in v1.** Persist to MongoDB GridFS only if a user opts into history. | Phase 4 |
| Backend host | **Fly.io** (free trial → ~$3–5/mo always-on machine) — beats Render free dyno cold-starts for the snap-meal loop | Phase 3 |
| Frontend host | Vercel (Hobby) | Phase 1 |
| CDN | Vercel default; **Cloudflare in front is optional**, validate in a Ghana-traffic spike before adding | Phase 7 (data-light pass) |
| Observability | Sentry free tier on both Next.js and Flask; Vercel Analytics built-in | Phase 6 |

---

## Frontend

### Core

| Package | Version | Why | Confidence |
|---------|---------|-----|------------|
| `next` | **15.2.4** (latest stable; do not jump to 16 yet — only released Oct 2025, ecosystem still catching up; matches user lock "Next.js 14+") | App Router + async request APIs + Turbopack stable. Use 15.2.x rather than 14 to get React 19 + the modern caching defaults; this is "Next.js 14+" with the leading edge of stable. ([Next.js Current Version: 15.2.4 is the latest stable as of March 2026](https://www.abhs.in/blog/nextjs-current-version-march-2026-stable-release-whats-new)) | HIGH |
| `react` / `react-dom` | **19.x** | Required by Next 15; shadcn/ui works against it. | HIGH |
| `typescript` | **5.5.x or 5.6.x** | Required for proper Zod inference + RHF types; do not pin below 5.4. | HIGH |
| `tailwindcss` | **v4 (4.0.x)** | 70% smaller production CSS than v3, 5× faster builds, CSS-first config via `@theme`. Data-light constraint → v4 is non-negotiable. ([Tailwind v4 launch](https://tailwindcss.com/blog/tailwindcss-v4)) | HIGH |
| `@tailwindcss/postcss` | **4.0.x** | Required PostCSS plugin for Next.js with Tailwind v4 (the "zero-config" Vite story doesn't fully apply to Next.js). | HIGH |

**Considered & rejected:**
- *Next.js 16* — bleeding edge as of May 2026; some ecosystem packages (Sentry, Clerk middleware variants) lag 1–2 minor versions behind. Re-evaluate after milestone 1.
- *Vite + React Router instead of Next.js* — locked out by user constraint; would also lose Vercel's automatic image optimization + edge functions.
- *Tailwind v3* — 2–3× larger CSS bundles than v4. Direct conflict with data-light constraint.

### Component Library

| Package | Version | Why |
|---------|---------|-----|
| `shadcn/ui` (CLI scaffold, not an npm package) | **v4 CLI (March 2026 release)** | Copy-paste Radix-based components into the repo; zero runtime weight beyond what you import; first-class Tailwind v4 + React 19 support. The shadcn/ui charts module wraps Recharts and gives a cohesive look. ([shadcn/ui Next.js install](https://ui.shadcn.com/docs/installation/next), [shadcn CLI v4 changelog](https://ui.shadcn.com/docs/changelog/2026-03-cli-v4)) |
| Underlying primitives | `@radix-ui/react-*` (whatever shadcn pulls in) | Accessibility (keyboard nav, focus management) and minimal CSS. |
| `lucide-react` | **^0.460+** | Tree-shakable icons used by shadcn; cheap on bundle. |
| `class-variance-authority` + `clsx` + `tailwind-merge` | latest | shadcn's class merging stack. |

**Considered & rejected:**
- *HeadlessUI + hand-rolled* — more work; loses shadcn/ui charts integration.
- *MUI / Chakra* — heavy runtime CSS-in-JS; conflicts with data-light goal.
- *DaisyUI* — extra theme weight; less customisable than shadcn for an avatar-led visual identity.

**Install (Phase 1):**
```bash
npx create-next-app@latest fitgh --typescript --tailwind --app --eslint --use-pnpm
cd fitgh
npx shadcn@latest init
npx shadcn@latest add button card form input label dialog sheet tabs toast chart
```

**Confidence:** HIGH for the whole frontend core.

### Forms & Validation

| Package | Version | Why |
|---------|---------|-----|
| `react-hook-form` | **^7.60.0** | Uncontrolled-input perf; minimal re-renders matter on lower-end Android. |
| `zod` | **^3.25.x** | Type-safe schemas; shared shape with Flask via JSON schema if we ever want to. |
| `@hookform/resolvers` | **^5.1.x** | RHF ↔ Zod glue. |

Use on: onboarding (Phase 2), profile edit, manual meal entry / correction (Phase 4), weight log (Phase 5). ([React Hook Form + Zod 2026 guide](https://dev.to/marufrahmanlive/react-hook-form-with-zod-complete-guide-for-2026-1em1))

**Considered & rejected:** Formik (less performant, larger), Valibot (lighter than Zod but smaller ecosystem in 2026), TanStack Form (newer, less proven for our scope).

**Confidence:** HIGH.

### Animation Runtime → **Rive**

| Package | Version | Why |
|---------|---------|-----|
| `@rive-app/react-canvas` | **^4.x** (canvas runtime; smaller than `@rive-app/react-webgl` and adequate for an avatar) | The avatar must reflect user state (weight delta, kcal balance, streak). Rive state machines accept boolean/number/trigger inputs at runtime via `useStateMachineInput` — Lottie has no equivalent and would force imperative frame seeking. Rive `.riv` files are 50–80% smaller than equivalent Lottie JSON, which matters for Ghana mobile data. ([Rive vs Lottie 2026](https://rive.app/blog/rive-as-a-lottie-alternative), [Rive React guide](https://medium.com/@hoainho.work/rivemastering-rive-animation-a-complete-guide-for-react-developers-b9d1f334873f)) |
| (alt for one-off UI bling) `lottie-react` | optional, **^2.4.x** | Only if a designer ships a Lottie file we want as-is (e.g. a confetti). Not needed in v1. |

**Considered & rejected:**
- *Lottie alone* — no state machine. We'd end up writing imperative goto-frame logic to drive the avatar from profile state. Lossy in DX and bundle.
- *Framer Motion for the avatar* — fine for layout transitions, wrong abstraction for a multi-state character.
- *Pure CSS animations* — would not deliver the "fluid avatar" feel the PROJECT.md calls out as a differentiator.

**Phase note:** Scaffold the `<Avatar />` component in Phase 1 with a placeholder SVG. Drop the real `.riv` in Phase 5 when the dashboard lands. The designer pipeline (Rive editor → export `.riv`) needs to start in Phase 1 to not block Phase 5.

**Confidence:** HIGH (technical), MEDIUM (designer availability — if there's no designer, allocate budget for a contract Rive artist or fall back to Lottie + a simpler avatar concept).

### Charts → **Recharts v3** (via shadcn/ui charts)

| Package | Version | Why |
|---------|---------|-----|
| `recharts` | **^3.x** | shadcn/ui's chart module wraps Recharts; it's the de-facto Next.js choice in 2026 with 2.4M weekly downloads. Uses WAAPI for smoother animation on low-end devices than Chart.js. Sufficient for weight-over-time, kcal balance bar, streak heatmap. ([Recharts v3 vs Tremor 2026 guide](https://www.pkgpulse.com/guides/recharts-v3-vs-tremor-vs-nivo-react-charting-2026)) |

**Considered & rejected:**
- *Tremor* — bundles Recharts + ~200kB of design layer; redundant when we already own shadcn theming.
- *Visx* — overpowered for v1's standard charts; 2–3× build time per chart.
- *Chart.js* — Canvas-based, harder to style in Tailwind, weaker animations on low-end devices.
- *Nivo* — heavier bundle than Recharts.

**Phase note:** Phase 5 (dashboard). Each chart should be a Server Component shell with the Recharts client-only sub-component dynamically imported (`next/dynamic` with `ssr: false`) to keep first-paint light.

**Confidence:** HIGH.

### Image Compression (Client-Side)

| Package | Version | Why |
|---------|---------|-----|
| `browser-image-compression` | **^2.0.x** | Compresses + resizes meal photos in the browser before upload. On a 4 MB iPhone photo, can hit 200–400 KB with imperceptible quality loss for vision purposes. Critical for the data-light constraint on the meal-snap loop. ([browser-image-compression usage](https://dev.to/ibelick/how-to-compress-images-on-client-side-2id3)) |

**Recommended compression config for vision:**
```ts
const compressed = await imageCompression(file, {
  maxSizeMB: 0.5,
  maxWidthOrHeight: 1568, // matches Claude vision's recommended max edge
  useWebWorker: true,
  fileType: 'image/jpeg',
  initialQuality: 0.85,
});
```

**Considered & rejected:**
- *Compressor.js* — smaller library but no web-worker option; janky on lower-end Android.
- *Next.js built-in image optimization* — that's for `<Image>` display, not for shrinking user uploads before they hit the API.

**Phase note:** Phase 4 (meal capture).

**Confidence:** HIGH.

---

## Backend

### Core

| Package | Version | Why |
|---------|---------|-----|
| `flask` | **3.1.3** | User-locked. 3.1.x is current; supports async def routes if needed. ([Flask changelog](https://flask.palletsprojects.com/en/stable/changes/)) |
| Python | **3.12.x** | Flask 3.1 is tested on 3.12; broad ecosystem coverage; `anthropic` SDK requires ≥3.9. |
| `gunicorn` | **^25.1.0** | Standard WSGI server. With Fly.io, use `--workers 2 --threads 4 --timeout 60` for vision endpoints (LLM calls can take 5–15s). |
| `flask-cors` | **^5.0.x** | Frontend on `*.vercel.app` needs CORS for Flask on `*.fly.dev`. |
| `python-dotenv` | **^1.0.x** | Load `.env` in local dev; in production, Fly secrets supply env vars. |
| `pydantic` | **^2.9.x** | Strict schema validation for request/response bodies and Mongo documents. Replaces the "ODM" we'd otherwise want. |

**Considered & rejected:**
- *FastAPI* — user locked Flask. (If unlocked, FastAPI would be the right call for async + auto-OpenAPI; but Flask is fine.)
- *Quart (async Flask fork)* — niche; Flask 3.1 async views cover what we need.

### MongoDB Driver / ODM → **PyMongo only, no ODM**

| Package | Version | Why |
|---------|---------|-----|
| `pymongo` | **^4.13** | Official driver. As of 4.13, Motor's async features merged in as `AsyncMongoClient`; Motor itself is **deprecated as of May 14, 2026** so do NOT pick up Motor. ([Motor deprecation note](https://pymongo.readthedocs.io/en/stable/tools.html)) |
| `pydantic` (already above) | **^2.9.x** | Use Pydantic models as the typed shape of each document; serialize/deserialize at the boundary. This is faster, simpler, and more flexible than MongoEngine for a small schema. |

**Recommended pattern:**
```python
from pydantic import BaseModel
from pymongo import MongoClient

class UserProfile(BaseModel):
    user_id: str  # Clerk user ID
    name: str
    sex: Literal["m", "f"]
    height_cm: int
    weight_kg: float
    goal: Literal["weight_loss", "muscle_gain"]

client = MongoClient(MONGO_URI)
db = client.fitgh
profile = UserProfile(**db.profiles.find_one({"user_id": uid}))
```

**Considered & rejected:**
- *MongoEngine* — adds an ORM-style class layer on top of PyMongo, but you pay for it in flexibility and migration friction. For a small flexible schema (profile + meal log + weight log + corrections), it's overkill.
- *uMongo* — async support is nice but Flask 3.1 sync is fine for our load, and uMongo has a smaller community than PyMongo+Pydantic in 2026.
- *Beanie* — requires FastAPI / async; not Flask-native.

**Confidence:** HIGH.

### MongoDB Driver in Next.js → **NONE (architectural call)**

**Recommendation: Flask owns 100% of MongoDB access. Next.js never imports `mongodb` or `mongoose`.**

**Why:**
1. **Single source of truth for data shape.** Pydantic schemas in Flask define the contract; Next.js consumes JSON via REST.
2. **Atlas IP allowlist surface is one host (Fly.io) instead of two** — Vercel's serverless function IPs are non-static on the free tier, which makes safely allowlisting them impossible without paying for Vercel's $100/mo Static IPs feature. Routing all DB traffic through Flask sidesteps this. ([MongoDB Atlas IP allowlist discussion](https://www.quotaguard.com/blog/serverless-static-ip-mongodb-atlas-whitelist))
3. **Connection pool sanity.** Vercel serverless reuses lambdas inconsistently; Mongo connection storms are a real failure mode. One always-on Fly machine with a stable pool is healthier.
4. **No duplicate validation logic** in JS and Python.

**The cost:** Next.js Server Components / Route Handlers must call Flask via HTTP for any data. Use `fetch` with `cache: 'no-store'` for user data, `revalidate: 60` for static-ish content like the exercise library.

**Confidence:** HIGH. If you really need Next.js to read from Mongo directly later (e.g. for a marketing landing page reading a public collection), add the official `mongodb` driver 6.x then — not now.

### Vision LLM → **Claude Sonnet 4.6**, not GPT-4V

| Package | Version | Why |
|---------|---------|-----|
| `anthropic` (Python SDK) | **latest (released May 6, 2026)** | Official SDK; supports Files API for upload-once-reference-many. Use `claude-sonnet-4-6` for the meal-snap loop. ([Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)) |

**Why Sonnet 4.6 over Opus 4.7 over GPT-4o:**

| Model | Per-image input cost (1024×1024) | Latency p50 | Strengths for meal kcal estimation |
|-------|----------------------------------|-------------|-------------------------------------|
| Claude Sonnet 4.6 | ~$0.0040 | ~2–4s | Best document/visual understanding scores in 2026 benchmarks; follows the Ghana-food kcal table provided in context very well; good at constrained JSON output | 
| Claude Opus 4.7 | ~$0.020 (5× Sonnet) | ~6–10s | Marginally better accuracy on edge dishes; cost not justified for v1 |
| GPT-4o | ~$0.0019 | ~1–3s | Cheaper per image and slightly faster; weaker at adhering to a long context-injected reference table; more inclined to "creative" portion guesses |

Source: [vision API comparison 2026](https://tokenmix.ai/blog/vision-api-comparison), [Claude Sonnet 4.6 pricing](https://pricepertoken.com/pricing-page/model/anthropic-claude-sonnet-4.6).

**Pick Sonnet 4.6 because:**
1. The wedge is **Ghanaian food accuracy**. The Ghana kcal table is the differentiator and Claude is measurably better at sticking to context-injected tables than GPT-4o is.
2. Cost is acceptable. At ~$0.004 per meal scan, **1,000 daily-active users averaging 3 meals/day = ~$360/month**. Bearable; lower than expected MongoDB or hosting costs.
3. Single-provider simplicity — no need to manage two SDKs.

**Cost ceiling (v1 launch projection):**
- 100 DAU × 3 meals/day × 30 days × $0.004 = **~$36/month** for vision
- 1,000 DAU × 3 meals/day × 30 days × $0.004 = **~$360/month**
- 10,000 DAU × 3 meals/day × 30 days × $0.004 = **~$3,600/month** — at this point negotiate volume pricing or migrate hot paths to a fine-tuned classifier.

**Considered & rejected:**
- *GPT-4o* — slightly cheaper and faster but loses on table adherence (which is the differentiator).
- *Claude Opus 4.7* — 5× the cost for marginal accuracy gain on already-correctable user-confirmed dish IDs.
- *Self-hosted LLaVA / IDEFICS* — DevOps tax kills the solo-build budget.
- *Two-model cascade (Sonnet for hard, GPT-4o for easy)* — interesting at scale; over-engineered for v1.

**Prompt strategy (Phase 4):** System prompt contains the Ghana kcal table (JSON, ~3KB). User message has the compressed image + portion hint. Force JSON output via the `tool_use` API with a strict schema (dish_id, dish_name, est_portion_g, est_kcal, confidence). Cache the system prompt with prompt caching for 90% cost reduction on the system portion. ([Anthropic prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching))

**Confidence:** HIGH on Sonnet 4.6 pick; MEDIUM on cost estimates (vary with actual prompt length and user behavior — re-evaluate at 100 DAU).

### HTTP / API Layer

| Package | Version | Purpose |
|---------|---------|---------|
| `flask-cors` | **^5.0.x** | CORS to `https://fitgh.vercel.app` (or production domain). |
| `httpx` | **^0.27.x** | Async-friendly HTTP client (preferred over `requests`) for outbound calls to wger/ExerciseDB for exercise data ingestion (Phase 3). |
| `marshmallow` | NOT needed — Pydantic covers serialization. |

---

## Database

### MongoDB Atlas (locked)

- **Cluster:** existing `cluster0.pcd3g.mongodb.net` (M0 free).
- **Collections (proposed):** `users`, `profiles`, `weight_logs`, `meal_logs`, `exercises`, `workout_sessions`, `dish_corrections`, `ghana_kcal_table`.
- **Indexes (Phase 3):** `users.clerk_id` (unique), `meal_logs.user_id_+date` (compound), `weight_logs.user_id_+date`, `exercises.equipment_+target_muscle_+goal`.
- **GridFS:** only if user opts into image history. Default to **no server-side image retention** per the privacy constraint in PROJECT.md.

### Atlas IP Access — Gotcha

Flask on Fly.io has rotating IPs unless you pay for static egress. Two options:

1. **Static egress IP on Fly.io** — supported as of 2026; a flat add-on cost (~$2–3/mo). Pair with a single IP entry in Atlas allowlist. **Recommended.**
2. **`0.0.0.0/0` in Atlas IP allowlist + strong SCRAM auth + TLS only** — works but is the "0.0.0.0/0 trap" Mongo warns about. ([Mongo 0.0.0.0/0 trap](https://www.quotaguard.com/blog/serverless-static-ip-mongodb-atlas-whitelist)) Acceptable only with a strong DB password, no admin user reuse, and network reads logged.

**Pick option 1 once Fly machine is provisioned. Use option 2 only in dev.**

**Confidence:** HIGH.

---

## Authentication → **Clerk**

| Package | Version | Why |
|---------|---------|-----|
| `@clerk/nextjs` | **latest (5.x)** | First-class App Router middleware, pre-built `<SignIn />` / `<SignUp />` components, Google + Apple + email OTP out of the box. 50,000 MAU free as of 2026 — well above any plausible v1 ceiling. ([Clerk free tier 50k MAU](https://saasprices.net/blog/clerk-free-plan-changes)) |
| `clerk-backend-api` (Python SDK) | **latest** | Verifies session JWTs on Flask side via `authenticate_request()` helper. Networkless verification with the JWT public key — no per-request API call. ([Clerk Python SDK](https://github.com/clerk/clerk-sdk-python)) |

**Why Clerk over the alternatives:**
- **Auth.js v5 / NextAuth** — Mongo adapter exists, but no built-in 2FA, no passkeys, no organisations, you implement everything. Auth.js maintainers themselves now point new projects to Better Auth. ([Auth library comparison 2026](https://blog.logrocket.com/best-auth-library-nextjs-2026/))
- **Better Auth** — closer to NextAuth in spirit; still requires you to wire your own UI and Flask verification flow. More DIY than we need for v1.
- **Supabase Auth** — couples nicely with Postgres, not with our MongoDB stack. Wrong gravity well.
- **Roll-your-own JWT** — guaranteed bug-farm for a solo build. Skip.

**Flow:**
1. User signs up via `<SignUp />` on Next.js.
2. Clerk issues a session JWT, stored in the `__session` cookie.
3. Next.js Route Handler / Server Component forwards JWT to Flask in `Authorization: Bearer ...`.
4. Flask middleware calls `clerk.authenticate_request(request, AuthenticateRequestOptions(authorized_parties=["https://fitgh.vercel.app"]))` — networkless verification.
5. Flask uses `auth_state.payload.sub` as the Clerk user ID, joins to `users` collection.

**Phase note:** Phase 2 (onboarding) — auth is the gate to the rest of the app.

**Free tier viability:** ✅ At 50k MAU free, you'd need a real success story before paying anything.

**Considered & rejected (detail above).**

**Confidence:** HIGH.

---

## Image Handling → **Compress client-side, POST to Flask, no cloud blob in v1**

**The pipeline:**

```
User snaps photo → browser-image-compression (target 400KB max, 1568px max edge, JPEG q=0.85)
  → POST multipart to Flask /api/meals/scan
  → Flask: temp memory buffer → base64 → Anthropic API
  → Flask: discard image, persist only the (dish_id, kcal, confidence, user_id, timestamp) to MongoDB
  → Return JSON to Next.js, dashboard updates
```

**Why no cloud blob store:**
1. **Privacy** — PROJECT.md says images "are not retained server-side beyond what's needed for the kcal estimate." No blob = nothing to retain.
2. **Cost** — saves Cloudinary/UploadThing/R2 spend at zero functional cost (no history-of-meal-photos feature in v1).
3. **Data-light** — no extra round-trip through a third-party domain.

**If/when history-of-meals lands (Phase 8+):**
- Pick **Cloudflare R2** ([R2 free tier 2026](https://nubbo.app/blog/cloudflare-r2-free-tier/)): 10 GB free storage, **zero egress fees**, $0.015/GB beyond. Egress-free is decisive vs Cloudinary (egress is what kills Cloudinary bills at scale).
- Or **Vercel Blob** if scope stays small ([Vercel Blob pricing](https://vercel.com/docs/vercel-blob/usage-and-pricing)) — 1 GB free on Hobby; integrates trivially but charges egress.
- Avoid **Cloudinary's free 25-credit plan** for retained meal images — at any meaningful scale the credits evaporate; egress costs balloon.
- Avoid **UploadThing free tier** for this use case — rate limits at ~10 files trip the meal-snap loop badly.

**Phase note:** Phase 4 (meal capture). Cloud blob store decision is **deferred to a separate spike in Phase 8 if/when history is built.**

**Confidence:** HIGH on v1 pipeline. MEDIUM on R2 being the right v2 pick (re-verify pricing when needed).

---

## Deployment

### Frontend → **Vercel (Hobby plan)**

User-locked. Confirmed correct:
- Free, generous on bandwidth for typical fitness-app traffic shapes.
- Automatic image optimization (use `next/image` for static assets like exercise photos and logo).
- Edge functions available if needed (not needed in v1; all data fetching goes via Flask).
- Vercel Analytics is included free.

**Beware:** Vercel Hobby bandwidth is 100 GB/month. With strict page-weight budgeting (data-light) this is comfortable until ~30–50k DAU.

### Backend → **Fly.io** (recommended over Render and Railway)

**Why Fly.io wins for this workload:**

| Concern | Render Free | Railway Trial | Fly.io |
|---------|-------------|---------------|--------|
| Free / cheap tier in 2026 | ✅ Free web service 512 MB | $5 trial credit, then paid | 2-hour trial → paid (~$3–5/mo min for an always-on small machine) |
| Cold start on free | ❌ **30–60s** after 15-min idle | ✅ Always-on during trial | ✅ Configurable (scale-to-zero with 300ms–2s cold, OR always-on) |
| Multi-region | ❌ | ❌ | ✅ Can deploy to JNB (Johannesburg) — closest to Ghana |
| Docker control | Limited | Limited | Full |
| Static egress IP | Add-on | Limited | **Available** — pair with Atlas allowlist |

Source: [Render vs Fly.io vs Railway 2026 comparison](https://techsy.io/en/blog/railway-vs-render-vs-fly-io), [Platforms with real free tier 2026](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026).

**The dealbreaker for Render free**: A 30–60s cold start the first time a user opens FitGH in the morning is fatal for the "snap a meal, see kcal in seconds" promise. Render's $7/mo Starter tier is the workaround, but for the same ~$5/mo Fly.io gets us closer to Ghana (JNB region), static egress IP, and Docker.

**Fly.io config sketch:**
```toml
# fly.toml
app = "fitgh-api"
primary_region = "jnb"  # Johannesburg — closest to Accra (~80–150ms RTT)

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "off"  # Always-on for snap-meal responsiveness
  min_machines_running = 1

[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"
```

**Considered & rejected (with reasons in the table above).**

**Phase note:** Phase 3 (backend scaffold). Phase 7 (data-light pass) may revisit auto-stop to save money once usage patterns are known.

**Confidence:** HIGH on Fly.io for this workload. MEDIUM on JNB being the right region (verify with Ghana-based test users; could also be `lhr` London if most diaspora are UK).

### CDN / Edge → Vercel's edge by default; **defer Cloudflare in front to Phase 7**

- **Cloudflare has POPs in Accra and Lagos**; Vercel's POP list is smaller and West Africa coverage is less documented. ([Vercel vs Cloudflare edge 2026](https://contracollective.com/blog/vercel-vs-cloudflare-pages-edge-deployment-2026))
- However, putting Cloudflare in front of Vercel adds complexity (DNS, cache rules, SSL handshake costs) and Vercel themselves discourage it in most cases. ([Vercel KB: Cloudflare in front](https://vercel.com/kb/guide/cloudflare-with-vercel))
- **For v1, ship on Vercel direct.** In Phase 7 (data-light pass), measure Ghana p75/p95 latency with `WebPageTest` from Accra/Lagos vantage points. If it's bad, evaluate Cloudflare in front then.

**Confidence:** MEDIUM. This is one of the things most worth flagging for a real Ghana-traffic spike.

---

## Observability

### Frontend (Next.js)

| Tool | Why | Phase |
|------|-----|-------|
| `@sentry/nextjs` (^9.x) | Errors + performance traces; free 5k errors/month tier; auto-instruments Next.js App Router. ([Sentry pricing 2026](https://nurbak.com/en/blog/sentry-pricing/)) | Phase 6 |
| Vercel Analytics (built-in) | Web Vitals — critical for measuring whether data-light targets are met. Free. | Phase 1 |
| Vercel Speed Insights | Free on Hobby. Tracks LCP/INP from real users. | Phase 1 |

### Backend (Flask)

| Tool | Why | Phase |
|------|-----|-------|
| `sentry-sdk[flask]` (^2.x) | Errors + tracing; PyMongo integration auto-traces DB calls. ([Sentry PyMongo integration](https://docs.sentry.io/platforms/python/integrations/pymongo/)) | Phase 6 |
| Fly.io built-in logs | Aggregate logs via `fly logs` and a Grafana dashboard later if needed. Free. | Phase 3 |

**Considered & rejected:**
- *Logflare* — niche; weaker Next.js story than Sentry; not worth the integration tax.
- *Datadog / New Relic* — overkill for a solo-build v1.
- *No observability in v1* — false economy; one unexplained 500 will cost more time than the 15 minutes Sentry takes to wire up.

**Confidence:** HIGH.

---

## Considered & Rejected (Summary)

| Category | Rejected | Why |
|----------|----------|-----|
| Vision LLM | GPT-4o | Worse at sticking to context-injected Ghana kcal table; differentiator-eroding |
| Vision LLM | Claude Opus 4.7 | 5× the cost for marginal accuracy on a user-correctable loop |
| Auth | NextAuth / Auth.js v5 | No 2FA / passkeys / orgs out of the box; more DIY than a solo build wants |
| Auth | Supabase Auth | Couples to Postgres, our DB is Mongo |
| Auth | Roll-your-own JWT | Bug farm for solo |
| Backend host | Render free | 30–60s cold start kills the snap-meal loop |
| Backend host | Railway | $5 credit then paid; no compelling latency win over Fly.io for Ghana |
| ODM | MongoEngine | Class layer that constrains schema flexibility |
| ODM | uMongo | Smaller community vs PyMongo + Pydantic |
| Charts | Tremor | Redundant design layer over Recharts; bundle bloat |
| Charts | Visx | Overpowered for v1 |
| Charts | Chart.js | Weaker animations on low-end devices, harder Tailwind theming |
| Animation | Lottie alone | No state machine → can't drive avatar from user state declaratively |
| Image upload | Cloudinary (v1) | Free credits evaporate; egress charges |
| Image upload | UploadThing (v1) | Free tier rate limits trip the snap-meal loop |
| MongoDB driver in Next.js | `mongodb` or `mongoose` | Atlas IP allowlist surface; duplicate validation logic; serverless connection storms |
| Tailwind | v3 | 2–3× larger CSS than v4; conflicts with data-light |
| Next.js | v16 | Too new (Oct 2025); ecosystem laggards |
| CSS framework | MUI / Chakra | Heavy runtime CSS-in-JS; conflicts with data-light |

---

## Installation Cheat-Sheet (Phase 1)

```bash
# Frontend
npx create-next-app@latest fitgh --typescript --tailwind --app --eslint --use-pnpm
cd fitgh
npx shadcn@latest init
npx shadcn@latest add button card form input label dialog sheet tabs toast chart

pnpm add @clerk/nextjs react-hook-form zod @hookform/resolvers \
  recharts @rive-app/react-canvas browser-image-compression lucide-react

pnpm add -D @sentry/nextjs
```

```bash
# Backend (Flask) — Phase 3
mkdir fitgh-api && cd fitgh-api
python -m venv .venv && source .venv/bin/activate  # PowerShell: .venv\Scripts\Activate.ps1
pip install \
  "flask>=3.1,<4" \
  "gunicorn>=25.1" \
  "flask-cors>=5" \
  "pymongo>=4.13" \
  "pydantic>=2.9" \
  "anthropic" \
  "clerk-backend-api" \
  "python-dotenv" \
  "httpx" \
  "sentry-sdk[flask]"

pip freeze > requirements.txt
```

---

## Version Compatibility Notes

| Constraint | Detail |
|------------|--------|
| Next.js 15 + React 19 | Required together; do NOT mix Next 15 with React 18. |
| Next.js 15 + Tailwind v4 | Requires `@tailwindcss/postcss` plugin in `postcss.config.mjs`. |
| shadcn/ui CLI v4 + React 19 | Works; use `pnpm` (not npm with `--legacy-peer-deps`). |
| `anthropic` Python SDK | Requires Python ≥3.9; we use 3.12. |
| PyMongo 4.13+ + Motor | Motor deprecated **May 14, 2026** — use only PyMongo's new `AsyncMongoClient` if async needed. |
| Clerk + Fly.io | Networkless JWT verification needs the JWT public key as a Fly secret; no need for outbound calls to Clerk API for verification. |

---

## Phase Mapping (for the Roadmapper)

| Phase | Picks introduced |
|-------|-------------------|
| **1 — Scaffold** | Next.js 15 + React 19 + TS + Tailwind v4 + shadcn/ui; Vercel deploy; Sentry frontend; Vercel Analytics; Rive placeholder component |
| **2 — Onboarding** | Clerk; RHF + Zod; TDEE calculator (pure TS, no lib) |
| **3 — Backend scaffold** | Flask 3.1.3 + Gunicorn + PyMongo 4.13 + Pydantic v2; Fly.io deploy (JNB region); MongoDB Atlas static egress IP; Sentry backend; Clerk Python SDK middleware |
| **4 — Meal snap loop** | `browser-image-compression`; multipart POST to Flask `/api/meals/scan`; `anthropic` SDK + Sonnet 4.6; Ghana kcal table loaded as system-prompt cache; correction UI (RHF) |
| **5 — Dashboard** | Rive `.riv` avatar with state machine inputs; Recharts via shadcn/ui charts; lazy-loaded with `next/dynamic` |
| **6 — Workout library** | wger / ExerciseDB ingest via `httpx`; offline cache via PWA service worker (Workbox or Next.js native PWA support) |
| **7 — Data-light pass** | Page-weight budgets; lazy assets; consider Cloudflare in front of Vercel **only if** Ghana p75 latency demands it |
| **8 — (Optional) Meal history** | Cloudflare R2 + opt-in setting; only if usage proves it's wanted |

---

## Open Questions for the Planner

1. **Designer pipeline for Rive avatar.** Rive needs a designer to author the `.riv` with state machine inputs. If there's no designer, budget a contract Rive artist OR fall back to Lottie + a simpler conceptual avatar. **Decide before Phase 5.**
2. **Ghana p75/p95 latency baseline.** Before committing to Vercel-only edge, run a WebPageTest from Accra against a deployed Vercel hello-world. Decision point: Phase 7.
3. **Static egress IP cost on Fly.io.** Verify the 2026 add-on price; if it's >$5/mo, reconsider `0.0.0.0/0` with strong auth as a temporary v1 stance.
4. **Vision cost ceiling alert threshold.** Wire a Sentry-or-equivalent alert when monthly Claude vision spend crosses a chosen threshold (e.g. $100). Decide threshold during budget planning.
5. **PWA support.** PROJECT.md mentions PWA-first; pick `next-pwa` or roll a manual service worker in Phase 6. (Not researched in depth here — separate spike.)
6. **Workout asset hosting.** wger/ExerciseDB GIFs — host them on Cloudflare R2 (free egress) or proxy via Flask? Phase 6 decision.
7. **Ghana kcal table source-of-truth.** Where does it live? In `db.ghana_kcal_table` editable by an admin? In a static JSON file in the Flask repo? Suggest: JSON in Flask repo for v1 (deterministic + easy to edit), migrate to DB once dietitian collaboration justifies an admin UI.

---

## Sources

### High confidence
- [Next.js 15.2.4 latest stable](https://www.abhs.in/blog/nextjs-current-version-march-2026-stable-release-whats-new) — current stable version
- [Tailwind CSS v4 launch](https://tailwindcss.com/blog/tailwindcss-v4) — perf + config changes
- [shadcn/ui Next.js install](https://ui.shadcn.com/docs/installation/next) — official setup
- [shadcn/ui CLI v4 changelog (March 2026)](https://ui.shadcn.com/docs/changelog/2026-03-cli-v4) — latest CLI features
- [Flask 3.1.x docs](https://flask.palletsprojects.com/en/stable/changes/) — current Flask + Python compat
- [PyMongo 4.13 / Motor deprecation](https://pymongo.readthedocs.io/en/stable/tools.html) — official driver story
- [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision) — Sonnet 4.6 + Files API
- [Clerk Python SDK](https://github.com/clerk/clerk-sdk-python) — networkless JWT verification
- [Clerk 50k MAU free tier](https://saasprices.net/blog/clerk-free-plan-changes) — pricing
- [Recharts v3 vs Tremor 2026](https://www.pkgpulse.com/guides/recharts-v3-vs-tremor-vs-nivo-react-charting-2026) — charting landscape
- [Rive vs Lottie (Rive blog)](https://rive.app/blog/rive-as-a-lottie-alternative) — state machine differentiator
- [React Hook Form + Zod 2026](https://dev.to/marufrahmanlive/react-hook-form-with-zod-complete-guide-for-2026-1em1) — versions
- [Vercel Blob pricing](https://vercel.com/docs/vercel-blob/usage-and-pricing) — Hobby tier limits

### Medium confidence (cross-source / blog-tier — verify in a spike)
- [Render vs Fly.io vs Railway 2026](https://techsy.io/en/blog/railway-vs-render-vs-fly-io) — cold start + free tier facts
- [Real free tier platforms 2026 (Render)](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026) — cross-check
- [Claude vs GPT vision cost per image](https://tokenmix.ai/blog/vision-api-comparison) — exact per-image costs (vary with image dims)
- [Cloudflare R2 free tier 2026](https://nubbo.app/blog/cloudflare-r2-free-tier/) — for the deferred image history decision
- [Vercel vs Cloudflare edge for Africa](https://contracollective.com/blog/vercel-vs-cloudflare-pages-edge-deployment-2026) — basis for the Phase 7 spike
- [Sentry pricing 2026](https://nurbak.com/en/blog/sentry-pricing/) — free tier sufficient for v1
- [Auth library comparison 2026 (LogRocket)](https://blog.logrocket.com/best-auth-library-nextjs-2026/) — Clerk position
- [MongoDB Atlas IP allowlist trap](https://www.quotaguard.com/blog/serverless-static-ip-mongodb-atlas-whitelist) — the egress-IP gotcha

### Low confidence (flag for spike validation)
- Specific Ghana POP performance for Vercel — verify with real WebPageTest from Accra/Lagos before committing to "Vercel-only edge"
- Fly.io static egress IP add-on price in 2026 — verify on Fly.io billing page
- UploadThing free-tier rate limit specifics — confirmed anecdotally only; not relevant to v1 since we don't use UploadThing

---

*Stack research for: FitGH — Ghanaian-food fitness webapp*
*Researched: 2026-05-11*
