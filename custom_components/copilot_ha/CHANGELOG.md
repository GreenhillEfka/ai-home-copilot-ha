# Changelog

All notable changes to PilotSuite will be documented in this file.

## [Unreleased]

### Fixed
- Config/Reconfigure hotfix: `config_flow.py` now imports `merge_config_data(...)`, fixing a direct NameError/500 path in Configure/Reconfigure flows.
- Zone auto-setup hotfix: `zone_auto_setup.py` now imports `validate_mapping(...)` correctly, fixing a direct failure path behind `Failed to auto-create Habitus Zones`.
- Area→zone registry loading used during auto-setup now has an async helper (`async_load_area_zone_map`) so the file read can be moved off the HA event loop in async setup paths.

### Notes
- The earlier `button_update_check.py` blocking VERSION-read fix remains an important preserved runtime safeguard (`d5e46f42`).

## [15.0.14] - 2026-03-22

### Fixed
- HACS compatibility restored for versioned installs: root `hacs.json` added back and `zip_release` declared explicitly so HACS can validate and download tagged releases again
- Keeps the startup/import fix from `v15.0.13` (`HabitusZonesV2ModulesSensor` registration order)
- Published HA version files now all report `15.0.14`

## [15.0.13] - 2026-03-22

### Fixed
- Follow-up release on the actually fixed commit after `v15.0.12` was tagged remotely before the import-fix landed
- Home Assistant startup/import crash remains fixed: `HabitusZonesV2ModulesSensor` is registered after its class definition
- Published HA version files now all report `15.0.13`

## [15.0.12] - 2026-03-22

### Fixed
- Import crash on Home Assistant startup: `HabitusZonesV2ModulesSensor` is now registered only after its class definition, fixing `NameError: name "HabitusZonesV2ModulesSensor" is not defined` during `custom_components.copilot_ha.sensor` import
- Published HA version files realigned for this release: `VERSION`, `custom_components/copilot_ha/VERSION`, and `manifest.json` now all report `15.0.12`

## [15.0.10] - 2026-03-22

### Fixed
- Follow-up HACS release after the parallel `v15.0.9` tag collision so the cleaned package ships under a fresh, unambiguous release number
- Published HA version files now all report `15.0.10`

## [15.0.9] - 2026-03-22

### Fixed
- HACS package cleanup: removed stray `custom_components/pilotsuite_core` stub from the HA repository so HACS installs only the supported `copilot_ha` integration
- Version truth re-aligned: `VERSION`, `custom_components/copilot_ha/VERSION`, and `custom_components/copilot_ha/manifest.json` now all publish `15.0.9`
- Manifest docs URL normalized to the repository root (no `#readme` anchor dependency)

### Changed
- Release workflow now bumps the root and component VERSION files together with the manifest
- CI now verifies that the HA repository exposes exactly one HACS integration (`copilot_ha`)

## [15.0.5] - 2026-03-22

### Fixed
- `CopilotHaCoordinator` → `CopilotDataUpdateCoordinator` (import typo fix — blocked startup)
- styx-zone-card: read zone_modules from `sensor.copilot_ha_habitus_zones_v2_modules` (correct sensor)
- Zone entities exposed in `HabitusZonesSensor` extra_state_attributes
- styx-zone-card: memory leaks from orphan setTimeout poll timers
- Zone sync: send `name_de` instead of `name` in zone sync body

### Changed
- Config flow: add STEP_MODULES between NETWORK and REVIEW

## [15.0.4] - 2026-03-22

### Added
- Module Config section in per-zone dashboard views (Lovelace)

## [15.0.3] - 2026-03-21

### Fixed
- HACS metadata: remove legacy `hacs.json` — manifest.json with `hacs: default` sufficient
- styx-zone-card: correct entity name to `sensor.copilot_ha_habitus_zones`

## [15.0.2] - 2026-03-21

### Added
- `CoreVersionDiagnosticSensor`: surfaces HA addon vs live Core version mismatch in HA UI
  - native_value: `aligned` | `gap_HAvsCore` | `unreachable`
  - attributes: `ha_version`, `core_version`, `gap_description`, `recommendation`
- `HabitusZonesV2ModulesSensor`: surfaces per-zone module configs (light, music, climate, cover, security) as HA sensor attributes — feeds `styx-zone-card.js show_module_states=true`
- `ModuleDashboardSensor`: surfaces Core's `/api/v1/modules/dashboard` as HA sensor (`N/M` active modules)
- `smoke_test_v15.sh`: CI-ready smoke test script for v15 E2E verification
- Lovelace: `show_module_states=true` activated for zone overview card

### Fixed
- Coordinator O(n) state iteration: replaced O(n*m) nested loop with `async_all()` single-pass (~25x faster on 5100+ entities)
- `_sync_zone_definitions`: explicit warning when Core returns 404 — version mismatch now visible in logs
- Zone card: `zone_modules` wiring corrected to read from `sensor.copilot_ha_autonomie_status` attributes
- `zone_card_yaml.md`: corrected v15 entity names

### Removed
- `agents/`, `docs/`, `pilotsuite_ops/`, `tests/e2e/` from HA repository (reconciliation Phase 1-3)
- Orphan Lovelace cards: `pilotstack-zone-cards.mjs`, `frontend/` directory (5 files)
- `habitus_module_schema.py` (deprecated)

### Deprecated
- `entity_zone_sorter.py` — use `habitus_entity_sorter.py`
- `habitat_adapter.py` — use `habitus_adapter.py`

### Performance
- O(n) entity state iteration: `async_all()` instead of nested loop — ~25x faster

## [15.0.1] - 2026-03-21

### Fixed
- Core import path corrected in `habitus_zones_api.py`: `zone_matcher` (was `habitus_zones_matcher` — never existed)
- `HAS_ZONE_MATCHER` now switches to True when Core HA-Modul is deployed

### Changed
- Schema packages (`schemas/`) added for module-per-zone validation
- `habitus_entity_sorting.py` added: enhanced entity→zone sorting with confidence scoring

### Removed
- Reconciliation cleanup: removed non-HACS content from HA repository (see PR #150)

## [14.9.1] - 2026-03-21

### Added
- `ModuleDashboardSensor`: surfaces Core's `/api/v1/modules/dashboard` as HA sensor (`N/M` active modules)
- Frontend module registry cleaned (orphan cards removed)
- Minimal CI workflow added

### Changed
- Schema packages (`schemas/`) added for module-per-zone validation
- `habitus_adapter.py` renamed to `habitus_adapter.py` (canonical name)
- `habitus_entity_sorting.py` added: enhanced entity→zone sorting with confidence scoring
- OpenAPI contract synced from Core

### Deprecated
- `entity_zone_sorter.py` — use `habitus_entity_sorting.py`
- `habitat_adapter.py` — use `habitus_adapter.py`
- `habitus_module_schema.py` — use `schemas/zone.py`

### Removed
- Orphan Lovelace cards (pilotstack-zone-cards.mjs, frontend/ directory)
- Non-HACS content from HA repository: dashboard/, docs/, agents/, tests/, pilotsuite_ops/
- Reconciliation cleanup: removed non-HACS content from HA repository (see PR #150)

## [14.6.1] - 2026-03-16

### Changed
- Frontend-Dashboard Redesign: 8 Views, Styx als Startseite
- Mood Card v3.0: Echter Mood-State + Konfidenz-Gauge + Neuronen
- Habitus Card: Auto-Entity-Detect
- Dashboard-Auto-Update bei bestehenden Installationen

## [14.4.2] - 2026-03-15

### Added
- **Neuron Feed Pipeline**: Vollstaendige Zone→Neuron→Brain→RAG Pipeline
  - Auto-Erstellung von Neuron-Tags aus bestehenden Habitus-Zonen beim Startup
  - `ROLE_NEURON_TYPE_MAP`: 16 Entity-Rollen → 3 Neurontypen (context/state/mood)
  - NeuronFeedTagSwitch pro Tag: Enable/Disable der Neuronbefeuerung
  - `SIGNAL_NEURON_FEED_CHANGED` Dispatcher-Signal bei Toggle
- **Event Envelope Enrichment**: Events enthalten jetzt `neuron_tags` Attribut fuer Core-seitige Layer-Klassifikation
- **Events Forwarder Integration**: Neuron-Feed-Filter in `_refresh_subscriptions()` und `_handle_state()`
  - Cached exclusion set, fruehes Return fuer nicht-gefuetterte Entities
  - Automatische Subscription-Aktualisierung bei Feed-Aenderungen
- **Coordinator API**: `async_sync_habitus_config()`, `async_get_habitus_config()`, `async_get_mood_history()`, `async_get_mood_trend()`
- **Habitus Config Sync**: Einmaliger Push der HA Mining-Konfiguration an Core beim ersten Coordinator-Refresh

### Fixed
- **HomeKit Entity Platform Split**: ButtonEntity in `button.py`, SensorEntity in `sensor.py` (zuvor silent failure durch falsche Plattform-Zuordnung)
- **Neuron Feed Signal**: `async_dispatcher_send` korrekt gemockt in Tests

### Tests
- 387+ passed, neue Tests fuer neuron_feed Signal und Pipeline-Integration

---

## [14.4.1] - 2026-03-15

### Added
- **Auto-Neuron-Tags**: Automatische Erstellung von Neuron-Tags aus bestehenden Habitus-Zonen
  - `entity_tags_module.py`: `_ensure_neuron_tags()` bei Setup wenn keine neuron_* Tags vorhanden
  - `zone_auto_setup.py`: `async_create_neuron_tags_from_zones()`

### Fixed
- **HomeKit Import**: Korrekte Import-Pfade fuer HomeKit-Entities

---

## [14.4.0] - 2026-03-15

### Added
- **FrontendModule**: Neues Runtime-Modul fuer Frontend-Entitaeten
- **Zone Automation Entities**: Per-Zone Slider/Switches fuer Light+Music Konfiguration
  - `zone_automation_entities.py`: 10 Entity-Typen pro Zone (Brightness, Delays, Volumes)
  - `ZoneAutomationNumber`, `ZoneAutomationSwitch` fuer granulare Steuerung
- **Neuron Feed Store**: `neuron_feed_store.py` mit `async_is_entity_neuron_fed()`
- **LLM Config Entities**: Conversation-Model-Auswahl ueber HA-Entities
- **Update Check**: `modules_ready` Flag fuer sauberen Startup-Status

### Changed
- **STT/TTS Lazy Init**: Speech-Services werden erst bei Bedarf initialisiert
- **Conversation Error Sanitization**: LLM-Fehlermeldungen werden fuer den User bereinigt

### Tests
- 387 passed, 0 failed, 41 skipped

---

## [14.3.18] - 2026-03-15

### Fixed
- **HA 2026.3 Kompatibilitaet**: LovelaceData Dataclass, MappingProxy Config, Startup-Blocking entfernt

---

## [14.3.17] - 2026-03-15

### Fixed
- Dashboard Wiring laeuft jetzt IMMER bei Setup/Reload (nicht nur beim ersten Setup)
- YAML-Dashboards `show_in_sidebar: false` wird zuverlaessig geschrieben
- Sidebar zeigt nur noch 1 PilotSuite Dashboard (Storage-Mode)

### Changed
- Wiring + Storage-Dashboard aus `_dashboards_generated` Guard herausgezogen
- YAML-Generierung bleibt einmalig

---

## [14.3.0-14.3.16] - 2026-03-14/15

### Added
- Storage-Mode Dashboard (kein HA-Restart noetig)
- Thin-Client Prinzip: nur Haushalt, Zonen, Chat im HA-Frontend
- System Health Dashboard, Cloud API Config UI
- Dashboard Wiring Auto-Merge in bestehende lovelace-Bloecke

### Fixed
- YAML-Dashboards aus Sidebar entfernt
- Zone-Card v2.1.0 Entity-Namen, Prefix-Normalisierung
- Coordinator Webhook-Daten Persistenz
- Null-Safety fuer postJSON/fetchJSON

---

## [14.2.0] - 2026-03-14

### Added
- **Autonomie-Webhook-Handler**: autonomy_executed, autonomy_failed, scene_captured, scene_applied, module_zone_state_changed (5 neue Event-Typen)
- **Autonomie-Sensoren**: AutonomyStatusSensor (aktiv/lernend/inaktiv), AutonomyHistorySensor (letzte 10 Aktionen), ZoneHealthOverviewSensor (Durchschnitts-Score)
- **Per-Zone Modul-Steuerung**: 6 Select-Entities pro Zone (Licht, Musik, Bewegung, Stimmung, Klima, Rollladen) mit active/learning/off
- **Szenen-Buttons**: ZoneSceneCaptureButton pro Zone zum Erfassen des aktuellen Zustands
- **Coordinator API**: async_get_autonomy_dashboard(), async_get_zone_health(), async_get_zone_aggregates(), async_set_zone_module_state(), async_capture_zone_scene(), async_apply_zone_scene()
- **Polling**: Autonomie-Dashboard + Zone-Health im _async_update_data() Zyklus
- **styx-zone-card.js v2.0**: Health-Score Badge, Modul-State Chips, Autonomie-Aktionslog
- **Dashboard**: Autonomie-System + Zonen-Gesundheit Karten
- **Constants**: CONF_AUTONOMY_ENABLED, CONF_AUTONOMY_AUTO_EXECUTE, CONF_ZONE_HEALTH_POLL_ENABLED

### Changed
- Webhook-Handler unterstützt 12 Event-Typen (zuvor 7)
- Zone-Card zeigt erweiterte Modul-Informationen

### Tests
- 387 passed, 0 failed, 41 skipped (Baseline unveraendert)
- Webhook-Contract-Tests fuer neue Event-Typen erweitert

## [7.9.0] - 2026-03-11

### Zone Presence Trigger Sensors
- Neue ZonePresenceTriggerSensor: Per-Zone Binary-Sensor mit Automationsmodus (off/learning/autonomy)
- ZonePresenceOverviewSensor: Globaler Praesenz-Binary-Sensor

### Module Mode Configuration
- Neuer Options-Flow-Step "automation_modes" fuer Per-Zone-Moduskonfiguration

### Dashboard Generator v6.0
- Komplett ueberarbeiteter 6-Tab-Dashboard-Generator (Styx, Haushalt, Energie, Praesenz, Musik, Per-Zone)

### Coordinator API Erweiterung
- Sonos, Zone Automation, Presence, Light Intelligence Endpunkte hinzugefuegt

### Test-Infrastruktur
- Root conftest.py mit HA-Stubs, ML-Tests bereinigt, 285+ Tests bestanden

## [7.8.9] - 2026-02-23
- Hassfest-Fix: `assist_pipeline` in `manifest.json` als `after_dependencies` deklariert.
- Behebt CI-Fehler fuer die neue Pipeline-Default-Logik in `agent_auto_config.py`.

## [7.8.8] - 2026-02-23
- Auto-Config versucht jetzt, Styx als `conversation_engine` der bevorzugten Assist-Pipeline zu setzen.
- Damit bleibt Styx als Standard-Gespraechsagent ueber Neustarts/Updates stabiler.
- Notification-Text fuer `set_default_agent` auf Pipeline-Mechanik aktualisiert.

## [7.8.6] - 2026-02-22
- Habitus-Zonen-Validierung auf UX-freundliches Minimum umgestellt:
  - nicht mehr hart `motion + lights`
  - mindestens eine gueltige Entity-ID reicht
- Zone-Formular zeigt klare Fehlermeldung bei leerer Entitaetsauswahl.
- Dashboard-Wiring kann fehlende PilotSuite-Dashboard-Keys in bestehenden `lovelace: dashboards:` Block automatisch einpflegen.
- Neuer Service `show_installation_guide` (persistente Notification mit exakter Setup-Anleitung).
- Optionen/Übersetzungen aktualisiert auf primäre `pilotsuite-styx/` Dashboard-Pfade.

## [7.8.2] - 2026-02-22
- Primäre Dashboard-Dateipfade auf `pilotsuite-styx/` umgestellt, inklusive Legacy-Mirror nach `ai_home_copilot/`.
- Habitus-Dashboard-Generator robust gemacht (tuple/list/set Rollen, sichere Zone-Paths, YAML-quoting).
- Dashboard-Wiring akzeptiert und schreibt jetzt sowohl branded als auch legacy Include-Pfade.

## [7.8.1] - 2026-02-22
- Hub-Sensoren fuer `modes/scenes/presence/notifications/integration/brain/energy/media/templates` repariert (wieder korrekte API-Calls mit Auth-Headern).
- `CopilotBaseEntity._fetch()` als gemeinsamer, robuster Core-GET-Helper ergaenzt.
- Syntax-Regression abgesichert durch neuen Source-Syntax-Test.

## [7.7.26] - 2026-02-22
- Runtime-kompatible Lifecycle-Wrappers fuer `ops_runbook`, `mood_context`, `knowledge_graph_sync`, `person_tracking`.
- Konstruktoren fuer Modul-Registry ohne Pflichtparameter vereinheitlicht.
- verhindert stilles Skippen dieser Module beim Runtime-Setup.

## [7.7.25] - 2026-02-22
- MLContextModule Lifecycle auf Runtime-v2 kompatibel gemacht (`ModuleContext` Signaturen, Task-Cancel auf Unload).
- behebt stilles Skippen des Moduls bei Runtime-Setup.

## [7.7.24] - 2026-02-22
- Dashboard-Wiring automatisiert (Include-Datei + Auto-Append bei fehlendem `lovelace:` Block, sonst Merge-Hinweis).
- Habitus-Dashboard-Generierung auf konsistentes v2 (`async_get_zones_v2`) umgestellt.
- Setup/Zone-Refresh erzeugt jetzt PilotSuite- und Habitus-Dashboard gemeinsam.
- Dashboard-Generator referenziert nur noch vorhandene Entities (weniger tote Eintraege).

## [7.7.23] - 2026-02-22
- Nach Device-Konsolidierung werden verwaiste Legacy-PilotSuite-Devices (ohne Entities) nun automatisch bereinigt.
- Cleanup bleibt konservativ (nur reine `ai_home_copilot`-Devices) und bricht Setup bei Fehlern nicht.

## [7.7.22] - 2026-02-22
- Runtime unload now coerces module unload results to strict boolean values.
- Connection options flow now tolerates `test_light_entity_id: null` safely.
- Config/Options network schema accepts optional `None` test light values.
- Pipeline health checks now support Core variants without `/api/v1/capabilities` or `/api/v1/habitus/status`.
- Core v1 capabilities fetch now falls back to agent/chat status endpoints on 404.
- Lovelace resource registration now handles both mapping and object-based Lovelace data.
- Quick-search service registration fixed (valid schemas, URL-encoded query params, registry access cleanup).

## [7.7.21] - 2026-02-22
- Connection config normalization added (host/port/token) incl. legacy key migration.
- Failover no longer switches hosts on 401/403 auth errors.
- `host.docker.internal` fallback made opt-in instead of always-on.
- Brain Graph/HomeKit/Core-v1/Lovelace/N3 service paths now resolve merged entry config.
- Legacy CSV/testlight text entities cleaned up during setup.
- Added regression tests for connection normalization and host candidate behavior.

## [7.7.20] - 2026-02-22
- Unified sensor Core endpoints to use coordinator active failover base URL.
- Added shared Core auth header helper (`Authorization` + `X-Auth-Token`).
- Coordinator startup now normalizes legacy `auth_token` into `token`.
- Legacy host/port-based sensor unique_ids migrated to stable IDs at setup.
- Added tests for new base entity endpoint/auth helper behavior.

## [7.7.19] - 2026-02-22
- OptionsFlow merge fixed: token/host/port/module options persist across updates and step saves.
- Habitus zones: multi-area selection (`area_ids`) for create/edit, merged auto-suggestions, metadata persistence.
- Tag edit flow: two-step prefilled entity editor.
- API fallback hosts expanded (`homeassistant`, `supervisor`, `host.docker.internal`).
- Token handling harmonized in affected sensors (`token` + `auth_token` fallback).
- Deprecated CSV text entities for entity selection removed.

## [7.7.18] - 2026-02-22
- Deprecated CSV text entities for media player selection removed.

## [7.7.17] - 2026-02-22
- PilotSuite dashboard auto-refresh on Habitus zone changes.
- Dashboard generate/download buttons enabled for core entity profile.

## [0.9.6] - 2026-02-16

### Added
- **Cross-Home Sync Module** (`cross_home_sync.py`):
  - Multi-home entity sharing via Core Add-on API
  - Peer discovery for other CoPilot homes on network
  - Entity share/unshare with permission control (read/read_write)
  - State change sync to remote homes
  - Conflict resolution (local_wins, remote_wins, merge)
  - Shared entity registry with sync status tracking
  - Tests: 9 unit tests

---

## [0.9.5] - 2026-02-16

### Added
- **Collective Intelligence Module** (`collective_intelligence.py`):
  - Federated Learning support for distributed pattern sharing
  - Differential privacy with configurable epsilon (privacy-first)
  - Support for multiple model types: habit, anomaly, preference, energy
  - Pattern contribution threshold to ensure quality
  - Aggregated intelligence from multiple homes
  - Local model registration and versioning
  - Pattern expiration and cleanup
  - Tests: 11 unit tests

### Fixed
- **test_repairs_workflow.py**: Fix mock configuration for hass.data

---

## [0.9.4] - 2026-02-15

### Added
- **Quick Search Module** (`core/modules/quick_search.py`):
  - Entity Search: Search all HA entities by name, state, domain
  - Automation Search: Search automations by name, trigger, action
  - Service Search: Search available services by domain, service name
  - Quick Actions: Direct access to commonly used entities/services
  - Services: `ai_home_copilot.search_entities`, `ai_home_copilot.search_automations`, `ai_home_copilot.search_services`, `ai_home_copilot.quick_action`

- **Voice Context Module** (`core/modules/voice_context.py`):
  - Voice Command Parser: Parse voice commands into structured actions
  - TTS Output: Text-to-speech via HA TTS services
  - Voice State Tracking: Track voice assistant states
  - Command Templates: Predefined command patterns (German/English)
  - Supported commands: Light on/off, Climate control, Media control, Scene activation, Automation trigger, Status queries
  - Services: `ai_home_copilot.parse_command`, `ai_home_copilot.speak`, `ai_home_copilot.execute_command`, `ai_home_copilot.get_voice_state`

- **Calendar Integration** (existing: `calendar_context.py`):
  - Calendar Events → Neurons integration
  - calendar.load neuron (CalendarLoadSensor)
  - Termine-basiertes Context (Meeting detection, Focus/Social/Relax keywords)
  - Mood-Weight Berechnung aus Kalender

- **Mobile Dashboard** (existing: `mobile_dashboard_cards.py`):
  - Responsive Cards für mobile Geräte
  - Touch-friendly UI mit min 44px Tap-Targets
  - Quick Actions Card, Mood Status Card, Entity Quick Access Card
  - Notification Badge Card, Calendar Today Card, Quick Search Card

---

## [0.9.3] - 2026-02-15

### Added
- **Predictive Automation Sensors** (`sensors/predictive_automation.py`):
  - `predictive_automation_sensor`: Shows ML-based automation suggestion count
  - `predictive_automation_details_sensor`: Shows detailed suggestions with pattern, confidence, lift, support
  - Integration with `repairs_enhanced.py` for enhanced UX

- **Anomaly Alert Sensors** (`sensors/anomaly_alert.py`):
  - `anomaly_alert_sensor`: Real-time anomaly detection status (healthy/active/idle)
  - `alert_history_sensor`: Shows recent anomaly history with timestamps and scores
  - Integration with `AnomalyDetector` from `ml/patterns/anomaly_detector.py`

- **Energy Insights Sensors** (`sensors/energy_insights.py`):
  - `energy_insight_sensor`: Shows total energy consumption (kWh) with device breakdown
  - `energy_recommendation_sensor`: Shows active energy optimization recommendations
  - Integration with `EnergyOptimizer` from `ml/patterns/energy_optimizer.py`

- **Habit Learning v2 Sensors** (`sensors/habit_learning_v2.py`):
  - `habit_learning_sensor`: Shows number of learned habit patterns
  - `habit_prediction_sensor`: Shows habit predictions with confidence scores
  - `sequence_prediction_sensor`: Shows device sequence predictions (cross-device correlation)
  - Integration with `HabitPredictor` from `ml/patterns/habit_predictor.py`

### Services
- `predictive_automation_suggest_automation`: Suggest automation based on ML patterns
- `anomaly_alert_check_and_alert`: Check for anomalies and send alerts
- `anomaly_alert_clear_history`: Clear anomaly history
- `energy_insights_get`: Get energy insights and recommendations
- `habit_learning_learn`: Learn new habit pattern through observation
- `habit_learning_predict`: Predict future events or sequences

### Features
- Unified ML context via `MLContext` module
- All sensors integrate with existing ML subsystems
- Push notifications via HA system notifications
- Dashboard cards via existing `habitus_dashboard_cards.py`

### Configuration
- Enable via `ml_enabled: true` in config entry options
- Auto-sync of entity states to ML context every 60 seconds

---

## [0.8.16] - 2026-02-15

### Added
- **Knowledge Graph Integration** (`api/knowledge_graph.py`):
  - Full async client for Core Add-on Knowledge Graph API
  - Node operations: create, list, get by ID/type
  - Edge operations: create, list, relationships
  - Query operations: structural, causal, contextual, temporal queries
  - Pattern import from Habitus mining

- **Knowledge Graph Sync Module** (`core/modules/knowledge_graph_sync.py`):
  - Auto-syncs HA entities to Knowledge Graph
  - Creates BELONGS_TO edges for entity→area relationships
  - Creates HAS_CAPABILITY edges for entity features
  - Creates HAS_TAG edges from tag registry
  - Creates RELATES_TO_MOOD edges from neural system
  - Periodic full sync (configurable interval)
  - Real-time state change tracking

- **Knowledge Graph Sensors** (`knowledge_graph_entities.py`):
  - Knowledge Graph Stats sensor (node/edge counts)
  - Knowledge Graph Nodes sensor
  - Knowledge Graph Edges sensor
  - Sync Status sensor
  - Last Sync timestamp sensor

### Features
- Entities automatically added to graph when discovered
- Zone/Tag/Mood relationships synced in real-time
- Query related entities for suggestion context
- Foundation for Pattern-to-Entity mapping

### Configuration
- `knowledge_graph_enabled`: Enable/disable sync (default: true)
- `knowledge_graph_sync_interval`: Full sync interval in seconds (default: 3600)

### Technical
- All modules pass py_compile validation
- Async-safe client with error handling
- Module registry integration for runtime access

## [0.8.15] - 2026-02-15

### Added
- **Suggestion Panel** (`suggestion_panel.py`): Dedicated UI for PilotSuite suggestions
  - Timeline view of pending suggestions
  - Accept/Reject/Snooze actions via service calls
  - Confidence indicator and "Why?" explanations
  - Zone and Mood context display
  - Priority-based sorting (High/Medium/Low)
  - WebSocket API for real-time updates

- **Mood Dashboard** (`mood_dashboard.py`): Visualisierung der aktuellen Stimmung
  - MoodSensor with icon, color, and German name
  - MoodHistorySensor for tracking mood changes
  - MoodExplanationSensor with "Warum?" explanations
  - Lovelace card config generator
  - Top contributing factors display

- **Calendar Context Neuron** (`calendar_context.py`): Kalender-basierter Kontext
  - Meeting detection (now/soon)
  - Weekend/holiday detection
  - Vacation mode detection
  - Mood weight computation based on calendar events
  - Conflict detection
  - Keyword-based categorization (focus, social, relax, alert)

### Enhanced
- Extended `const.py` with new configuration options
- Added sensor entities: ZoneOccupancySensor, UserPresenceSensor, UserPreferenceSensor, SuggestionQueueSensor
- Added calendar context integration to sensor setup

### Technical
- All modules pass py_compile validation
- WebSocket API with proper error handling
- Async storage for suggestion persistence

## [0.8.14] - 2026-02-15

### Added
- Enhanced Repairs UX with zone and mood context
- Risk visualization for suggestions

## [0.8.0] - 2026-02-15

### Added
- Multi-User Preference Learning (MUPL) v0.8.0
- User-spezifische Mood-Gewichtung
- Debug Mode v0.8.0

## [0.4.33] - 2026-02-14

### Added
- Neuronen-System: Context, State, Mood, Weather, Presence, Energy, Camera
- Habitus Zones: Zone-basierte Muster-Erkennung
- Tag System v0.2
- Brain Graph
## [0.9.4] - 2026-02-15

### Added
- Complete SETUP_GUIDE.md - German installation guide
- OpenAPI Specification for HA Integration services
- LazyHistoryLoader for on-demand history caching
- MUPL Phase2 Caching and Query Optimization

### Merged
- dev/mupl-phase2-v0.8.1
- dev/openapi-spec-v0.8.2
- dev/vector-store-v0.8.3

## [0.9.3] - 2026-02-15

### Added
- Phase 6.1 Core Features:
  - Predictive Automation (suggest_automation service)
  - Anomaly Alert (check_and_alert service)
  - Energy Insights (get_energy_insights service)
  - Habit Learning V2 (learn_habits, predict_sequence services)

### Changed
- button.py refactored (40KB → 8 modules)
- Critical fixes: N+1 queries, memory leak, blocking I/O
- Tags API verified (Flask + Auth)

### Tests
- 100+ new tests (Core + Integration)
