# Einrichtung

> **Eigenprojekt / Demo, kein Kundenauftrag.** Der lokale Import wurde mit n8n **2.43.7** geprüft ([`evidence/import-test.md`](../evidence/import-test.md)); die Einrichtung der Zugänge und ein Testlauf mit den echten Diensten sind in dieser Demo **nicht geprüft**.

## Voraussetzungen

- n8n (geprüft: Import in Version 2.43.7).
- Ein **eigener Test-Kalender** in Google Calendar, kein produktiver Kalender (siehe E1 und E2 im [README](../README.md)).
- Ein **eigener Telegram-Bot** (über den BotFather) und ein Chat mit ihm; dazu die **eigene Telegram-Benutzer-ID** (Absenderfilter).
- Eine n8n-Instanz, die der Telegram-Trigger über eine Webhook-Adresse erreichen kann (siehe [Webhook](#webhook-erreichbarkeit-der-instanz)).
- Ein OpenAI-API-Zugang.

## Benötigte Zugänge in n8n

| Zugangstyp | Nodes |
|---|---|
| Telegram API | `Telegram — User Message` und die fünf Antwort-Nodes (`Telegram — Event Created`, `— Agent Reply`, `— Calendar Summary`, `— Update Result`, `— Notice`) |
| Google Calendar OAuth2 | `Calendar — Create Event`, `Calendar — Read Events`, `Calendar — Find Event to Update`; dazu `Calendar API — Update Event` (HTTP Request mit vordefiniertem Zugangstyp «Google Calendar OAuth2 API») |
| OpenAI API | `OpenAI Chat Model`, `OpenAI Chat Model1`, `OpenAI Chat Model2` |

## Schritte

1. **Workflow importieren:** `workflows/telegram-calendar-assistant.json` über «Import from File» oder per CLI `n8n import:workflow --input=<Datei>`.
2. **Zugänge verbinden** (Tabelle oben).
3. **Eigene Telegram-Benutzer-ID eintragen:** in `IF — Allowed Sender?` den Platzhalter `REPLACE_WITH_TELEGRAM_USER_ID` (rechter Wert der Bedingung) durch die eigene ID ersetzen. Die ID steht in einer Ausführung des Workflows im Ausgang von `Telegram — User Message` unter `message.from.id`: den Workflow dafür kurz aktivieren, dem Bot eine Nachricht schreiben (der Bot antwortet noch nicht) und die Ausführung öffnen. Ohne Eintrag antwortet der Bot niemandem (E1).
4. **Kalender prüfen:** In den drei Calendar-Nodes und in der URL von `Calendar API — Update Event` steht `primary` (Hauptkalender des verbundenen Kontos). Für einen Test-Kalender dort dessen Kalender-ID eintragen, in der URL an der Stelle von `primary`.
5. **Optional:** einen eigenen Error-Workflow in den Workflow-Einstellungen verbinden (der Verweis auf den privaten Error-Workflow wurde entfernt). Ohne ihn bleiben Fehler (E7) ohne Meldung.
6. **Test:** Test-Termine nach [`test-data/synthetic-messages.json`](../test-data/synthetic-messages.json) anlegen («prepare»), den Workflow nur für die Dauer des Tests aktivieren und die Nachrichten M01–M15 an den Bot senden (M15 erfordert ein zweites Telegram-Konto). Ergebnisse mit [`docs/test-plan.md`](test-plan.md) vergleichen.
7. **Danach:** Workflow deaktivieren; Test-Termine im Kalender entfernen.

## Webhook: Erreichbarkeit der Instanz

Der Telegram-Trigger arbeitet mit einer Webhook-Adresse, unter der Telegram Nachrichten an die n8n-Instanz zustellt. Welche Adresse n8n dafür verwendet, legt die Einstellung `WEBHOOK_URL` fest; sie muss für Telegram aus dem Internet erreichbar sein.

**In dieser Demo nicht geprüft:** welche Adresse genügt und ob die beim Import fehlende `webhookId` beim Öffnen und Speichern im Editor ergänzt wird. Das Öffnen von Ports oder das Ändern von Netzwerkeinstellungen ist nicht Teil dieser Anleitung; dafür gelten die Sicherheitsregeln der eigenen Umgebung.

## Was der Import nicht ersetzt

> **Lokaler Import ≠ Funktionstest der Integrationen.**

Ob Telegram, Google Calendar und OpenAI nach der Einrichtung wie beschrieben zusammenarbeiten, ist für diese Demo nicht geprüft; die Ergebnisse des Autors im eigenen System stehen in [`evidence/live-test.md`](../evidence/live-test.md).
