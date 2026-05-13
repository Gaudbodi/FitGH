import withSerwistInit from "@serwist/next";
import type { NextConfig } from "next";

// Phase 6 P6-C.1 — wire Serwist for the PWA.
//
// `swSrc` is `src/app/sw.ts` (P6-C.2). `swDest` lands the compiled SW at
// `public/sw.js` so the runtime can `navigator.serviceWorker.register('/sw.js')`.
//
// `register: false` delegates registration to RegisterSW (P6-C.4) so the
// SW registration co-locates with the offline-meal-queue drain.
//
// `disable` in development avoids SW caching during HMR. Production builds
// emit the SW + precache manifest.
//
// `cacheOnNavigation` precaches the navigation HTML once visited; combined
// with the SWR `/workouts` route rule in sw.ts, this gives the workout
// library a working offline shell after the first online visit.

const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  cacheOnNavigation: true,
  reloadOnOnline: true,
  register: false,
  disable: process.env.NODE_ENV === "development",
});

const nextConfig: NextConfig = {
  /* config options here */
};

export default withSerwist(nextConfig);
