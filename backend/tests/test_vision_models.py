"""Tests for Pydantic vision models (Phase 4, Task P4-A.1).

The vision pipeline shapes:
  - VisionComponentRaw    — LLM tool-use output (pre table re-match).
  - VisionResponse        — wrapper holding the components list.
  - VisionUsageDoc        — per-(user, date) doc in vision_usage collection.
  - SystemStateDoc        — singleton in system_state ({_id: "vision_budget"}).
  - UserCorrectionDoc     — user_corrections collection.
  - AiMetadata            — sub-doc matching the Phase-3-reserved
                            Meal.ai_metadata shape (model, prompt_hash,
                            image_dims, latency_ms, cost_usd).
  - ANTHROPIC_TOOL_SCHEMA — the dict passed to Anthropic's `tools` arg;
                            its input_schema MUST match VisionResponse.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# VisionComponentRaw
# ---------------------------------------------------------------------------


def _valid_vc_kwargs(**overrides) -> dict:
    base = {
        "name": "Jollof rice",
        "kcal_low": 400,
        "kcal_high": 600,
        "kcal_point": 500,
        "portion_g_estimate": 300,
        "confidence": 0.85,
    }
    base.update(overrides)
    return base


def test_vision_component_raw_kcal_high_must_be_ge_low():
    from app.models.vision import VisionComponentRaw

    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(kcal_low=600, kcal_high=400, kcal_point=500))


def test_vision_component_raw_kcal_point_within_low_high():
    from app.models.vision import VisionComponentRaw

    # kcal_point above kcal_high → invalid
    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(kcal_low=100, kcal_high=200, kcal_point=300))
    # kcal_point below kcal_low → invalid
    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(kcal_low=300, kcal_high=400, kcal_point=200))


def test_vision_component_raw_confidence_range():
    from app.models.vision import VisionComponentRaw

    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(confidence=-0.1))
    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(confidence=1.5))


def test_vision_component_raw_extra_forbid():
    from app.models.vision import VisionComponentRaw

    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(smuggled="bad"))


def test_vision_component_raw_portion_bounds():
    from app.models.vision import VisionComponentRaw

    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(portion_g_estimate=5))
    with pytest.raises(ValidationError):
        VisionComponentRaw(**_valid_vc_kwargs(portion_g_estimate=1000))


# ---------------------------------------------------------------------------
# VisionResponse
# ---------------------------------------------------------------------------


def test_vision_response_components_min_1_max_10():
    from app.models.vision import VisionResponse

    with pytest.raises(ValidationError):
        VisionResponse(components=[])

    with pytest.raises(ValidationError):
        VisionResponse(components=[_valid_vc_kwargs()] * 11)


def test_vision_response_accepts_single_component():
    from app.models.vision import VisionResponse

    vr = VisionResponse(components=[_valid_vc_kwargs()])
    assert len(vr.components) == 1
    assert vr.components[0].name == "Jollof rice"


def test_vision_response_extra_forbid():
    from app.models.vision import VisionResponse

    with pytest.raises(ValidationError):
        VisionResponse(components=[_valid_vc_kwargs()], smuggled="bad")


# ---------------------------------------------------------------------------
# AiMetadata
# ---------------------------------------------------------------------------


def test_ai_metadata_extra_ignored():
    from app.models.vision import AiMetadata

    # extra="ignore" → unknown fields silently dropped (Phase 3 dict|None
    # acceptance plus forward-compat).
    am = AiMetadata(
        model="claude-sonnet-4-6",
        prompt_hash="a" * 64,
        image_dims={"w": 1024, "h": 768},
        latency_ms=2400,
        cost_usd=0.0042,
        future_field="ignored",  # type: ignore[arg-type]
    )
    assert am.model == "claude-sonnet-4-6"
    assert not hasattr(am, "future_field")


def test_ai_metadata_rejects_negative_latency():
    from app.models.vision import AiMetadata

    with pytest.raises(ValidationError):
        AiMetadata(
            model="claude-sonnet-4-6",
            prompt_hash="a" * 64,
            image_dims={"w": 1024, "h": 768},
            latency_ms=-1,
            cost_usd=0.0042,
        )


def test_ai_metadata_rejects_negative_cost():
    from app.models.vision import AiMetadata

    with pytest.raises(ValidationError):
        AiMetadata(
            model="claude-sonnet-4-6",
            prompt_hash="a" * 64,
            image_dims={"w": 1024, "h": 768},
            latency_ms=2400,
            cost_usd=-0.01,
        )


# ---------------------------------------------------------------------------
# VisionUsageDoc
# ---------------------------------------------------------------------------


def test_vision_usage_doc_valid():
    from app.models.vision import VisionUsageDoc

    doc = VisionUsageDoc(
        user_id="user_abc",
        date="2026-05-13",
        count=3,
        last_call_at=datetime.now(UTC),
    )
    assert doc.count == 3


def test_vision_usage_doc_rejects_negative_count():
    from app.models.vision import VisionUsageDoc

    with pytest.raises(ValidationError):
        VisionUsageDoc(
            user_id="user_abc",
            date="2026-05-13",
            count=-1,
            last_call_at=datetime.now(UTC),
        )


# ---------------------------------------------------------------------------
# SystemStateDoc
# ---------------------------------------------------------------------------


def test_system_state_doc_alert_fired_default_false():
    from app.models.vision import SystemStateDoc

    doc = SystemStateDoc(
        date="2026-05-13",
        spend_usd=0.0,
        cap_usd=5.0,
    )
    assert doc.alert_fired is False
    assert doc.id == "vision_budget"


def test_system_state_doc_rejects_negative_spend():
    from app.models.vision import SystemStateDoc

    with pytest.raises(ValidationError):
        SystemStateDoc(date="2026-05-13", spend_usd=-0.01, cap_usd=5.0)


# ---------------------------------------------------------------------------
# UserCorrectionDoc
# ---------------------------------------------------------------------------


def test_user_correction_doc_corrected_name_optional():
    from app.models.vision import UserCorrectionDoc

    # Only portion changed → corrected_name None.
    doc = UserCorrectionDoc(
        user_id="user_abc",
        original_name="Jollof rice",
        corrected_name=None,
        original_portion_g=350,
        corrected_portion_g=450,
        original_food_id="gh-jollof-rice",
        corrected_food_id="gh-jollof-rice",
        corrected_at=datetime.now(UTC),
    )
    assert doc.corrected_name is None


def test_user_correction_doc_food_id_pattern_when_present():
    from app.models.vision import UserCorrectionDoc

    # corrected_food_id None when user free-texts; matched_food_id None when
    # original was free-text. Test that a present food_id must match the
    # gh- pattern (mirrors Phase 3 GhanaFood.food_id).
    doc = UserCorrectionDoc(
        user_id="user_abc",
        original_name="rice",
        corrected_name="Jollof rice",
        original_portion_g=200,
        corrected_portion_g=350,
        original_food_id=None,
        corrected_food_id="gh-jollof-rice",
        corrected_at=datetime.now(UTC),
    )
    assert doc.corrected_food_id == "gh-jollof-rice"


# ---------------------------------------------------------------------------
# ANTHROPIC_TOOL_SCHEMA
# ---------------------------------------------------------------------------


def test_anthropic_tool_schema_matches_response_shape():
    from app.models.vision import ANTHROPIC_TOOL_SCHEMA, VisionResponse

    assert ANTHROPIC_TOOL_SCHEMA["name"] == "report_meal_components"
    assert "description" in ANTHROPIC_TOOL_SCHEMA
    # input_schema must match VisionResponse.model_json_schema().
    assert ANTHROPIC_TOOL_SCHEMA["input_schema"] == VisionResponse.model_json_schema()


def test_anthropic_tool_schema_is_dict():
    from app.models.vision import ANTHROPIC_TOOL_SCHEMA

    assert isinstance(ANTHROPIC_TOOL_SCHEMA, dict)
    assert isinstance(ANTHROPIC_TOOL_SCHEMA["input_schema"], dict)
