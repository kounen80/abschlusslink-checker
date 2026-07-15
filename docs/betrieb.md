# Betrieb und Freigabe

## Vor jeder Freigabe

1. Automatisierte Tests ausführen.
2. Täglichen reinen HTTP-Lauf ohne Mail prüfen.
3. Wochenlauf mit 61 eindeutigen Links ohne Mail ausführen und Report sowie
   Screenshots kontrollieren. Tracking-Links dürfen nicht im Funnel erscheinen.
4. Monats-Entry-Point kontrolliert manuell ohne Mail ausführen. Die reguläre
   Terminierung bleibt unabhängig vom Ausführungsdatum der 1. um 05:30 Uhr.
5. Erst dann Plists installieren/laden und Apple-Mail-Test ausführen.

```bash
uv run python -m unittest discover -s tests -v
uv run python -m checker.run_daily --ohne-mail
uv run python -m checker.run_weekly --ohne-mail
uv run python -m checker.run_monthly --ohne-mail
```

## launchd

Die Plists erwarten das operative Repository unter
`/Users/konrad/KI-Projekte/abschlusslink-checker`.

```bash
cp launchd/*.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/de.ovv.abschlusslink-checker.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/de.ovv.abschlusslink-daily.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/de.ovv.abschlusslink-monatscheck.plist
launchctl print gui/$(id -u)/de.ovv.abschlusslink-checker
launchctl print gui/$(id -u)/de.ovv.abschlusslink-daily
launchctl print gui/$(id -u)/de.ovv.abschlusslink-monatscheck
```

Bei bereits geladenen Jobs zuerst gezielt `launchctl bootout` für genau den
betroffenen Label-Pfad ausführen. Logs liegen im operativen Repository unter
`reports/launchd*.log`.

## Konservative Auswertung

- `OK`: Stop-Punkt sicher erreicht, ohne ihn zu klicken.
- `WEITERLEITUNG_OK`: passiver HTTP-Check nach Redirect erfolgreich.
- `MANUELL_PRÜFEN`: CAPTCHA, Bot-Sperre, 403/429 oder unklarer Browserzustand.
- `DEFEKT`: DNS/TLS/Netzwerk/Timeout, 404/410/5xx oder erkennbare Fehlerseite.

Ein Lauf mit fehlendem Internet oder Browser darf niemals als erfolgreich
dokumentiert oder zur Betriebsfreigabe verwendet werden.
