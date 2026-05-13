// Phase 6 P6-C.1 — Next 15 native PWA manifest file convention.
//
// Next 15's App Router auto-routes `src/app/manifest.ts` (default export
// of MetadataRoute.Manifest) to `/manifest.webmanifest` and injects the
// `<link rel="manifest">` into <head> automatically — no manual edit to
// layout.tsx needed.
//
// theme_color matches the emerald used on primary CTAs (Tailwind
// emerald-500 = #10b981). start_url '/dashboard' so an installed-app
// launcher tap lands the user on the meal-snap home rather than the
// marketing root.

import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "FitGH",
    short_name: "FitGH",
    description:
      "Snap a meal, see kcal — track Ghanaian food and workouts.",
    start_url: "/dashboard",
    display: "standalone",
    orientation: "portrait-primary",
    background_color: "#ffffff",
    theme_color: "#10b981",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
