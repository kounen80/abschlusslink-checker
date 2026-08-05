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
    # Letzten Dokument-Status der Hauptseite mitschneiden. Tracking-Redirects
    # (financeads) leiten per HTTP UND per JS/Meta weiter, z.B.
    # financeads -> i.ergo.de -> ergo.de; der Startstatus (financeads 200)
    # sagt nichts über die eigentliche Zielseite aus.
    final_status = {"code": 0}

    def _track(response):
        try:
            req = response.request
            if req.resource_type == "document" and req.frame == page.main_frame:
                final_status["code"] = response.status
        except Exception:
            pass

    page.on("response", _track)
    try:
        resp = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")

        # Redirect-Kette zu Ende laufen lassen: warten, bis sich URL UND
        # Textmenge stabilisieren. Eine feste Wartezeit trifft sonst manchmal
        # eine dünne Zwischen-Weiterleitungsseite und wertet sie als "leer".
        last_url, stable = "", 0
        for _ in range(10):
            await page.wait_for_timeout(1200)
            try:
                await page.wait_for_load_state("networkidle", timeout=4000)
            except Exception:
                pass
            current = page.url
            try:
                text_len = await page.evaluate("() => document.body.innerText.length")
            except Exception:
                text_len = 0
            if current == last_url and text_len > 400:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            last_url = current

        await dismiss_consent(page)
        await page.wait_for_timeout(1200)

        # Challenge-/Wartespiegel ("Nur einen Moment…", "Just a moment…")
        # laufen per JS weiter zur echten Seite: kurz nachwarten und neu lesen.
        for _ in range(4):
            title_now = (await page.title() or "").lower()
            if re.search(r"nur einen moment|just a moment|einen augenblick|checking your browser", title_now):
                await page.wait_for_timeout(3000)
            else:
                break

        status = final_status["code"] or (resp.status if resp else 0)
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
    """Bot-Schutz und wiederholte Netzwerkfehler per Browser nachprüfen.

    Erfolgreich nachgeprüfte Links werden auf OK gestuft (mit Nachweis im
    Protokoll). Gibt die Anzahl der hochgestuften Links zurück.
    """
    from playwright.async_api import async_playwright

    candidates = [
        r for r in results
        if r.status == "MANUELL_PRÜFEN"
        and any(
            "Sperre/Bot-Schutz" in d
            or "Browser-Nachprüfung erforderlich" in d
            for d in r.details
        )
    ]
    if not candidates:
        return 0

    upgraded = 0
    async with async_playwright() as pw:
        # Echtes sichtbares Chrome: nur so kommen die hart geschützten Seiten
        # durch. Bewusst KEIN eigener User-Agent und keine Maskierung, damit
        # die Prüfung exakt dem entspricht, was ein echter Kunde erlebt.
        browser = await launch_real_chrome(pw)
        for result in candidates:
            # Frischer Context pro Kandidat: Consent-/Cookie-Zustand einer
            # Versicherer-Seite darf die nächste Prüfung nicht verfälschen.
            # Bei Fehlschlag einmal wiederholen (Redirect-/Ladeflakiness).
            ok, details = False, []
            for attempt in (1, 2):
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 900}, locale="de-DE"
                )
                await context.add_init_script(
                    "try { localStorage.setItem('plausible_ignore', 'true'); } catch (e) {}"
                )
                try:
                    ok, details = await probe_url(context, result.link.url)
                finally:
                    await context.close()
                if ok:
                    break
                if attempt == 1:
                    details.append("erster Versuch erfolglos, wiederhole einmal")
            result.details.append("Automatische Browser-Nachprüfung: " + " | ".join(details))
            if ok:
                result.status = "OK"
                upgraded += 1
            elif any("Browser-Nachprüfung erforderlich" in d for d in result.details):
                # Erst drei HTTP-Fehler plus zwei erfolglose Browser-Versuche
                # liefern genügend Evidenz für einen echten Erreichbarkeitsdefekt.
                result.status = "DEFEKT"
                result.details.append(
                    "Auch die passive Browser-Nachprüfung ist fehlgeschlagen"
                )
        await browser.close()
    return upgraded
