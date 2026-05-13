---
phase: 04-image-kcal-loop
plan: 04
type: execute
wave: 1
depends_on: []
files_modified:
  # Backend — models + helpers + db wiring
  - backend/app/models/__init__.py
  - backend/app/models/vision.py
  - backend/app/lib/vision.py
  - backend/app/lib/rate_limit.py
  - backend/app/db.py
  - backend/app/config.py
  - backend/requirements.txt
  - backend/tests/conftest.py
  - backend/tests/test_vision_models.py
  - backend/tests/test_vision_lib.py
  - backend/tests/test_rate_limit.py
  # Backend — routes
  - backend/app/routes/scan.py
  - backend/app/routes/corrections.py
  - backend/app/__init__.py
  - backend/tests/test_scan_route.py
  - backend/tests/test_corrections_route.py
  - backend/tests/golden_set/README.md
  # Shared JSON Schemas
  - shared/schemas/vision-response.schema.json
  # Frontend — compression helper + Zod + BFFs
  - frontend/package.json
  - frontend/src/lib/compress-image.ts
  - frontend/src/lib/zod-schemas.ts
  - frontend/src/lib/api-server.ts
  - frontend/src/app/api/meals/scan/route.ts
  - frontend/src/app/api/corrections/route.ts
  - frontend/middleware.ts
  # Frontend — scan UI
  - frontend/src/app/dashboard/scan-sheet.tsx
  - frontend/src/app/dashboard/snap-meal-cta.tsx
  - frontend/src/app/dashboard/scan-result-chips.tsx
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/dashboard/log-meal-cta.tsx
  - frontend/src/app/layout.tsx
  - frontend/src/components/service-paused-banner.tsx
  # Deploy + env + traceability
  - render.yaml
  - backend/.env.example
  - .planning/REQUIREMENTS.md
autonomous: false
requirements:
  - VIS-01
  - VIS-02
  - VIS-03
  - VIS-04
  - VIS-05
  - VIS-06
  - VIS-07
  - VIS-08
  - VIS-09
  - VIS-10
  - VIS-11
  - VIS-12
  - OBS-03
user_setup:
  - service: anthropic
    why: "Claude Sonnet 4.6 vision API — the wedge feature. Without this key the /meals/scan route returns 503; manual meal log still works."
    env_vars:
      - name: ANTHROPIC_API_KEY
        source: "https://console.anthropic.com/ → Settings → API keys → Create key (sk-ant-...)"
    dashboard_config:
      - task: "Add billing: at least $5 prepaid credit (~1,250 vision calls at Sonnet 4.6 pricing)"
        location: "https://console.anthropic.com/ → Settings → Billing"
      - task: "Paste ANTHROPIC_API_KEY into backend/.env.local (gitignored)"
        location: "Local repo: backend/.env.local"
      - task: "Paste ANTHROPIC_API_KEY into Render fitgh-api → Environment (sync: false). Trigger redeploy."
        location: "https://dashboard.render.com → fitgh-api → Environment"
      - task: "(Optional) Set VISION_DAILY_CAP_USD (default 5.0 in code) and COST_ALERT_WEBHOOK_URL (Discord/Slack incoming webhook URL)."
        location: "Render fitgh-api → Environment"

must_haves:
  truths:
    - "A signed-in user on /dashboard taps 'Snap a meal' → file input opens with capture=environment so mobile devices launch the rear camera; user uploads or captures a JPEG/PNG → browser compresses it to ≤1024 px long edge, ≤0.5 MB, JPEG q=0.85 BEFORE network egress (VIS-02)"
    - "The compressed blob is POSTed as multipart/form-data to /api/meals/scan; the BFF forwards verbatim to Flask /meals/scan with the user's Bearer JWT; total round-trip target p50 ≤ 5 s on the happy path"
    - "Flask /meals/scan enforces @require_auth → checks vision_usage.{user_id, today} count < 8 (else 429 daily_cap) → checks system_state.vision_budget.spend_usd ≤ cap_usd (else 503 service_paused) → reads image bytes into memory → base64-encodes → calls Anthropic Sonnet 4.6 with tool_use schema `report_meal_components` and the cached system prompt (Ghana table + user's last 20 corrections) → parses response → table-rematches each component name against ghana_foods → computes kcal_point via app.lib.meals.compute_kcal_for_component → returns {components: [...]} (VIS-03, VIS-04, VIS-05)"
    - "After the Anthropic call returns, image bytes are dropped from memory (no temp file, no GridFS write, no R2 upload, no DB write of the bytes); test asserts the route handler tmpdir is empty and no file descriptors leak (VIS-11)"
    - "Frontend renders the returned components as tap-to-edit ComponentChip rows (reusing Phase 3's chip + FoodSearch); user can change dish name (cmdk autocomplete over /api/foods), adjust portion slider, or remove a chip; total kcal range + point estimate update live; on Confirm, the chips POST to /api/meals (Phase 3 endpoint) with source='ai_vision' carrying kcal_low/high/confidence/ai_metadata so the persisted shape is the day-1 multi-component Meal — NO separate ai_meals collection (VIS-06, VIS-07, VIS-12)"
    - "When the user edits or removes a chip on the scan-result sheet (before Confirm), the modal POSTs each correction to /api/corrections; Flask appends a user_corrections doc {user_id, original_name, corrected_name, original_portion_g, corrected_portion_g, original_food_id, corrected_food_id, corrected_at}; on the user's NEXT scan, build_system_prompt reads the last 20 corrections for that user and injects them as a 'User history' block in the cached system prompt so the model biases toward the user's past dishes (VIS-08)"
    - "On the 9th scan in a UTC-day, Flask returns 429 {error: 'daily_cap', reset_at: '<tomorrow_user_tz_midnight>'}; FE renders a toast 'You've used today's 8 scans — please log this one manually' and auto-opens the Phase 3 MealLogModal (VIS-09)"
    - "When system_state.vision_budget.spend_usd > VISION_DAILY_CAP_USD (default 5.0), Flask returns 503 {error: 'service_paused', reason: 'daily_budget'}; FE renders a site-wide banner 'Vision paused for the day — please log manually' on /dashboard and /history layouts; manual log still works (VIS-10)"
    - "Each successful scan increments system_state.vision_budget.spend_usd by compute_cost_usd(input_tokens, output_tokens) where input = $0.003/1k cached + $0.0125/1k uncached, output = $0.015/1k (Sonnet 4.6 pricing). When DAU_today is known and spend_usd / DAU_today > $0.05, Flask POSTs a Discord/Slack-compatible JSON payload to COST_ALERT_WEBHOOK_URL (if set; else WARN-logs to Render stdout) — OBS-03"
    - "Anthropic SDK calls are mocked in CI via respx (intercepting the SDK's underlying httpx transport); zero real API calls in pytest; a single live test in test_scan_route.py is gated by env var RUN_LIVE_VISION_TEST=1 and skipped by default"
    - "Operator pastes ANTHROPIC_API_KEY into backend/.env.local AND into Render fitgh-api Environment; backend/.env.example documents it; render.yaml declares ANTHROPIC_API_KEY (sync: false); backend/app/config.py validates the key is present when FLASK_ENV=production"
  artifacts:
    - path: "backend/app/models/vision.py"
      provides: "Pydantic v2 models for the vision pipeline — VisionComponentRaw (LLM tool-use shape), VisionResponse (parsed), VisionUsageDoc (vision_usage collection), SystemStateDoc (system_state singleton), UserCorrectionDoc (user_corrections collection), AiMetadata (matches Meal.ai_metadata sub-doc)"
      exports: ["VisionComponentRaw", "VisionResponse", "VisionUsageDoc", "SystemStateDoc", "UserCorrectionDoc", "AiMetadata", "ANTHROPIC_TOOL_SCHEMA"]
    - path: "backend/app/lib/vision.py"
      provides: "Pure helpers — build_system_prompt(ghana_foods, user_corrections) -> dict (system prompt + cache_control marker), parse_tool_use_response(raw) -> VisionResponse, table_rematch(components, ghana_foods) -> list[dict] (persisted Component shape), compute_cost_usd(usage), build_user_message(image_b64, mime). No SDK import, no Mongo."
      exports: ["build_system_prompt", "parse_tool_use_response", "table_rematch", "compute_cost_usd", "build_user_message", "MODEL_PRICING_PER_1K"]
    - path: "backend/app/lib/rate_limit.py"
      provides: "Atomic Mongo helpers for the 8/day per-user cap and the global $/day budget — check_and_increment_user_daily(user_id, today_str) -> tuple[allowed: bool, count: int], check_and_record_spend(today_str, spend_usd, cap_usd) -> tuple[allowed: bool, post_spend: float]. Uses Mongo $inc + $setOnInsert with upsert=True for race-safe increments."
      exports: ["check_and_increment_user_daily", "check_and_record_spend", "today_utc_str", "USER_DAILY_CAP", "DEFAULT_VISION_DAILY_CAP_USD"]
    - path: "backend/app/db.py"
      provides: "Extended with vision_usage + system_state + user_corrections collection singletons (Phase 3 pattern)"
    - path: "backend/app/config.py"
      provides: "Extended with ANTHROPIC_API_KEY (mandatory in production), LLM_VISION_MODEL (default 'claude-sonnet-4-6'), VISION_DAILY_CAP_USD (default 5.0), COST_ALERT_WEBHOOK_URL (optional)"
    - path: "backend/app/routes/scan.py"
      provides: "POST /meals/scan blueprint — multipart/form-data image in → components JSON out. Enforces daily cap + global breaker, calls Anthropic SDK, parses + table-rematches, records spend, fires cost-alert webhook."
      exports: ["bp"]
    - path: "backend/app/routes/corrections.py"
      provides: "POST /corrections blueprint — append a user_corrections doc when the user edits a chip on the scan-result sheet."
      exports: ["bp"]
    - path: "backend/requirements.txt"
      provides: "Adds anthropic>=0.40, respx>=0.21 (dev), pytest-asyncio>=0.24 (dev). No Sentry re-init, no Files API extras."
    - path: "shared/schemas/vision-response.schema.json"
      provides: "JSON Schema for the parsed vision response — used as the contract between Flask and Next.js; mirrored by Zod in zod-schemas.ts"
    - path: "frontend/src/lib/compress-image.ts"
      provides: "Thin wrapper around browser-image-compression: compressMealImage(File) -> File with options {maxSizeMB: 0.5, maxWidthOrHeight: 1024, fileType: 'image/jpeg', initialQuality: 0.85, useWebWorker: true}"
      exports: ["compressMealImage", "COMPRESS_OPTS"]
    - path: "frontend/src/lib/zod-schemas.ts"
      provides: "Extended with visionComponentSchema, visionResponseSchema, userCorrectionInputSchema, AiMetadata + VisionResponse types"
      exports: ["visionResponseSchema", "userCorrectionInputSchema", "VisionResponse", "VisionComponent", "AiMetadata"]
    - path: "frontend/src/lib/api-server.ts"
      provides: "Extended with forwardMultipart(method, path, formData) — same JWT-attaching shape as forwardToFlask but passes multipart/form-data through without re-serialisation"
      exports: ["forwardToFlask", "forwardMultipart"]
    - path: "frontend/src/app/api/meals/scan/route.ts"
      provides: "BFF POST /api/meals/scan — reads multipart FormData and forwardMultipart('POST', '/meals/scan', formData)"
    - path: "frontend/src/app/api/corrections/route.ts"
      provides: "BFF POST /api/corrections — forwardToFlask('POST', '/corrections', body)"
    - path: "frontend/src/app/dashboard/scan-sheet.tsx"
      provides: "Client component — Sheet hosting camera input, compression call, POST to /api/meals/scan, loading state, error states (429/503/network/parse), ScanResultChips render, Confirm button"
    - path: "frontend/src/app/dashboard/snap-meal-cta.tsx"
      provides: "Client component — 'Snap a meal' button on /dashboard that opens ScanSheet; sibling to LogMealCta"
    - path: "frontend/src/app/dashboard/scan-result-chips.tsx"
      provides: "Client component — vertical list of editable ComponentChips (reuses Phase 3 ComponentChip + FoodSearch). On chip change/remove fires onCorrection callback that POSTs to /api/corrections."
    - path: "frontend/src/app/dashboard/log-meal-cta.tsx"
      provides: "Extended — wires in SnapMealCta + ScanSheet alongside the existing manual MealLogModal; ScanSheet 'Confirm' falls through to the same POST /api/meals path as manual"
    - path: "frontend/src/components/service-paused-banner.tsx"
      provides: "Server component — checks GET /api/scan-budget (or reads a system_state doc via /api/me extension) and renders a banner when global budget is exhausted; absent otherwise"
    - path: "render.yaml"
      provides: "Extended fitgh-api envVars — ANTHROPIC_API_KEY (sync: false), LLM_VISION_MODEL (value: claude-sonnet-4-6), VISION_DAILY_CAP_USD (value: '5.0'), COST_ALERT_WEBHOOK_URL (sync: false)"
    - path: "backend/.env.example"
      provides: "Documents ANTHROPIC_API_KEY, LLM_VISION_MODEL, VISION_DAILY_CAP_USD, COST_ALERT_WEBHOOK_URL — without values; gitignore pattern unchanged"
    - path: "backend/tests/golden_set/README.md"
      provides: "Phase 7 hook — placeholder directory explaining how to drop 30 photos + expected components for the golden-set re-run on any model bump"
  key_links:
    - from: "frontend/src/app/dashboard/scan-sheet.tsx"
      to: "/api/meals/scan"
      via: "fetch with FormData body after compressMealImage"
      pattern: "fetch.*api/meals/scan"
    - from: "frontend/src/app/api/meals/scan/route.ts"
      to: "backend POST /meals/scan"
      via: "forwardMultipart('POST', '/meals/scan', formData)"
      pattern: "forwardMultipart.*meals/scan"
    - from: "backend/app/routes/scan.py"
      to: "app.lib.rate_limit.check_and_increment_user_daily + check_and_record_spend"
      via: "Mongo $inc with upsert — race-safe (no separate read-modify-write)"
      pattern: "check_and_increment_user_daily|check_and_record_spend"
    - from: "backend/app/routes/scan.py"
      to: "anthropic.Anthropic(api_key=...).messages.create(model=LLM_VISION_MODEL, tools=[...], system=cached_prompt)"
      via: "official SDK; respx intercepts the underlying httpx transport in tests"
      pattern: "Anthropic.*messages.create"
    - from: "backend/app/routes/scan.py"
      to: "app.lib.vision.table_rematch + app.lib.meals.compute_kcal_for_component"
      via: "post-parse, recompute each component's kcal_point from the Ghana table"
      pattern: "table_rematch|compute_kcal_for_component"
    - from: "backend/app/routes/scan.py"
      to: "image bytes discard"
      via: "no temp file, no GridFS write, image_b64 goes out of scope at end of handler"
      pattern: "del image_b64|# image bytes discarded"
    - from: "backend/app/routes/corrections.py"
      to: "db_mod.user_corrections.insert_one"
      via: "@require_auth → user_id from g.clerk_user_id"
      pattern: "user_corrections.insert_one"
    - from: "backend/app/routes/scan.py (next call)"
      to: "build_system_prompt with last 20 corrections"
      via: "db_mod.user_corrections.find({user_id: g.clerk_user_id}).sort('corrected_at', -1).limit(20)"
      pattern: "user_corrections.find.*limit\\(20\\)"
    - from: "frontend/src/app/dashboard/scan-sheet.tsx (Confirm)"
      to: "/api/meals (Phase 3 endpoint)"
      via: "POST with components mapped to ComponentCreate shape + ai_metadata in the meal-level body"
      pattern: "fetch.*api/meals[^/]"
    - from: "backend/app/routes/scan.py (alert)"
      to: "COST_ALERT_WEBHOOK_URL"
      via: "httpx.post with Discord/Slack-compatible {content: '...'} payload when spend_per_dau > 0.05"
      pattern: "COST_ALERT_WEBHOOK_URL|spend_per_dau"
---

# Phase 4 Plan 04 — Image → Kcal Core Loop (THE WEDGE)

## Phase Goal

A user can snap a photo of their plate from `/dashboard`, see each visible component identified separately as tap-to-edit chips with kcal ranges within ~5 seconds, correct the dish or portion inline if wrong, and have the confirmed meal persist via **the same multi-component schema as Phase 3** — while every request enforces the per-user 8/day cap and the global $/day circuit breaker, and **no image bytes are retained server-side**.

(From ROADMAP.md Phase 4. This is THE wedge feature — if everything else fails, this loop must work.)

## Success Criteria (from ROADMAP.md)

1. Capture/upload a meal photo from `/dashboard`, the image is compressed client-side (≤1024 px long edge, ≤0.5 MB, JPEG q=0.85), and within ~5 seconds the user sees each component (e.g., "jollof rice", "chicken thigh", "salad") identified separately, each with kcal range (low/high) and a total range — never a single point estimate.
2. Each component is presented as a tap-to-edit chip — user can change the dish name via Ghana-table autocomplete, adjust the portion slider, or remove the component entirely, and the total kcal recomputes; corrections are persisted to `user_corrections` and bias defaults on the next scan.
3. On confirm, the meal is saved via the **same multi-component schema** as a manually logged meal (no separate `ai_meals` collection), with kcal recomputed via Ghana-table re-match (`kcal_per_100g × portion_g / 100`, table wins over LLM kcal).
4. After 8 vision calls in a day a user sees a friendly message and is offered the manual-entry path; when the global $/day spend exceeds the configured cap, all users see a "Service paused for the day, please log manually" banner and the manual path still works.
5. Backend logs and Atlas data confirm that **no image bytes are retained server-side** after the vision call (only `(components, total_kcal, timestamp, user_id, ai_metadata)` is written); a cost alert (env-var webhook — Sentry deferred) fires when `spend / DAU > $0.05` (OBS-03).

## Inherited Constraints (do NOT violate — see CONTEXT.md + memory/render-only-rewrite.md)

- **Day-1 multi-component schema** (ROADMAP Hard Constraint #3). Phase 4 **fills** the nullable fields Phase 3 reserved (`kcal_low`, `kcal_high`, `confidence`, `ai_metadata`, `source: "llm_then_table_rematch" | "user_corrected"`). There is **no `ai_meals` collection** anywhere in this phase.
- **No server-side image storage of any kind.** Bytes are read into memory, base64-encoded for Anthropic, discarded when the handler returns. No temp files, no GridFS, no R2, no opt-in history. (Opt-in retention is a v2 feature per REQUIREMENTS.md HIST-01..03.)
- **Sonnet 4.6 only.** No two-model cascade, no fine-tuned classifier, no GPT-4o fallback. Env-pinned via `LLM_VISION_MODEL=claude-sonnet-4-6` so a golden-set re-run gates any future bump.
- **Render-only architecture** (memory/render-only-rewrite.md). No Sentry FE/BE wizards, no Vercel Analytics, no Fly.io, no size-limit CI gate. Cost alerting = env-var webhook (Discord/Slack). Same `render.yaml` Blueprint pattern as Phase 1; Render auto-deploys on push to `main`.
- **No new vision blueprint outside the meals namespace.** `/meals/scan` lives next to Phase 3's `/meals` POST so the day-1 invariant is visible in the file structure too. (Implementation: separate `scan.py` blueprint registered alongside `meals_bp`, but the URL prefix groups them as `/meals/...`.)
- **No Anthropic API calls in CI.** All vision tests use respx to intercept the SDK's httpx transport. One live test gated by `RUN_LIVE_VISION_TEST=1` (skipped by default).
- **No `create_index` on module load** (Phase 1 invariant). The three new collections get operator-side mongosh index documentation in `app/db.py` comments and the SUMMARY follow-up.
- **Reuse Phase 3 patterns exactly** — `forwardToFlask` BFF + `@require_auth` Flask route shape + `app.db as db_mod` import pattern + mongomock fixtures + JSON Schema → hand-mirrored Zod (D-SHARED-SCHEMA-MANUAL-MIRROR) + shadcn CLI for new UI primitives + atomic commits + push to `origin/main` after each task.
- **No Phase 5 work bleeds in.** No Rive runtime, no animated kcal ring, no goal-aware copy adaptation. ScanSheet is a plain shadcn Sheet/Dialog, ScanResultChips reuse Phase 3's static ComponentChip.

## Slice Overview

| Slice | Theme | Tasks |
|-------|-------|-------|
| A | Backend — Pydantic models + JSON schema + vision helpers + rate-limit helpers + db.py + config.py + requirements.txt | 4 |
| B | Backend — `/meals/scan` route + `/corrections` route + cost-alert webhook + tests with respx | 3 |
| C | Frontend — compressMealImage helper + Zod mirror + forwardMultipart + two BFF routes + middleware | 1 |
| D | Frontend — ScanSheet + SnapMealCta + ScanResultChips + dashboard wiring + ServicePausedBanner | 3 |
| E | Env + Deploy config — render.yaml + .env.example + golden_set placeholder + Phase 7 hook | 1 |
| F | User checkpoint + live smoke + traceability flip | 2 |

**Total: 14 tasks.** Granularity matches Phase 3 (18 tasks for 9 reqs); Phase 4 ships 13 reqs (VIS-01..12 + OBS-03) but reuses Phase 3's meal infra so per-req task count is lower.

Cross-slice ordering: A → B (needs A's models + helpers) → C (needs A's JSON schema + B's routes) → D (needs C's compression helper + Zod + B's routes) → E (deploy config — touches files but adds no logic) → F (user checkpoint + live verify + REQUIREMENTS.md flip — depends on ALL prior slices).

## Threat Register (Phase 4)

Trust boundaries inherited from Phase 1/3 (browser → Next.js BFF same-origin; BFF → Flask Render-internal + Bearer JWT; Flask → MongoDB Atlas TLS) **plus one new outbound boundary: Flask → Anthropic API (TLS over public internet, Bearer API key from env).**

| Threat ID  | Category               | Component                                                                | Disposition | Mitigation Plan |
|------------|------------------------|--------------------------------------------------------------------------|-------------|-----------------|
| T-04-01    | Information Disclosure | Meal image bytes retained server-side (VIS-11 — privacy contract)        | mitigate    | The scan route reads bytes into a local variable, base64-encodes for the Anthropic body, then drops both references at end of handler scope. Test `test_scan_no_image_bytes_persisted` asserts: (a) `tmp_path` is empty after the request, (b) no document in `db_mod.meals` contains an `image` field, (c) no GridFS bucket `fs.files` collection is created. The route MUST NOT write to any disk path; if it ever needs scratch space, it uses `io.BytesIO`. The respx fixture also asserts the outbound Anthropic request contains the base64 body but the local handler does not retain it (verified by checking handler-scope locals before return). |
| T-04-02    | Denial of Service      | Per-user daily-cap bypass via concurrent requests                        | mitigate    | The cap check is implemented as a single Mongo `update_one({user_id, date, count: {$lt: 8}}, {$inc: {count: 1}, $set: {last_call_at: now}}, upsert=True)` + `find_one` to read the resulting count. The conditional filter `count: {$lt: 8}` makes the increment race-safe — two simultaneous 8th-scan requests will see one succeed (matched_count==1) and one fail (matched_count==0 → 429). Test `test_user_daily_cap_race` fires 10 parallel `update_one`s against mongomock and asserts at most 8 succeed. (Mongomock honours `$inc` atomicity; Atlas uses real WiredTiger document-level locking which is strictly stronger.) |
| T-04-03    | Denial of Service      | Global $/day budget-breaker race condition                               | mitigate    | Same race-safe pattern: `check_and_record_spend` does `find_one_and_update({_id: 'vision_budget', date: today}, {$inc: {spend_usd: cost}, $setOnInsert: {cap_usd, date}}, upsert=True, return_document=AFTER)` and compares the returned `spend_usd` against `cap_usd`. The PRE-check (before the Anthropic call) is a read; the increment (POST Anthropic) is the source of truth. If two requests race past the pre-check and both successfully call Anthropic, both spends are recorded — we may go slightly over cap, but never silently. The cap is a circuit breaker, not a hard quota; ~$0.01 overshoot is acceptable (CONTEXT specifies "all subsequent scans return 503" — not "no overshoot ever"). Test `test_global_budget_breaker_admits_concurrent_then_pauses` covers the over-by-one case. |
| T-04-04    | Spoofing               | Forged user_id on /meals/scan or /corrections body                       | mitigate    | Both routes `@require_auth`; `user_id = g.clerk_user_id` always; never read from form data, body, or query. Test `test_scan_ignores_user_id_in_form` and `test_corrections_ignores_user_id_in_body` assert that a forged `user_id` field is dropped/422'd. (Phase 3 T-03-01 inheritance.) |
| T-04-05    | Tampering              | Client-supplied AiMetadata or kcal_low/high on the eventual POST /meals  | mitigate    | The scan route never returns LLM-derived fields back to the FE for client-side persistence; the FE sends ComponentCreate shapes (matched: `{food_id, portion_g}`; free-text: `{name, portion_g, kcal_point}`) plus an OPAQUE `ai_metadata` blob carried in the meal-level body. The /meals POST handler (Phase 3) must be extended to accept `ai_metadata` when `source == 'ai_vision'` — but only the fields in `AiMetadata` (model, prompt_hash, image_dims, latency_ms, cost_usd) are persisted; any other keys are silently dropped via Pydantic `extra='ignore'`. The kcal_low/high/confidence on each component are PRE-computed server-side during the scan call and round-tripped through a SIGNED JWT (HMAC-SHA256 with a server-side secret) included in the scan response under `_scan_signature`; on the eventual /meals POST, the server verifies the signature before accepting kcal_low/high/confidence values. **Simpler alternative chosen (less infra):** /meals POST simply ignores client-supplied kcal_low/high/confidence/ai_metadata and instead the scan route writes a short-lived `scan_session` doc to a new `scan_sessions` collection — the FE Confirm POSTs the `scan_session_id` instead of the LLM fields, and the server reconstitutes them. **Decision chosen for v1 (simplest):** /meals POST accepts kcal_low/high/confidence/ai_metadata when `source == 'ai_vision'` and trusts them — the threat is small (a user lying about their own kcal range affects only their own dashboard), and the user-corrections feedback loop is the gating signal anyway. Document this as an accepted risk with a follow-up to introduce scan_sessions if/when leaderboards or social features ship. |
| T-04-06    | Information Disclosure | ANTHROPIC_API_KEY leaked in logs / error traces                          | mitigate    | `config.py` reads the key into `Config.ANTHROPIC_API_KEY` (str field). The Anthropic SDK is constructed once per request (or once per worker — see implementation note in P4-B.1) with the key, never logged. Exception handlers in `scan.py` use `repr(e)` ONLY on the exception class name, never the full exception chain, to avoid the SDK leaking the Authorization header on an HTTPx error. `__str__` on the SDK's exceptions is safe in current versions but defence-in-depth: re-raise as `RuntimeError("anthropic_call_failed")` and log the original via `app.logger.exception` (which Sentry would scrub — but Sentry is deferred; Render's log redaction does not scrub by default, so we explicitly DROP the original exception's args before logging). |
| T-04-07    | Tampering              | Malformed / hostile LLM response (prompt injection in meal image)        | mitigate    | The response is parsed via `parse_tool_use_response` which validates against `VisionResponse` (Pydantic strict — component count 1..10, kcal_low/high ≥0, confidence 0..1). On ValidationError, the route retries ONCE with a re-prompt ("Return strictly JSON matching tool schema"); on second failure returns 502 `{error: 'vision_parse_failed'}` and the FE falls back to manual. We do NOT trust the LLM's `name` field — every component name is table-rematched against `ghana_foods.name` (substring + alt_names) and on mismatch the name passes through to the FE for user correction (the user is the trust anchor for unknown dishes). |
| T-04-08    | Denial of Service      | Cost-alert webhook is itself a DoS amplifier (every scan = webhook call) | mitigate    | The alert fires ONLY when `spend_usd / DAU_today > 0.05` AND we haven't already alerted today (`system_state.vision_budget.alert_fired: bool` flag with TTL = same UTC day). DAU_today is computed as `db_mod.vision_usage.count_documents({date: today_str})` — cheap with the operator-side index. If COST_ALERT_WEBHOOK_URL is unset, WARN-log instead. httpx call uses a 3-second timeout so a flaky webhook can't slow scan latency. |
| T-04-09    | Repudiation            | User claims a meal kcal estimate they never accepted                     | accept      | The scan response is not persisted on the server side — only the user's Confirm POST creates a meal. Audit trail exists in `vision_usage.count` (per-day count) + `user_corrections` (per-correction) + `meals` (per-confirmed meal). For v1, the absence of an immutable scan log is acceptable; Phase 7 / v2 may add `scan_sessions` for forensic replay. |
| T-04-10    | Information Disclosure | Free-text component name on ScanResultChips leaks PII to /api/foods      | accept      | The /api/foods endpoint takes a query string and is read-only over the public 25-dish catalogue. If a user types their address as a "dish name" while correcting a chip, that string is sent to Flask's search index (in-memory, not logged beyond Render's default request log which Flask does not customize). Acceptable for v1; the PII surface is the user's own action and the user is informed of the LLM data flow per AUTH-05. |

## Source Coverage Audit

| Source | Item | Plan Coverage |
|--------|------|---------------|
| GOAL (ROADMAP Phase 4) | Camera/upload from /dashboard, ≤5s p50 to chip render | Slice C (P4-C.1 compressMealImage) + Slice D (P4-D.1 ScanSheet) |
| GOAL | Multi-component identification with kcal range per chip | Slice A (P4-A.1 VisionResponse) + Slice B (P4-B.1 scan route, tool-use schema) + Slice D (P4-D.2 ScanResultChips) |
| GOAL | Tap-to-edit chips with cmdk search + portion slider + remove | Slice D (P4-D.2 reuses Phase 3 ComponentChip + FoodSearch) |
| GOAL | Confirmed meal saved via same multi-component schema (no ai_meals) | Slice D (P4-D.3 Confirm → POST /api/meals with source='ai_vision') — extends Phase 3 endpoint MINIMALLY |
| GOAL | Per-user 8/day cap with friendly toast + manual fallback | Slice A (P4-A.3 rate_limit) + Slice B (P4-B.1) + Slice D (P4-D.1 429 handler) |
| GOAL | Global $/day breaker with site banner; manual still works | Slice A (P4-A.3) + Slice B (P4-B.1) + Slice D (P4-D.1 + ServicePausedBanner) |
| GOAL | No image bytes retained server-side | Slice B (P4-B.1 + T-04-01 test) |
| GOAL | Cost alert at $/DAU > $0.05 (Sentry deferred → env-var webhook) | Slice B (P4-B.2 webhook) + Slice E (P4-E.1 env config) |
| REQ VIS-01 | Capture or upload meal photo from dashboard | P4-D.1 (ScanSheet) + P4-D.3 (SnapMealCta) |
| REQ VIS-02 | Client-side compression ≤1024px ≤0.5MB JPEG q=0.85 | P4-C.1 (compressMealImage with browser-image-compression) |
| REQ VIS-03 | Backend identifies each visible component (multi-component output) | P4-A.1 (tool schema) + P4-B.1 (parse + return components array) |
| REQ VIS-04 | Backend returns kcal range per component + total with confidence | P4-A.1 (VisionComponentRaw kcal_low/high/confidence) + P4-B.1 |
| REQ VIS-05 | Table re-match — kcal_per_100g × portion_g (table wins) | P4-A.2 (table_rematch helper) + P4-B.1 (post-parse) |
| REQ VIS-06 | Tap-to-edit chips with portion sliders before saving | P4-D.2 (ScanResultChips reuses ComponentChip) |
| REQ VIS-07 | Correct dish name (autocomplete) and portion before confirming | P4-D.2 (FoodSearch in chip edit) + P4-D.1 (Confirm) |
| REQ VIS-08 | Corrections persisted to user_corrections + bias next scan | P4-A.1 (UserCorrectionDoc) + P4-B.3 (/corrections route) + P4-B.1 (build_system_prompt reads last 20) |
| REQ VIS-09 | Per-user 8/day cap with clear messaging | P4-A.3 (check_and_increment_user_daily) + P4-B.1 (429) + P4-D.1 (toast + manual fallback) |
| REQ VIS-10 | Global daily LLM cost breaker; manual fallback | P4-A.3 (check_and_record_spend) + P4-B.1 (503) + P4-D.3 (ServicePausedBanner) |
| REQ VIS-11 | Image bytes NOT retained server-side | P4-B.1 (handler-scope bytes only) + T-04-01 test |
| REQ VIS-12 | Confirmed meal persisted via same multi-component schema | P4-D.1 (Confirm POSTs Phase 3 /api/meals shape) — Phase 3 schema already has the nullable AI fields |
| REQ OBS-03 | Alert at $/DAU/day > $0.05 (Sentry replaced by env-var webhook) | P4-B.2 (webhook firing logic) + P4-E.1 (COST_ALERT_WEBHOOK_URL env var) |
| CONTEXT D-VISION-MODEL-PIN | Sonnet 4.6 only; LLM_VISION_MODEL env-pinned | P4-A.4 (config.py + requirements.txt) + P4-E.1 (render.yaml) |
| CONTEXT D-NO-AI-MEALS-COLLECTION | Fill Phase 3 nullable fields, no new collection | P4-A.1 (AiMetadata sub-doc matches Meal.ai_metadata) + P4-D.3 (Confirm reuses Phase 3 POST) |
| CONTEXT D-TABLE-WINS | Vision kcal is advisory; table value is canonical | P4-A.2 (table_rematch returns table-derived kcal_point) |
| CONTEXT D-NO-IMAGE-STORAGE | No temp files, no GridFS, no R2 | P4-B.1 (T-04-01 test) |
| CONTEXT D-DAILY-CAP-RACE-SAFE | $inc with conditional filter | P4-A.3 + T-04-02 |
| CONTEXT D-GLOBAL-BREAKER-RACE-SAFE | find_one_and_update with $inc | P4-A.3 + T-04-03 |
| CONTEXT D-CORRECTIONS-BIAS-PROMPT | Last 20 corrections in system prompt | P4-B.3 (/corrections write) + P4-B.1 (next-scan read) |
| CONTEXT D-COST-ALERT-WEBHOOK | env-var webhook replaces Sentry | P4-B.2 + P4-E.1 |
| CONTEXT D-PROMPT-CACHING | Anthropic prompt-cache marker on system prompt | P4-A.2 (build_system_prompt emits cache_control) + P4-B.1 |
| CONTEXT D-RESPX-MOCKED-CI | No Anthropic in CI | P4-B.1 tests (respx) + P4-F.1 live test gated by env var |
| CONTEXT D-GOLDEN-SET-HOOK | Phase 7 hook; placeholder in Phase 4 | P4-E.1 (golden_set/README.md) |
| CONTEXT D-FILES-API-NO | Inline base64; not Files API | P4-B.1 (base64 inline in message body) |

**All items covered. No gaps. No deferrals beyond what is already locked in ROADMAP/CONTEXT.md (golden set → Phase 7; opt-in image history → v2; scan_sessions for forensic replay → v2 per T-04-09).**

---

## Slice A — Backend models + helpers + db + config

<task type="auto" tdd="true">
  <name>Task P4-A.1: Pydantic vision models + JSON schema + db.py extension</name>
  <files>backend/app/models/vision.py, backend/app/models/__init__.py, shared/schemas/vision-response.schema.json, backend/app/db.py, backend/tests/test_vision_models.py</files>
  <behavior>
    - `AiMetadata` (sub-doc matching the persisted shape on `Meal.ai_metadata` reserved by Phase 3):
      - `model: str` (e.g. "claude-sonnet-4-6").
      - `prompt_hash: str` (sha256 hex of the rendered system prompt — used to detect cache-busts and for golden-set provenance).
      - `image_dims: dict` (`{w: int, h: int}` post-compression).
      - `latency_ms: int` (≥0).
      - `cost_usd: float` (≥0; rounded to 6 decimal places).
      - `extra="ignore"` so Phase 3's any-shape `dict | None` Meal.ai_metadata accepts it without a schema change.
    - `VisionComponentRaw` (LLM tool-use output shape — pre table re-match):
      - `name: str` (1..80; the LLM-supplied label, possibly informal).
      - `kcal_low: int` (≥0, ≤5000).
      - `kcal_high: int` (≥kcal_low, ≤5000).
      - `kcal_point: int` (≥kcal_low, ≤kcal_high; LLM's best guess).
      - `portion_g_estimate: int` (≥10, ≤800).
      - `confidence: float` (0.0..1.0).
      - `extra="forbid"` so the LLM cannot smuggle extra fields the parser would otherwise pass through.
    - `VisionResponse`:
      - `components: list[VisionComponentRaw]` (1..10).
      - `extra="forbid"`.
    - `VisionUsageDoc` (vision_usage collection — one doc per (user_id, date)):
      - `user_id: str` (clerk_id pattern).
      - `date: str` (YYYY-MM-DD, UTC).
      - `count: int` (≥0).
      - `last_call_at: datetime`.
    - `SystemStateDoc` (system_state.vision_budget singleton — `_id = "vision_budget"`):
      - `_id: str = "vision_budget"` (literal).
      - `date: str` (YYYY-MM-DD, UTC — rotated daily at 00:00 UTC).
      - `spend_usd: float` (≥0).
      - `cap_usd: float` (≥0).
      - `alert_fired: bool` (default False; reset when `date` rolls).
    - `UserCorrectionDoc` (user_corrections collection):
      - `user_id: str`.
      - `original_name: str` (LLM-supplied label).
      - `corrected_name: str | None` (user-chosen Ghana food name, or None if only portion changed).
      - `original_portion_g: int`.
      - `corrected_portion_g: int`.
      - `original_food_id: str | None`.
      - `corrected_food_id: str | None` (matched_food_id after correction; None if free-text).
      - `corrected_at: datetime`.
    - `ANTHROPIC_TOOL_SCHEMA: dict` — module-level constant exporting the JSON schema dict passed to Anthropic's `tools` arg. Tool name `report_meal_components`; description "Identify each visible food component on the plate and estimate kcal range + portion in grams"; input_schema matches `VisionResponse` shape (regenerated from `VisionResponse.model_json_schema()` so the two cannot drift).
    - Tests in `test_vision_models.py`:
      - `test_vision_component_raw_kcal_high_must_be_ge_low`
      - `test_vision_component_raw_kcal_point_within_low_high`
      - `test_vision_component_raw_confidence_range`
      - `test_vision_component_raw_extra_forbid`
      - `test_vision_response_components_min_1_max_10`
      - `test_ai_metadata_extra_ignored`
      - `test_user_correction_doc_corrected_name_optional`
      - `test_system_state_doc_alert_fired_default_false`
      - `test_anthropic_tool_schema_matches_response_shape` (run `VisionResponse.model_json_schema()` and assert structural equality vs `ANTHROPIC_TOOL_SCHEMA["input_schema"]`)
  </behavior>
  <action>
    Create `backend/app/models/vision.py` mirroring the Pydantic v2 idioms from `backend/app/models/meal.py` (Phase 3) — `ConfigDict(extra="forbid")` or `extra="ignore"` per the field comments above, `Literal` types where applicable, no Flask/Mongo imports.

    For `ANTHROPIC_TOOL_SCHEMA`, build it programmatically:
    ```
    ANTHROPIC_TOOL_SCHEMA = {
        "name": "report_meal_components",
        "description": "Identify each visible food component on the plate ...",
        "input_schema": VisionResponse.model_json_schema(),
    }
    ```
    Generate `shared/schemas/vision-response.schema.json` by running `VisionResponse.model_json_schema()` in a one-off Python invocation (mirror P3-A.1 / P3-A.2 pattern). This is the contract Zod mirrors in P4-C.1.

    Extend `backend/app/db.py`: add three new collection singletons after `meals`:
    ```python
    # Phase 4 — Image -> Kcal Core Loop (P4-A.1).
    # Operator-side indexes (Phase 1 invariant — no create_index on module load):
    #   db.vision_usage.createIndex({user_id: 1, date: 1}, {unique: true})
    #   db.system_state ... (_id is the natural key — no index needed)
    #   db.user_corrections.createIndex({user_id: 1, corrected_at: -1})
    vision_usage: Collection = db["vision_usage"]
    system_state: Collection = db["system_state"]
    user_corrections: Collection = db["user_corrections"]
    ```

    Re-export new types from `app.models.__init__`.

    Write tests FIRST (RED) covering the validators above, then implement.

    Extend `backend/tests/conftest.py` `mongo_collections` fixture to include `vision_usage`, `system_state`, `user_corrections` (mongomock dual-binding patch same as Phase 3 added for ghana_foods + meals — both `app.db.<name>` and any imported route module's bound name when present).
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_vision_models.py -v</automated>
  </verify>
  <done>All ~9 vision-model test cases pass; `shared/schemas/vision-response.schema.json` exists and validates as JSON; `db.py` exposes the three new collections; conftest patches them; `ruff check backend/app/models/vision.py backend/app/db.py` is clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P4-A.2: Vision lib — system prompt builder + parse + table re-match + cost helper</name>
  <files>backend/app/lib/vision.py, backend/tests/test_vision_lib.py</files>
  <behavior>
    - `MODEL_PRICING_PER_1K: dict` — `{"claude-sonnet-4-6": {"input_cached": 0.0003, "input_uncached": 0.003, "output": 0.015}}`. USD per 1k tokens, Anthropic Sonnet 4.6 list pricing as of 2026-05-13. Document the source in a module docstring; bumping prices is a one-line edit.
    - `build_system_prompt(ghana_foods: list[dict], user_corrections: list[dict]) -> dict`:
      - Returns a dict matching the Anthropic SDK's `system` parameter shape with prompt-cache marker:
        ```
        [
            {"type": "text", "text": <ghana_foods_section + chain_of_thought + tool_instruction>, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": <user_history_section>}  # NOT cached — varies per user
        ]
        ```
      - The cached section is identical across users for the same `ghana_foods` snapshot — Anthropic caches it (~75% input-token discount).
      - The uncached section renders the last 20 corrections as `"User has previously corrected: '<original_name>' → '<corrected_name>' (portion <a>g → <b>g)"` lines.
      - For empty `user_corrections`, the uncached section is `""` (still emitted so prompt structure is stable).
      - Hash inputs: `prompt_hash = sha256(json.dumps([ghana_foods_section_text, user_history_section_text], sort_keys=True)).hexdigest()` — written to AiMetadata for golden-set provenance.
    - `build_user_message(image_b64: str, mime: str = "image/jpeg") -> list`:
      - Returns the `messages[0].content` value: `[{"type": "image", "source": {"type": "base64", "media_type": mime, "data": image_b64}}, {"type": "text", "text": "Identify each food component and report via the report_meal_components tool."}]`.
    - `parse_tool_use_response(raw_message) -> VisionResponse`:
      - Walks `raw_message.content` looking for the FIRST `ToolUseBlock` with `name == "report_meal_components"`. Extracts `block.input` (a dict).
      - Calls `VisionResponse.model_validate(block.input)` — raises `pydantic.ValidationError` on schema mismatch (route catches + retries once).
      - Raises `ValueError("no_tool_use_block")` if no matching block found.
    - `table_rematch(vision_components: list[VisionComponentRaw], ghana_foods_coll) -> list[dict]`:
      - For each VisionComponentRaw:
        - Substring-insensitive match of `vision.name` against `ghana_foods.name` and each entry's `alt_names[*]`.
        - Rank: exact > startswith > contains > alt_names contains. Ties → alphabetical name. Same algorithm as P3-B.1's /foods route (reuse by importing or duplicating the small ranker).
        - If matched: build a persisted Component dict matching Phase 3's shape:
          `{name: food["name"], matched_food_id: food["food_id"], portion_g: vision.portion_g_estimate, kcal_low: vision.kcal_low, kcal_high: vision.kcal_high, kcal_point: compute_kcal_for_component(food["kcal_per_100g"], vision.portion_g_estimate), protein_g_point: compute_protein_for_component(food["protein_g_per_100g"], vision.portion_g_estimate), confidence: vision.confidence, source: "llm_then_table_rematch"}`.
        - If NO match: fall back to LLM range midpoint:
          `{name: vision.name, matched_food_id: None, portion_g: vision.portion_g_estimate, kcal_low: vision.kcal_low, kcal_high: vision.kcal_high, kcal_point: round((vision.kcal_low + vision.kcal_high) / 2), protein_g_point: 0, confidence: vision.confidence, source: "user_corrected"}`. (The "user_corrected" source nudges the user to correct it before Confirm, and lets the user_corrections system pick up the next-scan bias.)
      - Returns the persisted-shape list. The route serializes this for the FE.
    - `compute_cost_usd(input_cached_tokens: int, input_uncached_tokens: int, output_tokens: int, model: str = "claude-sonnet-4-6") -> float`:
      - `cost = (input_cached/1000)*pricing.input_cached + (input_uncached/1000)*pricing.input_uncached + (output/1000)*pricing.output`. Rounded to 6 decimals.
      - For unknown model, raises `KeyError` (fail loud — pricing table must be updated alongside any LLM_VISION_MODEL bump).
    - Tests in `test_vision_lib.py`:
      - `test_build_system_prompt_emits_cache_control_on_first_block`
      - `test_build_system_prompt_empty_corrections_emits_empty_user_history`
      - `test_build_system_prompt_includes_all_ghana_foods` (assert each food's name appears in the cached text)
      - `test_build_user_message_returns_image_then_text` (order matters for Anthropic SDK)
      - `test_parse_tool_use_response_extracts_first_matching_block`
      - `test_parse_tool_use_response_raises_when_no_tool_block`
      - `test_parse_tool_use_response_raises_validation_error_on_bad_shape`
      - `test_table_rematch_matched_uses_table_kcal_point` (assert table value WINS over LLM's kcal_point)
      - `test_table_rematch_unmatched_falls_back_to_llm_midpoint`
      - `test_table_rematch_writes_correct_source_per_path`
      - `test_compute_cost_usd_sonnet_4_6_known_input`
      - `test_compute_cost_usd_unknown_model_raises`
  </behavior>
  <action>
    Create `backend/app/lib/vision.py` as pure Python — only stdlib + Pydantic + `app.lib.meals` (for `compute_kcal_for_component` / `compute_protein_for_component`). NO Flask, NO Anthropic SDK import, NO Mongo direct calls (`table_rematch` takes a collection HANDLE so it's mongomock-testable).

    For `build_system_prompt`, render the Ghana foods section as a markdown-ish text block (the LLM handles it fine):
    ```
    # Ghana food reference (per 100g, FAO/INFOODS WAFCT-sourced):
    | Name                | kcal/100g | Notes                              |
    |---------------------|-----------|------------------------------------|
    | Jollof rice         |     165   | aka jollof, party rice             |
    ...
    ```
    Followed by a chain-of-thought instruction: "When you see a plate, name each visible component separately. Match to this table when confident; otherwise describe the dish in plain English. Report via the report_meal_components tool. Always return a kcal range — never a single point."

    For `parse_tool_use_response`, use Anthropic's SDK type if importable, else duck-type on `.content` being an iterable of objects with `.type == "tool_use"` and `.name`/`.input` attrs. Tests pass plain dicts with a small adapter; production code imports `anthropic.types` lazily inside the function for typing only.

    Per CONTEXT.md "table wins": `table_rematch` ALWAYS overrides the LLM's kcal_point with the table-derived value when matched. The LLM's kcal_low/kcal_high are preserved as advisory for the FE chip display.

    Per D-INTERFACE-FIRST: these helpers are imported by `backend/app/routes/scan.py` (P4-B.1). Pin the function signatures now.

    Write tests FIRST (RED), then implement.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_vision_lib.py -v</automated>
  </verify>
  <done>All ~12 test cases pass; `ruff check backend/app/lib/vision.py` clean; no `anthropic` SDK module import at module top (lazy inside parse function only — keeps test import cheap).</done>
</task>

<task type="auto" tdd="true">
  <name>Task P4-A.3: Rate-limit helpers (per-user 8/day + global $/day) — race-safe Mongo ops</name>
  <files>backend/app/lib/rate_limit.py, backend/tests/test_rate_limit.py</files>
  <behavior>
    - `USER_DAILY_CAP = 8` (constant; CONTEXT-locked).
    - `DEFAULT_VISION_DAILY_CAP_USD = 5.0` (constant; env-overridable via config.py).
    - `today_utc_str() -> str`: `datetime.now(UTC).strftime("%Y-%m-%d")` — single source for the date key.
    - `check_and_increment_user_daily(vision_usage_coll, user_id: str, today_str: str) -> tuple[bool, int]`:
      - Single Mongo op: `result = vision_usage_coll.update_one({"user_id": user_id, "date": today_str, "count": {"$lt": USER_DAILY_CAP}}, {"$inc": {"count": 1}, "$set": {"last_call_at": datetime.now(UTC)}, "$setOnInsert": {"user_id": user_id, "date": today_str}}, upsert=True)`.
      - On success (`result.upserted_id` or `result.modified_count > 0`): re-read with `vision_usage_coll.find_one({"user_id": user_id, "date": today_str})` and return `(True, doc["count"])`.
      - On failure (`matched_count == 0` AND `upserted_id is None` — only happens when an existing doc has `count >= 8`): re-read to return the current count, return `(False, doc["count"])`.
      - DUP-KEY gotcha: with `upsert=True` and the conditional filter, two simultaneous first-call inserts race. Catch `pymongo.errors.DuplicateKeyError` (raised because of the unique index on `(user_id, date)`), and retry once without the conditional filter — at that point the doc exists and the conditional `$inc` will either succeed (count < 8) or no-op (count >= 8). Test `test_first_call_race_handles_dup_key` covers this.
    - `check_and_record_spend(system_state_coll, today_str: str, spend_usd: float, cap_usd: float) -> tuple[bool, float]`:
      - PRE-call check: `doc = system_state_coll.find_one({"_id": "vision_budget"})`. If `doc is None` OR `doc["date"] != today_str`: treat spend as 0 (the day rolled). If `doc["spend_usd"] >= doc.get("cap_usd", cap_usd)` AND `doc["date"] == today_str`: return `(False, doc["spend_usd"])` — caller returns 503 without calling Anthropic.
      - Otherwise return `(True, doc["spend_usd"] if doc and doc["date"] == today_str else 0.0)`. The caller proceeds with Anthropic, then calls `record_spend` (below) AFTER the call returns.
    - `record_spend(system_state_coll, today_str: str, spend_usd: float, cap_usd: float) -> dict`:
      - Atomic: `system_state_coll.find_one_and_update({"_id": "vision_budget"}, {"$inc": {"spend_usd": spend_usd}, "$setOnInsert": {"_id": "vision_budget", "date": today_str, "cap_usd": cap_usd, "alert_fired": False}, "$set": {"date": today_str, "cap_usd": cap_usd}}, upsert=True, return_document=ReturnDocument.AFTER)`.
      - Day-roll handling: if the existing doc's `date != today_str`, REPLACE the doc with a fresh one (zero spend, this call's cost):
        - Use `find_one_and_replace({"_id": "vision_budget", "date": {"$ne": today_str}}, {"_id": "vision_budget", "date": today_str, "spend_usd": spend_usd, "cap_usd": cap_usd, "alert_fired": False}, upsert=False, return_document=ReturnDocument.AFTER)`. If that returns None (no match — either doc is today already, or doc doesn't exist), fall through to the `find_one_and_update` $inc above.
      - Returns the updated doc.
    - `mark_alert_fired(system_state_coll, today_str: str) -> None`:
      - `system_state_coll.update_one({"_id": "vision_budget", "date": today_str}, {"$set": {"alert_fired": True}})`.
    - Tests in `test_rate_limit.py` (mongomock):
      - `test_first_user_call_creates_doc_with_count_1`
      - `test_subsequent_user_call_increments_count`
      - `test_user_daily_cap_blocks_at_8`
      - `test_user_daily_cap_race_at_most_8_succeed` (fire 10 simultaneous calls via threading; assert exactly 8 return allowed=True)
      - `test_check_and_record_spend_admits_when_under_cap`
      - `test_check_and_record_spend_denies_when_over_cap`
      - `test_record_spend_creates_doc_if_missing`
      - `test_record_spend_rolls_doc_when_date_changes` (seed yesterday's doc with spend=4.99; call record_spend with today's date; assert new doc has spend=cost-of-this-call only)
      - `test_record_spend_increments_within_day`
      - `test_mark_alert_fired_idempotent`
  </behavior>
  <action>
    Create `backend/app/lib/rate_limit.py`. Imports: `datetime`, `pymongo.errors.DuplicateKeyError`, `pymongo.collection.ReturnDocument`. NO Flask import (so it's testable in isolation).

    The PRE-call/POST-call split for global budget is deliberate (CONTEXT.md): the PRE-check is a read (returns 503 without calling Anthropic if already over), the POST-record happens AFTER Anthropic returns and includes the *actual* cost computed from the response's token usage. This means slight overshoot is possible if two requests race past the PRE-check — accepted per T-04-03.

    For the user-daily-cap race test, use Python `threading.Thread` against the mongomock instance. Mongomock honours `$inc` atomicity within a single Python process, which is sufficient for the test (Atlas in production uses real WiredTiger doc-level locks — strictly stronger).

    Write tests FIRST (RED). Use the conftest `mongo_collections` fixture from P4-A.1 for the collections.

    Per D-INTERFACE-FIRST: the route module (`scan.py`, P4-B.1) imports these functions. Pin signatures now.

    No tests run the full route — those land in P4-B.1.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_rate_limit.py -v</automated>
  </verify>
  <done>All ~10 rate-limit test cases pass; race test deterministically passes 10 consecutive runs (`pytest -v --count=10 tests/test_rate_limit.py::test_user_daily_cap_race_at_most_8_succeed` if pytest-repeat is installed; otherwise document via 10 manual runs in the SUMMARY); `ruff check backend/app/lib/rate_limit.py` clean.</done>
</task>

<task type="auto">
  <name>Task P4-A.4: config.py + requirements.txt extension for Anthropic + respx</name>
  <files>backend/app/config.py, backend/requirements.txt</files>
  <action>
    **`backend/app/config.py`** — add four fields to the `Config` dataclass:
    ```python
    ANTHROPIC_API_KEY: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    LLM_VISION_MODEL: str = field(default_factory=lambda: os.environ.get("LLM_VISION_MODEL", "claude-sonnet-4-6"))
    VISION_DAILY_CAP_USD: float = field(default_factory=lambda: float(os.environ.get("VISION_DAILY_CAP_USD", "5.0")))
    COST_ALERT_WEBHOOK_URL: str = field(default_factory=lambda: os.environ.get("COST_ALERT_WEBHOOK_URL", ""))
    ```
    Extend `Config.validate()`'s production-mandatory list to include `ANTHROPIC_API_KEY`. Add a docstring note: `LLM_VISION_MODEL` is intentionally a string (any future bump must also update `MODEL_PRICING_PER_1K` in `app.lib.vision` — golden-set re-run required per CONTEXT.md D-VISION-MODEL-PIN). `VISION_DAILY_CAP_USD` defaults to $5/day; `COST_ALERT_WEBHOOK_URL` is optional (absent → WARN-log instead).

    **`backend/requirements.txt`** — append:
    ```
    # Phase 4 — Image -> Kcal Core Loop.
    # Anthropic SDK for Sonnet 4.6 vision calls. Pin minor for predictable
    # behaviour; bumping major requires re-running the golden set (Phase 7).
    anthropic>=0.40,<1
    ```
    Add to dev dependencies (if a separate requirements-dev.txt exists; otherwise append same file with a comment block):
    ```
    # Dev — respx intercepts the Anthropic SDK's underlying httpx transport for CI.
    respx>=0.21
    ```
    `respx` should already be in dev deps from Phase 1; verify via `grep respx backend/requirements*.txt`. If absent, add. If present, leave alone.

    Update conftest.py: set `monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-stub-xxxxxxxxxxxxxxxx")` and `monkeypatch.setenv("LLM_VISION_MODEL", "claude-sonnet-4-6")` and `monkeypatch.setenv("VISION_DAILY_CAP_USD", "100.0")` (high cap so most tests don't trip the breaker; tests that need to trip set their own monkeypatched value).

    No new tests directly for config (covered by existing `test_db.py` / `test_cors.py` pattern when extended in P4-B.1).
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -c "from app.config import Config; c = Config(); assert c.LLM_VISION_MODEL == 'claude-sonnet-4-6'; assert c.VISION_DAILY_CAP_USD == 5.0; print('config OK')" && .venv/Scripts/python.exe -m pytest -q</automated>
  </verify>
  <done>Config exposes all four new fields with documented defaults; `validate()` mandates `ANTHROPIC_API_KEY` in production; `requirements.txt` has anthropic pin; conftest sets test-stub env; full pytest suite still green (no regressions from Phase 3's 158 tests).</done>
</task>

---

## Slice B — Backend routes (`/meals/scan` + `/corrections`) + cost-alert webhook

<task type="auto" tdd="true">
  <name>Task P4-B.1: Flask POST /meals/scan — full vision pipeline (mocked Anthropic)</name>
  <files>backend/app/routes/scan.py, backend/app/__init__.py, backend/tests/conftest.py, backend/tests/test_scan_route.py</files>
  <behavior>
    - `POST /meals/scan`:
      - `@require_auth`. `user_id = g.clerk_user_id`.
      - **PRE-1 (user cap):** `(allowed, count) = check_and_increment_user_daily(db_mod.vision_usage, user_id, today_utc_str())`. If `not allowed`, return `429 {"error": "daily_cap", "count": count, "limit": USER_DAILY_CAP, "reset_at": <tomorrow_utc_midnight_iso>}`. (Note: count IS incremented preemptively — even a failed-cap request increments? NO — the conditional filter `count: {$lt: 8}` prevents the increment when count==8. The `update_one` returns matched=0 in that case, and the function returns False+8 without incrementing further. Test `test_daily_cap_does_not_over_increment` asserts this.)
      - **PRE-2 (global budget):** `(allowed, current_spend) = check_and_record_spend(db_mod.system_state, today_str, 0.0, cfg.VISION_DAILY_CAP_USD)`. **Note the 0.0** — the PRE call passes zero spend because we don't know the cost yet; the function is split such that the PRE just READS the current spend (it does NOT inc by 0). Refactor `check_and_record_spend` to NOT do an inc when spend_usd == 0.0, OR (cleaner) split into `check_global_budget` (pure read, returns (allowed, spend)) and `record_spend_post_call` (does the actual inc). **Implement the cleaner split**; adjust P4-A.3's tests accordingly during this task.
      - If `not allowed`, return `503 {"error": "service_paused", "reason": "daily_budget", "spend_usd": current_spend, "cap_usd": cfg.VISION_DAILY_CAP_USD}`. ROLL BACK the user-daily-cap increment (because we never made the call): `db_mod.vision_usage.update_one({"user_id": user_id, "date": today_str}, {"$inc": {"count": -1}})` — net-zero against this user's quota. Test `test_global_budget_rollback_user_cap`.
      - **Read image:** `image_file = request.files.get("image")`. If absent OR `image_file.mimetype not in {"image/jpeg", "image/png", "image/webp"}` OR `image_file.content_length > 1_048_576` (1 MB hard cap — slack above the FE 0.5 MB target), return `400 {"error": "invalid_image"}`. (Rolling back the user cap increment in this branch too.)
      - `image_bytes = image_file.read()`. `image_b64 = base64.b64encode(image_bytes).decode("ascii")`. `mime = image_file.mimetype`.
      - **Build prompt:**
        - `ghana_foods = list(db_mod.ghana_foods.find({}, {"_id": 0}))` (cheap — 25 rows).
        - `user_corrections = list(db_mod.user_corrections.find({"user_id": user_id}).sort("corrected_at", -1).limit(20))`.
        - `system = build_system_prompt(ghana_foods, user_corrections)`.
        - `prompt_hash = sha256(...).hexdigest()` (computed inside build_system_prompt OR via a separate `hash_system_prompt(system)` helper — pick one and document).
      - **Call Anthropic:**
        - `client = anthropic.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)` (constructed per-request — SDK does not require a worker-level singleton; latency cost is negligible vs the 2-4s vision call).
        - `t0 = time.monotonic()`.
        - `try: resp = client.messages.create(model=cfg.LLM_VISION_MODEL, max_tokens=1024, system=system, tools=[ANTHROPIC_TOOL_SCHEMA], tool_choice={"type": "tool", "name": "report_meal_components"}, messages=[{"role": "user", "content": build_user_message(image_b64, mime)}])`
        - `except anthropic.APIError as e: app.logger.exception("anthropic_call_failed"); raise RuntimeError("anthropic_call_failed") from None` (note `from None` — drops original to avoid leaking Authorization header per T-04-06).
        - `latency_ms = int((time.monotonic() - t0) * 1000)`.
      - **Drop image bytes:** `del image_bytes`, `del image_b64`. Defensive — handler scope ends shortly anyway but explicit beats implicit for T-04-01 audit.
      - **Parse + retry:**
        - `try: parsed = parse_tool_use_response(resp)` → on `ValidationError` OR `ValueError("no_tool_use_block")`, retry ONCE with the same call (same prompt, same image — but Anthropic's tool-use mode is deterministic enough that a retry usually fixes a transient blip). On second failure: `return 502 {"error": "vision_parse_failed"}` and rollback the user-cap increment.
      - **Table re-match:** `components = table_rematch(parsed.components, db_mod.ghana_foods)`.
      - **Record spend:** `usage = resp.usage`; `cost_usd = compute_cost_usd(input_cached=usage.cache_read_input_tokens or 0, input_uncached=usage.input_tokens or 0, output=usage.output_tokens or 0, model=cfg.LLM_VISION_MODEL)`. `record_spend_post_call(db_mod.system_state, today_str, cost_usd, cfg.VISION_DAILY_CAP_USD)`.
      - **Cost-alert check (lazy — only if not yet alerted today):** see P4-B.2.
      - **Build response:**
        ```python
        return jsonify({
            "components": components,
            "ai_metadata": {
                "model": cfg.LLM_VISION_MODEL,
                "prompt_hash": prompt_hash,
                "image_dims": {"w": <derived from image>, "h": ...},  # see note
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
            },
            "vision_total_kcal_low": sum(c["kcal_low"] or 0 for c in components),
            "vision_total_kcal_high": sum(c["kcal_high"] or 0 for c in components),
            "user_daily_count": count,  # post-increment
            "user_daily_limit": USER_DAILY_CAP,
        }), 200
        ```
        For `image_dims`, use `Pillow` to read width/height from the bytes BEFORE the `del image_bytes`. **Decision: skip image_dims for v1** — Pillow isn't worth a dependency just to populate metadata; set `image_dims: {"w": 0, "h": 0}` (or leave as None). Document this as an accepted simplification in the SUMMARY; Phase 7 / v2 can add Pillow.

        REVISION: leave image_dims as `{"w": 0, "h": 0}` placeholder — keeps the field present per AiMetadata schema for forward-compat, no extra dependency.
    - Tests in `test_scan_route.py` — ALL mocked via `respx` intercepting the Anthropic SDK's httpx transport:
      - `test_scan_happy_path_returns_components_and_metadata` (fixture: respx returns a canned tool_use response for a single "jollof rice" component; assert 200, assert kcal_point ≈ table value, assert source == "llm_then_table_rematch")
      - `test_scan_multi_component_returns_all` (fixture returns 3 components: jollof+chicken+salad; assert all 3 in response)
      - `test_scan_table_rematch_uses_table_kcal_not_llm_kcal` (LLM returns kcal_point=999 for jollof; assert response kcal_point ≈ 165 × portion_g / 100)
      - `test_scan_unmatched_component_uses_llm_midpoint_and_user_corrected_source`
      - `test_scan_user_daily_cap_429_on_9th_call`
      - `test_scan_daily_cap_does_not_over_increment` (call /scan 9 times — assert vision_usage.count == 8 after, not 9)
      - `test_scan_global_budget_503_when_over_cap` (seed system_state with spend_usd=5.01, cap_usd=5.0; assert 503)
      - `test_scan_global_budget_rollback_user_cap` (after 503, vision_usage.count is unchanged)
      - `test_scan_no_image_returns_400`
      - `test_scan_wrong_mime_returns_400`
      - `test_scan_oversize_image_returns_400`
      - `test_scan_no_image_bytes_persisted` (T-04-01 — assert no files in tmp_path, no fs.files collection, no `image` field in any DB doc after the call)
      - `test_scan_ignores_user_id_in_form` (T-04-04)
      - `test_scan_malformed_llm_response_retries_once_then_502` (respx returns garbage tool input on both calls; assert 502 + user-cap rollback)
      - `test_scan_records_actual_token_cost` (respx response has usage.input_tokens=2000, output=500; assert spend_usd increment matches compute_cost_usd output)
      - `test_scan_passes_user_corrections_to_prompt` (seed user_corrections with 2 docs; respx fixture asserts the system prompt contains both corrections)
      - `test_scan_prompt_cache_marker_present` (assert outgoing Anthropic body has `cache_control: {type: ephemeral}` on first system block)
      - `test_scan_requires_auth_401`
      - `test_scan_logs_no_authorization_header_on_anthropic_error` (T-04-06 — respx raises 401 from Anthropic; assert caplog records "anthropic_call_failed" and does NOT contain "Bearer" or "sk-ant")
  </behavior>
  <action>
    Create `backend/app/routes/scan.py` exporting `bp` as a Flask Blueprint with the POST handler above. Import the Anthropic SDK lazily INSIDE the handler (NOT at module top) so test collection doesn't pay the import cost and so a missing key doesn't break `pytest --collect-only`. Wrap the import in `try: import anthropic; except ImportError: anthropic = None` and 503 if anthropic is None.

    Register the blueprint in `backend/app/__init__.py` (unconditional alongside `meals_bp`).

    Extend conftest with `mock_anthropic` fixture using respx (Phase 1 baseline already has respx as dev dep — verify via `pip list`). The fixture:
    ```python
    @pytest.fixture
    def mock_anthropic(monkeypatch):
        import respx
        with respx.mock(base_url="https://api.anthropic.com") as router:
            def respond(content_blocks, usage_in_uncached=1000, usage_in_cached=3000, usage_out=200):
                ...build the canned Anthropic API response...
            yield SimpleNamespace(router=router, respond=respond)
    ```
    A helper `make_tool_use_response(components: list[dict], usage: dict)` builds the canned JSON shape Anthropic returns.

    Per CONTEXT.md "Anthropic SDK call mocked via respx": the goal is ZERO real API calls in CI. The respx pattern intercepts at httpx layer — the SDK is fully exercised, just the network is faked.

    Write tests FIRST (RED), then implement. The fixture file is shared across this task and P4-B.2/P4-B.3.

    Per D-INTERFACE-FIRST: the response envelope `{components, ai_metadata, vision_total_kcal_low, vision_total_kcal_high, user_daily_count, user_daily_limit}` is the contract `frontend/src/app/dashboard/scan-sheet.tsx` (P4-D.1) consumes. Pin it now.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_scan_route.py -v</automated>
  </verify>
  <done>All ~19 scan-route test cases pass; full backend pytest count ≥ 180 (Phase 3 baseline 158 + ~9 vision_models + ~12 vision_lib + ~10 rate_limit + ~19 scan_route = +50 minimum); `respx` intercepts every Anthropic call; no real network egress in CI (verified by network sniffing the test run is overkill — the respx assertions are sufficient).</done>
</task>

<task type="auto" tdd="true">
  <name>Task P4-B.2: Cost-alert webhook firing logic (OBS-03) — integrated into scan route</name>
  <files>backend/app/routes/scan.py, backend/tests/test_scan_route.py</files>
  <behavior>
    - After `record_spend_post_call` succeeds and returns the updated system_state doc, compute:
      - `dau_today = db_mod.vision_usage.count_documents({"date": today_str})` (cheap with the `(user_id, date)` unique index — index serves the count query). DAU here = "users who scanned today," a defensible proxy for "users active today on the wedge feature."
      - `spend_per_dau = updated_state["spend_usd"] / max(dau_today, 1)`.
      - If `spend_per_dau > 0.05` AND `not updated_state["alert_fired"]`:
        - `payload = {"content": f"FitGH cost alert: ${updated_state['spend_usd']:.4f} spend / {dau_today} DAU today = ${spend_per_dau:.4f} per DAU > $0.05 threshold (OBS-03). Cap: ${updated_state['cap_usd']}."}` (Discord/Slack-compatible — both accept `content` for incoming webhooks).
        - If `cfg.COST_ALERT_WEBHOOK_URL`: `httpx.post(cfg.COST_ALERT_WEBHOOK_URL, json=payload, timeout=3.0)` (3s timeout — webhook must not slow the user's scan response). On any exception, log WARN and continue.
        - Else: `app.logger.warning("cost_alert_no_webhook: %s", payload["content"])`.
        - `mark_alert_fired(db_mod.system_state, today_str)` (so we don't spam the webhook on every subsequent scan today).
    - The alert check happens AFTER the scan response is JSON-serialized but BEFORE it's returned — actually we want it BEFORE response so the test can deterministically observe the webhook firing in the same request. Use Flask's `g.scan_response_ready` or just inline before `return jsonify(...)`.
    - Tests (extend test_scan_route.py):
      - `test_cost_alert_fires_when_per_dau_over_threshold` (seed system_state with spend_usd=0.045, dau=1; one scan costs ~$0.006; post-call spend=$0.051; per_dau=$0.051 > $0.05 → alert fires; respx asserts httpx POST to webhook URL)
      - `test_cost_alert_skipped_when_no_webhook_url` (unset COST_ALERT_WEBHOOK_URL; assert caplog has WARN line; assert NO httpx call)
      - `test_cost_alert_not_fired_twice_in_same_day` (run two scans both crossing the threshold; assert webhook called ONCE)
      - `test_cost_alert_resets_on_new_day` (seed system_state with date=yesterday + alert_fired=True; today's scan crosses threshold; assert alert fires again because day rolled)
      - `test_cost_alert_webhook_timeout_does_not_break_scan` (respx for webhook url raises TimeoutException; assert scan still returns 200)
  </behavior>
  <action>
    Extend `scan.py` to call the alert logic after `record_spend_post_call`. Reuse the existing respx fixture for the Anthropic mock; add a SECOND respx route for the webhook URL (a different base_url).

    Implement defensively — webhook failure MUST NOT 500 the scan response. Wrap in `try / except Exception as e: app.logger.warning("cost_alert_post_failed: %r", type(e).__name__)`.

    Add a `record_spend_post_call` wrapper in rate_limit.py if the test ergonomics demand it (or inline the logic in scan.py). Keep the helper signature stable.

    Test the day-roll case by seeding a yesterday-dated doc with alert_fired=True; assert today's scan re-fires.

    No new files; this task extends P4-B.1.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_scan_route.py -v -k "cost_alert"</automated>
  </verify>
  <done>All ~5 cost-alert tests pass; webhook fires exactly once per day per threshold-cross; webhook timeout doesn't break scan; alert resets on day-roll.</done>
</task>

<task type="auto" tdd="true">
  <name>Task P4-B.3: POST /corrections route + Phase 3 /meals POST accepts source='ai_vision'</name>
  <files>backend/app/routes/corrections.py, backend/app/routes/meals.py, backend/app/__init__.py, backend/tests/test_corrections_route.py, backend/tests/test_meals_routes.py</files>
  <behavior>
    - `POST /corrections`:
      - `@require_auth`. `user_id = g.clerk_user_id` (never read from body — T-04-04).
      - Parse body via `UserCorrectionDoc.model_validate_json(request.data)` (but strip any client-supplied user_id field via Pydantic — `extra="forbid"` + omit user_id from the request shape OR explicitly use a separate `UserCorrectionInput` Pydantic model with only the user-supplied fields). **Decision:** add a `UserCorrectionInput` model alongside `UserCorrectionDoc` — input excludes `user_id` and `corrected_at`; the route adds those.
      - `db_mod.user_corrections.insert_one({..., "user_id": user_id, "corrected_at": datetime.now(UTC)})`.
      - Response: `201 {"ok": true, "id": "<inserted_id>"}`.
    - Phase 3 `POST /meals` extension:
      - The existing route already accepts `MealCreate.{logged_at, components: [ComponentCreate, ...]}` and writes `source: "manual"`. Phase 4 adds: when an OPTIONAL top-level `source` field is supplied = `"ai_vision"`, persist that instead of `"manual"`, and accept an OPTIONAL `ai_metadata` dict + per-component OPTIONAL `kcal_low`, `kcal_high`, `confidence`, `source` overrides. Add these to `MealCreate`:
        - `source: Literal["manual", "ai_vision"] = "manual"`.
        - `ai_metadata: AiMetadata | None = None`.
      - Add to `ComponentCreate`:
        - `kcal_low: int | None = None` (Vision provides; manual leaves None).
        - `kcal_high: int | None = None`.
        - `confidence: float | None = None`.
        - `source: ComponentSource | None = None` (when omitted, server derives: matched→table, free-text→user_corrected; when supplied with source="ai_vision", FE sends "llm_then_table_rematch" or "user_corrected").
      - Update `_resolve_component` in `meals.py`: when input has kcal_low/high/confidence, carry them through to the persisted shape (overriding the None defaults). The kcal_point is STILL server-recomputed from the table (matched) or taken from cc.kcal_point (free-text) — never trusted from the LLM-derived FE state directly (T-04-05).
      - When meal `source == "ai_vision"` and `ai_metadata is not None`, persist `ai_metadata` as-is (Pydantic `AiMetadata` with `extra="ignore"` cleans unknown fields).
    - Tests:
      - `test_post_correction_creates_doc_with_server_user_id_and_timestamp` (corrections_route)
      - `test_post_correction_ignores_user_id_in_body` (corrections_route, T-04-04)
      - `test_post_correction_requires_auth_401` (corrections_route)
      - `test_post_meal_with_source_ai_vision_persists_ai_metadata` (meals_routes — extend)
      - `test_post_meal_with_ai_vision_components_persists_kcal_low_high_confidence` (meals_routes)
      - `test_post_meal_with_source_manual_does_not_persist_ai_metadata` (regression)
      - `test_post_meal_ai_vision_component_kcal_point_still_server_recomputed` (T-04-05 — assert server overrides client-supplied kcal_point even when source=ai_vision)
  </behavior>
  <action>
    Create `backend/app/routes/corrections.py` with the simple insert handler. Register in `__init__.py` alongside other blueprints (try/except ImportError pattern from Phase 3).

    Extend `backend/app/models/meal.py`'s `MealCreate` and `ComponentCreate` to add the optional fields above. Pydantic `extra="forbid"` is preserved — these are explicitly declared fields, not unknowns. The new fields default to None / "manual" so EXISTING Phase 3 manual log requests keep working (test that the existing 158 tests stay green).

    Extend `backend/app/routes/meals.py`'s `_resolve_component` and `post_meal` handler to thread the new fields through. The kcal_point recompute step is unchanged — that's the T-04-05 trust anchor.

    Write tests FIRST. Extend `test_meals_routes.py` with the AI-vision-specific cases.

    Per D-INTERFACE-FIRST: the FE `scan-sheet.tsx` Confirm handler (P4-D.3) POSTs to /api/meals with the new shape. Pin it now.

    Update `shared/schemas/meal.schema.json` by re-running `Meal.model_json_schema()` so the schema reflects the new optional fields. Frontend's `mealCreateSchema` Zod (P4-C.1) gets the same fields.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest tests/test_corrections_route.py tests/test_meals_routes.py -v</automated>
  </verify>
  <done>All ~7 new tests pass; Phase 3's existing test_meals_routes.py tests (~34) still green; full backend pytest count ≥ 185; meal.schema.json regenerated.</done>
</task>

---

## Slice C — Frontend lib (compress + Zod + BFFs + middleware)

<task type="auto">
  <name>Task P4-C.1: compressMealImage + Zod mirror + forwardMultipart + two BFF routes + middleware</name>
  <files>frontend/package.json, frontend/src/lib/compress-image.ts, frontend/src/lib/zod-schemas.ts, frontend/src/lib/api-server.ts, frontend/src/app/api/meals/scan/route.ts, frontend/src/app/api/corrections/route.ts, frontend/middleware.ts</files>
  <action>
    1. **Install browser-image-compression:** From `frontend/`, run `pnpm add browser-image-compression@^2.0`. Verify in `package.json` dependencies. The library is ~25 KB minified+gzipped, lazy-imported in the ScanSheet only (P4-D.1 uses `await import("browser-image-compression")`), so it does NOT enter the dashboard's initial bundle until the user taps "Snap a meal."

    2. **`frontend/src/lib/compress-image.ts`:**
       ```typescript
       export const COMPRESS_OPTS = {
         maxSizeMB: 0.5,
         maxWidthOrHeight: 1024,
         fileType: "image/jpeg" as const,
         initialQuality: 0.85,
         useWebWorker: true,
       };

       export async function compressMealImage(file: File): Promise<File> {
         const imageCompression = (await import("browser-image-compression")).default;
         const compressed = await imageCompression(file, COMPRESS_OPTS);
         // browser-image-compression returns a File for File input; assert.
         return compressed as File;
       }
       ```
       The dynamic import keeps the lib out of the dashboard's First Load JS (D-LAZY-COMPRESS).

    3. **Zod mirror in `zod-schemas.ts`:** Append (per D-SHARED-SCHEMA-MANUAL-MIRROR, mirroring shared/schemas/vision-response.schema.json + the extended meal.schema.json):
       ```typescript
       export const aiMetadataSchema = z.object({
         model: z.string(),
         prompt_hash: z.string(),
         image_dims: z.object({ w: z.number().int(), h: z.number().int() }),
         latency_ms: z.number().int().min(0),
         cost_usd: z.number().min(0),
       });
       export type AiMetadata = z.infer<typeof aiMetadataSchema>;

       export const visionComponentSchema = z.object({
         name: z.string().min(1).max(80),
         matched_food_id: z.string().nullable(),
         portion_g: z.number().int().min(10).max(800),
         kcal_low: z.number().int().min(0).nullable(),
         kcal_high: z.number().int().min(0).nullable(),
         kcal_point: z.number().int().min(0),
         protein_g_point: z.number().int().min(0),
         confidence: z.number().min(0).max(1).nullable(),
         source: z.enum(["table", "llm_then_table_rematch", "user_corrected"]),
       });
       export type VisionComponent = z.infer<typeof visionComponentSchema>;

       export const visionScanResponseSchema = z.object({
         components: z.array(visionComponentSchema).min(1).max(10),
         ai_metadata: aiMetadataSchema,
         vision_total_kcal_low: z.number().int().min(0),
         vision_total_kcal_high: z.number().int().min(0),
         user_daily_count: z.number().int().min(0),
         user_daily_limit: z.number().int().min(1),
       });
       export type VisionScanResponse = z.infer<typeof visionScanResponseSchema>;

       export const userCorrectionInputSchema = z.object({
         original_name: z.string(),
         corrected_name: z.string().nullable(),
         original_portion_g: z.number().int(),
         corrected_portion_g: z.number().int(),
         original_food_id: z.string().nullable(),
         corrected_food_id: z.string().nullable(),
       });
       ```
       Also EXTEND `mealCreateSchema` and `componentCreateSchema` to accept the new optional AI fields (mirror the Phase 4 extension to backend models). Ensure existing Phase 3 manual-log call sites still type-check (the fields are optional with defaults).

    4. **`forwardMultipart` in `frontend/src/lib/api-server.ts`:** Add a sibling function to `forwardToFlask`:
       ```typescript
       export async function forwardMultipart(
         method: "POST",
         path: string,
         formData: FormData,
       ): Promise<NextResponse> {
         const { userId, getToken } = await auth();
         if (!userId) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
         const token = await getToken();
         if (!token) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
         const apiUrl = process.env.NEXT_PUBLIC_API_URL;
         if (!apiUrl) return NextResponse.json({ error: "api_url_not_configured" }, { status: 503 });

         const upstream = await fetch(`${apiUrl}${path}`, {
           method,
           headers: { Authorization: `Bearer ${token}` },
           // NOTE: do NOT set Content-Type — fetch/Node infers multipart boundary from FormData.
           body: formData,
           cache: "no-store",
         });
         const text = await upstream.text();
         return new NextResponse(text, {
           status: upstream.status,
           headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" },
         });
       }
       ```
       Critical: do NOT set Content-Type — Node's fetch sets the multipart boundary automatically from the FormData body. Manually setting Content-Type strips the boundary and Flask sees no parts.

    5. **`frontend/src/app/api/meals/scan/route.ts`:**
       ```typescript
       import { NextRequest } from "next/server";
       import { forwardMultipart } from "@/lib/api-server";
       export async function POST(req: NextRequest) {
         const formData = await req.formData();
         return forwardMultipart("POST", "/meals/scan", formData);
       }
       ```

    6. **`frontend/src/app/api/corrections/route.ts`:**
       ```typescript
       import { NextRequest } from "next/server";
       import { forwardToFlask } from "@/lib/api-server";
       export async function POST(req: NextRequest) {
         return forwardToFlask("POST", "/corrections", await req.json());
       }
       ```

    7. **`frontend/middleware.ts`:** Extend `createRouteMatcher` to include `/api/corrections(.*)` (the `/api/meals(.*)` matcher already covers `/api/meals/scan`).

    No tests in this task — covered via build + manual smoke in P4-F.1.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`browser-image-compression` in package.json deps; compress-image.ts exports; new Zod schemas exported; `forwardMultipart` exported; two new BFF route files exist; middleware lists `/api/corrections(.*)`; `pnpm build` shows `/api/meals/scan` and `/api/corrections` in the route table; First Load JS for `/dashboard` recorded in commit message (manual gate — browser-image-compression should NOT appear in the dashboard chunk because of dynamic import).</done>
</task>

---

## Slice D — Frontend scan UI

<task type="auto">
  <name>Task P4-D.1: ScanSheet client component — capture, compress, scan, render chips</name>
  <files>frontend/src/app/dashboard/scan-sheet.tsx</files>
  <action>
    `scan-sheet.tsx` — client component. Wraps the shadcn `Dialog` (already in repo). Props:
    ```typescript
    {
      open: boolean;
      onOpenChange: (open: boolean) => void;
      onScanConfirmed: (meal: MealResponse) => void;   // bubble up to LogMealCta to refresh dashboard
      onFallbackToManual: () => void;                  // 429/network/parse-failure → open Phase 3 manual modal
    }
    ```

    State (React useState; no RHF needed because there's no traditional form):
    ```typescript
    const [stage, setStage] = useState<"idle" | "compressing" | "scanning" | "review" | "submitting" | "error">("idle");
    const [error, setError] = useState<{ code: string; message: string; details?: any } | null>(null);
    const [scanResult, setScanResult] = useState<VisionScanResponse | null>(null);
    const [draftComponents, setDraftComponents] = useState<ComponentDraft[]>([]);
    const [imageDims, setImageDims] = useState<{ w: number; h: number }>({ w: 0, h: 0 });
    ```

    Layout (top-down inside Dialog):
    1. **Stage = idle:** Header "Snap a meal" + `<input type="file" accept="image/*" capture="environment">` styled as a big tap target. `capture="environment"` tells mobile browsers to open the rear camera by default; desktop browsers fall back to a normal file picker. Sub-text: "We'll identify each food and estimate kcal. Your photo is not stored."

    2. **Stage = compressing:** Spinner + "Compressing image…" (target sub-second).

    3. **Stage = scanning:** Spinner + "Estimating kcal…" + a cancellable timer (display elapsed seconds; 5 s target, 30 s hard timeout via AbortController).

    4. **Stage = review:** Render `<ScanResultChips>` (P4-D.2) with `components={draftComponents}`, plus a header showing "Vision range: {vision_total_kcal_low}–{vision_total_kcal_high} kcal" (advisory; the persisted total comes from the table-recomputed kcal_point), plus a "Confirm" button that POSTs to /api/meals with `source: "ai_vision"`. Cancel button → reset to idle.

    5. **Stage = error:** Show error.message inline + an "Use manual entry instead" button that calls `onFallbackToManual()` + closes the sheet.

    On file select:
    ```typescript
    setStage("compressing");
    try {
      const compressed = await compressMealImage(file);
      setStage("scanning");
      const fd = new FormData();
      fd.append("image", compressed, compressed.name);
      const res = await fetch("/api/meals/scan", { method: "POST", body: fd });
      if (res.status === 429) {
        toast.error("You've used today's 8 scans. Switching to manual log.");
        onFallbackToManual();
        onOpenChange(false);
        return;
      }
      if (res.status === 503) {
        toast.error("Vision paused for the day. Switching to manual log.");
        onFallbackToManual();
        onOpenChange(false);
        return;
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError({ code: body.error ?? "unknown", message: body.error === "vision_parse_failed" ? "We couldn't read this photo — try a clearer shot or log manually." : "Scan failed." });
        setStage("error");
        return;
      }
      const parsed = visionScanResponseSchema.parse(await res.json());
      setScanResult(parsed);
      setDraftComponents(parsed.components.map(componentToDraft));
      setStage("review");
    } catch (e) {
      setError({ code: "network", message: "Network error — please try again or log manually." });
      setStage("error");
    }
    ```

    On Confirm:
    ```typescript
    setStage("submitting");
    const body = {
      source: "ai_vision",
      ai_metadata: scanResult!.ai_metadata,
      components: draftComponents.map(draftToComponentCreate),  // matched: {food_id, portion_g, kcal_low, kcal_high, confidence, source}; free-text: {name, portion_g, kcal_point, source}
    };
    const res = await fetch("/api/meals", { method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json" } });
    if (res.ok) {
      const meal = await res.json();
      toast.success("Meal logged from photo");
      onScanConfirmed(meal);
      onOpenChange(false);
      return;
    }
    // ... handle 422 / 5xx inline
    ```

    Per CONTEXT.md "Tap-to-edit chips UI" specifics: ScanSheet is parallel to Phase 3's MealLogModal — NOT a merged component. The Confirm button POSTs to the SAME /api/meals endpoint. The chip-edit interaction (P4-D.2) calls /api/corrections on each user change BEFORE Confirm so the corrections bias the next scan even if the user abandons the Confirm.

    Per D-LAZY-COMPRESS: browser-image-compression is imported via `compressMealImage` which itself dynamically imports the lib — so the dashboard's initial bundle stays unaffected.

    No tests — coverage via manual smoke in P4-F.2.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>`scan-sheet.tsx` builds; all five stages reachable in TS; 429/503/parse errors all route to `onFallbackToManual`; `pnpm build` shows browser-image-compression in a SEPARATE chunk (NOT in the dashboard's first-load JS — verify via `.next/build-manifest.json` inspection or commit-message route-table notes).</done>
</task>

<task type="auto">
  <name>Task P4-D.2: ScanResultChips — editable chip list with correction round-trip</name>
  <files>frontend/src/app/dashboard/scan-result-chips.tsx</files>
  <action>
    `scan-result-chips.tsx` — client component. Reuses Phase 3's `ComponentChip` (frontend/src/app/dashboard/component-chip.tsx) and `FoodSearch` (frontend/src/app/dashboard/food-search.tsx) verbatim — DO NOT fork them. The difference is the additional correction-callback that fires on each chip mutation BEFORE the Confirm button is pressed.

    Props:
    ```typescript
    {
      components: ComponentDraft[];   // initial list from /api/meals/scan response, mapped via componentToDraft
      onChange: (next: ComponentDraft[]) => void;
      onCorrection: (correction: UserCorrectionInput) => void;   // fires on each edit/remove
    }
    ```

    Behaviour:
    - Renders a vertical list of `<ComponentChip>` rows, one per draft component.
    - Above each chip: a small "Change dish" button that, when clicked, swaps the chip's name display for an inline `<FoodSearch>` that lets the user pick a different Ghana food. On select, calls `onChange` with the updated draft (`food_id` swapped, `name` swapped, `kcal_per_100g` swapped from the new food's value, `source` flipped to "table") AND fires `onCorrection({ original_name: prev.name, corrected_name: next.name, original_portion_g: prev.portion_g, corrected_portion_g: prev.portion_g, original_food_id: prev.food_id, corrected_food_id: next.food_id })`.
    - ComponentChip's existing `onChange` (portion-slider drag) is wrapped: when the drag completes (debounce 500 ms after last drag), if `portion_g` changed from initial, fire `onCorrection({ ..., original_portion_g: initial.portion_g, corrected_portion_g: latest.portion_g, corrected_name: null, corrected_food_id: prev.food_id })`.
    - ComponentChip's existing `onRemove` is wrapped: fire `onCorrection({ ..., corrected_name: null, corrected_food_id: null, corrected_portion_g: 0 })` to signal the user rejected the LLM's identification entirely. Then remove the draft from the list.
    - A "Add component" button below the list opens a `<FoodSearch>` that appends a new draft (rarely needed but supports the case where the LLM missed a dish).

    Calling /api/corrections:
    ```typescript
    async function postCorrection(c: UserCorrectionInput) {
      try {
        await fetch("/api/corrections", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(c),
        });
      } catch {
        // Silently swallow — corrections are best-effort. Don't break the user's flow on a missed correction.
      }
    }
    ```
    The ScanSheet wires `onCorrection={postCorrection}` so the chip component itself doesn't import fetch / Zod — it's a pure event emitter.

    Per CONTEXT.md "User corrections": every chip mutation is a correction. Even portion changes count — they feed into the next scan's user-history block. The 500ms debounce on slider drags keeps the correction stream readable in Mongo (one row per "the user moved the slider," not one per pixel).

    Per CONTEXT.md "Tap-to-edit chips UI" #4: this implements points 1-4 (search, slider, remove, add). Confirm + total kcal sum live in ScanSheet (P4-D.1).

    No tests — coverage via P4-F.2 manual smoke.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>ScanResultChips builds; debounced portion-correction POST observed in DevTools network panel during smoke; chip "Change dish" swaps the food and POSTs one correction; chip remove POSTs a correction with corrected_food_id=null; "Add component" appends a draft without any correction POST (it's an LLM omission, not a correction of a prior identification).</done>
</task>

<task type="auto">
  <name>Task P4-D.3: Dashboard wiring — SnapMealCta + LogMealCta merge + ServicePausedBanner + page.tsx</name>
  <files>frontend/src/app/dashboard/snap-meal-cta.tsx, frontend/src/app/dashboard/log-meal-cta.tsx, frontend/src/components/service-paused-banner.tsx, frontend/src/app/dashboard/page.tsx, frontend/src/app/layout.tsx</files>
  <action>
    **`snap-meal-cta.tsx`** — client component. Renders a primary button "Snap a meal" (with a camera icon from lucide-react). On click, opens a `<ScanSheet>`. Holds local state for sheet open + fallback callback. Wired such that 429/503/parse errors call `props.onFallbackToManual()` which the parent provides as "open the Phase 3 MealLogModal."

    **`log-meal-cta.tsx`** — EXTEND the existing Phase 3 island. The island currently hosts LogMealCta (manual) + TodaysMealsList + MealLogModal. Phase 4 ADDS:
    - SnapMealCta as a sibling button (rendered FIRST — "Snap a meal" is the wedge feature; manual is the fallback CTA below it).
    - ScanSheet rendered conditionally when SnapMealCta is open.
    - The `onFallbackToManual` prop wired so the existing MealLogModal opens in create mode when scan fails.
    - The `onScanConfirmed(meal)` callback calls `router.refresh()` to re-fetch the server-rendered KcalPill + TodaysMealsList (same path as Phase 3's manual create).

    Layout in the island:
    ```
    <SnapMealCta onFallbackToManual={openManualCreate} onScanConfirmed={() => router.refresh()} />
    <LogMealCtaButton onClick={openManualCreate}>Log meal manually</LogMealCtaButton>
    <TodaysMealsList meals={...} onEdit={openManualEdit} />
    <MealLogModal open={manualOpen} onOpenChange={setManualOpen} initial={manualEditTarget} />
    <ScanSheet open={scanOpen} onOpenChange={setScanOpen} onFallbackToManual={...} onScanConfirmed={...} />
    ```

    **`service-paused-banner.tsx`** — SERVER component (no client JS). Read the global system_state to decide whether to render:
    - Add a new Flask route `GET /scan-budget` that returns `{spend_usd, cap_usd, paused: bool, date}` (no auth — but it's behind the same BFF; for v1, **require auth** since the banner is only shown to signed-in users on /dashboard). Add the route to `backend/app/routes/scan.py` (cheap, same file) and to `backend/app/routes/scan.py`'s blueprint.
    - Add `frontend/src/app/api/scan-budget/route.ts` BFF: `forwardToFlask("GET", "/scan-budget")`.
    - The banner component awaits the BFF call (server-side from /dashboard's render) and renders a Tailwind-styled banner ONLY when `paused === true`. The banner says: "Vision is paused for today (daily cost cap reached). You can still log manually."

    **`frontend/src/app/dashboard/page.tsx`** — SERVER component. Add the ServicePausedBanner ABOVE the existing KcalPill. Pass nothing — the banner does its own fetch.

    **`frontend/src/app/layout.tsx`** — already protected by middleware; no change needed unless the banner should appear on /history too (CONTEXT decision: yes, it should — the banner is "system state," not "dashboard state"). Add `<ServicePausedBanner />` to the root layout above the children render, BUT it MUST early-return null when the user is not signed in (the BFF returns 401). Add an auth check inside ServicePausedBanner: try the fetch, on 401 return null.

    Per CONTEXT.md "Frontend on 503... site-wide banner": the banner lives in the root layout so /history sees it too. Manual log still works because the banner is purely informational.

    No tests — manual smoke in P4-F.2.

    Per D-INTERFACE-FIRST: the /scan-budget endpoint shape is the contract. Pin it as `{spend_usd: number, cap_usd: number, paused: boolean, date: string}`.
  </action>
  <verify>
    <automated>cd frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>SnapMealCta + ScanSheet wired into the dashboard island; "Snap a meal" appears above "Log meal manually"; ServicePausedBanner shows up in the route table for `/` and renders only when paused; 429 toast and fallback path both verified in build; `pnpm build` green; no new top-level deps beyond browser-image-compression.</done>
</task>

---

## Slice E — Deploy config + Phase 7 hooks

<task type="auto">
  <name>Task P4-E.1: render.yaml + .env.example + golden_set placeholder</name>
  <files>render.yaml, backend/.env.example, backend/tests/golden_set/README.md</files>
  <action>
    **`render.yaml`** — extend `fitgh-api.envVars` with four entries:
    ```yaml
          - key: ANTHROPIC_API_KEY
            sync: false
          - key: LLM_VISION_MODEL
            value: "claude-sonnet-4-6"
          - key: VISION_DAILY_CAP_USD
            value: "5.0"
          - key: COST_ALERT_WEBHOOK_URL
            sync: false
    ```
    `sync: false` on the two secret-shaped entries means Render prompts the user to paste at deploy time and they're never written to source. `value:` on the two non-secret entries lets the code's defaults be overridden in production without a code change.

    Frontend (`fitgh-web`) envVars unchanged — no new public env vars (browser-image-compression is bundled at build time, no runtime config).

    **`backend/.env.example`** — create the file (it does not currently exist per the Glob output) with the full env surface:
    ```
    # FitGH backend env example.
    # Copy to .env.local (gitignored) and fill in real values.
    # All four ANTHROPIC_* and VISION_* entries are Phase 4.

    MONGODB_URI=mongodb+srv://<user>:<pass>@cluster0.pcd3g.mongodb.net/fitgh?retryWrites=true&w=majority
    CLERK_SECRET_KEY=sk_test_...
    CLERK_AUTHORIZED_PARTIES=http://localhost:3000,https://fitgh-web.onrender.com
    CORS_ALLOWED_ORIGINS=http://localhost:3000

    # Phase 4 — Image -> Kcal Core Loop.
    ANTHROPIC_API_KEY=sk-ant-...
    LLM_VISION_MODEL=claude-sonnet-4-6
    VISION_DAILY_CAP_USD=5.0
    # Optional — leave empty to fall back to WARN-log on cost alerts.
    COST_ALERT_WEBHOOK_URL=
    ```
    Verify `.gitignore` already covers `.env.local` and `.env` (Phase 1 baseline). If `.env.example` itself is gitignored, fix the pattern.

    **`backend/tests/golden_set/README.md`** — placeholder file per CONTEXT.md "Golden-set construction (Phase 7) — out of scope for Phase 4 plan; just leave a hook":
    ```markdown
    # Vision golden set — Phase 7 hook

    Drop 30 representative meal photos here as `{nn}-{slug}.jpg` (e.g.,
    `01-jollof-with-chicken.jpg`). Each photo's expected components live in
    `{nn}-{slug}.expected.json` matching the VisionResponse schema.

    Phase 7 will add a `pytest tests/golden_set/test_golden_set.py` that, when
    invoked with `RUN_GOLDEN_SET=1`, calls real Anthropic Sonnet 4.6 for each
    photo and reports per-component MAPE + an aggregate MAPE. Target <25% MAPE
    on the env-pinned model (`LLM_VISION_MODEL=claude-sonnet-4-6`).

    For now this directory is intentionally empty.
    ```

    No tests — pure config / placeholder.
  </action>
  <verify>
    <automated>cd C:/dev/Fitness && python -c "import yaml; yaml.safe_load(open('render.yaml'))" && test -f backend/.env.example && test -f backend/tests/golden_set/README.md && echo "config files OK"</automated>
  </verify>
  <done>render.yaml parses cleanly; backend/.env.example documents all four new env vars; golden_set/README.md exists; .gitignore unchanged (still covers .env.local + .env); no commits of real secrets.</done>
</task>

---

## Slice F — User checkpoint + live smoke + traceability flip

<task type="checkpoint:human-action" gate="blocking">
  <name>Task P4-F.1: USER CHECKPOINT — Provision Anthropic API key</name>
  <what-built>
    All Phase 4 code is in place and tests pass with respx-mocked Anthropic calls. The production /meals/scan route returns 503 until ANTHROPIC_API_KEY is provisioned in Render's environment.
  </what-built>
  <how-to-verify>
    The user must complete these dashboard actions before P4-F.2 can run:

    1. Visit https://console.anthropic.com/ and sign up (or sign in if you already have an account).
    2. Add billing: Settings → Billing → Add credit. Add at least **$5 of prepaid credit** (≈ 1,250 vision calls at $0.004/call). This unlocks the API; without credit, every call returns 429 from Anthropic.
    3. Settings → API keys → **Create key**. Name it `fitgh-prod`. Copy the `sk-ant-...` value — it is shown ONCE; you cannot retrieve it later (only revoke + recreate).
    4. Paste into your LOCAL `backend/.env.local` as:
       ```
       ANTHROPIC_API_KEY=sk-ant-...
       ```
       (file is gitignored — confirm with `git check-ignore backend/.env.local`).
    5. Visit https://dashboard.render.com → **fitgh-api** → **Environment** → **Add Environment Variable**:
       - Key: `ANTHROPIC_API_KEY`
       - Value: the same `sk-ant-...`
       - **Sync to repo: OFF** (sync: false).
       Click **Save**. Render auto-redeploys fitgh-api with the new env.
    6. (Optional but recommended) In the same Render Environment page:
       - Add `VISION_DAILY_CAP_USD = 5.0` if you want a different cap than the code default.
       - Add `COST_ALERT_WEBHOOK_URL = <Discord/Slack incoming webhook URL>` if you want JSON alerts at $0.05/DAU. Without this, alerts WARN-log to Render's log stream — still observable from the Render dashboard.
    7. Wait for the redeploy to show "Deploy live" (~2-3 minutes). Confirm via `curl https://fitgh-api.onrender.com/health` returns `{ok: true, mongo: "connected"}` (unchanged) — the env var injection is silent; the next /meals/scan call will reveal whether the key is valid.
  </how-to-verify>
  <resume-signal>Type "key provisioned" when ANTHROPIC_API_KEY is set in BOTH backend/.env.local AND Render fitgh-api Environment. The executor proceeds to P4-F.2 live smoke.</resume-signal>
</task>

<task type="auto">
  <name>Task P4-F.2: Live operator smoke (RUN_LIVE_VISION_TEST=1) + REQUIREMENTS.md flip</name>
  <files>backend/tests/test_scan_route.py, .planning/REQUIREMENTS.md</files>
  <action>
    **Step 1 — Live test scaffold.** Add ONE test gated by env var to `test_scan_route.py`:
    ```python
    @pytest.mark.skipif(os.environ.get("RUN_LIVE_VISION_TEST") != "1",
                       reason="live test — requires ANTHROPIC_API_KEY and consumes ~$0.005 of credit")
    def test_live_scan_jollof_returns_components(client, monkeypatch, real_atlas_ghana_foods):
        # Sends a real test image of jollof rice from tests/fixtures/jollof.jpg to
        # /meals/scan and asserts the response contains at least one component
        # whose name contains "rice" or "jollof", with kcal_low > 0.
        ...
    ```
    The test fixture `tests/fixtures/jollof.jpg` is a 1024×768 photo of jollof rice (commit to repo — small enough at JPEG q=0.85 to not bloat the repo; ~80 KB). If a real photo is unavailable at task time, ship the test without the image and document the deferred step in SUMMARY for the operator to drop the image post-merge.

    The test calls Atlas + Anthropic REAL — uses the operator's `.env.local`. Do NOT run in CI (the skipif guards it).

    **Step 2 — Operator live smoke.** Run:
    ```
    cd backend
    RUN_LIVE_VISION_TEST=1 .venv/Scripts/python.exe -m pytest tests/test_scan_route.py::test_live_scan_jollof_returns_components -v -s
    ```
    Expected output: 200 from /meals/scan, components list contains at least one item with `name ~= "jollof"` or `"rice"`, kcal_point in 300-600 range for a 350g plate. Cost ≈ $0.004-$0.006 (one call).

    **Step 3 — Production smoke via browser.**
    1. Sign in at https://fitgh-web.onrender.com (production Clerk Production instance).
    2. /dashboard → click "Snap a meal".
    3. Upload a real photo of jollof rice (use your phone).
    4. Within ~5 seconds, chips appear: e.g., "Jollof rice 350 g · 580 kcal" (or similar).
    5. Drag the portion slider → live total updates → DevTools network panel shows a POST /api/corrections for the drag.
    6. Click "Confirm" → meal appears in TodaysMealsList → KcalPill updates.
    7. Repeat 8 times → 9th call shows toast "You've used today's 8 scans" + Phase 3 manual modal opens.
    8. (Optional, deferred) Set `VISION_DAILY_CAP_USD=0.01` in Render env temporarily, redeploy, scan once → expect 503 + ServicePausedBanner site-wide. Revert to 5.0 after.

    **Step 4 — Cost alert verification.** Set `COST_ALERT_WEBHOOK_URL` to a real Discord/Slack incoming webhook. Set `VISION_DAILY_CAP_USD=0.20` temporarily. Run 3 scans (total ~$0.012) — first scan should trigger the webhook because spend_per_dau ($0.012/1 = $0.012) is below $0.05, but... wait, $0.012 < $0.05. We need MORE spend or LESS DAU. **Simpler verification**: monkey-patch the threshold to $0.001 locally in a one-off CLI invocation, OR run the CI test `test_cost_alert_fires_when_per_dau_over_threshold` (already covers the firing logic). Revert all env overrides after.

    **Step 5 — Traceability flip.** Update `.planning/REQUIREMENTS.md`:
    - Flip `Pending` → `Complete` for: VIS-01, VIS-02, VIS-03, VIS-04, VIS-05, VIS-06, VIS-07, VIS-08, VIS-09, VIS-10, VIS-11, VIS-12, OBS-03 (13 IDs total).
    - Update the bottom-of-file "Last updated" line: `*Last updated: 2026-05-13 — Phase 4 (Image → Kcal Core Loop) complete; VIS-01..12 + OBS-03 flipped to Complete.*`

    **Step 6 — Final pytest count + commit.** Run `cd backend && .venv/Scripts/python.exe -m pytest -q` — assert count ≥ 180 (target per CONTEXT). Record exact count in the SUMMARY.
  </action>
  <verify>
    <automated>cd backend && .venv/Scripts/python.exe -m pytest -q && cd ../frontend && pnpm tsc --noEmit && pnpm build</automated>
  </verify>
  <done>Live test (when RUN_LIVE_VISION_TEST=1) returns a valid VisionResponse against real Anthropic; production browser smoke confirms the loop end-to-end; REQUIREMENTS.md has 13 IDs flipped to Complete; backend pytest count ≥ 180; SUMMARY captures: per-call cost from live test, daily cap toast verification, fallback manual path, ServicePausedBanner test, COST_ALERT_WEBHOOK_URL provisioning, three operator-side mongosh index commands (`db.vision_usage.createIndex({user_id: 1, date: 1}, {unique: true})`, `db.user_corrections.createIndex({user_id: 1, corrected_at: -1})`, no index needed for system_state).</done>
</task>

---

## Test Plan

- **Backend pytest count:** Phase 3 baseline 158 → Phase 4 target ≥ 180. Projected: ~205 (+50 vision tests across 4 new files).
- **Frontend:** `pnpm tsc --noEmit` + `pnpm build` are the v1 gates (no Jest, no Playwright in Phase 4 — matches Phase 3's posture). Visual + flow verification is the P4-F.2 operator smoke (8 steps).
- **No real Anthropic calls in CI** — respx intercepts every call. The ONE live test is env-gated and only runs locally by the operator post-key-provisioning.
- **Three new dev dependencies:** `anthropic>=0.40,<1` (prod), `respx>=0.21` (dev — verify already present from Phase 1 baseline), `browser-image-compression@^2.0` (frontend prod, lazy-imported).
- **Race-safety tests:** `test_user_daily_cap_race_at_most_8_succeed` and `test_global_budget_breaker_admits_concurrent_then_pauses` cover the two race windows; both pass deterministically against mongomock.

## Notes for the Executor

- The Render auto-deploy from Phase 1 is still in force: each commit to `main` triggers redeploys. Backend gets the new env vars on the redeploy that follows P4-F.1's user checkpoint.
- After P4-A.1 lands (db.py extension) and is deployed, run these operator-side mongosh commands ONCE against production Atlas:
  ```javascript
  db.vision_usage.createIndex({user_id: 1, date: 1}, {unique: true})
  db.user_corrections.createIndex({user_id: 1, corrected_at: -1})
  ```
  No index needed for `system_state` (single doc with natural key `_id: "vision_budget"`).
- The day-1 multi-component shape from Phase 3 is the canonical Meal contract. Phase 4 fills `kcal_low / kcal_high / confidence / ai_metadata` on writes from /meals/scan-confirmed → /meals POST. No schema migration.
- `MealCreate` and `ComponentCreate` gain optional fields (`source`, `ai_metadata`, `kcal_low`, `kcal_high`, `confidence`). Existing Phase 3 manual log requests continue working — the fields default to None / "manual" and the existing test suite stays green.
- The `/scan-budget` endpoint is new and small. It piggybacks on `scan.py` to keep all scan-related state queries in one file.
- The cost-alert webhook payload is a `{"content": "..."}` body. Discord, Slack, Telegram (with the official Bot API webhook shim), and most others accept this minimal shape. If the operator picks a webhook system that needs a different shape, swap in `scan.py` is one line.
- Atomic commits + push to origin/main per task (Render auto-deploys exercise each task's changes incrementally — same pattern as Phase 3).

## Output

After completion, create `.planning/phases/04-image-kcal-loop/04-SUMMARY.md` using the standard Phase template, including:
- Final pytest count (target ≥ 180).
- Live test result: per-call cost, per-call latency, components returned for the test jollof photo.
- Production smoke outcomes for the 8-step browser check.
- Operator-side actions performed: ANTHROPIC_API_KEY provisioning (Anthropic console + Render), three mongosh index commands, COST_ALERT_WEBHOOK_URL setup (or note it's deferred).
- Any deviations from the must_haves + their resolution.
- Phase 5 hand-off notes: Phase 5 (Animated Dashboard) builds on Phase 4's Confirm-meal path — when a meal is logged (manual OR AI), Phase 5's animated kcal ring will hook into the same `router.refresh()` signal already in place. Rive runtime + state machine inputs are Phase 5 concerns; Phase 4 ships a static UI.
- Phase 7 hand-off notes: `backend/tests/golden_set/` directory in place; Phase 7 drops 30 photos + expected.json fixtures and adds a `RUN_GOLDEN_SET=1`-gated test that reports MAPE against the env-pinned model.
