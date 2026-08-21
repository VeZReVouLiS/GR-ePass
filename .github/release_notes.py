#!/usr/bin/env python3
"""Βγάζει από το CHANGELOG.md την ενότητα μιας έκδοσης, για σώμα του release.

Χρήση: python3 .github/release_notes.py v0.5.3

Δέχεται το tag με ή χωρίς το «v». Αν δεν βρει ενότητα, δεν σκάει: γράφει έναν
σύνδεσμο στο CHANGELOG, ώστε να μη μπλοκάρει ποτέ ένα release εξαιτίας της
μορφοποίησης του αρχείου.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = "VeZReVouLiS/GR-ePass"
CHANGELOG = pathlib.Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def section_for(version: str, text: str) -> str | None:
    """Το σώμα του «## [version]» μέχρι το επόμενο «## [»."""
    pattern = rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)"
    match = re.search(pattern, text, re.S | re.M)
    if match is None:
        return None
    body = match.group(1).strip()
    # Τα link refs στο τέλος του αρχείου δεν έχουν νόημα μέσα στο release.
    body = re.sub(r"^\[[^\]]+\]: http.*$", "", body, flags=re.M).strip()
    return body or None


def main() -> int:
    # Το CHANGELOG είναι ελληνικό. Χωρίς αυτό, το script εξαρτάται από το
    # default encoding του συστήματος και σκάει σε ό,τι δεν είναι UTF-8.
    sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) != 2:
        print("usage: release_notes.py <tag>", file=sys.stderr)
        return 2

    version = sys.argv[1].lstrip("v")
    body = section_for(version, CHANGELOG.read_text(encoding="utf-8"))

    if body is None:
        print(
            f"Δείτε το [CHANGELOG](https://github.com/{REPO}"
            f"/blob/main/CHANGELOG.md) για τις αλλαγές του {version}."
        )
        return 0

    print(body)
    print()
    print("---")
    print()
    print(
        "**Εγκατάσταση / Install:** HACS → Integrations → GR e-Pass → "
        "Redownload, μετά restart του Home Assistant."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
