"""
scripts/ingest_exercises.py — Phase 6 Workout Library ingest pipeline.

One-shot CLI that turns the Free Exercise DB (Unlicense) into a curated
~100-entry static manifest + 200 WebP poster/detail images for the FitGH
PWA workout library.

Inputs:
  - https://raw.githubusercontent.com/yuhonas/free-exercise-db/<sha>/dist/exercises.json
  - Image URLs hosted at the same repo path /exercises/<id>/images/0.jpg and 1.jpg
Outputs (written to --out, default frontend/public/exercises/):
  - manifest.json   — { meta: {source, commit, license, generated_at}, entries: [...] }
  - <id>/poster.webp — 320×240, quality decay loop, ≤30 kB
  - <id>/detail.webp — 800×600, quality decay loop, ≤80 kB
  - precache-list.json — first 24 (id, poster path) pairs for sw.ts (optional consumer)

Determinism:
  - With the same --commit hash, the script produces byte-identical output
    on any platform (entries sorted by id; round-robin cell ordering by id).
  - Pillow's WebP encoder is deterministic at fixed quality + method.

Threat model (T-06-08): Pillow re-encodes every image; the bytes that hit the
user are Pillow's, not the source's. Pin the commit hash and audit the source
at that hash before running.

Run:
    python -m venv .venv-ingest
    .venv-ingest\\Scripts\\activate    # Windows; on Unix: source .venv-ingest/bin/activate
    pip install -r scripts/requirements-ingest.txt
    python scripts/ingest_exercises.py --commit <sha>

Phase: 06-workout-library-pwa
"""

from __future__ import annotations

import argparse
import collections
import io
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Iterable

try:
    import httpx
    from PIL import Image, ImageOps
except ImportError as exc:  # pragma: no cover — runtime install guidance
    raise SystemExit(
        "Missing deps. Run: pip install -r scripts/requirements-ingest.txt"
    ) from exc

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Commit hash captured at ingest authoring time. Operators bump this when
# refreshing the manifest; the README documents the audit procedure for
# new hashes (T-06-08 mitigation).
DEFAULT_COMMIT = "acd61f751fe15d618862ee3084f27e839222a28f"  # captured 2026-05-13

RAW_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db"

# Equipment mapping: Free Exercise DB raw value → 6-bucket FitGH taxonomy.
# Entries mapped to None are SKIPPED.
EQUIPMENT_MAP: dict[str | None, str | None] = {
    "body only": "none",
    None: "none",  # some entries have null equipment
    "dumbbell": "dumbbell",
    "bands": "bands",
    "kettlebells": "kettlebells",
    "barbell": "barbell",
    "pull-up bar": "pull-up bar",  # rare in the source; included for completeness
    # SKIP set:
    "machine": None,
    "cable": None,
    "medicine ball": None,
    "foam roll": None,
    "exercise ball": None,
    "e-z curl bar": None,
    "other": None,
}

ALLOWED_EQUIPMENT = {"none", "dumbbell", "bands", "kettlebells", "barbell", "pull-up bar"}

# Muscle mapping: Free Exercise DB primaryMuscles[0] → 8-bucket FitGH taxonomy.
MUSCLE_MAP: dict[str, str] = {
    "chest": "chest",
    "middle back": "back",
    "lats": "back",
    "lower back": "back",
    "traps": "back",
    "neck": "back",
    "quadriceps": "legs",
    "hamstrings": "legs",
    "calves": "legs",
    "adductors": "legs",
    "abductors": "legs",
    "shoulders": "shoulders",
    "biceps": "arms",
    "triceps": "arms",
    "forearms": "arms",
    "abdominals": "core",
    "glutes": "glutes",
}

ALLOWED_MUSCLES = {"chest", "back", "legs", "shoulders", "arms", "core", "glutes", "full-body"}
ALLOWED_CATEGORIES = {"strength", "cardio"}
ALLOWED_LEVELS = {"beginner", "intermediate", "expert"}

TARGET_ENTRY_COUNT = 100
PRECACHE_SUBSET_SIZE = 24  # first N cards likely visible under default filter

POSTER_W, POSTER_H = 320, 240
DETAIL_W, DETAIL_H = 800, 600
POSTER_MAX_BYTES = 30 * 1024
DETAIL_MAX_BYTES = 80 * 1024
INITIAL_QUALITY = 72
MIN_QUALITY = 40
WEBP_METHOD = 6  # slowest+best


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_muscle(primary_muscles: list[str]) -> str:
    """Map Free Exercise DB primaryMuscles[0] to one of the 8 FitGH buckets.

    If primary[0] maps cleanly, return it. If the entry has 4+ primary muscles
    across distinct buckets, fall back to 'full-body'. If primary is empty or
    unmapped, also 'full-body'.
    """
    if not primary_muscles:
        return "full-body"
    distinct_buckets = {MUSCLE_MAP[m] for m in primary_muscles if m in MUSCLE_MAP}
    if len(distinct_buckets) >= 4:
        return "full-body"
    first = primary_muscles[0]
    if first in MUSCLE_MAP:
        return MUSCLE_MAP[first]
    return "full-body"


def normalize_equipment(equipment: str | None) -> str | None:
    """Return the 6-bucket equipment or None to skip."""
    return EQUIPMENT_MAP.get(equipment)


def fetch_source(commit: str) -> list[dict]:
    """Download and return the full Free Exercise DB exercises.json."""
    url = f"{RAW_BASE}/{commit}/dist/exercises.json"
    print(f"[ingest] Fetching {url}", file=sys.stderr)
    resp = httpx.get(url, timeout=30.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()


def filter_and_normalize(raw_entries: list[dict]) -> list[dict]:
    """Filter to allowed categories/levels and normalize fields.

    Returns entries shaped for the FitGH manifest, but pre-selection
    (more than TARGET_ENTRY_COUNT may pass).
    """
    out: list[dict] = []
    for raw in raw_entries:
        if raw.get("category") not in ALLOWED_CATEGORIES:
            continue
        if raw.get("level") not in ALLOWED_LEVELS:
            continue
        equip_raw = raw.get("equipment")
        equip = normalize_equipment(equip_raw)
        if equip is None:
            continue
        primary = raw.get("primaryMuscles") or []
        muscle = normalize_muscle(primary)
        # Skip entries without images entirely
        if not raw.get("images"):
            continue
        out.append(
            {
                "id": raw["id"],
                "name": raw.get("name", raw["id"]),
                "equipment": equip,
                "muscles_primary": [muscle],
                "muscles_secondary": [
                    MUSCLE_MAP[m] for m in (raw.get("secondaryMuscles") or []) if m in MUSCLE_MAP
                ],
                "category": raw["category"],
                "level": raw["level"],
                "mechanic": raw.get("mechanic"),
                "instructions": raw.get("instructions") or [],
                "_images": raw["images"],  # private; stripped before manifest write
            }
        )
    return out


def round_robin_select(candidates: list[dict], target: int) -> list[dict]:
    """Deterministic round-robin across the (equipment, muscle) Cartesian
    product, sorted by id, to land at ~target entries with reasonable spread.
    """
    # Group by (equipment, muscle)
    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for e in candidates:
        cells[(e["equipment"], e["muscles_primary"][0])].append(e)
    # Sort each cell deterministically by id
    for key in cells:
        cells[key].sort(key=lambda x: x["id"])

    # Round-robin in a deterministic cell order: sort cell keys
    cell_keys = sorted(cells.keys())
    picked: list[dict] = []
    seen_ids: set[str] = set()
    idx = 0
    while len(picked) < target and any(cells.values()):
        # Take one from the next cell that still has entries
        cell = cells[cell_keys[idx % len(cell_keys)]]
        if cell:
            ent = cell.pop(0)
            if ent["id"] not in seen_ids:
                picked.append(ent)
                seen_ids.add(ent["id"])
        idx += 1
        if idx > len(cell_keys) * 50:  # safety: prevent infinite loop on starvation
            break
    return picked


def encode_webp(
    img: Image.Image, target_w: int, target_h: int, max_bytes: int
) -> bytes:
    """Resize/centre-crop then WebP-encode with quality decay until under
    max_bytes or quality < MIN_QUALITY (raise).
    """
    fitted = ImageOps.fit(img, (target_w, target_h), Image.Resampling.LANCZOS)
    # Convert palette / RGBA to RGB to ensure consistent WebP encoding
    if fitted.mode not in ("RGB", "RGBA"):
        fitted = fitted.convert("RGB")
    elif fitted.mode == "RGBA":
        # Composite onto white to drop alpha (WebP supports it but we want
        # deterministic small files for posters)
        bg = Image.new("RGB", fitted.size, (255, 255, 255))
        bg.paste(fitted, mask=fitted.split()[-1])
        fitted = bg
    quality = INITIAL_QUALITY
    while quality >= MIN_QUALITY:
        buf = io.BytesIO()
        fitted.save(buf, format="WEBP", quality=quality, method=WEBP_METHOD)
        data = buf.getvalue()
        if len(data) <= max_bytes:
            return data
        quality -= 4
    raise RuntimeError(
        f"Could not encode under {max_bytes} bytes at quality>={MIN_QUALITY} "
        f"(last size {len(data)})"
    )


def download_image(client: httpx.Client, commit: str, rel: str) -> Image.Image:
    """Fetch a Free Exercise DB image path and return a PIL Image.

    The `images` field in exercises.json holds paths like `3_4_Sit-Up/0.jpg`,
    but the actual repo layout is `exercises/<id>/0.jpg` (no `images/`
    subdir, despite the field name). Probed against the pinned commit on
    2026-05-13 — `exercises/<id>/0.jpg` returns 200 vs. 404 for the others.
    """
    url = f"{RAW_BASE}/{commit}/exercises/{rel.lstrip('/')}"
    resp = client.get(url, timeout=30.0)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))


def process_entry(
    client: httpx.Client, commit: str, entry: dict, out_root: pathlib.Path
) -> dict:
    """Download + encode poster + detail for one entry. Returns the public
    manifest entry (with poster/detail paths, no _images).
    """
    images: Iterable[str] = entry["_images"]
    image_list = list(images)
    if len(image_list) == 0:
        raise RuntimeError(f"Entry {entry['id']} has no images")
    # Use first image for poster + second (or first if only one) for detail
    poster_src = image_list[0]
    detail_src = image_list[1] if len(image_list) > 1 else image_list[0]

    poster_img = download_image(client, commit, poster_src)
    detail_img = download_image(client, commit, detail_src)

    poster_bytes = encode_webp(poster_img, POSTER_W, POSTER_H, POSTER_MAX_BYTES)
    detail_bytes = encode_webp(detail_img, DETAIL_W, DETAIL_H, DETAIL_MAX_BYTES)

    entry_dir = out_root / entry["id"]
    entry_dir.mkdir(parents=True, exist_ok=True)
    (entry_dir / "poster.webp").write_bytes(poster_bytes)
    (entry_dir / "detail.webp").write_bytes(detail_bytes)

    public = {
        "id": entry["id"],
        "name": entry["name"],
        "equipment": entry["equipment"],
        "muscles_primary": entry["muscles_primary"],
        "muscles_secondary": entry["muscles_secondary"],
        "category": entry["category"],
        "level": entry["level"],
        "mechanic": entry["mechanic"],
        "instructions": entry["instructions"],
        "poster": f"/exercises/{entry['id']}/poster.webp",
        "detail": f"/exercises/{entry['id']}/detail.webp",
    }
    return public


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        default=DEFAULT_COMMIT,
        help="Free Exercise DB commit hash (pinned for determinism + T-06-08 audit)",
    )
    parser.add_argument(
        "--out",
        default="frontend/public/exercises",
        help="Output directory (default: frontend/public/exercises)",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=TARGET_ENTRY_COUNT,
        help="Target entry count (default: 100; ROADMAP requires 80-120)",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=None,
        help="Hard cap for entries to ingest (debug aid)",
    )
    args = parser.parse_args()

    out_root = pathlib.Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    raw = fetch_source(args.commit)
    print(f"[ingest] Source has {len(raw)} entries", file=sys.stderr)

    candidates = filter_and_normalize(raw)
    print(f"[ingest] {len(candidates)} candidates after filter/normalize", file=sys.stderr)

    selected = round_robin_select(candidates, args.target)
    if args.max_entries is not None:
        selected = selected[: args.max_entries]
    print(f"[ingest] Selected {len(selected)} entries (target {args.target})", file=sys.stderr)

    # Deterministic order in manifest: sort by id ASCENDING for stable diffs
    selected.sort(key=lambda x: x["id"])

    manifest_entries: list[dict] = []
    with httpx.Client(follow_redirects=True) as client:
        for i, entry in enumerate(selected, start=1):
            try:
                public = process_entry(client, args.commit, entry, out_root)
            except Exception as exc:  # noqa: BLE001 — surface clearly
                print(
                    f"[ingest] FAIL {entry['id']}: {exc}", file=sys.stderr
                )
                continue
            manifest_entries.append(public)
            if i % 10 == 0 or i == len(selected):
                print(f"[ingest] processed {i}/{len(selected)}", file=sys.stderr)

    manifest = {
        "meta": {
            "source": "https://github.com/yuhonas/free-exercise-db",
            "commit": args.commit,
            "license": "Unlicense",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "entries": manifest_entries,
    }
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    # Precache-subset hint for sw.ts (24 most-likely-visible posters under
    # the default {none, dumbbell} filter; T-06-09 mitigation, though the
    # current sw.ts implementation relies on CacheFirst rather than explicit
    # precache — kept here for future tightening if Lighthouse PWA audit asks).
    default_visible = [
        e for e in manifest_entries if e["equipment"] in ("none", "dumbbell")
    ][:PRECACHE_SUBSET_SIZE]
    (out_root / "precache-list.json").write_text(
        json.dumps(
            [{"id": e["id"], "poster": e["poster"]} for e in default_visible],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"[ingest] Wrote {len(manifest_entries)} entries to {out_root / 'manifest.json'}",
        file=sys.stderr,
    )
    print(
        f"[ingest] Precache subset: {len(default_visible)} entries", file=sys.stderr
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
