"""Monatlicher Übersichts-Crawl, Linklisten-Abgleich und Wizard-Gegenprobe."""
from __future__ import annotations

import asyncio
import html
import sys
from datetime import datetime

from .check_uebersicht import crawl_tariff_links, fetch_tariff_pages, reconcile, write_linkliste
from .common import PROJECT_DIR, load_config, load_linkliste
from .discover import discover_links
from .report import send_via_apple_mail


async def main() -> int:
    config = load_config()
    run_dir = PROJECT_DIR / config["report"]["dir"] / "monthly" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    pages = await fetch_tariff_pages(config)
    if len(pages) < int(config["uebersicht"].get("min_tarifseiten", 400)):
        print(f"ABBRUCH: nur {len(pages)} Tarifseiten gefunden; linkliste.yaml bleibt unverändert")
        return 1
    scanned, crawl_log = await crawl_tariff_links(config, pages)
    scan_errors = sum(line.startswith("FEHLER") for line in crawl_log)
    if scan_errors > int(config["uebersicht"].get("max_scan_fehler", 20)):
        print(f"ABBRUCH: {scan_errors} Scanfehler; linkliste.yaml bleibt unverändert")
        return 1
    data, changes = reconcile(load_linkliste(), scanned)
    if not data:
        print("ABBRUCH: keine Abschlusslinks gefunden; linkliste.yaml bleibt unverändert")
        return 1

    wizard_links, wizard_log = await discover_links(config)
    known = {item["abschluss_url"] for item in data}
    wizard_only = sorted({l.url for l in wizard_links if l.kategorie == "abschluss"} - known)
    changes.extend(f"WARNUNG WIZARD-LINK NICHT IN LINKLISTE: {url}" for url in wizard_only)
    write_linkliste(data)

    rows = "".join(f"<li>{html.escape(c)}</li>" for c in changes) or "<li>Keine Änderungen.</li>"
    report = run_dir / "report.html"
    report.write_text(
        "<!doctype html><meta charset='utf-8'><h1>Monats-Check</h1>"
        f"<p>{len(pages)} Tarifseiten, {len(scanned)} Onlineabschlüsse, {len(data)} eindeutige Links, "
        f"{scan_errors} Scanfehler.</p><ul>{rows}</ul><h2>Protokoll</h2><pre>"
        + html.escape("\n".join(crawl_log + wizard_log)) + "</pre>",
        encoding="utf-8",
    )
    subject = f"[Linkcheck] Monats-Check – {len(changes)} Änderungen/Warnungen"
    if config["report"].get("send_email", True) and "--ohne-mail" not in sys.argv:
        if not send_via_apple_mail(report, subject, subject, config["report"]["email_to"], config["report"].get("email_from", "")):
            print("Apple-Mail-Versand fehlgeschlagen")
            return 1
    print(subject)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
