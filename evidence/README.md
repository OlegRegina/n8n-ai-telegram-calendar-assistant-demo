# Nachweise

Stand: 23.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

| Datei | Art | Was sie zeigt | Was sie **nicht** zeigt |
|---|---|---|---|
| [`validation-report.txt`](validation-report.txt) | automatisch: Ausgabe von `scripts/validate.py` (Datum und Anzahl geprüfter Dateien im Kopf) | Erlaubte Schlüssel, Musterprüfung aller Dateien des damaligen Stands, Struktur, nur genehmigte Änderungen gegenüber dem privaten Export | Keine Aussage über spätere Änderungen; kein Beweis, dass keine sensiblen Daten enthalten sind; persönliche Suchbegriffe sind nicht enthalten |
| [`validation-notes.md`](validation-notes.md) | manuell | Abdeckung des Berichts, offene Punkte | Keine automatische Prüfung |
| [`import-test.md`](import-test.md) | manuell: Protokoll des Autors | Ob sich der Workflow lokal in n8n 2.43.7 importieren lässt und Struktur, Parameter und Verbindungen erhalten bleiben; SHA-256 der getesteten Datei | **Lokaler Import ≠ Funktionstest der Integrationen** |
| [`logic-test.md`](logic-test.md) | wiederholbar: `tests/logic-harness/` | Logik von Absenderfilter, Anlegen, Anzeigen und Ändern mit Beispieldaten, 33 von 33 Szenarien; Start und Ende der Google-Anfragen sind gültig | Nicht Google, Telegram, Modell; nicht den Chat-Zweig |
| [`live-test.md`](live-test.md) | manuell: Protokoll des Autors | Ergebnisse im privaten System am 23.11.2026, auch die gefundenen Fehler der Vorgängerfassungen | Keine öffentlichen Nachweise; nur Teile der Testfälle |
| `screenshots/` | geplant, **noch nicht vorhanden** | – | – |

## Wer was nachprüfen kann

- **Alle**, ohne private Exporte: `python3 -I -B scripts/validate.py --repo . --workflow workflows/telegram-calendar-assistant.json` (S3, S5, S6 ohne Quellvergleich, S8, S9, S10); `bash tests/logic-harness/run.sh` (Logiktest, Docker).
- **Nur der Autor**, mit dem privaten Export (`--source`) und persönlichen Suchbegriffen (`--deny`): S2b, S4, S7 und der Quellvergleich in S6.

## Status

- Der Workflow ist inaktiv. In der Demo wurde nichts gegen echte Dienste ausgeführt.
- Ergebnisse aus dem privaten System sind in [`docs/test-plan.md`](../docs/test-plan.md) als **DOKUMENTIERT** markiert.
