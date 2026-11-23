# Testplan

> **Eigenprojekt / Demo, kein Kundenauftrag.** Stand: 23.11.2026. **Lokaler Import ≠ Funktionstest der Integrationen.**

Es gibt zwei Arten von Tests mit unterschiedlicher Aussage:

- **Teil A – Logiktest** (wiederholbar, ohne Konten): lässt die Nodes von Absenderfilter, Anlegen, Anzeigen und Ändern in einem isolierten n8n laufen; Kalender, Modell und Telegram sind durch feste Beispieldaten ersetzt.
- **Teil B – Testfälle mit den echten Diensten** (M01–M15): Nachrichten an den Bot in einem eigenen System. Die Status-Spalte «Live (Autor)» sind Angaben aus dem privaten System des Autors; **öffentliche Nachweise gibt es dafür nicht**. In dieser Demo wurde Teil B **nicht** ausgeführt.

## Teil A – Logiktest (PASS, 33 von 33)

Aufruf: `bash tests/logic-harness/run.sh` (Docker, Image `n8nio/n8n:2.43.7`). Je Szenario wird geprüft: Art des Ergebnisses, Antworttext, ob eine Anfrage an Google ausgelöst wird und – beim Anlegen und Ändern – Start, Ende und Zeitzone (beim Ändern wird der Körper der Anfrage als JSON gelesen; Ende vor Start oder leere Zeit lässt den Test fehlschlagen). Einzelheiten: [`evidence/logic-test.md`](../evidence/logic-test.md).

### Absenderfilter (erlaubte ID im Test: eine erfundene)

| ID | Szenario | Erwartung | Status |
|---|---|---|---|
| F1 | Nachricht der erlaubten ID | läuft weiter | PASS |
| F2 | Nachricht einer anderen ID | still ignoriert | PASS |
| F3 | Nachricht ohne Absender | still ignoriert | PASS |

### Anlegen

| ID | Szenario (Eingaben des Modells) | Erwartung | Status |
|---|---|---|---|
| C01 | Start gültig, Ende leer | Ende = Start + 60 Minuten: 10:00–11:00 | PASS |
| C02 | Start und Ende gültig | Ende bleibt: 10:00–11:30 | PASS |
| C03 | Ende vor dem Start | Ende = Start + 60 Minuten | PASS |
| C04 | Start leer | «Zeit nicht erkannt. Es wurde nichts angelegt.», nichts angelegt | PASS |
| C05 | Start ungültig («morgen») | wie C04 | PASS |
| C06 | Start ohne Offset | wird als `Europe/Zurich` gelesen: Offset +01:00 | PASS |
| C07 | Termin in der Sommerzeit | Offset +02:00 | PASS |
| C08 | Start leer, Sprache Russisch | russische Meldung | PASS |
| C09 | Start leer, Sprache Englisch | englische Meldung | PASS |
| C10 | Start gültig, Ende leer, Sprache Englisch | «✓ Added: …», 15:00–16:00 | PASS |

### Anzeigen

| ID | Szenario | Erwartung | Status |
|---|---|---|---|
| R01 | drei Termine | alle drei gehen an die Zusammenfassung | PASS |
| R02 | keine Termine | «Keine Termine im angefragten Zeitraum.», keine Zusammenfassung | PASS |
| R03 | keine Termine, Sprache Russisch | russische Meldung | PASS |
| R04 | keine Termine, Sprache Englisch | englische Meldung | PASS |
| R05 | nur Einträge ohne Termin-ID | wie R02 | PASS |

### Ändern

| ID | Szenario (Eingaben des Modells) | Erwartung | Status |
|---|---|---|---|
| U01 | nur neue Uhrzeit 14:00 | Datum und Dauer des Termins bleiben: 24.11. 14:00–15:00 | PASS |
| U02 | nur neues Datum | Uhrzeit und Dauer bleiben: 25.11. 10:00–11:00 | PASS |
| U03 | Datum, Uhrzeit und Dauer 45 Minuten | 26.11. 09:30–10:15 | PASS |
| U04 | nur neue Dauer 30 Minuten | 24.11. 10:00–10:30 | PASS |
| U05 | nichts erkannt | «Neue Zeit nicht erkannt», keine Änderung | PASS |
| U06 | ungültige Uhrzeit («vierzehn») | «Neue Zeit nicht erkannt», keine Änderung | PASS |
| U07 | ganztägiger Termin | «Ganztägige Termine verschiebe ich nicht», keine Änderung | PASS |
| U08 | nichts erkannt, Sprache Russisch | russische Antwort, keine Änderung | PASS |
| U09 | Titel nicht vorhanden, Sprache Englisch | englische Antwort «not found», keine Änderung | PASS |
| U10 | zwei Termine passen | Antwort mit beiden Terminen, keine Änderung | PASS |
| U11 | zwei Termine passen, bisherige Startzeit bekannt | der Termin mit dieser Startzeit wird geändert; sein Datum (26.11.) bleibt | PASS |
| U12 | Titel in anderer Gross-/Kleinschreibung | Termin wird gefunden und geändert | PASS |
| U13 | Uhrzeit ohne führende Null («9:05») | 09:05–10:05 | PASS |
| U14 | Termin in der Sommerzeit | Offset +02:00 im Körper der Anfrage | PASS |
| U15 | leerer Kalender | «nicht gefunden», keine Änderung | PASS |

## Teil B – Testfälle mit den echten Diensten

Vorbereitung und Nachrichten: [`test-data/synthetic-messages.json`](../test-data/synthetic-messages.json). Nur mit Test-Kalender und eigenem Bot (E2). «V1.2» und «V1.3» bezeichnen Fassungen des Workflows im privaten System; **diese Demo entspricht V1.3**. Die Nachrichten des Autors weichen teils von den Kurzformen ab (Testtermin «Test Besprechung»).

| ID | Zweig | Nachricht (Kurzform) | Erwartung | Live (Autor, 23.11.2026) | Demo |
|---|---|---|---|---|---|
| M01 | Anlegen | «Morgen um 10 Uhr Besprechung mit Muster AG» (ohne Dauer) | Termin morgen 10:00, Antwort «✓ Eingetragen: …» | V1.2 FEHLGESCHLAGEN (16:03: Google 400, das Modell lieferte ein leeres Ende); V1.3 DOKUMENTIERT (16:12: «✓ Eingetragen: Test Besprechung, 24.11.2026 10:00», Termin im Kalender; die Dauer von 60 Minuten ist im Kalender nicht gesondert dokumentiert, siehe Logiktest C01) | NICHT GETESTET |
| M02 | Anlegen | «Add dentist appointment on Friday at 3 pm for 30 minutes» | 15:00–15:30, Antwort auf Englisch | offen | NICHT GETESTET |
| M03 | Anzeigen | «Was steht morgen an?» | Zusammenfassung auf Deutsch | V1.2 DOKUMENTIERT (16:05: Datum, «14:00 Test Besprechung», ganztägiger Termin); V1.3 DOKUMENTIERT (16:22: Zusammenfassung auf Deutsch, chronologisch: 10:00 und 14:00 «Test Besprechung», dann der ganztägige Termin) | NICHT GETESTET |
| M04 | Anzeigen | «Что у меня на этой неделе?» | Zusammenfassung auf Russisch | offen | NICHT GETESTET |
| M05 | Anzeigen | «Was steht am 31. Dezember an?» (Tag ohne Termine) | Meldung «Keine Termine im angefragten Zeitraum.» | V1.2 keine Antwort (16:05, Ausführung erfolgreich, Bot schwieg); V1.3 DOKUMENTIERT (16:12: Meldung kam) | NICHT GETESTET |
| M06 | Ändern | «Besprechung Muster AG auf 14 Uhr verschieben» | Datum bleibt, 14:00–15:00 | V1.2 DOKUMENTIERT (15:51: «✓ Geändert: Test Besprechung, 24.11.2026 14:00–15:00»; Kalender zeigt den Termin um 14:00) | NICHT GETESTET |
| M07 | Ändern | «… auf Mittwoch verschieben» | nur das Datum ändert sich | offen (Logiktest U02 PASS) | NICHT GETESTET |
| M08 | Ändern | «… auf 14 Uhr verschieben, 30 Minuten» | 14:00–14:30 | offen (Logiktest U03/U04 PASS) | NICHT GETESTET |
| M09 | Ändern | «Zahnarzt auf Freitag verschieben» | «nicht gefunden», keine Änderung | V1.2 DOKUMENTIERT (15:52: «Termin «Zahnarzt» nicht gefunden. Es wurde nichts geändert.») | NICHT GETESTET |
| M10 | Ändern | «Besprechung auf 14 Uhr verschieben» (zwei Treffer) | Liste, keine Änderung | V1.3 DOKUMENTIERT (16:13: zwei Termine «Test Besprechung» im Kalender, 10:00 und 14:00; Antwort «Mehrere Termine passen …» mit beiden, nichts geändert) | NICHT GETESTET |
| M11 | Ändern | «… um eine Stunde später» | «Neue Zeit nicht erkannt» | offen (Logiktest U05 PASS; Verhalten des Modells offen) | NICHT GETESTET |
| M12 | Ändern | «Betriebsferien auf 14 Uhr verschieben» (ganztägig) | «Ganztägige Termine verschiebe ich nicht» | offen (Logiktest U07 PASS) | NICHT GETESTET |
| M13 | Chat | «Wie spät ist es in Tokio?» | freie Antwort des Agenten (E3) | offen | NICHT GETESTET |
| M14 | Anzeigen | Test-Termin mit Anweisung im Titel | Titel wird genannt, Anweisung nicht befolgt | offen (Prompt Injection, siehe [SECURITY.md](../SECURITY.md)) | NICHT GETESTET |
| M15 | Absender | Nachricht von einem zweiten Telegram-Konto | keine Antwort (E1) | offen (Logiktest F2/F3 PASS; mit dem eigenen Konto antwortet der Bot, V1.3) | NICHT GETESTET |

«offen» heißt: im privaten System noch nicht mit dieser Fassung ausgeführt oder nicht protokolliert.

## Frühere Fassungen

- **Verschieben (V1.0/V1.1):** scheiterte im Node `Calendar API — Update Event` mit Google-Antwort 400 «Bad Request» (23.11.2026, mehrere Versuche zwischen 15:30 und 15:44). Im Körper der Anfrage stand als Start der heutige Tag statt des Tags des Termins. Mutmassliche Ursache: Datum und Ende kamen vom Modell. V1.2 berechnet beides im Code-Node; M06 ist mit V1.2 bestanden. Ob die Ursache damit abschliessend geklärt ist, ist nicht belegt.
- **Anlegen (V1.2):** scheiterte im Node `Calendar — Create Event` mit Google-Antwort 400 «Bad Request» (16:03). Die Eingabe des Nodes zeigte ein leeres `end` (das Modell hatte keine Dauer in der Nachricht und lieferte kein Ende); mit V1.1 hatte dieselbe Nachricht um 15:30 funktioniert, das Modell hatte damals ein Ende geliefert. V1.3 berechnet das Ende im Code (M01).
- **Anzeigen ohne Termine (V1.2):** keine Antwort. V1.3 antwortet (M05).
