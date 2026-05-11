# PITFALLS

**Project:** FitGH — Ghanaian-focused fitness webapp (Next.js + Flask + MongoDB Atlas + LLM vision)
**Researched:** 2026-05-11
**Scope:** Pitfalls specific to *this* stack + domain + market. Generic "fitness app" advice is excluded.

**Reading order:** Skim the Priority Matrix at the bottom first; it ranks the top 5 to address in v1. The clusters below give the full detail.

---

## LLM Vision

These pitfalls compound: an inaccurate estimate at scale becomes an inaccurate AND expensive estimate. Cost and accuracy must be designed together, not sequenced.

### V-1. Confident-but-wrong kcal estimates

- **Pitfall:** The LLM returns a single kcal number with no uncertainty band, the user trusts it, and the daily-target loop is silently miscalibrated by 200–500 kcal/day.
- **Why it happens:** Vision models (GPT-4V, Claude vision) are trained for fluent natural-language output, not calibrated estimation. They will happily say "approximately 540 kcal" for any meal because the prompt asked for a number. Research shows average relative error of 0.1%–38.3% on calories; on medium/large meals portion weight is *underestimated 76% of the time* ([An Evaluation of ChatGPT for Nutrient Content Estimation](https://www.mdpi.com/2072-6643/17/4/607)).
- **Warning signs:**
  - Test set of 20 known-weight meals shows >25% mean absolute error and no correlation between meal size and predicted size.
  - Users who weigh meals at home start logging manual overrides constantly.
  - Backend logs show the LLM never returns "I'm not sure" or a confidence band even when the image is ambiguous.
- **Prevention:**
  - **Force a confidence range in the response schema** — require the model to return `{ kcal_low, kcal_high, kcal_point, confidence: low|med|high }`. Show the range, not the point estimate, in the UI. A 380–620 kcal band is more honest than "498 kcal" and trains the user to correct.
  - **Show the assumptions back to the user:** "Estimated as 1 cup jollof + 1 piece chicken thigh. Tap to correct." Surfacing the assumption is what makes correction cheap.
  - **Calibrate against a fixed test set** of 30–50 photographed Ghanaian meals with known weighed kcal *before* shipping. Track mean absolute percentage error (MAPE) as a release-gate metric (target: <25% MAPE on the test set).
- **Phase:** Phase that introduces the kcal estimation loop. Block release on MAPE target.

### V-2. Portion-size estimation is the hardest part — and the spec ignores it

- **Pitfall:** The team focuses on dish *identification* ("is this jollof?") and treats portion as a secondary detail; portion-size error then dominates total kcal error.
- **Why it happens:** Dish ID is what feels like the "AI bit," so it gets the attention. But research shows VLMs hit 87–90% on dish ID *and* underestimate portion 76% of the time on medium/large meals. The bottleneck is portion, not identification.
- **Warning signs:**
  - Spec / prompts talk about "identify the dish" with no equivalent attention to "estimate the portion."
  - No reference object (hand, fork, standard plate, coin) is requested or surfaced in the capture UI.
  - All test photos in dev are top-down with no scale reference, but production users shoot at an angle.
- **Prevention:**
  - **Prompt the LLM to explicitly identify a scale reference** in the image (hand, utensil, plate diameter assumption) and to *return* that reasoning. If no reference is detected, return `confidence: low` and offer a portion picker UI.
  - **Capture UI nudge:** before the user shoots, suggest "include your hand or a spoon in frame for better accuracy." Cheap, effective.
  - **Default to a portion picker after the estimate:** "Small / Medium / Large / Custom grams." Most users will tap one — and that one tap is your training signal.
- **Phase:** Same phase as V-1. These two must ship together or the loop is unusable.

### V-3. Per-image cost balloons at scale

- **Pitfall:** At 3 meals/day × 1000 active users, image-vision cost crosses $30–80/day with no monetisation in place to absorb it; founder panics, throttles, breaks the loop.
- **Why it happens:** Image tokens are expensive. A 1024×1024 image on Claude 3.5 Sonnet ≈ 1200 input tokens; with a 500-token Ghana food table system prompt and 300-token response, that's ~2000 tokens/call ≈ $0.009 input + $0.005 output ≈ **$0.014/image**. At 3 meals × 1000 users = **$42/day**, scaling linearly. On GPT-4o it's lower but still material. Without aggressive caching the unit economics break before PMF.
- **Warning signs:**
  - No prompt caching configured.
  - Same image being re-processed because the frontend retries on errors.
  - System prompt + Ghana food table > 2000 tokens, sent uncached every call.
  - No `max_tokens` ceiling on the response.
- **Prevention:**
  - **Use Anthropic prompt caching** for the system prompt + Ghana food table (cuts repeat input cost ~90%). This is the single biggest lever. ([Anthropic API Pricing](https://www.finout.io/blog/anthropic-api-pricing))
  - **Resize client-side to 1024px max long edge** before upload. A 4K phone photo at 1568×1568 hits ~1750 tokens; at 1024×768 it's ~750 tokens. Image quality at 1024px is still ample for food ID.
  - **Set `max_tokens: 400`** on responses. The LLM will pad if allowed to.
  - **Per-user daily cap** (e.g., 8 image calls/day) with a clear UX: "You've used your AI estimates for today; log manually or upgrade later." Hard cap protects against cost attacks (see S-4).
  - **Track $/active-user/day** as a top dashboard metric from day 1. The number to beat: <$0.05/DAU. If you cross it, fix before scaling marketing.
- **Phase:** Same phase as V-1/V-2. Build the cost ceiling before opening signups beyond the seed cohort.

### V-4. Estimates drift across model versions

- **Pitfall:** You ship on `claude-3-5-sonnet-20241022`, six months later switch to a newer model, and suddenly the same jollof photo returns 720 kcal instead of 540 kcal. User trust collapses overnight.
- **Why it happens:** New model versions change calibration silently. Users notice when their "usual breakfast" jumps 30%.
- **Warning signs:**
  - The model ID is hardcoded in one place and changed without a regression test.
  - No archive of historical (image, prompt, response) tuples to re-run against new models.
  - User complaints spike within 48 hours of a model change.
- **Prevention:**
  - **Pin the model ID in env** (`LLM_VISION_MODEL=claude-3-5-sonnet-20241022`), don't use a floating alias.
  - **Keep a frozen golden set** of 30–50 meals with their previous estimates. Re-run on any model bump and compare MAPE drift; require <15% drift before swapping.
  - **Announce model changes in-app** with a heads-up: "We've updated our AI; some estimates may shift slightly." Transparency preserves trust.
- **Phase:** Operational hygiene; revisit when shipping a model upgrade. Add to runbook in Phase 1.

### V-5. Non-determinism: same photo, different answers

- **Pitfall:** User takes a photo, gets 480 kcal. Retakes the same photo, gets 540 kcal. Posts a screenshot on Twitter; trust dies.
- **Why it happens:** Temperature > 0, plus sampling variance. Vision models are stochastic by default.
- **Warning signs:**
  - You haven't explicitly set `temperature: 0` (or 0.1).
  - QA repeatedly running the same image during testing sees varying outputs.
- **Prevention:**
  - **Set `temperature: 0`** on the vision call. Greedy decoding gives reproducible (or near-reproducible) outputs.
  - **Cache by perceptual hash:** if the same image (within tolerance) is submitted, return the cached result for some window (24h). Useful for "I closed the app and reopened it" cases. Bonus: cuts cost.
- **Phase:** Same phase as V-1.

### V-6. Hallucinated ingredients

- **Pitfall:** LLM claims the waakye contains shito when it doesn't, or invents "boiled egg" that's not in frame; the kcal estimate reflects ingredients the user didn't eat.
- **Why it happens:** Vision models pattern-match to typical preparations. If "waakye" usually has shito and boiled egg in training images, the model will assume them whether visible or not.
- **Warning signs:**
  - User corrections frequently strip components ("no, there was no egg").
  - The LLM's reasoning text mentions ingredients that aren't visible.
- **Prevention:**
  - **Prompt explicitly:** "Only include ingredients you can clearly see in the image. If a typical component is absent or not visible, do NOT include it. List what you see in `visible_components` separately from `assumed_components`."
  - **Show the component breakdown** in the UI with toggles ("Remove egg"). Removing an assumed component should recompute kcal. This makes the assumption visible and easy to fix.
- **Phase:** Same phase as V-1.

### V-7. No user-correction loop → users lose trust permanently

- **Pitfall:** Estimate is wrong, user has no fast way to fix it, user stops logging within 5 days.
- **Why it happens:** Building a correction UI feels like polish; it's actually a load-bearing trust mechanism. Users will accept ~30% error if they can fix it in one tap; they won't accept 10% error if they can't.
- **Warning signs:**
  - Median time-from-estimate-to-logged > 15 seconds.
  - Correction UI is a multi-step modal.
  - Corrections aren't being stored.
- **Prevention:**
  - **Inline correction:** kcal number is editable in place. Dish is editable in place. Portion is a horizontal slider/picker.
  - **Store every correction** as `(image_hash, original_estimate, user_correction, ghana_food_table_match)`. This is the most valuable data the app generates — it's the training signal for future calibration and the basis for any future custom model.
  - **Use corrections to bias future estimates:** if the user has corrected "jollof" portion to 1.5x three times, pass that as context next time.
- **Phase:** Phase that ships the kcal loop. Non-negotiable for v1.

---

## Ghanaian Food Coverage

This is the project's wedge. If this fails, FitGH is just another (slower) MyFitnessPal.

### G-1. Vision model misnames local dishes as generic Western categories

- **Pitfall:** GPT-4V/Claude vision sees banku + okra stew, returns "porridge with vegetable soup." Kontomire becomes "spinach stew." Red red becomes "bean stew." kcal then gets matched against the wrong baseline.
- **Why it happens:** Training data over-represents Western/East Asian cuisine. African food datasets exist (see [African foods dataset](https://www.sciencedirect.com/science/article/pii/S2352340924000659)) but aren't dominant in VLM pretraining.
- **Warning signs:**
  - Test set of 20 Ghana dish photos: <70% return the correct local name in the model's free-form output.
  - Model output uses descriptors ("brown stew with fish") instead of names ("palmnut soup").
- **Prevention:**
  - **Pass the Ghana food table as a constrained vocabulary in the system prompt:** "The dish is one of: jollof, waakye, banku, fufu, kenkey, kelewele, red red, kontomire stew, palmnut soup, groundnut soup, light soup, tilapia, koko, yam (boiled/fried), kokonte, gari foto, … (full list). If none match, return `dish: unknown` and describe what you see."
  - **Force a structured response:** require `dish_name` to be from the enum. The LLM's job is matching, not naming.
  - **Maintain a synonym/variant map:** "jollof" ↔ "jollof rice" ↔ "ceebu jen" (Senegalese variant the diaspora user might call it). Map on the backend.
  - **Quarterly accuracy audit:** 50 photos from real users, hand-labeled, MAPE per dish family. Track the worst 5 dishes — those are next quarter's prompt-engineering targets.
- **Phase:** Phase that ships the kcal loop. The Ghana table + constrained-vocabulary prompt are launch blockers.

### G-2. Western-database kcal values don't match Ghanaian portions

- **Pitfall:** App says "jollof: 220 kcal/cup" from a USDA-aligned source. In Accra the typical jollof serving is 1.5–2 cups + chicken + salad; real meal is 700–900 kcal, app reports 220. User loses weight chasing what they think is a deficit.
- **Why it happens:** Most online kcal databases derive from US/UK food data; Ghana serving sizes are systematically larger and contain different oil/stock loadings.
- **Warning signs:**
  - Your Ghana food table cites MyFitnessPal or USDA as the source for jollof.
  - No "typical Ghana portion" column in the table separate from "per 100g."
  - Diaspora users (smaller portions, restaurant servings) and in-Ghana users (home plates) report opposite-direction errors.
- **Prevention:**
  - **Build the Ghana food table with at least three values per dish:** `kcal_per_100g`, `typical_portion_grams_ghana`, `typical_portion_grams_diaspora`. Use FAO/INFOODS West Africa food composition tables as the primary source ([FAO/INFOODS West Africa table](https://www.fao.org/3/i3496e/i3496e.pdf) is the canonical reference) and validate against published Ghana studies (University of Ghana Department of Nutrition & Food Science has published portion-size data).
  - **Ask the user's location once during onboarding** and bias portion defaults accordingly.
  - **Surface portion grams in the UI** so users see the assumption.
- **Phase:** Phase that builds the Ghana food table (could be Phase 0 / data prep, before the main vision loop ships).

### G-3. Regional and preparation variants collapsed into one entry

- **Pitfall:** Northern jollof (drier, smokier, often with goat) and Southern/Ga jollof (oilier, tomato-heavier) have meaningfully different kcal/g. Kelewele spice level doesn't change kcal much, but kelewele *oil load* (deep-fried vs shallow-fried) does. App treats them as identical.
- **Why it happens:** Building a "minimum viable food list" tempts collapsing variants. The error is silent — no user sees a "wrong variant" warning.
- **Warning signs:**
  - Food table has one row per dish name.
  - User feedback mentions "this isn't how my mum makes it."
- **Prevention:**
  - **For the top 10 dishes only**, model 2–3 variants and let the LLM pick or the user pick. Don't model variants for all 50+ dishes — pareto on the top 10.
  - **For dishes with prep variants (kelewele fried in shallow vs deep oil), let the user toggle** prep style; recompute kcal.
  - **Track which dishes have the highest correction-rate** in production; those are the ones that need variant splits next.
- **Phase:** Initial Ghana food table can ship single-variant for non-top-10. Variant work is a Phase 2+ improvement driven by correction data.

### G-4. Multi-dish plates: single-dish assumption fails

- **Pitfall:** A typical Ghanaian plate has jollof + chicken + salad + sometimes shito on the side. The single-dish assumption returns kcal for "jollof rice" and misses 40–60% of the meal's energy.
- **Why it happens:** Implementations default to "identify the dish" (singular). Multi-component plates are the norm in this cuisine, not the exception.
- **Warning signs:**
  - The response schema has a single `dish_name` field, not a `components: []` list.
  - Users routinely take multiple photos of the same plate to log each item separately.
  - User corrections frequently add components.
- **Prevention:**
  - **Schema the response as a list of components from day 1:** `components: [{name, portion_grams, kcal, confidence}, ...]`. Sum on backend. This is the *single most important* schema decision.
  - **Prompt:** "Identify *each* visible food component separately, including sides (shito, salad, kelewele, plantain) and proteins."
  - **UI shows each component as a chip** the user can edit/remove. Tap to delete a component recomputes total.
- **Phase:** Phase that ships the kcal loop. This is a schema decision — get it wrong at v1 and refactor is painful.

---

## Data-Light

Ghana mobile data costs are roughly 5–10× higher per GB than US/EU. PWA bundle weight directly translates to user cost. This is a hard constraint per PROJECT.md.

### D-1. Page weight blows past 1 MB on first load

- **Pitfall:** Next.js default builds with `framer-motion`, Lottie, charting libraries, fonts, and Tailwind ship at 1.5–2.5 MB transferred even with code-splitting. On a Ghana 3G connection at MTN/Vodafone congested-hour speeds, that's 15–25 seconds to interactive.
- **Why it happens:** Modern web tooling defaults are designed for fast connections. Each "nice" library adds 50–200 KB and they accumulate quietly.
- **Warning signs:**
  - No bundle-size budget in CI.
  - Lighthouse "Total page weight" on dashboard > 600 KB transferred.
  - `next build` output shows any single chunk > 200 KB gzipped.
- **Prevention:**
  - **Set a hard budget in CI:** First Load JS < 180 KB gzipped on the landing + dashboard routes. Use `@next/bundle-analyzer` or `size-limit` to enforce.
  - **Defer Lottie/Rive:** dynamic-import the avatar animation on the dashboard. Show a static placeholder until the user has been on the page 3+ seconds; only then hydrate the animation. (See D-2.)
  - **Lazy-load charts:** `recharts` / `chart.js` should not be in the initial bundle. Dynamic-import on the dashboard tab visit.
  - **Subset fonts:** ship only the Latin glyph range. Avoid Google Fonts CDN; self-host with `next/font` to control caching.
  - **Test on real network throttling:** Chrome DevTools "Slow 3G" preset on a real device, not localhost.
- **Phase:** Every phase that ships UI. Add bundle-size CI gate from Phase 1.

### D-2. Lottie/Rive animations bundled eagerly

- **Pitfall:** The fluid avatar that's central to the dashboard UX is loaded on every page, including landing and onboarding, costing 100–300 KB per route.
- **Why it happens:** Tempting to import the player at the top level for "consistency."
- **Warning signs:**
  - `lottie-web` or `@rive-app/canvas` appears in the landing route bundle.
  - Animation JSON files are imported (not fetched) — they end up in JS bundles.
- **Prevention:**
  - **Animation JSON loaded via `fetch`** (not import), cached via service worker, *only* after dashboard route hydrates.
  - **Use Rive over Lottie** when possible — Rive runtime is smaller (~50 KB vs Lottie's ~150 KB) and Rive files are typically smaller than Lottie JSON.
  - **Provide a "Reduce motion" toggle** in settings (also an accessibility win); when toggled, skip the animation runtime entirely. Default ON for users on slow connections (detect via `navigator.connection.effectiveType`).
- **Phase:** Phase that introduces the avatar. Don't ship the avatar without the lazy-load + reduce-motion path.

### D-3. Workout media (GIFs, videos) downloaded over mobile data

- **Pitfall:** wger / ExerciseDB exercise GIFs are 500 KB – 2 MB each. A workout library showing 40 exercises with autoloading thumbnails = 20–80 MB. User browses once, burns a day's data.
- **Why it happens:** GIFs are easy to embed; auto-loading "feels snappy" on dev wifi.
- **Warning signs:**
  - `<img src="...gif">` in the workout list view.
  - Network panel shows GIF requests on scroll.
  - No `loading="lazy"` on workout images.
- **Prevention:**
  - **Static poster image (WebP, <30 KB) for the list view.** Tap to load the GIF/video.
  - **Convert GIFs to MP4/WebM** before serving (10–20× smaller). Many exercise GIFs are 1 MB+; the same animation in WebM is often <100 KB.
  - **Aggressive `Cache-Control: public, max-age=31536000, immutable`** on exercise media. Combine with content-hashed URLs.
  - **Service worker pre-caches** the user's saved workouts on wifi (detect via `navigator.connection.type`) for offline use.
  - **YouTube embeds:** use the lite-youtube-embed pattern (~3 KB placeholder) instead of the full iframe (which loads ~600 KB of player JS even before play).
- **Phase:** Phase that ships the workout library. Don't ship without lazy + WebP/WebM.

### D-4. No service worker / offline cache at launch

- **Pitfall:** App is online-only. Ghana user in a low-signal area opens the app to log a meal; the meal log fails. User stops trusting the app for the very moment they need it.
- **Why it happens:** SW setup feels like polish; offline is deferred. But the value of offline isn't "use the app on a plane" — it's "tolerate flaky 3G during a meal."
- **Warning signs:**
  - No `next-pwa` or custom SW.
  - No "Add to Home Screen" prompt logic.
  - Network errors during a meal-log request just throw to the user.
- **Prevention:**
  - **Ship `next-pwa` from v1.** Cache the app shell, static assets, and the Ghana food table.
  - **Queue meal-log writes when offline,** flush on reconnect. Show a "queued" indicator. Use IndexedDB + a sync handler in the SW.
  - **Pre-cache the user's saved workouts** when they save them (over wifi if possible).
  - **Don't pre-cache LLM responses** — meal-image uploads need connectivity. But *do* gracefully queue manual logging.
- **Phase:** Strong candidate for early-phase work. The cost (one library + a config) is low; the user-trust upside is large.

### D-5. Vercel edge ≠ Ghana POP

- **Pitfall:** Assumption: "Vercel is fast globally." Reality: Vercel's nearest POP to Accra is typically London or Frankfurt; static asset latency from Ghana is 150–250ms RTT. Flask backend on Render us-east is 200–400ms RTT. The kcal estimate roundtrip takes 3–5 seconds wall-clock from Accra even with a fast LLM.
- **Why it happens:** Founders test from US/EU, see <500ms responses, assume it's fine globally.
- **Warning signs:**
  - Never tested from a Ghana IP (or via WebPageTest from Lagos/Johannesburg).
  - No latency telemetry per-region.
- **Prevention:**
  - **Test from Ghana early:** WebPageTest has a Lagos node (closest available). Run weekly; track TTFB and time-to-interactive.
  - **Render backend region:** prefer Frankfurt over US (closer to Accra: ~120ms vs ~190ms). Render Frankfurt or Fly.io `fra` region is the right default.
  - **Edge-cache static API responses** (Ghana food table, exercise library) via Vercel edge or Cloudflare.
  - **Make the kcal call optimistic-UI:** show the loading spinner with "Analyzing..." and a cancel button; users can manually log without waiting.
- **Phase:** Pre-launch validation. Add Lagos WebPageTest to the launch checklist.

---

## MongoDB Atlas

The free M0 tier has hard limits that aren't obvious until they bite. ([Atlas Free Cluster Limits](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/))

### M-1. IP allowlist forgotten → Flask backend can't connect

- **Pitfall:** Local dev works. Deploy Flask to Render/Fly. Backend can't reach Atlas. Spend 90 minutes debugging "connection refused" before realizing Render's dynamic IPs aren't allowlisted.
- **Why it happens:** Atlas defaults to "no access from anywhere." Render/Fly free dynos have dynamic IPs that rotate.
- **Warning signs:**
  - `pymongo.errors.ServerSelectionTimeoutError` in deployed Flask logs.
  - Local dev works fine.
- **Prevention:**
  - **For free tier, allowlist `0.0.0.0/0`** with a strong DB user password. (Not ideal but free M0 has no VPC peering. Document the tradeoff.)
  - **Eventually**, move to a paid tier with VPC peering or PrivateLink and restrict to backend egress IPs.
  - **Add a connection-on-startup health check** in Flask: if Atlas isn't reachable, fail loudly on boot, not on first request.
- **Phase:** First deploy. Add to deploy checklist in Phase 1.

### M-2. M0 connection limit (500) hit during traffic spike

- **Pitfall:** Flask spawns a fresh `MongoClient` per request (or pymongo's pool grows unbounded). Modest spike → 500 connection limit → `ServerSelectionTimeoutError` for all users for 10+ minutes.
- **Why it happens:** Naive Flask + pymongo setups create a client per request. Or multiple Gunicorn workers each open their own pool.
- **Warning signs:**
  - `MongoClient(uri)` called inside route handlers instead of at module level.
  - No `maxPoolSize` set; default is 100 per process × N workers = blows past 500 quickly.
  - Atlas metrics show connection count saturating during load.
- **Prevention:**
  - **One `MongoClient` instance per Flask process,** module-level singleton. Pymongo's client is thread-safe and pooled.
  - **Set `maxPoolSize=10`** explicitly. With 4 Gunicorn workers that's 40 connections — well within the 500 limit.
  - **Monitor connection count in Atlas dashboard** weekly.
- **Phase:** Phase that introduces the Flask backend. Code-review the MongoClient instantiation pattern.

### M-3. Free tier storage (512 MB) consumed by meal photos in GridFS

- **Pitfall:** Implementation stores user meal images in MongoDB GridFS for "simplicity." At 500 KB/image × 3 meals/day × 100 users × 30 days = ~4.5 GB. The 512 MB limit is hit in week 1; writes fail; users see a generic error.
- **Why it happens:** GridFS is a tempting "everything in one place" solution. But Atlas free tier is small, and images are large.
- **Warning signs:**
  - Implementation plan mentions GridFS for images.
  - No object-storage component (S3, R2, Cloudflare Images) in the stack.
  - Atlas storage chart trending up linearly with active users.
- **Prevention:**
  - **Do NOT store images in MongoDB.** Period. Use Cloudflare R2 (free tier 10 GB, no egress fees), Cloudinary (free tier 25 GB), or S3.
  - **Better still: don't store images server-side at all by default.** The kcal estimate is the data point; the image is ephemeral. Per PROJECT.md the privacy stance is "Images are not retained server-side beyond what's needed for the kcal estimate unless the user opts in to a history feature." Match this: send image to LLM, store the estimate result, discard the image.
  - **If history is opt-in:** store opt-in images in R2 with a 90-day TTL.
- **Phase:** Phase that ships meal logging. This is an architectural decision — set before writing code.

### M-4. No backups on free tier — single point of failure

- **Pitfall:** Atlas free M0 has *no backups*. User data corruption or accidental drop = total loss. ([Atlas Free Cluster Limits](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/))
- **Why it happens:** Founders assume "managed = backed up." Free M0 explicitly omits backups; it's not a hidden footnote, but it's easy to miss.
- **Warning signs:**
  - No backup scheduler.
  - No exported snapshots in object storage.
- **Prevention:**
  - **Nightly `mongodump`** from a free GitHub Actions cron → upload to R2 or B2. ~20 lines of YAML. Encrypt the dump with `gpg` using a key in GH Secrets.
  - **Retain 7 daily + 4 weekly + 3 monthly snapshots.**
  - **Test restore quarterly** (restore to a local dev mongo, verify document counts and a sample document).
  - **Upgrade to paid M10 ($57/mo)** before launch-time-meaningful user counts (>500 DAU). M10 includes backups.
- **Phase:** First production deploy. Add to launch checklist.

### M-5. Connection string in code instead of env

- **Pitfall:** Connection string with username + password gets pasted into a commit, then into a public GitHub repo. Atlas detects the leak (it scans GitHub) and rotates the password — your prod backend goes down. Or worse: an attacker scrapes before Atlas does.
- **Why it happens:** Already nearly happened (per the project note: "user pasted it in chat").
- **Warning signs:**
  - `git log -p` shows the connection string anywhere in history.
  - `.env`, `.env.local` not in `.gitignore`.
- **Prevention:**
  - **`.env*` in `.gitignore` from commit 1.** Check via `git check-ignore .env.local`.
  - **Pre-commit hook** (`pre-commit` framework + `detect-secrets` or `gitleaks`) that scans for MongoDB URIs and other secret patterns.
  - **Rotate the current password now** (since it was exposed in chat history per project note), even though it's "just" chat — secret hygiene is binary.
  - **Use Atlas DB users with least privilege** — the Flask user shouldn't be a project admin; create a read/write user scoped to the FitGH database only.
  - **Document required env vars in `.env.example`** without values.
- **Phase:** Phase 0 / initial setup. Block any code commit until this is done.

---

## Auth & Security

### S-1. Flask doesn't validate JWT from frontend

- **Pitfall:** Frontend sends user identity in a header; Flask trusts it. Anyone can curl the backend with `X-User-Id: <any-id>` and read/write that user's data.
- **Why it happens:** "We'll add real auth later." Solo builders cut auth corners under time pressure.
- **Warning signs:**
  - Flask route handlers read `request.headers["X-User-Id"]` directly.
  - No JWT verification middleware.
  - Postman test with fabricated user ID succeeds.
- **Prevention:**
  - **Use a managed auth provider** (Clerk, Supabase Auth, Auth0 — free tiers ample). Avoid rolling your own JWT signing.
  - **Verify JWT on every Flask request** using the provider's JWKS endpoint. `python-jose` or `PyJWT` + the JWKS URL.
  - **Decorator on every protected route:** `@require_auth` extracts and verifies, populates `g.user`. No route reads `request.headers` for identity directly.
  - **Penetration test before launch:** craft a fake JWT, ensure every protected route rejects it.
- **Phase:** Phase that introduces auth. Block kcal-loop ship until JWT validation is enforced.

### S-2. Food images sent to LLM provider without explicit consent disclosure

- **Pitfall:** User uploads a photo of their meal. The photo (which may include their face, kitchen, kids) is sent to Anthropic/OpenAI. The privacy policy doesn't mention this. Diaspora user in EU files GDPR complaint.
- **Why it happens:** "It's just food" — but it's not just food, it's an image taken in the user's home.
- **Warning signs:**
  - Onboarding doesn't mention LLM image processing.
  - Privacy policy is generic ("we use third parties to provide our service") without naming Anthropic/OpenAI.
- **Prevention:**
  - **Onboarding screen:** "FitGH analyzes your meal photos using Anthropic's Claude. Images are sent to Anthropic's servers, not retained by us by default. Continue?" One-time opt-in, stored as a flag on the user record.
  - **Privacy policy names the data processors** (Anthropic, OpenAI, MongoDB, Render/Fly, etc.) and links to their privacy/data policies. Required by GDPR for diaspora users in EU/UK.
  - **Image hygiene:** show a "Tip: photograph just the plate" tip on first capture. Optional client-side face-blur (low priority for v1).
  - **Anthropic's commercial terms:** verify that images sent via API are not used for training (this is standard but verify the contract terms applying to your account).
- **Phase:** Phase that ships the kcal loop (onboarding consent) + Phase 0 (privacy policy draft).

### S-3. User-identifying metadata leaking into LLM prompts

- **Pitfall:** Backend constructs prompt as "Estimate calories for francisyiryel@gmail.com's lunch: [image]". User's name/email is now in Anthropic's logs.
- **Why it happens:** Verbose prompt building during dev; forgotten when shipping.
- **Warning signs:**
  - Prompts include user objects directly.
  - No "scrub PII before sending" step.
- **Prevention:**
  - **The LLM prompt should NEVER contain user PII.** No name, email, location, or any identifier. The prompt contains: system instructions, Ghana food table, the image. That's it.
  - **Code review checklist:** any function that builds an LLM prompt must be reviewed for PII inclusion.
  - **If you need correlation in logs:** use a non-PII session ID, not the user email.
- **Phase:** Phase that ships the kcal loop. Add to PR template.

### S-4. Rate limiting absent → cost attack vector

- **Pitfall:** Bad actor finds the `/api/analyze-meal` endpoint, scripts 10,000 image uploads, you wake up to a $400 Anthropic bill.
- **Why it happens:** Rate limiting is forgotten on greenfield builds. Or it's in front of HTML routes but not API routes.
- **Warning signs:**
  - No `Flask-Limiter` or equivalent.
  - No per-user-per-day cap on LLM calls (see V-3).
  - Endpoint accepts requests without auth in dev mode, and dev mode bleeds into prod.
- **Prevention:**
  - **`Flask-Limiter`** with Redis (or even in-memory for low scale) for IP-level + user-level limits. E.g., 30 req/min/IP, 8 LLM calls/day/user.
  - **Anthropic spend cap** in the Anthropic console (set a hard monthly limit).
  - **Cloudflare in front of Flask** — free tier provides bot protection and IP-level throttling. Combined with Flask-Limiter, you have defense in depth.
  - **Alerting:** Anthropic cost > $X/day → Slack/email/SMS alert. Set X at 2× expected daily cost.
- **Phase:** Phase that ships the kcal loop. Hard requirement before opening signups.

### S-5. CORS misconfigured between Next.js and Flask

- **Pitfall:** Either CORS is too tight (browser blocks legitimate requests) or too loose (`Access-Control-Allow-Origin: *` with credentials, enabling cross-origin attacks).
- **Why it happens:** CORS errors are confusing; the fastest fix is "allow everything."
- **Warning signs:**
  - `flask-cors` configured with `CORS(app, origins="*")` plus `supports_credentials=True` (this is invalid per spec; some implementations log a warning, others silently expose).
  - Browser console shows CORS errors during testing → developer wildcards everything.
- **Prevention:**
  - **Explicit origins:** `CORS(app, origins=["https://fitgh.app", "http://localhost:3000"], supports_credentials=True)`.
  - **Use cookies for auth (with `SameSite=Lax`)** instead of Authorization headers — simpler CORS, CSRF-protected.
  - **Or:** keep JWT in Authorization header, don't use cookies, no `credentials: include`, simpler CORS story.
  - **Test:** from a fake origin (`http://evil.localhost:9999`), the API should reject preflights.
- **Phase:** Phase that connects frontend to backend.

### S-6. No CSRF protection on browser-called Flask endpoints

- **Pitfall:** If you use session cookies for auth, a malicious site can trigger logged-in actions via image tags or auto-submitting forms.
- **Why it happens:** Skipping CSRF when using cookies. Or assuming SPA = no CSRF needed (wrong: cookies still get sent cross-origin if SameSite isn't Strict).
- **Warning signs:**
  - Session cookies without `SameSite=Lax` or `Strict`.
  - No CSRF token on state-changing endpoints when using cookies.
- **Prevention:**
  - **If using cookie auth:** `SameSite=Strict` for the session cookie + double-submit CSRF token pattern, or use `flask-wtf`'s CSRF protection on state-changing routes.
  - **If using bearer-token auth in Authorization header:** CSRF is structurally mitigated (cross-origin requests can't read the token to attach it). But verify no fallback to cookies.
- **Phase:** Phase that introduces auth.

---

## UX

### U-1. Onboarding too long → users bounce

- **Pitfall:** Onboarding asks name, sex, height, weight, age, goal, activity level, dietary restrictions, country, equipment, preferred language. Drop-off at 35% before reaching the dashboard.
- **Why it happens:** Every team member contributes a "necessary" field. The pile is sub-optimal.
- **Warning signs:**
  - Onboarding has >5 screens.
  - Median onboarding time > 60 seconds.
  - Funnel: <70% completion.
- **Prevention:**
  - **3 screens max:** (1) goal (lose weight / build muscle); (2) height + weight + age + sex (one screen); (3) snap your first meal. Equipment / activity level can be inferred or asked later.
  - **Skip everything possible:** allow "skip for now" on every field; ask again when relevant.
  - **Show value immediately:** the first meal photo should happen within 90 seconds of first app open. The faster the "wow" the better the retention.
- **Phase:** Phase that ships onboarding. Track funnel from day 1.

### U-2. Daily target shown but no fast log path → no habit forms

- **Pitfall:** Dashboard shows "1850 kcal target, 0 logged today" with a "Log meal" button that requires 4 taps + image + waiting + correction. User looks, doesn't log, drops off in week 2.
- **Why it happens:** Logging feels like work; the UX makes it feel more like work than necessary.
- **Warning signs:**
  - Time-from-app-open-to-meal-logged > 45 seconds (median).
  - "Quick add" path doesn't exist.
- **Prevention:**
  - **One-tap recent meals:** show the last 3 meals logged as quick-add chips on the dashboard ("Repeat breakfast", "Repeat usual jollof").
  - **Manual quick-add path** (skip image, type kcal) for users who already know.
  - **Push notification midday + evening** (opt-in, soft) — "Quick log: what did you have for lunch?"
- **Phase:** Phase that ships the daily log loop.

### U-3. Workout library overwhelming → users scroll, don't start

- **Pitfall:** 200 exercises in a flat list; user scrolls, gets paralyzed, closes the app.
- **Why it happens:** "More content = better." Wrong.
- **Warning signs:**
  - List view has >20 items on first load with no filtering applied.
  - No "Suggested for you today" prominent CTA.
- **Prevention:**
  - **Default view: "Today's workout" (5–8 exercises) for the user's goal + equipment.** Not a library.
  - **Library is one tap deeper,** with strong filters (goal, equipment, muscle, duration).
  - **Recommended workouts seeded by template** for first 4 weeks (push/pull/legs split for muscle, full-body for weight loss). Not a discovery problem to solve from scratch.
- **Phase:** Phase that ships workouts.

### U-4. Avatar animation is novelty without informational value

- **Pitfall:** Lottie avatar moves nicely but tells the user nothing they can act on. After week 2 users tune it out; it's just bundle weight.
- **Why it happens:** Designers ship what's fun to design. Users want feedback signals, not animation for its own sake.
- **Warning signs:**
  - Avatar animation doesn't change based on user state.
  - User testing: "What does the avatar mean?" gets shrugs.
- **Prevention:**
  - **Make the avatar reflect state:** lean/lighter when in deficit and tracking; stronger/larger when hitting protein targets and bulking; slumped when streak is broken. The animation should *say something*.
  - **Or cut it** — if you can't make it informational, ship a static illustration. It's lighter, and PROJECT.md explicitly flags data-light as a hard constraint.
  - **A/B test in beta:** does the avatar correlate with retention? If not, kill it.
- **Phase:** Phase that introduces the dashboard avatar. Decide cut-or-refine before launch.

### U-5. Streak break = user disengagement

- **Pitfall:** Day 14 streak, user travels, misses a day, streak resets to 0. Demoralised. Stops opening the app.
- **Why it happens:** "Streak" mechanic is borrowed from Duolingo without Duolingo's recovery features.
- **Warning signs:**
  - Drop-off spike on day after streak-break.
  - No "streak freeze" or grace mechanic.
- **Prevention:**
  - **Soft streak:** miss one day, streak pauses (not resets). Miss two consecutive, then it resets. Show "streak paused" gently.
  - **Streak freeze tokens:** 2 per month, auto-applied. Like Duolingo. Users feel safety, not threat.
  - **Or don't lead with streaks at all:** lead with "5 of 7 days this week" — frames partial wins as wins.
- **Phase:** Phase that introduces streak. Or skip streaks for v1 and let retention metrics inform.

---

## Legal

### L-1. YouTube embeds without proper terms compliance

- **Pitfall:** App embeds YouTube videos; doesn't show the YouTube logo, doesn't link to the video on YouTube, customises the player heavily. Google could (rarely does, but could) require takedown; more practically, hides traffic from creators who could be partners.
- **Why it happens:** "It's just an iframe."
- **Warning signs:**
  - Custom-styled player without YouTube branding.
  - No link to the original video page.
  - Removing the "Watch on YouTube" affordance.
- **Prevention:**
  - **Use the official YouTube IFrame Player API** with default branding visible. ([YouTube IFrame Player API Terms](https://developers.google.com/youtube/iframe_api_reference)).
  - **Show creator name + "Watch on YouTube" link** below every embed. Cheap goodwill; legally required.
  - **Don't proxy or re-host** videos. Embed only.
  - **Track per-creator embed counts** — useful for future partnership outreach.
- **Phase:** Phase that introduces video embeds.

### L-2. wger / ExerciseDB licence requires attribution that's missing

- **Pitfall:** App displays wger exercise data without attribution. wger uses CC-BY-SA 4.0 which *requires* attribution; you're in technical breach. ExerciseDB's licence (RapidAPI) has its own terms.
- **Why it happens:** Attribution feels like a footer concern, gets forgotten.
- **Warning signs:**
  - No "Exercise data from wger.de under CC-BY-SA 4.0" or equivalent in the app.
  - No `LICENSES.md` documenting upstream licences.
- **Prevention:**
  - **Footer attribution on every workout page:** "Exercise data from [wger.de](https://wger.de) (CC-BY-SA 4.0), [ExerciseDB], [MuscleWiki]."
  - **`LICENSES.md` in the repo** documenting every third-party asset source and its licence.
  - **CC-BY-SA is share-alike:** if you create derivative exercise data, your derivative must also be CC-BY-SA. Be careful what you call "your" data.
  - **Read ExerciseDB's terms before launch** — RapidAPI-distributed datasets sometimes prohibit redistribution in your app; you may need to call their API at runtime rather than mirror it.
- **Phase:** Phase that ships workouts. Block launch until attribution + LICENSES.md exist.

### L-3. Privacy policy not in place at v1 launch

- **Pitfall:** Launch happens without a privacy policy. UK/EU diaspora users sign up; you're in breach of GDPR / UK GDPR before the first kcal is logged. App stores (if listed as PWA) will also flag.
- **Why it happens:** Privacy policy feels like later-work. Founders use a template that doesn't reflect the actual data flows.
- **Warning signs:**
  - No `/privacy` route.
  - Onboarding doesn't link to a privacy policy.
- **Prevention:**
  - **Ship a real privacy policy before launch.** Use a service like Termly or iubenda (~$10/mo) or hand-roll one. Cover: (a) what's collected (profile, weight, meal images, meal estimates), (b) who processes it (Anthropic, OpenAI, MongoDB Atlas, Render/Fly, Vercel), (c) retention (per PROJECT.md: images not retained by default), (d) user rights (access, deletion), (e) contact for data requests.
  - **GDPR rights endpoints:** support data export and delete-my-account from day 1. Two Flask routes; user clicks one button in settings. This is *required*, not optional.
  - **Cookie banner only if you actually use non-essential cookies** — auth cookies are essential and don't require banners.
- **Phase:** Pre-launch. Block launch until privacy policy + delete-account flow exist.

### L-4. Health-claim language: "fitness tracking" vs "medical advice"

- **Pitfall:** Marketing copy or in-app language says "FitGH will help you lose weight" or "achieve your goal weight." User in poor health follows the deficit blindly, has an adverse event, sues.
- **Why it happens:** Confident copy reads better. But "will help you lose weight" implies clinical efficacy.
- **Warning signs:**
  - Marketing/onboarding uses verbs like "will," "achieves," "guarantees."
  - No disclaimer about consulting a healthcare provider.
  - Calorie deficits below medical thresholds (e.g., 1200 kcal/day for women, 1500 for men) are recommended without warning.
- **Prevention:**
  - **Language audit:** "tracks your progress," "supports your goals," "helps you understand your intake." Never "will make you lose weight."
  - **Floor the calculated deficit:** never recommend <1200 kcal/day for women or <1500 kcal/day for men by default. If the math says lower, cap and show a warning to consult a clinician.
  - **Standard disclaimer in onboarding + footer:** "FitGH is a fitness tracking tool, not medical advice. Consult a healthcare provider before making significant dietary or exercise changes, especially if you have pre-existing conditions."
  - **Don't claim to diagnose or treat anything** — including obesity, diabetes risk, etc.
- **Phase:** Phase that ships TDEE/goal calculation + marketing site.

---

## Solo-Build Velocity

These pitfalls don't break the app — they prevent it from shipping.

### B-1. Perfecting the Ghana food list before shipping

- **Pitfall:** "I need every dish from every region before I can launch." 6 months in, food list is at 200 dishes, no users.
- **Why it happens:** Comprehensiveness feels like quality. Also: the list is researchable from your desk, while user feedback requires shipping.
- **Warning signs:**
  - Food table has >50 dishes before any user has tested the loop.
  - Spending >2 weeks on food data without shipping.
- **Prevention:**
  - **Start with the top 25 dishes.** Jollof (variants), waakye, banku, fufu, kenkey, kelewele, red red, kontomire, palmnut soup, groundnut soup, light soup, tilapia (grilled), boiled yam, fried yam, plantain (boiled/fried), gari soakings, koko, koko + koose, ampesi, omotuo, gari foto, eba, ga kenkey, fante kenkey, shito. That's 25 and it covers ~80% of daily eating in Accra. ([FAO/INFOODS West Africa table](https://www.fao.org/3/i3496e/i3496e.pdf) is the canonical source for kcal values.)
  - **Add dishes driven by user "unknown" reports** post-launch. Real demand, not speculation.
  - **Set a deadline:** "I will ship the kcal loop with whatever food table I have on [date]."
- **Phase:** Phase that builds the food table. Hard cap at 25 dishes for v1.

### B-2. Custom-trained food vision model before LLM proves the loop

- **Pitfall:** "LLM accuracy isn't perfect; I'll train a CNN on a Ghanaian food dataset." 3 months on data collection + training. LLM v1 never ships. Loop never gets validated. (PROJECT.md explicitly flags this as out-of-scope — keep it that way.)
- **Why it happens:** ML feels prestigious. Engineering ego pulls toward "real ML" instead of "an API call."
- **Warning signs:**
  - You're reading papers on food classification in week 2.
  - You're labeling images yourself.
  - You're not shipping.
- **Prevention:**
  - **Ship the LLM-vision loop first.** Measure MAPE in production with real users. *Then* decide if accuracy needs improvement worth a custom model.
  - **A custom model is worth it only if** (a) MAPE >35% on the top 10 dishes, AND (b) cost per estimate is breaking unit economics. Neither has been measured yet.
  - **PROJECT.md flags this as out-of-scope.** Hold the line.
- **Phase:** N/A — explicitly deferred.

### B-3. Over-engineering offline cache before validating users want it

- **Pitfall:** You build elaborate IndexedDB-backed offline-first sync with conflict resolution. Users actually open the app online 95% of the time. 4 weeks down a hole.
- **Why it happens:** "Data-light Ghana" gets conflated with "fully offline app." Different problems.
- **Warning signs:**
  - More than 3 days on offline sync logic before launching.
  - Designing conflict-resolution policy before any user has experienced a conflict.
- **Prevention:**
  - **Ship a service worker that caches the app shell + static assets (D-4).** That's the 80% win.
  - **Queue meal-log POSTs when offline + retry on reconnect.** ~50 lines of code with Workbox.
  - **Don't build offline-first for everything else.** Workouts can fail offline; users will accept that.
  - **Measure offline usage** post-launch via telemetry. Build more only if data justifies it.
- **Phase:** Initial SW work in Phase 1; advanced offline only if data justifies it later.

### B-4. Designing for monetisation before validating retention

- **Pitfall:** Building Stripe, subscription tiers, paywall logic in week 3 instead of getting the first 100 users to week 4 retention.
- **Why it happens:** Founders need to see a revenue path to stay motivated. Building monetisation feels like progress.
- **Warning signs:**
  - Stripe integration appears in the codebase before 50 users have used the app.
  - Conversations about "premium tier" before week-4 retention is measured.
- **Prevention:**
  - **PROJECT.md is clear: "v1 is free; monetisation explored after PMF signal."** Hold the line.
  - **The metric to hit before discussing monetisation: 30%+ day-28 retention** on a cohort of 100+ users. Below that, monetisation is a distraction.
  - **If you must think about pricing: write it in a doc, don't build it.** Notion page > code.
- **Phase:** N/A — explicitly deferred. Don't entertain in v1.

### B-5. Polishing the avatar before the kcal loop works

- **Pitfall:** Lottie animation tuning consumes 2 weeks while the kcal estimate still has 40% error.
- **Why it happens:** Visual polish gives immediate feedback; algorithmic accuracy is slow and frustrating.
- **Warning signs:**
  - More commits to avatar/animation than to LLM prompts or food-table data.
- **Prevention:**
  - **Order of work: kcal loop accuracy → daily log UX → workouts → animations.** Animations are last because they're cuttable; the loop is core (per PROJECT.md "If everything else fails, this loop must work").
  - **Ship a static SVG avatar in v1.** Animate in v1.1 if retention justifies the bundle weight.
- **Phase:** Sequencing. The roadmapper should put the kcal loop before any visual polish.

### B-6. Building the workout library before validating the food loop

- **Pitfall:** 3 weeks on exercise data, filtering UI, GIF compression. Meanwhile the LLM-vision loop hasn't been tested with real users. Food was the wedge; workouts were the differentiator-helper.
- **Why it happens:** The workout library has clearer requirements (it's a CRUD problem); the food loop is uncertain. Founders flee uncertainty.
- **Warning signs:**
  - Workout library is "done" before the kcal loop has been used by anyone besides you.
- **Prevention:**
  - **Ship the food loop first, alone, to a seed cohort of 20–50 users.** Iterate to <25% MAPE before adding workouts.
  - **Workouts can be v1.1.** They're additive, not core.
  - **PROJECT.md core value:** "Snap a meal, see kcal in seconds…" — workouts aren't in the core value sentence.
- **Phase:** Sequencing. Food loop → workouts. Not parallel; sequential.

---

## Priority Matrix — Top 5 to address in v1

If only five pitfalls get prevention work in v1, these are the five. Ranked by *cost of getting it wrong* × *likelihood of getting it wrong on a solo build*.

| # | Pitfall | Why top priority | Phase to address |
|---|---------|------------------|------------------|
| 1 | **G-4. Multi-dish plate schema** | Schema decision; refactor cost is high; multi-component plates are the norm in this cuisine, not the exception. Get this wrong at v1 and every subsequent feature is built on a wrong foundation. | Phase that ships the kcal loop (schema before code). |
| 2 | **V-3. LLM cost ceiling + per-user cap** | At 1000 users this is $40/day with no monetisation. Without a cap + caching + image resize, the app cannot scale without breaking the founder financially. Easy to add early, painful to retrofit. | Phase that ships the kcal loop (before any signup beyond seed cohort). |
| 3 | **M-3. Don't store meal images in MongoDB** | Architectural decision; storing in GridFS will hit the 512 MB free-tier ceiling in week 1 of any meaningful traffic. The right answer (don't store, or use R2) is cheap to implement early, expensive to migrate. | Phase that ships meal logging. |
| 4 | **G-2. Ghana food table built on Western databases** | Wedge differentiator; if portion+kcal calibration is wrong, the entire value prop ("food the user actually eats") fails. Must be built from West Africa-specific sources, not MyFitnessPal. | Phase 0 / data-prep phase (before the kcal loop ships). |
| 5 | **V-7. User correction loop** | Without it, accuracy errors compound into trust loss within days. With it, users will tolerate ~30% error because they can fix it in one tap. Single biggest retention lever in the loop. | Phase that ships the kcal loop. |

**Honorable mentions** (high impact but lower urgency, or already partially handled by PROJECT.md):

- M-5 (env hygiene) — already flagged in PROJECT.md but needs `gitleaks` enforcement, not just gitignore.
- S-2 (LLM consent disclosure) — PROJECT.md flags it; just don't forget at launch.
- D-1 (page-weight budget in CI) — cheap to add early, painful to retrofit.
- L-3 (privacy policy + delete-account flow) — required by law for diaspora cohort.

---

## Sources

### High-confidence (Context7 / official documentation)
- [MongoDB Atlas Free Cluster Limits](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/) — verifies 512 MB / 500 connections / no backups.
- [Anthropic API Pricing](https://www.finout.io/blog/anthropic-api-pricing) — $3/M input, $15/M output for Claude 3.5 Sonnet; prompt caching.

### Medium-confidence (peer-reviewed research)
- [An Evaluation of ChatGPT for Nutrient Content Estimation from Meal Photographs](https://www.mdpi.com/2072-6643/17/4/607) — portion underestimation in 76% of medium/large meals; calorie MAPE 0.1%–38.3%.
- [Dietary Assessment with Multimodal ChatGPT: Systematic Analysis](https://arxiv.org/html/2312.08592v1) — GPT-4V food ID 87.5–89.8%; portion correlation r=0.81.
- [African foods for deep-learning food recognition (dataset)](https://www.sciencedirect.com/science/article/pii/S2352340924000659) — documents the data gap that underlies G-1.
- [FAO/INFOODS West Africa Food Composition Table](https://www.fao.org/3/i3496e/i3496e.pdf) — canonical kcal/macro source for G-2.

### Medium-confidence (industry / community)
- [YouTube IFrame Player API Reference](https://developers.google.com/youtube/iframe_api_reference) — L-1 compliance.
- [wger licence (CC-BY-SA 4.0)](https://wger.de/en/software/api) — L-2 attribution requirement.

### Confidence levels by cluster
- **LLM Vision (V-*):** HIGH on pricing math and accuracy bounds (research-backed). MEDIUM on prevention specifics (Anthropic prompt caching syntax verified; per-user cap pattern is best-practice not standard).
- **Ghana Food (G-*):** MEDIUM. African-food dataset literature confirms the gap; specific dish-level accuracy needs your own measurement.
- **Data-Light (D-*):** HIGH on bundle-size and SW patterns; MEDIUM on Vercel Ghana latency (needs your WebPageTest measurement to confirm).
- **MongoDB (M-*):** HIGH — all numbers from official Atlas docs.
- **Auth/Security (S-*):** HIGH on patterns; standard application-security practice.
- **UX (U-*):** MEDIUM — patterns from app analytics literature; specific thresholds (60s onboarding, 45s log time) are heuristics not rules.
- **Legal (L-*):** MEDIUM-HIGH on attribution requirements; verify with a lawyer before relying on the GDPR specifics for your jurisdiction.
- **Solo-build (B-*):** Opinion, but grounded in PROJECT.md's own explicit out-of-scope decisions.
