"""Tests for app.lib.vision pure helpers (Phase 4, Task P4-A.2).

Covers:
  - build_system_prompt   — cache_control marker, user-history block,
                            Ghana table coverage.
  - build_user_message    — image-first then text content order.
  - parse_tool_use_response — first matching ToolUseBlock extraction,
                            error paths.
  - table_rematch         — table wins kcal_point on match, LLM-midpoint
                            fallback on miss, correct `source` per path.
  - compute_cost_usd      — Sonnet 4.6 pricing arithmetic + unknown-model
                            fail-loud.
"""

from __future__ import annotations

from types import SimpleNamespace

import mongomock
import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ghana_foods_seed():
    """Subset of WAFCT seed mirroring the canonical jollof + chicken entries."""
    return [
        {
            "food_id": "gh-jollof-rice",
            "name": "Jollof rice",
            "alt_names": ["jollof", "party rice"],
            "kcal_per_100g": 165.0,
            "protein_g_per_100g": 4.0,
            "fat_g_per_100g": 5.5,
            "carbs_g_per_100g": 26.0,
            "portion_defaults": [{"label": "1 plate", "grams": 350}],
            "category": "staple",
            "source": "wafct_composite",
            "source_confidence": "medium",
        },
        {
            "food_id": "gh-grilled-chicken",
            "name": "Grilled chicken",
            "alt_names": ["chicken", "chicken thigh", "chicken breast"],
            "kcal_per_100g": 195.0,
            "protein_g_per_100g": 30.0,
            "fat_g_per_100g": 8.0,
            "carbs_g_per_100g": 0.0,
            "portion_defaults": [{"label": "1 piece", "grams": 120}],
            "category": "protein",
            "source": "wafct",
            "source_confidence": "high",
        },
        {
            "food_id": "gh-kontomire",
            "name": "Kontomire stew",
            "alt_names": ["kontomire", "palava sauce"],
            "kcal_per_100g": 110.0,
            "protein_g_per_100g": 4.5,
            "fat_g_per_100g": 7.0,
            "carbs_g_per_100g": 7.0,
            "portion_defaults": [{"label": "1 cup", "grams": 200}],
            "category": "soup_stew",
            "source": "wafct_composite",
            "source_confidence": "medium",
        },
    ]


@pytest.fixture
def ghana_foods_coll(ghana_foods_seed):
    """Mongomock ghana_foods collection seeded with the above."""
    coll = mongomock.MongoClient()["fitgh"]["ghana_foods"]
    coll.insert_many([dict(f) for f in ghana_foods_seed])
    return coll


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------


def test_build_system_prompt_emits_cache_control_on_first_block(ghana_foods_seed):
    from app.lib.vision import build_system_prompt

    result = build_system_prompt(ghana_foods_seed, [])
    assert isinstance(result, dict)
    blocks = result["system"]
    assert isinstance(blocks, list)
    assert blocks[0]["type"] == "text"
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    # The user-history block (second block) is NOT cached.
    assert "cache_control" not in blocks[1]


def test_build_system_prompt_empty_corrections_emits_empty_user_history(
    ghana_foods_seed,
):
    from app.lib.vision import build_system_prompt

    result = build_system_prompt(ghana_foods_seed, [])
    blocks = result["system"]
    # User-history block exists but its text is empty (or near-empty
    # placeholder). Stable structure is the contract.
    assert blocks[1]["type"] == "text"
    assert blocks[1]["text"] == ""


def test_build_system_prompt_includes_all_ghana_foods(ghana_foods_seed):
    from app.lib.vision import build_system_prompt

    result = build_system_prompt(ghana_foods_seed, [])
    cached_text = result["system"][0]["text"]
    for food in ghana_foods_seed:
        assert food["name"] in cached_text


def test_build_system_prompt_renders_user_corrections(ghana_foods_seed):
    from app.lib.vision import build_system_prompt

    corrections = [
        {
            "original_name": "rice",
            "corrected_name": "Jollof rice",
            "original_portion_g": 200,
            "corrected_portion_g": 350,
        },
        {
            "original_name": "Chicken",
            "corrected_name": "Grilled chicken",
            "original_portion_g": 100,
            "corrected_portion_g": 120,
        },
    ]
    result = build_system_prompt(ghana_foods_seed, corrections)
    user_history = result["system"][1]["text"]
    # Both corrections must surface in the un-cached block.
    assert "rice" in user_history
    assert "Jollof rice" in user_history
    assert "Grilled chicken" in user_history


def test_build_system_prompt_exposes_prompt_hash(ghana_foods_seed):
    from app.lib.vision import build_system_prompt

    a = build_system_prompt(ghana_foods_seed, [])
    b = build_system_prompt(ghana_foods_seed, [])
    # Determinism: same inputs → same hash (sha256 hex).
    assert a["prompt_hash"] == b["prompt_hash"]
    assert len(a["prompt_hash"]) == 64
    # Different user corrections → different hash.
    c = build_system_prompt(
        ghana_foods_seed,
        [
            {
                "original_name": "rice",
                "corrected_name": "Jollof rice",
                "original_portion_g": 200,
                "corrected_portion_g": 350,
            }
        ],
    )
    assert a["prompt_hash"] != c["prompt_hash"]


# ---------------------------------------------------------------------------
# build_user_message
# ---------------------------------------------------------------------------


def test_build_user_message_returns_image_then_text():
    from app.lib.vision import build_user_message

    content = build_user_message("BASE64DATA", "image/jpeg")
    assert isinstance(content, list)
    assert content[0]["type"] == "image"
    assert content[0]["source"]["type"] == "base64"
    assert content[0]["source"]["media_type"] == "image/jpeg"
    assert content[0]["source"]["data"] == "BASE64DATA"
    assert content[1]["type"] == "text"
    assert "report_meal_components" in content[1]["text"]


# ---------------------------------------------------------------------------
# parse_tool_use_response
# ---------------------------------------------------------------------------


def _make_tool_use_block(name: str, input_dict: dict):
    return SimpleNamespace(type="tool_use", name=name, input=input_dict)


def _make_text_block(text: str):
    return SimpleNamespace(type="text", text=text)


def test_parse_tool_use_response_extracts_first_matching_block():
    from app.lib.vision import parse_tool_use_response

    payload = {
        "components": [
            {
                "name": "Jollof rice",
                "kcal_low": 400,
                "kcal_high": 600,
                "kcal_point": 500,
                "portion_g_estimate": 300,
                "confidence": 0.8,
            }
        ]
    }
    raw = SimpleNamespace(
        content=[
            _make_text_block("preamble"),
            _make_tool_use_block("report_meal_components", payload),
        ]
    )
    parsed = parse_tool_use_response(raw)
    assert len(parsed.components) == 1
    assert parsed.components[0].name == "Jollof rice"


def test_parse_tool_use_response_raises_when_no_tool_block():
    from app.lib.vision import parse_tool_use_response

    raw = SimpleNamespace(content=[_make_text_block("hi")])
    with pytest.raises(ValueError, match="no_tool_use_block"):
        parse_tool_use_response(raw)


def test_parse_tool_use_response_raises_validation_error_on_bad_shape():
    from app.lib.vision import parse_tool_use_response

    bad_payload = {"components": [{"name": "x"}]}  # missing kcal_* fields
    raw = SimpleNamespace(
        content=[_make_tool_use_block("report_meal_components", bad_payload)]
    )
    with pytest.raises(ValidationError):
        parse_tool_use_response(raw)


def test_parse_tool_use_response_skips_non_matching_tool_name():
    from app.lib.vision import parse_tool_use_response

    raw = SimpleNamespace(
        content=[_make_tool_use_block("other_tool", {"x": 1})]
    )
    with pytest.raises(ValueError, match="no_tool_use_block"):
        parse_tool_use_response(raw)


# ---------------------------------------------------------------------------
# table_rematch
# ---------------------------------------------------------------------------


def test_table_rematch_matched_uses_table_kcal_point(ghana_foods_coll):
    from app.lib.vision import table_rematch
    from app.models.vision import VisionComponentRaw

    # LLM gives a kcal_point that DIFFERS from the table value; table wins.
    # LLM says 600 kcal_point (within its own [400,600] range);
    # table value is 165 * 300 / 100 = 495 kcal — strictly different.
    vc = VisionComponentRaw(
        name="jollof",  # matches via alt_name
        kcal_low=400,
        kcal_high=600,
        kcal_point=600,
        portion_g_estimate=300,
        confidence=0.9,
    )
    components = table_rematch([vc], ghana_foods_coll)
    assert len(components) == 1
    c = components[0]
    assert c["matched_food_id"] == "gh-jollof-rice"
    # Table: 165 kcal/100g × 300g = 495 kcal.
    assert c["kcal_point"] == round(165.0 * 300 / 100)
    # LLM advisory range preserved.
    assert c["kcal_low"] == 400
    assert c["kcal_high"] == 600
    assert c["source"] == "llm_then_table_rematch"
    assert c["name"] == "Jollof rice"  # name from table, not LLM


def test_table_rematch_unmatched_falls_back_to_llm_midpoint(ghana_foods_coll):
    from app.lib.vision import table_rematch
    from app.models.vision import VisionComponentRaw

    vc = VisionComponentRaw(
        name="exotic-dish-no-table-match",
        kcal_low=200,
        kcal_high=400,
        kcal_point=300,
        portion_g_estimate=150,
        confidence=0.5,
    )
    components = table_rematch([vc], ghana_foods_coll)
    c = components[0]
    assert c["matched_food_id"] is None
    # Midpoint of [200, 400] = 300.
    assert c["kcal_point"] == 300
    assert c["protein_g_point"] == 0
    assert c["source"] == "user_corrected"
    assert c["name"] == "exotic-dish-no-table-match"


def test_table_rematch_writes_correct_source_per_path(ghana_foods_coll):
    from app.lib.vision import table_rematch
    from app.models.vision import VisionComponentRaw

    matched = VisionComponentRaw(
        name="Grilled chicken",
        kcal_low=200,
        kcal_high=240,
        kcal_point=220,
        portion_g_estimate=120,
        confidence=0.9,
    )
    unmatched = VisionComponentRaw(
        name="random-dish",
        kcal_low=100,
        kcal_high=200,
        kcal_point=150,
        portion_g_estimate=100,
        confidence=0.4,
    )
    components = table_rematch([matched, unmatched], ghana_foods_coll)
    assert components[0]["source"] == "llm_then_table_rematch"
    assert components[1]["source"] == "user_corrected"


def test_table_rematch_alt_name_match(ghana_foods_coll):
    from app.lib.vision import table_rematch
    from app.models.vision import VisionComponentRaw

    # Alt name "party rice" should hit jollof.
    vc = VisionComponentRaw(
        name="party rice on a plate",
        kcal_low=300,
        kcal_high=500,
        kcal_point=400,
        portion_g_estimate=350,
        confidence=0.7,
    )
    components = table_rematch([vc], ghana_foods_coll)
    assert components[0]["matched_food_id"] == "gh-jollof-rice"


# ---------------------------------------------------------------------------
# compute_cost_usd
# ---------------------------------------------------------------------------


def test_compute_cost_usd_sonnet_4_6_known_input():
    from app.lib.vision import compute_cost_usd

    # 3000 cached input + 2000 uncached input + 200 output for sonnet-4-6:
    #   cached:    3000/1000 * 0.0003   = 0.0009
    #   uncached:  2000/1000 * 0.003    = 0.006
    #   output:    200/1000  * 0.015    = 0.003
    #   total:                          = 0.0099
    cost = compute_cost_usd(
        input_cached_tokens=3000,
        input_uncached_tokens=2000,
        output_tokens=200,
        model="claude-sonnet-4-6",
    )
    assert round(cost, 6) == 0.0099


def test_compute_cost_usd_zero_tokens():
    from app.lib.vision import compute_cost_usd

    cost = compute_cost_usd(0, 0, 0, model="claude-sonnet-4-6")
    assert cost == 0.0


def test_compute_cost_usd_unknown_model_raises():
    from app.lib.vision import compute_cost_usd

    with pytest.raises(KeyError):
        compute_cost_usd(100, 100, 100, model="gpt-4-pretend")
