"""Gemeinsame Hilfsfunktionen: Konfiguration, Datenmodelle, Browser-Setup."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import yaml

PROJECT_DIR = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    with open(PROJECT_DIR / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_testdata() -> dict:
    with open(PROJECT_DIR / "testdaten.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class LinkInfo:
    """Ein entdeckter Abschluss- oder Detail-Link."""
    url: str
    tarif: str = ""
    quelle: str = ""          # Seite/Profil, auf der der Link gefunden wurde
    typ: str = "intern"       # intern | extern
    kategorie: str = "abschluss"  # abschluss | detail


@dataclass
class CheckResult:
    """Ergebnis einer Einzelprüfung."""
    link: LinkInfo
    check: str                # http | funnel | download
    status: str = "ok"        # ok | warnung | fehler
    details: list[str] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    steps_done: int = 0
    stop_button: str = ""     # Text des erreichten Abschluss-Buttons


def is_internal(url: str, base_url: str) -> bool:
    host = urlparse(url).netloc.replace("www.", "")
    base_host = urlparse(base_url).netloc.replace("www.", "")
    return host == base_host


def compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def matches_any(text: str, patterns: list[re.Pattern]) -> bool:
    # Soft Hyphens (­) entfernen, sie stecken unsichtbar in Button-Texten
    # (z.B. "herunter­laden" bei Signal Iduna) und brechen die Muster.
    text = " ".join((text or "").replace("­", "").split())
    return any(p.search(text) for p in patterns)


KLARO_CONSENT_SELECTORS = [
    "button.cm-btn-accept",
    "button.cn-decline",
    ".klaro button.cm-btn:not(.cm-btn-success)",
]


async def prepare_context(context, config: dict) -> None:
    """Plausible-Ausschluss und Test-Markierung vor jedem Seitenaufruf setzen."""
    await context.add_init_script(
        "try { localStorage.setItem('plausible_ignore', 'true'); } catch (e) {}"
    )


async def dismiss_consent(page) -> bool:
    """Klaro-Dialog (eigene Seite) oder gängige Consent-Banner wegklicken.

    Wählt immer die zurückhaltendste Variante (nur notwendige Dienste).
    Consent-Dialoge können auch in iframes leben (z.B. TrustCommander bei
    AXA), deshalb werden alle Frames durchsucht.
    """
    button_patterns = [
        r"ausgew(ä|ae)hlte akzeptieren",
        r"nur (technisch )?notwendige",
        r"nur mit erforderlichen",
        r"^(alle )?ablehnen$",
        r"alle akzeptieren",
        r"^akzeptieren",
        r"zustimmen",
    ]
    text_patterns = [
        r"nur mit erforderlichen cookies fortfahren",
        r"weiter mit den erforderlichen cookies",
        r"^(alles?|alle) akzeptieren$",
    ]
    clicked = False
    for frame in page.frames:
        candidates = [
            frame.get_by_role("button", name=re.compile(p, re.I)) for p in button_patterns
        ] + [frame.get_by_text(re.compile(p, re.I)) for p in text_patterns]
        for locator in candidates:
            try:
                btn = locator.first
                if await btn.is_visible(timeout=800):
                    await btn.click(timeout=3000)
                    await page.wait_for_timeout(800)
                    clicked = True
                    break
            except Exception:
                continue
        if clicked:
            break

    # Hartnäckige Overlays (z.B. TrustCommander bei AXA), die trotz Klick
    # bestehen bleiben, notfalls entfernen. Betrifft nur die Cookie-Schicht,
    # nicht die eigentliche Antragsstrecke.
    try:
        removed = await page.evaluate(
            """() => {
                let n = 0;
                for (const sel of ['#privacy-overlay', '#tc-privacy-wrapper',
                                   '.tc-privacy-overlay', '#popin_tc_privacy']) {
                    document.querySelectorAll(sel).forEach(e => { e.remove(); n++; });
                }
                return n;
            }"""
        )
        if removed:
            clicked = True
    except Exception:
        pass
    return clicked
