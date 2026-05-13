// Phase 6 P6-C.1 — Serwist swSrc stub.
//
// This file is replaced by the real route table in P6-C.2. The stub keeps
// `pnpm build` green at the P6-C.1 commit boundary (Serwist compiles
// swSrc → swDest at build time and would fail on a missing path). The
// stub installs no fetch handler, so production builds at this commit
// are effectively no-op service workers; the next commit (P6-C.2) wires
// the full route table.
//
// We deliberately do NOT use `/// <reference no-default-lib="true" />` or
// add `"webworker"` to the global tsconfig `lib` array — both would
// poison the rest of the app's type-checking (no-default-lib leaks file
// boundaries in incremental builds, and "webworker" globally would
// conflict with DOM's overlapping symbols in client components). Instead,
// we declare the few SW-specific globals we use inline.

import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";

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

// Reference __SW_MANIFEST so Serwist's build-time scan finds it (required
// even in this stub; the precache injection point gets a real precache
// list in P6-C.2).
const precacheEntries = self.__SW_MANIFEST;
void precacheEntries;

self.addEventListener("install", () => {
  void self.skipWaiting();
});
self.addEventListener("activate", () => {
  void self.clients.claim();
});
