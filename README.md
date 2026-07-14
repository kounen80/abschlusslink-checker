# Abschlusslink-Checker

Wöchentlicher automatischer Prüflauf für alle "Online abschließen"-Strecken
auf www.test-zahnzusatzversicherung.de.

**Wichtigste Regel: Es wird NIE ein Antrag abgesendet.** Buttons wie
"Jetzt abschließen", "kostenpflichtig bestellen" oder "Antrag senden" werden
erkannt und niemals geklickt. Das Erreichen eines solchen Buttons gilt als
erfolgreicher Test der Strecke.

## Was wird geprüft

1. **Link-Entdeckung**: Der Vergleichsrechner wird mit 3 Test-Profilen
   (8 / 25 / 60 Jahre, alle Gesundheitsfragen "Nein") durchgeklickt; dazu
   Startseite und alle Tarif-Detailseiten. Neue Tarife werden automatisch
   erkannt, verschwundene gemeldet.
2. **Erreichbarkeit**: Jeder Abschluss- und Detail-Link (HTTP-Status,
   Redirects, Soft-404, Antwortzeit, Vermittler-Parameter).
3. **Klickstrecken**: Jede Antragsstrecke (intern und extern) wird mit
   markierten Testdaten ("TEST Testlauf-OVV") bis zum letzten Klick vor dem
   Abschluss ausgefüllt und durchgeklickt. Screenshot je Schritt.
4. **Downloads**: Alle gefundenen PDFs (Status, Inhaltstyp, Größe, %PDF-Header).

## Bedienung

```bash
# Kompletter Lauf inkl. E-Mail-Report
uv run python -m checker.run_weekly

# Lauf ohne E-Mail
uv run python -m checker.run_weekly --ohne-mail

# Nur Link-Entdeckung testen
uv run python smoke_test.py
```

Reports landen in `reports/JJJJ-MM-TT/report.html` (mit Screenshots).
Der E-Mail-Versand läuft über Apple Mail an info@test-zahnzusatzversicherung.de.

## Zeitplan

launchd-Job `de.ovv.abschlusslink-checker` läuft montags 07:00
(`~/Library/LaunchAgents/de.ovv.abschlusslink-checker.plist`).

```bash
# Status prüfen
launchctl list | grep abschlusslink
# Sofort manuell auslösen
launchctl kickstart gui/$(id -u)/de.ovv.abschlusslink-checker
```

## Konfiguration

- `config.yaml`: Profile, Stop-/Weiter-Button-Muster, E-Mail-Empfänger
- `testdaten.yaml`: Dummy-Daten für die Formulare (deutlich als TEST markiert;
  IBAN ist die offizielle Bundesbank-Test-IBAN und wird nur in Pflichtfelder
  eingetragen)

## Hinweise

- Der Test-Browser setzt `plausible_ignore`, taucht also nicht in der
  eigenen Plausible-Statistik auf. User-Agent: `OVV-LinkChecker/1.0`.
- Externe Versicherer-Strecken werden bewusst mit durchgeklickt (Risiko
  von Test-Leads beim Versicherer wurde akzeptiert; Daten sind eindeutig
  als Test erkennbar).
- Scheitert eine Strecke, steht im Report das Klick-Protokoll samt
  Validierungsmeldungen und Ganzseiten-Screenshot des Fehlerzustands.
