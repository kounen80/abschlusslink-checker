#!/usr/bin/env python3
"""Die dokumentierte Linkrecherche deterministisch nach linkliste.yaml importieren."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "docs" / "uebergabe-linkpruefung-2026-07-15.md"
DEFAULT_TARGET = ROOT / "linkliste.yaml"
BLOCK = re.compile(
    r"^##\s+(\d+)\.\s+(.+?)\s+—\s+(\d+)\s+Tarife?\s*$\n"
    r"\s*\[Onlineabschluss öffnen\]\((https?://[^)]+)\)\s*\n"
    r"\s*Zugeordnete Tarife:\s*\n(?P<tarife>.*?)(?=^##\s+\d+\.|\Z)",
    re.MULTILINE | re.DOTALL,
)
TARIF = re.compile(r"^-\s+\[([^]]+)\]\((https?://[^)]+)\)\s*$", re.MULTILINE)


def parse_markdown(text: str) -> list[dict]:
    entries: list[dict] = []
    for match in BLOCK.finditer(text):
        index, gesellschaft, expected, url = match.group(1, 2, 3, 4)
        tarife = [
            {"name": name.strip(), "tarifseite": page.strip()}
            for name, page in TARIF.findall(match.group("tarife"))
        ]
        if len(tarife) != int(expected):
            raise ValueError(f"Block {index}: {len(tarife)} statt {expected} Tarife")
        item = {
            "gesellschaft": gesellschaft.strip(),
            "abschluss_url": url.strip(),
            "tarife": tarife,
        }
        if "financeads.net/" in url:
            item["typ"] = "tracking"
        entries.append(item)
    urls = [entry["abschluss_url"] for entry in entries]
    tariff_pages = [t["tarifseite"] for entry in entries for t in entry["tarife"]]
    if len(entries) != 61 or len(set(urls)) != 61:
        raise ValueError(f"Erwartet 61 eindeutige Links, erhalten {len(entries)}/{len(set(urls))}")
    if len(tariff_pages) != 172:
        raise ValueError(f"Erwartet 172 Tarifzuordnungen, erhalten {len(tariff_pages)}")
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    args = parser.parse_args()
    entries = parse_markdown(args.source.read_text(encoding="utf-8"))
    args.target.write_text(
        yaml.safe_dump(entries, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(f"{len(entries)} eindeutige Links / {sum(len(e['tarife']) for e in entries)} Tarife -> {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
