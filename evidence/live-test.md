# Live-Tests im privaten System des Autors

Stand: 23.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> «V1.0/V1.1» sind frühere Fassungen des Workflows im privaten System, «V1.2» die Fassung mit dem neuen Zweig «Termin ändern», «V1.3» die Fassung dieser Demo. Protokoll des Autors zu Tests im eigenen n8n mit eigenem Telegram-Bot und eigenem Google-Kalender (Terminname «Test Besprechung»). **Es gibt dafür keine öffentlichen Nachweise** (Bildschirmfotos gehören nicht in dieses Repository). In dieser Demo wurde nichts ausgeführt.

| Zeit (23.11.2026) | Fassung | Nachricht | Ergebnis |
|---|---|---|---|
| 15:30 | Vorgängerfassung | «Morgen um 10 Uhr Test Besprechung» | Antwort «✓ Eingetragen: Test Besprechung, 24.11.2026 10:00»; Termin im Kalender |
| 15:30–15:44 | Vorgängerfassungen | «Test Besprechung auf 14 Uhr verschieben» (mehrere Versuche) | Node `Calendar API — Update Event`: Google-Antwort 400 «Bad Request» (ohne weitere Angabe); Alarm des privaten Error-Workflows. Im Körper der Anfrage stand als Start der heutige Tag statt des Tags des Termins |
| 15:51 | V1.2 | «Test Besprechung auf 14 Uhr verschieben» | Antwort «✓ Geändert: Test Besprechung, 24.11.2026 14:00–15:00»; der Termin steht im Kalender um 14:00 |
| 15:52 | V1.2 | «Zahnarzt auf Freitag verschieben» | Antwort «Termin «Zahnarzt» nicht gefunden. Es wurde nichts geändert.» |
| 16:03 | V1.2 | «Morgen um 10 Uhr Test Besprechung» (ohne Dauer) | **Fehler** im Node `Calendar — Create Event`: Google-Antwort 400 «Bad Request». Die Eingabe des Nodes zeigte `end` leer: Das Modell hatte kein Ende geliefert. Keine Antwort im Chat; Alarm des privaten Error-Workflows |
| 16:05 | V1.2 | «Was steht morgen an?» | Antwort auf Deutsch: Datum, «14:00 Test Besprechung», ein ganztägiger Termin |
| 16:05 | V1.2 | «Was steht am 31. Dezember an?» | **keine Antwort**; die Ausführung in n8n lief als erfolgreich durch |
| 16:12 | V1.3 | «Morgen um 10 Uhr Test Besprechung» (ohne Dauer) | Antwort «✓ Eingetragen: Test Besprechung, 24.11.2026 10:00»; Termin im Kalender |
| 16:12 | V1.3 | «Was steht am 31. Dezember an?» | Antwort «Keine Termine im angefragten Zeitraum.» |
| 16:22 | V1.3 | «Was steht morgen an?» | Antwort auf Deutsch, chronologisch: 10:00 «Test Besprechung», 14:00 «Test Besprechung», ganztägiger Termin |
| 16:13 | V1.3 | «Test Besprechung auf 14 Uhr verschieben» (zwei Termine «Test Besprechung» im Kalender: 10:00 und 14:00) | Antwort «Mehrere Termine passen. Welchen meinen Sie? Es wurde nichts geändert.» mit beiden Terminen; nichts geändert |

## Was daraus folgt

- Mit V1.3 bestanden: Anlegen ohne Dauer (M01), Anzeigen mit Terminen (M03) und ohne Termine (M05), mehrere Treffer beim Ändern (M10). Dabei antwortete der Bot dem eigenen Konto; der Absenderfilter war aktiv.
- Mit V1.2 bestanden: Ändern (M06), «nicht gefunden» (M09). V1.3 ändert an Ändern und «nicht gefunden» nur die Wiederholungs-Einstellungen und den Namen des Meldungs-Nodes; mit V1.3 selbst wurde der Zweig «Termin ändern» nur im Fall «mehrere Treffer» ausgeführt.
- **Bestätigt (nicht mehr nur vermutet):** Die Vorgängerfassung V1.2 scheiterte beim Anlegen ohne Dauer an einem leeren Ende (E4) und schwieg bei einem Zeitraum ohne Termine (E6). Beide Fälle behebt V1.3.
- Die Ursache des früheren Fehlers 400 beim Ändern ist nicht abschliessend belegt; mutmasslich bestimmte das Modell Datum und Ende selbst (E5).
- Alle übrigen Fälle, darunter die Abweisung fremder Konten (M15), sind offen ([`docs/test-plan.md`](../docs/test-plan.md)).
