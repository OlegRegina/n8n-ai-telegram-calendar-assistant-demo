# Telegram Calendar Assistant – Demo (n8n)

> **Eigenprojekt / Demo, kein Kundenauftrag.**
> Bereinigte Kopie eines privat betriebenen n8n-Workflows. Alle Testdaten sind synthetisch. Der Workflow in diesem Repository ist **inaktiv** und wurde in der Demo **nicht ausgeführt**.
> English version: [README.en.md](README.en.md)

## Was der Workflow macht

Man schreibt dem Telegram-Bot in normaler Sprache (Deutsch, Russisch oder Englisch). Ein Sprachmodell (OpenAI, `gpt-5.4-mini`) erkennt die Absicht; der Rest läuft regelbasiert in n8n.

0. **Absender prüfen:** `IF — Allowed Sender?` lässt nur Nachrichten der eingetragenen Telegram-Benutzer-ID durch; alle anderen werden still ignoriert (E1).
1. **Absicht erkennen:** `AI — Detect Intent` liefert strukturierte Daten: Absicht (`create_calendar_event`, `read_calendar`, `update_calendar_event`, `general_chat`), Titel, Zeiten, Sprache der Nachricht.
2. **Termin anlegen:** Ein Code-Node berechnet Start und Ende (Ende laut Modell, sonst Start + 60 Minuten); ohne erkennbaren Start wird nichts angelegt. Google Calendar legt den Termin an; Antwort im Chat, z. B. «✓ Eingetragen: Besprechung Muster AG, 24.11.2026 10:00».
3. **Termine anzeigen:** Google Calendar liest den Zeitraum. Ohne Termine antwortet der Bot «Keine Termine im angefragten Zeitraum.»; sonst werden die Termine gesammelt und vom Modell in der Sprache der Nachricht zusammengefasst.
4. **Termin ändern:** Die Termine der nächsten 30 Tage werden gelesen. Ein Code-Node sucht den Termin über den Titel (Teilstring, ohne Beachtung von Gross-/Kleinschreibung) und berechnet die neue Zeit aus dem gefundenen Termin: Das Modell liefert nur, was der Nutzer gesagt hat (neues Datum, neue Uhrzeit, neue Dauer); fehlende Angaben kommen vom Termin selbst. Nur bei **genau einem** Treffer und einer erkannten neuen Zeit wird der Termin über die Google-Calendar-API geändert («✓ Geändert: …»). Sonst antwortet der Bot und ändert nichts: nicht gefunden, mehrere Treffer, neue Zeit nicht erkannt, ganztägiger Termin.
5. **Allgemeiner Chat:** Alles andere beantwortet ein KI-Agent mit Gesprächsgedächtnis (ohne Zugriff auf den Kalender).

**Kein Freigabeschritt.** Anders als im [Inbox-Triage-Demo](https://github.com/OlegRegina/n8n-ai-inbox-triage-demo) gibt es hier keine Bestätigung vor dem Anlegen oder Ändern: Der Auftrag des Nutzers ist die Freigabe, der Assistent plant nichts von sich aus. Dafür gilt E1.

Ablauf und Node-Übersicht: [docs/architecture.md](docs/architecture.md).

## Inhalt

| Pfad | Inhalt |
|---|---|
| [`workflows/telegram-calendar-assistant.json`](workflows/telegram-calendar-assistant.json) | Workflow «Telegram Calendar Assistant (Demo)» (27 Nodes, 28 Verbindungen) |
| [`docs/setup.md`](docs/setup.md) | Einrichtung: Zugänge, Import, Test |
| [`docs/architecture.md`](docs/architecture.md) | Ablauf und Zuordnung aller Nodes |
| [`docs/test-plan.md`](docs/test-plan.md) | Testfälle mit Status |
| [`docs/datenschutz.md`](docs/datenschutz.md) | Datenflüsse und Datenschutzhinweise |
| [`test-data/`](test-data/) | Synthetische Testnachrichten |
| [`tests/logic-harness/`](tests/logic-harness/) | Wiederholbarer Logiktest (33 Szenarien, isoliertes n8n, Docker) |
| [`evidence/`](evidence/) | Prüfbericht, Importtest, Logiktest, Protokoll der Live-Tests |
| [`scripts/`](scripts/) | Bereinigung (`sanitize.py`) und Prüfung (`validate.py`) des Exports |
| [`SECURITY.md`](SECURITY.md) | Was entfernt wurde, Risiken, Meldung von Problemen |

## Import in Kürze

1. `workflows/telegram-calendar-assistant.json` in n8n importieren («Import from File»).
2. Zugänge verbinden: Telegram, Google Calendar (OAuth2), OpenAI.
3. **Eigene Telegram-Benutzer-ID** in `IF — Allowed Sender?` eintragen (Platzhalter `REPLACE_WITH_TELEGRAM_USER_ID`); ohne Eintrag antwortet der Bot niemandem.
4. Kalender prüfen: Der Wert `primary` bezeichnet den Hauptkalender des verbundenen Kontos.
5. Für Tests einen **eigenen Test-Kalender** und einen **eigenen Bot** verwenden und E2 beachten.

Details: [docs/setup.md](docs/setup.md). Der Workflow enthält genau einen Platzhalter (die Benutzer-ID).

## Status & Grenzen

### Stand der Prüfung (23.11.2026)

| Bereich | Status | Nachweis |
|---|---|---|
| Bereinigung des Exports: erlaubte Schlüssel, Musterprüfung, Struktur, nur genehmigte Änderungen | PASS laut automatischem Bericht; Datum, Anzahl geprüfter Dateien und Ergebnis stehen im Kopf des Berichts. Gilt nur für den damaligen Dateistand | [`evidence/validation-report.txt`](evidence/validation-report.txt), [`evidence/validation-notes.md`](evidence/validation-notes.md) |
| Lokaler Import in n8n 2.43.7 (isoliert, ohne Netzwerk): Struktur, Node-Parameter und Verbindungen unverändert | PASS | [`evidence/import-test.md`](evidence/import-test.md) |
| Logiktest mit Beispieldaten (33 Szenarien: Absenderfilter, Anlegen, Anzeigen, Ändern; echte Ausführung der Nodes in isoliertem n8n 2.43.7) | PASS, 33 von 33. Zeigt die Logik von Filter, Zeitberechnung, Suche und Antworttexten sowie dass Start und Ende der Google-Anfragen gültig sind (Ende nach Start, Zeitzone); **nicht** Google, Telegram oder das Modell | [`evidence/logic-test.md`](evidence/logic-test.md), [`tests/logic-harness/`](tests/logic-harness/) |
| Live-Tests im privaten System des Autors (23.11.2026) | DOKUMENTIERT, teilweise: Anlegen ohne Dauer, Anzeigen mit und ohne Termine und «mehrere Treffer» mit dieser Fassung bestanden; Ändern und «nicht gefunden» mit der Vorgängerfassung bestanden; übrige Fälle offen. Keine öffentlichen Nachweise | [`evidence/live-test.md`](evidence/live-test.md), [`docs/test-plan.md`](docs/test-plan.md) |
| Testfälle M01–M15 in dieser Demo (mit eigener Einrichtung) | NICHT GETESTET | [`docs/test-plan.md`](docs/test-plan.md) |
| Funktion der Integrationen Telegram, Google Calendar, OpenAI aus diesem Repository | NICHT GETESTET | – |

> **Lokaler Import ≠ Funktionstest der Integrationen.** Der Logiktest ersetzt Kalender, Modell und Telegram durch feste Beispieldaten.

### Bekannte Grenzen E1–E8

Gegenüber dem ursprünglichen privaten Workflow geändert wurden: der Absenderfilter (neu), das Anlegen (E4), das Anzeigen ohne Termine (E6), der Zweig «Termin ändern» (E5) und Wiederholungsversuche (E7); die Gründe stehen in [`evidence/live-test.md`](evidence/live-test.md). Die übrigen Grenzen bestehen fort.

**E1 – Absenderfilter nur über die Telegram-Benutzer-ID.** Der Telegram-Trigger selbst nimmt Nachrichten von **jedem** entgegen, der den Bot findet. `IF — Allowed Sender?` lässt nur die eingetragene Benutzer-ID weiter und ignoriert alle anderen still; solange der Platzhalter nicht ersetzt ist, antwortet der Bot niemandem. Die Prüfung beruht auf der Absender-ID, die Telegram in der Nachricht liefert. Im Logiktest weist der Filter fremde und fehlende Absender ab (F2, F3); im privaten System arbeitete der Bot nach Einführung des Filters für das eigene Konto; die Abweisung eines fremden Kontos ist live nicht geprüft (M15). Wer die Benutzer-ID eintragen darf, kann Termine lesen, anlegen und ändern.

**E2 – kein Freigabeschritt.** Anlegen und Ändern laufen ohne Rückfrage. Ein Missverständnis des Modells (falscher Tag, falscher Titel) wird sofort im Kalender wirksam; die Antwort im Chat nennt Titel und Zeit, damit es auffällt.

**E3 – freier Chat-Zweig.** Der Zweig «general_chat» ist ein KI-Agent **ohne Systemanweisung** (nur die Nachricht und das Gesprächsgedächtnis je Chat). Er hat keine Werkzeuge und keinen Kalenderzugriff, beantwortet aber beliebige Fragen auf Kosten des OpenAI-Kontos.

**E4 – Anlegen: Annahmen.** `Prepare — Event Times` übernimmt das Ende des Modells; fehlt es, ist es leer oder liegt es nicht nach dem Start, gilt Start + 60 Minuten; ohne erkennbaren Start wird nichts angelegt. Titel und Datum bestimmt weiterhin das Modell. Es gibt keine Konfliktprüfung mit bestehenden Terminen und keinen Schutz vor doppelten Terminen (dieselbe Nachricht zweimal legt zwei Termine an). Eine Vorgängerfassung übergab ein leeres Ende an Google und scheiterte mit HTTP 400 (live bestätigt, 23.11.2026, 16:03); mit dieser Fassung ist der Fall bestanden (16:12).

**E5 – Ändern: Umfang.** Gesucht wird nur in den nächsten 30 Tagen ab heute, über einen Teilstring des Titels. Bei mehreren Treffern ändert der Bot nichts und fragt nach; nur wenn das Modell die bisherige Startzeit liefert, wird darüber auf einen Termin eingegrenzt. Geändert werden nur Start und Ende, nicht der Titel; relative Angaben («eine Stunde später») werden nicht berechnet («Neue Zeit nicht erkannt»); ganztägige Termine werden nicht verschoben. Vorgängerfassungen scheiterten beim Verschieben mit HTTP 400; mutmassliche Ursache war, dass das Modell Datum und Ende selbst bestimmte (nicht abschliessend bestätigt). Diese Fassung berechnet beides aus dem gefundenen Termin.

**E6 – Anzeigen: Datenumfang.** Für die Zusammenfassung wird der **vollständige Datensatz jedes Termins** an OpenAI gesendet, also auch Teilnehmer, Beschreibung, Ort und Links, nicht nur Titel und Zeit (siehe [Datenschutz](docs/datenschutz.md)). Ein Zeitraum ohne Termine bleibt nicht mehr ohne Antwort («Keine Termine im angefragten Zeitraum.»); die Vorgängerfassung schwieg (live bestätigt, 16:05), diese antwortet (16:12).

**E7 – Fehler ohne Antwort.** Lesen (Anzeigen, Suchen) und Ändern werden bei einem Fehler bis zu dreimal im Abstand von 2 Sekunden wiederholt; das Anlegen nicht, weil ein Wiederholen doppelte Termine erzeugen könnte. Bleibt ein Fehler bestehen, gibt es keine Antwort im Chat. Bewusst gibt es keine eigene Fehlermeldung an den Nutzer: Der Verweis auf den privaten Error-Workflow wurde entfernt, und ein Fehlerausgang würde dessen Alarm unterdrücken. In den Workflow-Einstellungen kann ein eigener Error-Workflow verbunden werden.

**E8 – Festlegungen.** Zeitzone `Europe/Zurich` steht fest in den Prompts und in der Anfrage zum Ändern. Antworttexte gibt es auf Deutsch, Russisch und Englisch (andere Sprachen: Englisch). Der Ausgang «Calender» der Node `Route — User Intent` trägt einen Tippfehler und ein führendes `=`; er bleibt unverändert, weil die Verbindungen Nodes und Ausgänge über Namen referenzieren.

### Weitere Grenzen

- Die Absichtserkennung ist probabilistisch; Fehlzuordnungen sind möglich.
- Bei mehreren Treffern gleichen Titels nennt die Antwort die Termine in der Reihenfolge, in der Google sie liefert (nicht zwingend nach Uhrzeit).
- Das Gesprächsgedächtnis des Chat-Zweigs ist ein einfacher Fenster-Speicher je Chat; er wird nicht gelöscht.
- Der Workflow schreibt keine eigenen Protokolle; Ausführungsdaten speichert n8n nach den Einstellungen der Instanz.

### Nicht geprüft

- Ausführung und Aktivierung des Workflows aus diesem Repository.
- Öffnen im Editor, Verbinden von Zugangsdaten.
- Registrierung des Telegram-Webhooks und Erreichbarkeit der n8n-Instanz (`WEBHOOK_URL`).
- Verhalten des Modells bei gezielter Prompt Injection (z. B. Anweisungen im Titel eines Termins) und bei anderen Sprachen als Deutsch, Russisch, Englisch.
- Andere n8n-Versionen als 2.43.7 und die Plattform `linux/amd64`.

## Datenschutz

Der Workflow verarbeitet Nachrichten und Kalenderdaten und übermittelt Teile davon an Anbieter ausserhalb der Schweiz (OpenAI, Google, Telegram). Übersicht der Datenflüsse und Hinweise: [docs/datenschutz.md](docs/datenschutz.md). Keine Rechtsberatung, keine Konformitätszusage.

## Sicherheit

Was aus dem Export entfernt wurde, Risiken durch nicht vertrauenswürdige Inhalte und wie Probleme gemeldet werden: [SECURITY.md](SECURITY.md).

## Lizenz

MIT – siehe [LICENSE](LICENSE). Eigenentwicklung, mit Unterstützung von KI-Assistenten erstellt.
