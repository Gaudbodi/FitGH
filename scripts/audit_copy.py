#!/usr/bin/env python3
"""Health-claim copy audit — Phase 7 P7-D.1 (LEGAL-03).

Scans frontend + backend source for forbidden health-claim phrases and
verifies the required disclaimer is present in the root layout footer
AND on the onboarding consent screen.

Usage:
    python scripts/audit_copy.py            # informational; exit 0 always
    python scripts/audit_copy.py --strict   # exit 1 if any findings

Forbidden phrases (case-insensitive):
    - "will help you lose weight"
    - "achieves your goal"
    - "guaranteed results"
    - "medical advice"   (allowlisted on the line that contains
                          "not medical advice" — the disclaimer itself)
    - "treats <disease>" (treats diabetes/obesity/hypertension/cancer/disease)

Required disclaimer (exact string):
    "FitGH is a fitness tracking tool, not medical advice. Consult a
    qualified clinician for health decisions."

Must appear in:
    1. frontend/src/app/layout.tsx (root footer) OR
       frontend/src/app/(public)/layout.tsx
    2. one of frontend/src/app/(authed)/onboarding/**/*.tsx

Scope (scanned for forbidden phrases):
    frontend/src/**/*.{ts,tsx}
    frontend/src/**/*.md
    backend/app/**/*.py

Excluded (vendor / generated):
    node_modules/, .next/, public/exercises/, LICENSES.md, .planning/
    (the planning prose discusses the forbidden phrases by name as part of
    the audit definition — it does not ship to users).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_DISCLAIMER = (
    "FitGH is a fitness tracking tool, not medical advice. Consult a "
    "qualified clinician for health decisions."
)

# Forbidden phrases. Each entry is (label, compiled regex, allowlist_fn or None).
# The allowlist_fn takes (path, line) -> bool; returns True to SKIP the match.
FORBIDDEN_PATTERNS = [
    ("will help you lose weight", re.compile(r"will help you lose weight", re.I), None),
    ("achieves your goal", re.compile(r"achieves your goal", re.I), None),
    ("guaranteed results", re.compile(r"guaranteed results", re.I), None),
    (
        "medical advice",
        re.compile(r"\bmedical advice\b", re.I),
        # Disclaimer itself contains the phrase "not medical advice" —
        # that is exactly what we want it to say. Skip the match when
        # the line contains "not medical advice" (case-insensitive).
        lambda path, line: "not medical advice" in line.lower(),
    ),
    (
        "treats <disease>",
        re.compile(
            r"\btreats\b\s+(?:diabetes|obesity|hypertension|cancer|disease)",
            re.I,
        ),
        None,
    ),
]

# Scan globs (relative to repo root).
SCAN_GLOBS = [
    "frontend/src/**/*.ts",
    "frontend/src/**/*.tsx",
    "frontend/src/**/*.md",
    "backend/app/**/*.py",
]

# Path-substring blocklist (skip any file whose path contains any of these).
SKIP_SUBSTRINGS = (
    "node_modules",
    ".next",
    "public/exercises",
    "LICENSES.md",
    ".planning",
    "/.venv",
    "/__pycache__",
)


@dataclass(frozen=True)
class Finding:
    path: str
    line_no: int
    category: str  # "FORBIDDEN" | "MISSING_REQUIRED"
    description: str

    def render(self) -> str:
        if self.line_no > 0:
            return f"{self.path}:{self.line_no}: {self.category} {self.description}"
        return f"{self.path}: {self.category} {self.description}"


def _iter_files(root: Path):
    for pattern in SCAN_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            posix = path.as_posix()
            if any(s in posix for s in SKIP_SUBSTRINGS):
                continue
            yield path


def scan_forbidden(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line_no, line in enumerate(text.splitlines(), start=1):
            for label, regex, allowlist in FORBIDDEN_PATTERNS:
                match = regex.search(line)
                if not match:
                    continue
                if allowlist and allowlist(rel, line):
                    continue
                snippet = line.strip()[:120]
                findings.append(
                    Finding(
                        path=rel,
                        line_no=line_no,
                        category="FORBIDDEN",
                        description=f'"{label}" -> {snippet}',
                    )
                )
    return findings


def check_required_disclaimer(root: Path) -> list[Finding]:
    """Verify the required disclaimer string appears in both required spots."""
    findings: list[Finding] = []
    # Slot 1: root layout footer OR (public)/layout.tsx
    slot1_candidates = [
        root / "frontend" / "src" / "app" / "layout.tsx",
        root / "frontend" / "src" / "app" / "(public)" / "layout.tsx",
    ]
    if not _any_file_contains(slot1_candidates, REQUIRED_DISCLAIMER):
        findings.append(
            Finding(
                path="frontend/src/app/layout.tsx OR (public)/layout.tsx",
                line_no=0,
                category="MISSING_REQUIRED",
                description=(
                    "standard health-claim disclaimer not found in root "
                    "layout footer or (public)/layout.tsx"
                ),
            )
        )
    # Slot 2: any file under (authed)/onboarding/**
    onboarding_dir = root / "frontend" / "src" / "app" / "(authed)" / "onboarding"
    onboarding_files = list(onboarding_dir.rglob("*.tsx"))
    if not _any_file_contains(onboarding_files, REQUIRED_DISCLAIMER):
        findings.append(
            Finding(
                path="frontend/src/app/(authed)/onboarding/**/*.tsx",
                line_no=0,
                category="MISSING_REQUIRED",
                description=(
                    "standard health-claim disclaimer not found on any "
                    "onboarding screen"
                ),
            )
        )
    return findings


_WS_RUN = re.compile(r"\s+")


def _normalize_whitespace(s: str) -> str:
    """Collapse all whitespace runs to a single space so JSX line-wrapped
    text matches the canonical single-line needle.
    """
    return _WS_RUN.sub(" ", s).strip()


def _any_file_contains(paths, needle: str) -> bool:
    needle_norm = _normalize_whitespace(needle)
    for p in paths:
        try:
            if not p.is_file():
                continue
            haystack = _normalize_whitespace(
                p.read_text(encoding="utf-8", errors="replace")
            )
            if needle_norm in haystack:
                return True
        except OSError:
            continue
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root to scan (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any findings (default: exit 0 with summary)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"audit_copy: root '{root}' is not a directory", file=sys.stderr)
        return 2

    forbidden = scan_forbidden(root)
    missing = check_required_disclaimer(root)
    findings = forbidden + missing

    if not findings:
        print("audit_copy: clean — no forbidden phrases, all required disclaimers present.")
        return 0

    for f in findings:
        print(f.render())

    print(
        f"\naudit_copy: {len(findings)} finding(s) — "
        f"{len(forbidden)} forbidden, {len(missing)} missing required.",
        file=sys.stderr,
    )
    if args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
