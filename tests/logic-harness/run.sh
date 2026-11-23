#!/usr/bin/env bash
# Logiktest (Absenderfilter, Anlegen, Anzeigen, Ändern) in einer isolierten n8n-Instanz (kein Netzwerk, keine Zugangsdaten).
# Aufruf aus dem Repository-Stamm:  bash tests/logic-harness/run.sh
# Voraussetzung: Docker und das lokale Image n8nio/n8n:2.43.7 (--pull never).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$(mktemp -d)"; mkdir -p "$WORK/harness" "$WORK/db" "$WORK/runs"
python3 -I -B "$REPO/tests/logic-harness/make_harness.py" "$REPO/workflows/telegram-calendar-assistant.json" "$WORK/harness" > "$WORK/ids.txt"
n8n_cli() {
  docker run --rm --pull never --network none --cap-drop ALL --security-opt no-new-privileges \
    -e N8N_DIAGNOSTICS_ENABLED=false -e N8N_VERSION_NOTIFICATIONS_ENABLED=false -e N8N_TEMPLATES_ENABLED=false \
    -e N8N_PERSONALIZATION_ENABLED=false -e N8N_HIRING_BANNER_ENABLED=false -e GENERIC_TIMEZONE=Europe/Zurich \
    -v "$WORK/db:/home/node/.n8n" -v "$WORK/harness:/work:ro" n8nio/n8n:2.43.7 "$@"
}
n8n_cli --version
n8n_cli import:workflow --separate --input=/work/ | tail -1
while read -r id name; do n8n_cli execute --id="$id" --rawOutput > "$WORK/runs/$name.json" 2> "$WORK/runs/$name.err" || true; done < "$WORK/ids.txt"
python3 -I -B "$REPO/tests/logic-harness/verify.py" "$WORK/runs"
echo "Arbeitsordner (nach dem Test löschen): $WORK"
