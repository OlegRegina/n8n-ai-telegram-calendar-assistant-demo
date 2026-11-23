"""Testaufbau für den Telegram Calendar Assistant. Aufruf:  python3 -I -B make_harness.py <workflow.json> <ausgabeordner>
Die Nodes der Zweige (Absenderfilter, Anlegen, Anzeigen, Ändern) (Absenderfilter, Anlegen vorbereiten, Termine filtern, Meldungen) und die ECHTEN Ausdrücke von URL, Körper und Antworttexten laufen in n8n;
Modell, Google und Telegram sind durch feste Beispieldaten ersetzt."""
import json, sys, uuid
from pathlib import Path

def load(wf): return {n["name"]: n for n in json.load(open(wf, encoding="utf-8"))["nodes"]}
def code(name, js, pos=(0, 0)): return {"parameters": {"jsCode": js}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": list(pos), "id": str(uuid.uuid4()), "name": name}
def setn(name, assigns, keep=False, pos=(0, 0)):
    return {"parameters": {"assignments": {"assignments": [{"id": str(uuid.uuid4()), "name": k, "value": x, "type": "string"} for k, x in assigns.items()]}, "includeOtherFields": keep, "options": {}},
            "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": list(pos), "id": str(uuid.uuid4()), "name": name}
trigger = {"parameters": {}, "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0], "id": str(uuid.uuid4()), "name": "Start"}
def link(*pairs):
    c = {}
    for a, b, i in pairs: c.setdefault(a, {"main": []}); m = c[a]["main"]; m += [[] for _ in range(i + 1 - len(m))]; m[i].append({"node": b, "type": "main", "index": 0})
    return c
def out(o): return "return [{ json: { output: " + json.dumps(o, ensure_ascii=False) + " } }];"
ev = lambda s, a, b, i: {"id": i, "summary": s, "start": {"dateTime": a, "timeZone": "Europe/Zurich"}, "end": {"dateTime": b, "timeZone": "Europe/Zurich"}}
CAL = [ev("Team-Runde", "2026-11-24T08:30:00+01:00", "2026-11-24T09:00:00+01:00", "e1"), ev("Test Besprechung", "2026-11-24T10:00:00+01:00", "2026-11-24T11:00:00+01:00", "e2"),
       ev("Lieferant Beispiel GmbH", "2026-11-24T15:00:00+01:00", "2026-11-24T16:00:00+01:00", "e3"), ev("Besprechung Treuhand", "2026-11-26T09:00:00+01:00", "2026-11-26T10:00:00+01:00", "e4"),
       ev("Sommertermin", "2027-04-06T10:00:00+02:00", "2027-04-06T11:00:00+02:00", "e5"), {"id": "e6", "summary": "Betriebsferien", "start": {"date": "2026-12-24"}, "end": {"date": "2026-12-25"}}]
INTENT = lambda **k: dict({"intent": "x", "title": "", "start": "", "end": "", "new_start": "", "new_end": "", "new_date": "", "new_time": "", "new_duration_minutes": 0, "user_message": "", "chat_id": "12345", "language": "de"}, **k)

def make(wf, dst):
    v = load(wf); dst = Path(dst); dst.mkdir(parents=True, exist_ok=True); S = {}
    # ---- Absenderfilter (mit erfundener erlaubter ID 42; der Workflow enthält nur den Platzhalter)
    sender = json.loads(json.dumps(v["IF — Allowed Sender?"])); sender["parameters"]["conditions"]["conditions"][0]["rightValue"] = "42"
    for k, frm in (("F1_erlaubt", 42), ("F2_fremd", 43), ("F3_ohne_Absender", None)):
        msg = {"message": {"text": "hallo", "chat": {"id": 1}}} if frm is None else {"message": {"text": "hallo", "from": {"id": frm}, "chat": {"id": frm}}}
        nodes = [trigger, code("Telegram — User Message", "return [{ json: " + json.dumps(msg) + " }];"), sender, setn("Passed", {"t": "ja"}), setn("Blocked", {"t": "nein"})]
        S[k] = (nodes, link(("Start", "Telegram — User Message", 0), ("Telegram — User Message", "IF — Allowed Sender?", 0), ("IF — Allowed Sender?", "Passed", 0), ("IF — Allowed Sender?", "Blocked", 1)))
    # ---- Anlegen
    create = v["Calendar — Create Event"]["parameters"]
    def make_create(o):
        nodes = [trigger, code("AI — Detect Intent", out(o)), dict(v["Prepare — Event Times"]), dict(v["IF — Times OK?"]),
                 setn("Calendar — Create Event", {"start": create["start"], "end": create["end"], "summary": create["additionalFields"]["summary"]}),
                 code("Fake Google", "if (!$json.start || !$json.end) throw new Error('leere Zeit'); if (DateTime.fromISO($json.end) <= DateTime.fromISO($json.start)) throw new Error('Ende vor Start'); "
                      "return [{ json: { summary: $json.summary, start: { dateTime: $json.start }, end: { dateTime: $json.end } } }];"),
                 setn("Telegram — Event Created", {"text": v["Telegram — Event Created"]["parameters"]["text"]}), setn("Telegram — Notice", {"text": v["Telegram — Notice"]["parameters"]["text"]})]
        return nodes, link(("Start", "AI — Detect Intent", 0), ("AI — Detect Intent", "Prepare — Event Times", 0), ("Prepare — Event Times", "IF — Times OK?", 0),
                           ("IF — Times OK?", "Calendar — Create Event", 0), ("IF — Times OK?", "Telegram — Notice", 1), ("Calendar — Create Event", "Fake Google", 0), ("Fake Google", "Telegram — Event Created", 0))
    for k, o in {
        "C01_ohne_Ende": INTENT(title="Test Besprechung", start="2026-11-24T10:00:00+01:00"),
        "C02_mit_Ende": INTENT(title="Test Besprechung", start="2026-11-24T10:00:00+01:00", end="2026-11-24T11:30:00+01:00"),
        "C03_Ende_vor_Start": INTENT(title="Test Besprechung", start="2026-11-24T10:00:00+01:00", end="2026-11-24T09:00:00+01:00"),
        "C04_Start_leer": INTENT(title="Test Besprechung"),
        "C05_Start_ungueltig": INTENT(title="Test Besprechung", start="morgen"),
        "C06_ohne_Offset": INTENT(title="Test Besprechung", start="2026-11-24T10:00:00"),
        "C07_Sommerzeit": INTENT(title="Sommertermin", start="2027-04-06T10:00:00+02:00"),
        "C08_ru_Start_leer": INTENT(title="Встреча", language="ru"),
        "C09_en_Start_leer": INTENT(title="Meeting", language="en"),
        "C10_en_ohne_Ende": INTENT(title="Dentist", start="2026-11-27T15:00:00+01:00", language="en"),
    }.items(): S[k] = make_create(o)
    # ---- Anzeigen
    def make_read(lang, events):
        nodes = [trigger, code("AI — Detect Intent", out(INTENT(language=lang))), code("Calendar — Read Events", "return " + json.dumps([{"json": e} for e in events], ensure_ascii=False) + ";"),
                 dict(v["Filter — Real Events"]), dict(v["IF — Any Events?"]), dict(v["Aggregate — Calendar Events"]), setn("Telegram — Notice", {"text": v["Telegram — Notice"]["parameters"]["text"]})]
        return nodes, link(("Start", "AI — Detect Intent", 0), ("AI — Detect Intent", "Calendar — Read Events", 0), ("Calendar — Read Events", "Filter — Real Events", 0), ("Filter — Real Events", "IF — Any Events?", 0),
                           ("IF — Any Events?", "Aggregate — Calendar Events", 0), ("IF — Any Events?", "Telegram — Notice", 1))
    S["R01_mit_Terminen"] = make_read("de", CAL[:3]); S["R02_leer_de"] = make_read("de", [{}]); S["R03_leer_ru"] = make_read("ru", [{}])
    S["R04_leer_en"] = make_read("en", [{}]); S["R05_nur_Rauschen"] = make_read("de", [{}, {"kind": "x"}])
    # ---- Ändern (wie v1.2; Meldungs-Node heisst jetzt «Telegram — Notice»)
    patch = v["Calendar API — Update Event"]["parameters"]
    def U(title, language="de", start="", date="", time="", dur=0): return INTENT(intent="update_calendar_event", title=title, start=start, language=language, new_date=date, new_time=time, new_duration_minutes=dur)
    def make_update(o, cal):
        nodes = [trigger, code("AI — Detect Intent", out(o)), code("Calendar — Find Event to Update", "return " + json.dumps([{"json": e} for e in cal], ensure_ascii=False) + ";"),
                 dict(v["Match — Event to Update"]), dict(v["IF — Exactly One Match?"]), setn("Calendar API — Update Event", {"_url": patch["url"], "_body": patch["jsonBody"]}, keep=True),
                 code("Fake Google", "const b = JSON.parse($json._body); if (!b.start.dateTime || !b.end.dateTime) throw new Error('leere Zeit'); if (DateTime.fromISO(b.end.dateTime) <= DateTime.fromISO(b.start.dateTime)) throw new Error('Ende vor Start'); "
                      "return [{ json: { id: $json.id, summary: $json.summary, start: { dateTime: b.start.dateTime }, end: { dateTime: b.end.dateTime } } }];"),
                 setn("Telegram — Update Result", {"text": v["Telegram — Update Result"]["parameters"]["text"]}), setn("Telegram — Notice", {"text": v["Telegram — Notice"]["parameters"]["text"]})]
        return nodes, link(("Start", "AI — Detect Intent", 0), ("AI — Detect Intent", "Calendar — Find Event to Update", 0), ("Calendar — Find Event to Update", "Match — Event to Update", 0), ("Match — Event to Update", "IF — Exactly One Match?", 0),
                           ("IF — Exactly One Match?", "Calendar API — Update Event", 0), ("IF — Exactly One Match?", "Telegram — Notice", 1), ("Calendar API — Update Event", "Fake Google", 0), ("Fake Google", "Telegram — Update Result", 0))
    for k, (o, cal) in {
        "U01_nur_Uhrzeit": (U("Test Besprechung", time="14:00"), CAL), "U02_nur_Datum": (U("Test Besprechung", date="2026-11-25"), CAL),
        "U03_Datum_Zeit_Dauer": (U("Test Besprechung", date="2026-11-26", time="09:30", dur=45), CAL), "U04_nur_Dauer": (U("Test Besprechung", dur=30), CAL),
        "U05_nichts_erkannt": (U("Test Besprechung"), CAL), "U06_ungueltige_Zeit": (U("Test Besprechung", time="vierzehn"), CAL), "U07_ganztaegig": (U("Betriebsferien", time="14:00"), CAL),
        "U08_ru_nichts_erkannt": (U("Test Besprechung", language="ru"), CAL), "U09_nicht_gefunden_en": (U("Dentist", language="en", time="14:00"), CAL), "U10_mehrere": (U("Besprechung", time="14:00"), CAL),
        "U11_mehrere_eingegrenzt": (U("Besprechung", start="2026-11-26T09:00:00+01:00", time="14:00"), CAL), "U12_gross_klein": (U("test BESPRECHUNG", time="14:00"), CAL),
        "U13_Zeit_ohne_fuehrende_Null": (U("Test Besprechung", time="9:05"), CAL), "U14_Sommerzeit": (U("Sommertermin", time="14:00"), CAL), "U15_leerer_kalender": (U("Test Besprechung", time="14:00"), [{}]),
    }.items(): S[k] = make_update(o, cal)
    ids = []
    for i, (k, (nodes, conn)) in enumerate(S.items()):
        wid = f"tm{i + 1:014d}"; ids.append(f"{wid} {k}")
        json.dump({"id": wid, "name": k, "nodes": nodes, "connections": conn, "settings": {"executionOrder": "v1"}, "active": False, "pinData": {}}, open(dst / f"{k}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(ids))

if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2])
