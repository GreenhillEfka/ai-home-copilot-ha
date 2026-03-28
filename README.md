# PilotSuite HACS Integration (`copilot_ha`)

[![Release](https://img.shields.io/github/v/release/GreenhillEfka/pilotsuite-styx-ha)](https://github.com/GreenhillEfka/pilotsuite-styx-ha/releases)

PilotSuite HACS-Integration für Home Assistant.

## State of the Art (Stand: 2026-03-28)

- Aktive Release-Linie: **v15.2.7** (lokal vorbereitet, offizieller GitHub-Tag aktuell: **v15.2.7**)
- Kontrakt-Ziel: **paired with Core v15.2.7+**
- Integrationseinbindung: auf dem Repo-Stand, PR-Konsolidierung siehe unten

## Aktuelle PR-Konsolidierung

- **#166** (`feat(config_flow): STEP_MODULES`) — Merge vorbereitet / bereits im Integrationspfad
- **#167** (`feat: restore and harden habitus zone WS API`) — umgesetzt im 15.2.7 Konsolidierungsstand
- **#146** (`release: v14.7.5`) — älterer Release-Lane-Fork, nicht mehr für aktuelles `main` geeignet

## Installation (HACS)

1. HACS → Integrations → `PilotSuite` hinzufügen
2. Home Assistant automatisch `update.ai_home_copilot_update` erzeugen nach erfolgreicher Config-Flow-Anlage

