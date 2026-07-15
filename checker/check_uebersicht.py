"""Monatlicher Abgleich der Tarifübersicht mit der versionierten Linkliste."""
from __future__ import annotations

import asyncio
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import yaml

from .common import PROJECT_DIR, LinkInfo, load_linkliste, prepare_context
from .discover import _scan_static_page


class _HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def is_tariff_page(url: str) -> bool:
    parts = [p for p in urlparse(url).path.split("/") if p]
    if not parts or parts[0] != "anbieter":
        return False
    rest = parts[1:]
    if rest and rest[0] == "aok":
        return len(rest) == 3
    return len(rest) == 2


async def fetch_tariff_pages(config: dict) -> list[str]:
    overview = config["uebersicht"]["url"]
    async with httpx.AsyncClient(
        headers={"User-Agent": config["user_agent"]}, timeout=60, follow_redirects=True
    ) as client:
        response = await client.get(overview)
        response.raise_for_status()
    parser = _HrefParser()
    parser.feed(response.text)
    return sorted({urljoin(str(response.url), h).split("#", 1)[0] for h in parser.hrefs if is_tariff_page(urljoin(str(response.url), h))})


async def crawl_tariff_links(config: dict, tariff_pages: list[str]) -> tuple[dict[str, LinkInfo], list[str]]:
    from playwright.async_api import async_playwright

    log: list[str] = []
    found: dict[str, LinkInfo] = {}
    delay = int(config["uebersicht"].get("delay_ms", 0))
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=config["user_agent"], viewport={"width": 1280, "height": 900}, locale="de-DE"
        )
        await prepare_context(context, config)
        for index, page_url in enumerate(tariff_pages, 1):
            links = await _scan_static_page(context, page_url, page_url, config["base_url"], log)
            candidates = [l for l in links if l.kategorie == "abschluss"]
            if candidates:
                link = candidates[0]
                link.tarife = [{"name": link.tarif, "tarifseite": page_url}]
                found[page_url] = link
            if index % 25 == 0:
                log.append(f"{index}/{len(tariff_pages)} Tarifseiten gescannt")
            if delay:
                await asyncio.sleep(delay / 1000)
        await context.close()
        await browser.close()
    return found, log


def reconcile(current: list[LinkInfo], scanned: dict[str, LinkInfo]) -> tuple[list[dict], list[str]]:
    old_by_page = {t["tarifseite"]: (link, t) for link in current for t in link.tarife}
    changes: list[str] = []
    grouped: dict[str, list[dict]] = defaultdict(list)
    companies: dict[str, set[str]] = defaultdict(set)
    for page, scan in scanned.items():
        old = old_by_page.get(page)
        name = (old[1].get("name") if old else scan.tarif) or urlparse(page).path.rstrip("/").split("/")[-1]
        grouped[scan.url].append({"name": name, "tarifseite": page})
        company = old[0].gesellschaft if old else urlparse(page).path.split("/")[2].replace("-", " ").title()
        companies[scan.url].add(company)
        if old is None:
            changes.append(f"NEUER ONLINEABSCHLUSS: {name}: {scan.url}")
        elif old[0].url != scan.url:
            changes.append(f"ZIEL-URL GEÄNDERT: {name}: {old[0].url} -> {scan.url}")
    for page, (_, tariff) in old_by_page.items():
        if page not in scanned:
            changes.append(f"ONLINEABSCHLUSS ENTFALLEN: {tariff.get('name', page)} ({page})")
    data = []
    for url in sorted(grouped):
        item = {
            "gesellschaft": " / ".join(sorted(companies[url])),
            "abschluss_url": url,
            "tarife": sorted(grouped[url], key=lambda t: t["tarifseite"]),
        }
        if "financeads.net/" in url:
            item["typ"] = "tracking"
        data.append(item)
    return data, changes


def write_linkliste(data: list[dict], path: Path | None = None) -> None:
    target = path or PROJECT_DIR / "linkliste.yaml"
    temporary = target.with_suffix(".yaml.tmp")
    temporary.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    temporary.replace(target)
