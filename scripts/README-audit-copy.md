# Health-claim copy audit

`scripts/audit_copy.py` — Phase 7 LEGAL-03 deliverable.

Scans the frontend and backend source for health-claim language that could
expose FitGH to medical-advice liability, and verifies the standard
disclaimer is present in both required locations.

## Usage

```bash
# Informational run — prints any findings, exits 0.
python scripts/audit_copy.py

# Strict run — exits 1 if any findings (pre-launch gate, see LAUNCH.md §1).
python scripts/audit_copy.py --strict
```

Optional `--root <path>` to scan a different working tree.

## Forbidden phrases (case-insensitive)

| Phrase                | Why                                                              |
| --------------------- | ---------------------------------------------------------------- |
| `will help you lose weight` | Implies clinical efficacy.                                  |
| `achieves your goal`        | Implies guaranteed outcome.                                 |
| `guaranteed results`        | Direct guarantee — medical-advice red flag.                 |
| `medical advice`            | Allowed only inside the disclaimer string (line containing  |
|                             | "not medical advice" is allowlisted).                       |
| `treats <disease>`          | "treats diabetes/obesity/hypertension/cancer/disease" —     |
|                             | implies clinical treatment.                                 |

## Required disclaimer (exact string)

```
FitGH is a fitness tracking tool, not medical advice. Consult a qualified clinician for health decisions.
```

Must appear in:

1. `frontend/src/app/layout.tsx` (root layout footer) **or**
   `frontend/src/app/(public)/layout.tsx`
2. At least one of `frontend/src/app/(authed)/onboarding/**/*.tsx`

## Scope

Scanned:

- `frontend/src/**/*.{ts,tsx,md}`
- `backend/app/**/*.py`

Excluded (skipped by path-substring match):

- `node_modules/`, `.next/`, `public/exercises/`
- `LICENSES.md` — third-party licence text
- `.planning/` — planning prose discusses the forbidden phrases by name as
  part of the audit definition; that prose never ships to users
- `__pycache__/`, `/.venv/`

## CI policy

v1.0 does NOT add this as a CI gate (per the Phase 7 anti-patterns — Render-
only rewrite drops CI gates beyond pytest + pnpm build). The intent is the
operator runs `python scripts/audit_copy.py --strict` as a manual pre-launch
step. If a regression motivates promoting it to a GitHub Actions job in
v1.1, do so then.
