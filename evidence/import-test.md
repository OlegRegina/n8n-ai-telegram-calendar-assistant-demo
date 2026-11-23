# Lokaler Importtest – n8n 2.43.7

Stand: 23.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> **Lokaler Import ≠ Funktionstest der Integrationen.**
> Geprüft wurde nur, ob sich der bereinigte Workflow in eine leere, isolierte n8n-Instanz importieren lässt und Struktur und Logik dabei erhalten bleiben. Telegram, Google Calendar und OpenAI wurden nicht aufgerufen.

## Umgebung

| Punkt | Wert |
|---|---|
| n8n-Version (`n8n --version` im Container) | **2.43.7** |
| Image | `n8nio/n8n:2.43.7` |
| Image-Digest | `sha256:3db21366be1d3c77c1708963129c051948573019659e8873e0294be035ffc1b2` |
| Plattform | `linux/arm64` |
| Image erstellt | 2026-10-16 |
| Getestete Datei | `workflows/telegram-calendar-assistant.json`, SHA-256 `98d40b1b1f7796a037ec8d446b5a519cffb1f7dbb9123e6d4cad6b9060df25a5` |

Das Image lag bereits lokal vor (`--pull never`).

## Isolation

- `--network none`: kein Netzwerkzugang des Containers.
- Keine veröffentlichten Ports, keine Editor-Oberfläche, kein Benutzerkonto; nur CLI-Befehle.
- `--cap-drop ALL`, `--security-opt no-new-privileges`, `--rm`.
- Kein Docker-Socket, kein Home-Verzeichnis, kein Cloud-Laufwerk eingebunden.
- Eingebunden: ein leeres Testverzeichnis für die n8n-Datenbank, `workflows/` **nur lesend**, ein Exportverzeichnis.
- Keine Zugangsdaten, keine Secrets.
- Umgebungsvariablen: `N8N_DIAGNOSTICS_ENABLED=false`, `N8N_VERSION_NOTIFICATIONS_ENABLED=false`, `N8N_TEMPLATES_ENABLED=false`, `N8N_PERSONALIZATION_ENABLED=false`, `N8N_HIRING_BANNER_ENABLED=false`.

## Befehle

`$REPO` = dieses Repository, `$SCRATCH` = temporäres Testverzeichnis ausserhalb des Repositorys.

```bash
n8n_cli() {
  docker run --rm --pull never --network none --cap-drop ALL --security-opt no-new-privileges \
    -e N8N_DIAGNOSTICS_ENABLED=false -e N8N_VERSION_NOTIFICATIONS_ENABLED=false \
    -e N8N_TEMPLATES_ENABLED=false -e N8N_PERSONALIZATION_ENABLED=false -e N8N_HIRING_BANNER_ENABLED=false \
    -v "$SCRATCH/db:/home/node/.n8n" -v "$REPO/workflows:/import:ro" -v "$SCRATCH/export:/export" \
    n8nio/n8n:2.43.7 "$@"
}
n8n_cli --version
n8n_cli import:workflow --input=/import/telegram-calendar-assistant.json
n8n_cli export:workflow --all --pretty --output=/export/back.json   # Rücklesen
```

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Import | PASS – «Successfully imported 1 workflow» |
| Export | PASS – «Successfully exported 1 workflow» |
| 27 Nodes, 28 Verbindungen | PASS (Import und Rücklesen gleich) |
| Namen, Typen, Typversionen und Positionen aller Nodes gleich | PASS |
| Node-Parameter gleich der importierten Datei | PASS |
| Verbindungen gleich | PASS |
| Workflow inaktiv nach dem Import; `availableInMCP = false` | PASS |
| Keine Zugangsdaten an Nodes | PASS (0 Nodes) |
| Wiederholungs-Einstellungen (`retryOnFail`, `maxTries = 3`, Abstand 2000 ms) an den drei Nodes erhalten | PASS |

### Erwartete, servicebedingte Unterschiede

Der Export ist nicht byteidentisch mit der importierten Datei. n8n ergänzt auf oberster Ebene: `id`, `versionId`, `versionCounter`, `versionMetadata`, `activeVersionId`, `createdAt`, `updatedAt`, `isArchived`, `triggerCount`, `shared`, `sourceWorkflowId`, `description`, `staticData`. Diese Felder sind Verwaltungsdaten der Test-Instanz und keine Änderung an Nodes, Parametern oder Verbindungen.

## Nicht geprüft

- Öffnen im Editor, Verbinden von Zugangsdaten, Aktivieren.
- Aufruf von Telegram, Google Calendar und OpenAI.
- Andere n8n-Versionen und die Plattform `linux/amd64`.
