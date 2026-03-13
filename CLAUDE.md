# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Projektueberblick

**PilotSuite Styx HA** ist die Home Assistant HACS Integration der PilotSuite-Plattform. Sie stellt Sensoren, Buttons, Dashboards, Lovelace Cards und eine Config-Flow UI bereit, die mit dem PilotSuite Core Add-on kommuniziert.

**Gegenstueck:** [pilotsuite-styx-core](../pilotsuite-styx-core) -- Backend Add-on (Flask REST-API, Brain Graph, Neurons, LLM)

- **Typ:** HACS Custom Integration (`integration_type: hub`)
- **Domain:** `copilot_ha`
- **Sprache:** Python 3.11+ (Backend), TypeScript/JS (Lovelace Cards)
- **HA Mindestversion:** 2024.1.0
- **Lizenz:** Privat, alle Rechte vorbehalten
- **Version:** Muss in `custom_components/copilot_ha/manifest.json` und `VERSION` uebereinstimmen, paired mit Core-Version

---

## Entwicklungskommandos

```bash
# Tests ausfuehren (alle Python-Tests)
cd /home/user/pilotsuite-styx-ha && python -m pytest tests/ -v --tb=short -x

# Einzelne Testdatei
python -m pytest tests/test_zone_matching.py -v -x

# Einzelne Testklasse
python -m pytest tests/test_zone_matching.py::TestZoneMatchingBasics -v

# JS/TS Tests (Playwright E2E + Jest)
npx playwright test
npx jest tests/test_neuron_dashboard.test.js

# Syntax-Check
python -m py_compile $(find custom_components/copilot_ha -name '*.py')
```

**Hinweis:** `conftest.py` fuegt `custom_components/copilot_ha` automatisch zum Python-Path hinzu. Kein PYTHONPATH-Export noetig.

---

## Architektur

### Kommunikationsmodell

```
Home Assistant <--> copilot_ha Integration <--> PilotSuite Core Add-on (Port 8909)
                         |                              |
                    Sensoren/Buttons              Flask REST-API
                    Dashboard YAML                Brain Graph
                    Lovelace Cards                LLM / Neurons
                    Config Flow                   Zone Automation
                    Event Forwarding              Musikwolke
```

Die Integration ist ein **Thin Client**: Sie pollt/pusht Daten vom/zum Core Add-on via HTTP und mappt die Ergebnisse auf HA-Entities.

### CopilotRuntime + ModuleRegistry (core/)

Zentrales Plugin-System fuer die Integration:

```python
# core/runtime.py — Singleton pro HA-Instanz
runtime = CopilotRuntime.get(hass)
await runtime.async_setup_entry(entry, ["brain_sync", "event_forwarder", ...])
```

- **CopilotRuntime**: Verwaltet `ModuleRegistry`, erstellt und lifecycle-managed Module pro ConfigEntry
- **CopilotModule**: Basisklasse (async_setup_entry / async_unload_entry)
- **ModuleContext**: `(hass, entry)` Wrapper fuer Module
- Fehlgeschlagene Module werden uebersprungen (graceful degradation)

### Config Flow (7-Step Wizard)

Modulare Config Flow in 5 Dateien aufgeteilt:

| Datei | Verantwortung |
|-------|-------------|
| `config_flow.py` | Duenner Coordinator, importiert Steps |
| `config_wizard_steps.py` | Wizard-Step-Handler (Discovery, Zones, Entities, Features, Network, Review) |
| `config_schema_builders.py` | Schema-Builder Funktionen (voluptuous) |
| `config_zones_flow.py` | Zone-Management + Helpers |
| `config_options_flow.py` | OptionsFlowHandler (nach Setup) |
| `config_helpers.py` | Constants, CSV-Utils, Validierung |

Steps: DISCOVERY -> ZONES -> ZONE_ENTITIES -> ENTITIES -> FEATURES -> NETWORK -> REVIEW

### Entity-Plattformen

145+ Python-Module in `custom_components/copilot_ha/`. Plattformen:

- **sensor.py**: Hauptsensoren (Brain Score, Mood, etc.)
- **binary_sensor.py**: Praesenz-, Anomalie-Sensoren
- **button.py + button_*.py**: ~20 Button-Module (Debug, Graph, Camera, Demo, etc.)
- **switch.py**: Automation Toggles
- **number.py**: Konfigurierbare Zahlenwerte
- **select.py**: Dropdowns
- **conversation.py**: HA Conversation Agent (Styx Assist)
- **stt.py + tts.py**: Speech-to-Text / Text-to-Speech via Core LLM
- **camera.py**: Brain Graph Visualisierung als Kamera-Entity

### Dashboard

- `dashboard/pilotsuite_dashboard_v13.yaml` — Haupt-Dashboard (YAML, wird bei Setup installiert)
- `dashboard/card_generator.py` — Dynamische Card-Generierung
- `brain_graph_panel.py` — Brain Graph Custom Panel

### Connection Config

- `connection_config.py` — Merged Entry Config: Kombiniert `config_entry.data` + `config_entry.options` + Umgebungsvariablen
- `resolve_core_connection_from_mapping()` — Findet Core Add-on URL (Fallback-Kette: Entry → Env → localhost:8909)
- Token-Handling: Auth-Token aus Config Entry, COPILOT_AUTH_TOKEN Env, oder Add-on Options

---

## Konventionen

### HA Entity Pattern

Entities erben von `CopilotStyxEntity` (in `entity.py`) und definieren:
- `_attr_unique_id`: Basierend auf `INTEGRATION_UNIQUE_ID` + Suffix
- `device_info`: Verknuepfung mit Haupt-Device "Styx Hub"
- `async_update()`: Pollt Core API

### Neue Module hinzufuegen

1. Python-Modul in `custom_components/copilot_ha/` anlegen
2. Entity-Plattform (sensor, button, etc.) implementieren
3. In `__init__.py` PLATFORMS-Liste eintragen (falls neue Plattform)
4. Optional: ModuleRegistry-Plugin via `core/module.py` Basisklasse

### Services

`services_setup.py` + `services.yaml` registrieren HA-Services unter `copilot_ha.*`:
- `copilot_ha.send_event` — Event an Core weiterleiten
- `copilot_ha.trigger_brain_sync` — Brain Graph Sync ausloesen
- etc.

---

## Hinweise fuer KI-Assistenten

- **Dual-Repo**: Aenderungen an der API muessen in beiden Repos (core + ha) synchron sein
- **Version Sync**: `VERSION`, `manifest.json` in HA MUSS mit Core-Version uebereinstimmen
- Domain ist `copilot_ha`, aber User-facing Name ist "PilotSuite"
- `MAIN_DEVICE_IDENTIFIER = "styx_hub"` — alle Entities gehoeren zu diesem Device
- Legacy-Identifiers (`copilot_ha`, `copilot_hub`, `pilotsuite_hub`) werden fuer Migration unterstuetzt
- Dashboard-Pfad: `pilotsuite-styx/` (Primary) oder `copilot_ha/` (Legacy)
- Tests: Python in `tests/`, JS in `tests/*.test.js`, E2E in `tests/e2e/`
- Dokumentation in Deutsch bevorzugt
- Commit-Messages: `feat:`, `fix:`, `chore:`, `release:` Prefix

### Projektprinzipien

| Prinzip | Bedeutung |
|---------|-----------|
| **Local-first** | Alles lokal, kein Cloud-API-Call |
| **Privacy-first** | PII-Redaktion, bounded Storage, opt-in |
| **Governance-first** | Vorschlaege vor Aktionen, Human-in-the-Loop |
| **Thin Client** | HA-Integration ist duenn, Logik lebt im Core |

---

## Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `custom_components/copilot_ha/__init__.py` | Integration Entry Point (async_setup_entry) |
| `custom_components/copilot_ha/const.py` | Domain, Constants, Data Keys |
| `custom_components/copilot_ha/core/runtime.py` | CopilotRuntime + ModuleRegistry |
| `custom_components/copilot_ha/config_flow.py` | Config Flow Coordinator |
| `custom_components/copilot_ha/connection_config.py` | Core-Verbindungs-Resolver |
| `custom_components/copilot_ha/entity.py` | Basis-Entity-Klasse |
| `custom_components/copilot_ha/sensor.py` | Haupt-Sensoren |
| `custom_components/copilot_ha/conversation.py` | HA Conversation Agent |
| `custom_components/copilot_ha/services_setup.py` | HA Service-Registration |
| `custom_components/copilot_ha/manifest.json` | HACS/HA Manifest |
| `custom_components/copilot_ha/dashboard/pilotsuite_dashboard_v14.yaml` | Dashboard YAML (3-Tab) |
| `custom_components/copilot_ha/dashboard/card_generator.py` | Dashboard YAML Generator (6-Tab) |
| `custom_components/copilot_ha/sensors/zone_presence_trigger.py` | Zone Praesenz Trigger Sensoren |
| `custom_components/copilot_ha/config_options_flow.py` | Options Flow (inkl. Automation-Modi) |
| `custom_components/copilot_ha/coordinator.py` | Coordinator mit Sonos/Zone/Presence APIs |
| `hacs.json` | HACS Repository Config |
| `VERSION` | Aktuelle Version (muss mit Core synchron sein) |
