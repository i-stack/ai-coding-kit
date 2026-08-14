#!/usr/bin/env python3
"""Validate canonical Skill entrypoints and reference freshness metadata."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "source-truth.json"
HEADER = re.compile(r"^<!--\s*last-verified:\s*(\d{4})-(\d{2})\s*-->$")


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    max_age = int(data["max_age_months"])
    declared = data["skills"]
    discovered = {path.parent.name for path in ROOT.glob("*/SKILL.md")}
    errors: list[str] = []

    if set(declared) != discovered:
        errors.append(f"manifest skills differ: missing={sorted(discovered-set(declared))}, extra={sorted(set(declared)-discovered)}")

    now = date.today()
    checked = 0
    for skill, relative in sorted(declared.items()):
        entry = ROOT / relative
        expected = ROOT / skill / "SKILL.md"
        if entry.resolve() != expected.resolve() or not entry.is_file():
            errors.append(f"{skill}: canonical entry must be {expected.relative_to(ROOT)}")
            continue
        refs = sorted((entry.parent / "references").glob("*.md"))
        if not refs:
            errors.append(f"{skill}: canonical references directory is empty")
        for ref in refs:
            checked += 1
            first = ref.read_text(encoding="utf-8").splitlines()[:1]
            match = HEADER.match(first[0]) if first else None
            if not match:
                errors.append(f"{ref.relative_to(ROOT)}: missing first-line last-verified marker")
                continue
            year, month = map(int, match.groups())
            try:
                verified = date(year, month, 1)
            except ValueError:
                errors.append(f"{ref.relative_to(ROOT)}: invalid last-verified date")
                continue
            age = (now.year - verified.year) * 12 + now.month - verified.month
            if age < 0 or age > max_age:
                errors.append(f"{ref.relative_to(ROOT)}: freshness age {age} months outside 0..{max_age}")

    if errors:
        print("Source/freshness validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Source/freshness validation passed: {len(declared)} skills, {checked} references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
