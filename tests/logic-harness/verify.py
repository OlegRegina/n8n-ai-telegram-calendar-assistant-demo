#!/usr/bin/env python3
"""Prüft die Ergebnisse des Logiktests: Aufruf  python3 -I -B verify.py <ordner-mit-den-Läufen>
Szenarien: F (Absenderfilter), C (Termin anlegen), R (Termine anzeigen), U (Termin ändern). Je Szenario: Art des Ergebnisses, Antworttext, ob eine Anfrage an Google
ausgelöst wird und – bei Anlegen und Ändern – Start, Ende und Zeitzone der Anfrage. Bei Änderungen wird der Körper der Anfrage als JSON gelesen;
leer, ungültig oder Ende vor Start lässt das Szenario fehlschlagen."""
import json, sys
from pathlib import Path

def verify(run):
    run = Path(run); ok = 0; rows = []
    def res(name):
        raw = (run / f"{name}.json").read_text(encoding="utf-8"); j = json.loads(raw[raw.index("{"):]); rd = j["data"]["resultData"]["runData"]
        def o(node):
            r = rd.get(node)
            return [it["json"] for br in r[0]["data"]["main"] if br for it in br] if r else None
        return o, j["data"]["resultData"].get("error")
    def rec(name, good, info):
        nonlocal ok; ok += bool(good); rows.append(f"{'PASS' if good else 'FAIL'} {name} | {info}")
    for name, want in (("F1_erlaubt", ("Passed", "Blocked")), ("F2_fremd", ("Blocked", "Passed")), ("F3_ohne_Absender", ("Blocked", "Passed"))):
        o, err = res(name); rec(name, not err and o(want[0]) is not None and o(want[1]) is None, f"läuft weiter bei: {'Bot' if o('Passed') else 'niemand (still ignoriert)'}")
    C = {
        "C01_ohne_Ende": ("2026-11-24T10:00:00+01:00", "2026-11-24T11:00:00+01:00", "✓ Eingetragen: Test Besprechung, 24.11.2026 10:00"),
        "C02_mit_Ende": ("2026-11-24T10:00:00+01:00", "2026-11-24T11:30:00+01:00", "✓ Eingetragen: Test Besprechung, 24.11.2026 10:00"),
        "C03_Ende_vor_Start": ("2026-11-24T10:00:00+01:00", "2026-11-24T11:00:00+01:00", "✓ Eingetragen: Test Besprechung, 24.11.2026 10:00"),
        "C04_Start_leer": (None, None, "Zeit nicht erkannt. Es wurde nichts angelegt."), "C05_Start_ungueltig": (None, None, "Zeit nicht erkannt. Es wurde nichts angelegt."),
        "C06_ohne_Offset": ("2026-11-24T10:00:00+01:00", "2026-11-24T11:00:00+01:00", "✓ Eingetragen: Test Besprechung, 24.11.2026 10:00"),
        "C07_Sommerzeit": ("2027-04-06T10:00:00+02:00", "2027-04-06T11:00:00+02:00", "✓ Eingetragen: Sommertermin, 06.04.2027 10:00"),
        "C08_ru_Start_leer": (None, None, "Время не распознано. Ничего не создано."), "C09_en_Start_leer": (None, None, "Time not recognised. Nothing was created."),
        "C10_en_ohne_Ende": ("2026-11-27T15:00:00+01:00", "2026-11-27T16:00:00+01:00", "✓ Added: Dentist, 27.11.2026 15:00"),
    }
    for name, (s, e, text) in C.items():
        o, err = res(name); created = o("Calendar — Create Event"); final = o("Telegram — Event Created") if s else o("Telegram — Notice")
        got = final[0]["text"] if final else None
        good = not err and got == text and (created is not None) == bool(s) and (not s or (created[0]["start"] == s and created[0]["end"] == e))
        rec(name, good, (f"angelegt {s[11:16]}–{e[11:16]} ({s[-6:]})" if s and good else "nichts angelegt" if not created else "?") + f" | {got!r}"[:90])
    R = {"R01_mit_Terminen": ("agg", 3, None), "R02_leer_de": ("note", 0, "Keine Termine im angefragten Zeitraum."), "R03_leer_ru": ("note", 0, "В запрошенный период событий нет."),
         "R04_leer_en": ("note", 0, "No events in the requested period."), "R05_nur_Rauschen": ("note", 0, "Keine Termine im angefragten Zeitraum.")}
    for name, (kind, n, text) in R.items():
        o, err = res(name); agg = o("Aggregate — Calendar Events"); note = o("Telegram — Notice")
        good = not err and ((kind == "agg" and agg and len(agg[0]["events"]) == n and note is None) or (kind == "note" and note and note[0]["text"] == text and agg is None))
        rec(name, good, f"{n} Termine an die Zusammenfassung" if kind == "agg" else f"Meldung statt Schweigen: {text!r}")
    U = {
     "U01_nur_Uhrzeit": ("found", "✓ Geändert: Test Besprechung, 24.11.2026 14:00–15:00", "2026-11-24T14:00:00+01:00", "2026-11-24T15:00:00+01:00"),
     "U02_nur_Datum": ("found", "✓ Geändert: Test Besprechung, 25.11.2026 10:00–11:00", "2026-11-25T10:00:00+01:00", "2026-11-25T11:00:00+01:00"),
     "U03_Datum_Zeit_Dauer": ("found", "✓ Geändert: Test Besprechung, 26.11.2026 09:30–10:15", "2026-11-26T09:30:00+01:00", "2026-11-26T10:15:00+01:00"),
     "U04_nur_Dauer": ("found", "✓ Geändert: Test Besprechung, 24.11.2026 10:00–10:30", "2026-11-24T10:00:00+01:00", "2026-11-24T10:30:00+01:00"),
     "U05_nichts_erkannt": ("unclear", "Neue Zeit nicht erkannt. Es wurde nichts geändert.", None, None), "U06_ungueltige_Zeit": ("unclear", "Neue Zeit nicht erkannt. Es wurde nichts geändert.", None, None),
     "U07_ganztaegig": ("allday", "Ganztägige Termine verschiebe ich nicht. Es wurde nichts geändert.", None, None), "U08_ru_nichts_erkannt": ("unclear", "Новое время не распознано. Ничего не изменено.", None, None),
     "U09_nicht_gefunden_en": ("none", 'Event "Dentist" not found. Nothing was changed.', None, None),
     "U10_mehrere": ("multiple", "Mehrere Termine passen. Welchen meinen Sie? Es wurde nichts geändert.\n• 24.11. 10:00 Test Besprechung\n• 26.11. 09:00 Besprechung Treuhand", None, None),
     "U11_mehrere_eingegrenzt": ("found", "✓ Geändert: Besprechung Treuhand, 26.11.2026 14:00–15:00", "2026-11-26T14:00:00+01:00", "2026-11-26T15:00:00+01:00"),
     "U12_gross_klein": ("found", "✓ Geändert: Test Besprechung, 24.11.2026 14:00–15:00", "2026-11-24T14:00:00+01:00", "2026-11-24T15:00:00+01:00"),
     "U13_Zeit_ohne_fuehrende_Null": ("found", "✓ Geändert: Test Besprechung, 24.11.2026 09:05–10:05", "2026-11-24T09:05:00+01:00", "2026-11-24T10:05:00+01:00"),
     "U14_Sommerzeit": ("found", "✓ Geändert: Sommertermin, 06.04.2027 14:00–15:00", "2027-04-06T14:00:00+02:00", "2027-04-06T15:00:00+02:00"),
     "U15_leerer_kalender": ("none", "Termin «Test Besprechung» nicht gefunden. Es wurde nichts geändert.", None, None)}
    for name, (kind, text, s, e) in U.items():
        o, err = res(name); m = o("Match — Event to Update")[0]; final = o("Telegram — Update Result") if kind == "found" else o("Telegram — Notice"); got = final[0]["text"] if final else None
        ran = o("Calendar API — Update Event") is not None
        good = not err and m.get("_match") == kind and got == text and ran == (kind == "found")
        if kind == "found" and good:
            b = json.loads(o("Calendar API — Update Event")[0]["_body"]); good = b["start"]["dateTime"] == s and b["end"]["dateTime"] == e and b["start"]["timeZone"] == "Europe/Zurich"
        rec(name, good, (f"Änderung {s[11:16]}–{e[11:16]} ({s[-6:]})" if s and good else "keine Änderung" if not ran else "?"))
    print("\n".join(rows)); print(f"{ok}/{len(rows)} PASS"); sys.exit(0 if ok == len(rows) else 1)

if __name__ == "__main__":
    verify(sys.argv[1])
