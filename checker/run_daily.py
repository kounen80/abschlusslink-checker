"""Täglicher, strikt passiver Erreichbarkeitslauf ohne Browserinteraktion."""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime

from .check_links import check_all_links
from .common import PROJECT_DIR, load_config, load_linkliste
from .report import build_report, send_via_apple_mail


async def main() -> int:
    config = load_config()
    links = load_linkliste()
    # Plausibilitätsprüfung statt exakter Zahl: der Monats-Check darf die
    # Liste legitim erweitern oder kürzen. Abbruch nur bei kaputter Liste.
    if len(links) < 50 or len(links) != len({l.url for l in links}):
        print(f"ABBRUCH: Linkliste unplausibel ({len(links)} Einträge, Duplikate möglich)", flush=True)
        return 1
    run_dir = PROJECT_DIR / config["report"]["dir"] / "daily" / datetime.now().strftime("%Y-%m-%d")
    run_dir.mkdir(parents=True, exist_ok=True)
    results = await check_all_links(links, config)
    report_path, _, defects = build_report(
        run_dir, [], results, [], [], [], titel="Täglicher Erreichbarkeits-Check"
    )
    manual = sum(r.status == "MANUELL_PRÜFEN" for r in results)
    subject = (
        f"[Linkcheck] Tages-Erreichbarkeit – {defects} defekt, {manual} manuell prüfen"
    )
    if config["report"].get("send_email", True) and "--ohne-mail" not in sys.argv:
        ok = send_via_apple_mail(
            report_path,
            subject,
            "Reiner HTTP-/Redirect-Check. Keine Abschlussstrecke wurde bedient.",
            config["report"]["email_to"],
            config["report"].get("email_from", ""),
        )
        if not ok:
            print("Apple-Mail-Versand fehlgeschlagen", flush=True)
            return 1
    print(subject, flush=True)
    return 1 if defects else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
