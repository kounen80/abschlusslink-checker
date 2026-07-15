"""Browser-Nachprüfung für Links, die den einfachen HTTP-Check blocken.

Manche Versicherer (ERGO, ottonova, Allianz, DA Direkt) beantworten
Skript-Anfragen mit HTTP 403, funktionieren im echten Browser aber
einwandfrei. Diese Nachprüfung lädt die Seite passiv in einem vollen
Chromium (Standard-Browser-Kennung, "new headless"), klickt höchstens den
Cookie-Dialog weg und bewertet, ob eine plausible Rechner-/Antragsseite
erscheint. Es findet keine Formularinteraktion statt und es wird kein
CAPTCHA bedient.
"""
from __future__ import annotations

import re

from .common import CheckResult, dismiss_consent

# Deutliche Sperr-/Fehlerseiten-Marker
BLOCK_MARKERS = re.compile(
    r"access denied|zugriff verweigert|forbidden|blocked|bot.?erkennung"
    r"|captcha|are you a robot|ungewöhnliche aktivität|rate limit"
    r"|seite wurde nicht gefunden|404",
    re.I,
)
# Marker, die für eine echte Rechner-/Antragsseite sprechen
GOOD_MARKERS = re.compile(
    r"beitrag|tarif|versicher|geburtsdatum|berechnen|abschlie(ß|ss)|zahn|rechner|antrag",
    re.I,
)


async def launch_browser(pw, headless: bool = True):
    """Volles Chromium bevorzugen (weniger Bot-Verdacht als die Headless-Shell)."""
    try:
        return await pw.chromium.launch(headless=headless, channel="chromium")
    except Exception:
        return await pw.chromium.launch(headless=headless)


async def launch_real_chrome(pw):
    """Echtes, sichtbares Google Chrome für die Bot-Schutz-Nachprüfung.

    Manche Versicherer (ERGO, Allianz, financeads) blocken jede Headless-
    Variante mit 403, ein normales sichtbares Chrome-Fenster kommt dagegen
    durch, weil es schlicht ein echter Browser ist. Kein Tarnen, keine
    Automatisierungs-Maskierung, kein CAPTCHA-Umgehen. Fällt Chrome aus,
    wird auf Chromium zurückgegriffen (dann greift der Schutz evtl. wieder).
    """
    for channel in ("chrome", None):
        try:
            return await pw.chromium.launch(headless=False, channel=channel)
        except Exception:
            continue
    return await pw.chromium.launch(headless=True)


async def probe_url(context, url: str, timeout_ms: int = 45000) -> tuple[bool, list[str]]:
    """True, wenn die Seite im Browser plausibel lädt. Mit Detailprotokoll."""
    details: list[str] = []
    page = await context.new_page()
    try:
        resp = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await dismiss_consent(page)
        await page.wait_for_timeout(1500)

        # Challenge-/Wartespiegel ("Nur einen Moment…", "Just a moment…")
        # laufen per JS weiter zur echten Seite: kurz nachwarten und neu lesen.
        for _ in range(4):
            title_now = (await page.title() or "").lower()
            if re.search(r"nur einen moment|just a moment|einen augenblick|checking your browser", title_now):
                await page.wait_for_timeout(3000)
            else:
                break

        status = resp.status if resp else 0
        title = (await page.title() or "").strip()
        try:
            text = await page.evaluate("() => document.body.innerText")
        except Exception:
            text = ""
        text = " ".join((text or "").split())

        details.append(f"Browser: HTTP {status}, Titel '{title[:60]}', {len(text)} Zeichen Text")

        if status >= 400:
            details.append("Browser bekommt ebenfalls einen Fehlerstatus")
            return False, details
        if len(text) < 200:
            details.append("Seite bleibt im Browser (nahezu) leer")
            return False, details
        if BLOCK_MARKERS.search(title) or BLOCK_MARKERS.search(text[:3000]):
            details.append("Sperr-/Fehlerseiten-Marker im Inhalt gefunden")
            return False, details
        # Positiv-Marker nur bei wenig Text verlangen. Lädt die Seite mit HTTP
        # 200 ordentlich Inhalt (kein Block-Marker), gilt sie als erreichbar.
        if len(text) < 800 and not GOOD_MARKERS.search(title + " " + text[:5000]):
            details.append("Wenig Inhalt und kein Versicherungs-/Rechner-Marker erkennbar")
            return False, details

        details.append("Browser-Prüfung erfolgreich: Seite lädt plausibel (HTTP 200, kein Sperr-Marker)")
        return True, details
    except Exception as exc:
        details.append(f"Browser-Prüfung fehlgeschlagen: {type(exc).__name__}: {str(exc)[:120]}")
        return False, details
    finally:
        await page.close()


async def escalate_blocked(results: list[CheckResult], config: dict) -> int:
    """Alle 403/429-MANUELL_PRÜFEN-Ergebnisse per Browser nachprüfen.

    Erfolgreich nachgeprüfte Links werden auf OK gestuft (mit Nachweis im
    Protokoll). Gibt die Anzahl der hochgestuften Links zurück.
    """
    from playwright.async_api import async_playwright

    candidates = [
        r for r in results
        if r.status == "MANUELL_PRÜFEN"
        and any("Sperre/Bot-Schutz" in d for d in r.details)
    ]
    if not candidates:
        return 0

    upgraded = 0
    async with async_playwright() as pw:
        # Echtes sichtbares Chrome: nur so kommen die hart geschützten Seiten
        # durch. Bewusst KEIN eigener User-Agent und keine Maskierung, damit
        # die Prüfung exakt dem entspricht, was ein echter Kunde erlebt.
        browser = await launch_real_chrome(pw)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900}, locale="de-DE"
        )
        await context.add_init_script(
            "try { localStorage.setItem('plausible_ignore', 'true'); } catch (e) {}"
        )
        for result in candidates:
            ok, details = await probe_url(context, result.link.url)
            result.details.append("Automatische Browser-Nachprüfung: " + " | ".join(details))
            if ok:
                result.status = "OK"
                upgraded += 1
        await browser.close()
    return upgraded
