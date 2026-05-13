"""Vision golden-set harness — Phase 7 P7-D.2.

Iterates the 10 entries in `manifest.json`, calls the vision pipeline
(real Anthropic when ANTHROPIC_API_KEY is set, otherwise a deterministic
fake that returns each entry's expected midpoint), and reports per-entry
MAPE + dish-name accuracy.

The single test function is `@pytest.mark.skipif`-gated on the
RUN_GOLDEN_SET=1 env var so CI default is SKIP. The harness self-validates
in the fake path: with the fake (predicted = midpoint), MAPE is 0 % by
construction — the deliverable is the harness shape, not the model
accuracy. Real-Anthropic re-run is an operator follow-up per LAUNCH.md §5.

Per CONTEXT.md: failures print diagnostics but do NOT block phase close
on the < 25 % MAPE / ≥ 70 % dish-accuracy targets — these are documented
targets, not gates.
"""

from __future__ import annotations

import difflib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


HERE = Path(__file__).resolve().parent


@dataclass
class GoldenEntry:
    id: str
    photo_path: Path
    expected_components: list[dict]  # [{name, kcal_low, kcal_high}]
    expected_total_kcal_low: int
    expected_total_kcal_high: int

    @property
    def expected_midpoint(self) -> float:
        return (self.expected_total_kcal_low + self.expected_total_kcal_high) / 2.0

    @property
    def expected_names(self) -> list[str]:
        return [c["name"] for c in self.expected_components]


def _load_manifest() -> list[GoldenEntry]:
    raw = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    entries: list[GoldenEntry] = []
    for r in raw:
        entries.append(
            GoldenEntry(
                id=r["id"],
                photo_path=HERE / r["photo"],
                expected_components=r["expected_components"],
                expected_total_kcal_low=r["expected_total_kcal_low"],
                expected_total_kcal_high=r["expected_total_kcal_high"],
            )
        )
    return entries


def _fake_vision_response(entry: GoldenEntry) -> dict:
    """Deterministic fake — predicted total = expected midpoint.

    Used when ANTHROPIC_API_KEY is unset (default in CI and in the
    in-phase executor run). MAPE is 0 % by construction in this mode —
    the harness self-validates its shape rather than vision accuracy.
    """
    return {
        "predicted_total_kcal": entry.expected_midpoint,
        "predicted_names": list(entry.expected_names),
    }


def _real_vision_response(entry: GoldenEntry, image_bytes: bytes) -> dict:
    """Call the real vision pipeline via app.lib.vision.

    Routed via `analyze_meal_for_golden_set` if present, else falls back to
    a direct Anthropic SDK call. This is the operator-pass path — when
    ANTHROPIC_API_KEY is set in the local env, this runs against
    claude-sonnet-4-6 and incurs real cost (~$0.005/photo).

    For v1.0, this path is intentionally a thin shim. The plan explicitly
    accepts a v1.1 operator pass for the real-Anthropic re-run; we wire
    the deterministic fake by default.
    """
    # Import lazily so the fake path doesn't require the anthropic SDK.
    import anthropic
    from app.lib.vision import (
        ANTHROPIC_MODEL,
        build_system_prompt,
        build_user_message,
        parse_tool_use_response,
    )
    from app.models.vision import ANTHROPIC_TOOL_SCHEMA
    import base64

    # Minimal system prompt — golden-set runs do NOT pull user history.
    sys_prompt_blocks = build_system_prompt(ghana_foods=[], corrections=[])
    image_b64 = base64.b64encode(image_bytes).decode()
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=os.environ.get("LLM_VISION_MODEL", ANTHROPIC_MODEL),
        max_tokens=1024,
        system=sys_prompt_blocks,
        messages=[
            {"role": "user", "content": build_user_message(image_b64)},
        ],
        tools=[ANTHROPIC_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": ANTHROPIC_TOOL_SCHEMA["name"]},
    )
    parsed = parse_tool_use_response(msg)
    total = sum(c.kcal_point for c in parsed.components)
    return {
        "predicted_total_kcal": float(total),
        "predicted_names": [c.name for c in parsed.components],
    }


def _dish_accuracy(predicted_names: list[str], expected_names: list[str]) -> float:
    """Per-entry dish accuracy: fraction of expected names that fuzzy-match
    (ratio >= 0.7) ANY predicted name.
    """
    if not expected_names:
        return 0.0
    hits = 0
    for expected in expected_names:
        for predicted in predicted_names:
            ratio = difflib.SequenceMatcher(
                None, expected.lower(), predicted.lower()
            ).ratio()
            if ratio >= 0.7:
                hits += 1
                break
    return hits / len(expected_names)


def _mape(predicted: float, expected_midpoint: float) -> float:
    """Mean absolute percentage error for a single entry."""
    if expected_midpoint <= 0:
        return 0.0
    return abs(predicted - expected_midpoint) / expected_midpoint * 100.0


# ---------------------------------------------------------------------------
# The harness test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("RUN_GOLDEN_SET") != "1",
    reason="Set RUN_GOLDEN_SET=1 to run the vision golden set.",
)
def test_golden_set() -> None:
    """Run all 10 entries; aggregate MAPE + dish accuracy."""
    entries = _load_manifest()
    assert len(entries) == 10, f"expected 10 entries, got {len(entries)}"

    # Use the real Anthropic vision pipeline only when explicitly opted in
    # via GOLDEN_SET_REAL=1 (and a real ANTHROPIC_API_KEY is available).
    # conftest.py sets a stub ANTHROPIC_API_KEY for every backend test, so
    # we cannot use the presence of that var as the signal.
    use_real = (
        os.environ.get("GOLDEN_SET_REAL") == "1"
        and bool(os.environ.get("ANTHROPIC_API_KEY"))
        and not os.environ["ANTHROPIC_API_KEY"].startswith("sk-ant-test-")
    )
    mode = "real-anthropic" if use_real else "deterministic-fake"

    rows: list[dict[str, Any]] = []
    for entry in entries:
        assert entry.photo_path.is_file(), f"missing photo: {entry.photo_path}"
        if use_real:
            image_bytes = entry.photo_path.read_bytes()
            result = _real_vision_response(entry, image_bytes)
        else:
            result = _fake_vision_response(entry)
        mape_val = _mape(result["predicted_total_kcal"], entry.expected_midpoint)
        dish_acc = _dish_accuracy(result["predicted_names"], entry.expected_names)
        rows.append({
            "id": entry.id,
            "expected_midpoint": entry.expected_midpoint,
            "predicted_total_kcal": result["predicted_total_kcal"],
            "mape": mape_val,
            "dish_accuracy": dish_acc,
        })

    mean_mape = sum(r["mape"] for r in rows) / len(rows)
    mean_dish_acc = sum(r["dish_accuracy"] for r in rows) / len(rows)

    # Markdown table for stdout (captured by the runner via `-s`).
    print()
    print(f"## Golden-set run — mode: {mode}")
    print()
    print("| id | expected_kcal | predicted_kcal | MAPE % | dish_accuracy |")
    print("|----|--------------:|---------------:|-------:|--------------:|")
    for r in rows:
        print(
            f"| {r['id']} | {r['expected_midpoint']:.0f} | "
            f"{r['predicted_total_kcal']:.0f} | {r['mape']:.2f} | "
            f"{r['dish_accuracy']:.2f} |"
        )
    print()
    print(f"**Aggregate MAPE:** {mean_mape:.2f} %")
    print(f"**Aggregate dish accuracy:** {mean_dish_acc:.2f}")
    print()

    # Documented targets — CONTEXT.md treats failure here as informational,
    # not a phase blocker. We assert them so the operator running with
    # real Anthropic gets a clear PASS/FAIL signal.
    assert mean_mape < 25.0, (
        f"MAPE {mean_mape:.2f}% >= 25% target. Per-entry: "
        + ", ".join(f"{r['id']}={r['mape']:.1f}%" for r in rows)
    )
    assert mean_dish_acc >= 0.70, (
        f"dish accuracy {mean_dish_acc:.2f} < 0.70 target. Per-entry: "
        + ", ".join(f"{r['id']}={r['dish_accuracy']:.2f}" for r in rows)
    )
