# Übergabe: Online-Abschlusslinks für Zahnzusatzversicherungen

Stand: 15.07.2026  
Ausgangsseite: https://www.test-zahnzusatzversicherung.de/teilnehmende-versicherungen-und-tarife/

## Ziel des Projekts

Gesucht werden die tatsächlichen Online-Abschlussstrecken der auf der Ausgangsseite aufgeführten Tarife. Die Links sollen regelmäßig darauf geprüft werden, ob sie erreichbar sind, korrekt weiterleiten und eine plausible Abschluss- beziehungsweise Tarifauswahl ermöglichen.

Wichtig: Viele Tarife einer Gesellschaft verwenden denselben zentralen Abschlussrechner. Ein identischer Abschlusslink darf deshalb nur einmal in der Prüfliste vorkommen. Die betroffenen Tarife werden diesem einen Link zugeordnet.

## Bisheriges Ergebnis

- Auf der Übersichtsseite wurden 441 echte Tarifseiten berücksichtigt.
- Vier verschachtelte AOK-Gesellschaftsseiten wurden nicht als Tarife gezählt.
- Auf 172 Tarifseiten war ein sichtbarer Link mit der Bezeichnung „Online abschließen“ vorhanden.
- Nach exakter Deduplizierung der Ziel-URLs verblieben 61 eindeutige Abschlusslinks.
- Die 172 Tarife sind unter diesen 61 Links als Zuordnungen erhalten.
- Identische Links, die sogar gesellschaftsübergreifend verwendet werden, wurden ebenfalls zusammengeführt.
- Das Geburtsjahr 2000 wurde exemplarisch auf einer Tarifseite eingegeben. Der Abschlusslink war dort unabhängig von dieser Eingabe sichtbar.
- Es wurde kein Versicherungsantrag abgeschickt und keine Abschlussstrecke final bestätigt.

## Wo die Links gefunden wurden

Die Tarifseiten wurden aus der Gesellschafts- und Tarifübersicht extrahiert. Anschließend wurde jede Tarifseite geöffnet und gezielt nach dem sichtbaren Link „Online abschließen“ gesucht. Aus dessen `href` wurde die absolute Ziel-URL gebildet. Relative Links, beispielsweise interne Getsafe-Antragswege, wurden gegen die jeweilige Tarifseiten-Domain aufgelöst.

Für jeden Treffer wurden gespeichert:

- Gesellschaft
- Tarifname
- Tarifseite auf test-zahnzusatzversicherung.de
- direkter Online-Abschlusslink

Die vollständigen Zuordnungen stehen weiter unten in dieser Datei.

## Vorgehensweise

1. Tarifübersicht geöffnet und Tariflinks nach Gesellschaft erfasst.
2. Gesellschaftsseiten und echte Tarifseiten voneinander getrennt.
3. Jede echte Tarifseite einzeln aufgerufen.
4. Sichtbarkeit eines Links „Online abschließen“ kontrolliert.
5. Ziel-URL des Links extrahiert und relative URLs absolut aufgelöst.
6. Exakt identische Ziel-URLs zusammengeführt.
7. Alle Tarife, die denselben Abschlussrechner verwenden, diesem einen Link zugeordnet.
8. Ergebnis als Markdown-Liste strukturiert.

## Was bereits belastbar ist

Belastbar bestätigt ist:

- Die unten aufgeführten Abschlusslinks waren am 15.07.2026 auf den jeweiligen Tarifseiten als „Online abschließen“ verlinkt.
- Die Liste enthält jeden exakt identischen Ziel-Link nur einmal.
- Die Zuordnung der 172 Tarifseiten zu den 61 Ziel-URLs ist dokumentiert.

## Was noch nicht vollständig geprüft ist

Die 61 Ziel-URLs wurden noch nicht vollständig und einheitlich auf einer gemeinsamen Prüflogik validiert. Einzelne Zielseiten wurden geöffnet und erschienen plausibel; für die Gesamtheit liegt aber noch kein belastbarer, pro Link dokumentierter Funktionsstatus vor.

Noch ausstehend sind je Link:

- HTTP- beziehungsweise Browser-Erreichbarkeit
- endgültige URL nach Weiterleitungen
- Erkennung von Fehler-, Wartungs- oder Sperrseiten
- plausible Abschluss- oder Beitragsrechner-Oberfläche
- gegebenenfalls vorhandene Tarifauswahl
- Kontrolle, ob die zugeordneten Tarife dort auswählbar sind
- Ergebnisstatus und Prüfzeitpunkt

Daher bedeutet ein Eintrag aktuell: **„Abschlusslink auf der Tarifseite gefunden“**. Er bedeutet noch nicht automatisch: **„Abschlussstrecke vollständig funktionsfähig“**.

## Empfohlene Prüflogik für die nächste KI oder ein Skript

Für jeden der 61 Links sollte ein Datensatz mit folgenden Feldern erzeugt werden:

| Feld | Bedeutung |
|---|---|
| Gesellschaft(en) | Zugeordnete Gesellschaften |
| Tarife | Zugeordnete Tarife |
| Ausgangs-URL | Der unten gespeicherte Abschlusslink |
| Prüfzeitpunkt | Datum und Uhrzeit mit Zeitzone |
| Status | OK, WEITERLEITUNG_OK, MANUELL_PRÜFEN oder DEFEKT |
| HTTP-Status | Falls technisch verfügbar |
| Finale URL | Ziel nach allen Weiterleitungen |
| Seitentitel | Titel der geladenen Seite |
| Ladezeit | Gemessene Dauer |
| Nachweis | Gefundener Seitentext, Bedienelement oder Screenshot |
| Tarifauswahl | Vorhanden / nicht vorhanden / unklar |
| Bemerkung | CAPTCHA, Bot-Sperre, Timeout oder sonstige Auffälligkeit |

Empfohlene Statusdefinitionen:

- **OK:** Zielseite lädt und zeigt eine plausible Abschluss- oder Tarifauswahl.
- **WEITERLEITUNG_OK:** Link leitet weiter; die finale Seite ist plausibel.
- **MANUELL_PRÜFEN:** CAPTCHA, Bot-Sperre, Cookie-Overlay oder technisch nicht eindeutig.
- **DEFEKT:** DNS-/TLS-Fehler, dauerhafter Timeout, 404/410/5xx oder erkennbare Fehlerseite.

Zuerst kann ein tokenfreies Skript HTTP-Status, Weiterleitungen und Ladezeiten prüfen. Anschließend sollte Playwright oder ein anderer Headless-Browser nur dynamische beziehungsweise auffällige Links öffnen. Eine KI muss dann nur noch unklare Fälle beurteilen.

Nicht erlaubt beziehungsweise nicht erforderlich:

- keinen Antrag absenden
- keine personenbezogenen Daten eingeben
- kein CAPTCHA umgehen
- keine Zahlungs- oder Vertragsbestätigung auslösen

## Hinweis zur Deduplizierung

Die aktuelle Deduplizierung basiert auf der vollständigen absoluten URL. Zwei URLs mit unterschiedlichen Trackingparametern gelten daher noch als verschieden, selbst wenn sie möglicherweise denselben Rechner öffnen. Eine weitere funktionale Zusammenführung sollte nur erfolgen, wenn Weiterleitung, finale URL und angezeigte Abschlussstrecke nachweislich identisch sind.

## Arbeitsauftrag für die nächste KI

> Prüfe alle 61 eindeutigen Online-Abschlusslinks in dieser Datei. Öffne jeden Link, dokumentiere finale URL, Erreichbarkeit, Seitentitel, sichtbaren Nachweis einer Abschlussstrecke und – soweit ohne Antrag oder personenbezogene Daten möglich – die vorhandene Tarifauswahl. Ordne jedem Link einen der Status OK, WEITERLEITUNG_OK, MANUELL_PRÜFEN oder DEFEKT zu. Sende keinen Antrag ab und umgehe keine Captchas. Aktualisiere die Liste um Prüfzeitpunkt, Status und Bemerkung. Fasse funktional identische Links mit abweichenden Trackingparametern nur zusammen, wenn ihre Gleichheit belegt ist.

---

# Eindeutige Online-Abschlusslinks

Stand: 15.07.2026

Aus 441 geprüften Tarifseiten wurden 172 Tarife mit Online-Abschluss ermittelt. Da viele Tarife denselben gesellschaftsweiten Abschlussrechner verwenden, ist jeder eindeutige Abschlusslink in dieser Liste nur einmal enthalten.

**Ergebnis: 61 eindeutige Abschlusslinks.**

## 1. ADVIGON — 4 Tarife

[Onlineabschluss öffnen](https://secure2.advigon.com/ola-ui2/46/100/tr/basisdaten?adnr=4161618)

Zugeordnete Tarife:

- [Dental Premium AZE4+AZB3](https://www.test-zahnzusatzversicherung.de/anbieter/advigon/advigon-azb3-aze4/)
- [Dental Medium (AZM)](https://www.test-zahnzusatzversicherung.de/anbieter/advigon/dental-medium-azm/)
- [Dental Luxus (AZL)](https://www.test-zahnzusatzversicherung.de/anbieter/advigon/dental-luxus-azl/)
- [Dental Clever AZE1+AZB2](https://www.test-zahnzusatzversicherung.de/anbieter/advigon/advigon-azb2-aze1/)

## 2. Allianz — 6 Tarife

[Onlineabschluss öffnen](https://www.allianz.de/angebot/kooperation/gesundheit/zahnzusatzversicherung/rechner#OnlineVersicherungsVergleich)

Zugeordnete Tarife:

- [MeinZahnschutz 90](https://www.test-zahnzusatzversicherung.de/anbieter/allianz/allianz-mein-zahnschutz90/)
- [MeinZahnschutz 75](https://www.test-zahnzusatzversicherung.de/anbieter/allianz/allianz-mein-zahnschutz75/)
- [MeinZahnschutz 100](https://www.test-zahnzusatzversicherung.de/anbieter/allianz/allianz-mein-zahnschutz100/)
- [MeinZahnschutz 100AR](https://www.test-zahnzusatzversicherung.de/anbieter/allianz/allianz-mein-zahnschutz100ar/)
- [MeinZahnschutz 90AR](https://www.test-zahnzusatzversicherung.de/anbieter/allianz/allianz-mein-zahnschutz90ar/)
- [MeinZahnschutz 75AR](https://www.test-zahnzusatzversicherung.de/anbieter/allianz/allianz-mein-zahnschutz75ar/)

## 3. AOK / DKV — 2 Tarife

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/tarifrechner/1302076/Z80-PLS)

Zugeordnete Tarife:

- [AOK: Hessen - Basis Z80 Plus](https://www.test-zahnzusatzversicherung.de/anbieter/aok/aok-hessen/hessen-basis-z80-pls/)
- [DKV: KombiMed Zahn Z80 + PLS](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/kombimed-zahn-z80-pls/)

## 4. AXA — 3 Tarife

[Onlineabschluss öffnen](https://zahnzusatz.axa.de/?ORGANUMMER=8834003274&VERTRIEBAKT=MVT&VM_NACHNAME=Online%20Versicherungsvergleich%20GmbH&VM_EMAIL=info@test-zahnzusatzversicherung.de&VM_FA_TELVOR=089&VM_FA_TEL=40287399&MODE=71)

Zugeordnete Tarife:

- [Zahn Premium](https://www.test-zahnzusatzversicherung.de/anbieter/axa/zahn-premium/)
- [Zahn Klassik](https://www.test-zahnzusatzversicherung.de/anbieter/axa/zahn-klassik/)
- [Zahn Komfort](https://www.test-zahnzusatzversicherung.de/anbieter/axa/zahn-komfort/)

## 5. Barmenia — 11 Tarife

[Onlineabschluss öffnen](https://ssl.barmenia.de/oa-zahn/#/Beitrag?adm=00104231&sparte=sonstige&p0=234003)

Zugeordnete Tarife:

- [Mehr Zahn 100 + Mehr Zahnvorsorge Bonus](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahn-100-zahnvorsorge-bonus/)
- [Mehr Zahn 80 + Mehr Zahnvorsorge Bonus](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahn-80-zahnvorsorge-bonus/)
- [Mehr Zahn 90 + Mehr Zahnvorsorge Bonus](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahn-90-zahnvorsorge-bonus/)
- [Mehr Zahn 80](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahn-80/)
- [MehrZahnvorsorge](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahnvorsorge/)
- [Mehr Zahn 90](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahn-90/)
- [Mehr Zahn 100](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahn-100/)
- [Mehr Zahnvorsorge D](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-zahnvorsorge-d/)
- [Mehr Zahn 90 + Mehr Zahnvorsorge Bonus D](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/mehr-zahn-90-zahnvorsorge-bonus-d/)
- [Mehr Zahn 80 + Mehr Zahnvorsorge Bonus D](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/mehr-zahn-80-zahnvorsorge-bonus-d/)
- [Mehr Zahn 100 + Mehr Zahnvorsorge Bonus D](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/mehr-zahn-100-zahnvorsorge-bonus-d/)

## 6. Barmenia — 3 Tarife

[Onlineabschluss öffnen](https://ssl.barmenia.de/oa-ambulant/#/Beitrag?adm=00104231&sparte=sonstige&p0=234003)

Zugeordnete Tarife:

- [Mehr Gesundheit 2.000 D](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-gesundheit-2000-d/)
- [Mehr Gesundheit 1.000 D](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-gesundheit-1000-d/)
- [Mehr Gesundheit 500 D](https://www.test-zahnzusatzversicherung.de/anbieter/barmenia/barmenia-mehr-gesundheit-500-d/)

## 7. Berlin Direkt — 3 Tarife

[Onlineabschluss öffnen](https://buchung.berlin-direktversicherung.de/bdv/zahnzusatz?TerminalId=4161618)

Zugeordnete Tarife:

- [DZ](https://www.test-zahnzusatzversicherung.de/anbieter/berlin-direkt/dz/)
- [DZL](https://www.test-zahnzusatzversicherung.de/anbieter/berlin-direkt/dzl/)
- [DZM](https://www.test-zahnzusatzversicherung.de/anbieter/berlin-direkt/dzm/)

## 8. Concordia — 4 Tarife

[Onlineabschluss öffnen](https://cosima.concordia.de/tarifrechner/Krankenzusatz-Tarifrechner/start?vermittler-id=07702000)

Zugeordnete Tarife:

- [ZT + ZB](https://www.test-zahnzusatzversicherung.de/anbieter/concordia/concordia-zt-zb/)
- [Concordia Familie (Kind + Elternteil)](https://www.test-zahnzusatzversicherung.de/anbieter/concordia/zahn-sorglos-familie/)
- [ZAHN SORGLOS](https://www.test-zahnzusatzversicherung.de/anbieter/concordia/zahn-sorglos/)
- [Zahnersatz ZT](https://www.test-zahnzusatzversicherung.de/anbieter/concordia/concordia-zt/)

## 9. DA Direkt / dentolo — 6 Tarife

[Onlineabschluss öffnen](https://www.da-direkt.de/partner/zz-rechner?flow=schema_da_direkt_026072981)

Zugeordnete Tarife:

- [DA Direkt: Zahnschutz Premium Plus](https://www.test-zahnzusatzversicherung.de/anbieter/da-direkt/da-direkt-premium-plus/)
- [DA Direkt: Zahnschutz Komfort](https://www.test-zahnzusatzversicherung.de/anbieter/da-direkt/da-direkt-komfort/)
- [DA Direkt: Zahnschutz Premium](https://www.test-zahnzusatzversicherung.de/anbieter/da-direkt/da-direkt-premium/)
- [dentolo: Dentolo Zahnschutz Premium Plus](https://www.test-zahnzusatzversicherung.de/anbieter/dentolo/zahnschutz-premium-plus/)
- [dentolo: Dentolo Zahnschutz Komfort](https://www.test-zahnzusatzversicherung.de/anbieter/dentolo/zahnschutz-komfort/)
- [dentolo: Dentolo Zahnschutz Premium](https://www.test-zahnzusatzversicherung.de/anbieter/dentolo/zahnschutz-premium/)

## 10. DA Direkt / dentolo — 2 Tarife

[Onlineabschluss öffnen](https://www.financeads.net/tc.php?t=53926C37097538T)

Zugeordnete Tarife:

- [DA Direkt: Zahnschutz Akut Soforthilfe + Zahnschutz Komfort](https://www.test-zahnzusatzversicherung.de/anbieter/da-direkt/zahnschutz-komfort-akut-soforthilfe/)
- [dentolo: Dentolo Akut Soforthilfe Komfort](https://www.test-zahnzusatzversicherung.de/anbieter/dentolo/zahnschutz-akut-soforthilfe/)

## 11. Deutsche Familienversicherung / MAXCARE — 3 Tarife

[Onlineabschluss öffnen](https://makler.deutsche-familienversicherung.de/partner/iframe/zahnschutz/antrag-exklusiv?cm_mmc=onlineVersicherungsVergleichGmbh)

Zugeordnete Tarife:

- [Deutsche Familienversicherung: DFV ZahnSchutz Exklusiv 100](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/dfv-zahnschutz-exclusiv-100/)
- [Deutsche Familienversicherung: ZahnSchutz Exklusiv 100](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/zahnschutz-exklusiv-100/)
- [MAXCARE: DFV ZahnSchutz früher MAXCARE Exklusiv](https://www.test-zahnzusatzversicherung.de/anbieter/maxcare/maxcare-dfv-zahnschutz-exclusiv-100/)

## 12. Deutsche Familienversicherung / MAXCARE — 3 Tarife

[Onlineabschluss öffnen](https://makler.deutsche-familienversicherung.de/partner/iframe/zahnschutz/antrag-premium?cm_mmc=onlineVersicherungsVergleichGmbh)

Zugeordnete Tarife:

- [Deutsche Familienversicherung: DFV ZahnSchutz Premium 90](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/dfv-zahnschutz-premium-90/)
- [Deutsche Familienversicherung: ZahnSchutz Premium 90](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/zahnschutz-premium-90/)
- [MAXCARE: DFV ZahnSchutz früher MAXCARE Premium](https://www.test-zahnzusatzversicherung.de/anbieter/maxcare/maxcare-dfv-zahnschutz-premium-90/)

## 13. Deutsche Familienversicherung — 2 Tarife

[Onlineabschluss öffnen](https://makler.deutsche-familienversicherung.de/partner/iframe/zahnschutz/antrag-premium-80/?cm_mmc=onlineVersicherungsVergleichGmbh)

Zugeordnete Tarife:

- [DFV ZahnSchutz Premium 80](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/dfv-zahnschutz-premium-80/)
- [ZahnSchutz Premium 80](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/zahnschutz-premium-80/)

## 14. Deutsche Familienversicherung — 2 Tarife

[Onlineabschluss öffnen](https://makler.deutsche-familienversicherung.de/partner/iframe/zahnschutz/antrag-komfort?cm_mmc=onlineVersicherungsVergleichGmbh)

Zugeordnete Tarife:

- [DFV ZahnSchutz Komfort 70](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/dfv-zahnschutz-komfort-70/)
- [ZahnSchutz Komfort 70](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/zahnschutz-komfort-70/)

## 15. Deutsche Familienversicherung — 1 Tarif

[Onlineabschluss öffnen](https://makler.deutsche-familienversicherung.de/partner/iframe/zahnschutz/antrag-basis?cm_mmc=onlineVersicherungsVergleichGmbh)

Zugeordnete Tarife:

- [ZahnSchutz Basis 50](https://www.test-zahnzusatzversicherung.de/anbieter/deutsche-familienversicherung/dfv-zahnschutz-basis-50/)

## 16. Die Bayerische — 11 Tarife

[Onlineabschluss öffnen](https://www.diebayerische.de/diebayerische/online-berechnen/zahnzusatzversicherung-berechnen?m=162615)

Zugeordnete Tarife:

- [Die Bayerische ZAHN Sofort + ZAHN Smart](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/die-bayerische-zahn-sofort-zahn-smart/)
- [ZAHN Komfort Regionalklasse 1](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-komfort-2023-regionalklasse-1/)
- [ZAHN Komfort Regionalklasse 2](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-komfort-2023-regionalklasse-2/)
- [ZAHN Prestige Regionalklasse 1](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-prestige-2023-regionalklasse-1/)
- [ZAHN Prestige Regionalklasse 2](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-prestige-2023-regionalklasse-2/)
- [ZAHN Smart](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-smart-2023/)
- [ZAHN Sofort + ZAHN Komfort Regionalklasse 1](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-sofort-zahn-komfort-2023-regionalklasse-1/)
- [ZAHN Sofort + ZAHN Komfort Regionalklasse 2](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-sofort-zahn-komfort-2023-regionalklasse-2/)
- [ZAHN Sofort + ZAHN Prestige Regionalklasse 1](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-sofort-zahn-prestige-2023-regionalklasse-1/)
- [ZAHN Sofort + ZAHN Prestige Regionalklasse 2](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-sofort-zahn-prestige-2023-regionalklasse-2/)
- [ZAHN Sofort + ZAHN Smart](https://www.test-zahnzusatzversicherung.de/anbieter/die-bayerische/zahn-sofort-zahn-smart-2023/)

## 17. DKV — 1 Tarif

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/OnlineAbschluss/process/1302076/KDBP-KDTK85)

Zugeordnete Tarife:

- [KDTK85+KDBP](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/dkv-kdtk85-kdbp/)

## 18. DKV — 1 Tarif

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/OnlineAbschluss/process/1302076/KDT)

Zugeordnete Tarife:

- [KombiMed KDT](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/dkv-kdt/)

## 19. DKV — 1 Tarif

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/tarifrechner/1302076/Z100)

Zugeordnete Tarife:

- [KombiMed Zahn Z100](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/kombimed-zahn-z100/)

## 20. DKV — 1 Tarif

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/tarifrechner/1302076/Z80)

Zugeordnete Tarife:

- [KombiMed Zahn Z80](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/kombimed-zahn-z80/)

## 21. DKV — 1 Tarif

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/tarifrechner/1302076/Z100-PLS)

Zugeordnete Tarife:

- [KombiMed Zahn Z100 + PLS](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/kombimed-zahn-z100-pls/)

## 22. DKV — 1 Tarif

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/tarifrechner/1302076/Z90)

Zugeordnete Tarife:

- [KombiMed Zahn Z90](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/kombimed-zahn-z90/)

## 23. DKV — 1 Tarif

[Onlineabschluss öffnen](https://www.beitragsrechner.dkv.com/tarifrechner/1302076/Z90-PLS)

Zugeordnete Tarife:

- [KombiMed Zahn Z90 + PLS](https://www.test-zahnzusatzversicherung.de/anbieter/dkv/kombimed-zahn-z90-pls/)

## 24. ERGO — 1 Tarif

[Onlineabschluss öffnen](https://i.ergo.de/?wmid=528355711734779904)

Zugeordnete Tarife:

- [KFO-Sofort-Schutz](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/ergo-kfo-sofort/)

## 25. ERGO — 1 Tarif

[Onlineabschluss öffnen](https://i.ergo.de/?wmid=190930613)

Zugeordnete Tarife:

- [ZZP](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/ergo-direkt-versicherungen-zzp/)

## 26. ERGO — 1 Tarif

[Onlineabschluss öffnen](https://www.financeads.net/tc.php?t=53926C36041741T)

Zugeordnete Tarife:

- [ZEF](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/ergo-direkt-versicherungen-zef/)

## 27. ERGO — 2 Tarife

[Onlineabschluss öffnen](https://i.ergo.de/?wmid=398333143)

Zugeordnete Tarife:

- [Dental-Vorsorge-Premium](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-vorsorge-premium/)
- [Dental-Vorsorge](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-vorsorge/)

## 28. ERGO — 9 Tarife

[Onlineabschluss öffnen](https://i.ergo.de/?wmid=790012563046797312)

Zugeordnete Tarife:

- [Dental-Schutz 90 + Dental-Vorsorge](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-90-dental-vorsorge/)
- [Dental-Schutz 90](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-90/)
- [Dental-Schutz 75 + Vorsorge-Premium](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-75-dental-vorsorge-premium/)
- [Dental-Schutz 75 + Dental-Vorsorge](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-75-dental-vorsorge/)
- [Dental-Schutz 75](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-75/)
- [Dental-Schutz 100 + Vorsorge-Premium](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-100-dental-vorsorge-premium/)
- [Dental-Schutz 100](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-100/)
- [Dental-Schutz 100 + Dental-Vorsorge](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-100-dental-vorsorge/)
- [Dental-Schutz 90 + Vorsorge-Premium](https://www.test-zahnzusatzversicherung.de/anbieter/ergo/dental-schutz-90-dental-vorsorge-premium/)

## 29. Getsafe — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/vergleich/dental-100/online-antrag-getsafe/)

Zugeordnete Tarife:

- [Dental 100](https://www.test-zahnzusatzversicherung.de/anbieter/getsafe/dental-100/)

## 30. Getsafe — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/vergleich/dental-75/online-antrag-getsafe/)

Zugeordnete Tarife:

- [Dental 75](https://www.test-zahnzusatzversicherung.de/anbieter/getsafe/dental-75/)

## 31. Getsafe — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/vergleich/dental-90/online-antrag-getsafe/)

Zugeordnete Tarife:

- [Dental 90](https://www.test-zahnzusatzversicherung.de/anbieter/getsafe/dental-90/)

## 32. Gothaer — 2 Tarife

[Onlineabschluss öffnen](https://koop.gothaer.de/makleronlineversicherungsvergleich/privatkunden/krankenzusatzversicherung/zahnzusatzversicherung/medizduo-rechner.htm)

Zugeordnete Tarife:

- [MediZ Smile 85](https://www.test-zahnzusatzversicherung.de/anbieter/gothaer/gothaer-mediz-smile-85/)
- [MediZ Smile 75](https://www.test-zahnzusatzversicherung.de/anbieter/gothaer/gothaer-mediz-smile-75/)

## 33. Hallesche — 7 Tarife

[Onlineabschluss öffnen](https://www.vermittlerportal.de/appserver/b2c/ZahnZusatz/?PID=ZZ_V%2COM_LG%2COM_NOBP%2CZZ_HIDEV&VMNR=559952&VMMAIL=info%40test-zahnzusatzversicherung.de)

Zugeordnete Tarife:

- [dentZE.90+dentZB.100](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-ze90-zb100/)
- [dentZE.100+dentZB.100](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-dent-zb100-ze100/)
- [dentZE.90](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-ze90/)
- [dentZE.100](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-dent-ze100/)
- [dentZE.90+dentPRO.80](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-ze90-pro80/)
- [dentZE.100+dentPRO.80](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-dent-ze100-pro80/)
- [dentZB.100](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-dent-zb100/)

## 34. Hallesche — 1 Tarif

[Onlineabschluss öffnen](https://www.vermittlerportal.de/appserver/b2c/ZahnZusatz/?PID=ZZ_V%2COM_LG%2CZZ_MEGA%2COM_NOBP%2CZZ_HIDEV&VMNR=559952&VMMAIL=info%40test-zahnzusatzversicherung.de)

Zugeordnete Tarife:

- [MEGA.Dent](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-mega-dent/)

## 35. Hallesche — 1 Tarif

[Onlineabschluss öffnen](https://www.vermittlerportal.de/appserver/b2c/ZahnZusatz/?PID=ZZ_V%2COM_LG%2CZZ_GIGA%2COM_NOBP%2CZZ_HIDEV&VMNR=559952&VMMAIL=info%40test-zahnzusatzversicherung.de)

Zugeordnete Tarife:

- [GIGA.Dent](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-giga-dent/)

## 36. Hallesche — 1 Tarif

[Onlineabschluss öffnen](https://www.vermittlerportal.de/appserver/b2c/ZahnZusatz/?PID=ZZ_V,ZZ_HIDETARIF&VMNR=559952&VMMAIL=info%40test-zahnzusatzversicherung.de)

Zugeordnete Tarife:

- [SMART.Dent](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-smart-dent/)

## 37. Hallesche — 2 Tarife

[Onlineabschluss öffnen](https://www.vermittlerportal.de/appserver/b2c/ZahnZusatz/?PID=ZZ_V%2COM_LG%2CZZ_PLUSZ%2COM_NOBP%2CZZ_HIDEV&VMNR=559952&VMMAIL=info%40test-zahnzusatzversicherung.de)

Zugeordnete Tarife:

- [plusZ+dentPRO.80 (Easy.dent)](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-plusz-pro80/)
- [plusZ](https://www.test-zahnzusatzversicherung.de/anbieter/hallesche/hallesche-plusz/)

## 38. HanseMerkur — 5 Tarife

[Onlineabschluss öffnen](https://secure2.hansemerkur.de/ola-ui/1/100?adnr=4161618)

Zugeordnete Tarife:

- [EZ+EZT](https://www.test-zahnzusatzversicherung.de/anbieter/hansemerkur/hansemerkur-ezezt/)
- [EZ+EZT+EZP](https://www.test-zahnzusatzversicherung.de/anbieter/hansemerkur/hansemerkur-ezeztezp/)
- [EZ+EZE](https://www.test-zahnzusatzversicherung.de/anbieter/hansemerkur/hansemerkur-ez-eze/)
- [Zahnzusatz Basis plus Prophylaxe](https://www.test-zahnzusatzversicherung.de/anbieter/hansemerkur/hansemerkur-ez-eze-ezp/)
- [EZ](https://www.test-zahnzusatzversicherung.de/anbieter/hansemerkur/hansemerkur-ez/)

## 39. HanseMerkur — 1 Tarif

[Onlineabschluss öffnen](https://secure2.hansemerkur.de/ola-ui/1/110?adnr=4161618&etpn=Zahnvorsorgeversicherung&etsc=PFsU6m)

Zugeordnete Tarife:

- [EZP](https://www.test-zahnzusatzversicherung.de/anbieter/hansemerkur/hansemerkur-ezp/)

## 40. INTER — 5 Tarife

[Onlineabschluss öffnen](https://www.inter.de/gesundheit/zahnzusatzversicherung/onlineabschluss/?vermnr=687640&vermemail=info@test-zahnzusatzversicherung.de)

Zugeordnete Tarife:

- [QualiMed Z Z90Plus](https://www.test-zahnzusatzversicherung.de/anbieter/inter/inter-qualimedz-z90plus/)
- [QualiMed Z 90pro | DE vor Auswanderung CH](https://www.test-zahnzusatzversicherung.de/anbieter/inter/inter-qualimedz-z90zpro2/)
- [QualiMed Z Z80](https://www.test-zahnzusatzversicherung.de/anbieter/inter/inter-qualimedz-z80/)
- [QualiMed Z Z90](https://www.test-zahnzusatzversicherung.de/anbieter/inter/inter-qualimedz-z90/)
- [Z70](https://www.test-zahnzusatzversicherung.de/anbieter/inter/inter-qualimedz-z70/)

## 41. Janitos — 2 Tarife

[Onlineabschluss öffnen](https://onlinetarifrechner.janitos.she.de/kzv/?a=xsmqscgsyrcee)

Zugeordnete Tarife:

- [dental plus](https://www.test-zahnzusatzversicherung.de/anbieter/janitos/janitos-dental-plus/)
- [dental max](https://www.test-zahnzusatzversicherung.de/anbieter/janitos/janitos-dental-max/)

## 42. LKH Landeskrankenhilfe — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/online-antrag/lkh70l/)

Zugeordnete Tarife:

- [ZahnUpgrade 70+L](https://www.test-zahnzusatzversicherung.de/anbieter/lkh-landeskrankenhilfe/zu70-plus-l/)

## 43. LKH Landeskrankenhilfe — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/online-antrag/lkh90/)

Zugeordnete Tarife:

- [ZahnUpgrade 90+](https://www.test-zahnzusatzversicherung.de/anbieter/lkh-landeskrankenhilfe/zu90-plus/)

## 44. LKH Landeskrankenhilfe — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/online-antrag/lkh70/)

Zugeordnete Tarife:

- [ZahnUpgrade 70+](https://www.test-zahnzusatzversicherung.de/anbieter/lkh-landeskrankenhilfe/zu70-plus/)

## 45. LKH Landeskrankenhilfe — 1 Tarif

[Onlineabschluss öffnen](https://antrag.lkh.de/?tarif=ZU90_PLUS_L&vermittlerId=725735)

Zugeordnete Tarife:

- [ZahnUpgrade 50](https://www.test-zahnzusatzversicherung.de/anbieter/lkh-landeskrankenhilfe/zu50/)

## 46. LKH Landeskrankenhilfe — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/online-antrag/lkh90l/)

Zugeordnete Tarife:

- [ZahnUpgrade 90+L](https://www.test-zahnzusatzversicherung.de/anbieter/lkh-landeskrankenhilfe/zu90-plus-l/)

## 47. MAXCARE — 2 Tarife

[Onlineabschluss öffnen](https://www.financeads.net/tc.php?t=53926C236142535T)

Zugeordnete Tarife:

- [DFV ZahnSchutz früher MAXCARE Basis](https://www.test-zahnzusatzversicherung.de/anbieter/maxcare/maxcare-dfv-zahnschutz-basis-30/)
- [DFV ZahnSchutz früher MAXCARE Komfort](https://www.test-zahnzusatzversicherung.de/anbieter/maxcare/maxcare-dfv-zahnschutz-komfort-60/)

## 48. MAXCARE / Münchener Verein — 6 Tarife

[Onlineabschluss öffnen](https://www.muenchener-verein.de/J-MVP-Redirect/spring/mvp-redirect?accessParam=8LT77ytIy2tHz0z0FVIptEBwScbw0UdK1kEDjk5GjFQcWPgkgmu5vA==)

Zugeordnete Tarife:

- [MAXCARE: Exklusiv | ZahnGesund 100](https://www.test-zahnzusatzversicherung.de/anbieter/maxcare/maxcare-exklusiv/)
- [MAXCARE: Premium | ZahnGesund 85+](https://www.test-zahnzusatzversicherung.de/anbieter/maxcare/maxcare-premium/)
- [MAXCARE: Komfort | ZahnGesund 75+](https://www.test-zahnzusatzversicherung.de/anbieter/maxcare/maxcare-komfort/)
- [Münchener Verein: ZahnGesund 100](https://www.test-zahnzusatzversicherung.de/anbieter/muenchener-verein/muenchener-verein-zahngesund-100/)
- [Münchener Verein: ZahnGesund 75+](https://www.test-zahnzusatzversicherung.de/anbieter/muenchener-verein/muenchener-verein-zahngesund-75/)
- [Münchener Verein: ZahnGesund 85+](https://www.test-zahnzusatzversicherung.de/anbieter/muenchener-verein/muenchener-verein-zahngesund-85/)

## 49. Nürnberger — 3 Tarife

[Onlineabschluss öffnen](https://www.nuernberger.de/beitragsrechner/zahnzusatz/?agNr=z0agKsl_jkQj5WX33crROw==)

Zugeordnete Tarife:

- [Komfort 100 / Z100](https://www.test-zahnzusatzversicherung.de/anbieter/nuernberger/nuernberger-z100-komfort-100/)
- [Komfort 90 / Z90](https://www.test-zahnzusatzversicherung.de/anbieter/nuernberger/nuernberger-z90-komfort-90/)
- [Komfort 80 / Z80](https://www.test-zahnzusatzversicherung.de/anbieter/nuernberger/nuernberger-z80-komfort-80/)

## 50. ottonova — 13 Tarife

[Onlineabschluss öffnen](https://b2b.ottonova.de/b2b/dental-signup?brokerId=0050%2F00001)

Zugeordnete Tarife:

- [Zahn 90 plus](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn90-plus/)
- [Zahn 70 plus](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn70-plus/)
- [Zahn 90 Business](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn90-business/)
- [Zahn 70 Economy](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn70-economy/)
- [Zahn 100 First Class](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn100-first-class/)
- [Zahn 85 plus](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn85-plus/)
- [Zahn 75 plus](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn75-plus/)
- [Zahn 100 plus](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn100-plus/)
- [Zahn 75 Economy](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn75-economy/)
- [Zahn 85 Business](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/zahn85-business/)
- [Zahn 100 First Class (geschlossen)](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/ottonova-zahn100-first-class/)
- [Zahn 70 Economy Class](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/ottonova-zahn70-economy-class/)
- [Zahn 85 Business Class](https://www.test-zahnzusatzversicherung.de/anbieter/ottonova/ottonova-zahn85-business-class/)

## 51. SDK — 7 Tarife

[Onlineabschluss öffnen](https://insurances-online.levelnine.biz/?mandant=sdk&tarifftypes=Zahn&agentId1=903212&agentId2=&insurers=36&tariffs=&customValues=e30=&contactInformation=eyJmaXJzdE5hbWUiOiJPbmxpbmUiLCJsYXN0TmFtZSI6IlZlcnNpY2hlcnVuZ3NWZXJnbGVpY2ggR21iSCIsImNvbXBhbnkiOiIiLCJzdHJlZXQiOiJSb3NlbmhlaW1lciBMYW5kc3RyLiAzNSIsInppcGNvZGUiOiI4NTUyMSIsImNpdHkiOiJPdHRvYnJ1bm4iLCJwaG9uZSI6IjA4OSA0MDI4NzI3MiIsIm1vYmlsZSI6IiIsImVtYWlsIjoiaW5mb0B0ZXN0LXphaG56dXNhdHp2ZXJzaWNoZXJ1bmcuZGUifQ==&remarks=IkJlaSBGcmFnZW4gc2luZCB3aXIgZ2VybmUgZvxyIFNpZSBkYS4i&defaultContact=false&employeeInsurance=NOT_BKV)

Zugeordnete Tarife:

- [Zahn 100 | ZP1](https://www.test-zahnzusatzversicherung.de/anbieter/sdk/sdk-zahn-100/)
- [Zahn 70 | ZP7](https://www.test-zahnzusatzversicherung.de/anbieter/sdk/sdk-zahn-70/)
- [Zahn 90 | ZP9](https://www.test-zahnzusatzversicherung.de/anbieter/sdk/sdk-zahn-90/)
- [Zahn 50 | ZP5](https://www.test-zahnzusatzversicherung.de/anbieter/sdk/sdk-zahn-50/)
- [Zahn 70 | ZP7 Schweiz](https://www.test-zahnzusatzversicherung.de/anbieter/sdk/sdk-schweiz-70/)
- [Zahn100 | ZP1 Schweiz](https://www.test-zahnzusatzversicherung.de/anbieter/sdk/sdk-schweiz-100/)
- [Zahn90 | ZP9 Schweiz](https://www.test-zahnzusatzversicherung.de/anbieter/sdk/sdk-schweiz-90/)

## 52. Signal Iduna — 6 Tarife

[Onlineabschluss öffnen](https://url.signal-iduna.de/redir/zahn.html?advnr=3093810)

Zugeordnete Tarife:

- [ZahnTOPpur](https://www.test-zahnzusatzversicherung.de/anbieter/signal-iduna/signal-zahntop-pur/)
- [ZahnTOP](https://www.test-zahnzusatzversicherung.de/anbieter/signal-iduna/signal-zahntop/)
- [ZahnPLUSpur](https://www.test-zahnzusatzversicherung.de/anbieter/signal-iduna/signal-zahnplus-pur/)
- [ZahnPLUS](https://www.test-zahnzusatzversicherung.de/anbieter/signal-iduna/signal-zahnplus/)
- [ZahnBasispur](https://www.test-zahnzusatzversicherung.de/anbieter/signal-iduna/signal-zahnbasis-pur/)
- [ZahnEXKLUSIVpur](https://www.test-zahnzusatzversicherung.de/anbieter/signal-iduna/signal-zahnexklusiv-pur/)

## 53. Signal Iduna — 1 Tarif

[Onlineabschluss öffnen](https://url.signal-iduna.de/redir/ambulant-d.html?advnr=3093810)

Zugeordnete Tarife:

- [AmbulantPLUSpur](https://www.test-zahnzusatzversicherung.de/anbieter/signal-iduna/signal-ambulantplus-pur/)

## 54. Union Krankenversicherung — 1 Tarif

[Onlineabschluss öffnen](https://www.ukv.de/KVEinfachWeb/servlet/NaturPRIVAT?Mandant=cmsukv&Style=CMS_neu&VERM_ID=180191331&ADE_ID=01638108)

Zugeordnete Tarife:

- [NaturPRIVAT](https://www.test-zahnzusatzversicherung.de/anbieter/ukv/ukvbbkk-naturprivat/)

## 55. Union Krankenversicherung — 1 Tarif

[Onlineabschluss öffnen](https://www.ukv.de/KVEinfachWeb/servlet/VorsorgePRIVAT?Mandant=cmsukv&Style=CMS_neu&VERM_ID=180191331&ADE_ID=01638108)

Zugeordnete Tarife:

- [VorsorgePRIVAT](https://www.test-zahnzusatzversicherung.de/anbieter/ukv/ukvbbkk-vorsorgeprivat/)

## 56. Union Krankenversicherung — 1 Tarif

[Onlineabschluss öffnen](https://tinyurl.com/5v283h6w)

Zugeordnete Tarife:

- [ZahnPrivat 75](https://www.test-zahnzusatzversicherung.de/anbieter/ukv/zahnprivat-75/)

## 57. Union Krankenversicherung — 1 Tarif

[Onlineabschluss öffnen](https://tinyurl.com/n4mcszs2)

Zugeordnete Tarife:

- [ZahnPrivat 90](https://www.test-zahnzusatzversicherung.de/anbieter/ukv/zahnprivat-90/)

## 58. Union Krankenversicherung — 1 Tarif

[Onlineabschluss öffnen](https://tinyurl.com/2f4ssf5c)

Zugeordnete Tarife:

- [ZahnPrivat 100](https://www.test-zahnzusatzversicherung.de/anbieter/ukv/zahnprivat-100/)

## 59. Universa — 3 Tarife

[Onlineabschluss öffnen](https://onlineabschluss.universa.de/zahnzusatz?kk=XH5yYzQ4Nj4SMCpUa2VCMCwnOjksHw%3d%3d)

Zugeordnete Tarife:

- [uni-dent|Top 100](https://www.test-zahnzusatzversicherung.de/anbieter/universa/uni-denttop100/)
- [uni-dent|Top 75](https://www.test-zahnzusatzversicherung.de/anbieter/universa/uni-denttop75/)
- [uni-dent|Top 90](https://www.test-zahnzusatzversicherung.de/anbieter/universa/uni-denttop90/)

## 60. Vigo — 1 Tarif

[Onlineabschluss öffnen](https://www.test-zahnzusatzversicherung.de/online-antrag/vigo-zahnvorsorge-premium/)

Zugeordnete Tarife:

- [vigo 4YOU Zahnvorsorge Premium](https://www.test-zahnzusatzversicherung.de/anbieter/vigo-krankenversicherung/vigo-4you-zahnvorsorge-premium/)

## 61. Württembergische — 3 Tarife

[Onlineabschluss öffnen](https://www.wuerttembergische.de/gesundheit/zahnzusatzversicherung/abschluss/?channel=Makler&vnr=0821-2148-0)

Zugeordnete Tarife:

- [Zahnersatz90 + Zahnbehandlung](https://www.test-zahnzusatzversicherung.de/anbieter/wuerttembergische/wuerttembergische-zahnersatz-90-zahnbehandlung/)
- [Zahnersatz100 + ZahnbehandungPlus](https://www.test-zahnzusatzversicherung.de/anbieter/wuerttembergische/wuerttembergische-zahnersatz-100-zahnbehandlung-plus/)
- [Zahnersatz75 + Zahnbehandlung](https://www.test-zahnzusatzversicherung.de/anbieter/wuerttembergische/wuerttembergische-zahnersatz-75-zahnbehandlung/)


