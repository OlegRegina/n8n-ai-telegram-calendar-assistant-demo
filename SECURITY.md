# Sicherheit

Dieses Repository enthält die bereinigte Kopie eines privaten n8n-Exports. **Eigenprojekt / Demo, kein Kundenauftrag.**

## Was entfernt oder ersetzt wurde

| Inhalt | Behandlung |
|---|---|
| Zugangsdaten-Verweise an Nodes (ID und Name) | entfernt |
| Webhook-IDs | entfernt |
| Instanz-ID, Workflow-ID, Versions-ID, Tags | entfernt |
| Verweis auf den privaten Error-Workflow | entfernt |
| Telegram-Benutzer-ID im Absenderfilter | durch `REPLACE_WITH_TELEGRAM_USER_ID` ersetzt |
| Kalender-ID (E-Mail-Adresse des Kontos) in den Calendar-Nodes und in der URL der Termin-Änderung | durch `primary` ersetzt |
| Beispiel-Chat-ID im Beispiel des Output-Parsers | durch `12345` ersetzt |
| Name des Workflows | durch «Telegram Calendar Assistant (Demo)» ersetzt |
| MCP-Zugriff und Aktivierung | `availableInMCP = false`, `active = false` |
| Interne UUIDs von Nodes und Bedingungen (zufällige UUID v4) | bewusst unverändert: gewähren keinen Zugriff; erlauben höchstens die Zuordnung zu Kopien des privaten Exports |

Hinterlegte Zugangsdaten (Credentials) speichert n8n getrennt vom Workflow; ein Workflow-Export enthält nur Verweise darauf (ID und Name), und diese wurden entfernt. Werte, die direkt in Node-Parameter eingetragen werden (z. B. ein API-Schlüssel in einem HTTP-Header, in einer URL oder in einem Code-Node), exportiert n8n dagegen im Klartext; solche Werte enthält dieser Workflow nach der Prüfung nicht.

## Wie geprüft wurde

- [`scripts/sanitize.py`](scripts/sanitize.py) wendet nur die genehmigten Änderungen an und bricht ab, wenn unbekannte Felder auftreten oder die Zahl der Änderungen abweicht.
- [`scripts/validate.py`](scripts/validate.py) prüft erlaubte Schlüssel, sucht in allen Dateien nach E-Mail-Adressen, Links, langen Nummern, Schlüsseln und Tokens, vergleicht mit dem privaten Quell-Export und stellt sicher, dass sich nur genehmigte Felder geändert haben. Ergebnis: [`evidence/validation-report.txt`](evidence/validation-report.txt).
- Zusätzlich wurden alle Zeichenketten des Workflows manuell durchgesehen.

Automatische Prüfungen sind **kein Beweis**, dass keine sensiblen Daten mehr enthalten sind.

## Hinweise für die Nutzung

- Unbereinigte n8n-Exporte nie in ein Repository legen; `.gitignore` schliesst `*.raw.json`, `private/` und `exports/` aus.
- Zugangsdaten nur in n8n hinterlegen, nie in Workflow-Dateien, Node-Parametern, Screenshots oder Chats. Gelangt ein Token dorthin, sofort widerrufen und ersetzen.
- `n8n export:credentials` (insbesondere mit `--decrypted`) nie für Dateien dieses Repositorys verwenden.
- **Absender einschränken (E1):** `IF — Allowed Sender?` bedient nur die eingetragene Telegram-Benutzer-ID. Vor der Aktivierung den Platzhalter ersetzen; ohne Eintrag antwortet der Bot niemandem. Die Abweisung fremder Konten ist im Logiktest geprüft (F2, F3), live nicht (M15). Den Bot trotzdem nicht öffentlich bekannt machen.
- Nur mit einem **Test-Kalender** und einem eigenen Bot aktivieren (E2).
- `availableInMCP` nur aktivieren, wenn ein Zugriff über MCP wirklich nötig ist.

## Nicht vertrauenswürdige Eingaben (Untrusted Input / Prompt Injection)

- **Nachrichten:** Der Text der Telegram-Nachricht geht in den Prompt von `AI — Detect Intent` und, im Chat-Zweig, an den KI-Agenten. Fremde Absender werden vor der Absichtserkennung verworfen (E1); der Filter prüft nur die ID, nicht den Inhalt.
- **Termine:** Titel, Beschreibung, Teilnehmer und Ort der Termine stammen oft von Dritten (Einladungen). Beim Anzeigen werden sie vollständig in den Prompt von `AI — Summarize Calendar` eingesetzt.
- **Mögliche Folgen:** Ein Termin kann Anweisungen enthalten, die das Modell befolgt (Prompt Injection), z. B. eine irreführende oder unvollständige Zusammenfassung.
- **Begrenzte Wirkung:** `AI — Summarize Calendar` und `AI — Detect Intent` sind einfache Ketten ohne Werkzeuge; sie können selbst nichts ändern. Anlegen und Ändern führen Calendar-Nodes und der HTTP-Request-Node aus, mit Werten aus der Absichtserkennung der **Nachricht**; Termin-Inhalte gehen nicht dorthin. `AI — General Assistant` hat keine Werkzeuge. Wer als erlaubter Absender gilt, kann dagegen über die Nachricht selbst Termine anlegen oder ändern (E1, E2).
- **Nicht Teil dieser Version:** Freigabeschritt, Begrenzung der an OpenAI gesendeten Termin-Felder, Prüfung von Titel und Datum der Modellausgabe beim Anlegen (E4; nur Ende und Start werden im Code abgesichert).
- **Nicht geprüft:** Verhalten der Modelle gegenüber gezielter Prompt Injection (Prüffall M14 in [`docs/test-plan.md`](docs/test-plan.md)).

## Probleme melden

Bitte ein Issue in diesem Repository eröffnen – **ohne** Zugangsdaten, IDs oder personenbezogene Daten. Für vertrauliche Hinweise die private Sicherheitsmeldung des Repositorys verwenden, sofern sie aktiviert ist.
