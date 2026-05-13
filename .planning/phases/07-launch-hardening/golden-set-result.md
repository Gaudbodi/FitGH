# Golden-set run — Phase 7 P7-D.3

**Run date:** 2026-05-13
**Run mode:** deterministic-fake (ANTHROPIC_API_KEY stub from conftest.py;
`GOLDEN_SET_REAL` not set)
**Command:**
```bash
cd backend && RUN_GOLDEN_SET=1 \
  .venv/Scripts/python.exe -m pytest tests/golden_set/test_golden_vision.py -v -s
```

## Per-entry table

| id                          | expected_kcal | predicted_kcal | MAPE % | dish_accuracy |
| --------------------------- | ------------: | -------------: | -----: | ------------: |
| 01-jollof-with-chicken      |           830 |            830 |   0.00 |          1.00 |
| 02-banku-tilapia-shito      |           640 |            640 |   0.00 |          1.00 |
| 03-waakye                   |           500 |            500 |   0.00 |          1.00 |
| 04-fufu-light-soup          |           580 |            580 |   0.00 |          1.00 |
| 05-kelewele                 |           425 |            425 |   0.00 |          1.00 |
| 06-red-red                  |           550 |            550 |   0.00 |          1.00 |
| 07-kontomire-stew           |           610 |            610 |   0.00 |          1.00 |
| 08-omotuo-groundnut-soup    |           690 |            690 |   0.00 |          1.00 |
| 09-tuo-zaafi                |           730 |            730 |   0.00 |          1.00 |
| 10-kenkey-fried-fish        |           720 |            720 |   0.00 |          1.00 |

## Aggregate

- **Mean MAPE:** **0.00 %** — well under the 25 % target (passes by
  construction in deterministic-fake mode).
- **Mean dish accuracy:** **1.00** — well above the 0.70 target (passes by
  construction in deterministic-fake mode).
- **Outcome:** PASS.

## What deterministic-fake mode validates

The fake mode validates the **shape of the harness**:

- All 10 photos on disk are valid JPEGs the harness can `open(path,
  'rb').read()` without crashing.
- The manifest schema is consistent across all 10 entries.
- The per-entry kcal-band and dish-name aggregation logic computes
  correctly (when input matches expectation exactly, MAPE = 0 and
  dish_accuracy = 1).
- The skipif gate correctly suppresses CI runs unless RUN_GOLDEN_SET=1.

It does NOT validate the Claude Sonnet 4.6 vision model's accuracy on
Ghana-food images — that requires real photos and real API calls.

## Next step — operator follow-up

Real-Anthropic re-run is documented in `LAUNCH.md` §5. The expected cost
for v1.0 placeholder photos is ~$0.005 × 10 = **$0.05** total. The
expected outcome with these solid-colour 64×64 placeholders is FAIL on
MAPE — Claude will not be able to derive jollof-with-chicken from a red
square — that's the v1.1 operator task: replace each `source:
"placeholder"` photo in `backend/tests/golden_set/manifest.json` with a
real Ghana-food image (10–30 entries) and re-run.

When real photos land:

```bash
cd backend && RUN_GOLDEN_SET=1 GOLDEN_SET_REAL=1 \
  ANTHROPIC_API_KEY=sk-ant-... \
  .venv/Scripts/python.exe -m pytest tests/golden_set/test_golden_vision.py -v -s \
  2>&1 | tee .planning/phases/07-launch-hardening/golden-set-result-real.md
```

The < 25 % MAPE target then becomes meaningful. If it's not hit, triage:

1. Are kcal bands too tight in `manifest.json`? Loosen to ±30 % of midpoint.
2. Is the Ghana table missing a key dish (e.g. waakye-with-spaghetti)? Add
   to `seeds/ghana_foods.json` and re-run.
3. Is the system prompt missing a calibration example? Edit
   `app/lib/vision.build_system_prompt` and re-run (NB: this triggers the
   prompt-cache invalidation hash bump documented in
   `backend/tests/golden_set/README.md`).
