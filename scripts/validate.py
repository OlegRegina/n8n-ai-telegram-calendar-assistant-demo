#!/usr/bin/env python3
"""Validate the sanitized n8n export and scan the repository for sensitive data.

Checks
  S2b  no repository file is byte-identical to a private source export
  S3   allowlist of keys: unknown or forbidden keys fail (credentials, webhookId,
       cachedResultUrl, instanceId, errorWorkflow, staticData, workflow id/versionId);
       pinData and nodeGroups must be empty
  S4   no value taken from the private source (credential/webhook/instance/error-workflow ids,
       calendar id, e-mails, numbers with 7+ digits) appears in any repository file  [needs --source]
  S5   pattern scan of every repository file: e-mails outside example.com, URLs outside
       the allowlist, numbers with 7+ digits, API keys/tokens/JWT/private keys, IPv4,
       16-character n8n-style ids, personal tokens given with --deny
  S6   structure: node/edge counts, node names and connections unchanged, every $('...')
       reference resolves                                              [names: needs --source]
  S7   the only differences to the source are the approved map paths A1-C2   [needs --source]
  S8   active = false and settings.availableInMCP = false
  S9   calendar = primary (3 Calendar nodes x 2 fields, 1 URL); exactly one placeholder (sender filter)
  S10  synthetic test data: flagged synthetic, unique ids, example.com only, expected values present

Values are never printed: only file names, JSON paths and categories.
Automatic checks are not proof that no sensitive data remains; a manual review is required.

Usage:
  python3 -I -B scripts/validate.py --repo . --workflow workflows/telegram-calendar-assistant.json \
      [--source PRIVATE_EXPORT.json] [--deny TOKEN ...] [--report evidence/validation-report.txt] [--overwrite]
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

CALENDAR = "primary"
USER_ID = "REPLACE_WITH_TELEGRAM_USER_ID"
NAME = "[Your Name]"
EXAMPLE_CHAT = "12345"
PUBLIC_NAME = "Telegram Calendar Assistant (Demo)"
CAL_URL = re.compile(r"(/calendars/)([^/]+)(/events)")

EXPECT = {PUBLIC_NAME: {"nodes": 27, "edges": 28, "calendar_primary": 6, "url_primary": 1, "user_id_placeholder": 1}}

TOP_ALLOWED = {"name", "nodes", "pinData", "connections", "active", "settings", "meta", "nodeGroups", "tags"}
NODE_ALLOWED = {"parameters", "type", "typeVersion", "position", "id", "name",
                "alwaysOutputData", "retryOnFail", "waitBetweenTries", "executeOnce", "maxTries"}
SETTINGS_ALLOWED = {"executionOrder", "binaryMode", "availableInMCP", "timeSavedMode", "callerPolicy"}
FORBIDDEN_KEYS = {"credentials", "webhookId", "cachedResultUrl", "instanceId", "errorWorkflow",
                  "staticData", "versionId", "templateCredsSetupCompleted"}
SAFE_16 = {"autoMapInputData"}
URL_HOSTS_ALLOWED = {"www.googleapis.com", "example.com", "github.com"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+(?:@|%40)[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL = re.compile(r"https?://[^\s\"'<>)\]]+")
LONG_NUMBER = re.compile(r"(?<![\w-])\d{7,}(?![\w-])")
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
SECRETS = {
    "openai-style key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "github token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "google api key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "slack token": re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    "telegram bot token": re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "bearer token": re.compile(r"[Bb]earer\s+[A-Za-z0-9._-]{20,}"),
}

ALLOWED_DIFF = [  # (regex on path, kind, required new value or None)
    (re.compile(r"^nodes\[.*\]\.credentials\."), "removed", None),                       # A1
    (re.compile(r"^nodes\[.*\]\.webhookId$"), "removed", None),                          # A2
    (re.compile(r"^meta\.(instanceId|templateCredsSetupCompleted)$"), "removed", None),  # A3
    (re.compile(r"^meta$"), "added", {}),                                                 # A3 (meta now empty)
    (re.compile(r"^(id|versionId)$"), "removed", None),                                  # A4
    (re.compile(r"^settings\.errorWorkflow$"), "removed", None),                         # A5
    (re.compile(r"\.cachedResultUrl$"), "removed", None),                                # A6
    (re.compile(r"^tags(\[|\.|$)"), "removed", None),                                    # A7
    (re.compile(r"^nodes\[IF — Allowed Sender\?\]\.parameters\.conditions\.conditions\[\d+\]\.rightValue$"), "changed", USER_ID),  # B2
    (re.compile(r"\.parameters\.calendar\.(value|cachedResultName)$"), "changed", CALENDAR),  # B3
    (re.compile(r"^name$"), "changed", PUBLIC_NAME),                                     # B9
    (re.compile(r"^settings\.availableInMCP$"), "changed", False),                       # C1
    (re.compile(r"^active$"), "changed", False),                                         # C2
]


class Report:
    def __init__(self):
        self.lines, self.failed = [], 0

    def add(self, check, status, detail=""):
        if status == "FAIL":
            self.failed += 1
        self.lines.append(f"{status:7} {check:5} {detail}".rstrip())


def flat(obj, prefix=""):
    if isinstance(obj, dict):
        if not obj and prefix:
            yield prefix, {}
        for k, v in obj.items():
            yield from flat(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        if not obj and prefix:
            yield prefix, []
        for i, v in enumerate(obj):
            yield from flat(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def keyed(wf):
    out = dict(flat({k: v for k, v in wf.items() if k != "nodes"}))
    for node in wf.get("nodes", []):
        out.update(flat(node, f"nodes[{node.get('name')}]"))
    return out


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_keys(v)


def string_values(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from string_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from string_values(v)
    elif isinstance(obj, str):
        yield obj


def edges(wf):
    return sum(len(t) for outs in wf.get("connections", {}).values() for o in outs.values() for t in o)


def sensitive_values(src):
    vals = {}

    def add(value, category):
        if value is None:
            return
        value = str(value).strip()
        if value and value not in {NAME, CALENDAR, EXAMPLE_CHAT, PUBLIC_NAME, USER_ID}:
            vals[value] = category

    add(src.get("id"), "workflow id")
    add(src.get("versionId"), "version id")
    add(src.get("meta", {}).get("instanceId"), "instance id")
    add(src.get("settings", {}).get("errorWorkflow"), "error workflow id")
    for tag in src.get("tags") or []:
        add(tag.get("id"), "tag id")
    for node in src.get("nodes", []):
        for cred in (node.get("credentials") or {}).values():
            add(cred.get("id"), "credential id")
        add(node.get("webhookId"), "webhook id")
        p = node.get("parameters", {})
        if isinstance(p.get("calendar"), dict):
            add(p["calendar"].get("value"), "calendar id")
        if node.get("name") == "IF — Allowed Sender?":
            for cond in p.get("conditions", {}).get("conditions", []):
                add(cond.get("rightValue"), "telegram id")
    raw = json.dumps(src, ensure_ascii=False)
    for email in EMAIL.findall(raw):
        add(email, "e-mail")
    for number in LONG_NUMBER.findall(raw):
        add(number, "long number")
    return vals


def repo_files(repo):
    for path in sorted(repo.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(repo).parts:
            yield path


def name_patterns(tokens):
    return [re.compile(rf"(?<!\w){re.escape(t)}(?!\w)", re.IGNORECASE) for t in tokens]


def allowed_special(path, old, new):
    """B7 (calendar in URL) and B8 (chat_id in the parser example): only that part may differ."""
    if path.endswith(".parameters.url") and isinstance(old, str) and isinstance(new, str):
        return CAL_URL.sub(rf"\g<1>{CALENDAR}\g<3>", old) == new
    if path.endswith(".parameters.jsonSchemaExample") and isinstance(old, str) and isinstance(new, str):
        try:
            a, b = json.loads(old), json.loads(new)
        except ValueError:
            return False
        a["chat_id"] = EXAMPLE_CHAT
        return a == b
    return False


def check_workflow(rep, rel, wf, src, deny):
    name = wf.get("name")
    exp = EXPECT.get(name)
    tag = f"[{rel}]"
    if exp is None:
        rep.add("S6", "FAIL", f"{tag} workflow name is not part of the approved map")
        return

    # S3 allowlist
    problems = []
    if set(wf) - TOP_ALLOWED:
        problems.append(f"top-level keys {sorted(set(wf) - TOP_ALLOWED)}")
    if wf.get("pinData") not in ({}, None):
        problems.append("pinData not empty")
    if wf.get("nodeGroups") not in ([], None):
        problems.append("nodeGroups not empty")
    if wf.get("tags") not in ([], None):
        problems.append("tags not empty")
    if wf.get("meta") not in ({}, None):
        problems.append("meta not empty")
    if set(wf.get("settings", {})) - SETTINGS_ALLOWED:
        problems.append(f"settings keys {sorted(set(wf['settings']) - SETTINGS_ALLOWED)}")
    for node in wf.get("nodes", []):
        extra = set(node) - NODE_ALLOWED
        if extra:
            problems.append(f"node '{node.get('name')}' keys {sorted(extra)}")
    forbidden = sorted(set(walk_keys(wf)) & FORBIDDEN_KEYS)
    if forbidden:
        problems.append(f"forbidden keys present {forbidden}")
    rep.add("S3", "FAIL" if problems else "PASS", f"{tag} " + ("; ".join(problems) if problems else "allowlist of keys respected"))

    # S6 structure
    n_nodes, n_edges = len(wf.get("nodes", [])), edges(wf)
    ok = n_nodes == exp["nodes"] and n_edges == exp["edges"]
    rep.add("S6", "PASS" if ok else "FAIL", f"{tag} nodes {n_nodes}/{exp['nodes']}, edges {n_edges}/{exp['edges']}")
    names = [n.get("name") for n in wf.get("nodes", [])]
    refs = set(re.findall(r"\$\('([^']+)'\)", json.dumps(wf, ensure_ascii=False)))
    refs |= set(re.findall(r'\$node\["([^"]+)"\]', json.dumps(wf, ensure_ascii=False)))
    refs |= set(re.findall(r"\$node\[\\\"([^\\]+)\\\"\]", json.dumps(wf, ensure_ascii=False)))
    missing = sorted(r for r in refs if r not in names)
    rep.add("S6", "FAIL" if missing else "PASS", f"{tag} {len(refs)} node references, unresolved: {missing or 0}")
    if src is not None:
        same = names == [n.get("name") for n in src.get("nodes", [])] and wf.get("connections") == src.get("connections")
        rep.add("S6", "PASS" if same else "FAIL", f"{tag} node names, order and connections identical to source")
    else:
        rep.add("S6", "SKIPPED", f"{tag} comparison with source (no --source)")

    # S7 diff-limited
    if src is not None:
        a, b = keyed(src), keyed(wf)
        patterns = name_patterns(deny)
        bad = []
        for path in sorted(set(a) | set(b)):
            if path in a and path in b and a[path] == b[path]:
                continue
            kind = "removed" if path not in b else "added" if path not in a else "changed"
            allowed = False
            for rx, rule_kind, required in ALLOWED_DIFF:
                if rx.search(path) and rule_kind == kind and (required is None or b.get(path) == required):
                    allowed = True
                    break
            if not allowed and kind == "changed" and allowed_special(path, a[path], b[path]):
                allowed = True  # B7, B8
            if not allowed and kind == "changed" and isinstance(a[path], str) and patterns:
                rebuilt = a[path]
                for p in patterns:
                    rebuilt = p.sub(NAME, rebuilt)
                allowed = rebuilt == b[path]  # B5: only name tokens replaced
            if not allowed:
                bad.append(f"{kind}:{path}")
        rep.add("S7", "FAIL" if bad else "PASS", f"{tag} " + (f"unexpected differences: {bad}" if bad else "only approved map paths differ from source"))
    else:
        rep.add("S7", "SKIPPED", f"{tag} diff against source (no --source)")

    # S8 flags
    flags_ok = wf.get("active") is False and wf.get("settings", {}).get("availableInMCP") is False
    rep.add("S8", "PASS" if flags_ok else "FAIL", f"{tag} active=false, availableInMCP=false")

    # S9 calendar = primary, no placeholders
    cal = sum(1 for n in wf.get("nodes", []) if n.get("type") == "n8n-nodes-base.googleCalendar"
              for k in ("value", "cachedResultName") if n.get("parameters", {}).get("calendar", {}).get(k) == CALENDAR)
    url = sum(1 for n in wf.get("nodes", []) if n.get("type") == "n8n-nodes-base.httpRequest"
              and CAL_URL.search(n.get("parameters", {}).get("url", ""))
              and CAL_URL.search(n["parameters"]["url"]).group(2) == CALENDAR)
    strings = list(string_values(wf))
    placeholders = sum(1 for s in strings if "REPLACE_WITH" in s)
    user_ph = sum(1 for s in strings if s == USER_ID)
    diff = {}
    if cal != exp["calendar_primary"]:
        diff["calendar primary"] = (cal, exp["calendar_primary"])
    if url != exp["url_primary"]:
        diff["url primary"] = (url, exp["url_primary"])
    if user_ph != exp["user_id_placeholder"] or placeholders != user_ph:
        diff["placeholders"] = (placeholders, exp["user_id_placeholder"])
    rep.add("S9", "FAIL" if diff else "PASS", f"{tag} " + (f"count mismatch {diff}" if diff else f"calendar = primary ({cal} fields, {url} URL), one placeholder ({USER_ID})"))

    # S5 (workflow-specific) n8n-style 16-character ids
    ids = sorted({s for s in strings if re.fullmatch(r"[A-Za-z0-9]{16}", s) and s not in SAFE_16})
    rep.add("S5", "FAIL" if ids else "PASS", f"{tag} 16-character id-like values: {len(ids)}")


def scan_repo(rep, repo, secrets, deny, source_hashes):
    files = list(repo_files(repo))
    patterns = name_patterns(deny)
    findings, leaked, identical = {}, {}, []
    for path in files:
        rel = str(path.relative_to(repo))
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() in source_hashes:
            identical.append(rel)
        text = raw.decode("utf-8", errors="replace")
        hits = []
        for email in EMAIL.findall(text):
            if not email.lower().endswith("@example.com"):
                hits.append("e-mail outside example.com")
        for url in URL.findall(text):
            host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
            if host not in URL_HOSTS_ALLOWED:
                hits.append("url host not allowlisted")
        if LONG_NUMBER.search(text):
            hits.append("number with 7+ digits")
        if IPV4.search(text):
            hits.append("ipv4 address")
        for label, rx in SECRETS.items():
            if rx.search(text):
                hits.append(label)
        if any(p.search(text) for p in patterns):
            hits.append("personal deny token")
        if hits:
            findings[rel] = sorted(set(hits))
        cats = sorted({cat for value, cat in secrets.items() if value in text})
        if cats:
            leaked[rel] = cats
    rep.add("S2b", "FAIL" if identical else ("PASS" if source_hashes else "SKIPPED"),
            f"repository files identical to a private source: {identical or 0}" if source_hashes else "no --source given")
    if secrets:
        rep.add("S4", "FAIL" if leaked else "PASS",
                f"{len(secrets)} source values checked in {len(files)} files" + (f"; found: {leaked}" if leaked else "; none found"))
    else:
        rep.add("S4", "SKIPPED", "no --source given")
    rep.add("S5", "FAIL" if findings else "PASS",
            f"pattern scan of {len(files)} files" + (f"; findings: {findings}" if findings else "; no findings"))


def check_test_data(rep, repo):
    f = repo / "test-data" / "synthetic-messages.json"
    if not f.exists():
        rep.add("S10", "FAIL", "test-data/synthetic-messages.json missing")
        return
    data = json.loads(f.read_text(encoding="utf-8"))
    problems = []
    if data.get("synthetic") is not True:
        problems.append("file not flagged synthetic")
    msgs = data.get("messages", [])
    ids = [m.get("id") for m in msgs]
    if len(ids) != len(set(ids)):
        problems.append("duplicate record ids")
    for m in msgs:
        for field in ("id", "text", "branch", "expected"):
            if field not in m:
                problems.append(f"{m.get('id')}: missing {field}")
        for addr in EMAIL.findall(json.dumps(m, ensure_ascii=False)):
            if not addr.lower().endswith("@example.com"):
                problems.append(f"{m.get('id')}: address outside example.com")
    rep.add("S10", "FAIL" if problems else "PASS",
            f"{len(msgs)} synthetic messages" + (f"; problems: {problems}" if problems else "; flagged synthetic, unique ids, example.com only"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--workflow", action="append", default=[])
    ap.add_argument("--source", action="append", default=[], help="private export, same order as --workflow")
    ap.add_argument("--deny", action="append", default=[], help="personal token that must not appear (repeatable)")
    ap.add_argument("--report")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if args.source and len(args.source) != len(args.workflow):
        sys.exit("--source must be given once per --workflow, in the same order")
    rep = Report()
    loaded = []
    secrets, source_hashes = {}, set()
    for i, wf_path in enumerate(args.workflow):
        wf_path = Path(wf_path).resolve()
        wf = json.loads(wf_path.read_text(encoding="utf-8"))
        src = None
        if args.source:
            src_path = Path(args.source[i])
            source_hashes.add(hashlib.sha256(src_path.read_bytes()).hexdigest())
            src = json.loads(src_path.read_text(encoding="utf-8"))
            secrets.update(sensitive_values(src))
        loaded.append((str(wf_path.relative_to(repo)), wf, src))
    for rel, wf, src in loaded:
        check_workflow(rep, rel, wf, src, args.deny)
    scan_repo(rep, repo, secrets, args.deny, source_hashes)
    check_test_data(rep, repo)

    head = [
        "Telegram Calendar Assistant Demo - validation report",
        f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "tool: scripts/validate.py",
        f"workflows: {', '.join(rel for rel, _, _ in loaded)}",
        f"private sources: {len(args.source)} provided for comparison (not part of this repository; paths and hashes not recorded)",
        f"personal deny tokens: {len(args.deny)} provided (values not recorded)",
        "note: automatic checks are not proof that no sensitive data remains; a manual review is required.",
        "",
    ]
    summary = ["", f"result: {'FAIL' if rep.failed else 'PASS'} ({rep.failed} failed checks)"]
    text = "\n".join(head + rep.lines + summary) + "\n"
    print(text, end="")
    if args.report:
        out = Path(args.report)
        if out.exists() and not args.overwrite:
            sys.exit(f"STOP: {out} exists (use --overwrite)")
        out.write_text(text, encoding="utf-8")
    sys.exit(1 if rep.failed else 0)


if __name__ == "__main__":
    main()
