"""Erreichbarkeits-Checks: Status, Redirect-Kette, Antwortzeit, Vermittler-Parameter."""
from __future__ import annotations

import asyncio
import time
from urllib.parse import parse_qs, urlparse

import httpx

from .common import CheckResult, LinkInfo

# Parameter, über die die Vermittler-Zuordnung läuft. Geht einer davon in der
# Redirect-Kette verloren, gibt es eine Warnung (Provision!).
VERMITTLER_PARAMS = [
    "organummer", "wmid", "vermittler-id", "advnr", "agentid1", "m",
    "kk", "vnr", "cm_mmc", "flow", "accessparam", "mandant",
]


def _vermittler_params(url: str) -> dict[str, str]:
    query = parse_qs(urlparse(url).query)
    return {k.lower(): v[0] for k, v in query.items() if k.lower() in VERMITTLER_PARAMS}


async def check_link(client: httpx.AsyncClient, link: LinkInfo) -> CheckResult:
    result = CheckResult(link=link, check="http")
    try:
        start = time.monotonic()
        resp = await client.get(link.url)
        elapsed = time.monotonic() - start
        chain = [str(r.url) for r in resp.history] + [str(resp.url)]

        if resp.status_code >= 400:
            result.status = "fehler"
            result.details.append(f"HTTP {resp.status_code} für {link.url}")
        else:
            result.details.append(f"HTTP {resp.status_code} in {elapsed:.1f}s")

        if len(chain) > 1:
            result.details.append("Redirect-Kette: " + " -> ".join(chain))

        # Soft-404: Server liefert 200, aber eine Fehlerseite
        text_start = resp.text[:4000].lower()
        if resp.status_code == 200 and (
            "seite wurde nicht gefunden" in text_start or "404" in (resp.url.path or "")
        ):
            result.status = "fehler"
            result.details.append("Soft-404: Seite meldet 'nicht gefunden' trotz HTTP 200")

        if elapsed > 10:
            if result.status == "ok":
                result.status = "warnung"
            result.details.append(f"Langsame Antwort: {elapsed:.1f}s")

        # Vermittler-Parameter dürfen in der Redirect-Kette nicht verloren gehen.
        params_start = _vermittler_params(link.url)
        if params_start and len(chain) > 1:
            params_end = _vermittler_params(str(resp.url))
            lost = {k: v for k, v in params_start.items() if params_end.get(k) != v}
            if lost and not params_end:
                if result.status == "ok":
                    result.status = "warnung"
                result.details.append(
                    "Vermittler-Parameter nach Redirect nicht mehr in der URL: "
                    + ", ".join(sorted(lost))
                    + " (kann in Session/Cookie stecken, bitte Strecken-Check beachten)"
                )
    except Exception as exc:
        result.status = "fehler"
        result.details.append(f"Nicht erreichbar: {exc}")
    return result


async def check_all_links(links: list[LinkInfo], config: dict) -> list[CheckResult]:
    headers = {
        "User-Agent": config["user_agent"],
        "Accept-Language": "de-DE,de;q=0.9",
    }
    async with httpx.AsyncClient(
        headers=headers, timeout=30, follow_redirects=True, verify=True
    ) as client:
        sem = asyncio.Semaphore(5)

        async def guarded(link: LinkInfo) -> CheckResult:
            async with sem:
                return await check_link(client, link)

        return list(await asyncio.gather(*(guarded(l) for l in links)))
