// Phase 6 P6-C.2 — Serwist service-worker route table.
//
// Compiled to public/sw.js by Serwist at build time. Strategies:
//   - /api/*                          → NetworkOnly  (never cache mutating
//                                                     or user-scoped data;
//                                                     offline POSTs queue
//                                                     via offline-meal-queue
//                                                     in P6-C.3, NOT via SW)
//   - /exercises/**/*.webp            → CacheFirst   (30-day TTL, 250 max
//                                                     entries, purge on quota
//                                                     error). The cache-first
//                                                     rule populates entries
//                                                     on first view — no
//                                                     pre-cache of all 100
//                                                     posters per T-06-09
//                                                     (would drain Ghana
//                                                     metered data on install).
//   - /exercises/manifest.json        → StaleWhileRevalidate
//   - /workouts (and /workouts/*)     → StaleWhileRevalidate
//   - everything else                 → Serwist defaultCache (App Shell,
//                                                              fonts, images
//                                                              under /_next)
//
// Order matters: more-specific matchers must come before broader ones.
// /api/ rule is first so it never falls through to the default cache.
// /exercises/*.webp comes before /exercises/manifest.json (both share the
// /exercises/ prefix but the .webp extension is the disambiguator and
// must be checked first).
//
// As in the P6-C.1 stub: we declare WebWorker-side globals inline
// rather than poisoning the whole project's tsconfig `lib` with
// "webworker" (which conflicts with DOM in client components).

import { defaultCache } from "@serwist/next/worker";
import {
  CacheFirst,
  ExpirationPlugin,
  NetworkOnly,
  type PrecacheEntry,
  Serwist,
  type SerwistGlobalConfig,
  StaleWhileRevalidate,
} from "serwist";

interface ServiceWorkerGlobalScopeLite extends SerwistGlobalConfig {
  readonly clients: {
    claim: () => Promise<void>;
  };
  skipWaiting: () => Promise<void>;
  addEventListener: (
    type: string,
    listener: (event: Event) => void,
  ) => void;
  __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
}

declare const self: ServiceWorkerGlobalScopeLite;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: [
    // 1. /api/* — never cache. Mutating endpoints (POST /api/meals,
    //    /api/weights), user-scoped reads, and the live scan-budget all
    //    must reach the network. Offline POSTs are handled by
    //    offline-meal-queue (P6-C.3), not the SW.
    {
      matcher: ({ url }) => url.pathname.startsWith("/api/"),
      handler: new NetworkOnly(),
    },
    // 2. /exercises/**/*.webp — CacheFirst 30 days. ExpirationPlugin caps
    //    storage at 250 entries (~12 MB at 50 kB avg) and purges on quota
    //    error so older posters cycle out gracefully.
    {
      matcher: ({ url }) =>
        url.pathname.startsWith("/exercises/") &&
        url.pathname.endsWith(".webp"),
      handler: new CacheFirst({
        cacheName: "exercise-webp-v1",
        plugins: [
          new ExpirationPlugin({
            maxEntries: 250,
            maxAgeSeconds: 30 * 24 * 60 * 60,
            purgeOnQuotaError: true,
          }),
        ],
      }),
    },
    // 3. /exercises/manifest.json — SWR. Cheap to refresh; we want the
    //    user to see new exercises when the manifest changes, but still
    //    work offline.
    {
      matcher: ({ url }) => url.pathname === "/exercises/manifest.json",
      handler: new StaleWhileRevalidate({
        cacheName: "exercise-manifest-v1",
      }),
    },
    // 4. /workouts and /workouts/[id] — SWR so the workout library shell
    //    is available offline after first visit.
    {
      matcher: ({ url }) => url.pathname.startsWith("/workouts"),
      handler: new StaleWhileRevalidate({
        cacheName: "workouts-html-v1",
      }),
    },
    // 5. Fall through to Serwist's defaultCache (App Shell, static
    //    assets, fonts, /_next/* images).
    ...defaultCache,
  ],
});

serwist.addEventListeners();
