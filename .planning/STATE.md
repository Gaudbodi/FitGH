# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-11)

**Core value:** Snap a meal, see kcal in seconds, know whether you're hitting your daily target — with food the user actually eats.
**Current focus:** Phase 1 — Walking Skeleton

## Current Position

Phase: 1 of 7 (Walking Skeleton)
Plan: 0 of TBD in current phase
Status: Roadmap drafted; ready to plan Phase 1
Last activity: 2026-05-11 — Roadmap created by gsd-roadmapper; 65 v1 requirements mapped across 7 vertical-MVP phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: 0 h

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| — | — | — | — |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion.*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table and research/SUMMARY.md "Locked Stack Decisions". Most recent / load-bearing for current work:

- Phase 1: Walking Skeleton convention — emit `SKELETON.md` in the phase directory (template at `$HOME/.claude/get-shit-done/references/skeleton-template.md`).
- Phase 1: Backend on **Fly.io JNB** always-on `shared-cpu-1x` 512 MB + **static egress IP** pinned in Atlas allowlist.
- Phase 1: **Clerk** for auth (50k MAU free; networkless JWT verify on Flask).
- Phase 1: CI **bundle-size gate** (size-limit ≤ 180 KB First Load JS) + **gitleaks** pre-commit from commit 1.
- Phase 3: **Multi-component `meals` schema from day 1** (`components: []`). Single `dish_name` is forbidden — this is the most expensive schema mistake.
- Phase 4: **Claude Sonnet 4.6** via Anthropic SDK with prompt caching; pin in env; **no image storage** in v1.
- Phase 4: **Per-user 8/day cap** + **global $/day breaker** + **Sentry alert at $/DAU/day > $0.05**.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- **Rive designer pipeline** (Phase 5 gate) — decide by end of Phase 2 whether to contract a Rive artist (~£200–500) or ship static SVG and animate in v1.1.
- **Static egress IP cost on Fly.io 2026** — verify add-on price during Phase 1 setup; fallback is `0.0.0.0/0` + strong DB password (dev only) if > $5/mo.
- **MongoDB Atlas password rotation** — flagged as exposed in chat per PITFALLS M-5; must be rotated before Phase 1 deploy.

## Deferred Items

Items acknowledged and carried forward:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| v2 | Opt-in meal-image history (Cloudflare R2, 90-day TTL) | Post-MVP | Phase 4 |
| v2 | Wearables (Apple Health, Google Fit, step counter) | Post-MVP | — |
| v2 | Twi / Ga / Ewe localisation | Post-MVP | — |
| v2 | Payments / paid tier | Post-MVP | — |
| v2 | Push notifications + friends/leaderboards | Post-MVP | — |

## Session Continuity

Last session: 2026-05-11
Stopped at: ROADMAP.md + STATE.md emitted; REQUIREMENTS.md traceability table populated; Phase 1 SKELETON.md scaffolded.
Resume file: None — next step is `/gsd-plan-phase 1` (or discuss-phase if enabled).
