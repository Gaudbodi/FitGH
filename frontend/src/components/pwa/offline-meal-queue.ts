// Phase 6 P6-C.3 — TDD RED stub.
//
// Real implementation lands in the GREEN commit. This stub satisfies
// type-checking and import resolution but does NOT implement the queue
// behaviour, so all 8 tests in offline-meal-queue.test.ts fail.

export const MAX_QUEUE_SIZE = 50;

export interface QueuedPost {
  url: string;
  body: string;
  headers: Record<string, string>;
}

export interface DrainResult {
  synced: number;
  retained: number;
  dropped: number;
}

export async function enqueueMealPost(_post: QueuedPost): Promise<void> {
  throw new Error("offline-meal-queue: not yet implemented (RED phase)");
}

export async function drainMealQueue(): Promise<DrainResult> {
  throw new Error("offline-meal-queue: not yet implemented (RED phase)");
}

export async function getQueueSize(): Promise<number> {
  throw new Error("offline-meal-queue: not yet implemented (RED phase)");
}

export async function clearMealQueue(): Promise<void> {
  throw new Error("offline-meal-queue: not yet implemented (RED phase)");
}
