# Licences and Attribution

This document records the licences of third-party material redistributed
by, or depended upon by, FitGH. Updated each phase as new dependencies
are added.

Last reviewed: 2026-05-13 (Phase 6 — Workout Library + PWA).

## Exercise Data

FitGH's workout library is sourced from
[Free Exercise DB](https://github.com/yuhonas/free-exercise-db), released
under [The Unlicense](https://unlicense.org/). FitGH redistributes a
curated, re-encoded subset (100 exercises) of Free Exercise DB images and
metadata under this licence.

> This is free and unencumbered software released into the public
> domain.
>
> Anyone is free to copy, modify, publish, use, compile, sell, or
> distribute this software, either in source code form or as a compiled
> binary, for any purpose, commercial or non-commercial, and by any
> means.
>
> [...]
>
> For more information, please refer to <https://unlicense.org/>

The Unlicense does NOT require attribution. FitGH provides attribution
as good-citizen practice in the global site footer (see
`frontend/src/app/layout.tsx`).

## Third-Party Services

| Service | Role | Licence / Terms |
|---|---|---|
| Anthropic (Claude Sonnet 4.6 vision) | Meal-photo kcal estimation | [Anthropic Commercial Terms](https://www.anthropic.com/legal/commercial-terms) |
| MongoDB Atlas | Application data store (users, meals, weights) | [MongoDB Atlas Terms of Service](https://www.mongodb.com/legal/terms-of-service) |
| Clerk | Authentication + session management | [Clerk Terms of Service](https://clerk.com/terms) |
| Render | Backend hosting (Flask web service) | [Render Terms of Service](https://render.com/terms-of-service) |

Each service is used in accordance with its commercial terms; secrets
required for these services live in environment files only (never
committed) per `CLAUDE.md`.

## Open-Source Dependencies

Full dependency trees:

- Frontend: see `frontend/package.json` and `frontend/pnpm-lock.yaml`.
- Backend: see `backend/requirements.txt`.

Each package retains its upstream licence (MIT, Apache 2.0, BSD, ISC,
etc.). FitGH does NOT relicense or sublicense any of these dependencies.
Notable choices include:

- Next.js (MIT), React (MIT), TypeScript (Apache 2.0), Tailwind CSS (MIT).
- shadcn/ui components (MIT) — copy-paste primitives, not an npm package.
- Recharts (MIT) — charting layer used by the dashboard.
- Serwist (MIT) — service-worker tooling added in Phase 6.
- Flask (BSD-3), Pydantic (MIT), PyMongo (Apache 2.0).
- Anthropic Python SDK (MIT).

## FitGH Source Code

TBD — no licence chosen as of 2026-05-13. Source is private until a
licence decision in Phase 7 or later. This file will be updated when a
project licence is selected (Apache 2.0, MIT, or AGPL are the current
shortlist candidates).

## Attribution Required by Source

| Source | Attribution required? | Where attributed |
|---|---|---|
| Free Exercise DB (Unlicense) | No (Unlicense waives it) | Global footer (`frontend/src/app/layout.tsx`) and this file |
| Anthropic | No (commercial terms) | This file |
| MongoDB Atlas | No (commercial terms) | This file |
| Clerk | No (commercial terms) | This file |
| Render | No (commercial terms) | This file |

The MIT/BSD/Apache-licensed npm + pip dependencies include their own
LICENSE files inside their distribution tarballs. FitGH does not extract
or re-bundle these; the user-facing app does not need to surface them
directly per their licence terms (the licence text remains attached to
the source distribution).
