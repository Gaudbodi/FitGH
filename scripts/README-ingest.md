# scripts/ingest_exercises.py — Workout Library Ingest

One-shot Python CLI that turns the **Free Exercise DB (Unlicense)** into the
FitGH Phase 6 static workout library: a curated ~100-entry `manifest.json`
plus 200 WebP images committed into `frontend/public/exercises/`.

Phase: **06-workout-library-pwa**. CONTEXT decisions:
**D-FREE-DB-ONLY**, **D-STATIC-FIRST**, **D-INGEST-PILLOW**, **D-WEBP-BUDGETS**.

---

## Run it

### 1. Set up an isolated venv (do NOT use `backend/.venv` — Render's Flask dyno would inherit Pillow)

```powershell
# Windows PowerShell — from repo root
python -m venv .venv-ingest
.venv-ingest\Scripts\Activate.ps1
pip install -r scripts/requirements-ingest.txt
```

```bash
# macOS / Linux — from repo root
python -m venv .venv-ingest
source .venv-ingest/bin/activate
pip install -r scripts/requirements-ingest.txt
```

### 2. Audit the pinned commit (T-06-08 mitigation — REQUIRED before each refresh)

Before running, open
<https://github.com/yuhonas/free-exercise-db/commits/main>, find the latest
trusted commit, and **read the diff vs. the previously pinned hash**. Look for:

- New image binaries with suspicious sizes or unfamiliar filenames.
- Removed/changed image URLs that would now point to attacker-controlled hosts.
- License-text changes (Free Exercise DB is Unlicense — verify it has not been
  relicensed).

The current pinned hash is set as `DEFAULT_COMMIT` at the top of
`scripts/ingest_exercises.py`. Update it via `--commit <new-sha>` and replace
the constant in the same PR. The pinning is the trust anchor; ad-hoc `main`
pulls bypass the audit.

### 3. Run

```bash
python scripts/ingest_exercises.py --commit <sha>
```

This downloads ~5 MB of JSON + ~200 source JPEGs and runs Pillow over each.
Expected runtime: **3–5 minutes** on a typical broadband line. The Pillow
WebP encoder is deterministic at fixed quality + method, so re-running with
the same `--commit` yields byte-identical outputs.

### 4. Inspect the output

```
frontend/public/exercises/
├── manifest.json              ~70-90 kB
├── precache-list.json         ~3 kB (first 24 posters; hint for sw.ts)
├── <id-1>/
│   ├── poster.webp            ≤30 kB
│   └── detail.webp            ≤80 kB
├── <id-2>/
…
```

Spot-check three `poster.webp` files in Explorer / Preview — they should
render as plausible exercise photos. Then stage with explicit paths:

```bash
git add frontend/public/exercises/
git status   # confirm ~200 WebPs + manifest.json + precache-list.json
```

**DO NOT use `git add -A`** — explicit paths only (CLAUDE.md rule).

---

## Taxonomies (used by the script + `frontend/src/lib/exercises.ts`)

### Equipment — 6 buckets

| Bucket          | Free Exercise DB raw values mapped here          |
| --------------- | ------------------------------------------------ |
| `none`          | `body only`, `null`                              |
| `dumbbell`      | `dumbbell`                                       |
| `bands`         | `bands`                                          |
| `kettlebells`   | `kettlebells`                                    |
| `barbell`       | `barbell`                                        |
| `pull-up bar`   | `pull-up bar`                                    |
| _(SKIPPED)_     | `machine`, `cable`, `medicine ball`, `foam roll`, `exercise ball`, `e-z curl bar`, `other` |

### Muscle — 8 buckets

| Bucket       | Free Exercise DB `primaryMuscles[0]` mapped here              |
| ------------ | ------------------------------------------------------------- |
| `chest`      | `chest`                                                       |
| `back`       | `middle back`, `lats`, `lower back`, `traps`, `neck`          |
| `legs`       | `quadriceps`, `hamstrings`, `calves`, `adductors`, `abductors`|
| `shoulders`  | `shoulders`                                                   |
| `arms`       | `biceps`, `triceps`, `forearms`                               |
| `core`       | `abdominals`                                                  |
| `glutes`     | `glutes`                                                      |
| `full-body`  | (fallback for entries with 4+ distinct primary buckets, or empty/unmapped primary) |

---

## Budget enforcement

The Pillow encoder loops:

```
quality = 72
while quality >= 40:
    bytes = encode(img, quality)
    if len(bytes) <= MAX:
        return bytes
    quality -= 4
raise RuntimeError("could not encode under MAX at quality >= 40")
```

- Poster: 320×240, max **30 kB**
- Detail: 800×600, max **80 kB**

If an entry raises, the operator should drop that id from the candidate pool
(by filtering it out manually) and re-run. In practice the Free Exercise DB's
source JPEGs are well within budget at q=72.

---

## App icon generation (one-off, separate from ingest)

For `frontend/public/icons/icon-192.png`, `icon-512.png`, and `maskable-512.png`:

```python
# Run in a Python REPL with Pillow installed (use .venv-ingest).
from PIL import Image, ImageDraw, ImageFont
import os
os.makedirs("frontend/public/icons", exist_ok=True)

EMERALD = (16, 185, 129)        # Tailwind emerald-500 / theme_color
WHITE   = (255, 255, 255)

def make_icon(size: int, padding: int = 0, path: str = "icon.png") -> None:
    img = Image.new("RGB", (size, size), EMERALD)
    draw = ImageDraw.Draw(img)
    # Use a default font scaled to the visible area
    visible = size - 2 * padding
    try:
        font = ImageFont.truetype("arialbd.ttf", int(visible * 0.6))
    except OSError:
        font = ImageFont.load_default()
    text = "F"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
        text, fill=WHITE, font=font,
    )
    img.save(path, format="PNG", optimize=True)

make_icon(192, 0,  "frontend/public/icons/icon-192.png")
make_icon(512, 0,  "frontend/public/icons/icon-512.png")
make_icon(512, 64, "frontend/public/icons/maskable-512.png")  # 64px safe-zone padding
```

---

## Threat-model notes

- **T-06-08 (malicious WebP via libwebp exploit):** Pillow re-encodes every
  image — the bytes shipped to users come from Pillow, not the source repo.
  Combined with the commit-hash pin + manual diff audit, this is the v1
  mitigation. Browser-side libwebp CVE patching is out of scope.
- **T-06-04 (cache-first stale-serves an updated WebP):** the SW's 30-day
  max-age auto-evicts; Serwist's precache hash bumps on every rebuild so a
  new ingest run is picked up by clients on next reload.

---

## Re-running

The script is idempotent. With the same `--commit`, output bytes are
identical, so `git status` should report no changes after a clean re-run.
This is the determinism contract — if it breaks (e.g. Pillow version bump
changes encoder output), document the new pinning in this README.
