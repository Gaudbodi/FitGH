"""FitGH seed data package.

Phase 3 Plan 03 — Task P3-A.4.

Read-only catalogue data lives here. The 25-entry ghana_foods.json catalogue
is sourced from:

  - FAO / INFOODS West African Food Composition Table (WAFCT):
    https://www.fao.org/3/i2698b/i2698b.pdf
  - USDA FoodData Central SR-Legacy (for ingredients absent from WAFCT,
    used as a fall-back in composite recipe summation):
    https://fdc.nal.usda.gov/

Provenance per entry is captured via the `source` field:
  - "wafct"            -> direct WAFCT row (high confidence).
  - "wafct_composite"  -> sum of WAFCT (+ optional USDA) ingredients per a
                          typical Ghanaian recipe; medium confidence.
  - "usda"             -> sole USDA SR-Legacy ingredient row used as a
                          fall-back when no WAFCT row exists.

Numeric accuracy is editorial — the catalogue is repo-versioned and an
operator can edit the JSON + re-run `scripts.seed_ghana_foods` to update.
"""
