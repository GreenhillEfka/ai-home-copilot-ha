# PilotSuite Agent Scripts

## health_check.py
Autonomer Health-Check für PilotSuite. Läuft auf HA-System.

```bash
# Env vars
export HA_TOKEN="..."           # HA API token
export HA_URL="http://supervisor/core/api"
export CORE_URL="http://localhost:8909"
export GH_TOKEN="..."           # GitHub token (für Issue-Posting)

# Checks
python3 health_check.py              # Alle Checks ausführen
python3 health_check.py --report     # Report als GitHub Issue posten
python3 health_check.py --dry-run    # Kein GitHub Post
```

## fixer.py
Autonomer Fixer — erkennt Probleme und reportet sie.

```bash
python3 fixer.py --dry-run    # Diagnose only
```

## Checks
1. **Core Health** — Version, Erreichbarkeit
2. **HA Integration** — Sensor-States, Zone-Count
3. **Zone Sync** — HA↔Core Sync-Status
4. **Module Schemas** — 7 Module geladen

## Output
Markdown-Format, postbar als GitHub Issue mit Label `health`.
