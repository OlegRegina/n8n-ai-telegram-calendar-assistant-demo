# Logiktest

Stand: 23.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> Der Test lässt die Logik von Absenderfilter, Anlegen, Anzeigen und Ändern in einer isolierten n8n-Instanz laufen. Kalender, Modell, die Anfragen an Google und Telegram sind durch feste Beispieldaten ersetzt: **kein Funktionstest der Integrationen.**

## Ergebnis

**PASS, 33 von 33 Szenarien** (F1–F3, C01–C10, R01–R05, U01–U15), Ausführung der Nodes in n8n 2.43.7 (Image und Isolation wie in [`import-test.md`](import-test.md)). Die Szenarien und Erwartungen stehen in [`docs/test-plan.md`](../docs/test-plan.md), Aufbau und Wiederholung in [`tests/logic-harness/README.md`](../tests/logic-harness/README.md).

## Was die Szenarien belegen

- **Absenderfilter (F):** nur die erlaubte ID läuft weiter; andere und fehlende Absender werden still ignoriert.
- **Anlegen (C):** Das Ende wird aus dem Modell übernommen oder auf Start + 60 Minuten gesetzt (leer, ungültig oder vor dem Start); ohne erkennbaren Start wird nichts angelegt und der Nutzer erhält eine Meldung; Start ohne Zeitzone wird als `Europe/Zurich` gelesen; der Sommerzeit-Offset stimmt; Start und Ende der Anfrage sind gültig, das Ende liegt nach dem Start.
- **Anzeigen (R):** Termine gehen an die Zusammenfassung; ohne Termine (auch bei leeren Einträgen) kommt eine Meldung in der Sprache der Nachricht.
- **Ändern (U):**
  - Termin wird über den Titel gefunden (auch in anderer Gross-/Kleinschreibung); bei mehreren Treffern wird nichts geändert oder, mit bekannter bisheriger Startzeit, auf den passenden Termin eingegrenzt.
  - Die neue Zeit wird aus dem gefundenen Termin und den Angaben des Nutzers berechnet: nur Uhrzeit, nur Datum, Datum mit Uhrzeit und Dauer, nur Dauer; Sommerzeit-Offset stimmt.
  - Fehlende, ungültige oder unverständliche Angaben, ganztägige Termine und leere Kalender führen zu einer Antwort und zu **keiner** Änderung (der Node `Calendar API — Update Event` läuft dann nicht).
  - Der **Körper der Anfrage** an Google, erzeugt mit den echten Ausdrücken des Workflows, ist gültiges JSON mit Start und Ende, Ende nach Start, Zeitzone `Europe/Zurich`.
  - Antworttexte auf Deutsch, Russisch und Englisch.

## Was sie nicht belegen

- Dass die Google-API die Anfrage annimmt (das zeigt nur ein Test mit echtem Zugang, siehe [`live-test.md`](live-test.md)).
- Dass das Modell die Felder (`start`, `end`, `new_date`, `new_time`, `new_duration_minutes`, `language`) aus einer Nachricht richtig füllt.
- Dass fremde Telegram-Konten live tatsächlich abgewiesen werden (M15).
- Den allgemeinen Chat-Zweig und die Zusammenfassung durch das Modell.

## Wiederholung

```bash
bash tests/logic-harness/run.sh
```
