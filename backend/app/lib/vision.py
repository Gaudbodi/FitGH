"""Pure Python helpers for the Phase 4 vision pipeline.

Phase 4 Plan 04 — Task P4-A.2.

These helpers are imported by `app/routes/scan.py` (P4-B.1):
  - build_system_prompt   — Ghana-foods reference table + user-history
                            block, with the prompt-cache marker on the
                            stable cached block.
  - build_user_message    — image-then-text content array for the
                            Anthropic SDK's messages[].content shape.
  - parse_tool_use_response — extracts the first ToolUseBlock named
                            `report_meal_components` from the SDK's
                            response and validates it against
                            VisionResponse.
  - table_rematch         — re-matches each LLM-reported component name
                            against ghana_foods (D-TABLE-WINS): the
                            persisted `kcal_point` is recomputed from the
                            table's kcal_per_100g; the LLM's range stays
                            as advisory data for the FE chip display.
  - compute_cost_usd      — Sonnet 4.6 token-priced cost calculation. Bump
                            MODEL_PRICING_PER_1K alongside any
                            LLM_VISION_MODEL change and re-run the
                            golden set (CONTEXT D-VISION-MODEL-PIN).

Pure Python — only stdlib + Pydantic + `app.lib.meals`. NO Flask. NO
direct Mongo. NO Anthropic SDK import at module top (parse function
duck-types on the response shape so respx tests don't need the SDK
imported either).

`MODEL_PRICING_PER_1K` is USD per 1000 tokens as of 2026-05-13 (Sonnet
4.6 list pricing per https://platform.claude.com/docs/en/build-with-claude/pricing):

  input (cache hit, 5-min ephemeral cache):    $0.0003 / 1k
  input (cache miss / first call):             $0.003  / 1k
  output:                                      $0.015  / 1k
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.lib.meals import (
    compute_kcal_for_component,
    compute_protein_for_component,
)
from app.models.vision import VisionComponentRaw, VisionResponse

MODEL_PRICING_PER_1K: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {
        "input_cached": 0.0003,
        "input_uncached": 0.003,
        "output": 0.015,
    }
}


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------


def _render_ghana_table(ghana_foods: list[dict]) -> str:
    """Render the Ghana foods reference as a markdown-ish table for the LLM."""
    lines = [
        "# Ghana food reference (per 100g, FAO/INFOODS WAFCT-sourced):",
        "",
        "| Name | kcal/100g | Aliases |",
        "|------|-----------|---------|",
    ]
    for food in ghana_foods:
        name = food.get("name", "")
        kcal = food.get("kcal_per_100g", 0)
        alts = ", ".join(food.get("alt_names") or []) or "—"
        lines.append(f"| {name} | {kcal:.0f} | {alts} |")
    return "\n".join(lines)


def _render_user_history(corrections: list[dict]) -> str:
    """Render the user's recent corrections as a free-text 'history' block.

    Empty list -> empty string. Stable structure: the FE chip-edit emits
    `corrected_name = None` when only portion changed, so we render
    "kept name '<original>' but portion <a>g -> <b>g" in that case.
    """
    if not corrections:
        return ""
    lines = ["# User correction history (last 20, newest first):"]
    for c in corrections:
        orig_name = c.get("original_name") or "?"
        corr_name = c.get("corrected_name")
        orig_p = c.get("original_portion_g")
        corr_p = c.get("corrected_portion_g")
        if corr_name and corr_name != orig_name:
            lines.append(
                f"- '{orig_name}' -> '{corr_name}' "
                f"(portion {orig_p}g -> {corr_p}g)"
            )
        else:
            lines.append(
                f"- kept '{orig_name}' but portion {orig_p}g -> {corr_p}g"
            )
    return "\n".join(lines)


def build_system_prompt(
    ghana_foods: list[dict], user_corrections: list[dict]
) -> dict[str, Any]:
    """Build the Anthropic `system` payload + a prompt_hash for provenance.

    Returns:
        {
          "system": [
            {"type": "text", "text": <cached_text>, "cache_control": {...}},
            {"type": "text", "text": <user_history_text>},
          ],
          "prompt_hash": <sha256 hex digest>,
        }

    The cached block is identical across users for a given `ghana_foods`
    snapshot, so Anthropic's ephemeral cache hits on it (~75% input-token
    discount on subsequent calls within the 5-minute TTL).

    `prompt_hash` covers BOTH blocks so two users on the same Ghana
    snapshot but different correction histories get distinct hashes —
    useful for golden-set provenance.
    """
    cached_text = (
        f"{_render_ghana_table(ghana_foods)}\n\n"
        "# Instructions:\n"
        "When you see a plate, name each visible component separately. "
        "Match each to the Ghana food reference table above when "
        "confident; otherwise describe the dish in plain English. Report "
        "via the `report_meal_components` tool. Always return a kcal "
        "range (kcal_low, kcal_high) and a kcal_point inside that range "
        "— never just a single point. Estimate portion_g_estimate based "
        "on visible plate-relative sizing. Components 1..10 only; merge "
        "small garnishes into the nearest main item."
    )
    user_history_text = _render_user_history(user_corrections)

    hash_payload = json.dumps(
        [cached_text, user_history_text], sort_keys=True
    ).encode("utf-8")
    prompt_hash = hashlib.sha256(hash_payload).hexdigest()

    return {
        "system": [
            {
                "type": "text",
                "text": cached_text,
                "cache_control": {"type": "ephemeral"},
            },
            {"type": "text", "text": user_history_text},
        ],
        "prompt_hash": prompt_hash,
    }


# ---------------------------------------------------------------------------
# build_user_message
# ---------------------------------------------------------------------------


def build_user_message(image_b64: str, mime: str = "image/jpeg") -> list[dict]:
    """Build the messages[0].content value for an Anthropic vision call.

    Image MUST come first, then the text instruction — Anthropic's
    prompt-engineering guide states the image is anchored before the
    request text for best attention behaviour.
    """
    return [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime,
                "data": image_b64,
            },
        },
        {
            "type": "text",
            "text": (
                "Identify each food component on this plate and report "
                "via the `report_meal_components` tool. Use the Ghana "
                "food reference table from the system prompt."
            ),
        },
    ]


# ---------------------------------------------------------------------------
# parse_tool_use_response
# ---------------------------------------------------------------------------


def parse_tool_use_response(raw_message: Any) -> VisionResponse:
    """Extract the first matching ToolUseBlock and validate it.

    Walks `raw_message.content`. The content blocks may be Anthropic SDK
    types (`anthropic.types.ToolUseBlock`) or simple SimpleNamespace
    objects (used in tests) — both have `.type`, `.name`, `.input` attrs.

    Raises:
        ValueError("no_tool_use_block") — no matching ToolUseBlock.
        pydantic.ValidationError         — block.input fails VisionResponse
                                           validation. Caller retries once.
    """
    for block in raw_message.content:
        block_type = getattr(block, "type", None)
        if block_type != "tool_use":
            continue
        if getattr(block, "name", None) != "report_meal_components":
            continue
        payload = getattr(block, "input", None)
        if payload is None:
            continue
        return VisionResponse.model_validate(payload)
    raise ValueError("no_tool_use_block")


# ---------------------------------------------------------------------------
# table_rematch
# ---------------------------------------------------------------------------


def _rank_food(food: dict, q: str) -> tuple[int, str]:
    """Same algorithm as app.routes.foods._rank (Phase 3): exact > startswith
    > contains > alt-name contains."""
    name_l = food["name"].lower()
    if name_l == q:
        return (0, name_l)
    if name_l.startswith(q):
        return (1, name_l)
    if q in name_l:
        return (2, name_l)
    return (3, name_l)


def _find_match(name: str, foods: list[dict]) -> dict | None:
    """Return the best matching food (substring on name + alt_names) or None."""
    q = name.lower().strip()
    if not q:
        return None
    candidates: list[dict] = []
    for food in foods:
        if q in food["name"].lower():
            candidates.append(food)
            continue
        for alt in food.get("alt_names") or []:
            if q in alt.lower():
                candidates.append(food)
                break
    # Reverse: also accept the case where the table-name is a substring of q
    # (e.g. q = "party rice on a plate" matches "Jollof rice" via "party rice"
    # alias, OR "Plain boiled rice" via "rice" — but the alt_name match above
    # covers the alias path. The name-in-q case below covers "Jollof" being
    # a substring of "Jollof rice with chicken").
    if not candidates:
        for food in foods:
            if food["name"].lower() in q:
                candidates.append(food)
                continue
            for alt in food.get("alt_names") or []:
                if alt.lower() in q:
                    candidates.append(food)
                    break
    if not candidates:
        return None
    candidates.sort(key=lambda f: _rank_food(f, q))
    return candidates[0]


def table_rematch(
    vision_components: list[VisionComponentRaw], ghana_foods_coll: Any
) -> list[dict]:
    """Re-match each VisionComponentRaw against ghana_foods.

    Returns a list of persisted-shape Component dicts (same shape Phase 3
    writes to `meals.components`). The table value WINS on `kcal_point`
    when a match is found; on no match the LLM's range midpoint is used.

    `ghana_foods_coll` is a PyMongo / mongomock Collection — we read all
    25 entries once per call (cheap; ~25 docs).
    """
    foods = list(ghana_foods_coll.find({}, {"_id": 0}))
    out: list[dict] = []
    for vc in vision_components:
        match = _find_match(vc.name, foods)
        if match is not None:
            out.append(
                {
                    "name": match["name"],
                    "matched_food_id": match["food_id"],
                    "portion_g": vc.portion_g_estimate,
                    "kcal_low": vc.kcal_low,
                    "kcal_high": vc.kcal_high,
                    "kcal_point": compute_kcal_for_component(
                        match["kcal_per_100g"], vc.portion_g_estimate
                    ),
                    "protein_g_point": compute_protein_for_component(
                        match["protein_g_per_100g"], vc.portion_g_estimate
                    ),
                    "confidence": vc.confidence,
                    "source": "llm_then_table_rematch",
                }
            )
        else:
            midpoint = round((vc.kcal_low + vc.kcal_high) / 2)
            out.append(
                {
                    "name": vc.name,
                    "matched_food_id": None,
                    "portion_g": vc.portion_g_estimate,
                    "kcal_low": vc.kcal_low,
                    "kcal_high": vc.kcal_high,
                    "kcal_point": midpoint,
                    "protein_g_point": 0,
                    "confidence": vc.confidence,
                    "source": "user_corrected",
                }
            )
    return out


# ---------------------------------------------------------------------------
# compute_cost_usd
# ---------------------------------------------------------------------------


def compute_cost_usd(
    input_cached_tokens: int,
    input_uncached_tokens: int,
    output_tokens: int,
    model: str = "claude-sonnet-4-6",
) -> float:
    """Compute total USD cost of one Anthropic Messages call.

    Pricing pinned in MODEL_PRICING_PER_1K. Bumping LLM_VISION_MODEL
    requires bumping the pricing table here — KeyError on unknown model
    is intentional (fail loud).

    Returns:
        Cost in USD rounded to 6 decimal places.
    """
    pricing = MODEL_PRICING_PER_1K[model]  # KeyError -> caller bug
    cost = (
        (input_cached_tokens / 1000) * pricing["input_cached"]
        + (input_uncached_tokens / 1000) * pricing["input_uncached"]
        + (output_tokens / 1000) * pricing["output"]
    )
    return round(cost, 6)


__all__ = [
    "MODEL_PRICING_PER_1K",
    "build_system_prompt",
    "build_user_message",
    "compute_cost_usd",
    "parse_tool_use_response",
    "table_rematch",
]
