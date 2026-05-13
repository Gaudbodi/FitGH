// Phase 6 P6-C.3 — offline-meal-queue (GREEN).
//
// IndexedDB-backed FIFO queue for meal POSTs that fail because the user
// is offline. The dashboard meal-log form catches a network error, calls
// enqueueMealPost, and renders an "Offline — meal will sync on reconnect"
// toast. RegisterSW (P6-C.4) listens to `window.online` and calls
// drainMealQueue, which replays each request oldest-first.
//
// Design notes:
//
//  - Single idb-keyval key `'meal_queue'` holds the whole array. Avoids
//    needing a custom IDBObjectStore + index management for ~50 entries.
//
//  - Idempotency: each enqueue stamps an `Idempotency-Key: <uuid v4>`
//    header. The backend MUST treat a repeated key as the same request
//    and respond with the original result. If we lose connectivity mid
//    POST + retry, the user's meal log doesn't double-count.
//
//  - 401 handling (T-06-02 mitigation): when the server returns 401 while
//    draining, we break the loop and retain the queue. The user is
//    presumed signed out; once they re-authenticate, the next 'online'
//    event drains again. If a different user signs in on the same device,
//    THEIR 401 will also stop the drain — the previous user's bodies are
//    never replayed under a different identity (the backend rejects them
//    because the bearer token doesn't match the queued body's owner).
//
//  - Reentrancy guard: an in-memory `isDraining` flag prevents the
//    'online' listener firing twice in quick succession from racing the
//    drain loop against itself.
//
//  - MAX_QUEUE_SIZE = 50: caps growth. If a user is offline for very
//    long, the OLDEST entries are dropped and we surface a toast so the
//    user knows.

import { del, get, set } from "idb-keyval";
import { toast } from "sonner";

export const MAX_QUEUE_SIZE = 50;
const STORE_KEY = "meal_queue";

export interface QueuedPost {
  url: string;
  body: string;
  headers: Record<string, string>;
}

interface QueueEntry {
  id: string; // UUID v4, also used as Idempotency-Key
  url: string;
  body: string;
  headers: Record<string, string>;
  enqueuedAt: number; // ms epoch
}

export interface DrainResult {
  synced: number;
  retained: number;
  dropped: number;
}

let isDraining = false;

async function readQueue(): Promise<QueueEntry[]> {
  const raw = (await get<QueueEntry[]>(STORE_KEY)) ?? [];
  return Array.isArray(raw) ? raw : [];
}

async function writeQueue(entries: QueueEntry[]): Promise<void> {
  await set(STORE_KEY, entries);
}

function uuidv4(): string {
  // crypto.randomUUID is available in jsdom + modern browsers + Node 19+.
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Last-resort RFC4122-v4 fallback (only hit in extremely old runtimes).
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0"));
  return (
    hex.slice(0, 4).join("") +
    "-" +
    hex.slice(4, 6).join("") +
    "-" +
    hex.slice(6, 8).join("") +
    "-" +
    hex.slice(8, 10).join("") +
    "-" +
    hex.slice(10, 16).join("")
  );
}

export async function enqueueMealPost(post: QueuedPost): Promise<void> {
  const id = uuidv4();
  const entry: QueueEntry = {
    id,
    url: post.url,
    body: post.body,
    headers: {
      ...post.headers,
      "Idempotency-Key": id,
    },
    enqueuedAt: Date.now(),
  };
  const queue = await readQueue();
  queue.push(entry);
  // Cap at MAX_QUEUE_SIZE; drop oldest entries.
  while (queue.length > MAX_QUEUE_SIZE) {
    queue.shift();
    toast.warning(
      "Offline meal queue full — earliest pending meal dropped",
    );
  }
  await writeQueue(queue);
}

export async function drainMealQueue(): Promise<DrainResult> {
  if (isDraining) {
    return { synced: 0, retained: 0, dropped: 0 };
  }
  isDraining = true;
  let synced = 0;
  let dropped = 0;
  let auth_break = false;
  try {
    let queue = await readQueue();
    while (queue.length > 0) {
      const entry = queue[0];
      let response: Response | null = null;
      let networkError = false;
      try {
        response = await fetch(entry.url, {
          method: "POST",
          body: entry.body,
          headers: {
            ...entry.headers,
            "X-Replayed-Offline": "1",
          },
          credentials: "include",
        });
      } catch {
        networkError = true;
      }

      if (networkError) {
        // Transient — leave queued, retry on next 'online' event.
        break;
      }

      const status = response!.status;
      if (status >= 200 && status < 300) {
        synced += 1;
        queue.shift();
        await writeQueue(queue);
        queue = await readQueue(); // re-read for safety vs. concurrent edits
      } else if (status === 401) {
        // Auth gate — keep the queue intact; user needs to re-auth.
        auth_break = true;
        break;
      } else if (status >= 400 && status < 500) {
        // Permanent client error — body is bad, drop it.
        dropped += 1;
        queue.shift();
        await writeQueue(queue);
        queue = await readQueue();
      } else {
        // 5xx or other server error — transient, leave queued.
        break;
      }
    }

    const retained = (await readQueue()).length;

    if (synced > 0) {
      toast.success(
        `Synced ${synced} offline meal${synced === 1 ? "" : "s"}`,
      );
    }
    if (dropped > 0) {
      toast.error(
        `Could not sync ${dropped} meal${dropped === 1 ? "" : "s"} — entry rejected by server`,
      );
    }
    if (auth_break) {
      toast.info("Please sign in to send your offline meals");
    }

    return { synced, retained, dropped };
  } finally {
    isDraining = false;
  }
}

export async function getQueueSize(): Promise<number> {
  const queue = await readQueue();
  return queue.length;
}

export async function clearMealQueue(): Promise<void> {
  await del(STORE_KEY);
}
