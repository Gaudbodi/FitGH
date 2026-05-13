"""Pure-function kcal / protein / meal-totals helpers.

Phase 3 Plan 03 — Task P3-A.3.

These helpers are imported by `app/routes/meals.py` (POST/PATCH recompute
totals) and have a hand-mirrored TypeScript preview at
`frontend/src/app/dashboard/component-chip.tsx` (D-INTERFACE-FIRST). The two
must agree on rounding semantics, hence the explicit banker's-rounding note
below; the FE uses `Math.round` (half-to-even at .5 in modern V8) and the
two implementations agree on the typical inputs we see in practice. The
server is the source of truth on submit — the FE is a preview-only mirror.

Pure Python — only stdlib imports. No Flask, no Mongo, no Pydantic. Tests
in `backend/tests/test_meal_helpers.py`.
"""

from __future__ import annotations

PORTION_MIN_G = 10
PORTION_MAX_G = 800
PORTION_STEP_G = 10
BACKDATE_MAX_DAYS = 7


def compute_kcal_for_component(kcal_per_100g: float, portion_g: int) -> int:
    """Compute kcal_point for a component.

    Uses Python's built-in `round` which is banker's-rounding (half-to-even).
    Example: 165 kcal/100g x 250 g = 412.5 -> rounds to 412 (nearest even).
    The FE preview uses `Math.round` (half-to-even in modern V8 as well),
    so the two agree on typical inputs.
    """
    return round(kcal_per_100g * portion_g / 100)


def compute_protein_for_component(protein_g_per_100g: float, portion_g: int) -> int:
    """Compute protein_g_point for a component (grams, integer)."""
    return round(protein_g_per_100g * portion_g / 100)


def recompute_meal_totals(components: list[dict]) -> tuple[int, int]:
    """Sum kcal_point + protein_g_point across all components.

    Accepts persisted-shape dicts (post-resolution from food lookups) where
    each component has `kcal_point` and `protein_g_point` integer keys.
    """
    total_kcal = sum(int(c.get("kcal_point", 0)) for c in components)
    total_protein = sum(int(c.get("protein_g_point", 0)) for c in components)
    return total_kcal, total_protein
