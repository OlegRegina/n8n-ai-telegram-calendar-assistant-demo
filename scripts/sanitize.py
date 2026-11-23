#!/usr/bin/env python3
"""Sanitize the n8n export of the Telegram Calendar Assistant for the public demo.

Applies the approved sanitization map and nothing else:

  A1  remove node credentials (id + name)
  A2  remove node webhookId
  A3  remove meta.instanceId and meta.templateCredsSetupCompleted
  A4  remove workflow id and versionId
  A5  remove settings.errorWorkflow
  A6  remove every cachedResultUrl
  A7  remove non-empty tags
  B2  Telegram user ID in the sender filter                  -> REPLACE_WITH_TELEGRAM_USER_ID
  B3  Google Calendar calendar value/name (Calendar nodes)  -> primary
  B5  personal name tokens in any string                    -> [Your Name]   (tokens are passed with --name)
  B7  calendar in the URL of the HTTP Request node           -> primary
  B8  chat_id in the example of the Structured Output Parser -> 12345
  B9  workflow name                                          -> Telegram Calendar Assistant (Demo)
  C1  settings.availableInMCP                                -> false
  C2  active                                                 -> false

Safety rules:
  * unknown top-level, node, settings or meta keys, non-empty pinData or nodeGroups,
    or staticData abort the run before anything is written;
  * the number of changes per rule must equal the approved map, otherwise nothing is written;
  * values of removed or replaced fields are never printed;
  * an existing output file is only replaced with --overwrite.

Usage:
  python3 -I -B scripts/sanitize.py --source PRIVATE_EXPORT.json --out workflows/telegram-calendar-assistant.json \
      [--name TOKEN ...] [--overwrite]
"""
import argparse
import json
import re
import sys
from pathlib import Path

CALENDAR = "primary"
USER_ID = "REPLACE_WITH_TELEGRAM_USER_ID"
NAME = "[Your Name]"
EXAMPLE_CHAT = "12345"
PUBLIC_NAME = "Telegram Calendar Assistant (Demo)"
CAL_URL = re.compile(r"(/calendars/)([^/]+)(/events)")

ALLOWED_TOP = {"name", "nodes", "pinData", "connections", "active", "settings",
               "versionId", "meta", "nodeGroups", "id", "tags"}
ALLOWED_NODE = {"parameters", "type", "typeVersion", "position", "id", "name",
                "credentials", "alwaysOutputData", "retryOnFail", "waitBetweenTries",
                "webhookId", "executeOnce", "maxTries"}
ALLOWED_SETTINGS = {"executionOrder", "binaryMode", "availableInMCP", "timeSavedMode",
                    "errorWorkflow", "callerPolicy"}
ALLOWED_META = {"instanceId", "templateCredsSetupCompleted"}

# Approved number of changes per rule (sanitization map, 2026-11-23).
EXPECTED = {
    "📅G.CALENDAR v1.3": {"A1": 13, "A2": 6, "A3": 2, "A4": 0, "A5": 1, "A6": 0, "A7": 0,
                         "B2": 1, "B3": 6, "B5": 0, "B7": 1, "B8": 1, "B9": 1, "C1": 1, "C2": 1},
}


def fail(msg):
    print(f"STOP: {msg}. Nothing written.", file=sys.stderr)
    sys.exit(1)


def precheck(wf):
    problems = []
    unknown = set(wf) - ALLOWED_TOP
    if unknown:
        problems.append(f"unknown top-level keys {sorted(unknown)}")
    if wf.get("pinData") not in ({}, None):
        problems.append("pinData is not empty")
    if wf.get("nodeGroups") not in ([], None):
        problems.append("nodeGroups is not empty")
    unknown = set(wf.get("settings", {})) - ALLOWED_SETTINGS
    if unknown:
        problems.append(f"unknown settings keys {sorted(unknown)}")
    unknown = set(wf.get("meta", {})) - ALLOWED_META
    if unknown:
        problems.append(f"unknown meta keys {sorted(unknown)}")
    for node in wf.get("nodes", []):
        unknown = set(node) - ALLOWED_NODE
        if unknown:
            problems.append(f"node '{node.get('name')}': unknown keys {sorted(unknown)}")
    return problems


def remove_key_everywhere(obj, key):
    count = 0
    if isinstance(obj, dict):
        if key in obj:
            del obj[key]
            count += 1
        for value in obj.values():
            count += remove_key_everywhere(value, key)
    elif isinstance(obj, list):
        for value in obj:
            count += remove_key_everywhere(value, key)
    return count


def replace_names(obj, patterns):
    """Replace name tokens in every string value; return (new_obj, count)."""
    if isinstance(obj, dict):
        total = 0
        for k in list(obj):
            obj[k], n = replace_names(obj[k], patterns)
            total += n
        return obj, total
    if isinstance(obj, list):
        total = 0
        for i, value in enumerate(obj):
            obj[i], n = replace_names(value, patterns)
            total += n
        return obj, total
    if isinstance(obj, str):
        total = 0
        for pattern in patterns:
            obj, n = pattern.subn(NAME, obj)
            total += n
        return obj, total
    return obj, 0


def sanitize(wf, name_tokens):
    c = {rule: 0 for rule in EXPECTED[next(iter(EXPECTED))]}
    for node in wf["nodes"]:
        if node.pop("credentials", None) is not None:
            c["A1"] += 1
        if node.pop("webhookId", None) is not None:
            c["A2"] += 1
    meta = wf.get("meta", {})
    for key in ("instanceId", "templateCredsSetupCompleted"):
        if meta.pop(key, None) is not None:
            c["A3"] += 1
    for key in ("id", "versionId"):
        if wf.pop(key, None) is not None:
            c["A4"] += 1
    if wf.get("settings", {}).pop("errorWorkflow", None) is not None:
        c["A5"] += 1
    c["A6"] = remove_key_everywhere(wf["nodes"], "cachedResultUrl")
    if wf.get("tags"):
        del wf["tags"]
        c["A7"] += 1
    for node in wf["nodes"]:
        p = node.get("parameters", {})
        if node.get("name") == "IF — Allowed Sender?" and node.get("type") == "n8n-nodes-base.if":
            for cond in p.get("conditions", {}).get("conditions", []):
                cond["rightValue"] = USER_ID
                c["B2"] += 1
        if node.get("type") == "n8n-nodes-base.googleCalendar" and isinstance(p.get("calendar"), dict):
            for key in ("value", "cachedResultName"):
                if key in p["calendar"]:
                    p["calendar"][key] = CALENDAR
                    c["B3"] += 1
        if node.get("type") == "n8n-nodes-base.httpRequest" and isinstance(p.get("url"), str):
            new, n = CAL_URL.subn(rf"\g<1>{CALENDAR}\g<3>", p["url"])
            if n and new != p["url"]:
                p["url"] = new
                c["B7"] += 1
        if node.get("type") == "@n8n/n8n-nodes-langchain.outputParserStructured" and "jsonSchemaExample" in p:
            example = json.loads(p["jsonSchemaExample"])
            if "chat_id" in example:
                example["chat_id"] = EXAMPLE_CHAT
                p["jsonSchemaExample"] = json.dumps(example, ensure_ascii=False, indent=2)
                c["B8"] += 1
    patterns = [re.compile(rf"(?<!\w){re.escape(t)}(?!\w)") for t in name_tokens]
    wf["nodes"], c["B5"] = replace_names(wf["nodes"], patterns)
    wf["name"] = PUBLIC_NAME
    c["B9"] += 1
    if "settings" in wf:
        wf["settings"]["availableInMCP"] = False
        c["C1"] += 1
    wf["active"] = False
    c["C2"] += 1
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="private n8n export (read only)")
    ap.add_argument("--out", required=True, help="sanitized output file")
    ap.add_argument("--name", action="append", default=[], help="personal name token for B5 (repeatable)")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    src, out = Path(args.source), Path(args.out)
    if src.resolve() == out.resolve():
        fail("output must not be the source file")
    if out.exists() and not args.overwrite:
        fail(f"{out} exists (use --overwrite)")

    wf = json.loads(src.read_text(encoding="utf-8"))
    name = wf.get("name")
    if name not in EXPECTED:
        fail("workflow name is not part of the approved map")
    problems = precheck(wf)
    if problems:
        fail("; ".join(problems))

    counts = sanitize(wf, args.name)
    mismatch = {r: (counts[r], EXPECTED[name][r]) for r in counts if counts[r] != EXPECTED[name][r]}
    if mismatch:
        fail("change count differs from approved map " +
             ", ".join(f"{r}: {got} != {exp}" for r, (got, exp) in mismatch.items()))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {name} -> {out}")
    print("changes per rule: " + ", ".join(f"{r}={n}" for r, n in counts.items()))


if __name__ == "__main__":
    main()
