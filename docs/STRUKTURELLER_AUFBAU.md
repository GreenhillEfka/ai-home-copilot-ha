# PilotSuite Styx HA -- Struktureller Aufbau

**Version:** 14.6.5 | **Stand:** 2026-03-16

Dieses Dokument beschreibt die Verzeichnisstruktur, Dateikategorien,
Plattformen, Datenfluss und Speichermechanismen der PilotSuite Styx
Home Assistant Integration.

---

## Inhaltsverzeichnis

1. [Verzeichnisstruktur](#verzeichnisstruktur)
2. [Dateikategorien](#dateikategorien)
3. [Plattform-Uebersicht](#plattform-uebersicht)
4. [Datenfluss-Architektur](#datenfluss-architektur)
5. [Storage-Dateien](#storage-dateien)
6. [Custom Lovelace Cards](#custom-lovelace-cards)
7. [Dashboard-System](#dashboard-system)
8. [Config Flow Architektur](#config-flow-architektur)
9. [API-Schicht](#api-schicht)

---

## Verzeichnisstruktur

```
pilotsuite-styx-ha/
|
|-- CLAUDE.md                      Projektrichtlinien fuer KI-Assistenten
|-- CHANGELOG.md                   Aenderungshistorie
|-- README.md                      Projekt-Readme
|-- RELEASE_NOTES.md               Release-Notizen
|-- VERSION                        Aktuelle Version (14.6.5)
|-- hacs.json                      HACS Repository-Konfiguration
|-- conftest.py                    Pytest Root-Konfig (path-injection)
|-- icon.png / logo.png            Branding-Assets (Root)
|
|-- custom_components/
|   +-- copilot_ha/                === HAUPTVERZEICHNIS DER INTEGRATION ===
|       |
|       |-- __init__.py            Entry Point: async_setup, async_setup_entry
|       |-- const.py               Domain, Konstanten, Signale, Data-Keys
|       |-- manifest.json          HA/HACS Manifest (Version, Dependencies)
|       |-- entity.py              CopilotBaseEntity Basisklasse
|       |-- entity_profile.py      Entity-Profil-Ermittlung (full vs. minimal)
|       |-- coordinator.py         CopilotDataUpdateCoordinator + API-Client
|       |-- connection_config.py   Core-Verbindungs-Resolver (Fallback-Kette)
|       |-- core_endpoint.py       URL-Builder + Kandidaten-Host-Liste
|       |
|       |-- VERSION                Integration-Version (14.6.5)
|       |-- icon.png / icon@2x.png Integration-Icon
|       |-- logo.png               Integration-Logo
|       |-- icons.json             MDI-Icon-Zuordnungen
|       |-- strings.json           UI-Strings (EN)
|       |-- services.yaml          HA Service-Definitionen
|       |
|       |-- ===== CONFIG FLOW =====
|       |-- config_flow.py         Duenner Coordinator (importiert Steps)
|       |-- config_helpers.py      CSV-Utils, Konstanten, Validierung
|       |-- config_schema_builders.py  Voluptuous Schema-Builder
|       |-- config_wizard_steps.py     7-Schritt-Wizard-Handler
|       |-- config_zones_flow.py       Zone-Management-Flow
|       |-- config_options_flow.py     OptionsFlowHandler (nach Setup)
|       |-- config_snapshot_flow.py    Config-Snapshot-Flow
|       |-- config_snapshot_store.py   Snapshot-Persistenz
|       |-- config_snapshot.py         Snapshot-Logik
|       |-- config_sync.py            Config-Synchronisation
|       |-- config_tags_flow.py        Entity-Tags-Flow
|       |
|       |-- ===== ENTITY-PLATTFORMEN =====
|       |-- sensor.py              Haupt-Sensor-Setup (50+ Sensoren)
|       |-- binary_sensor.py       Binary-Sensor-Setup
|       |-- button.py              Button-Setup (Wrapper)
|       |-- switch.py              Switch-Setup (Zone-Automations)
|       |-- number.py              Number-Setup
|       |-- select.py              Select-Setup
|       |-- text.py                Text-Entity-Setup
|       |-- conversation.py        HA Conversation Agent (Styx)
|       |-- stt.py                 Speech-to-Text (Core LLM)
|       |-- tts.py                 Text-to-Speech (Core LLM)
|       |
|       |-- ===== BUTTON-MODULE =====
|       |-- button_base.py         Button-Basisklasse
|       |-- button_camera.py       Camera-Dashboard-Buttons
|       |-- button_debug.py        Debug-Buttons (Haupt)
|       |-- button_debug_brain.py  Brain-Graph-Debug
|       |-- button_debug_core.py   Core-Debug
|       |-- button_debug_debug_controls.py  Debug-Steuerung
|       |-- button_debug_forwarder.py  Forwarder-Debug
|       |-- button_debug_ha_errors.py  HA-Error-Debug
|       |-- button_debug_logs.py   Log-Debug
|       |-- button_debug_misc.py   Verschiedene Debug-Buttons
|       |-- button_media.py        Medien-Buttons (Volume, Mute)
|       |-- button_safety_backup.py  Safety-Backup-Buttons
|       |-- button_system.py       System-Buttons
|       |-- button_tag_registry.py Tag-Registry-Sync
|       |-- button_update_check.py Version-Check-Buttons
|       |-- button_update_rollback.py  Rollback-Buttons
|       |
|       |-- ===== KERN-FUNKTIONALITAET =====
|       |-- webhook.py             Core->HA Webhook-Empfaenger
|       |-- suggest.py             Suggestion/Candidate-System
|       |-- suggestion_panel.py    Suggestion-Panel-Services
|       |-- search_integration.py  Quick-Search HA-Services
|       |-- blueprints.py          Blueprint-Installation
|       |-- diagnostics.py         HA-Diagnostik-Export
|       |-- lovelace_resources.py  Card-Resource-Registration
|       |-- services_setup.py      Global-Service-Registration
|       |-- agent_auto_config.py   Auto-Config Styx als Conversation Agent
|       |-- privacy.py             Privacy-Utilities
|       |-- storage.py             Allgemeine Storage-Utilities
|       |
|       |-- ===== HABITUS-ZONEN =====
|       |-- habitus_zones_store_v2.py      Zone-Store v2 (HA Storage)
|       |-- habitus_zones_entities_v2.py   Zone-Entities (Sensoren, Buttons)
|       |-- habitus_zone_aggregates.py     Zone-Durchschnitt-Sensoren
|       |-- habitus_dashboard.py           Zonen-Dashboard-Generator
|       |-- habitus_dashboard_store.py     Dashboard-Persistenz
|       |-- habitus_dashboard_entities.py  Dashboard-Entities
|       |-- habitus_dashboard_cards.py     Zonen-Dashboard-Cards
|       |-- habitus_dashboard_cards_entities.py  Card-Entities
|       |-- habitus_miner_entities.py      Miner-Sensoren
|       |-- zone_auto_setup.py             Auto-Zonen aus HA Areas
|       |-- zone_detector.py               Zonen-Eintritts-Erkennung
|       |-- zone_automation_entities.py    Zone-Automations-Switches
|       |-- zone_entity_select.py          Zone-Entity-Auswahl
|       |-- zone_energy_devices.py         Energie-Geraete pro Zone
|       |
|       |-- ===== BRAIN / MOOD / NEURONEN =====
|       |-- brain_graph_sync.py    Brain-Graph-Sync-Service
|       |-- brain_graph_viz.py     Brain-Graph-Visualisierung
|       |-- brain_graph_panel.py   Brain-Graph Custom Panel
|       |-- mood_store.py          Mood-Persistenz
|       |-- mood_dashboard.py      Mood-Dashboard-Generator
|       |-- module_connector.py    Inter-Modul-Signale
|       |-- neuron_feed_store.py   Neuron-Feed-Persistenz
|       |-- neuron_feed_entities.py  Neuron-Feed-Entities
|       |
|       |-- ===== KONTEXT-MODULE =====
|       |-- media_context.py           Media-Kontext v1 (read-only)
|       |-- media_context_v2.py        Media-Kontext v2 (Zonen + Volume)
|       |-- media_context_v2_setup.py  v2 Setup
|       |-- media_context_v2_entities.py  v2 Entities
|       |-- media_entities.py          Media-Sensoren
|       |-- media_setup.py             Media-Context v1 Setup
|       |-- ml_context.py              ML-Context-Coordinator
|       |-- unifi_context.py           UniFi-Kontext-Coordinator
|       |-- unifi_context_entities.py  UniFi-Entities
|       |-- weather_context.py         Weather-Context-Coordinator
|       |-- weather_context_entities.py  Weather-Entities
|       |-- energy_context.py          Energy-Context-Coordinator
|       |-- energy_context_entities.py Energy-Entities
|       |-- calendar_context.py        Calendar-Context
|       |-- collective_intelligence.py Collective Intelligence
|       |-- cross_home_sync.py         Multi-Home-Sync
|       |
|       |-- ===== ENTITIES (SPEZIELL) =====
|       |-- camera_entities.py         Camera-Entities (Motion, Presence)
|       |-- camera_dashboard.py        Camera-Dashboard
|       |-- core_v1.py                 Core API v1 Capabilities
|       |-- core_v1_entities.py        Core API v1 Status-Sensor
|       |-- autonomy_entities.py       Autonomie-Entities
|       |-- frontend_entities.py       Frontend-Entities
|       |-- homekit_entities.py        HomeKit-Entities
|       |-- inventory_entities.py      Inventar-Entities
|       |-- inventory.py / inventory_kernel.py / inventory_store.py
|       |-- knowledge_graph_entities.py  KG-Entities
|       |-- ops_runbook_entities.py    Ops-Runbook-Entities
|       |-- ops_runbook.py / ops_runbook_store.py
|       |-- pipeline_health_entities.py  Pipeline-Health
|       |-- forwarder_quality_entities.py  Forwarder-Qualitaet
|       |-- systemhealth_entities.py   System-Health-Entities
|       |-- systemhealth_report.py     System-Health-Bericht
|       |-- systemhealth_store.py      System-Health-Store
|       |-- home_alerts_sensor.py      Home-Alerts-Sensor
|       |-- multi_user_preferences.py  MUPL Hauptmodul
|       |-- multi_user_preferences_entities.py  MUPL-Entities
|       |-- user_preference_module.py  User-Preference-Modul
|       |
|       |-- ===== MESH / NETZWERK =====
|       |-- mesh_monitoring.py         ZWave/Zigbee Mesh-Health
|       |-- mesh_dashboard.py          Mesh-Topologie-Sensoren
|       |
|       |-- ===== SONSTIGE =====
|       |-- entity_tags_store.py       Entity-Tags-Persistenz
|       |-- tag_registry.py            Tag-Registry
|       |-- tag_sync.py                Tag-Synchronisation
|       |-- seed_adapter.py / seed_store.py  Suggestion-Seeds
|       |-- entity_discovery.py        Entity-Erkennung
|       |-- error_tracking.py          Error-Tracking
|       |-- devlog_push.py             DevLog an Core pushen
|       |-- ha_errors_digest.py        HA-Fehler-Digest
|       |-- log_fixer.py / log_store.py  Log-Utilities
|       |-- conflict_resolution.py     Konflikterkennung
|       |-- conversation_ids.py        Conversation-ID-Normalisierung
|       |-- debug.py                   Debug-Mode-Sensor
|       |-- forwarder_n3.py            Forwarder N3
|       |-- issues.py                  HA Issues/Repairs
|       |-- overview_store.py          Overview-Store
|       |-- pilotsuite_dashboard.py    PilotSuite-Dashboard-Generator
|       |-- pilotsuite_dashboard_store.py  Dashboard-Persistenz
|       |-- repairs.py / repairs_enhanced.py / repairs_blueprints.py
|       |-- safety_backup.py           Safety-Backup
|       |-- scene_store.py             Scene-Persistenz
|       |-- setup_wizard.py            Setup-Wizard-Logik
|       |-- update_rollback.py         Update-Rollback
|       |-- vector_client.py           Vector-DB-Client
|       |-- inventory_publish.py       Inventar-Veroeffentlichung
|       |
|       |-- ===== UNTERVERZEICHNISSE =====
|       |
|       |-- core/                      Runtime-Kern
|       |   |-- __init__.py
|       |   |-- runtime.py             CopilotRuntime (Singleton)
|       |   |-- registry.py            ModuleRegistry (Factories)
|       |   |-- module.py              CopilotModule (Protocol)
|       |   |-- module_registry.py     ModuleRegistry (SQLite, Autonomie)
|       |   |-- performance.py         TTLCache, Performance-Hilfsmittel
|       |   |-- retry_helpers.py       Retry-Logik
|       |   |-- error_helpers.py       Fehler-Formatierung
|       |   |
|       |   |-- modules/              37 Module (siehe MODULBESCHREIBUNG.md)
|       |   |   |-- legacy.py          LegacyModule
|       |   |   |-- performance_scaling.py
|       |   |   |-- events_forwarder.py
|       |   |   |-- history_backfill.py
|       |   |   |-- dev_surface.py
|       |   |   |-- habitus_miner.py
|       |   |   |-- ops_runbook.py
|       |   |   |-- unifi_module.py
|       |   |   |-- brain_graph_sync.py
|       |   |   |-- candidate_poller.py
|       |   |   |-- media_context_module.py
|       |   |   |-- mood_module.py
|       |   |   |-- mood_context_module.py
|       |   |   |-- energy_context_module.py
|       |   |   |-- unifi_context_module.py
|       |   |   |-- weather_context_module.py
|       |   |   |-- knowledge_graph_sync.py
|       |   |   |-- ml_context_module.py
|       |   |   |-- camera_context_module.py
|       |   |   |-- quick_search.py
|       |   |   |-- voice_context.py
|       |   |   |-- home_alerts_module.py
|       |   |   |-- character_module.py
|       |   |   |-- waste_reminder_module.py
|       |   |   |-- birthday_reminder_module.py
|       |   |   |-- entity_tags_module.py
|       |   |   |-- person_tracking_module.py
|       |   |   |-- frigate_bridge.py
|       |   |   |-- scene_module.py
|       |   |   |-- homekit_bridge.py
|       |   |   |-- calendar_module.py
|       |   |   |-- licht_module.py
|       |   |   |-- helligkeit_module.py
|       |   |   |-- heiz_module.py
|       |   |   |-- bewegung_module.py
|       |   |   |-- praesenz_module.py
|       |   |   |-- frontend_module.py
|       |   |   +-- (weitere: interface.py, module.py,
|       |   |        performance_guardrails.py,
|       |   |        user_preference_module.py)
|       |   |
|       |   |-- character/             Charakter-Persoenlichkeit
|       |   |   |-- __init__.py
|       |   |   |-- models.py          Charakter-Datenmodelle
|       |   |   +-- service.py         Charakter-Service
|       |   |
|       |   |-- mupl/                  Multi-User Preference Learning
|       |   |   |-- __init__.py
|       |   |   +-- action_attribution.py  Aktions-Attribution
|       |   |
|       |   +-- user_hints/            User Hints System
|       |       |-- __init__.py
|       |       |-- models.py          Hint-Datenmodelle
|       |       +-- service.py         Hint-Service
|       |
|       |-- api/                       API-Client-Schicht
|       |   |-- __init__.py            CopilotApiClient, CopilotApiError
|       |   |-- models.py             API-Datenmodelle
|       |   |-- knowledge_graph.py    KnowledgeGraphClient
|       |   +-- user_preference.py    User-Preference-API
|       |
|       |-- sensors/                   60+ spezialisierte Sensoren
|       |   |-- __init__.py
|       |   |-- mood_sensor.py         Mood, Confidence, Neuron Activity
|       |   |-- neuron_dashboard.py    Neuron Dashboard, Mood History
|       |   |-- voice_context.py       Voice Context, Voice Prompt
|       |   |-- energy_insights.py     Energy Insight
|       |   |-- energy_sensors.py      Energy-Kernsensoren
|       |   |-- calendar_sensors.py    Kalender-Sensoren
|       |   |-- presence_sensors.py    Praesenz-Sensoren
|       |   |-- activity_sensors.py    Aktivitaets-Sensoren
|       |   |-- anomaly_detection_sensor.py  Anomalie-Sensor
|       |   |-- automation_suggestion_sensor.py  Automations-Vorschlaege
|       |   |-- brain_activity_sensor.py  Brain-Aktivitaet
|       |   |-- comfort_index_sensor.py  Komfort-Index
|       |   |-- hub_dashboard_sensor.py  Hub-Dashboard
|       |   |-- zone_presence_trigger.py  Zone-Praesenz-Trigger
|       |   +-- (50+ weitere spezialisierte Sensoren)
|       |
|       |-- dashboard/                 Dashboard-YAML-Templates
|       |   |-- __init__.py
|       |   |-- card_generator.py      Dynamischer Dashboard-Generator
|       |   |-- pilotsuite_dashboard_v14.yaml   Dashboard v14
|       |   |-- pilotsuite_dashboard_v13_3tab.yaml  Dashboard v13 (3-Tab)
|       |   |-- pilotsuite_dashboard_v13.yaml   Dashboard v13
|       |   +-- example_dashboard_modules.yaml
|       |
|       |-- dashboard_cards/           Dashboard-Card-Module
|       |   |-- data_classes.py        Datenmodelle
|       |   |-- home_alerts_card.py    Home-Alerts-Card
|       |   |-- media_context_card.py  Media-Card
|       |   |-- zone_context_card.py   Zone-Card
|       |   |-- preference_input_card.py  Preference-Card
|       |   |-- user_hints_card.py     User-Hints-Card
|       |   |-- user_together_card.py  Multi-User-Card
|       |   +-- (Unterverzeichnisse: energy, interactive, mesh,
|       |        mobile, overview, presence, weather)
|       |
|       |-- www/                       Lovelace Custom Cards (JS)
|       |   |-- styx-card-base.js      Basis-Klasse fuer alle Cards
|       |   |-- styx-chat-card.js      Chat-Card
|       |   |-- styx-suggestions-card.js  Suggestions-Card
|       |   |-- styx-error-card.js     Error-Card
|       |   |-- styx-household-card.js Household-Card
|       |   |-- styx-mood-card.js      Mood-Card
|       |   |-- styx-brain-card.js     Brain-Card
|       |   |-- styx-habitus-card.js   Habitus-Card
|       |   |-- styx-zone-card.js      Zone-Card
|       |   |-- styx-neural-card.js    Neural-Card
|       |   +-- zone_card_yaml.md      Zone-Card-Beispiel
|       |
|       |-- frontend/                  Frontend-JS-Module
|       |   |-- habitus-zone-card.js   Habitus-Zone-Card
|       |   |-- module-control-card.js Module-Control-Card
|       |   |-- neuron-layer-card.js   Neuron-Layer-Card
|       |   +-- styx-dashboard-card.js Styx-Dashboard-Card
|       |
|       |-- ml/                        ML-Subsystem
|       |   |-- __init__.py
|       |   |-- base.py               ML-Basis-Klassen
|       |   |-- inference/             Inferenz-Module
|       |   |-- patterns/             Muster-Erkennung
|       |   |-- training/             Trainings-Logik
|       |   +-- tests/                ML-Unit-Tests
|       |
|       |-- services/                  Service-Implementierungen
|       |   |-- habitus_dashboard_cards_service.py
|       |   +-- user_preference_services.py
|       |
|       |-- entities/                  Entitaets-Definitionen
|       |   +-- user_preference_entities.py
|       |
|       |-- data/                      Statische Daten
|       |   +-- zones_config.json      9 Habitus-Zonen, 141 Entities
|       |
|       |-- translations/              Uebersetzungen
|       |   |-- de.json               Deutsch
|       |   +-- en.json               Englisch
|       |
|       |-- blueprints/               HA Automation Blueprints
|       |   +-- automation/           Automatisierungs-Vorlagen
|       |
|       +-- requirements-dev.txt      Entwicklungs-Abhaengigkeiten
|
|-- tests/                            Python-Tests
|-- docs/                             Dokumentation (30+ Dateien)
|-- dashboard/                        Externe Dashboard-Dateien
|-- brand/                            Branding-Assets
|-- pilotsuite_ops/                   Operations-Tools
|-- sdk/                              SDK-Dateien
+-- skills/                           Skill-Definitionen
```


---

## Dateikategorien

### Uebersicht nach Funktion

| Kategorie | Anzahl | Verzeichnis / Pattern |
|-----------|--------|----------------------|
| Module (CopilotModule) | 37 | `core/modules/*.py` |
| Sensoren (spezialisiert) | 60+ | `sensors/*.py` |
| Button-Module | 15 | `button_*.py` |
| Entity-Plattformen | 9 | `sensor.py`, `binary_sensor.py`, etc. |
| Config-Flow-Dateien | 10 | `config_*.py` |
| Habitus-Zonen | 12 | `habitus_*.py`, `zone_*.py` |
| Dashboard | 8 | `dashboard/`, `dashboard_wiring.py` |
| API-Client | 4 | `api/` |
| ML-Subsystem | 10+ | `ml/` |
| Custom Lovelace Cards | 10 | `www/styx-*.js` |
| Frontend JS | 4 | `frontend/*.js` |
| Uebersetzungen | 2 | `translations/` |

### Datei-Typ-Verteilung

| Typ | Beschreibung | Anzahl (ca.) |
|-----|-------------|:---:|
| `.py` (Python) | Integration Backend | 200+ |
| `.js` (JavaScript) | Lovelace Cards + Frontend | 14 |
| `.yaml` | Dashboard-Templates, Services, API-Specs | 10+ |
| `.json` | Manifest, Strings, Icons, Config | 6 |
| `.md` | Dokumentation | 30+ |


---

## Plattform-Uebersicht

Die Integration registriert 9 HA-Entity-Plattformen:

```
+-------------------------------------------------------------------+
|                    HA Entity-Plattformen                            |
+-------------------------------------------------------------------+
|                                                                     |
|  sensor          50+ Sensoren: Brain Score, Mood, Neurons,         |
|  (sensor.py)     Energy, Media, Zone Aggregates, Forwarder,        |
|                  Habitus Miner, Pipeline Health, System Health,     |
|                  Voice, Calendar, Comfort, Anomaly, ...             |
|                                                                     |
|  binary_sensor   Online-Status, Musik aktiv, TV aktiv,             |
|  (binary_sensor.py) Forwarder Connected, ZWave/Zigbee Mesh,       |
|                  Camera Motion/Presence, UniFi-Sensoren             |
|                                                                     |
|  button          Debug-Buttons (Brain, Core, Forwarder, Logs),     |
|  (button.py)     Camera Dashboard, Tag Sync, Update Check,         |
|                  Rollback, Safety Backup, Media Volume,             |
|                  Zone Validate/Sync/Reload                          |
|                                                                     |
|  switch          Zone-Automations-Switches:                         |
|  (switch.py)     Licht Auto, Musik Auto, Musik Follow,             |
|                  View-Toggle-Switches, Neuron-Feed-Switches         |
|                                                                     |
|  number          Konfigurierbare Zahlenwerte                        |
|  (number.py)     (z.B. Polling-Intervalle, Schwellenwerte)          |
|                                                                     |
|  select          Dropdown-Auswahlen                                 |
|  (select.py)     (z.B. Charakter-Modus, Debug-Level)               |
|                                                                     |
|  text            Text-Entities                                      |
|  (text.py)       (Legacy, groesstenteils migriert)                  |
|                                                                     |
|  conversation    Styx Conversation Agent                            |
|  (conversation.py) Proxy zu Core OpenAI-kompatiblem Endpoint       |
|                                                                     |
|  stt             Speech-to-Text via Core LLM                       |
|  (stt.py)        Audio-Upload -> Core -> Text                       |
|                                                                     |
|  tts             Text-to-Speech via Core LLM                       |
|  (tts.py)        Text -> Core -> Audio                              |
|                                                                     |
+-------------------------------------------------------------------+
```

### Entity-Basis-Klassen

| Klasse | Datei | Beschreibung |
|--------|-------|-------------|
| `CopilotBaseEntity` | `entity.py` | CoordinatorEntity-Wrapper, DeviceInfo "Styx Hub" |
| `CopilotStyxEntity` | `entity.py` | Erweiterte Basis fuer Styx-Entities |

Alle Entities gehoeren zum Device "Styx Hub" mit dem Identifier `styx_hub`.
Legacy-Identifier (`copilot_ha`, `copilot_hub`, `pilotsuite_hub`) werden
fuer Migration unterstuetzt.


---

## Datenfluss-Architektur

### Hauptdatenfluss

```
+------------------+     +-----------------+     +------------------+
|   Home Assistant |     |   copilot_ha    |     | PilotSuite Core  |
|   (HA Runtime)   |     |  (Integration)  |     |  (Add-on :8909)  |
+--------+---------+     +--------+--------+     +--------+---------+
         |                        |                        |
    Config Entry          async_setup_entry           REST API
         |                        |                   (Flask)
         v                        v                        |
    +---------+          +------------------+              |
    | Options |--------->| merged_entry_    |              |
    |  Flow   |          | config()         |              |
    +---------+          +--------+---------+              |
                                  |                        |
                                  v                        |
                         +------------------+              |
                         | CopilotRuntime   |              |
                         | (37 Module laden)|              |
                         +--------+---------+              |
                                  |                        |
              +-------------------+-------------------+    |
              |                   |                   |    |
              v                   v                   v    |
     +--------+------+  +--------+------+  +---------+--+ |
     | LegacyModule  |  | EventsForw.   |  | BrainGraph | |
     | (Coordinator) |  | (HA->Core)    |  | Sync       | |
     +--------+------+  +--------+------+  +---------+--+ |
              |                   |                   |    |
              v                   v                   v    v
     +--------+------+  +--------+------+  +---------+--------+
     | Coordinator   |  | POST /api/v1/ |  | POST /api/v1/    |
     | (120s Poll)   |  | events        |  | graph            |
     +--------+------+  +---------------+  +------------------+
              |
              v
     +--------+------+
     | HA Entities   |
     | (sensor.*,    |
     |  binary_*,    |
     |  button.*,    |
     |  switch.*, ..) |
     +---------------+
```

### Detaillierter Datenfluss

```
1. CONFIG ENTRY
   +-----------+     +-----------+     +------------------+
   | Discovery |---->| Wizard    |---->| ConfigEntry.data |
   | (mDNS,    |     | (7 Steps) |     | + .options       |
   |  Probing) |     +-----------+     +--------+---------+
   +-----------+                                |
                                                v
2. VERBINDUNGSAUFBAU            +------------------------------+
                                | resolve_core_connection()     |
                                | (Entry -> Env -> localhost)   |
                                | + discover_reachable_endpoint |
                                | + fetch_setup_token           |
                                +---------------+--------------+
                                                |
3. COORDINATOR                                  v
                                +------------------------------+
                                | CopilotDataUpdateCoordinator |
                                | - api: CopilotApiClient      |
                                | - Polling: 120s              |
                                | - Endpoints: Failover-Kette  |
                                +---------------+--------------+
                                                |
4. DATENABHOLUNG                                v
   +--------------------+  +--------------------+  +------------------+
   | GET /health        |  | GET /mood          |  | GET /api/v1/     |
   | (Version, Status)  |  | (Zone Moods)       |  | neurons          |
   +--------------------+  +--------------------+  +------------------+
              |                      |                      |
              v                      v                      v
5. ENTITY-UPDATE            +------------------------------+
                            | coordinator.data = {         |
                            |   "ok": True,                |
                            |   "version": "14.6.5",       |
                            |   "mood": {...},             |
                            |   "neurons": {...},          |
                            |   "dominant_mood": "relaxed",|
                            |   "habit_summary": {...},    |
                            |   ...                        |
                            | }                            |
                            +---------------+--------------+
                                            |
6. HA ENTITIES                              v
   +------------+  +---------------+  +------------------+
   | MoodSensor |  | NeuronDash.   |  | ForwarderQueue   |
   | BrainScore |  | SuggestionS.  |  | DroppedTotal     |
   | Confidence |  | EnergyInsight |  | ErrorStreak      |
   +------------+  +---------------+  +------------------+
```

### Kommunikationskanaele

| Kanal | Richtung | Beschreibung | Intervall |
|-------|----------|-------------|-----------|
| REST Polling | HA -> Core | Coordinator holt Daten | 120s |
| Event Forwarding | HA -> Core | State-Changes an Core | Konfig. Flush |
| Webhook Push | Core -> HA | Mood, Neuron, Suggestion Updates | Echtzeit |
| Polling Fallback | HA -> Core | Wenn Webhook nicht verfuegbar | 120s |
| History Backfill | HA -> Core | Einmalig bei Erst-Setup | Einmalig |
| Candidate Poll | HA -> Core | Pending Candidates holen | 5 Min |

### Timeout-Konfiguration

| Endpoint-Typ | Timeout | Beispiel |
|-------------|---------|---------|
| Standard REST | 10s | /health, /mood, /neurons |
| Audio (STT/TTS) | 30s | /v1/audio/transcriptions |
| Chat Completions | 90s | /v1/chat/completions |


---

## Storage-Dateien

Die Integration nutzt HA Storage (`.storage/`) fuer persistente Daten:

| Storage-Key | Beschreibung | Datei |
|-------------|-------------|-------|
| `copilot_ha.habitus_zones_v2.{entry_id}` | Habitus-Zonen v2 (Zone-IDs, Entity-IDs, Metadata) | `habitus_zones_store_v2.py` |
| `copilot_ha.entity_tags.{entry_id}` | Entity-Tags (manuell + auto) | `entity_tags_store.py` |
| `copilot_ha.suggestions.{entry_id}` | Vorschlags-Persistenz | `suggest.py` |
| `copilot_ha.events_forwarder.{entry_id}` | Persistente Event-Queue + Seen-Cache | `events_forwarder.py` |
| `copilot_ha.history_backfill.{entry_id}` | Backfill-Completion-Status | `history_backfill.py` |
| `copilot_ha.habitus_miner` | Miner Event-Buffer + Discovered Rules | `habitus_miner.py` |
| `copilot_ha.character_config` | Charakter-Konfiguration | `character_module.py` |
| `copilot_ha.homekit_zones` | HomeKit-Zone-Toggles | `homekit_bridge.py` |
| `copilot_ha.home_alerts` | Quittierte Alerts + Historie | `home_alerts_module.py` |
| `copilot_ha.frontend_view_toggles` | Dashboard-View-Toggles (8 Views) | `frontend_module.py` |
| `copilot_ha.pilotsuite_dashboard` | PilotSuite-Dashboard-State | `pilotsuite_dashboard_store.py` |
| `copilot_ha.habitus_dashboard` | Habitus-Dashboard-State | `habitus_dashboard_store.py` |
| `copilot_ha.ops_runbook` | Runbook-Daten | `ops_runbook_store.py` |
| `copilot_ha.systemhealth` | System-Health-Daten | `systemhealth_store.py` |
| `copilot_ha.overview` | Overview-Daten | `overview_store.py` |
| `copilot_ha.scene_store` | Szenen-Daten | `scene_store.py` |
| `copilot_ha.mood_store` | Mood-Persistenz | `mood_store.py` |
| `copilot_ha.neuron_feed` | Neuron-Feed-State | `neuron_feed_store.py` |
| `copilot_ha.inventory` | Inventar-Daten | `inventory_store.py` |
| `copilot_ha.config_snapshot` | Config-Snapshots | `config_snapshot_store.py` |
| `copilot_ha.log_store` | Log-Persistenz | `log_store.py` |

### SQLite-Datenbank (Core-Backend)

| Pfad | Beschreibung |
|------|-------------|
| `/data/module_states.db` | ModuleRegistry: Modul-Zustaende (active/learning/off) |


---

## Custom Lovelace Cards

Die Integration liefert 10 JavaScript-Dateien fuer Custom Lovelace Cards
im Verzeichnis `www/`:

| Datei | Card-Tag | Beschreibung |
|-------|----------|-------------|
| `styx-card-base.js` | (Basis-Klasse) | Gemeinsame Basis fuer alle Styx-Cards: Ingress-Pfad-Erkennung, Theme-Integration, Common Styles |
| `styx-chat-card.js` | `styx-chat-card` | Chat-Interface zum Styx Conversation Agent. Nachrichten-Verlauf, Eingabefeld, Markdown-Rendering. |
| `styx-suggestions-card.js` | `styx-suggestions-card` | Zeigt Automations-Vorschlaege an. Accept/Reject/Snooze-Buttons, Quell-Info. |
| `styx-error-card.js` | `styx-error-card` | Fehler-Uebersicht: letzte Fehler, Error-Digest, Gruppen. |
| `styx-household-card.js` | `styx-household-card` | Haushaltsuebersicht: Bewohner, Praesenz, Kalender, Abfall. |
| `styx-mood-card.js` | `styx-mood-card` | Stimmungs-Visualisierung: aktuelle Mood, Confidence, Historie. |
| `styx-brain-card.js` | `styx-brain-card` | Brain-Graph-Visualisierung: Knoten, Kanten, Aktivitaet. |
| `styx-habitus-card.js` | `styx-habitus-card` | Habitus-Zonen-Uebersicht: Zone-Status, Aggregationen. |
| `styx-zone-card.js` | `styx-zone-card` | Einzelzonen-Detail: Licht, Klima, Praesenz, Automation. |
| `styx-neural-card.js` | `styx-neural-card` | Neural-Dashboard: Neuron-Layers, Aktivitaet, Feed-Status. |

### Card-Registrierung

Cards werden via `lovelace_resources.py` automatisch als Lovelace-Ressourcen
registriert. Der Pfad wird relativ zum Integration-Verzeichnis aufgeloest:

```
/hacsfiles/copilot_ha/styx-chat-card.js
/hacsfiles/copilot_ha/styx-suggestions-card.js
...
```

### Frontend-Module (frontend/)

Zusaetzlich existieren 4 spezialisierte Frontend-Module:

| Datei | Beschreibung |
|-------|-------------|
| `habitus-zone-card.js` | Habitus-Zone-Card (Konfigurations-UI) |
| `module-control-card.js` | Modul-Steuerungs-Card (active/learning/off) |
| `neuron-layer-card.js` | Neuron-Layer-Visualisierung |
| `styx-dashboard-card.js` | Styx-Dashboard-Gesamt-Card |


---

## Dashboard-System

### Zwei Modi: YAML vs. Storage

```
+-----------------+     +------------------+
| YAML-Modus      |     | Storage-Modus    |
| (Legacy)        |     | (Standard)       |
+-----------------+     +------------------+
| - Erfordert     |     | - Sofort sichtbar|
|   HA-Restart    |     |   (kein Restart) |
| - Datei in      |     | - Gespeichert in |
|   pilotsuite-   |     |   HA .storage/   |
|   styx/         |     | - WebSocket API  |
| - Sidebar:      |     |   fuer Updates   |
|   ausgeblendet  |     | - 8 Views,       |
|                 |     |   17+ Cards      |
+-----------------+     +------------------+
         |                       |
         v                       v
  YAML-Dashboard          Storage-Dashboard
  (show_in_sidebar:       (Primaer-Dashboard)
   false)
```

### Storage-Dashboard Views (8 Views)

| Pfad | Titel | Inhalt |
|------|-------|--------|
| `styx` | Styx | Mood-Card, Brain-Card, Suggestions, Neural |
| `haushalt` | Haushalt | Household-Card, Kalender, Abfall, Personen |
| `zonen` | Zonen | Habitus-Zone-Cards, Zone-Details |
| `automation` | Automation | Automations-Vorschlaege, Szenen |
| `energie` | Energie | Energy-Insight, Verbrauch, Prognose |
| `musik` | Musik | Media-Context, Zonen-Musik, Volume |
| `ki` | KI | Brain-Graph, ML-Status, Anomalien |
| `chat` | Chat | Chat-Card (Conversation Agent) |

### Dashboard-Erzeugung

```
async_setup_entry()
    |
    +-- async_ensure_lovelace_dashboard_wiring()
    |   (Schreibt YAML-Snippet, versteckt in Sidebar)
    |
    +-- async_ensure_storage_dashboard()
    |   (Erstellt Storage-Dashboard via WebSocket API)
    |
    +-- async_generate_pilotsuite_dashboard()
    |   (Generiert PilotSuite Haupt-Dashboard)
    |
    +-- async_generate_habitus_zones_dashboard()
        (Generiert Habitus-Zonen-Dashboard)
```

### Dashboard-Dateien

| Datei | Beschreibung |
|-------|-------------|
| `dashboard/pilotsuite_dashboard_v14.yaml` | Aktuelles Dashboard-Template |
| `dashboard/pilotsuite_dashboard_v13.yaml` | Legacy v13 |
| `dashboard/pilotsuite_dashboard_v13_3tab.yaml` | Legacy v13 (3-Tab) |
| `dashboard/card_generator.py` | Dynamischer Dashboard-Generator (6 Tabs) |
| `dashboard_wiring.py` | Lovelace-Wiring (YAML-Modus) |
| `pilotsuite_dashboard.py` | PilotSuite-Dashboard-Generator (Storage) |
| `habitus_dashboard.py` | Zonen-Dashboard-Generator (Storage) |


---

## Config Flow Architektur

### 7-Schritt-Wizard

```
DISCOVERY -> ZONES -> ZONE_ENTITIES -> ENTITIES -> FEATURES -> NETWORK -> REVIEW
    |           |          |              |            |           |          |
    v           v          v              v            v           v          v
  Core-       Zone-     Entity-       Media-       Feature-    UniFi-     Zusammen-
  Erkennung   Verwalt.  Zuordnung     Player       Toggles     Config     fassung
  + Token     + Areas   pro Zone      Config       (Forwarder, (Network   + Anlegen
  Auto-Fetch  + Auto-                               Debug,      Monitor)
              Setup                                  MUPL, ...)
```

### Dateien

| Datei | Verantwortung |
|-------|-------------|
| `config_flow.py` | Duenner Coordinator, importiert Steps |
| `config_wizard_steps.py` | Wizard-Step-Handler (7 Steps) |
| `config_schema_builders.py` | Voluptuous Schema-Builder |
| `config_zones_flow.py` | Zone-Management + Helpers |
| `config_options_flow.py` | OptionsFlowHandler (nach Setup) |
| `config_helpers.py` | Constants, CSV-Utils, Validierung |
| `config_tags_flow.py` | Entity-Tags-Flow |
| `config_snapshot_flow.py` | Config-Snapshot-Flow |
| `config_sync.py` | Config-Synchronisation |


---

## API-Schicht

### Client-Architektur

```
api/__init__.py
    |
    +-- CopilotApiClient (Basis)
    |       |-- async_get(path)
    |       |-- async_post(path, data)
    |       +-- health_check()
    |
    +-- coordinator.py
            |
            +-- CopilotApiClient (Erweitert)
                    |-- Endpoint-Failover (mehrere base_urls)
                    |-- Automatisches Wechseln bei Fehler
                    +-- Timeout-Konfiguration pro Endpoint-Typ
```

### Failover-Kette

Der Coordinator probiert mehrere Endpoints in Reihenfolge:

```
1. Konfigurierter Host:Port (z.B. 192.168.30.18:8909)
2. Add-on Host (addon_slug, z.B. local-pilotsuite-core:8909)
3. host.docker.internal:8909
4. localhost:8909
```

Bei HTTP 404/405/408/429/5xx wird automatisch zum naechsten Endpoint gewechselt.
Auth-Fehler (401/403) loesen KEINEN Failover aus.

### Core API Endpoints (genutzt von HA)

| Endpoint | Methode | Beschreibung | Modul |
|----------|---------|-------------|-------|
| `/health` | GET | Health-Check + Version | Coordinator |
| `/mood` | GET | Zone-Moods | mood_context |
| `/api/v1/events` | POST | Event-Forwarding (Batches) | events_forwarder |
| `/api/v1/graph` | POST | Brain-Graph-Sync | brain_graph_sync |
| `/api/v1/candidates` | GET | Pending Candidates | candidate_poller |
| `/api/v1/neurons` | GET | Neuron-Daten | Coordinator |
| `/v1/chat/completions` | POST | Chat (OpenAI-kompatibel) | conversation |
| `/v1/audio/transcriptions` | POST | STT | stt |
| `/v1/audio/speech` | POST | TTS | tts |
| `/habitus/mine` | POST | Pattern Mining | habitus_miner |
| `/habitus/rules` | GET | Entdeckte Regeln | habitus_miner |
| `/habitus/reset` | POST | Cache-Reset | habitus_miner |


---

## Abhaengigkeiten (manifest.json)

```json
{
  "domain": "copilot_ha",
  "name": "PilotSuite",
  "integration_type": "hub",
  "iot_class": "local_push",
  "dependencies": [
    "conversation", "history", "http",
    "recorder", "stt", "tag", "tts", "webhook"
  ],
  "after_dependencies": ["assist_pipeline"],
  "config_flow": true,
  "version": "14.6.5"
}
```

Die Integration hat KEINE externen Python-Abhaengigkeiten (`requirements: []`).
Alle benoetigen Bibliotheken werden von HA selbst bereitgestellt (aiohttp, voluptuous, etc.).

### Minimale HA-Version

- Home Assistant >= 2024.1.0 (definiert in `hacs.json`)


---

## Versionierung

Die Version muss an 3 Stellen synchron sein:

| Datei | Pfad | Aktuell |
|-------|------|---------|
| `VERSION` | Repository-Root | 14.6.5 |
| `custom_components/copilot_ha/VERSION` | Integration | 14.6.5 |
| `custom_components/copilot_ha/manifest.json` | `"version"` | 14.6.5 |

Die Version muss IMMER synchron mit dem Core-Repository
(`pilotsuite-styx-core`) gehalten werden (Paired Releases).
