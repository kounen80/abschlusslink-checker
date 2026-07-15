# Umsetzungsplan: Linkliste als Datenbasis + monatlicher Übersichts-Check

Dieser Plan ist für eine umsetzende KI (z.B. ChatGPT/Codex) oder einen
Entwickler geschrieben. Er erweitert den bestehenden Abschlusslink-Checker
in diesem Repository.

## Verbindliche Regeln für die Umsetzung

1. **NIEMALS einen Versicherungsantrag absenden.** Buttons, deren Text auf
   die `stop_patterns` in `config.yaml` passt ("jetzt abschließen",
   "kostenpflichtig", "zahlungspflichtig", "verbindlich", "Antrag senden",
   "beantragen" usw.), dürfen unter keinen Umständen geklickt werden. Das
   Erreichen eines solchen Buttons gilt als erfolgreiches Testende. Diese
   Schutzlogik in `checker/check_funnel.py` darf nicht abgeschwächt werden.
2. Kein CAPTCHA umgehen, keine Bot-Erkennung austricksen. Solche Strecken
   bekommen den Status MANUELL_PRÜFEN.
3. Testdaten nur aus `testdaten.yaml` (eindeutig als TEST markiert,
   Bundesbank-Test-IBAN). Keine echten personenbezogenen Daten Dritter.
4. `anleitungen.md` enthält die manuell verifizierten Klick-Abläufe je
   Versicherer und ist die fachliche Referenz bei Streckenproblemen.
5. Live-Tests gegen die Versicherer-Seiten brauchen echten Internetzugang
   und einen installierten Playwright-Chromium (`uv run playwright install
   chromium`). In Sandboxen ohne Netz nur Code schreiben, nicht "grün" melden.
6. Zwei Schritte können nur lokal auf Konrads Mac erfolgen und sind hier nur
   vorzubereiten: das Laden der launchd-Jobs und der Apple-Mail-Testversand.

---

## Kontext

Der bestehende Checker (`/Users/konrad/KI-Projekte/abschlusslink-checker/`, auch auf GitHub kounen80/abschlusslink-checker) entdeckt Abschlusslinks bisher über den Vergleichsrechner-Wizard und findet so 22 Links. Eine externe Recherche (Übergabe-Datei `/Users/konrad/Documents/Codex/2026-07-15/ich-m-chte-eine-linkliste-erstellen/outputs/uebergabe-linkpruefung.md`) hat über die Übersichtsseite https://www.test-zahnzusatzversicherung.de/teilnehmende-versicherungen-und-tarife/ die vollständige Basis ermittelt: **441 Tarifseiten, 172 Tarife mit Onlineabschluss, 61 eindeutige Abschlusslinks** (inkl. Zuordnung Tarif → Link).

Konrads Entscheidungen:
- **Wöchentlich** (bestehender Montags-Job): alle 61 Links per HTTP prüfen UND alle 61 Strecken voll durchklicken (Laufzeit ~2h ist akzeptiert).
- **Monatlich** (neuer Job): Übersichtsseite crawlen, Ist-Zustand mit der Linkliste abgleichen; Änderungen automatisch übernehmen und im Report ausweisen.

Technischer Befund: Die Übersichtsseite listet die ~506 Anbieter-/Tarifseiten-Links statisch (httpx reicht). Die "Online abschließen"-Links auf den Tarifseiten werden per JavaScript gerendert → der Monats-Crawl nutzt Playwright; die vorhandene Funktion `_scan_static_page` in `checker/discover.py` macht genau das bereits.

## Umsetzung

### 1. Linkliste als versionierte Datenbasis: `linkliste.yaml`

Einmalige Konvertierung der Übergabe-Markdown (61 Blöcke) in `linkliste.yaml`:

```yaml
- gesellschaft: "ADVIGON"
  abschluss_url: "https://secure2.advigon.com/ola-ui2/46/100/tr/basisdaten?adnr=4161618"
  tarife:
    - name: "Dental Premium AZE4+AZB3"
      tarifseite: "https://www.test-zahnzusatzversicherung.de/anbieter/advigon/advigon-azb3-aze4/"
    - ...
```

Konvertierungsskript `tools/import_uebergabe.py` (parst die Markdown-Struktur `## N. Gesellschaft — X Tarife` / `[Onlineabschluss öffnen](URL)` / Tarif-Liste). Wird einmal ausgeführt, bleibt für spätere Re-Importe im Repo.

### 2. Wochenlauf umbauen (`checker/run_weekly.py`, `checker/discover.py`)

- Prüfziele kommen aus `linkliste.yaml` (61 Links mit Gesellschaft/Tarifen als Metadaten) statt aus der Wizard-Discovery.
- Der bisherige Wizard-Crawl + Detailseiten-Scan entfällt im Wochenlauf (wandert in den Monatslauf als Gegenprobe).
- HTTP-Check (`check_links.py`) und Klickstrecken-Test (`check_funnel.py`) laufen unverändert über alle 61 Links; Report zeigt je Link Gesellschaft + zugeordnete Tarife.
- `LinkInfo` bekommt Feld `gesellschaft`; Report-Template entsprechend ergänzen.
- Duplikat-Schutz: financeads.net-Tracking-Links (Nr. 10, 26, 47 der Liste) sind Affiliate-Redirects → nur HTTP-Check + finale URL dokumentieren, kein Klick-Test (Affiliate-Klicks nicht künstlich erzeugen? Doch, einer pro Woche ist ok — aber als `typ: tracking` markieren und im Report kennzeichnen).

### 3. Neuer Monatslauf: `checker/run_monthly.py` + `checker/check_uebersicht.py`

1. Übersichtsseite per httpx laden, alle `/anbieter/<gesellschaft>/<tarif>/`-URLs extrahieren (Gesellschaftsseiten von Tarifseiten trennen: Tarifseiten haben 2 Pfadsegmente unter /anbieter/; AOK-Sonderfall 3 Segmente beachten, siehe Übergabe).
2. Jede Tarifseite mit Playwright öffnen (`_scan_static_page` wiederverwenden), sichtbaren "Online abschließen"-Link extrahieren (~441 Seiten × ~3s ≈ 25–40 min).
3. Abgleich mit `linkliste.yaml`:
   - neue Tarifseiten / neue Abschluss-URLs → ergänzen
   - entfallene Tarife (kein "Online abschließen" mehr) → aus Liste entfernen, im Report als "Onlineabschluss entfallen" melden
   - geänderte Ziel-URL eines Tarifs → aktualisieren + melden
4. Aktualisierte `linkliste.yaml` schreiben (git-versioniert → Änderungshistorie), Monats-Report als HTML + Mail (bestehendes `report.py` wiederverwenden, eigener Betreff `[Linkcheck] Monats-Check – N Änderungen`).
5. Wizard-Crawl (bisherige `discover_links`) als Gegenprobe: Links, die der Rechner zeigt, aber nicht in der Linkliste stehen → Warnung.

### 4. Zeitpläne (launchd)

- Bestehender Job `de.ovv.abschlusslink-checker` (Mo 07:00) bleibt → Wochenlauf.
- Neuer Job `de.ovv.abschlusslink-monatscheck`: 1. Tag des Monats, 05:30 (`StartCalendarInterval` mit `Day=1`), gleiche Plist-Struktur, ruft `checker.run_monthly` auf.

### 5. Status-Modell aus der Übergabe übernehmen

Mapping im Report ergänzen: OK (Strecke bis Abschluss-Button) / WEITERLEITUNG_OK (HTTP ok nach Redirect, Klick-Test nicht möglich) / MANUELL_PRÜFEN (Captcha/Bot-Sperre/unklar — statt "fehler", damit ottonova/ERGO/DA Direkt nicht dauerhaft rot sind) / DEFEKT (404/5xx/Timeout/Fehlerseite). Erkennung Bot-Sperre: 403-Ressourcen + leere Seite → MANUELL_PRÜFEN.

### 6. Doku & Repo

`README.md` und `anleitungen.md` ergänzen (Datenfluss: Monats-Check pflegt linkliste.yaml → Wochenlauf prüft sie), Übergabe-Datei als `docs/uebergabe-linkpruefung-2026-07-15.md` ins Repo kopieren, alles committen und pushen.

## Kritische Dateien

- `linkliste.yaml` (neu), `tools/import_uebergabe.py` (neu)
- `checker/run_monthly.py`, `checker/check_uebersicht.py` (neu)
- `checker/run_weekly.py`, `checker/discover.py`, `checker/common.py` (LinkInfo), `checker/report.py` (anpassen)
- `launchd/de.ovv.abschlusslink-monatscheck.plist` (neu)

Wiederverwendung: `_scan_static_page`, `check_all_links`, `check_all_funnels`, `build_report`, `send_via_apple_mail`.

## Verifikation

1. `tools/import_uebergabe.py` → linkliste.yaml enthält exakt 61 Links / 172 Tarife (Zähl-Assert).
2. Monatslauf einmal manuell: findet auf der Übersichtsseite ~441 Tarifseiten, Abgleich meldet idealerweise 0–wenige Abweichungen gegenüber der frischen Recherche vom 15.07.; Stichprobe von 3 gemeldeten Abweichungen manuell prüfen.
3. Wochenlauf einmal manuell mit der neuen 61er-Liste (Laufzeit messen); Report zeigt Gesellschaft/Tarife je Link; die 9 bekannten grünen Strecken bleiben grün.
4. launchd: beide Jobs geladen (`launchctl list | grep ovv`).
5. Commit + Push nach GitHub.

## Offene Punkte

- Die 3 financeads-Tracking-Links: beim ersten Lauf beobachten, ob der Klick-Test dort sauber terminiert; sonst auf HTTP-Check beschränken.
- Falls der Playwright-Crawl der 441 Seiten von der eigenen Seite gedrosselt wird: Wartezeit zwischen Seiten erhöhen (Konfig `uebersicht.delay_ms`).
