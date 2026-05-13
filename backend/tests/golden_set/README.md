# Vision golden set — Phase 7 hook

This directory is intentionally empty as of Phase 4. It exists so that
Phase 7's accuracy work has a stable target path.

## Plan for Phase 7

Drop 30 representative meal photos here as `{nn}-{slug}.jpg` (e.g.
`01-jollof-with-chicken.jpg`). Each photo's expected components live in
`{nn}-{slug}.expected.json` matching the `VisionResponse` schema
(`shared/schemas/vision-response.schema.json`).

Phase 7 will add `backend/tests/golden_set/test_golden_set.py` that, when
invoked with `RUN_GOLDEN_SET=1`, calls real Anthropic Sonnet 4.6 for each
photo and reports per-component MAPE plus an aggregate MAPE. Target
< 25 % MAPE on the env-pinned model (`LLM_VISION_MODEL=claude-sonnet-4-6`).

The set MUST be re-run on:

  - Any bump of `LLM_VISION_MODEL` in env / `app/config.py`.
  - Any change to `MODEL_PRICING_PER_1K` in `app/lib/vision.py` (price
    bumps usually coincide with model rev releases).
  - Any non-trivial change to `build_system_prompt` in
    `app/lib/vision.py` (the cached block hash will shift; re-prove
    accuracy stays in bounds).

## CI policy

This test is `@pytest.mark.skipif(os.environ.get("RUN_GOLDEN_SET") != "1", ...)`
gated. CI never runs it. The operator runs it locally after key changes
above; expected cost is ~30 calls × $0.005 ≈ $0.15.

For now this directory is intentionally empty.
