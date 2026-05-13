# Avatar — design contract

Static SVG sprite implementation. Rive runtime was the canonical CLAUDE.md
pick but is deferred to v1.1 per phase-05 CONTEXT.md `D-AVATAR-STATIC-SVG`.

## File layout

- `public/avatar-sprite.svg` — single sprite. 20 named `<g id="state-...">`
  blocks reuse 5 body silhouettes + 2 heads + 3 direction arrows from the
  `<defs>` section.
- `src/components/avatar/avatar-state.ts` — pure helpers
  (`bmiBand`, `goalDirection`, `avatarStateKey`).
- `src/components/avatar/avatar.tsx` — `<Avatar>` client component, renders
  `<svg><use href="/avatar-sprite.svg#state-..." />`.

## State naming scheme

`state-{sex}-{bmi-band}-{direction}`

- `sex`: `m` | `f`
- `bmi-band`: `slim` | `healthy-lean` | `healthy-firm` | `heavier` | `much-heavier`
- `direction`: `toward` | `steady` | `away`

The full 5x2x3 = 30 grid is theoretical. The shipped sprite includes the
**20 most-used states**, picked to cover the common combos (every BMI band
has at least one direction; both sexes have all 5 bands). Missing combos
gracefully fall back to the nearest available state at the consumer level
(see Avatar.tsx fallback).

## BMI band cutoffs

Match the Mifflin-St Jeor convention used by `app.lib.tdee`:

| Band            | BMI range            |
| --------------- | -------------------- |
| `slim`          | < 18.5               |
| `healthy-lean`  | 18.5 -- 24.99        |
| `healthy-firm`  | 25.0 -- 27.99        |
| `heavier`       | 28.0 -- 31.99        |
| `much-heavier`  | >= 32.0              |

Boundary semantics: 24.99 -> `healthy-lean`, 25.00 -> `healthy-firm`.

## Goal direction

Computed from the 7-day weight slope vs the user's `primary_goal` sign:

- `weight_loss`: negative slope -> `toward`; positive -> `away`; flat -> `steady`.
- `muscle_gain`: positive slope -> `toward`; negative -> `away`; flat -> `steady`.

Slope threshold: `+/- 0.1 kg/week`. Empty array or single weight entry -> `steady`.

## Theming via CSS variables

The sprite root sets:

```svg
<svg style="--skin-tone:#d4a574; --clothing-color:#2563eb; --accent:#10b981">
```

Consumers can override on the `<svg>` element that holds the `<use>`:

```tsx
<svg style={{ '--skin-tone': '#a87b53', '--clothing-color': '#dc2626' }}>
  <use href="/avatar-sprite.svg#state-m-healthy-firm-toward" />
</svg>
```

## Adding a new state

1. Decide a name following the `state-{sex}-{bmi}-{dir}` scheme.
2. Append a `<g id="state-...">` block at the bottom of `avatar-sprite.svg`
   composing the existing `body-*`, `head-*`, `arrow-*` defs.
3. Re-run the verifier script in `phase-05/05-PLAN.md` Task B.1 — it asserts
   the count of `id="state-*"` matches the planned total.
4. Update `bmiBand` / `goalDirection` in `avatar-state.ts` if the new state
   is reached via a new BMI cutoff or goal-direction rule.

## Reduced-motion + slow-connection interplay

The sprite's `@keyframes breath` and `@keyframes blink` run by default.
`globals.css` adds the `[data-motion='disabled']` rule applied at the
document root by `MotionDetector` on:

- `prefers-reduced-motion: reduce` media match, OR
- `navigator.connection.saveData === true`, OR
- `navigator.connection.effectiveType` in `{2g, slow-2g, 3g}`.

When the attribute is set, **all** CSS transitions and animations site-wide
collapse to `0.001ms` — including the avatar's breath/blink. The sprite's
internal `@media (prefers-reduced-motion: reduce) { animation: none }` is a
belt-and-braces fallback in case the sprite is consumed outside the FitGH
shell.

## Bundle cost

- Sprite raw: ~8 kB.
- Sprite gzipped: ~2 kB.
- The Avatar component itself is < 1 kB (pure JSX wrapper).

The sprite is served from `/public` so it doesn't add to the dashboard
JS bundle; the browser fetches it once and caches it.
