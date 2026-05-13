# FitGH Launch Runbook

**For:** the operator (Francis Yiryel) preparing FitGH v1.0 for soft launch.
**Last updated:** 2026-05-13 (Phase 7 close)
**Prerequisite:** all 7 phases complete, master branch deploys cleanly to
Render fitgh-web + fitgh-api.

This runbook covers the four launch-time tasks Phase 7 cannot automate, plus
the optional real-Anthropic golden-set re-run. Follow each section before
inviting users.

## 1. Pre-launch checklist

Run this checklist 24 h before opening signups.

- [ ] **Atlas backup verified.** Trigger the GH Actions `nightly-mongo-backup`
      workflow manually once (`gh workflow run nightly-mongo-backup`). Confirm
      the artifact appears in the run output with `mongodump-*.tar.gz` and
      that the size is non-trivial (typically > 200 KB even for an empty DB).
      The DATA-01 backup path is real — operator should be able to download
      the artifact, decrypt with `MONGODB_BACKUP_PASSPHRASE`, and re-import.

- [ ] **All `.env.example` vars filled in Render.**
      In the Render dashboard for both `fitgh-web` and `fitgh-api`, go to
      Environment → confirm every variable listed in `.env.example` has a
      value (no blanks). Cross-check:
      - `MONGODB_URI` (sync:false in production)
      - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (Production key, not Test)
      - `CLERK_SECRET_KEY` (Production)
      - `CLERK_AUTHORIZED_PARTIES` = your production Render URL (e.g.
        `https://fitgh-web.onrender.com`)
      - `NEXT_PUBLIC_API_URL` = `https://fitgh-api.onrender.com` (NOT
        localhost)
      - `ANTHROPIC_API_KEY` (Production)
      - `LLM_VISION_MODEL` = `claude-sonnet-4-6`
      - `VISION_DAILY_CAP_USD` (recommended: `5.00` for soft launch — see §2)
      - `COST_ALERT_WEBHOOK_URL` (see §4)
      - `FITGH_GIT_SHA` (mapped from `RENDER_GIT_COMMIT` via render.yaml,
        OR pasted manually; surfaces in `/me/export` archive metadata)
      - `FLASK_ENV=production`

- [ ] **Copy audit clean in strict mode.**
      ```bash
      python scripts/audit_copy.py --strict
      ```
      Should print `audit_copy: clean` and exit 0. Any forbidden phrase
      finding MUST be rewritten before launch.

- [ ] **Privacy policy reflects current data flows.**
      Open `https://fitgh-web.onrender.com/privacy` and verify all 5
      sub-processors named (Anthropic / Clerk / MongoDB Atlas / Render /
      GitHub Actions) match the current architecture. If a new sub-processor
      (e.g. Cloudflare R2 for v2 image history) has been added, update
      `frontend/src/app/(public)/privacy/page.tsx` BEFORE launching that
      feature.

- [ ] **Clerk Production keys swapped in.**
      If you've been running with Clerk Test keys (`pk_test_*` /
      `sk_test_*`), switch to Production (`pk_live_*` / `sk_live_*`) in the
      Render env. Test keys auto-allow all origins; Production requires
      the `fitgh-web.onrender.com` origin to be added in
      Clerk Dashboard → Domains → Authorized Origins.

- [ ] **End-to-end smoke test.**
      In an incognito window: sign up → onboard → snap a meal photo (try
      jollof for a real-world test) → confirm the meal lands in /history →
      delete account from /settings. The whole loop should work without
      errors in any of: Clerk modal, Flask /meals/scan response, MongoDB
      writes, Anthropic vision pipeline, /settings cascade-delete.

## 2. Anthropic spend cap

Anthropic enforces a hard monthly spend cap at the account level. Set it
**before** opening signups — the per-user 8/day + global $/day caps in code
are belt-and-braces, but the console cap is the final fuse.

1. Open <https://console.anthropic.com/settings/limits>.
2. Set a monthly spend limit. Recommended starting value: **$200/month**.
   - Rationale: per CLAUDE.md cost table — ~$36/month at 100 DAU × 3
     meals/day. $200 gives 5× headroom and time to react if traffic spikes.
   - Hard ceiling: at $200 even a single rogue user can't bankrupt you.
3. Save. Anthropic will block API calls once the cap is reached; the Flask
   `/meals/scan` route translates Anthropic 4xx into a 503 service_paused
   banner via `app/components/service-paused-banner.tsx`.

## 3. WebPageTest Lagos — Ghana-edge TTFB measurement (PERF-04)

This measures the production p75 TTFB from a Lagos client over 4G. Lagos is
the closest WebPageTest vantage point to Accra (no Accra POP as of 2026).

1. Open <https://www.webpagetest.org/>.
2. Paste the production URL: `https://fitgh-web.onrender.com/dashboard`.
3. **Test Location:** `Lagos, Nigeria (gp-chrome)`. If unavailable, fall
   back to `Cape Town, South Africa (za-chrome)` and note the substitution
   in the result.
4. **Browser:** Chrome. **Connection:** `4G (9 Mbps / 9 Mbps / 170 ms RTT)`.
5. Number of tests: **5** (so the median run is meaningful).
6. Start test.

When the run completes:

- Read **Document TTFB** from the median run's column (NOT First View
  TTFB — Document TTFB is the server processing time exclusive of TCP
  + TLS).
- Record the p75 across the 5 runs in `07-SUMMARY.md` Measurements
  section.
- Pass criterion: **p75 TTFB ≤ 2 s**.

### If p75 > 2 s — Cloudflare-in-front fallback (DOCUMENTED, NOT shipped)

The v1.0 stance is to ship Vercel/Render direct and only add Cloudflare
when measurement justifies it. If the run shows p75 > 2 s:

1. **Don't** implement immediately. Wait one week and re-run — Render's
   regional balancer may shift workloads. Cold-start spikes inflate p75
   on the free tier.
2. If still > 2 s, two-option ladder:
   - **R-1 (cheap, predictable):** Upgrade Render `fitgh-web` to the
     Starter plan ($7/mo). Kills cold starts entirely. Expected TTFB
     improvement: 400–600 ms.
   - **R-2 (cheap, network-edge):** Cloudflare proxied DNS in front of
     `fitgh-web.onrender.com`. Lagos POP. Adds caching on /workouts (HTML
     + posters). Expected improvement: 200–400 ms.
3. Either option is v1.1 operator work — DO NOT block soft launch on it.

## 4. Cost-alert webhook (COST_ALERT_WEBHOOK_URL)

Phase 4 ships a $/DAU/day > $0.05 cost alert. The alert fires once per UTC
day to the webhook URL in `COST_ALERT_WEBHOOK_URL`; if unset it falls back
to a WARN log line that nobody will read.

**Choose Discord OR Slack.** Both accept the same Phase 4 payload shape:
```json
{ "content": "FitGH cost alert: $/DAU/day = $0.07 at 12 DAU on 2026-05-14" }
```

### Discord option

1. Create or open a Discord server you control.
2. Settings → Integrations → Webhooks → New Webhook.
3. Channel: `#fitgh-alerts` (or any channel you'll see).
4. Copy Webhook URL (looks like `https://discord.com/api/webhooks/...`).
5. Paste into Render `fitgh-api` Environment → `COST_ALERT_WEBHOOK_URL` →
   Save. The service redeploys automatically.

### Slack option

1. Slack workspace → Apps → Incoming WebHooks → Add to Slack.
2. Choose channel `#fitgh-alerts`.
3. Copy Webhook URL.
4. Paste into Render `fitgh-api` Environment → `COST_ALERT_WEBHOOK_URL` →
   Save.

Verify by triggering a test post once Render redeploy completes — pick a
date in the past and force a write to `system_state`:
```bash
# Connect to Atlas via mongosh and bump alert_fired = false / spend > cap
# then call /api/scan-budget to surface the next-write path. The next real
# /meals/scan call will fire the webhook.
```

## 5. Real-Anthropic golden-set re-run

The Phase 7 P7-D.2 harness ships with 10 placeholder JPEGs. Real photos
land in v1.1. The harness shape is validated by the in-phase
deterministic-fake run (`golden-set-result.md` shows MAPE 0 % / dish
accuracy 1.00 — by construction).

To run against real Anthropic on the current photos (which will FAIL on
solid-colour placeholders, as expected):

```bash
cd backend && RUN_GOLDEN_SET=1 GOLDEN_SET_REAL=1 \
  ANTHROPIC_API_KEY=sk-ant-... \
  .venv/Scripts/python.exe -m pytest tests/golden_set/test_golden_vision.py \
  -v -s | tee ../.planning/phases/07-launch-hardening/golden-set-result-real.md
```

Expected cost: ~$0.005/photo × 10 = **$0.05 total**. The output expects FAIL
because Claude cannot derive "jollof rice" from a 64×64 red square. That's
the v1.1 task:

- Replace each `photos/NN-slug.jpg` with a real Ghana-food photo (public
  domain or own-shot).
- Flip `source: "placeholder"` to `source: "public-domain"` or
  `source: "operator-shot"` in `manifest.json`.
- Re-run the command above. The < 25 % MAPE target then becomes meaningful.

## Re-run triggers (post-launch)

Re-run the real-Anthropic golden set on:

- Bump of `LLM_VISION_MODEL` env (e.g. when Anthropic releases Sonnet 5.0).
- Edit of `MODEL_PRICING_PER_1K` in `app/lib/vision.py`.
- Non-trivial change to `build_system_prompt` (cached block hash shifts).

## Explicit NON-steps (v1.0 stance)

These were deliberately NOT shipped in v1.0:

- **No custom-domain setup.** `fitgh-web.onrender.com` is the production URL
  for soft launch. Deferred to v1.1 — when DNS + SSL contract gets
  procured.
- **No Sentry on frontend or backend.** Phase 6 + Phase 7 dropped Sentry per
  the Render-only rewrite. Render's built-in logs cover the v1.0 needs.
- **No Cloudflare R2 / Vercel Blob.** Image storage is intentionally
  transient (Anthropic call → discard). v2 opt-in image history would
  introduce R2 — until then, no blob store is provisioned.
- **No Vercel Analytics.** Vercel isn't part of the production stack —
  Render hosts both services.
- **No CI gates beyond pytest + pnpm build.** The size-limit and gitleaks-
  CI gates from Phase 1's original plan were dropped in the Render-only
  rewrite. Gitleaks runs as a pre-commit hook locally only.

## Quick verification commands

```bash
# Backend test suite (296 passed, 2 skipped expected — golden-set + live scan).
cd backend && .venv/Scripts/python.exe -m pytest -q

# Frontend test suite (100 passed).
cd frontend && pnpm test --run

# Frontend build (108 static pages).
cd frontend && pnpm build

# Copy audit clean.
python scripts/audit_copy.py --strict

# Working tree clean (only GEMINI.md remains untracked).
git status --short
```
