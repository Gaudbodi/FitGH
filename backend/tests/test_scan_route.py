"""Tests for POST /meals/scan + GET /scan-budget (Phase 4, P4-B.1).

Anthropic SDK calls are intercepted via respx so CI never makes a real
HTTPS hop. The single live test at the bottom is gated by env var
RUN_LIVE_VISION_TEST=1 and skipped otherwise — see P4-F.2.

Test surface:
  - Happy path: single + multi component, ai_metadata, total_*, count.
  - Table re-match wins kcal_point.
  - Unmatched component falls back to LLM midpoint + source="user_corrected".
  - 429 daily cap on 9th call; no over-increment.
  - 503 global breaker; user-cap rollback on 503.
  - 400 paths: missing image, wrong mime, oversize, empty.
  - 502 on malformed LLM (retried once, both fail).
  - Spend recorded matches compute_cost_usd output.
  - System prompt includes user_corrections.
  - cache_control on first system block.
  - 401 unauth.
  - No Authorization header in caplog on SDK error (T-04-06).
  - No image bytes in any Mongo doc after the call (T-04-01).
  - Cost-alert webhook fires once per threshold cross / day.
"""

from __future__ import annotations

import io
import os
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
import respx

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_clerk_signed_in(monkeypatch, *, clerk_user_id: str = "user_scan") -> None:
    import app.middleware.auth as auth_mod

    fake_state = SimpleNamespace(
        is_signed_in=True,
        reason=None,
        payload={"sub": clerk_user_id, "email": "m@example.com"},
    )

    class _StubClerk:
        def authenticate_request(self, _req, _opts):  # noqa: ARG002
            return fake_state

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerk())


def _seed_foods(mongo_collections) -> None:
    foods = [
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
            "alt_names": ["chicken", "chicken thigh"],
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
            "food_id": "gh-tilapia-grilled",
            "name": "Grilled tilapia",
            "alt_names": [],
            "kcal_per_100g": 130.0,
            "protein_g_per_100g": 26.0,
            "fat_g_per_100g": 3.0,
            "carbs_g_per_100g": 0.0,
            "portion_defaults": [{"label": "1 medium", "grams": 250}],
            "category": "protein",
            "source": "wafct",
            "source_confidence": "high",
        },
    ]
    mongo_collections.ghana_foods.insert_many(foods)


def _make_anthropic_response(
    *,
    components: list[dict] | None = None,
    input_tokens: int = 2000,
    cache_read_input_tokens: int = 3000,
    output_tokens: int = 200,
    bad_payload: bool = False,
    no_tool_use: bool = False,
) -> dict:
    """Build a canned Anthropic Messages API response body."""
    if components is None:
        components = [
            {
                "name": "Jollof rice",
                "kcal_low": 400,
                "kcal_high": 600,
                "kcal_point": 500,
                "portion_g_estimate": 300,
                "confidence": 0.9,
            }
        ]
    if bad_payload:
        # Missing required fields → ValidationError in our parser.
        content_blocks = [
            {
                "type": "tool_use",
                "id": "toolu_01abc",
                "name": "report_meal_components",
                "input": {"components": [{"name": "x"}]},
            }
        ]
    elif no_tool_use:
        content_blocks = [{"type": "text", "text": "I cannot identify the dish."}]
    else:
        content_blocks = [
            {
                "type": "tool_use",
                "id": "toolu_01abc",
                "name": "report_meal_components",
                "input": {"components": components},
            }
        ]
    return {
        "id": "msg_01abc",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-4-6",
        "content": content_blocks,
        "stop_reason": "tool_use" if not no_tool_use else "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": input_tokens,
            "cache_read_input_tokens": cache_read_input_tokens,
            "cache_creation_input_tokens": 0,
            "output_tokens": output_tokens,
        },
    }


def _post_scan(client, *, image_bytes: bytes = b"FAKEIMG", mime: str = "image/jpeg"):
    """POST a multipart image to /meals/scan."""
    data = {"image": (io.BytesIO(image_bytes), "meal.jpg", mime)}
    return client.post(
        "/meals/scan",
        data=data,
        headers={"Authorization": "Bearer test-token"},
        content_type="multipart/form-data",
    )


def _refresh_config(client) -> None:
    """Re-read env into a fresh Config and stash on the app.

    The app fixture froze a Config at create_app() time; tests that
    monkeypatch.setenv after that point need to refresh the dataclass
    so the route's `cfg = current_app.config['FITGH']` picks them up.
    """
    from app.config import Config

    client.application.config["FITGH"] = Config()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_scan_happy_path_returns_components_and_metadata(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        resp = _post_scan(client)
    assert resp.status_code == 200
    body = resp.get_json()
    assert "components" in body
    assert "ai_metadata" in body
    assert body["user_daily_count"] == 1
    assert body["user_daily_limit"] == 8
    assert body["ai_metadata"]["model"] == "claude-sonnet-4-6"
    assert len(body["ai_metadata"]["prompt_hash"]) == 64
    assert body["ai_metadata"]["latency_ms"] >= 0
    assert body["ai_metadata"]["cost_usd"] > 0


def test_scan_multi_component_returns_all(client, mongo_collections, monkeypatch):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    components = [
        {
            "name": "Jollof rice",
            "kcal_low": 400,
            "kcal_high": 600,
            "kcal_point": 500,
            "portion_g_estimate": 300,
            "confidence": 0.9,
        },
        {
            "name": "Grilled chicken",
            "kcal_low": 200,
            "kcal_high": 280,
            "kcal_point": 240,
            "portion_g_estimate": 120,
            "confidence": 0.85,
        },
        {
            "name": "Tilapia",
            "kcal_low": 250,
            "kcal_high": 350,
            "kcal_point": 300,
            "portion_g_estimate": 250,
            "confidence": 0.7,
        },
    ]
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(
                200, json=_make_anthropic_response(components=components)
            )
        )
        resp = _post_scan(client)
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["components"]) == 3
    names = [c["name"] for c in body["components"]]
    assert "Jollof rice" in names
    assert "Grilled chicken" in names


def test_scan_table_rematch_uses_table_kcal_not_llm_kcal(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    # LLM says jollof has kcal_point=600 (matching its own range high);
    # table for jollof is 165 kcal/100g * 300g = 495 kcal.
    components = [
        {
            "name": "jollof",
            "kcal_low": 400,
            "kcal_high": 600,
            "kcal_point": 600,
            "portion_g_estimate": 300,
            "confidence": 0.9,
        }
    ]
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(
                200, json=_make_anthropic_response(components=components)
            )
        )
        resp = _post_scan(client)
    body = resp.get_json()
    c = body["components"][0]
    assert c["matched_food_id"] == "gh-jollof-rice"
    assert c["kcal_point"] == round(165.0 * 300 / 100)  # = 495
    assert c["kcal_low"] == 400  # LLM range preserved as advisory
    assert c["kcal_high"] == 600
    assert c["source"] == "llm_then_table_rematch"


def test_scan_unmatched_component_uses_llm_midpoint_and_user_corrected_source(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    components = [
        {
            "name": "exotic-dish-not-in-table",
            "kcal_low": 200,
            "kcal_high": 400,
            "kcal_point": 300,
            "portion_g_estimate": 150,
            "confidence": 0.5,
        }
    ]
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(
                200, json=_make_anthropic_response(components=components)
            )
        )
        resp = _post_scan(client)
    c = resp.get_json()["components"][0]
    assert c["matched_food_id"] is None
    assert c["kcal_point"] == 300  # midpoint of [200, 400]
    assert c["source"] == "user_corrected"


# ---------------------------------------------------------------------------
# Per-user daily cap
# ---------------------------------------------------------------------------


def test_scan_user_daily_cap_429_on_9th_call(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        # 8 successful calls
        for i in range(8):
            r = _post_scan(client)
            assert r.status_code == 200, f"call {i + 1} failed"
        # 9th — capped
        r = _post_scan(client)
    assert r.status_code == 429
    body = r.get_json()
    assert body["error"] == "daily_cap"
    assert body["limit"] == 8
    assert body["count"] == 8
    assert "reset_at" in body


def test_scan_daily_cap_does_not_over_increment(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        for _ in range(12):
            _post_scan(client)
    doc = mongo_collections.vision_usage.find_one({"user_id": "user_scan"})
    assert doc["count"] == 8


# ---------------------------------------------------------------------------
# Global budget breaker
# ---------------------------------------------------------------------------


def test_scan_global_budget_503_when_over_cap(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    # Seed an over-cap system_state for today (using today_utc_str).
    from app.lib.rate_limit import today_utc_str

    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": today_utc_str(),
            "spend_usd": 5.01,
            "cap_usd": 5.00,
            "alert_fired": True,
        }
    )
    monkeypatch.setenv("VISION_DAILY_CAP_USD", "5.0")
    _refresh_config(client)
    # We DO NOT mock respx — the route MUST 503 before any HTTP call.
    resp = _post_scan(client)
    assert resp.status_code == 503
    body = resp.get_json()
    assert body["error"] == "service_paused"
    assert body["reason"] == "daily_budget"


def test_scan_global_budget_rollback_user_cap(
    client, mongo_collections, monkeypatch
):
    """T-04-03 rollback: 503 from global budget → user-cap count unchanged."""
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    from app.lib.rate_limit import today_utc_str

    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": today_utc_str(),
            "spend_usd": 5.01,
            "cap_usd": 5.00,
            "alert_fired": True,
        }
    )
    monkeypatch.setenv("VISION_DAILY_CAP_USD", "5.0")
    _post_scan(client)
    doc = mongo_collections.vision_usage.find_one({"user_id": "user_scan"})
    # Either the doc was never created (preferred — no net change) OR
    # count rolled back to 0. Both are acceptable: no positive count.
    assert doc is None or doc["count"] == 0


# ---------------------------------------------------------------------------
# 400 image-validation paths
# ---------------------------------------------------------------------------


def test_scan_no_image_returns_400(client, mongo_collections, monkeypatch):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    resp = client.post(
        "/meals/scan",
        data={},
        headers={"Authorization": "Bearer t"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_image"


def test_scan_wrong_mime_returns_400(client, mongo_collections, monkeypatch):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    resp = _post_scan(client, image_bytes=b"abc", mime="application/pdf")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "invalid_image"
    assert body["reason"] == "mime"


def test_scan_oversize_image_returns_400(client, mongo_collections, monkeypatch):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    # 2 MB > 1 MB hard cap.
    big = b"\x00" * (2 * 1024 * 1024)
    resp = _post_scan(client, image_bytes=big)
    assert resp.status_code == 400
    assert resp.get_json()["reason"] == "too_large"


def test_scan_image_validation_does_not_consume_daily_cap(
    client, mongo_collections, monkeypatch
):
    """Validation failures must roll back the conditional increment so a
    user with bad uploads doesn't burn their 8/day quota."""
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    for _ in range(3):
        _post_scan(client, image_bytes=b"abc", mime="application/pdf")
    doc = mongo_collections.vision_usage.find_one({"user_id": "user_scan"})
    assert doc is None or doc["count"] == 0


# ---------------------------------------------------------------------------
# T-04-01 — no image bytes persisted
# ---------------------------------------------------------------------------


def test_scan_no_image_bytes_persisted(client, mongo_collections, monkeypatch):
    """After a successful scan, no Mongo doc carries the image bytes."""
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        resp = _post_scan(client, image_bytes=b"REALISTICIMAGEBYTES" * 50)
    assert resp.status_code == 200
    # Inspect every doc in every meaningful collection.
    for coll in [
        mongo_collections.meals,
        mongo_collections.vision_usage,
        mongo_collections.system_state,
        mongo_collections.user_corrections,
    ]:
        for doc in coll.find({}):
            # No `image` key anywhere.
            assert "image" not in doc
            assert "image_bytes" not in doc
            assert "image_b64" not in doc


# ---------------------------------------------------------------------------
# T-04-04 — user_id from form/body is ignored
# ---------------------------------------------------------------------------


def test_scan_ignores_user_id_in_form(client, mongo_collections, monkeypatch):
    _stub_clerk_signed_in(monkeypatch, clerk_user_id="user_truth")
    _seed_foods(mongo_collections)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        data = {
            "image": (io.BytesIO(b"FAKE"), "m.jpg", "image/jpeg"),
            "user_id": "user_attacker",
        }
        resp = client.post(
            "/meals/scan",
            data=data,
            headers={"Authorization": "Bearer t"},
            content_type="multipart/form-data",
        )
    assert resp.status_code == 200
    # vision_usage doc is keyed by g.clerk_user_id, not the form value.
    doc = mongo_collections.vision_usage.find_one({"user_id": "user_truth"})
    assert doc is not None
    assert mongo_collections.vision_usage.find_one({"user_id": "user_attacker"}) is None


# ---------------------------------------------------------------------------
# 502 paths — malformed LLM
# ---------------------------------------------------------------------------


def test_scan_malformed_llm_response_retries_once_then_502(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    bad = _make_anthropic_response(bad_payload=True)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        # Both calls return malformed payloads → retry burns + 502.
        route = router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=bad)
        )
        resp = _post_scan(client)
    assert resp.status_code == 502
    assert resp.get_json()["error"] == "vision_parse_failed"
    # Two attempts (initial + 1 retry).
    assert route.call_count == 2
    # And the user-cap was rolled back.
    doc = mongo_collections.vision_usage.find_one({"user_id": "user_scan"})
    assert doc is None or doc["count"] == 0


def test_scan_no_tool_use_block_retries_then_502(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    no_tool = _make_anthropic_response(no_tool_use=True)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        route = router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=no_tool)
        )
        resp = _post_scan(client)
    assert resp.status_code == 502
    assert route.call_count == 2


# ---------------------------------------------------------------------------
# Cost recording
# ---------------------------------------------------------------------------


def test_scan_records_actual_token_cost(client, mongo_collections, monkeypatch):
    from app.lib.rate_limit import today_utc_str
    from app.lib.vision import compute_cost_usd

    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    canned = _make_anthropic_response(
        input_tokens=2000, cache_read_input_tokens=3000, output_tokens=500
    )
    expected_cost = compute_cost_usd(
        input_cached_tokens=3000,
        input_uncached_tokens=2000,
        output_tokens=500,
        model="claude-sonnet-4-6",
    )
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=canned)
        )
        resp = _post_scan(client)
    assert resp.status_code == 200
    assert resp.get_json()["ai_metadata"]["cost_usd"] == expected_cost
    state = mongo_collections.system_state.find_one({"_id": "vision_budget"})
    assert state is not None
    assert state["date"] == today_utc_str()
    assert round(state["spend_usd"], 6) == expected_cost


# ---------------------------------------------------------------------------
# User-corrections feed into the prompt
# ---------------------------------------------------------------------------


def test_scan_passes_user_corrections_to_prompt(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    mongo_collections.user_corrections.insert_many(
        [
            {
                "user_id": "user_scan",
                "original_name": "rice",
                "corrected_name": "Jollof rice",
                "original_portion_g": 200,
                "corrected_portion_g": 350,
                "original_food_id": None,
                "corrected_food_id": "gh-jollof-rice",
                "corrected_at": datetime.now(UTC),
            },
            {
                "user_id": "user_other",  # different user — must be filtered out
                "original_name": "should_not_appear",
                "corrected_name": "x",
                "original_portion_g": 1,
                "corrected_portion_g": 1,
                "original_food_id": None,
                "corrected_food_id": None,
                "corrected_at": datetime.now(UTC),
            },
        ]
    )
    captured_body: dict = {}

    def _handler(request):
        captured_body["json"] = request.content.decode("utf-8")
        return httpx.Response(200, json=_make_anthropic_response())

    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(side_effect=_handler)
        resp = _post_scan(client)
    assert resp.status_code == 200
    body_str = captured_body["json"]
    # The user's correction text surfaces in the un-cached prompt block.
    assert "Jollof rice" in body_str
    assert "rice" in body_str
    # Other user's correction is NOT included.
    assert "should_not_appear" not in body_str


def test_scan_prompt_cache_marker_present(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    captured_body: dict = {}

    def _handler(request):
        captured_body["json"] = request.content.decode("utf-8")
        return httpx.Response(200, json=_make_anthropic_response())

    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(side_effect=_handler)
        resp = _post_scan(client)
    assert resp.status_code == 200
    assert "ephemeral" in captured_body["json"]
    assert "cache_control" in captured_body["json"]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_scan_requires_auth_401(client, mongo_collections, monkeypatch):
    """No stub_clerk_signed_in — the real auth middleware rejects."""
    # The default stub Clerk in conftest is None; the auth middleware
    # raises RuntimeError because CLERK_SECRET_KEY is stubbed and the
    # _StubClerk never runs. Use a stub that returns is_signed_in=False.
    import app.middleware.auth as auth_mod

    class _StubClerkAnon:
        def authenticate_request(self, _req, _opts):
            return SimpleNamespace(is_signed_in=False, reason="no_session_token", payload=None)

    monkeypatch.setattr(auth_mod, "_clerk", _StubClerkAnon())
    resp = _post_scan(client)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# T-04-06 — no Authorization header in caplog on SDK error
# ---------------------------------------------------------------------------


def test_scan_logs_no_authorization_header_on_anthropic_error(
    client, mongo_collections, monkeypatch, caplog
):
    """T-04-06: on Anthropic 401, we log the failure with a fixed message
    but do NOT leak the original exception's args (which can include the
    request URL + Authorization header). Re-raised as a plain RuntimeError
    via `from None` before logging happens.
    """
    import logging

    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    caplog.set_level(logging.WARNING)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(401, json={"error": {"message": "bad key"}})
        )
        resp = _post_scan(client)
    assert resp.status_code == 502
    log_text = "\n".join(rec.getMessage() for rec in caplog.records)
    # No Bearer token / API key fragments in logs.
    assert "sk-ant-test-stub-xxxxxxxxxxxxxxxx" not in log_text
    assert "Bearer sk-ant" not in log_text


# ---------------------------------------------------------------------------
# Cost-alert webhook (P4-B.2)
# ---------------------------------------------------------------------------


def test_cost_alert_fires_when_per_dau_over_threshold(
    client, mongo_collections, monkeypatch
):
    """Seed near-cap state + tiny DAU; one scan crosses $0.05/DAU → webhook fires."""
    from app.lib.rate_limit import today_utc_str

    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    monkeypatch.setenv("COST_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")
    monkeypatch.setenv("VISION_DAILY_CAP_USD", "100.0")
    _refresh_config(client)
    # Pre-seed: spend already 0.045, 1 DAU. One scan ~$0.0099 → spend
    # 0.0549, per-DAU = 0.0549 > 0.05 → alert.
    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": today_utc_str(),
            "spend_usd": 0.045,
            "cap_usd": 100.0,
            "alert_fired": False,
        }
    )
    with respx.mock(base_url="https://api.anthropic.com") as router_anth:
        router_anth.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        with respx.mock(base_url="https://hooks.example.com") as router_hook:
            route = router_hook.post("/x").mock(
                return_value=httpx.Response(200, json={})
            )
            resp = _post_scan(client)
    assert resp.status_code == 200
    assert route.call_count == 1
    # Latch fires.
    state = mongo_collections.system_state.find_one({"_id": "vision_budget"})
    assert state["alert_fired"] is True


def test_cost_alert_skipped_when_no_webhook_url(
    client, mongo_collections, monkeypatch, caplog
):
    """Without COST_ALERT_WEBHOOK_URL, alerts WARN-log; no HTTP egress."""
    import logging

    from app.lib.rate_limit import today_utc_str

    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    monkeypatch.delenv("COST_ALERT_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("VISION_DAILY_CAP_USD", "100.0")
    _refresh_config(client)
    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": today_utc_str(),
            "spend_usd": 0.045,
            "cap_usd": 100.0,
            "alert_fired": False,
        }
    )
    caplog.set_level(logging.WARNING)
    with respx.mock(base_url="https://api.anthropic.com") as router:
        router.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        resp = _post_scan(client)
    assert resp.status_code == 200
    log_text = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "cost_alert_no_webhook" in log_text


def test_cost_alert_not_fired_twice_in_same_day(
    client, mongo_collections, monkeypatch
):
    from app.lib.rate_limit import today_utc_str

    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    monkeypatch.setenv("COST_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")
    monkeypatch.setenv("VISION_DAILY_CAP_USD", "100.0")
    _refresh_config(client)
    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": today_utc_str(),
            "spend_usd": 0.045,
            "cap_usd": 100.0,
            "alert_fired": False,
        }
    )
    with respx.mock(base_url="https://api.anthropic.com") as router_anth:
        router_anth.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        with respx.mock(base_url="https://hooks.example.com") as router_hook:
            route = router_hook.post("/x").mock(
                return_value=httpx.Response(200, json={})
            )
            _post_scan(client)
            _post_scan(client)
    assert route.call_count == 1  # single-fire latch


def test_cost_alert_resets_on_new_day(client, mongo_collections, monkeypatch):
    """Day-roll: yesterday's alert_fired latch is irrelevant — today's
    crossing threshold re-fires."""
    from app.lib.rate_limit import today_utc_str

    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    monkeypatch.setenv("COST_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")
    monkeypatch.setenv("VISION_DAILY_CAP_USD", "100.0")
    _refresh_config(client)
    # Yesterday's stale doc.
    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": "2026-05-12",
            "spend_usd": 0.20,
            "cap_usd": 100.0,
            "alert_fired": True,  # latched yesterday
        }
    )
    with respx.mock(base_url="https://api.anthropic.com") as router_anth:
        # Use ~0.060 cost (60k cached input would do it; or just inflate
        # output tokens). Goal: today's spend > 0.05/DAU after one call.
        # Output tokens 4000 → 4 * 0.015 = 0.06. Plus inputs ~0.006 → 0.066.
        router_anth.post("/v1/messages").mock(
            return_value=httpx.Response(
                200,
                json=_make_anthropic_response(
                    output_tokens=4000, cache_read_input_tokens=0, input_tokens=0
                ),
            )
        )
        with respx.mock(base_url="https://hooks.example.com") as router_hook:
            route = router_hook.post("/x").mock(
                return_value=httpx.Response(200, json={})
            )
            resp = _post_scan(client)
    assert resp.status_code == 200
    # Today's doc replaced yesterday's, alert_fired re-fired.
    state = mongo_collections.system_state.find_one({"_id": "vision_budget"})
    assert state["date"] == today_utc_str()
    assert state["alert_fired"] is True
    assert route.call_count == 1


def test_cost_alert_webhook_timeout_does_not_break_scan(
    client, mongo_collections, monkeypatch
):
    from app.lib.rate_limit import today_utc_str

    _stub_clerk_signed_in(monkeypatch)
    _seed_foods(mongo_collections)
    monkeypatch.setenv("COST_ALERT_WEBHOOK_URL", "https://hooks.example.com/x")
    monkeypatch.setenv("VISION_DAILY_CAP_USD", "100.0")
    _refresh_config(client)
    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": today_utc_str(),
            "spend_usd": 0.045,
            "cap_usd": 100.0,
            "alert_fired": False,
        }
    )
    with respx.mock(base_url="https://api.anthropic.com") as router_anth:
        router_anth.post("/v1/messages").mock(
            return_value=httpx.Response(200, json=_make_anthropic_response())
        )
        with respx.mock(base_url="https://hooks.example.com") as router_hook:
            router_hook.post("/x").mock(side_effect=httpx.TimeoutException("slow"))
            resp = _post_scan(client)
    # Scan still succeeds — webhook failure is non-fatal.
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /scan-budget
# ---------------------------------------------------------------------------


def test_scan_budget_returns_zero_when_no_doc(
    client, mongo_collections, monkeypatch
):
    _stub_clerk_signed_in(monkeypatch)
    resp = client.get("/scan-budget", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["spend_usd"] == 0.0
    assert body["paused"] is False


def test_scan_budget_returns_paused_when_over_cap(
    client, mongo_collections, monkeypatch
):
    from app.lib.rate_limit import today_utc_str

    _stub_clerk_signed_in(monkeypatch)
    mongo_collections.system_state.insert_one(
        {
            "_id": "vision_budget",
            "date": today_utc_str(),
            "spend_usd": 5.50,
            "cap_usd": 5.00,
            "alert_fired": True,
        }
    )
    resp = client.get("/scan-budget", headers={"Authorization": "Bearer t"})
    body = resp.get_json()
    assert body["paused"] is True
    assert body["spend_usd"] == 5.50


# ---------------------------------------------------------------------------
# Live test — env-gated, skipped by default (P4-F.2 hook).
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_VISION_TEST") != "1",
    reason="live test — requires ANTHROPIC_API_KEY and consumes ~$0.005 of credit",
)
def test_live_scan_jollof_returns_components():
    """One end-to-end live test. Requires:
      - ANTHROPIC_API_KEY set in backend/.env.local.
      - backend/tests/fixtures/jollof.jpg present (Phase 7 may drop the file).
      - RUN_LIVE_VISION_TEST=1.

    Asserts a real Sonnet 4.6 call returns at least one component whose
    name contains 'rice' or 'jollof' with kcal_low > 0.
    """
    import pathlib

    fixture = pathlib.Path(__file__).parent / "fixtures" / "jollof.jpg"
    if not fixture.exists():
        pytest.skip("fixtures/jollof.jpg not present — drop one for Phase 7")
    # Live route requires a real Atlas + Clerk session — out of scope for
    # an automated test. Documented as operator-driven via P4-F.2.
    pytest.skip("live operator test — see SUMMARY.md P4-F.2 for manual steps")
