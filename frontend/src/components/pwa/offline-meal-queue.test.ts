// Phase 6 P6-C.3 — offline-meal-queue TDD RED.
//
// Tests the IndexedDB-backed queue used by the dashboard when the user
// submits a meal POST while offline. Behaviour spec lives in
// 06-PLAN.md → Task P6-C.3 → <behavior>. We import 'fake-indexeddb/auto'
// at the top so idb-keyval (which the module under test uses) has an
// IDBFactory in the test environment.

import "fake-indexeddb/auto";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import {
  clearMealQueue,
  drainMealQueue,
  enqueueMealPost,
  getQueueSize,
  MAX_QUEUE_SIZE,
} from "./offline-meal-queue";

// Suppress Sonner toast side-effects in the test env: the module imports
// `toast` from 'sonner' — under vitest+jsdom that just no-ops, but we
// mock to make any toast call a vi.fn we can introspect when useful.
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}));

beforeEach(async () => {
  await clearMealQueue();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("offline-meal-queue", () => {
  test("test_enqueue_then_drain_replays_request", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    await enqueueMealPost({
      url: "/api/meals",
      body: JSON.stringify({ name: "Banku" }),
      headers: { "Content-Type": "application/json" },
    });
    expect(await getQueueSize()).toBe(1);

    const result = await drainMealQueue();

    expect(result.synced).toBe(1);
    expect(result.retained).toBe(0);
    expect(result.dropped).toBe(0);
    expect(await getQueueSize()).toBe(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = fetchMock.mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(calledUrl).toBe("/api/meals");
    expect(calledInit.method).toBe("POST");
    expect(calledInit.credentials).toBe("include");
    const headers = calledInit.headers as Record<string, string>;
    expect(headers["X-Replayed-Offline"]).toBe("1");
    expect(typeof headers["Idempotency-Key"]).toBe("string");
    expect(headers["Idempotency-Key"].length).toBeGreaterThanOrEqual(32);
  });

  test("test_drain_breaks_on_401_and_retains_queue", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 401 }));
    vi.stubGlobal("fetch", fetchMock);

    await enqueueMealPost({
      url: "/api/meals",
      body: "{}",
      headers: { "Content-Type": "application/json" },
    });
    await enqueueMealPost({
      url: "/api/meals",
      body: "{}",
      headers: { "Content-Type": "application/json" },
    });

    const result = await drainMealQueue();

    expect(result.synced).toBe(0);
    expect(result.retained).toBe(2);
    expect(result.dropped).toBe(0);
    expect(await getQueueSize()).toBe(2);
    // 401 breaks the loop on first hit — only one fetch attempt.
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  test("test_drain_drops_on_400_other_than_401", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 422 }));
    vi.stubGlobal("fetch", fetchMock);

    await enqueueMealPost({
      url: "/api/meals",
      body: "{}",
      headers: { "Content-Type": "application/json" },
    });

    const result = await drainMealQueue();

    expect(result.synced).toBe(0);
    expect(result.retained).toBe(0);
    expect(result.dropped).toBe(1);
    expect(await getQueueSize()).toBe(0);
  });

  test("test_drain_leaves_queued_on_5xx", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);

    await enqueueMealPost({
      url: "/api/meals",
      body: "{}",
      headers: { "Content-Type": "application/json" },
    });

    const result = await drainMealQueue();

    expect(result.synced).toBe(0);
    expect(result.retained).toBe(1);
    expect(result.dropped).toBe(0);
    expect(await getQueueSize()).toBe(1);
  });

  test("test_drain_leaves_queued_on_network_error", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("network down"));
    vi.stubGlobal("fetch", fetchMock);

    await enqueueMealPost({
      url: "/api/meals",
      body: "{}",
      headers: { "Content-Type": "application/json" },
    });

    const result = await drainMealQueue();

    expect(result.synced).toBe(0);
    expect(result.retained).toBe(1);
    expect(result.dropped).toBe(0);
    expect(await getQueueSize()).toBe(1);
  });

  test("test_max_queue_size_drops_oldest", async () => {
    // Stamp a sentinel body on the first entry so we can verify it's gone.
    await enqueueMealPost({
      url: "/api/meals",
      body: JSON.stringify({ sentinel: "first" }),
      headers: { "Content-Type": "application/json" },
    });
    for (let i = 0; i < MAX_QUEUE_SIZE; i++) {
      await enqueueMealPost({
        url: "/api/meals",
        body: JSON.stringify({ i }),
        headers: { "Content-Type": "application/json" },
      });
    }

    expect(await getQueueSize()).toBe(MAX_QUEUE_SIZE);

    // Drain everything as 201; assert the sentinel never reaches fetch.
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    await drainMealQueue();
    const seenBodies = fetchMock.mock.calls.map(
      (c) => (c[1] as RequestInit).body as string,
    );
    expect(seenBodies.some((b) => b.includes('"sentinel":"first"'))).toBe(false);
  });

  test("test_idempotency_key_present_on_each_entry", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    for (let i = 0; i < 3; i++) {
      await enqueueMealPost({
        url: "/api/meals",
        body: JSON.stringify({ i }),
        headers: { "Content-Type": "application/json" },
      });
    }
    await drainMealQueue();

    const keys = fetchMock.mock.calls.map(
      (c) => ((c[1] as RequestInit).headers as Record<string, string>)[
        "Idempotency-Key"
      ],
    );
    expect(keys.length).toBe(3);
    expect(new Set(keys).size).toBe(3); // all distinct
    for (const k of keys) {
      // UUID v4 shape — 8-4-4-4-12 hex with version digit '4'
      expect(k).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
      );
    }
  });

  test("test_get_queue_size_returns_count", async () => {
    expect(await getQueueSize()).toBe(0);
    await enqueueMealPost({
      url: "/api/meals",
      body: "{}",
      headers: {},
    });
    expect(await getQueueSize()).toBe(1);
    await enqueueMealPost({
      url: "/api/meals",
      body: "{}",
      headers: {},
    });
    expect(await getQueueSize()).toBe(2);
  });
});
