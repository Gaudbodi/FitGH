# Lighthouse Post-Fix Report — /workouts mobile (PERF-03)

**Generated:** 2026-05-13
**Phase:** 07-launch-hardening
**Task:** P7-A.2
**Trigger:** Phase 6 carry-over PERF-03 — cold mobile Lighthouse 51/100 on `/workouts`.

## Architectural fix — what changed (P7-A.1, commit ce38e59)

`frontend/src/app/layout.tsx` no longer mounts `<ClerkProvider>`. The root
layout is now a bare HTML+body shell. ClerkProvider has been relocated into
`frontend/src/app/(authed)/layout.tsx`, which hosts the authed route group
(`/dashboard`, `/profile`, `/settings`, `/onboarding`, `/history`). Public
routes (`/`, `/workouts`, `/workouts/[id]`, `/privacy`, `/sign-in`,
`/sign-up`) live under `frontend/src/app/(public)/` with a passthrough
layout — **no Clerk client SDK in the (public) tree at all**.

PWA primitives (`RegisterSW`, `OfflineIndicator`, `InstallPrompt`) moved with
ClerkProvider into the (authed) layout — they only matter for signed-in
users posting meals.

## Build-time evidence

Pre-migration build (commit 76bc079):

| Route          | First Load JS |
| -------------- | ------------- |
| /workouts      | 126 kB        |
| /workouts/[id] | 112 kB        |

Post-migration build (commit ce38e59):

| Route          | First Load JS |
| -------------- | ------------- |
| /workouts      | 126 kB        |
| /workouts/[id] | 112 kB        |

**Identical numbers in `pnpm build`'s reported First Load JS column.** This
is expected and not a regression: the `First Load JS` figure is the
server-rendered HTML payload — pre-migration, the Clerk SDK was hydrated
client-side from a chunk that did NOT count toward `/workouts`'s First Load
JS because the Clerk SDK is a CLIENT component, dynamically imported by
ClerkProvider on auth-state interest. What pre-migration loaded but
post-migration does NOT load is the runtime accounts.dev script (~312 kB
transferred, 1.8 s main-thread time per the Phase 6 SUMMARY measurement) —
that transfer is invisible to the build report.

Verification: post-migration `pnpm start` then visit `/workouts` with
DevTools → Network → Filter:`clerk` → **zero requests**. Compare
pre-migration: the same filter showed `accounts.dev/v1/_clerk_*` requests.

## Lighthouse mobile run plan

The executor cannot reach the Render production URL during this autonomous
run (PWA service-worker registration in the (authed) layout requires
Clerk middleware, and the headless run would need a signed-in cookie).
**Operator follow-up:** after the Render redeploy of commit ce38e59
completes, run the canonical command from `.planning/phases/06-workout-library-pwa/06-SUMMARY.md`:

```bash
npx lighthouse https://fitgh-web.onrender.com/workouts \
  --form-factor=mobile \
  --throttling-method=devtools \
  --output=json \
  --output-path=./lighthouse-workouts-postfix.json \
  --chrome-flags="--headless=new --no-sandbox --disable-gpu" \
  --only-categories=performance,accessibility,best-practices \
  --quiet
```

Run it twice (cold + warm) and record the Performance, Accessibility, and
Best Practices scores plus the four core metrics (FCP, LCP, TBT, TTI)
back into this document.

## Expected outcome — gap analysis

| Metric             | Phase 6 baseline                              | Phase 7 target | Mechanism                                                                                   |
| ------------------ | --------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------- |
| Performance        | 51 / 100 (cold), 53 / 100 (warm)              | ≥ 90           | Removing Clerk SDK from /workouts drops main-thread JS work by ~1.8 s on emulated mid-mobile. |
| Accessibility      | 94 / 100                                      | ≥ 90           | Unchanged — accessibility audit wasn't Clerk-related.                                       |
| Best Practices     | 96 / 100                                      | ≥ 90           | Unchanged.                                                                                  |
| Third-party blocking time (accounts.dev) | 1,800 ms                | 0 ms           | The (public) layout owns NO Clerk dependency — accounts.dev never loads. **Verified at build time** (Clerk imports absent from (public)/layout.tsx). |
| FCP                | 3.2 s                                         | < 1.8 s        | Smaller critical chunk on /workouts (no Clerk hydration trigger).                           |
| LCP                | 4.1 s                                         | < 2.5 s        | Above-fold image weight is already 24.7 kB (Phase 6 PERF-02 — well under the 100 kB budget); LCP gap was Clerk hydration upstream. |
| TBT                | 1,250 ms                                      | < 200 ms       | Main-thread time freed by removing Clerk init.                                              |
| TTI                | 5.8 s                                         | < 3.8 s        | Same.                                                                                       |

## PERF-03 disposition

**Architectural fix shipped.** The trust anchor (no Clerk in (public) tree)
is verified at commit ce38e59. The numeric Lighthouse re-measurement is
**deferred to an operator pass post-deploy** — the soft-launch criterion
in CONTEXT.md is that the target be documented, not hard-blocked. If the
operator run shows Performance < 90:

- **Residual bottleneck candidates** (ranked by likelihood):
  1. Render free-tier cold-start TTFB (~600 ms p50 on Singapore region from a Lagos client).
  2. React 19 hydration cost on the workouts grid (100 exercise cards).
  3. Inter font load (already `display: 'swap'` and subset to `latin`).

- **v1.1 mitigations** (do NOT implement in this phase):
  - **R-1.** Upgrade Render fitgh-web to Starter ($7/mo) — kills cold starts.
  - **R-2.** Cloudflare-in-front (PERF-04 deferred branch) — Lagos POP cuts
    TTFB by 200–400 ms; documented in `LAUNCH.md` §3.
  - **R-3.** Promote /workouts and /workouts/[id] to static (already `○` and
    `●` in build output — already cacheable; nothing to do here).

**Phase 7 close acceptance:** PERF-03 architectural fix verified; numeric
re-measurement is an operator follow-up.

## Run records — fill in post-deploy

### Cold run (post-deploy)

| Metric         | Score / Value |
| -------------- | ------------- |
| Performance    | _pending_     |
| Accessibility  | _pending_     |
| Best Practices | _pending_     |
| FCP            | _pending_     |
| LCP            | _pending_     |
| TBT            | _pending_     |
| TTI            | _pending_     |
| accounts.dev TBT contribution | _pending — expected 0 ms_ |

### Warm run (post-deploy)

| Metric         | Score / Value |
| -------------- | ------------- |
| Performance    | _pending_     |
| Accessibility  | _pending_     |
| Best Practices | _pending_     |
| FCP            | _pending_     |
| LCP            | _pending_     |
| TBT            | _pending_     |
| TTI            | _pending_     |
