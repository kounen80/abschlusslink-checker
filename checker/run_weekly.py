"""Wöchentlicher Gesamtlauf: entdecken, prüfen, berichten.

Aufruf:  uv run python -m checker.run_weekly [--ohne-mail]
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import httpx

from .check_downloads import check_all_downloads, check_download
from .check_funnel import check_all_funnels
from .check_links import check_all_links
from .common import PROJECT_DIR, load_config
from .discover import diff_with_last_run, discover_links
from .report import build_report, notify_macos, send_via_apple_mail


async def main() -> int:
    config = load_config()
    run_dir = PROJECT_DIR / config["report"]["dir"] / datetime.now().strftime("%Y-%m-%d")
    shots_dir = run_dir / "screenshots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir / "lauf.log"

    def say(msg: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    say("1/4 Link-Entdeckung läuft ...")
    links, discover_log = await discover_links(config, screenshots_dir=shots_dir)
    for line in discover_log:
        say("   " + line)
    neue, verschwundene = diff_with_last_run(links)

    say("2/4 Erreichbarkeits-Checks laufen ...")
    http_results = await check_all_links(links, config)

    say("3/4 Klickstrecken-Tests laufen (das dauert einige Minuten) ...")
    funnel_results, funnel_downloads = await check_all_funnels(links, config, shots_dir)
    for r in funnel_results:
        say(f"   [{r.status}] {r.link.tarif or r.link.url[:60]} ({r.steps_done} Schritte)")

    say("4/4 Download-Checks laufen ...")
    download_results = await check_all_downloads(links, config)
    # PDFs, die erst innerhalb der Klickstrecken auftauchen, mitprüfen.
    checked = {r.link.url for r in download_results}
    headers = {"User-Agent": config["user_agent"]}
    async with httpx.AsyncClient(headers=headers, timeout=60, follow_redirects=True) as client:
        for url, quelle in funnel_downloads.items():
            if url not in checked:
                download_results.append(
                    await check_download(client, url, quelle, config["downloads"]["min_pdf_bytes"])
                )

    report_path, subject, fehler = build_report(
        run_dir, funnel_results, http_results, download_results, neue, verschwundene
    )
    say(f"Report: {report_path}")
    say(subject)

    if config["report"].get("send_email", True) and "--ohne-mail" not in sys.argv:
        body = (
            f"Wöchentlicher Abschlusslink-Check vom {run_dir.name}.\n"
            f"{subject.split('] ', 1)[1]}\n"
            f"Details im angehängten Report. Screenshots liegen unter:\n{shots_dir}"
        )
        if send_via_apple_mail(
            report_path, subject, body,
            config["report"]["email_to"], config["report"].get("email_from", ""),
        ):
            say(f"E-Mail an {config['report']['email_to']} verschickt.")
        else:
            say("E-Mail-Versand über Apple Mail fehlgeschlagen!")
            notify_macos("Linkcheck: Mailversand fehlgeschlagen", subject)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
