# Datenschutz

> **Eigenprojekt / Demo, kein Kundenauftrag.**
> **Keine Rechtsberatung, keine Konformitätszusage.** Diese Seite beschreibt die Datenflüsse des Workflows, damit eine Prüfung nach dem Schweizer Datenschutzgesetz (revDSG) und – wo anwendbar – der DSGVO vorbereitet werden kann.

## Datenflüsse

| Daten | Ziel | Zweck |
|---|---|---|
| Nachrichten an den Bot, Antworten des Bots, Chat-ID (die Benutzer-ID des Absenders wird nur im Workflow mit der eingetragenen ID verglichen) | Telegram | Bedienung; Telegram-Chats mit Bots sind nicht Ende-zu-Ende-verschlüsselt (Angabe des Anbieters, nicht geprüft) |
| Text der Nachricht, Chat-ID, aktuelles Datum mit Uhrzeit | OpenAI | Absichtserkennung (`AI — Detect Intent`) |
| Text der Nachricht und frühere Nachrichten des Chats | OpenAI | allgemeiner Chat (`AI — General Assistant`, mit Gesprächsgedächtnis) |
| **Vollständiger Datensatz jedes angezeigten Termins** (Titel, Zeiten, Teilnehmer, Beschreibung, Ort, Links, Ersteller und Organisator mit E-Mail-Adresse, soweit vorhanden) | OpenAI | Zusammenfassung (`AI — Summarize Calendar`); der Workflow filtert die Felder nicht (E6) |
| Zeitraum der Anfrage; Titel, Start und Ende beim Anlegen; Start und Ende beim Ändern; die Termine der nächsten 30 Tage beim Suchen | Google Calendar | Termine lesen, anlegen, ändern |
| Ein- und Ausgaben der Nodes einer Ausführung (Nachricht, Absichtsfelder, Termine, Antworten), je nach Einstellungen der Instanz | n8n-Instanz (Ausführungsdaten) | Ablauf und Fehlersuche |

## Aufbewahrung

Ein Löschkonzept ist nicht umgesetzt. Die Daten bleiben an folgenden Orten, bis sie gelöscht werden:

- **Telegram:** Nachrichten und Antworten bleiben im Chat, bis sie dort gelöscht werden.
- **n8n-Ausführungsdaten:** Ob und wie lange n8n Ausführungen speichert, hängt von den Einstellungen der Instanz ab (Speichern erfolgreicher und fehlgeschlagener Ausführungen, automatisches Löschen nach Alter oder Anzahl). Der Workflow setzt dafür keine eigenen Einstellungen.
- **Gesprächsgedächtnis des Chat-Zweigs:** ein Fenster-Speicher je Chat in der Instanz; er wird vom Workflow nicht geleert.
- **Google Calendar:** angelegte und geänderte Termine bleiben bis zur manuellen Löschung.
- **OpenAI:** Aufbewahrung beim Anbieter nach dessen Bedingungen und den Einstellungen des verwendeten Kontos; nicht geprüft.

## Hinweise

- **Personenbezogene Daten Dritter:** Termine enthalten oft Namen, Teilnehmer und Beschreibungen von Dritten, die über die Verarbeitung informiert sein sollten. Beim Anzeigen gehen diese Angaben vollständig an OpenAI (E6).
- **Anbieter ausserhalb der Schweiz:** OpenAI, Google und Telegram sind Anbieter mit Sitz ausserhalb der Schweiz. Vor einem Einsatz mit echten Daten sind Bekanntgabe ins Ausland, Verträge zur Auftragsbearbeitung und die Einstellungen der Anbieter zu prüfen.
- **Datenminimierung:** Für die Absichtserkennung gehen nur die Nachricht, die Chat-ID und das Datum an OpenAI. Für die Zusammenfassung wäre ein Filter auf Titel, Start und Ende möglich; er ist nicht Teil dieser Version.
- **Zugriff:** Nur die eingetragene Telegram-Benutzer-ID wird bedient, alle anderen Nachrichten werden ignoriert (E1); Nachrichten fremder Absender werden dennoch vom Trigger entgegengenommen und als Ausführung in n8n gespeichert. Zugriff auf Kalender, Bot, Telegram-Chat und n8n-Instanz ist eigenverantwortlich zu beschränken.
- **Menschliche Kontrolle:** Es gibt keinen Freigabeschritt (E2); der Auftrag des Nutzers löst die Änderung aus. Die Antwort im Chat nennt Titel und Zeit.
- **Demo-Betrieb:** Für Tests nur synthetische Daten aus [`test-data/`](../test-data/) und einen eigenen Test-Kalender verwenden.

## Nicht geprüft

- Ob ein konkreter Einsatz die Anforderungen von revDSG oder DSGVO erfüllt; das hängt vom jeweiligen Einsatz ab.
- Welche Ausführungsdaten eine konkrete n8n-Instanz tatsächlich speichert und wie lange.
