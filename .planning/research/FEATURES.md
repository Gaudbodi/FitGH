# FEATURES — FitGH Feature Landscape

**Domain:** Fitness / calorie tracking with image-based food logging, targeted at Ghanaians (in-Ghana + diaspora).
**Researched:** 2026-05-11
**Confidence:** MEDIUM-HIGH (table stakes and anti-features HIGH; Ghana kcal numbers MEDIUM — drawn from recipe sources and FAO INFOODS West Africa rather than per-restaurant measurement, so confidence is wide bands not point estimates).

This document is the input to REQUIREMENTS.md. Every entry is annotated with **Complexity (S/M/L)** so the requirements step can sequence work.

---

## Table Stakes

Features that v1 must ship or users churn inside a session. Benchmarked against MyFitnessPal, Lose It, Cronometer, Yazio, Noom in 2026.

| # | Feature | Why expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| TS-1 | Account + profile (name, sex, height, weight, age, goal) | Every tracker collects this; nothing personalises without it | S | Single onboarding flow; persist in MongoDB. Goal = `weight_loss` \| `muscle_gain` per PROJECT.md |
| TS-2 | Daily calorie target (TDEE ± deficit/surplus) | Tracker without a target is just a journal; users need a number to hit | S | Mifflin-St Jeor BMR formula × activity factor; -300 to -500 kcal for cut, +200 to +300 for bulk. Recalculate on every weight log per Mifflin-St Jeor guidance. Confidence HIGH — equation is industry standard with ±10% vs metabolic analyser ([Inch Calculator](https://www.inchcalculator.com/mifflin-st-jeor-calculator/)) |
| TS-3 | Daily protein target (for muscle gain goal) | Muscle-gain users expect macro splits, not just kcal | S | 1.6–2.2 g/kg bodyweight is the accepted band; surface only when goal = muscle_gain to keep onboarding clean for cut users |
| TS-4 | Daily intake log (meals consumed today, running totals vs target) | The home screen of every tracker; primary daily-return surface | M | Meal entry, edit, delete; running kcal + protein sum; "remaining" pill |
| TS-5 | Weight log + history | Single weight today is useless without trend; gates re-calibration of TDEE | S | Date-stamped weight entries; simple list view in v1, chart in TS-7 |
| TS-6 | History view (past days/meals) | Users want to look back at what they ate; retention driver | S | List of dates, drill into meals; no aggregation in v1 |
| TS-7 | Animated progress chart (weight + kcal balance) | Charts are now expected; static numbers feel dated. Lottie/Rive ticks the brief's "fluid animations" requirement | M | Weight line chart + per-day kcal-vs-target bars; animated entry/transitions |
| TS-8 | Weekly streak | Streaks are the single best-validated retention mechanic in habit apps (Duolingo, Noom, every modern tracker) | S | Day counter where any meal was logged; reset on missed day with grace window |
| TS-9 | Exercise library (browse all) | Users expect a "what to do" surface even if they don't follow a programme | M | List + detail view; 80–120 exercises v1 (see Workout Asset Sources below) |
| TS-10 | Exercise search + equipment filter | Equipment filter is the differentiator in TS-9; search is the table-stakes inside it | S | Filter by equipment, primary muscle, force (push/pull); text search on name |
| TS-11 | Mobile-friendly responsive UI | Mid-tier Android is the dominant device for in-Ghana users (per PROJECT.md) | M | Mobile-first Tailwind layout; thumb-reachable primary actions; viewport-correct |
| TS-12 | Food image capture → kcal estimate (the core loop) | This IS the wedge; without it the product has no reason to exist over MyFitnessPal | L | Camera capture + file upload, server-side LLM-vision call, dish + portion + kcal response. See Food Vision UX Patterns below |
| TS-13 | Correct dish + portion after the estimate | Foodvisor / Cal AI / Bitesnap all do this — research shows manual correction "can significantly improve performance" ([PMC review](https://pmc.ncbi.nlm.nih.gov/articles/PMC10348006/)). Without it accuracy stays low | M | Edit dish name (search Ghana table), edit grams/portion, save corrected meal |
| TS-14 | Add a meal manually (no photo) | Cameras break, lighting is bad, sometimes you just typed it. Every tracker has it | S | Text search of Ghana table + generic foods; quantity input |
| TS-15 | Privacy disclosure on food image upload | Required by PROJECT.md constraint; minimum-viable trust | S | One-liner on capture screen + linked policy. Not retaining images server-side beyond estimation per PROJECT.md |

**Equipment filter categories users expect** (TS-10): `none` (bodyweight), `dumbbells`, `resistance bands`, `pull-up bar`, `kettlebell`, `barbell`, `full home gym`, `commercial gym`. Both wger and ExerciseDB tag these natively, so no custom taxonomy work.

---

## Differentiators

Features that win the Ghanaian + diaspora market vs MyFitnessPal / Lose It / Cronometer / Yazio / Noom. None of these incumbents have meaningful Ghanaian-food coverage; that's the entire wedge.

| # | Differentiator | Why it wins | Complexity | Implementation note |
|---|----------------|-------------|------------|---------------------|
| D-1 | **Curated Ghanaian-food kcal table** | MyFitnessPal's database is user-submitted (high noise) and Western-centric. Jollof, banku, waakye, etc. are either missing or buried under contradictory user entries with ±15% error band ([Nutrition Research Review 2026](https://nutrition-research-review.com/articles/systematic-review-calorie-tracking-accuracy-2026/)). Curating ~50 dishes calibrated against FAO West African Food Composition Table 2019 is achievable, differentiated, and defensible | M | See Ghanaian Foods Starter Catalogue below — 50 entries with portion + kcal range + source |
| D-2 | **LLM-vision dish identification calibrated against Ghana table** | Generic vision models systematically struggle with culturally specific dishes ([Arxiv benchmark](https://arxiv.org/html/2507.07048v1)). Passing the Ghana table as context in the LLM prompt forces it to map to known dishes rather than guessing "rice with sauce". This is the cheapest path to Ghana-specific accuracy without training a model | L | Server-side Python (Flask) calls Claude vision or GPT-4o with system prompt = Ghana dish catalogue + portion heuristics. Output JSON: `{dish, portion_grams, kcal_estimate, confidence}` |
| D-3 | **Animated avatar reflecting profile + progress** | Competitor coverage: Visbody, MeThreeSixty, ShapeScale all do this but require a phone scan or hardware. None are calorie trackers — they're measurement tools. A simple Lottie/Rive avatar parameterised by sex + BMI band would be unique among Ghana-targeted apps and competitive with global trackers (none have this). Recommended pattern: **Rive state machine** keyed by sex + BMI band + goal direction (Lottie is for one-shot illustrations, Rive handles reactive state) per [Callstack comparison](https://www.callstack.com/blog/lottie-vs-rive-optimizing-mobile-app-animation) | M | One Rive file, ~5 BMI bands (underweight / lean / healthy / overweight / obese) × 2 sexes = 10 visual states. Interpolate between bands as weight changes. Keep file under 200 KB |
| D-4 | **Workout library with equipment filter tuned to home/gym/none** | Most apps assume gym access. In-Ghana cohort often has bodyweight or limited home equipment. Default filter to `none` + `dumbbells` and surface that on first run | S | Filter UI on workout list page; default state matters more than the filter itself |
| D-5 | **Data-light delivery (page-weight budget, lazy assets, image compression, offline workout cache)** | Sub-Saharan Africa mobile data is ~$3.31/GB or ~18% of monthly income ([RAMP Index](https://researchictafrica.net/project/africa-mobile-pricing-ramp-index/)). Concrete patterns: **(a)** PWA install prompt, **(b)** service worker with cache-first for workout assets, network-first for meal data, stale-while-revalidate for charts ([MagicBell guide](https://www.magicbell.com/blog/offline-first-pwas-service-worker-caching-strategies)), **(c)** AVIF / WebP imagery (~25–50% smaller than JPEG), **(d)** lazy-load below-fold, **(e)** hard page-weight budgets (initial route < 200 KB JS, < 100 KB images) | M | Next.js App Router image component handles AVIF; PWA via next-pwa; budget enforced in CI via Lighthouse / bundlesize |
| D-6 | **Diaspora-aware portion phrasing** | Ghana table portions described both in grams AND in cultural units ("1 ball of banku", "1 ladle of soup", "half a tilapia") — diaspora users may not have a kitchen scale and in-Ghana users don't think in grams | S | Two-field display: `display_portion: "1 ball (~200g)"`; LLM prompt instructs cultural-unit-first output |
| D-7 | **Goal-aware home screen** | Show protein progress prominently for muscle-gain users; show kcal-deficit progress for weight-loss users. Generic tracker shows both equally; goal-aware version reduces cognitive load | S | Conditional render on profile.goal |
| D-8 | **Correction feedback loop** | "Each correction informs subsequent estimates" per PROJECT.md. In v1 this is per-user: corrected dish becomes the user's default when their next photo matches that dish. In v2 it could aggregate cross-user. Foodvisor explicitly does this and it's the single biggest driver of long-term accuracy ([Foodvisor portion help](https://foodvisor.zendesk.com/hc/en-us/articles/360013672119)) | M | Store `user_corrections: {original_dish, corrected_dish, count}`; on next vision result, if (dish, user) has correction history, surface corrected dish as default |

---

## Anti-Features

Things to deliberately NOT build in v1. The user already excluded several; this section confirms those and adds others.

| # | Anti-feature | Why excluded |
|---|--------------|--------------|
| AF-1 | **Social feed / following / sharing** (already excluded) | Confirmed. Social mechanics demand moderation, reporting, abuse handling, blocking, privacy controls — months of work that doesn't move the core loop. Defer until PMF |
| AF-2 | **Wearable integrations** (already excluded) | Confirmed. Apple Watch / Fitbit / Garmin SDKs are platform-specific, require native app shells, and don't move the calorie loop. Manual weight entry covers v1 |
| AF-3 | **Payments / subscriptions** (already excluded) | Confirmed. v1 is free per PROJECT.md. Payment infra (Stripe, Paystack for Ghana) is its own quarter of work |
| AF-4 | **Native iOS/Android apps** (already excluded) | Confirmed. PWA covers both cohorts; native ships post-PMF |
| AF-5 | **Scraping Pinterest / Instagram / creator accounts** (already excluded) | Confirmed. ToS + copyright violation; licensed sources cover the need |
| AF-6 | **Self-trained food-vision model** (already excluded) | Confirmed. LLM vision + Ghana table is the v1 path |
| AF-7 | **Barcode scanner** | Ghana's packaged-food retail is fragmented; many staples (jollof, fufu) aren't packaged at all. Barcode UX presumes a Western grocery world. Skip until diaspora-user signal demands it |
| AF-8 | **Recipe builder / meal planner** | Compounds scope with both UX and data work. The core loop is "snap meal → see kcal", not "plan meal in advance". Validate the snap loop first |
| AF-9 | **Water tracking, sleep tracking, mood, period** | Each is a feature category in itself with retention dynamics distinct from the kcal loop. Adding them dilutes the product. If signal demands, add one at a time post-PMF |
| AF-10 | **Coach / chat / 1-on-1 expert** (already excluded) | Confirmed. Service-business dynamics, not product dynamics. Not the wedge |
| AF-11 | **Workout video player with playback controls, sets/reps timer, rest timer, programme builder** | A complete training app inside the calorie tracker — months of work. v1 workout library is browsable reference, not a guided session. If users ask, that's a v2 phase |
| AF-12 | **Push notifications to a service worker / native bridge** | Adds infra (FCM / VAPID keys, opt-in dance, OS quirks). Email reminders are cheaper and address the same retention angle |
| AF-13 | **Multi-user / family accounts** | Doubles the data model and the auth flow. Single user per account in v1 |
| AF-14 | **Restaurant menu / chain lookup** | Useful for diaspora users at chain restaurants, but the Ghana table is the wedge. Defer |
| AF-15 | **Detailed micronutrient tracking** (vitamins, minerals beyond protein) | Cronometer's territory. Adds data-entry burden and UI complexity. v1 = kcal + protein only |
| AF-16 | **Localisation / multi-language** | Twi / Ga / Ewe localisation is valuable long-term but English covers both cohorts in v1. Single-language ships faster |

---

## Ghanaian Foods Starter Catalogue

**v1 recommendation: 50 dishes.** Rationale: this is the smallest set that covers daily Ghanaian eating across regions (Akan / Ga / Ewe / Northern) and across meal types (breakfast, lunch, dinner, snacks, drinks). Below 30 leaves embarrassing gaps; above 60 is curation overhead without proportional coverage.

**Kcal ranges, not point estimates.** Numbers below are typical-portion bands drawn from recipe-site nutrition panels, FAO West African Food Composition Table 2019 ingredients, and published Ghanaian nutrition research. Confidence is wide (±20%) because dish prep varies by household. The LLM-vision prompt should pass the band, not a single number, and the user-correction loop tightens individual cases.

**Sources:** FAO/INFOODS Food Composition Table for Western Africa 2019 ([intake.org](https://www.intake.org/resource/faoinfoods-food-composition-table-west-africa-2019)) for ingredient baselines; PMC4864731 ([Mineral contents of popular Ghanaian foods](https://pmc.ncbi.nlm.nih.gov/articles/PMC4864731/)) for prepared-dish profiles; recipe sites (snapcalorie.com, mynetdiary.com, fatsecret.com) for portion calibration; USDA Food Data Central as a proxy for cross-cultural ingredients (rice, beans, plantain, oil).

### Starches & staples (10)

| # | Dish | Typical portion | Kcal/portion | Source confidence |
|---|------|-----------------|--------------|-------------------|
| 1 | Jollof rice (plain) | 1 plate, ~250 g | 380–500 | MEDIUM (140 kcal/100g per snapcalorie; +oil in prep) |
| 2 | Jollof rice with chicken | 1 plate + 1 piece chicken | 600–750 | MEDIUM |
| 3 | Waakye (plain) | 1 portion, ~300 g | 320–420 | MEDIUM (278 kcal/serving per mynetdiary) |
| 4 | Waakye with gari, egg, fish | full bowl | 600–800 | LOW (compounding sides) |
| 5 | Banku (1 ball) | ~200 g | 240–280 | MEDIUM (250 kcal/200g consensus) |
| 6 | Kenkey (Ga, 1 ball) | ~300 g | 380–450 | MEDIUM (400 kcal/ball cited) |
| 7 | Fufu (1 serving) | ~250 g pounded | 280–360 | MEDIUM (267 kcal/100g dry, hydrates 3×) |
| 8 | Plain rice (white, 1 cup cooked) | ~150 g | 200–230 | HIGH (USDA) |
| 9 | Tuo zaafi (1 ball) | ~250 g | 320–400 | MEDIUM (PMC mineral study) |
| 10 | Omo tuo (rice balls, 2) | ~250 g | 300–360 | LOW |

### Soups & stews (10)

| # | Dish | Typical portion | Kcal/portion | Source confidence |
|---|------|-----------------|--------------|-------------------|
| 11 | Palm nut soup (abenkwan) | 1 bowl, ~400 ml | 350–500 | MEDIUM (palm fruit + oil dense; Kitchn recipe) |
| 12 | Groundnut soup (with chicken) | 1 bowl | 400–550 | MEDIUM |
| 13 | Light soup (with fish or meat) | 1 bowl | 180–280 | MEDIUM (tomato-water based; lower) |
| 14 | Okra (okro) soup / stew | 1 bowl | 200–320 | MEDIUM |
| 15 | Kontomire stew (palaver sauce) | 1 portion | 250–380 | MEDIUM (greens + egusi/agushi + oil) |
| 16 | Garden egg stew | 1 portion | 200–300 | MEDIUM |
| 17 | Tomato / fish stew | 1 ladle (~150 g) | 180–280 | MEDIUM |
| 18 | Egusi (agushi) stew | 1 portion | 350–450 | MEDIUM (melon seed + oil heavy) |
| 19 | Pepper soup (goat / fish) | 1 bowl | 180–280 | MEDIUM |
| 20 | Red red (bean stew, plantain) | 1 plate | 380–450 | MEDIUM (412 kcal/serving per Honest Food) |

### Proteins & sides (10)

| # | Dish | Typical portion | Kcal/portion | Source confidence |
|---|------|-----------------|--------------|-------------------|
| 21 | Grilled tilapia | 1 whole medium fish | 280–380 | MEDIUM (lean fish; varies with skin/oil) |
| 22 | Fried tilapia | 1 whole medium fish | 400–550 | MEDIUM (frying adds ~150–200) |
| 23 | Chicken stew piece (one) | 1 thigh/drumstick | 220–320 | HIGH (USDA chicken + stew oil) |
| 24 | Fried chicken (1 piece) | 1 piece | 280–400 | HIGH |
| 25 | Beef stew portion | ~100 g cooked | 240–340 | MEDIUM |
| 26 | Goat stew portion | ~100 g cooked | 220–320 | MEDIUM |
| 27 | Boiled egg | 1 large | 70–80 | HIGH (USDA) |
| 28 | Fried egg (in oil) | 1 large | 90–120 | HIGH |
| 29 | Shito (pepper sauce) | 1 tbsp (~15 g) | 30–60 | LOW (oil-heavy, recipe varies) |
| 30 | Gari (raw, sprinkled) | 2 tbsp (~30 g) | 100–120 | HIGH (cassava flour, USDA proxy) |

### Snacks, sides, fried (10)

| # | Dish | Typical portion | Kcal/portion | Source confidence |
|---|------|-----------------|--------------|-------------------|
| 31 | Kelewele (spicy fried plantain) | 1 small bowl | 220–460 | MEDIUM (220 per chef sources; up to 463 deep-fried per healthier-steps comparison) |
| 32 | Fried plantain (kaakro / tatale) | 3 pieces | 200–280 | MEDIUM |
| 33 | Boiled plantain | 1 medium | 180–220 | HIGH (USDA) |
| 34 | Roasted plantain (bofrot variants) | 1 medium | 160–200 | HIGH |
| 35 | Yam (boiled, ~200g) | 1 portion | 220–280 | HIGH |
| 36 | Yam chips (fried) | 1 portion | 320–450 | MEDIUM |
| 37 | Bofrot (doughnut, 1) | 1 piece | 150–200 | MEDIUM |
| 38 | Meat pie (Ghanaian style) | 1 piece | 280–380 | MEDIUM |
| 39 | Spring roll / kebab (1 stick) | 1 stick | 80–140 | MEDIUM |
| 40 | Chofi (fried turkey tail) | ~100 g | 320–450 | LOW (fatty cut, fried) |

### Breakfast, drinks, fruits (10)

| # | Dish | Typical portion | Kcal/portion | Source confidence |
|---|------|-----------------|--------------|-------------------|
| 41 | Hausa koko (millet porridge) | 1 mug | 150–220 | MEDIUM |
| 42 | Tom Brown (cereal porridge) | 1 mug | 200–280 | MEDIUM |
| 43 | Oats porridge (with milk + sugar) | 1 bowl | 250–350 | HIGH |
| 44 | Koko + koose (porridge + bean cake) | 1 mug + 2 koose | 350–500 | MEDIUM |
| 45 | Koose (bean cake, 1) | 1 piece | 80–120 | MEDIUM |
| 46 | Sobolo (hibiscus drink, sweetened) | 1 cup (~250 ml) | 80–140 | MEDIUM |
| 47 | Asaana (corn drink) | 1 cup | 120–200 | LOW |
| 48 | Bissap / fresh fruit juice | 1 cup | 80–160 | MEDIUM |
| 49 | Pineapple (sliced) | 1 cup | 70–90 | HIGH (USDA) |
| 50 | Mango (1 medium) | 1 fruit | 130–200 | HIGH (USDA) |

**Implementation note for D-1 + D-2:** Store each entry with fields `{id, name, aliases[], region, meal_type, portion_description, portion_grams, kcal_low, kcal_high, kcal_default, protein_g, source_url, source_confidence}`. Pass the catalogue (id + name + portion_description + kcal_default) to the LLM-vision system prompt so it can map any photo to a catalogue entry.

---

## Workout Asset Sources

**Recommendation: Primary = Free Exercise DB (yuhonas). Fallback = wger. Avoid MuscleWiki and ExerciseDB for v1.**

### Comparison

| Source | Count | Media | Licence | Verdict |
|--------|-------|-------|---------|---------|
| [Free Exercise DB (yuhonas)](https://github.com/yuhonas/free-exercise-db) | ~800 | Images (JPG, ~2 per exercise) | **Unlicense (public domain)** — no attribution required | **Primary.** Cleanest legal posture, ~800 exercises is plenty for v1, JSON is local (no API dependency, no rate limits), images are smaller than GIFs — fits data-light constraint |
| [wger](https://github.com/wger-project/wger) | ~400 | Images + some GIFs | **CC-BY-SA 3.0** (exercise data) — attribution + share-alike required | **Fallback for missing exercises.** Adds breadth where Free Exercise DB is thin. Share-alike clause means any derived dataset must also be CC-BY-SA — acceptable if we don't bundle wger data into a paid product, but the share-alike viral clause needs care |
| [ExerciseDB](https://exercisedb.dev/) | ~1,500 free / 11,000 paid | GIFs at 180p free, higher res paid | Source "open" but distribution via RapidAPI free tier with usage caps and 180p GIFs only — paid tier for HD | **Avoid for v1.** GIFs are heavy (data-light violation), API dependency is fragile, paid tier needed for production-quality media |
| [MuscleWiki](https://musclewiki.com/terms) | ~2,000 | Videos | **Non-commercial use only**, written permission required for redistribution, attribution mandated | **Avoid.** Terms explicitly forbid commercial use without permission; even if v1 is free, "free" is monetisation-deferred not non-commercial. Legal risk |
| exrx.net | ~1,400 | Static images | All rights reserved, read-only reference | **Avoid.** Not redistributable |
| GIPHY | Unbounded | GIFs | Per-asset licensing; mixed | **Avoid.** No bulk licence, ToS varies per uploader |

### v1 catalogue size: 80–120 exercises

**Reasoning:**
- Free Exercise DB has ~800; that's too many to curate quality for v1 and too many for users to browse without overload.
- A workout library is **a reference, not a programme** in v1 (per AF-11). Users browse and pick; they don't follow guided sessions yet.
- 80–120 covers: 8 muscle groups × ~12 exercises each, balanced across equipment categories.
- Below 60 feels empty; above 150 feels unbrowsable on mobile.
- Curation strategy: start with all bodyweight exercises (~30 from Free Exercise DB), all dumbbell exercises (~30), plus 20–40 covering bands / pull-up bar / kettlebell / barbell. This biases toward what the in-Ghana cohort actually has access to.

### YouTube embeds

Per PROJECT.md, official YouTube embeds with attribution are permitted. Use cautiously — embeds defer image-budget cost to YouTube's player (heavy), so:
- Don't embed by default; show a thumbnail and let users tap-to-load (saves ~500 KB of player JS per page).
- Only embed channels that have explicitly permitted embedding (default YouTube setting).
- Curate 1 reference video per exercise as enhancement, not requirement.

---

## Food Vision UX Patterns

Synthesised from MyFitnessPal Meal Scan, Foodvisor, Cal AI (now MFP-acquired), Bitesnap, Calorie Mama, and academic reviews ([PMC10348006](https://pmc.ncbi.nlm.nih.gov/articles/PMC10348006/)).

### Pattern 1: The estimate → confirm → correct flow

The industry-converged flow:

```
1. Capture / upload photo
2. Show loading state with progress hint ("Identifying dish...", "Estimating portion...")
3. Show estimate with explicit confidence ("We think this is jollof rice with chicken, ~620 kcal — is that right?")
4. Two-tap accept: [Looks right] [Edit]
5. Edit screen: change dish (search Ghana table), change portion (slider or grams input), save
```

The "is that right?" framing is the single most important UX detail: it primes the user to correct rather than passively accept, which **improves long-term accuracy** ([PMC review](https://pmc.ncbi.nlm.nih.gov/articles/PMC10348006/) — "manual modification can improve the accuracy of predictions").

### Pattern 2: Portion estimation strategies

LLM-vision MAPE on portion estimation is ~36% ([PMC12513282 — Performance Evaluation of 3 LLMs](https://pmc.ncbi.nlm.nih.gov/articles/PMC12513282/)). That's the limiting factor on overall accuracy.

Mitigations in order of cost:

1. **Cultural-unit portion phrasing (CHEAP, ESSENTIAL).** "1 ball of banku (~200 g)", "half a tilapia", "1 ladle of soup". Users recognise these instantly; grams require a kitchen scale most users don't have. Pass these as the portion vocabulary to the LLM.
2. **Reference-object hinting in capture screen (CHEAP).** Show a hint: "Place a coin, phone, or fork in the photo for better portion accuracy." Doesn't force it, but trains good habits.
3. **Default to a typical portion when LLM uncertain (CHEAP).** If LLM confidence is low, fall back to the catalogue's typical portion rather than its own guess.
4. **Volumetric estimation with SAM segmentation (EXPENSIVE).** Some apps use Segment Anything to mask the plate, estimate volume, compute kcal. Out of scope for v1 — the LLM does the segmentation implicitly.

### Pattern 3: Cold-start "unknown food"

When LLM returns low confidence or "unknown":

```
1. Don't fail. Show: "We couldn't confidently identify this. Want to log it manually?"
2. Surface the manual-entry path (TS-14) pre-filled with a placeholder ("unknown meal").
3. Optional: show 3 closest catalogue matches as quick-picks ("Maybe... jollof rice? waakye? fried rice?").
4. Allow saving as "unknown meal — 500 kcal estimate" with a note that the user can correct later.
```

The anti-pattern: making the user retake the photo or blocking save. Foodvisor reviews repeatedly flag this as a frustration ([Satu Kyrolainen UX review](http://www.satukyrolainen.com/foodvisor-the-good-the-bad-and-the-ux/)).

### Pattern 4: Correction-as-learning (D-8)

Per-user correction store (v1):
- Each `(user, photo_dish_guess, corrected_dish)` correction is recorded.
- On next photo, if the LLM guess matches a user's prior correction pattern, surface the corrected dish as default.
- Display "We learned from your last correction" subtly to reinforce the loop.

Cross-user aggregation (defer to v2): if 100 users correct "rice with sauce" → "waakye" on the same kind of photo, that signal updates the prompt.

### Pattern 5: Privacy-respecting image handling

Per PROJECT.md: images not retained server-side beyond estimation unless user opts in to a history feature.

Concrete pattern:
- Upload image to Flask backend over HTTPS.
- Flask streams the image to the LLM-vision API.
- Flask stores only `{dish, portion, kcal, timestamp, user_id}` — not the image bytes.
- One-liner on the capture screen: "Photo is sent to our AI partner to estimate calories. We don't store it."
- Link to a real privacy policy.

This is the minimum trust posture; do not ship without it.

---

## Open Questions for Requirements

These are deliberate non-decisions for the REQUIREMENTS.md step to resolve. Each is flagged here so that step is faster.

1. **Which LLM vision provider — Claude or GPT-4o?**
   - Performance is comparable (MAPE ~36% both; [PMC12513282](https://pmc.ncbi.nlm.nih.gov/articles/PMC12513282/)). Cost differs and pricing changes. Decision: ship with one, abstract the call behind an interface so swapping is a config change. Default recommendation: Claude (since user has Anthropic context), but verify per-call pricing at requirements time.

2. **What's the daily-target activity-factor UX?**
   - Standard Mifflin-St Jeor multipliers (sedentary 1.2 / light 1.375 / moderate 1.55 / active 1.725 / very active 1.9) work but are jargon-heavy. Modern apps use plain-English buckets ("Mostly desk", "Some walking", "Workout 3–4×/week"). Recommend the plain-English version; map to multipliers internally.

3. **PWA install prompt — when and where?**
   - Prompting on first session is intrusive; never prompting loses installs. Convention: prompt after user has logged ≥3 meals (signals retention). Configurable.

4. **Image-budget targets — what are the exact numbers?**
   - Recommend: initial route ≤ 200 KB JS gzipped, ≤ 100 KB images above-fold, ≤ 500 KB total above-fold, Lighthouse performance ≥ 90 on simulated mid-tier Android. CI enforces these.

5. **Workout asset hosting — bundle Free Exercise DB images or CDN them?**
   - Free Exercise DB images total ~80 MB across 800 exercises. Don't bundle. Host on a CDN (Vercel's static asset CDN works), lazy-load per exercise, cache aggressively in service worker on first view.

6. **How many exercises to ship in v1?**
   - Stated above: 80–120. Need a curated list before phase 2 (workout library) starts. Curation is itself a discrete task — flag as a research/curation phase deliverable.

7. **Ghana table — JSON file or MongoDB collection?**
   - 50 entries is small enough for a static JSON file imported by both Next.js and Flask. MongoDB collection makes sense only when the catalogue grows past ~200 entries or when cross-user corrections (D-8 v2) need to update it. Recommend: JSON in v1, migrate to MongoDB when D-8 cross-user lands.

8. **Avatar visual style and BMI banding — do we have design assets?**
   - Rive avatar with 10 visual states is a design deliverable that doesn't exist yet. Either commission a Rive file (~£200–500 from a marketplace) or use a simpler 2D SVG morph parameterised by BMI band. Decide at requirements time.

9. **Onboarding — single screen or multi-step?**
   - Multi-step (height → weight → age → sex → goal) is the modern pattern (Yazio, Noom). Single screen ships faster. Recommend multi-step for v1 since it's the user's first impression and bounces are expensive. ~5 screens, each one input.

10. **Streak grace period?**
    - Strict daily streaks punish users who genuinely intended to log but forgot. Recommend a 1-day grace per week (user can "freeze" streak once per week). Tweakable.

---

**End of FEATURES.md** — feeds REQUIREMENTS.md.
