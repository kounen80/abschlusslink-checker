"""Link-Entdeckung: Sitemap + Wizard-Crawl + Detailseiten-Scan.

Findet alle "Online abschließen"-Links und Tarif-Detailseiten, die der
Vergleichsrechner für die konfigurierten Profile anzeigt. Alle
Gesundheitsfragen werden mit "Nein" beantwortet (maximale Tarifanzahl).
Die internen Antragsseiten stehen nicht in der Sitemap (noindex), deshalb
werden zusätzlich Startseite und alle Tarif-Detailseiten abgesucht.
"""
from __future__ import annotations

import asyncio
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

from .common import (
    PROJECT_DIR,
    LinkInfo,
    dismiss_consent,
    is_internal,
    load_config,
    prepare_context,
)

KNOWN_LINKS_FILE = PROJECT_DIR / "reports" / "known_links.json"

ABSCHLUSS_TEXT = re.compile(r"online\s+abschlie(ß|ss)en|online[-\s]antrag|zum\s+antrag", re.I)
ANTRAG_URL = re.compile(r"online-antrag", re.I)
DETAIL_TEXT = re.compile(r"details?\s+anzeigen", re.I)
NEIN_TEXT = re.compile(r"^\s*nein\s*$", re.I)

COLLECT_LINKS_JS = """() => [...document.querySelectorAll('a')].map(a => ({
      text: (a.textContent || '').trim().replace(/\\s+/g, ' '),
      href: a.href,
      tarif: (a.closest('[class*="tarif" i], [class*="card" i], article, section')
                ?.querySelector('h1, h2, h3, h4')?.textContent || '')
                .trim().replace(/\\s+/g, ' ')
   }))"""


async def fetch_sitemap_links(config: dict) -> list[LinkInfo]:
    """Antragsseiten aus der Sitemap (falls doch welche gelistet sind)."""
    base = config["base_url"].rstrip("/")
    found: list[LinkInfo] = []
    seen_maps: set[str] = set()

    async with httpx.AsyncClient(
        headers={"User-Agent": config["user_agent"]}, timeout=30, follow_redirects=True
    ) as client:

        async def walk(sitemap_url: str) -> None:
            if sitemap_url in seen_maps:
                return
            seen_maps.add(sitemap_url)
            try:
                resp = await client.get(sitemap_url)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
            except Exception:
                return
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall(".//sm:sitemap/sm:loc", ns):
                await walk(loc.text.strip())
            for loc in root.findall(".//sm:url/sm:loc", ns):
                url = loc.text.strip()
                if ANTRAG_URL.search(url):
                    found.append(LinkInfo(url=url, quelle="sitemap", typ="intern"))

        await walk(f"{base}/sitemap.xml")

    return found


def _classify(items: list[dict], quelle: str, base_url: str, tarif_fallback: str = "") -> list[LinkInfo]:
    links: list[LinkInfo] = []
    for item in items:
        href = item.get("href") or ""
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        text = item.get("text") or ""
        if ABSCHLUSS_TEXT.search(text) or ANTRAG_URL.search(href):
            kategorie = "abschluss"
        elif DETAIL_TEXT.search(text):
            kategorie = "detail"
        else:
            continue
        links.append(
            LinkInfo(
                url=href,
                tarif=(item.get("tarif") or tarif_fallback)[:80],
                quelle=quelle,
                typ="intern" if is_internal(href, base_url) else "extern",
                kategorie=kategorie,
            )
        )
    return links


async def _answer_wizard(page, profile: dict, log: list[str]) -> None:
    """Geburtsjahr eingeben und alle Folgefragen mit Nein beantworten."""
    birth_input = page.locator("#birthyear-input")
    await birth_input.wait_for(state="visible", timeout=15000)
    await birth_input.fill(str(profile["birthyear"]))
    await birth_input.press("Enter")
    await page.wait_for_timeout(1500)

    # Bis zu 10 Fragerunden: sichtbaren "Nein"-Button klicken.
    for _ in range(10):
        nein = page.get_by_role("button", name=NEIN_TEXT).first
        try:
            if not await nein.is_visible(timeout=2500):
                break
        except Exception:
            break
        question = ""
        try:
            question = await page.locator("h2, h3").filter(
                has_text=re.compile(r"\?")
            ).first.inner_text(timeout=1000)
        except Exception:
            pass
        await nein.click()
        log.append(f"  Frage mit Nein beantwortet: {' '.join(question.split())[:80]}")
        await page.wait_for_timeout(1200)


async def _collect_tariff_links(page, quelle: str, base_url: str) -> list[LinkInfo]:
    """Abschluss- und Detail-Links aus der geladenen Tarifliste ziehen."""
    try:
        await page.wait_for_function(
            """() => [...document.querySelectorAll('a')].some(
                a => /online\\s+abschlie(ß|ss)en/i.test(a.textContent))""",
            timeout=30000,
        )
    except Exception:
        return []
    items = await page.evaluate(COLLECT_LINKS_JS)
    return _classify(items, quelle, base_url)


async def _scan_static_page(context, url: str, quelle: str, base_url: str, log: list[str]) -> list[LinkInfo]:
    """Eine normale Seite (Startseite, Tarif-Detailseite) nach Links absuchen."""
    page = await context.new_page()
    try:
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await dismiss_consent(page)
        await page.wait_for_timeout(800)
        h1 = ""
        try:
            h1 = " ".join((await page.locator("h1").first.inner_text(timeout=2000)).split())
        except Exception:
            pass
        items = await page.evaluate(COLLECT_LINKS_JS)
        return _classify(items, quelle, base_url, tarif_fallback=h1)
    except Exception as exc:
        log.append(f"FEHLER beim Scan von {url}: {exc}")
        return []
    finally:
        await page.close()


async def discover_links(
    config: dict, screenshots_dir: Path | None = None
) -> tuple[list[LinkInfo], list[str]]:
    """Alle Abschluss-/Detail-Links entdecken (Sitemap, Wizard, Detailseiten)."""
    from playwright.async_api import async_playwright

    log: list[str] = []
    base_url = config["base_url"]
    all_links: list[LinkInfo] = list(await fetch_sitemap_links(config))
    log.append(f"Sitemap: {len(all_links)} Antragsseiten gefunden")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        # 1. Wizard-Crawl: pro Profil ein frischer Kontext, damit der Rechner
        #    nicht die gespeicherten Antworten des vorherigen Profils übernimmt.
        for profile in config["profiles"]:
            context = await browser.new_context(
                user_agent=config["user_agent"], viewport={"width": 1280, "height": 900}
            )
            await prepare_context(context, config)
            page = await context.new_page()
            try:
                await page.goto(base_url + "/vergleich/", timeout=45000)
                await dismiss_consent(page)
                await _answer_wizard(page, profile, log)
                links = await _collect_tariff_links(page, f"Rechner ({profile['name']})", base_url)
                log.append(f"Profil {profile['name']}: {len(links)} Links in der Tarifliste")
                if screenshots_dir:
                    shot = screenshots_dir / f"rechner_{profile['birthyear']}.png"
                    await page.screenshot(path=str(shot), full_page=False)
                all_links.extend(links)
            except Exception as exc:
                log.append(f"FEHLER Profil {profile['name']}: {exc}")
            finally:
                await context.close()

        # 2. Startseite + alle gefundenen Tarif-Detailseiten absuchen
        #    (die internen Antragsseiten stehen nicht in der Sitemap).
        context = await browser.new_context(
            user_agent=config["user_agent"], viewport={"width": 1280, "height": 900}
        )
        await prepare_context(context, config)

        all_links.extend(await _scan_static_page(context, base_url + "/", "Startseite", base_url, log))

        detail_urls = sorted({l.url for l in all_links if l.kategorie == "detail"})
        log.append(f"Scanne {len(detail_urls)} Tarif-Detailseiten nach Abschlusslinks")
        for url in detail_urls:
            found = await _scan_static_page(context, url, f"Detailseite {url}", base_url, log)
            all_links.extend(l for l in found if l.kategorie == "abschluss")

        await context.close()
        await browser.close()

    # Deduplizieren (URL als Schlüssel); Abschluss gewinnt vor Detail,
    # ein Eintrag mit Tarifname gewinnt vor einem ohne.
    dedup: dict[str, LinkInfo] = {}
    for link in all_links:
        existing = dedup.get(link.url)
        if (
            existing is None
            or (existing.kategorie == "detail" and link.kategorie == "abschluss")
            or (not existing.tarif and link.tarif)
        ):
            if existing is not None and existing.kategorie == "abschluss":
                link.kategorie = "abschluss"
            dedup[link.url] = link
    result = sorted(dedup.values(), key=lambda l: (l.kategorie, l.typ, l.url))
    n_abschluss = sum(1 for l in result if l.kategorie == "abschluss")
    log.append(f"Gesamt nach Deduplizierung: {len(result)} Links, davon {n_abschluss} Abschlusslinks")
    return result, log


def diff_with_last_run(links: list[LinkInfo]) -> tuple[list[str], list[str]]:
    """Neue und verschwundene Abschluss-URLs gegenüber dem letzten Lauf."""
    current = {l.url for l in links if l.kategorie == "abschluss"}
    previous: set[str] = set()
    if KNOWN_LINKS_FILE.exists():
        previous = set(json.loads(KNOWN_LINKS_FILE.read_text(encoding="utf-8")))
    new = sorted(current - previous)
    gone = sorted(previous - current)
    KNOWN_LINKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    KNOWN_LINKS_FILE.write_text(json.dumps(sorted(current), indent=1), encoding="utf-8")
    return new, gone


if __name__ == "__main__":
    cfg = load_config()
    links, log = asyncio.run(discover_links(cfg))
    for line in log:
        print("*", line)
    for link in links:
        print(f"[{link.kategorie:9}] [{link.typ:6}] {link.tarif[:38]:38} {link.url}")
