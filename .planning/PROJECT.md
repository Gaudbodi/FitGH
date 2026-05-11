# FitGH

## What This Is

A responsive, interactive fitness webapp built for Ghanaians at home and in the diaspora. Users build a profile (name, sex, height, weight, goal), snap a photo of their meal to get an LLM-vision calorie estimate calibrated against a Ghanaian-food kcal table (jollof, banku, waakye, fufu, kelewele, kontomire, etc.), and follow a workout library filtered by available equipment. The dashboard uses fluid avatar and graph animations to make progress feel tangible.

## Core Value

**Snap a meal, see kcal in seconds, know whether you're hitting your daily target — with food the user actually eats.** If everything else fails, this loop must work.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Hypotheses until shipped and validated. Full breakdown lives in REQUIREMENTS.md. -->

- [ ] User onboarding capturing name, sex, height, weight, age, and primary goal (weight loss OR muscle gain)
- [ ] Profile persistence + progress tracking (weight log, body metrics over time)
- [ ] Daily kcal target derived from profile + goal (Mifflin-St Jeor TDEE ± deficit/surplus); daily protein target for muscle-gain goal
- [ ] Food image capture / upload → LLM-vision dish identification → kcal estimate
- [ ] Ghanaian-food kcal table used to normalise estimates (jollof, banku, waakye, fufu, kelewele, kontomire, red red, kenkey, tilapia, etc.)
- [ ] User can correct dish + portion; correction informs subsequent estimates
- [ ] Daily intake log: meals taken today, running kcal/protein total vs target
- [ ] Workout library filtered by equipment (none / home / full home gym), goal (cut / bulk), and target muscle
- [ ] Workout assets: licensed exercise GIFs (wger, ExerciseDB, MuscleWiki) + curated YouTube embeds (no scraping)
- [ ] Animated dashboard: fluid avatar (Lottie/Rive) reflecting profile + progress, animated charts for weight + kcal balance + streak
- [ ] Data-light delivery: page-weight budgets, lazy assets, image compression, offline cache for workout library

### Out of Scope

<!-- Explicit boundaries. Reasoning included to prevent re-adding. -->

- **Native mobile apps (iOS/Android)** — v1 ships responsive PWA only; native is post-MVP if engagement justifies it.
- **Social feed / following / sharing** — out of v1 to keep scope focused on the core loop.
- **Wearable integrations (Apple Watch, Fitbit, Garmin)** — defer to v2; manual entry covers v1.
- **Coach / 1-on-1 expert features** — not in scope; not the wedge.
- **Payments / subscriptions / freemium gating** — v1 is free; monetisation explored after PMF signal.
- **Scraping Pinterest / Instagram / deluxesupps for workout videos** — breaches platform ToS and creator copyright; flagged and rejected as a source. Licensed alternatives only.
- **Self-trained food-vision model** — too costly for v1; LLM vision + Ghana food table is the chosen path. Revisit if accuracy / cost forces it.

## Context

- **Audience:** Diaspora-aware — Ghanaians in Ghana plus diaspora (UK, US, Canada, Germany). Ghanaian food coverage is the defining differentiator vs. existing Western-centric trackers (MyFitnessPal, Lose It, Cronometer) which under-represent local dishes.
- **Mobile-data reality:** Ghana mobile data is expensive and variable; even mid-tier Android is the dominant device class for the in-Ghana cohort. Data-light is a hard constraint, not a nice-to-have.
- **Asset legality:** Workout content sourced from permissively-licensed libraries (wger has CC-BY-SA exercise data; ExerciseDB; MuscleWiki) plus official YouTube embeds. Pinterest / Instagram scraping is explicitly off the table.
- **Food vision approach:** LLM vision (Claude vision or GPT-4V) is the v1 engine because it generalises across dishes without a training set; we calibrate by passing a Ghana-food kcal table as context and letting users confirm/correct. Cheaper, faster to ship, easier to evolve than a custom model.
- **Stack reality:** Mixed runtime — Next.js (TypeScript) for the responsive web shell, Python (Flask) for the backend API where the LLM vision integration lives, MongoDB Atlas for data. Deployment surface spans Vercel (Next.js) + a Python host (Render / Fly.io / Railway — research will recommend).

## Constraints

- **Tech stack — Frontend:** Next.js (App Router) + TypeScript + Tailwind for the responsive web shell. Lottie / Rive for fluid animations.
- **Tech stack — Backend:** Python (Flask) API service for LLM vision integration and any heavier processing. Reason: Python is the path of least resistance for vision-model and image-pipeline work.
- **Tech stack — Database:** MongoDB Atlas (existing cluster `cluster0.pcd3g.mongodb.net`). Connection string MUST live only in `.env.local` (Next.js) and the backend's env (Flask). Never committed.
- **Security — Secrets:** Database credentials, LLM API keys, and any third-party keys live exclusively in environment files. `.env.local` and `.env` are gitignored from project start. `.env.example` documents required vars without values.
- **Performance — Data-light:** Hard page-weight budgets (TBD per phase). Lazy-load animations; compress and cache imagery; offline cache for workout library.
- **Legal — Workout assets:** Only licence-cleared sources (wger, ExerciseDB, MuscleWiki) plus official YouTube embeds with attribution. No scraping.
- **Privacy:** User images of food are sent to an LLM vision provider; this must be disclosed in onboarding and addressable in a privacy policy. Images are not retained server-side beyond what's needed for the kcal estimate unless the user opts in to a history feature.
- **Timeline / budget:** Solo build, free tiers preferred (Vercel free, MongoDB Atlas free, Render free dyno OK for backend).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Target diaspora-aware audience (Ghana + abroad) | Defining differentiator is Ghanaian-food calorie coverage, which is valuable to both in-Ghana and diaspora users; broader reach without diluting wedge. | — Pending |
| Support weight loss AND muscle gain in v1 | Both are core fitness goals for the audience; covering both materially expands TAM with shared infra (TDEE + macro target). | — Pending |
| Food vision via LLM (Claude/GPT-4V) + Ghana food kcal table | Avoids cost/time of a self-trained model; Ghana table calibrates outputs; user correction loop tightens accuracy over time. | — Pending |
| Workout assets from licensed sources + YouTube embeds only | Scraping Pinterest / Instagram / creator accounts breaches ToS and copyright; licensed sources cover the catalogue need. | ✓ Good |
| Free at v1 launch | Maximises learning and reach; monetisation explored only after PMF signal. | — Pending |
| Strict data-light constraint | Ghana mobile-data cost makes this a first-class concern, not an optimisation. | — Pending |
| Stack: Next.js + Flask + MongoDB Atlas | User-directed; Python for LLM vision ergonomics, Next.js for responsive web shell, MongoDB for flexible profile + meal-log schemas. | — Pending |
| PWA-first; no native apps in v1 | Responsive web ships fastest, covers both in-Ghana and diaspora cohorts on any device. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-11 after initialization*
