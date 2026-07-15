"""Klickstrecken-Engine: Antragsstrecken bis zum letzten Klick VOR dem
Abschluss durchklicken.

Härteste Regel dieses Moduls: Buttons, deren Text auf ein Stop-Muster passt
("jetzt abschließen", "kostenpflichtig", ...), werden NIEMALS geklickt.
Das Erreichen eines solchen Buttons gilt als erfolgreiches Streckenende.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import (
    CheckResult,
    LinkInfo,
    compile_patterns,
    dismiss_consent,
    load_testdata,
    matches_any,
)

# Feld-Heuristik: Testdaten-Schlüssel -> Muster für name/id/placeholder/label
FIELD_PATTERNS: dict[str, str] = {
    "vorname": r"vorname|first.?name",
    "nachname": r"nachname|familienname|last.?name|surname",
    "strasse": r"stra(ß|ss)e|street",
    "hausnummer": r"haus.?n(r|ummer)",
    "plz": r"\bplz\b|postleitzahl|zip|postal",
    "ort": r"\bort\b|wohnort|stadt|\bcity\b",
    "email": r"e.?mail",
    "vorwahl": r"vorwahl",
    "rufnummer": r"rufnummer|durchwahl",
    "mobil": r"mobil|handy",   # oft mit +49-Präfix: keine führende Null
    "telefon": r"telefon|phone",
    "geburtsdatum": r"geburt|birth",
    "geburtsort": r"geburtsort",
    "beruf": r"beruf|occupation|t(ä|ae)tigkeit",
    "iban": r"\biban\b",
    "bic": r"\bbic\b",
    "kontoinhaber": r"kontoinhaber",
    "krankenkasse": r"krankenkasse|krankenversicherung|gesetzlich\s+versichert",
    # "Anzahl ..." auf Gesundheitsfragen-Seiten (z.B. Anzahl fehlender Zähne)
    "anzahl": r"\banzahl\b",
}

DOWNLOAD_LINK = re.compile(r"\.pdf(\?|$)|download", re.I)
CAPTCHA_PATTERN = re.compile(
    r"captcha|recaptcha|hcaptcha|turnstile|ich bin kein roboter|"
    r"are you human|verify you are human|bot detection|access denied|zugriff verweigert",
    re.I,
)

# JS: sichtbare, leere Formularfelder samt Kontext (Label etc.) einsammeln
COLLECT_FIELDS_JS = """() => {
  const visible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const labelFor = el => {
    let t = '';
    // Nächstgelegenen Vorfahren mit einem Label suchen (Material UI & Co.
    // vergeben teils dieselbe id an mehrere Felder, dann wäre die globale
    // label[for=...]-Zuordnung falsch).
    let p = el.parentElement, scoped = null;
    for (let i = 0; i < 4 && p && !scoped; i++) {
      scoped = p.querySelector('label');
      p = p.parentElement;
    }
    if (scoped) t += ' ' + scoped.textContent;
    else if (el.id) t += ' ' + (document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.textContent || '');
    t += ' ' + (el.closest('label')?.textContent || '');
    t += ' ' + (el.getAttribute('aria-label') || '');
    return t;
  };
  const fields = [];
  document.querySelectorAll('input, select, textarea').forEach((el, i) => {
    // Selects auch dann mitnehmen, wenn sie optisch versteckt sind (Custom-
    // Dropdown-Optik über einem nativen select, z.B. Signal Iduna).
    if ((!visible(el) && el.tagName !== 'SELECT') || el.disabled || el.readOnly) return;
    el.setAttribute('data-ovv-idx', String(i));
    fields.push({
      idx: i,
      tag: el.tagName.toLowerCase(),
      type: (el.type || '').toLowerCase(),
      name: el.name || '',
      id: el.id || '',
      placeholder: el.placeholder || '',
      label: labelFor(el).trim().replace(/\\s+/g, ' ').slice(0, 120),
      cls: (el.className || '').toString().slice(0, 80),
      value: el.tagName === 'SELECT' ? (el.selectedIndex > 0 ? 'x' : '') : (el.value || ''),
      required: el.required || el.getAttribute('aria-required') === 'true',
      checked: !!el.checked,
      options: el.tagName === 'SELECT'
        ? [...el.options].map(o => o.textContent.trim()).slice(0, 40) : [],
    });
  });
  return fields;
}"""

PAGE_STATE_JS = """() => location.href + '::' + document.body.innerText.length
                       + '::' + document.querySelectorAll('input,select,button').length"""

# JS: Frage-Buttons ("Nein", "keine", "0" in Zahlengruppen) anklicken, wie sie
# z.B. der privyou-Antrags-Wizard nutzt. Bereits ausgewählte werden übersprungen.
ANSWER_BUTTONS_JS = """() => {
  const norm = t => (t || '').trim().replace(/\\s+/g, ' ').toLowerCase();
  // Icon-Elemente (Material-Icons-Ligaturen wie "close", "check") aus dem
  // Button-Text entfernen, sonst wird aus "Nein" ein "close nein".
  const textOf = b => {
    const c = b.cloneNode(true);
    c.querySelectorAll('i, svg, [class*="icon" i], [class*="material" i]')
      .forEach(x => x.remove());
    return norm(c.textContent);
  };
  const selectedSelf = b => b.getAttribute('aria-pressed') === 'true'
      || b.getAttribute('aria-checked') === 'true'
      || /(^|\\s|-)(active|selected|checked|current|chosen)(\\s|-|$)/i.test(b.className);
  // Auswahl-Zustand kann auch auf einem Eltern-Element liegen (privyou
  // markiert div.question-answer, geklickt wird aber das Text-Kind).
  const selected = b => [b, b.parentElement, b.parentElement?.parentElement]
      .some(e => e && selectedSelf(e));
  const visible = el => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const clicked = [];
  // Neben echten Buttons auch klickbare Antwort-Elemente berücksichtigen
  // (z.B. div.question-answer bei privyou, Labels von Toggle-Gruppen).
  const candidates = document.querySelectorAll(
    'button, [role=button], [role=radio], [role=checkbox], [role=switch], mat-checkbox, label, ' +
    '[class*="answer" i], [class*="option" i], [class*="choice" i], mat-button-toggle'
  );
  const confirmRe = /kenntnis|gelesen|verstanden|best(ä|ae)tig|mitglied|gesetzlich|krankenkasse|wohnsitz|angeh(ö|oe)rige|einwillig|datenschutz|anzeigepflicht|gesundheitsdaten|verzicht|schweigepflicht|lastschrift|sepa/;
  // Fragen, die mit JA beantwortet werden müssen (siehe anleitungen.md):
  // "Sind Sie gesetzlich krankenversichert?" u.ä.
  const yesRe = /gesetzlich(e|en)?\\s+(kranken)?versicher|gesetzlich\\s+versichert/;
  const questionOf = b => {
    let p = b.parentElement;
    for (let i = 0; i < 5 && p; i++) {
      const txt = norm(p.textContent);
      if (txt.length > 40) return txt.slice(0, 400);
      p = p.parentElement;
    }
    return '';
  };
  for (const b of candidates) {
    if (!visible(b) || b.disabled || selected(b)) continue;
    if (b.dataset.ovvClicked) continue; // nie doppelt klicken (würde toggeln)
    if (b.querySelector('button, label, [class*="answer" i]')) continue; // nur Blatt-Elemente
    // Label eines bereits ausgewählten (versteckten) Radios überspringen.
    if (b.tagName === 'LABEL') {
      const input = b.control || (b.htmlFor && document.getElementById(b.htmlFor)) || b.querySelector('input');
      if (input && input.checked) continue;
    }
    const t = textOf(b);
    let hit = false;
    if (t === 'nein' || t === 'keine') {
      // GKV-Fragen brauchen JA, hier also NICHT Nein klicken.
      if (!yesRe.test(questionOf(b))) hit = true;
    }
    else if (t === 'ja' && yesRe.test(questionOf(b))) hit = true;
    // Anrede-Auswahl ("Herr" / "Frau" als Pseudo-Buttons, z.B. Signal Iduna)
    else if (t === 'herr') hit = true;
    // "Nein, weiter mit ..." / "Nein, keine Beratung" (z.B. Signal Iduna)
    else if (/^nein[,:]?\\s/.test(t) && t.length < 60) hit = true;
    // Kenntnisnahme-Bestätigungen (z.B. rechtliche Hinweise bei Signal Iduna).
    else if (/^(zur kenntnis genommen|verstanden|gelesen und verstanden)$/.test(t)) hit = true;
    // Custom-Checkboxen (role=checkbox) für Bestätigungen: GKV-Mitglied,
    // Wohnsitz Deutschland, Kenntnisnahme etc. (z.B. DKV).
    else if ((b.getAttribute('role') === 'checkbox' || b.tagName === 'MAT-CHECKBOX')
             && b.getAttribute('aria-checked') !== 'true'
             && confirmRe.test(t)) {
      hit = true;
    }
    // Bestätigungs-Labels von (Shadow-DOM-)Checkboxen, deren Input nicht
    // erreichbar ist (z.B. Signal Iduna moonlab/si-checkbox).
    else if (b.tagName === 'LABEL' && t.length < 250 && confirmRe.test(t)) hit = true;
    // Schieberegler "Vorsorge für die Zähne" aktivieren (Concordia).
    else if (b.getAttribute('role') === 'switch'
             && b.getAttribute('aria-checked') !== 'true'
             && /z(ä|ae)hne|zahn/.test(questionOf(b))) {
      hit = true;
    }
    else if (t === '0') {
      // "0" nur klicken, wenn es Teil einer Zahlen-Auswahlgruppe ist:
      // im selben Container gibt es Geschwister-Optionen "1" und "2".
      const group = b.closest('[class*="container" i], [class*="group" i], fieldset')
          || b.parentElement?.parentElement?.parentElement;
      const childTexts = [...(group?.children || [])].map(c => textOf(c));
      if (childTexts.includes('1') && childTexts.includes('2')) hit = true;
    }
    if (hit) {
      b.dataset.ovvClicked = '1';
      b.click();
      clicked.push(t);
    }
  }
  return clicked;
}"""


def _context_text(field: dict) -> str:
    return " ".join([field["name"], field["id"], field["placeholder"], field["label"]]).lower()


def _next_month_first() -> str:
    """Erster Tag des übernächsten Monats als TT.MM.JJJJ (Versicherungsbeginn)."""
    from datetime import date
    today = date.today()
    month = today.month + 2
    year = today.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return f"01.{month:02d}.{year}"


def _value_for_field(field: dict, testdata: dict) -> str | None:
    """Passenden Testwert für ein Feld bestimmen; None = nicht anfassen.

    Wichtig: erst der Kontext (Label/Name), dann der Feldtyp. Ein
    Geburtsdatum-Feld kann type=tel haben (Eingabemaske) und darf keine
    Telefonnummer bekommen.
    """
    ctx = _context_text(field)
    ftype = field["type"]
    # Ein einzelnes kombiniertes Feld "Straße und Hausnummer" braucht beides.
    # (Feld-PAARE mit gemeinsamem Label behandelt _fill_street_pair vorab.)
    if re.search(FIELD_PATTERNS["strasse"], ctx, re.I) and re.search(
        FIELD_PATTERNS["hausnummer"], ctx, re.I
    ):
        return f"{testdata['fields']['strasse']} {testdata['fields']['hausnummer']}"
    # Hausnummern-Felder, die nur "Nr." heißen (z.B. Getsafe) - als
    # Placeholder oder Label.
    for hint in (field["placeholder"], field["label"]):
        if hint.strip().rstrip(".").lower() == "nr":
            return testdata["fields"]["hausnummer"]
    for key, pattern in FIELD_PATTERNS.items():
        if re.search(pattern, ctx, re.I):
            # IBAN/BIC werden mit der offiziellen Bundesbank-Test-IBAN
            # gefüllt; ohne sie ist der letzte Schritt oft nicht erreichbar.
            # Es wird ohnehin nie ein Antrag abgesendet.
            value = testdata["fields"].get(key)
            if key == "geburtsdatum" and ftype == "date":
                d, m, y = value.split(".")
                return f"{y}-{m}-{d}"
            return value
    # Versicherungsbeginn-Datumsfelder: nächstmöglicher Monatserster.
    if re.search(r"beginn|versicherungsstart", ctx, re.I) and (
        ftype == "date" or re.search(r"(dd|tt)\.mm\.(yyyy|jjjj)", field["placeholder"], re.I)
    ):
        value = _next_month_first()
        if ftype == "date":
            d, m, y = value.split(".")
            return f"{y}-{m}-{d}"
        return value
    # Datums-Eingabemasken ohne erkannten Kontext: Geburtsdatum annehmen.
    if re.search(r"(dd|tt)\.mm\.(yyyy|jjjj)", field["placeholder"], re.I):
        return testdata["fields"]["geburtsdatum"]
    # Typ-basierte Standardwerte erst NACH der Kontext-Erkennung.
    if ftype == "email":
        return testdata["fields"]["email"]
    if ftype == "tel":
        return testdata["fields"]["telefon"]
    if ftype == "date":
        return "1990-06-15"
    if ftype == "number":
        return "1"
    return None


class FunnelRunner:
    def __init__(self, config: dict, screenshots_dir: Path):
        self.config = config
        self.testdata = load_testdata()
        self.stop_patterns = compile_patterns(config["stop_patterns"])
        self.next_patterns = compile_patterns(config["next_patterns"])
        self.screenshots_dir = screenshots_dir
        self.found_downloads: dict[str, str] = {}

    # ---------- Hilfen ----------

    async def _manual_reason(self, page, response=None) -> str:
        """CAPTCHA/Bot-Sperre erkennen, ohne sie zu bedienen oder zu umgehen."""
        status = response.status if response is not None else 0
        texts: list[str] = [page.url]
        for frame in page.frames:
            try:
                texts.append(await frame.title())
                texts.append((await frame.locator("body").inner_text(timeout=1500))[:5000])
                marker = await frame.locator(
                    "iframe[src*='captcha' i], [class*='captcha' i], [id*='captcha' i], "
                    "iframe[src*='challenges.cloudflare.com' i]"
                ).count()
                if marker:
                    return "CAPTCHA/Bot-Challenge erkannt"
            except Exception:
                continue
        combined = " ".join(texts)
        if CAPTCHA_PATTERN.search(combined):
            return "CAPTCHA/Bot-Sperre im Seiteninhalt erkannt"
        visible_len = len(" ".join(combined.split()))
        if status in (403, 429) and visible_len < 800:
            return f"HTTP {status} mit leerer/unklarer Seite (Bot-Sperre möglich)"
        return ""

    async def _collect_validation_errors(self, frames) -> list[str]:
        """Sichtbare Validierungs-/Fehlermeldungen von der Seite einsammeln."""
        texts: list[str] = []
        js = """() => [...document.querySelectorAll(
                '[class*="error" i], [class*="invalid" i], [role=alert], [class*="hint" i]'
            )].filter(e => {
                const r = e.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }).map(e => (e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 100))
              .filter(t => t.length > 2)"""
        for frame in frames:
            try:
                texts.extend(await frame.evaluate(js))
            except Exception:
                pass
        return sorted(set(texts))[:8]

    async def _wait_until_ready(self, page, timeout_s: int = 25) -> None:
        """Warten, bis irgendein Frame interaktive Antrags-Elemente zeigt.

        Single-Page-Apps (Angular/Livewire) rendern oft erst Sekunden nach
        dem Laden; feste Wartezeiten reichen nicht immer.
        """
        probe = """() => document.querySelectorAll(
            'input, select, textarea, [class*="answer" i], button[type=submit]'
        ).length"""
        for second in range(timeout_s):
            child_frames = [
                f for f in page.frames
                if f != page.main_frame and f.url not in ("", "about:blank")
            ]
            if child_frames:
                for frame in child_frames:
                    try:
                        if await frame.evaluate(probe) > 0:
                            return
                    except Exception:
                        pass
            elif second >= 5:
                # Nach 5s ohne iframe: die Hauptseite selbst ist die Strecke.
                try:
                    if await page.main_frame.evaluate(probe) > 0:
                        return
                except Exception:
                    pass
            await page.wait_for_timeout(1000)

    async def _page_state(self, page) -> str:
        """Zustands-Fingerabdruck über alle Frames (Wizards leben oft in iframes)."""
        parts = []
        for frame in page.frames:
            try:
                parts.append(await frame.evaluate(PAGE_STATE_JS))
            except Exception:
                pass
        return "||".join(parts)

    def _slug(self, link: LinkInfo) -> str:
        raw = link.tarif or link.url
        return re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")[:50] or "strecke"

    async def _shoot(self, page, link: LinkInfo, step: int, result: CheckResult) -> None:
        path = self.screenshots_dir / f"{self._slug(link)}_schritt{step:02d}.png"
        try:
            await page.screenshot(path=str(path), full_page=False, timeout=10000)
            result.screenshots.append(path.name)
        except Exception:
            pass

    async def _collect_downloads(self, frame, source_url: str) -> None:
        try:
            hrefs = await frame.evaluate(
                "() => [...document.querySelectorAll('a[href]')].map(a => a.href)"
            )
        except Exception:
            return
        for href in hrefs:
            if DOWNLOAD_LINK.search(href) and not href.startswith(("mailto:", "tel:", "javascript:")):
                self.found_downloads.setdefault(href, source_url)

    async def _find_button(
        self, frame, patterns, exclude_counts: dict[str, int] | None = None
    ) -> tuple[object | None, str]:
        """Ersten sichtbaren, aktiven Button/Link finden, dessen Text passt.

        exclude_counts: Buttons, die als wirkungslos markiert wurden (Wert 99),
        werden übersprungen; erfolgreiche Klicks verbrauchen kein Budget.
        """
        locator = frame.locator(
            "button, input[type=submit], input[type=button], a[role=button], a.btn, a[class*='button'], [class*='pseudo-button']"
        )
        try:
            count = await locator.count()
        except Exception:
            return None, ""
        for i in range(min(count, 60)):
            el = locator.nth(i)
            try:
                if not await el.is_visible():
                    continue
                info = await el.evaluate(
                    """e => {
                        let text;
                        if (e.tagName === 'INPUT') {
                            text = e.value || '';
                        } else {
                            // Icon-Ligaturen (z.B. "arrow_forward_ios") entfernen,
                            // sie kleben sonst ohne Leerzeichen am Button-Text.
                            const c = e.cloneNode(true);
                            c.querySelectorAll('i, svg, [class*="icon" i], [class*="material" i]')
                                .forEach(x => x.remove());
                            text = c.textContent || '';
                        }
                        return {
                            text,
                            disabled: e.disabled === true
                                || e.getAttribute('aria-disabled') === 'true'
                                || /(^|\\s|-)disabled(\\s|-|$)/i.test(e.className),
                        };
                    }"""
                )
            except Exception:
                continue
            text = " ".join((info["text"] or "").split())
            if not text or info["disabled"]:
                continue
            if exclude_counts is not None and exclude_counts.get(text, 0) >= 90:
                continue
            if matches_any(text, patterns):
                return el, text
        return None, ""

    async def _fill_split_birthdate(self, frame, fields: list[dict], result: CheckResult) -> int:
        """Geburtsdatum als Tag/Monat/Jahr-Einzelfelder erkennen und füllen.

        Manche Strecken (z.B. AXA) nutzen drei kleine Felder statt einem
        Datumsfeld. Erkennung: 3 aufeinanderfolgende kleine Textfelder, deren
        Kontext auf Geburtsdatum passt. Reihenfolge im DOM: Tag, Monat, Jahr.
        """
        day, month, year = self.testdata["fields"]["geburtsdatum"].split(".")
        filled = 0

        def is_input(f: dict) -> bool:
            return f["tag"] == "input" and f["type"] in ("text", "number", "tel", "") and not f["value"]

        # Variante 1: Felder heißen explizit Tag / Monat / Jahr (z.B. DKV).
        by_name = {"tag": day, "monat": month, "jahr": year, "tt": day, "mm": month, "jjjj": year}
        for f in fields:
            if not is_input(f):
                continue
            hint = (f["label"] or f["placeholder"]).strip().rstrip(".").lower()
            if hint in by_name:
                try:
                    await frame.fill(f"[data-ovv-idx='{f['idx']}']", by_name[hint], timeout=3000)
                    filled += 1
                except Exception:
                    result.details.append("Geburtsdatum-Einzelfeld nicht ausfüllbar")
                f["_handled"] = True
        if filled:
            return filled

        # Variante 2: drei Felder in Folge mit Geburtsdatum-Kontext (z.B. AXA).
        date_fields = [
            f for f in fields
            if is_input(f) and re.search(FIELD_PATTERNS["geburtsdatum"], _context_text(f), re.I)
        ]
        if len(date_fields) != 3:
            return 0
        for field, value in zip(date_fields, (day, month, year)):
            try:
                await frame.fill(f"[data-ovv-idx='{field['idx']}']", value, timeout=3000)
                filled += 1
            except Exception:
                result.details.append("Geburtsdatum-Einzelfeld nicht ausfüllbar")
            field["_handled"] = True
        return filled

    async def _fill_street_pair(self, frame, fields: list[dict], result: CheckResult) -> int:
        """Zwei Felder mit gemeinsamem Label "Straße / Hausnummer" (z.B. DKV):
        erstes Feld bekommt die Straße, zweites die Hausnummer."""
        pair = [
            f for f in fields
            if f["tag"] == "input"
            and f["type"] in ("text", "")
            and re.search(FIELD_PATTERNS["strasse"], _context_text(f), re.I)
            and re.search(FIELD_PATTERNS["hausnummer"], _context_text(f), re.I)
        ]
        if len(pair) != 2:
            return 0
        values = (self.testdata["fields"]["strasse"], self.testdata["fields"]["hausnummer"])
        filled = 0
        for field, value in zip(pair, values):
            field["_handled"] = True  # Einzelfeld-Pfad darf sie nie anfassen
            if field["value"]:
                continue
            sel = f"[data-ovv-idx='{field['idx']}']"
            try:
                await frame.fill(sel, value, timeout=3000)
                await frame.locator(sel).evaluate(
                    "e => { e.dispatchEvent(new Event('change', {bubbles: true})); e.blur(); }"
                )
                filled += 1
            except Exception:
                result.details.append("Straße/Hausnummer-Feld nicht ausfüllbar")
        return filled

    async def _answer_choice_buttons(self, frame, result: CheckResult) -> int:
        """Ja/Nein- und Zahlen-Frage-Buttons beantworten (immer Nein/0/keine)."""
        total = 0
        last: list[str] = []
        for _ in range(6):
            try:
                clicked = await frame.evaluate(ANSWER_BUTTONS_JS)
            except Exception:
                break
            if not clicked or clicked == last:
                break
            total += len(clicked)
            result.details.append("Fragen beantwortet: " + ", ".join(f"'{c}'" for c in clicked))
            last = clicked
            await frame.page.wait_for_timeout(800)
        return total

    async def _fill_fields(self, frame, result: CheckResult) -> int:
        """Sichtbare Felder eines Frames mit Testdaten füllen. Gibt Anzahl zurück."""
        try:
            fields = await frame.evaluate(COLLECT_FIELDS_JS)
        except Exception:
            return 0
        filled = 0
        filled += await self._fill_split_birthdate(frame, fields, result)
        filled += await self._fill_street_pair(frame, fields, result)
        for field in fields:
            if field.get("_handled"):
                continue
            sel = f"[data-ovv-idx='{field['idx']}']"
            try:
                if field["tag"] == "select":
                    if field["value"]:
                        continue
                    choice = self._select_choice(field)
                    if choice:
                        try:
                            await frame.select_option(sel, label=choice, timeout=3000)
                        except Exception:
                            # Versteckte native Selects direkt per JS setzen.
                            await frame.locator(sel).evaluate(
                                """(e, lbl) => {
                                    const o = [...e.options].find(
                                        o => o.textContent.trim() === lbl);
                                    if (o) {
                                        e.value = o.value;
                                        e.dispatchEvent(new Event('input', {bubbles: true}));
                                        e.dispatchEvent(new Event('change', {bubbles: true}));
                                    }
                                }""",
                                choice,
                            )
                        filled += 1
                elif field["type"] == "radio":
                    # Gesundheits-/Ja-Nein-Fragen: immer "Nein" bevorzugen.
                    if await self._pick_radio(frame, field):
                        filled += 1
                elif field["type"] == "checkbox":
                    ctx = _context_text(field)
                    if not field["checked"] and (
                        field["required"]
                        or re.search(
                            r"gelesen|kenntnis|einwillig|datenschutz|best(ä|ae)tig"
                            r"|mitglied|gesetzlich|krankenkasse|krankenversicher"
                            r"|wohnsitz|angeh(ö|oe)rige|verstanden"
                            r"|anzeigepflicht|gesundheitsdaten|verzicht|schweigepflicht"
                            r"|lastschrift|sepa",
                            ctx, re.I,
                        )
                    ):
                        try:
                            await frame.check(sel, timeout=3000)
                        except Exception:
                            # Gestylte Checkboxen (Overlay-Label) nativ klicken.
                            await frame.locator(sel).evaluate("e => e.click()")
                        filled += 1
                elif "muiselect" in field.get("cls", "").lower():
                    # Material-UI-Dropdown: Combobox öffnen, Option wählen.
                    if not field["value"]:
                        if await self._pick_custom_select(frame, field):
                            filled += 1
                elif field["type"] in ("text", "email", "tel", "number", "date", "") or field["tag"] == "textarea":
                    # Vorbefüllte Felder in Ruhe lassen. Ausnahme: reine
                    # Länder-Präfixe wie "DE" im IBAN-Feld (z.B. Getsafe).
                    if field["value"] and not (
                        len(field["value"].strip()) <= 3
                        and re.search(FIELD_PATTERNS["iban"], _context_text(field), re.I)
                    ):
                        continue
                    value = _value_for_field(field, self.testdata)
                    if value is not None:
                        try:
                            await frame.fill(sel, value, timeout=3000)
                        except Exception:
                            # Maskierte/gestylte Felder: Wert nativ setzen.
                            await frame.locator(sel).evaluate(
                                """(e, v) => {
                                    const set = Object.getOwnPropertyDescriptor(
                                        window.HTMLInputElement.prototype, 'value').set;
                                    set.call(e, v);
                                    e.dispatchEvent(new Event('input', {bubbles: true}));
                                }""",
                                value,
                            )
                        # Manche Framework-Felder (Vue .lazy) validieren erst
                        # bei change/blur, das fill() nicht auslöst.
                        await frame.locator(sel).evaluate(
                            """e => {
                                e.dispatchEvent(new Event('change', {bubbles: true}));
                                e.blur();
                            }"""
                        )
                        filled += 1
            except Exception as exc:
                label = field["label"] or field["name"] or field["id"] or field["type"]
                result.details.append(f"Feld nicht ausfüllbar: '{label[:60]}' ({type(exc).__name__})")
                if result.status == "OK":
                    result.status = "MANUELL_PRÜFEN"
        return filled

    async def _pick_custom_select(self, frame, field: dict) -> bool:
        """Custom-Dropdown (z.B. Material UI) öffnen und Option wählen."""
        sel = f"[data-ovv-idx='{field['idx']}']"
        try:
            # Combobox neben dem versteckten Input anklicken
            await frame.locator(sel).evaluate(
                """e => {
                    const c = e.parentElement?.querySelector('[role=combobox], .MuiSelect-select')
                        || e.closest('div')?.querySelector('[role=combobox], .MuiSelect-select');
                    if (c) c.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                }"""
            )
            await frame.page.wait_for_timeout(800)
            options = frame.locator("[role=option]")
            count = await options.count()
            if count == 0:
                return False
            texts = []
            for i in range(min(count, 30)):
                texts.append(" ".join(((await options.nth(i).inner_text()) or "").split()))
            choice_idx = 0
            wanted = self._select_choice({"options": texts, **{k: field[k] for k in ("name", "id", "placeholder", "label")}})
            if wanted and wanted in texts:
                choice_idx = texts.index(wanted)
            await options.nth(choice_idx).click(timeout=3000)
            await frame.page.wait_for_timeout(500)
            return True
        except Exception:
            return False

    def _select_choice(self, field: dict) -> str | None:
        ctx = _context_text(field)
        prefs: dict[str, list[str]] = self.testdata.get("select_preferences", {})
        for key, wanted in prefs.items():
            if key in ctx:
                for want in wanted:
                    for option in field["options"]:
                        if want.lower() in option.lower():
                            return option
        for option in field["options"][1:]:
            if option and not re.search(r"bitte|w(ä|ae)hlen|ausw(ä|ae)hlen", option, re.I):
                return option
        return None

    async def _pick_radio(self, frame, field: dict) -> bool:
        """Radiogruppe bedienen: 'Nein' bevorzugen, sonst erste Option.

        Ausnahme laut anleitungen.md: GKV-Fragen ("gesetzlich
        krankenversichert?") werden mit 'Ja' beantwortet.
        """
        name = field["name"]
        if not name:
            return False
        group = frame.locator(f"input[type=radio][name='{name}']")
        try:
            already = await group.evaluate_all("els => els.some(e => e.checked)")
            if already:
                return False
            question = await group.first.evaluate(
                """e => {
                    let p = e.parentElement;
                    for (let i = 0; i < 5 && p; i++) {
                        const t = (p.textContent || '').trim().replace(/\\s+/g, ' ');
                        if (t.length > 40) return t.slice(0, 400);
                        p = p.parentElement;
                    }
                    return '';
                }"""
            )
            wants_yes = bool(re.search(
                r"gesetzlich(e|en)?\s+(kranken)?versicher|gesetzlich\s+versichert",
                question, re.I,
            ))
            prefer = r"^ja\b" if wants_yes else r"^nein\b|^keine\b"
            count = await group.count()
            best = None
            for i in range(count):
                radio = group.nth(i)
                # Sichtbaren Options-Text bestimmen: Label kann zusätzlich die
                # komplette Frage enthalten (z.B. AXA: "Frage...?;Nein").
                label = (await radio.evaluate(
                    """e => {
                        const lab = (e.id && document.querySelector(`label[for="${CSS.escape(e.id)}"]`))
                            || e.closest('label');
                        if (!lab) return e.value || '';
                        const clone = lab.cloneNode(true);
                        clone.querySelectorAll(
                            'input, i, svg, [class*="icon" i], [class*="sr-only" i], [class*="visually-hidden" i]'
                        ).forEach(x => x.remove());
                        let t = (clone.textContent || '').trim();
                        if (t.includes(';')) t = t.split(';').pop().trim();
                        return t;
                    }"""
                )).strip().lower()
                if re.search(prefer, label):
                    best = radio
                    break
                if best is None:
                    best = radio
            if best is not None:
                # Nativer Klick statt Playwright-check(): bei Framework-Radios
                # (Vue/Angular) schlägt check() sonst still fehl.
                await best.evaluate("e => e.click()")
                return True
        except Exception:
            pass
        return False

    # ---------- Hauptlauf ----------

    async def run(self, context, link: LinkInfo) -> CheckResult:
        result = CheckResult(link=link, check="funnel")
        page = await context.new_page()
        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text[:200]) if msg.type == "error" else None,
        )
        page.on("pageerror", lambda err: console_errors.append(str(err)[:200]))
        timeout = self.config["funnel"]["page_timeout_ms"]
        page.set_default_timeout(timeout)

        try:
            response = await page.goto(link.url, timeout=45000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)
            manual_reason = await self._manual_reason(page, response)
            if manual_reason:
                result.status = "MANUELL_PRÜFEN"
                result.details.append(manual_reason + "; keine weitere Interaktion")
                return result
            dismissed = await dismiss_consent(page)
            await self._wait_until_ready(page)
            if not dismissed:
                # Manche Consent-Dialoge (z.B. TrustCommander) erscheinen erst
                # einige Sekunden nach dem Laden.
                await page.wait_for_timeout(2000)
                await dismiss_consent(page)

            last_state = ""
            clicked_counts: dict[str, int] = {}
            download_done = False
            for step in range(1, self.config["funnel"]["max_steps"] + 1):
                result.steps_done = step
                await page.wait_for_timeout(1500)
                await self._shoot(page, link, step, result)
                manual_reason = await self._manual_reason(page)
                if manual_reason:
                    result.status = "MANUELL_PRÜFEN"
                    result.details.append(manual_reason + "; keine weitere Interaktion")
                    return result

                frames = [f for f in page.frames if f.url not in ("", "about:blank")] or [page.main_frame]
                for frame in frames:
                    await self._collect_downloads(frame, page.url)

                # 1. Frage-Buttons beantworten und Felder füllen
                for frame in frames:
                    await self._answer_choice_buttons(frame, result)
                for frame in frames:
                    await self._fill_fields(frame, result)

                # 1b. Pflicht-Downloads ("Unterlagen herunterladen") einmal
                #     klicken; manche Strecken (Signal Iduna, levelnine)
                #     verlangen das vor dem Abschluss. Shadow-DOM-Buttons sind
                #     nur über die Accessibility-Suche erreichbar.
                if not download_done:
                    for frame in frames:
                        try:
                            dl = frame.get_by_role(
                                "button", name=re.compile(r"herunter.?laden", re.I)
                            ).first
                            if not await dl.is_visible(timeout=400):
                                dl = frame.get_by_role(
                                    "link", name=re.compile(r"herunter.?laden", re.I)
                                ).first
                                if not await dl.is_visible(timeout=400):
                                    continue
                            await dl.click(timeout=5000)
                            download_done = True
                            result.details.append("Pflicht-Download geklickt")
                            await page.wait_for_timeout(1500)
                            break
                        except Exception:
                            continue

                # 2. Weiter-Button suchen. Wichtig: Wizards wie privyou haben
                #    alle Schritte (inkl. Abschluss-Button) gleichzeitig im DOM.
                #    Erfolg gilt deshalb erst, wenn kein Weiter-Kandidat mehr
                #    übrig ist und der Abschluss-Button ansteht.
                next_el, next_text = None, ""
                for frame in frames:
                    next_el, next_text = await self._find_button(
                        frame, self.next_patterns, clicked_counts
                    )
                    if next_el is not None:
                        break
                if next_el is None:
                    # Vielleicht wird der Weiter-Button erst durch die gerade
                    # gegebenen Antworten aktiviert: eine kurze zweite Chance.
                    await page.wait_for_timeout(2000)
                    for frame in frames:
                        next_el, next_text = await self._find_button(
                            frame, self.next_patterns, clicked_counts
                        )
                        if next_el is not None:
                            break

                if next_el is None:
                    # Kein Weiter mehr: Strecke ist zu Ende. Erfolg, wenn der
                    # Abschluss-Button erreichbar ist (er wird NICHT geklickt).
                    for frame in frames:
                        stop_el, stop_text = await self._find_button(frame, self.stop_patterns)
                        if stop_el is not None:
                            result.stop_button = stop_text
                            result.details.append(
                                f"Abschluss-Button erreicht (NICHT geklickt): '{stop_text}' "
                                f"nach {step} Schritt(en)"
                            )
                            return result
                    result.status = "MANUELL_PRÜFEN"
                    result.details.append(
                        f"Kein aktiver Weiter- oder Abschluss-Button in Schritt {step} gefunden"
                    )
                    errors = await self._collect_validation_errors(frames)
                    if errors:
                        result.details.append("Meldungen auf der Seite: " + " | ".join(errors))
                    full = self.screenshots_dir / f"{self._slug(link)}_fehler_komplett.png"
                    try:
                        await page.screenshot(path=str(full), full_page=True, timeout=15000)
                        result.screenshots.append(full.name)
                    except Exception:
                        pass
                    return result

                # Sicherheitsnetz: nie einen Stop-Button klicken.
                if matches_any(next_text, self.stop_patterns):
                    result.stop_button = next_text
                    result.details.append(f"Abschluss-Button erreicht (NICHT geklickt): '{next_text}'")
                    return result
                clicked_counts[next_text] = clicked_counts.get(next_text, 0) + 1
                # Auswahl-Buttons ("Wählen", "Klassik auswählen") nur EINMAL
                # klicken, sonst wird die Tarifwahl endlos umgeschaltet.
                if re.search(r"\bw(ä|ae)hlen\b", next_text, re.I):
                    clicked_counts[next_text] = 99
                # Andere Nicht-"Weiter"-Buttons ("Tarife anzeigen", "Übernehmen")
                # nach 3 Versuchen sperren; nur "Weiter..." darf beliebig oft.
                elif not re.search(r"\bweiter\b", next_text, re.I) and clicked_counts[next_text] >= 3:
                    clicked_counts[next_text] = 99

                before = await self._page_state(page)
                try:
                    await next_el.click(timeout=8000)
                except Exception:
                    # DOM kann sich zwischen Suchen und Klicken geändert haben:
                    # als Fallback direkt per JS klicken.
                    try:
                        await next_el.evaluate("e => e.click()")
                    except Exception:
                        result.status = "DEFEKT"
                        result.details.append(
                            f"'{next_text}' in Schritt {step} nicht klickbar"
                        )
                        return result
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                await page.wait_for_timeout(1500)
                after = await self._page_state(page)
                result.details.append(f"Schritt {step}: '{next_text}' geklickt")
                if after == before:
                    if clicked_counts.get(next_text, 0) >= 2:
                        # Diesen Button aufgeben und Alternativen versuchen
                        # (z.B. "Beantragung starten" statt erneut
                        # "Tarife anzeigen" bei levelnine).
                        clicked_counts[next_text] = 99
                        result.details.append(
                            f"'{next_text}' ohne Wirkung, versuche andere Buttons"
                        )
                        errors = await self._collect_validation_errors(frames)
                        if errors:
                            result.details.append(
                                "Meldungen auf der Seite: " + " | ".join(errors)
                            )
                else:
                    last_state = after

            result.status = "MANUELL_PRÜFEN"
            result.details.append(
                f"Abschluss-Button nach {self.config['funnel']['max_steps']} Schritten nicht erreicht"
            )
            full = self.screenshots_dir / f"{self._slug(link)}_fehler_komplett.png"
            try:
                await page.screenshot(path=str(full), full_page=True, timeout=15000)
                result.screenshots.append(full.name)
            except Exception:
                pass
            return result
        except Exception as exc:
            result.status = "DEFEKT"
            result.details.append(f"Strecke abgebrochen: {type(exc).__name__}: {str(exc)[:200]}")
            return result
        finally:
            if console_errors:
                result.details.append(
                    "JS-Fehler auf der Seite: " + " | ".join(sorted(set(console_errors))[:5])
                )
            await page.close()


def select_funnel_targets(links: list[LinkInfo], config: dict) -> list[LinkInfo]:
    """Nur Abschlusslinks auswählen; Tracking-Redirects bleiben HTTP-only."""
    targets = [l for l in links if l.kategorie == "abschluss" and l.typ != "tracking"]
    if not config["funnel"].get("allow_external_click_through", True):
        targets = [l for l in targets if l.typ == "intern"]
    return targets


async def check_all_funnels(
    links: list[LinkInfo], config: dict, screenshots_dir: Path
) -> tuple[list[CheckResult], dict[str, str]]:
    """Alle Abschluss-Strecken nacheinander durchklicken."""
    from playwright.async_api import async_playwright

    from .common import prepare_context

    runner = FunnelRunner(config, screenshots_dir)
    results: list[CheckResult] = []
    targets = select_funnel_targets(links, config)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        for link in targets:
            result = None
            # Bei Fehlern einmal wiederholen: Lade-Flakiness (SPA-Wizards,
            # langsame Versicherer-Server) soll keinen Fehlalarm auslösen.
            for attempt in (1, 2):
                context = await browser.new_context(
                    user_agent=config["user_agent"],
                    viewport={"width": 1280, "height": 900},
                    locale="de-DE",
                )
                await prepare_context(context, config)
                try:
                    result = await runner.run(context, link)
                finally:
                    await context.close()
                if result.status != "DEFEKT":
                    break
                if attempt == 1:
                    result.details.append("Erster Versuch fehlgeschlagen, wiederhole einmal ...")
                    first_details = list(result.details)
            if result.status == "DEFEKT" and attempt == 2:
                result.details = first_details + ["--- 2. Versuch ---"] + result.details
            results.append(result)
        await browser.close()

    return results, runner.found_downloads
