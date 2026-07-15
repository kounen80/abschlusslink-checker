# Abschlusslink-Checker

Der Checker nutzt `linkliste.yaml` als versionierte Datenbasis mit 61
eindeutigen Abschlusslinks. Der initiale Import enthielt 172 Tarife; der
kontrollierte Monatslauf vom 15.07.2026 ergänzte die neue Tarifseite
`barmenia/barmeniagothaer/` und erhöhte den aktuellen Stand auf 173.

**Unveränderliche Sicherheitsregel:** Es wird niemals ein Antrag, Kauf,
Auftrag oder eine Zahlung final bestätigt. Die in `config.yaml` definierten
`stop_patterns` werden vor jedem Klick geprüft. CAPTCHAs und unklare
Bot-Sperren werden nicht bedient, sondern als `MANUELL_PRÜFEN` gemeldet.

## Datenfluss

1. Der monatliche Lauf liest die Tarifübersicht, scannt die Tarifseiten mit
   Playwright und gleicht die sichtbaren Onlineabschlusslinks mit
   `linkliste.yaml` ab. Der bisherige Wizard-Crawl dient als Gegenprobe.
2. Der wöchentliche Lauf prüft jeden eindeutigen Link einmal per HTTP und
   jeden Nicht-Tracking-Link einmal in der Klickstrecke bis zum Stop-Punkt.
3. Der tägliche Lauf ist strikt passiv: nur HTTP-Erreichbarkeit und Redirects,
   keine Browser-, Tarif- oder Formularinteraktion.

Statuswerte: `OK`, `WEITERLEITUNG_OK`, `MANUELL_PRÜFEN`, `DEFEKT`.
DNS-, TLS-, Netzwerk- und Timeoutfehler sind nie erfolgreich.

## Bedienung

```bash
uv run python tools/import_uebergabe.py
uv run python -m unittest discover -s tests -v
uv run python -m checker.run_daily --ohne-mail
uv run python -m checker.run_weekly --ohne-mail
uv run python -m checker.run_monthly --ohne-mail
```

Reports liegen unter `reports/`. Apple Mail wird nur verwendet, wenn
`--ohne-mail` fehlt.

## launchd-Zeitpläne (Europe/Berlin / lokale Mac-Zeit)

- `de.ovv.abschlusslink-checker`: Montag 10:00 Uhr
- `de.ovv.abschlusslink-daily`: täglich 10:00 Uhr
- `de.ovv.abschlusslink-monatscheck`: am 1. des Monats 05:30 Uhr

Die Plists liegen in `launchd/`. Installation und Freigabe erfolgen erst nach
erfolgreichem Tages-, Wochen- und kontrolliert manuellem Monatslauf. Details:
`docs/betrieb.md`.

## Konfiguration

- `config.yaml`: Stop-/Weiter-Muster, Crawl- und Reporteinstellungen
- `testdaten.yaml`: eindeutig markierte Dummy-Daten und Bundesbank-Test-IBAN
- `anleitungen.md`: fachlich verifizierte Klickabläufe
- `docs/uebergabe-linkpruefung-2026-07-15.md`: Quelle der initialen Linkliste
