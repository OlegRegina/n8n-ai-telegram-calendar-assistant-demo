# Architektur

> **Eigenprojekt / Demo, kein Kundenauftrag.** Beschreibung nach der Konfiguration der Nodes; der Workflow wurde in der Demo nicht ausgeführt.

## Ablauf

```
Telegram — User Message
        │  (Nachricht)
        ▼
IF — Allowed Sender?  ── nein ──► (still ignoriert)
        │ ja
        ▼
AI — Detect Intent ◄── OpenAI Chat Model + Parser — Calendar Intent
        │  (intent, title, start, end, new_date, new_time, new_duration_minutes, language, …)
        ▼
Route — User Intent (Switch nach intent)
 │
 ├─ create_calendar_event ─► Prepare — Event Times (Code) ─► IF — Times OK?
 │                                                            ├─ ja ──► Calendar — Create Event ─► Telegram — Event Created
 │                                                            └─ nein ─► Telegram — Notice
 │
 ├─ general_chat ──────────► AI — General Assistant ◄── OpenAI Chat Model1 + Memory — Conversation
 │                              └─► Telegram — Agent Reply
 │
 ├─ read_calendar ─────────► Calendar — Read Events ─► Filter — Real Events (Code) ─► IF — Any Events?
 │                                                            ├─ ja ──► Aggregate — Calendar Events
 │                                                            │            └─► AI — Summarize Calendar ◄── OpenAI Chat Model2
 │                                                            │                   └─► Telegram — Calendar Summary
 │                                                            └─ nein ─► Telegram — Notice
 │
 └─ update_calendar_event ─► Calendar — Find Event to Update (nächste 30 Tage)
                                └─► Match — Event to Update (Code)
                                       └─► IF — Exactly One Match?
                                              ├─ ja ──► Calendar API — Update Event (PATCH) ─► Telegram — Update Result
                                              └─ nein ─► Telegram — Notice
```

## Nodes (27)

| Node | Typ | Aufgabe |
|---|---|---|
| `Telegram — User Message` | Telegram Trigger | nimmt Nachrichten (`message`) entgegen; selbst ohne Einschränkung auf Chat oder Benutzer |
| `IF — Allowed Sender?` | IF | lässt nur die Telegram-Benutzer-ID weiter, die rechts eingetragen ist (Platzhalter `REPLACE_WITH_TELEGRAM_USER_ID`); fremde und fehlende Absender: kein Ausgang, keine Antwort (E1) |
| `AI — Detect Intent` | Basic LLM Chain | Prompt: Absicht bestimmen und strukturierte Felder liefern; löst relative Datumsangaben in `Europe/Zurich` auf; kopiert Nachricht und Chat-ID; setzt `language`; liefert beim Ändern nur, was der Nutzer sagt (`new_date`, `new_time`, `new_duration_minutes`) |
| `Parser — Calendar Intent` | Structured Output Parser | erzwingt die Felder der Absichtserkennung (Beispiel-JSON) |
| `OpenAI Chat Model` | OpenAI Chat Model | `gpt-5.4-mini` für `AI — Detect Intent` |
| `Route — User Intent` | Switch | vier Ausgänge nach `intent`: Anlegen, allgemeiner Chat, Anzeigen, Ändern |
| `Prepare — Event Times` | Code | Anlegen: Start und Ende vorbereiten; Ende des Modells, sonst Start + 60 Minuten; liefert `_ok`, `_start`, `_end` oder eine Meldung |
| `IF — Times OK?` | IF | `_ok` → anlegen; sonst Meldung «Zeit nicht erkannt. Es wurde nichts angelegt.» |
| `Calendar — Create Event` | Google Calendar | legt den Termin an (Titel vom Modell, Start und Ende aus `Prepare — Event Times`); ohne Wiederholung |
| `Telegram — Event Created` | Telegram | Antwort «✓ Eingetragen: <Titel>, <Datum Uhrzeit>» in der Sprache der Nachricht |
| `AI — General Assistant` | AI Agent | beantwortet allgemeine Fragen; keine Systemanweisung, keine Werkzeuge (E3) |
| `OpenAI Chat Model1` | OpenAI Chat Model | `gpt-5.4-mini` für den Agenten |
| `Memory — Conversation` | Window Buffer Memory | Gedächtnis je Chat (Schlüssel: Chat-ID) |
| `Telegram — Agent Reply` | Telegram | sendet die Antwort des Agenten |
| `Calendar — Read Events` | Google Calendar | liest die Termine zwischen `start` und `end` der Absichtserkennung; `alwaysOutputData`, bis zu 3 Versuche (Abstand 2 s) |
| `Filter — Real Events` | Code | gibt nur echte Termine weiter; ohne Termine eine Meldung «Keine Termine im angefragten Zeitraum.» |
| `IF — Any Events?` | IF | Termine → zusammenfassen; keine → Meldung |
| `Aggregate — Calendar Events` | Aggregate | fasst alle Termine in ein Feld `events` zusammen |
| `AI — Summarize Calendar` | Basic LLM Chain | fasst die Termine chronologisch in der Sprache der Nachricht zusammen; erhält den **vollständigen** Datensatz jedes Termins (E6) |
| `OpenAI Chat Model2` | OpenAI Chat Model | `gpt-5.4-mini` für die Zusammenfassung |
| `Telegram — Calendar Summary` | Telegram | sendet die Zusammenfassung |
| `Calendar — Find Event to Update` | Google Calendar | liest die Termine von heute bis 30 Tage voraus; `alwaysOutputData`, bis zu 3 Versuche (Abstand 2 s) |
| `Match — Event to Update` | Code | sucht den Termin über den Titel, grenzt bei mehreren Treffern über die bisherige Startzeit ein, berechnet Start und Ende der Änderung aus dem Termin und den Angaben des Nutzers; liefert `_match` (`found`, `none`, `multiple`, `unclear`, `allday`) und den Antworttext |
| `IF — Exactly One Match?` | IF | `found` → Änderung; sonst → Meldung ohne Änderung |
| `Calendar API — Update Event` | HTTP Request | `PATCH` auf `…/calendars/primary/events/<ID>` mit Start und Ende (Zeitzone `Europe/Zurich`); Zugang: Google Calendar OAuth2; bis zu 3 Versuche (Abstand 2 s) |
| `Telegram — Update Result` | Telegram | Antwort «✓ Geändert: <Titel>, <Datum> <von>–<bis>» |
| `Telegram — Notice` | Telegram | sendet den Text `text` der vorherigen Node: Meldungen ohne Änderung (nicht gefunden, mehrere Treffer, Zeit nicht erkannt, ganztägig, nichts angelegt, keine Termine) |

## Entscheidungen in `Prepare — Event Times` (Anlegen)

| Fall | Ergebnis |
|---|---|
| Start gültig, Ende gültig und nach dem Start | Termin mit diesem Start und Ende |
| Start gültig, Ende leer, ungültig oder nicht nach dem Start | Ende = Start + 60 Minuten |
| Start ohne Zeitzonen-Angabe | wird als `Europe/Zurich` gelesen und mit Offset an Google gesendet |
| Start leer oder ungültig | kein Termin; Meldung «Zeit nicht erkannt. Es wurde nichts angelegt.» |

## Entscheidungen in `Match — Event to Update` (Ändern)

| Fall | `_match` | Antwort (de) | Änderung an Google |
|---|---|---|---|
| kein Termin enthält den Titel | `none` | «Termin «…» nicht gefunden. Es wurde nichts geändert.» | nein |
| mehrere Termine, auch nach Eingrenzung | `multiple` | «Mehrere Termine passen. Welchen meinen Sie? Es wurde nichts geändert.» + bis zu 5 Termine | nein |
| genau ein Termin, ganztägig | `allday` | «Ganztägige Termine verschiebe ich nicht. Es wurde nichts geändert.» | nein |
| genau ein Termin, aber weder neues Datum noch neue Uhrzeit noch neue Dauer erkannt | `unclear` | «Neue Zeit nicht erkannt. Es wurde nichts geändert.» | nein |
| genau ein Termin, neue Zeit erkannt | `found` | «✓ Geändert: …» (nach der Änderung) | ja |

**Berechnung bei `found`:** neues Datum = `new_date`, sonst Datum des Termins; neue Uhrzeit = `new_time`, sonst Uhrzeit des Termins; Dauer = `new_duration_minutes`, sonst Dauer des Termins. Zeitzone `Europe/Zurich` inklusive Sommerzeit; Start und Ende gehen mit Offset an Google.

Antworttexte gibt es auf Deutsch, Russisch und Englisch; für andere Sprachen gilt Englisch.
