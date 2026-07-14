"""Schnelltest: Die Link-Entdeckung muss die bekannten Strecken finden.

Aufruf: uv run python smoke_test.py
"""
import asyncio
import sys

from checker.common import load_config
from checker.discover import discover_links


def main() -> int:
    config = load_config()
    links, log = asyncio.run(discover_links(config))
    for line in log:
        print("*", line)

    abschluss = [l for l in links if l.kategorie == "abschluss"]
    extern = [l for l in abschluss if l.typ == "extern"]
    intern = [l for l in abschluss if l.typ == "intern"]

    errors = []
    if len(abschluss) < 3:
        errors.append(f"Nur {len(abschluss)} Abschlusslinks gefunden (erwartet: mindestens 3)")
    if not extern:
        errors.append("Kein externer Abschlusslink gefunden")
    if not intern:
        errors.append("Kein interner Abschlusslink gefunden")
    if not any("axa" in l.url for l in extern):
        errors.append("AXA-Strecke nicht gefunden")
    if not any("lkh" in l.url for l in intern):
        errors.append("LKH-Strecke nicht gefunden")

    if errors:
        print("\nSMOKE-TEST FEHLGESCHLAGEN:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"\nSMOKE-TEST OK: {len(abschluss)} Abschlusslinks ({len(intern)} intern, {len(extern)} extern)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
