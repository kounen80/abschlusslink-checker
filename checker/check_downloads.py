"""Download-Checks: PDFs auf Tarif-Detail- und Antragsseiten prüfen."""
from __future__ import annotations

import asyncio
import re
from urllib.parse import urljoin

import httpx

from .common import CheckResult, LinkInfo

PDF_LINK = re.compile(r"\.pdf(\?|$)", re.I)


async def collect_download_urls(client: httpx.AsyncClient, page_url: str) -> list[str]:
    """PDF-/Download-Links aus dem HTML einer Seite ziehen (ohne Browser)."""
    try:
        resp = await client.get(page_url)
        resp.raise_for_status()
    except Exception:
        return []
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', resp.text)
    urls = {urljoin(str(resp.url), h) for h in hrefs if PDF_LINK.search(h) or "download" in h.lower()}
    return sorted(urls)


async def check_download(client: httpx.AsyncClient, url: str, quelle: str, min_bytes: int) -> CheckResult:
    link = LinkInfo(url=url, quelle=quelle, kategorie="download")
    result = CheckResult(link=link, check="download")
    try:
        resp = await client.get(url)
        if resp.status_code >= 400:
            result.status = "fehler"
            result.details.append(f"HTTP {resp.status_code}")
            return result
        content = resp.content
        ctype = resp.headers.get("content-type", "")
        result.details.append(f"HTTP {resp.status_code}, {len(content)} Bytes, {ctype}")
        if PDF_LINK.search(url) or "pdf" in ctype:
            if not content.startswith(b"%PDF"):
                result.status = "fehler"
                result.details.append("Datei ist kein gültiges PDF (fehlender %PDF-Header)")
            elif len(content) < min_bytes:
                result.status = "warnung"
                result.details.append(f"PDF verdächtig klein (< {min_bytes} Bytes)")
    except Exception as exc:
        result.status = "fehler"
        result.details.append(f"Download fehlgeschlagen: {exc}")
    return result


async def check_all_downloads(links: list[LinkInfo], config: dict) -> list[CheckResult]:
    """Alle internen Detail- und Antragsseiten nach Downloads absuchen und prüfen."""
    headers = {"User-Agent": config["user_agent"], "Accept-Language": "de-DE,de;q=0.9"}
    min_bytes = config["downloads"]["min_pdf_bytes"]
    pages = [l for l in links if l.typ == "intern"]

    async with httpx.AsyncClient(headers=headers, timeout=60, follow_redirects=True) as client:
        found: dict[str, str] = {}  # url -> quelle (erste Fundstelle)
        for page in pages:
            for url in await collect_download_urls(client, page.url):
                found.setdefault(url, page.url)

        sem = asyncio.Semaphore(5)

        async def guarded(url: str, quelle: str) -> CheckResult:
            async with sem:
                return await check_download(client, url, quelle, min_bytes)

        return list(await asyncio.gather(*(guarded(u, q) for u, q in found.items())))
