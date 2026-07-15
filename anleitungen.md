# Klick-Anleitungen von Konrad (14.07.2026, diktiert)

## Automatischer Datenfluss und Sicherheitsstatus

`linkliste.yaml` wird monatlich aus der Tarifübersicht abgeglichen und ist
die alleinige Zielbasis für Wochen- und Tageslauf. Identische absolute URLs
werden nur einmal geprüft. `typ: tracking` erhält nur den HTTP-/Redirect-Check.
CAPTCHA, Bot-Sperre oder ein unklarer Zustand beendet jede Interaktion sofort
mit `MANUELL_PRÜFEN`. Die folgenden Abläufe gelten nur bis zum ersten Element,
das auf ein `stop_pattern` passt; dieses Element wird niemals geklickt.

Konrad hat die fehlgeschlagenen Antragsstrecken manuell durchgespielt.
Diese Anleitungen sind die Referenz für die Strecken-Heuristiken.

## Generelle Regeln (gelten bei fast allen Gesellschaften)

- "Sind Sie gesetzlich krankenversichert (in Deutschland)?" → **JA**
- Alle Gesundheitsfragen (Prothese, Erkrankung, fehlende Zähne, Parodontose,
  laufende Behandlung, andere Zahnversicherung vorhanden) → **NEIN** / 0
- Vorbelegte Tarife/Versicherungsbeginne einfach übernehmen
- Haken für Anzeigepflicht, Gesundheitsdaten-Erhebung, Kenntnisnahme,
  Beratungsverzicht, Lastschrift/SEPA setzen
- Test endet jeweils nach Eingabe der persönlichen Daten / vor dem finalen
  Absenden

## ottonova (Zahn 100 plus)

Partnerdaten oben sind fix (Partner-/Agenturnummer optional leer lassen).
Geburtsdatum. Gesetzlich versichert: JA. Bereits Zahnversicherung: NEIN.
Haken: gesetzliche Anzeigepflicht + Erhebung/Verwendung Gesundheitsdaten.
Prothese/Erkrankung/fehlende Zähne: Nein (teils vorbelegt). Persönliche
Dummy-Daten, IBAN, Kreuz bei Lastschrift, dann zur Zusammenfassung. Bis dahin prüfen.

## ERGO (i.ergo.de, Dental-Schutz)

Erst Popup bestätigen. Geburtsdatum (TT MM JJJJ Einzelfelder). Tarifvariante
ist vorbelegt (Baukasten, nichts ändern). **"Jetzt online abschließen" ist hier
ein ZWISCHENSCHRITT** (führt zu "Wer soll versichert werden?"). Dann "Ich",
Geburtsdatum, weiter, Versicherungsbeginn bestätigen, Versicherungsauswahl
stehen lassen, weiter.

## SDK / UKV (levelnine-Plattform, "verhalten identisch")

Geburtsdatum, Geschlecht, "Tarife anzeigen". Tarif 1 / 100 wählen.
"Berechnung starten". Vor-/Nachname, Haken "Informationen zur Verwendung
Ihrer Daten gelesen". "Beantragung starten". Vorletzter Punkt: "alle
Dokumente herunterladen" klicken (lädt PDFs). "Weiter", mehreres zustimmen
(Werbe-Einwilligung ja/nein egal). Fehlende Zähne: 0, weiter.
Beratungsverzicht zustimmen, weiter. Persönliche Daten, zustimmen, weiter → Ende.

## Concordia (ZAHN SORGLOS)

Cookies akzeptieren. Beginn: nächstmöglicher. Geburtsdatum. Versicherungsart:
gesetzlich. Schieberegler: Punkt 3 "Vorsorge für die Zähne" AKTIVIEREN.
Weitere Personen: Nein. Weiter. Nächste Seite: "Antrag stellen". Persönliche
Daten bis Bankverbindung, weiter → Ende.

## ERGO direkt / DA Direkt

Cookies akzeptieren, Geburtsdatum, Tarif vorbelegt, "Jetzt online abschließen"
(Zwischenschritt), "Ich", weiter, Geburtsdatum. DA Direkt: "für mich",
Geburtsdatum Tag/Monat/Jahr, Zahnschutz Komfort stehen lassen, weiter,
gesetzlich versichert JA, weiter, persönliche Daten, weiter → Ende.

## Deutsche Familienversicherung (DFV)

Vertragsangaben: "mich", Geburtsdatum, Beginn vorbelegt, weiter. Persönliche
Daten. Haken "die zu versichernde Person ist gesetzlich krankenversichert".
Weiter → Ende.

## uniVersa (uni-dent)

"Wen möchtest Du versichern": mich selbst (vorbelegt). Gesetzliche KV
(vorbelegt). Private Zusatzversicherung: Nein (vorbelegt). Nur Geburtsdatum
eintragen, Beginn vorbelegt, weiter. Absicherung: immer ganz rechts 100 % /
250 € pro Kalenderjahr / 100 % / "unsere Empfehlung". Nächste Seite: Empfehlung
"uni-dent privat" → "auswählen". Persönliche Daten. "Ja, ich erteile der
uniVersa das SEPA-Mandat", "Angaben prüfen" → Ende.

## Signal Iduna (ZahnEXKLUSIVpur)

Cookies akzeptieren. Beginn vorbelegt. Vorname, Nachname, Geburtsdatum, weiter.
"Ich habe den Link geöffnet, das Dokument zur Kenntnis genommen" anhaken.
Gesundheitsfragen alle Nein. Weiter. "Nein, weiter mit Tarifauswahl".
Teuersten Tarif ZahnEXKLUSIVpur (eh vorgewählt). Weiter. Andere
Zahnversicherung: Nein. Gesetzliche Krankenversicherung: AOK auswählen.
Weiter. Persönliche Daten, weiter → Ende.

## Allianz (MeinZahnschutz)

Cookies akzeptieren. Geburtsdatum. Beginn vorbelegt. Gesetzlich
krankenversichert in Deutschland: **JA**. Anderweitige Zahnversicherung: Nein.
Gesundheitsfragen (in Behandlung?): Nein. Fehlende Zähne 0 vorbelegt. Tarif
100 % wählen. "Jetzt günstige Beiträge ohne Alterungsrückstellungen" klicken.
**"Jetzt Tarif beantragen" ist ZWISCHENSCHRITT**. Nächste Seite: Empfehlung
"MeinZahnschutz 100" auswählen, ganz unten "weiter zum Antrag". Persönliche
Daten → Ende.

## Die Bayerische (ZAHN Komfort/Prestige)

Cookies akzeptieren. Beginn vorbelegt. **Gültige PLZ eingeben (wichtig für
Berechnung)**, Vorname, Geburtsdatum. "Zur Tarifauswahl". Tarif Prestige
vorgewählt. Ganz unten "zu den Zahnauskünften" (Gesundheitsauskünfte).
Gesundheitsfragen alle Nein (auch Zahnfleischschutz letzte 12 Monate).
"Zu den persönlichen Angaben". Persönliche Daten, weiter → Ende.

## Münchener Verein (ZahnGesund)

Cookies zustimmen. Beginn vorbelegt, Tarif gewählt, fehlende Zähne Nein.
"Weiter zu Ihren Angaben". Persönliche Daten, weiter → Ende.

## Württembergische

Cookies akzeptieren. Anrede, Vor-/Nachname, Geburtsdatum. Gesetzlich
versichert. "Weiter zur Tarifauswahl" (Kompakttarif stehen lassen).
"Weiter zur Risikoprüfung": **Möglichkeit 1 wählen** (Einwilligung Erhebung/
Verarbeitung Gesundheitsdaten). "Weiter zu den rechtlichen Hinweisen":
Kenntnisnahme zur Risikoprüfung ankreuzen. "Weiter zu den Gesundheitsfragen":
0 fehlende Zähne eingeben, **"Übernehmen"**, "weiter zur Auswertung".
Zahnbetterkrankung letzte 24 Monate: Nein. "Weiter zur Auswertung",
"weiter zum Angebot", "weiter zum Antrag", persönliche Daten → Ende.
