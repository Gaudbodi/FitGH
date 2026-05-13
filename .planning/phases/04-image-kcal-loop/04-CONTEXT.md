# Phase 4: Image → Kcal Core Loop — Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — user driving autonomous mode)

<domain>
## Phase Boundary

**The wedge feature.** A user snaps a meal photo from the dashboard, sees each visible component identified separately as tap-to-edit chips with kcal ranges within ~5s, can correct dish/portion inline, and the confirmed meal persists into the same multi-component `meals` collection Phase 3 established. Server enforces a per-user 8/day cap + a global $/day circuit breaker. **No image bytes retained server-side** after the vision call.

</domain>

<decisions>
## Implementation Decisions

### Vision model

- **Claude Sonnet 4.6** (`claude-sonnet-4-6`) via the official `anthropic` Python SDK.
- **Prompt caching** for the system prompt (Ghana food table reference + chain-of-thought example) so cost-per-call drops to the variable input (image + brief user prefs).
- **Model pin via env var:** `LLM_VISION_MODEL=claude-sonnet-4-6`. Re-run the golden set (Phase 7) on any bump.

### Image pipeline (no server storage)

- **Client-side compression** with `browser-image-compression` already in the project plan: max 1024px long edge, max 0.5 MB, JPEG q=0.85.
- POST to Flask `/meals/scan` as **multipart/form-data** — Flask reads bytes into memory, base64-encodes for the Anthropic call, **discards bytes immediately** after the call returns. No temp files. No GridFS. No R2.
- Response is the structured component list + ranges; Flask returns it to BFF, which returns it to the client. The client renders chips; on confirm, POSTs to `/meals` (Phase 3 endpoint) with the corrected components.

### Multi-component schema integration

Phase 3 already shipped the canonical `meals` shape. Phase 4 only fills the nullable fields the Phase 3 plan reserved: `kcal_low`, `kcal_high`, `confidence`, `ai_metadata: { model, prompt_hash, image_dims, latency_ms, cost_usd }`. **No new `ai_meals` collection.** `source` becomes `"llm_then_table_rematch"` or `"user_corrected"`.

### Table re-match (table wins)

Vision returns `kcal_per_component` as a range; Flask re-matches each `name` against `ghana_foods` (substring + alt_names). If matched, `kcal_point` is recomputed as `kcal_per_100g × portion_g / 100` (table value). The LLM's kcal_low/high stays in the response as advisory but the *persisted* kcal_point comes from the table. Falls back to the LLM range midpoint if no table match.

### Per-user 8/day cap

- New collection `vision_usage`: `{user_id, date: "YYYY-MM-DD", count, last_call_at}`. Compound unique index on `(user_id, date)`.
- On `/meals/scan`: load today's doc, if `count >= 8` return HTTP 429 `{error: "daily_cap", reset_at: "tomorrow_00:00_user_tz"}`.
- Frontend on 429: friendly toast + auto-fallback to the manual `MealLogModal` from Phase 3.

### Global $/day circuit breaker

- New collection `system_state`: single doc `{_id: "vision_budget", date: "YYYY-MM-DD", spend_usd: 0.0, cap_usd: env(VISION_DAILY_CAP_USD, default 5.0)}`.
- Each scan increments `spend_usd` by computed cost (input tokens × $0.003/1k + output × $0.015/1k ≈ ~$0.004/image for Sonnet 4.6).
- If `spend_usd > cap_usd`: all subsequent scans return HTTP 503 `{error: "service_paused", reason: "daily_budget"}` until the next UTC day.
- Frontend on 503: site-wide banner "Service paused for the day — please log manually," manual path still works.

### Cost alerting (Sentry deferred)

Sentry was dropped in the 2026-05-12 rewrite. Replace with **simple webhook alert**: when `spend_usd / DAU_today > 0.05` (per the OBS-03 requirement), Flask POSTs a JSON payload to env var `COST_ALERT_WEBHOOK_URL` if set. Discord/Slack/Telegram-compatible payload shape. If the env var isn't set, log to Render at WARNING level instead — operator still sees it.

### User corrections

- New collection `user_corrections`: `{user_id, original_name, corrected_name, original_portion_g, corrected_portion_g, original_food_id, corrected_food_id, corrected_at}`.
- On the chip-edit UI, when a user changes a component, log to `user_corrections`.
- Next scan from the same user: Flask passes the last 20 corrections to the vision system prompt as a "user history" block so the model biases toward dishes the user has corrected to before.

### Tap-to-edit chips UI

- New `/dashboard` button: **"Snap a meal"** opens a sheet:
  1. Camera-first input (`<input type="file" accept="image/*" capture="environment">`) for mobile direct capture.
  2. After upload, client compresses, POSTs to `/api/meals/scan`, shows a loading state (target p50 ≤ 5s).
  3. Response renders as a vertical list of `ComponentChip`s (reuse the Phase 3 chip with kcal range overlay).
  4. Per chip: tap-to-edit name (cmdk search against `/foods`), portion slider, remove-chip X.
  5. Footer: total kcal range + "Confirm" button which POSTs to `/api/meals` with the corrected components (same shape as manual).

### Env var surface

- `ANTHROPIC_API_KEY` (sk-ant-...) — secret, paste in Render fitgh-api env + `backend/.env.local` for local dev.
- `LLM_VISION_MODEL=claude-sonnet-4-6` — default in code; overridable.
- `VISION_DAILY_CAP_USD=5.0` — default in code; overridable for stress tests.
- `COST_ALERT_WEBHOOK_URL` — optional; if absent, warn-log instead.

### Testing

- Vision route tested via **`respx`** (already a dev dep) — intercept Anthropic SDK's underlying HTTPS call and return canned fixtures. No real API calls in CI.
- One end-to-end live test gated behind env var `RUN_LIVE_VISION_TEST=1` to verify the production wiring works without burning credits in CI.
- Golden-set construction (Phase 7) — out of scope for Phase 4 plan; just leave a hook (`backend/tests/golden_set/` directory with placeholder README).

</decisions>

<code_context>
## Existing Code Insights

- `backend/app/middleware/auth.py` — reuse `@require_auth`.
- `backend/app/routes/meals.py` — Phase 3's POST /meals. Phase 4 adds `POST /meals/scan` in the same blueprint or a new `scan.py` blueprint (planner picks).
- `backend/app/lib/meals.py` — has `compute_kcal_for_component`, `recompute_meal_totals`. Phase 4 reuses them after table re-match.
- `backend/app/db.py` — adds `vision_usage`, `system_state`, `user_corrections` collections.
- `frontend/src/app/dashboard/meal-log-modal.tsx` — Phase 3's manual log. Phase 4's `ScanSheet` is parallel, reuses `ComponentChip` and `FoodSearch`.
- `frontend/src/lib/api-server.ts` — `forwardToFlask` BFF helper; multipart support may need a minor extension (planner verifies and adds `forwardMultipart` variant if needed).
- `browser-image-compression` — already declared in the original technology plan; install if not already in package.json.

</code_context>

<specifics>
## Specific Ideas

- System prompt includes the full `ghana_foods` collection (25 items × ~150 tokens = ~4k tokens, well within Sonnet 4.6's context). Use **prompt caching** so this is cached across calls — drops per-call cost by ~75%.
- Image is provided as base64 inline (Anthropic SDK supports this). Don't use the Files API for v1 — adds complexity for no clear win at 1 image per call.
- Vision response schema: strict JSON via Anthropic's tool-use mode. Tool name: `report_meal_components`. Args: `{components: [{name, kcal_low, kcal_high, kcal_point, portion_g_estimate, confidence}]}`. If the model returns malformed JSON, retry once; on second failure return 502 with friendly fallback.
- Sonnet 4.6 with 1024×1024 image + 4k cached system prompt: ~1.5–3s p50 latency. The 5s target has ~2s of slack.

</specifics>

<deferred>
## Deferred Ideas

- **Opt-in meal-image history (Cloudflare R2):** v2.
- **Two-model cascade (Sonnet for hard, GPT-4o for easy):** v2 — over-engineered for MVP.
- **Fine-tuned classifier for the easy 60%:** v2 once we have ≥1000 user_corrections to train on.
- **Golden-set construction (30-photo accuracy benchmark):** Phase 7. Phase 4 leaves the hook.
- **Cloud blob for images:** No. Per-call discard is the privacy promise.
- **Volume pricing renegotiation with Anthropic:** post-1000-DAU milestone.

</deferred>

---

*Phase: 04-image-kcal-loop*
*Context auto-generated: 2026-05-13 (discuss skipped per user-driven autonomous mode)*

## ⚠ User checkpoint — Anthropic API key

Before Slice F (deploy + verify), the user must:

1. Visit https://console.anthropic.com/, sign up if needed, add billing (~$5 min credit).
2. Create an API key (sk-ant-...).
3. Paste into **`backend/.env.local`** as `ANTHROPIC_API_KEY=sk-ant-...` (gitignored).
4. Paste into **Render fitgh-api → Environment** as `ANTHROPIC_API_KEY=sk-ant-...` (sync: false). Trigger redeploy.
5. Optionally set `VISION_DAILY_CAP_USD=5.0` (default) and `COST_ALERT_WEBHOOK_URL=...` (Discord/Slack webhook for budget alerts).

Plan executor proceeds without the key (mocked Anthropic calls via respx); only Slice F's live test + the production deploy blocks on this checkpoint.
