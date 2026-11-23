# Logiktest

**Was getestet wird:** die Logik des Workflows `workflows/telegram-calendar-assistant.json` in vier Bereichen: Absenderfilter (F), Anlegen (C), Anzeigen (R) und Ändern (U). Die Nodes `IF — Allowed Sender?`, `Prepare — Event Times`, `IF — Times OK?`, `Filter — Real Events`, `IF — Any Events?`, `Aggregate — Calendar Events`, `Match — Event to Update`, `IF — Exactly One Match?`, die **Ausdrücke** der Calendar-Nodes und des HTTP-Request-Nodes für Start, Ende, URL und Körper sowie die Antworttexte der Telegram-Nodes laufen echt in n8n 2.43.7. Für den Absenderfilter wird im Test eine erfundene erlaubte ID (42) eingesetzt.

**Was ersetzt ist:** Absichtserkennung (Modell), Kalender (Google), die eigentlichen Anfragen an Google und das Senden bei Telegram sind durch feste Beispieldaten ersetzt. Der Test sagt deshalb nichts über Google, Telegram oder das Modell aus; er zeigt, dass die Logik zwischen Absichtserkennung und Google-Anfrage die erwarteten Werte erzeugt, Start und Ende gültig sind (Ende nach Start, Zeitzone) und die Antworten stimmen.

**Isolierung:** `--network none`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pull never`, `--rm`; keine Zugangsdaten, keine Ports; leeres temporäres Datenverzeichnis.

## Ablauf

```bash
bash tests/logic-harness/run.sh
```

Voraussetzung: Docker und das lokale Image `n8nio/n8n:2.43.7`. Das Skript erzeugt aus dem Workflow 33 Test-Workflows (`make_harness.py`), importiert und führt sie aus und wertet die Ausgaben aus (`verify.py`). Der Arbeitsordner liegt unter dem temporären Verzeichnis des Systems und kann danach gelöscht werden.

Die Szenarien F1–F3, C01–C10, R01–R05 und U01–U15 stehen in [`docs/test-plan.md`](../../docs/test-plan.md); `verify.py` enthält die erwarteten Werte.
