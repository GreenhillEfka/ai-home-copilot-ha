# Changelog

Alle wesentlichen Aenderungen am PilotSuite Styx HA Add-on werden in dieser Datei dokumentiert.

## [14.7.5] - 2026-03-20

### HA ConfigFlow Modernisierung

#### Added
- **Delta-Write-Pattern**: ConfigEntry State wird nur noch als Delta geschrieben, kein Full-Overwrite mehr
- **Reconfigure-Step**: `async_step_reconfigure()` mit `_get_reconfigure_entry()` nach HA 2024.4+ Muster
- **OptionsFlow Parameter-Sync**: Gemeinsame Parameter (host/port/token) werden beim Reconfigure akkumuliert, nicht verworfen
- **ConfigFlow Helper-Migration**: Alle Flows auf `self.config_entry` + `self._config_entry_id` migriert

### HA UI Cards

#### Added
- **Zone-Creator-Card getConfigForm()**: `static async getConfigForm()` mit HaFormSchema nach HA-PR #16142
- **habitus-brain-card.ts**: Number-Felder (stale_threshold_seconds, mood_history_hours), Mehrfachfelder (zones, monitored_modules)
- **zone-module-editor-card.ts**: Modulabhängige Pflichtfeld-Validierung, Secondary-Zone-States (dark/sleep/extended)
- **card-form-helper.ts**: number/array/attribute-Support, zentrale Validierung
- **editor-schema-validation.ts**: Typsichere Schema-Validierung
- **zone-editor-api-client.ts**: CRUD-Client für /api/v1/zone-editor Endpunkte

### HA Dashboard

#### Fixed
- **Dashboard-Init-Binding**: `window.dashboard` wird jetzt per IIFE vor `init()` gesetzt — inline onclick-Handler funktionieren korrekt
- **Snapshot-Import Path-Resolve**: Robust gegen `/local/...`, `~`, `$ENV` und Path-Traversal

### HA Tests & Schema

#### Added
- **conftest.py**: Standardisierte Test-Fixtures (MockHass, ConfigEntry, Flow-Handler-Factories)
- **Module-per-Zone Schemas**: Pydantic-v2-Schema-Dateien für alle 8 Modultypen (Light/Audio/Climate/Cover/Energy/Scene/Security/Zone)
- **Integration-Tests Zone-Flows**: 46 neue Tests für ConfigFlow/OptionsFlow/SnapshotFlow
- **Dynamic-Entity-Generation-Tests**: 57 Tests für schema-getriebene Entity-Generierung

### HA Add-on

#### Added
- **hacs.json**: HACS-Listing-Konfiguration

#### Changed
- **homeassistant-Constraint**: Manifest auf HA 2024.4.0+ begrenzt

### Compatibility
- HA v14.7.5 <-> Core v14.7.5 (Paired Release)
- HA 2024.4.0+ required

---

## [14.7.3] - 2026-03-17

### Module-per-Zone Schema-Driven Entities

#### Added
- **Schema-Fetch**: Coordinator holt `module-schemas` vom Core und cached sie
- **Dynamische Entities**: _ZoneModuleSwitch und _ZoneModuleNumber Klassen fuer schema-getriebene Entity-Generierung
- **5 neue Module**: Climate, Cover, Energy, Scene, Security — pro Zone als Switch/Number Entities
- **async_set_zone_module_config()**: API-Client Methode fuer Modul-Config Updates

#### Changed
- **zone_automation_entities.py**: Factory-Funktion akzeptiert `module_schemas` Parameter
- **switch/number/select Platform Setup**: Durchreichen von `module_schemas` an Entity-Factory

#### Fixed
- **Config Options Flow**: `backup_restore` Menuepunkt entfernt (keine Implementierung vorhanden)

### Compatibility
- HA v14.7.3 <-> Core v14.7.3 (Paired Release)
- Tests: 522 passed, 41 skipped

---

## [14.6.1] - 2026-03-16

### Frontend-Dashboard Redesign + Mood Card v3.0

#### Changed
- **Storage-Dashboard**: 8 Views komplett redesigned (Styx, Haushalt, Zonen, Automation, Energie, Musik, KI, Chat)
- **Styx-Tab**: Neue Startseite mit Neural Interface + Brain Graph + Mood + Suggestions + Error Log
- **Dashboard-Updates**: Bestehende Dashboards werden bei Integration-Reload automatisch aktualisiert
- **Mood Card v3.0**: Zeigt echten Mood-State (Relax/Focus/Active/Sleep/Away/Alert/Social/Recovery), Konfidenz-Gauge, beitragende Neuronen
- **Habitus Card**: Auto-Entity-Detect (kein harter Entity-Requirement mehr)
- **DASHBOARD_VIEW_PATHS**: "module" ersetzt durch "styx" als primaerer Tab

### Compatibility
- HA v14.6.1 <-> Core v14.6.1 (Paired Release)
- Tests: 522 passed, 41 skipped

---

## [14.6.0] - 2026-03-16

### Version Sync mit Core v14.6.0

#### Changed
- Version bump fuer Paired Release mit Core Backend Dashboard Ueberarbeitung

---

## [14.4.3] - 2026-03-15

### Bugfixes

#### Fixed
- Diverse kleinere Fixes

---

## [14.4.2] - 2026-03-15

### Vollstaendige Zone→Neuron→Brain→RAG Pipeline

#### Added
- **Neuron Feed Pipeline**: Auto-Erstellung von Neuron-Tags aus Habitus-Zonen beim Startup
- **ROLE_NEURON_TYPE_MAP**: 16 Entity-Rollen → 3 Neurontypen (context/state/mood)
- **NeuronFeedTagSwitch**: Enable/Disable der Neuronbefeuerung pro Tag
- **Event Envelope Enrichment**: Events enthalten `neuron_tags` Attribut fuer Core-seitige Layer-Klassifikation
- **Events Forwarder**: Neuron-Feed-Filter mit Cached Exclusion Set und automatischer Subscription-Aktualisierung
- **Coordinator API**: `async_sync_habitus_config()`, `async_get_mood_history()`, `async_get_mood_trend()`
- **Habitus Config Sync**: Einmaliger Push der HA Mining-Konfiguration an Core

#### Fixed
- **HomeKit Entity Platform Split**: ButtonEntity korrekt in `button.py`, SensorEntity in `sensor.py`
- **Neuron Feed Signal**: SIGNAL_NEURON_FEED_CHANGED Dispatcher korrekt verdrahtet

### Compatibility
- HA v14.4.2 <-> Core v14.4.2 (Paired Release)
- Tests: 387+ passed

---

## [14.4.1] - 2026-03-15

### Auto-Neuron-Tags + HomeKit Fix

#### Added
- Auto-Erstellung von Neuron-Tags aus bestehenden Habitus-Zonen (`_ensure_neuron_tags()`)
- `async_create_neuron_tags_from_zones()` in zone_auto_setup

#### Fixed
- HomeKit Import-Pfade korrigiert

---

## [14.4.0] - 2026-03-15

### FrontendModule, Neuron Feed, LLM Config

#### Added
- **Zone Automation Entities**: Per-Zone Slider/Switches (Brightness, Delays, Volumes)
- **Neuron Feed Store**: `async_is_entity_neuron_fed()` fuer Feed-State-Tracking
- **LLM Config Entities**: Conversation-Model-Auswahl ueber HA-Entities
- **modules_ready Flag**: Sauberer Startup-Status

#### Changed
- STT/TTS Lazy Init — Speech-Services erst bei Bedarf
- Conversation Error Sanitization

---

## [14.3.18] - 2026-03-15

### Fix: HA 2026.3 Kompatibilitaet, Startup-Blockade, Config-Persistierung

#### Fixed
- **Dashboard Wiring**: `LovelaceData` ist seit HA 2026.3 ein Dataclass, nicht dict — `.get()` durch Attribut-Zugriff ersetzt
- **Config Entry Persistierung**: `isinstance(entry.data, dict)` war `False` weil HA `MappingProxyType` verwendet — geaendert zu `isinstance(..., Mapping)`. Token/Host/Port gingen nach Zero-Config-Flow verloren
- **Entity Profile**: Gleicher `MappingProxyType`-Bug in `entity_profile.py`
- **ZoneDetector Leak**: Periodischer Task wurde bei Reload nicht gecancelt — doppelte Tasks nach jedem Reload
- **Startup-Blockade**: 4 Endlos-Loop-Tasks blockierten HA-Startup (CandidatePoller, ZoneDetector, MLContext, PerformanceScaling) — `async_create_task` durch `async_create_background_task` ersetzt

#### Added
- **YAML-Dashboard Sidebar-Hide**: Neue Funktion `async_hide_yaml_dashboards_from_sidebar()` versteckt Legacy-YAML-Dashboards sofort (ohne HA-Restart)

### Compatibility
- HA v14.3.18 <-> Core v14.3.17 (Core unveraendert)
- Migration required: no
- Breaking Changes: keine

### Tests
- 387 passed, 0 failed, 41 skipped

---

## [14.3.17] - 2026-03-15

### Fix: Dashboard Wiring immer aktualisieren

#### Fixed
- **Dashboard Wiring**: `async_ensure_lovelace_dashboard_wiring()` und `async_ensure_storage_dashboard()` laufen jetzt IMMER bei Setup/Reload, nicht nur beim ersten Setup
- **YAML-Dashboards**: Snippet-Datei wird bei jedem Reload aktualisiert (vorher durch `_dashboards_generated` Guard uebersprungen)
- **Sidebar-Duplikate**: YAML-Dashboards `show_in_sidebar: false` wird jetzt zuverlaessig geschrieben

#### Changed
- Dashboard-Wiring und Storage-Dashboard-Erstellung aus dem `_dashboards_generated`-Guard herausgezogen
- YAML-Dashboard-Generierung bleibt weiterhin einmalig (Guard gilt nur noch fuer `pilotsuite_dashboard` und `habitus_zones_dashboard`)

### Compatibility
- HA v14.3.17 <-> Core v14.3.17
- Migration required: no
- Breaking Changes: keine

### Tests
- 387 passed, 0 failed, 41 skipped

---

## [14.3.16] - 2026-03-15

### Fix: YAML-Dashboards aus Sidebar entfernen

#### Fixed
- **YAML Snippet**: `show_in_sidebar: false` fuer beide YAML-Dashboards (copilot-pilotsuite, copilot-habitus-zones)
- **Storage Dashboard**: Thin-Client Prinzip — nur Haushalt, Zonen, Chat (3 Views)

---

## [14.3.15] - 2026-03-15

### Fix: Thin-Client Dashboard

#### Changed
- **Storage Dashboard**: Reduziert auf 3 Views (Haushalt, Zonen, Chat) — Brain, Neurons, System gehoeren ins Core Backend

---

## [14.3.14] - 2026-03-15

### Fix: Storage-Mode Dashboard + Ingress Detection

#### Added
- **Storage-Mode Dashboard**: `async_ensure_storage_dashboard()` erstellt Lovelace Dashboard ohne HA-Restart
- **Dashboard Wiring Merge**: `_merge_dashboards_into_existing_lovelace()` kann PilotSuite-Dashboards in bestehende lovelace-Bloecke injizieren

---

## [14.3.0] - 2026-03-14

### System Health + Cloud API + Blueprint Fixes

#### Added
- System Health Dashboard: CPU%, RAM, Disk, Uptime, Service-Verfuegbarkeit
- Cloud API Config UI im Dashboard konfigurierbar
- Blueprint-Registrierung: automations_bp + onboarding_bp verdrahtet

#### Fixed
- Null-Safety: postJSON(), fetchJSON() Aufrufer abgesichert
- Zone-Card v2.1.0: Entity-Namen deutsch, zone: Prefix-Normalisierung
- Coordinator: Webhook-Daten ueber Refreshes erhalten

---

## [13.10.0] - 2026-03-13

### Quality Release — Paired mit Core v13.10.0

### Compatibility
- HA v13.10.0 <-> Core v13.10.0
- Protocol/API contract: aligned
- Migration required: no
- Breaking Changes: keine

### Fixed (Core-seitig)
- Production Bug in `zone_dashboard.py` behoben (undefinierte Variablen)
- Blueprint-Doppelregistrierungen in `core_setup.py` bereinigt
- Alle 210 Core-Test-Failures behoben (0 failed, 4133 passed)

### Unchanged
- HA Integration: 373 passed, 0 failed, 41 skipped (stabil)
- 240+ Entity-Klassen, 174 Services, 9 Custom Cards
- Config Flow (7 Steps), STT/TTS/Conversation Agent

---

## [13.9.0] - 2026-03-13

### Offizielles Release — Alle Beitraege seit v13.5.8

Dies ist das konsolidierte offizielle Release, das alle Entwicklungen seit dem letzten getaggten Release (v13.5.8) zusammenfasst.

### Compatibility
- HA v13.9.0 <-> Core v13.9.0
- Protocol/API contract: aligned
- Migration required: no
- Breaking Changes: keine

### Added

#### 8 Musikwolke HA-Services
| Service | Beschreibung |
|---------|-------------|
| `copilot_ha.musikwolke_create` | Musikwolke-Gruppe erstellen |
| `copilot_ha.musikwolke_dissolve` | Musikwolke-Gruppe aufloesen |
| `copilot_ha.musikwolke_play` | Wiedergabe starten |
| `copilot_ha.musikwolke_pause` | Wiedergabe pausieren |
| `copilot_ha.musikwolke_volume` | Lautstaerke setzen (0-100%) |
| `copilot_ha.musikwolke_start_follow` | Follow-Session starten |
| `copilot_ha.musikwolke_stop_follow` | Follow-Session beenden |
| `copilot_ha.zone_automation_set_mode` | Automatisierungsmodus setzen |

#### 14 Coordinator-API-Methoden
- Musikwolke-Status, Play/Pause/Volume, Create/Dissolve
- Media Follow Start/Stop
- Zone Automation Mode Get/Set
- Zone Map Abfrage

#### 5 PilotSuite HA Module
- Licht, Helligkeit, Heiz, Bewegung, Praesenz als eigenstaendige HA-Module
- Beispiel-Dashboard mit realen Entities
- Integration in Zone Dashboard

#### Living BrainGraph Dashboard
- Pulsierender BrainGraph mit Echtzeit-Visualisierung
- Neurale Cross-Dependencies sichtbar
- Automation Repair direkt aus dem Dashboard

#### Dashboard-API Core-Anbindung
- Alle Dashboard-Endpunkte mit echten Core-API-Daten statt Hardcoded-Daten
- ML-Mocks und Platzhalter durch funktionalen Code ersetzt

#### Core<->HA Module Communication
- Vollstaendige Core<->HA Kommunikations-Pipeline verdrahtet
- Webhook Receiver fuer zone_update Events (Echtzeit)
- Memory API Client, Services und Coordinator Wiring

#### Interaktives Musik-Dashboard
- Play/Pause/Dissolve Buttons mit direkter Steuerung
- Follow Start/Stop per Knopfdruck
- Button-Cards statt statischem Markdown

#### Zone Dashboard Erweiterungen
- Habituszonen-IDs synchron mit Core
- Reichere Datenstruktur mit Controls, Musik, Playlists
- Notifications, Birthdays, Todos pro Zone

#### Bidirektionale Tag-Synchronisierung
- `async_sync_tags_to_core()` und `async_get_core_tags()` im Coordinator
- EntityTagsModule Sync zwischen HA und Core
- Zone Presence Trigger: 3-Stufen-Modus (off/learning/autonomy) pro Zone

#### Dokumentation
- Deutsches Benutzerhandbuch (docs/HANDBUCH.md)
- Installationsanleitung (docs/INSTALLATIONSANLEITUNG.md)
- Vollstaendige Modul-Referenz (docs/MODULE_REFERENCE.md)

### Code-Qualitaet & Hardening

- **Button Base Class**: Gemeinsame Basisklasse fuer alle Button-Entities
- **Lovelace Card Base**: Wiederverwendbare Basis fuer Custom Cards
- **API Contract**: Verbesserte API-Vertraege zwischen HA und Core
- **Coordinator API Cleanup**: `_safe_get`/`_safe_post` Wrapper fuer robustere API-Aufrufe
- **Coordinator Timeouts**: Zentralisierte Timeout-Konfiguration
- **Debug Logging**: Logging in zuvor stillen Handlern ergaenzt

### Fixed
- 6 tote Button-Dateien mit doppelten unique_ids entfernt
- Fehlender `asyncio`-Import und Auth-Header-Alignment in API Client
- Warning Logs fuer fehlenden Coordinator in Musikwolke Service Handlers
- Ungebundene Variable `e` in coordinator.py Musikwolke-Methoden
- Edge Cases, Type Safety und Automation Hardening
- CrossDependencySensor Registration, Edge Count und Type Safety
- 13 vergessene Sensoren verdrahtet, Translations korrigiert

### QA
- Neuron Dashboard Sensors registriert und getestet
- Decision-Sync Retry Queue fuer Offline-Core-Resilienz
- Verbesserte Module Lifecycle, SQLite Safety, Nonce Cache Cleanup

---

## [13.7.0] - 2026-03-11

### Compatibility
- HA v13.7.0 <-> Core v13.7.0
- Protocol/API contract: aligned
- Migration required: no

### Added
- **8 Musikwolke HA-Services**: musikwolke_create, musikwolke_dissolve, musikwolke_play, musikwolke_pause, musikwolke_volume, musikwolke_start_follow, musikwolke_stop_follow, zone_automation_set_mode
- **14 Coordinator-API-Methoden**: Musikwolke-Status, Play/Pause/Volume, Create/Dissolve, Media Follow, Zone Automation Mode, Zone Map
- **Interaktives Musik-Dashboard**: Button-Cards fuer Play/Pause/Dissolve, Follow Start/Stop
- **Handbuch** (docs/HANDBUCH.md): Deutsches Benutzerhandbuch
- **Installationsanleitung** (docs/INSTALLATIONSANLEITUNG.md): Setup-Guide
- **Modul-Referenz** (docs/MODULE_REFERENCE.md): Alle HA-Komponenten dokumentiert

### Changed
- Musik-Tab von statischem Markdown zu interaktiven Button-Cards
- Versions-Bump auf 13.7.0

## [13.6.0] - 2026-03-11

### Compatibility
- HA v13.6.0 ↔ Core v13.6.0
- Protocol/API contract: aligned
- Migration required: no

### Added
- **Bidirektionale Tag-Synchronisierung**: `async_sync_tags_to_core()` und `async_get_core_tags()` im Coordinator
- **EntityTagsModule Sync**: Tags werden zwischen HA und Core synchronisiert
- **Zone Presence Trigger**: 3-Stufen-Modus (off/learning/autonomy) pro Zone

### Fixed
- **Versions-Synchronisierung**: Alle VERSION-Dateien auf 13.6.0 vereinheitlicht

## [13.5.8] - 2026-03-10

### Compatibility
- HA v13.5.8 ↔ Core v13.5.8
- Protocol/API contract: aligned
- Migration required: no

### Fixed
- **Drift-A Closed**: 5 OpenAPI-Pfade dokumentiert (`/api/v1/zone*`, `/api/v1/mood/aggregated`)
- OpenAPI sync: HA + Core aligned (572/572 paths, 100%)

## [13.5.7] - 2026-03-09

### Compatibility
- Core v13.5.7 ↔ HA v13.5.7
- Migration required: no

### Docs
- Webhook contract mirrored in OpenAPI.
- Version files normalized for aligned dual-repo release.

## [13.5.4] - 2026-03-07

### Compatibility
- Core v13.5.4 ↔ HA v13.5.4
- Protocol/API contract: X-Auth-Token; Webhook envelope {type,data}; event types mood|neuron|suggestion|status
- Migration required: no

### Fixed
- Inventory/Drift-Fix Batch A release mirror: HA OpenAPI auf aktive v13 Candidates/Tag-System-Pfade synchronisiert (inkl. `{candidate_id}`/`{tag_id}` Parametrisierung).

### QA/Ops
- Release-Gates nach Drift-Fix erneut verifiziert: Inventory/Drift Guard (PS-QA-083) + Smoke Preflight + Dual-Repo Tag Guard + PS-REL-018 Artefaktvalidator.

## [13.5.3] - 2026-03-07

### Compatibility
- Core v13.5.3 ↔ HA v13.5.3
- Protocol/API contract: X-Auth-Token; Webhook envelope {type,data}; event types mood|neuron|suggestion|status
- Migration required: no

### Security
- HA webhook HMAC signature verification implemented (primary/secondary keys) with replay defense (timestamp TTL + nonce cache).

### Docs
- OpenAPI webhook signing 401 examples (`missing_signature_headers`, `stale_timestamp`, `replay_detected`, `invalid_signature`) aligned for drift-fix release readiness.


## [13.5.2] - 2026-03-06

### Compatibility
- Core v13.5.2 ↔ HA v13.5.2
- Protocol/API contract: X-Auth-Token; Webhook envelope {type,data}; event types mood|neuron|suggestion|status
- Migration required: no

### Ops
- Version-Sync Release.
- PS-REL-017: Release-Commit verweist auf Smoke/Tag Gate Report (siehe Dossier/Evidence).

## [13.5.1] - 2026-03-06

### Compatibility
- Core v13.5.1 ↔ HA v13.5.1
- Protocol/API contract: X-Auth-Token; Webhook envelope {type,data}; event types mood|neuron|suggestion|status
- Test gate: /config/clawd/pilotsuite_ops/AEGIS_SMOKE_GATE_DUAL_REPO.md
- Migration required: no

### Ops
- Version-Sync Release (HA UI unverändert). Core-Fix: Core bootet auch ohne `sklearn` (Anomaly-Endpoints dann deaktiviert).

## [13.5.0] - 2026-03-05

### Compatibility
- Core v13.5.0 ↔ HA v13.5.0
- Protocol/API contract: X-Auth-Token; Webhook envelope {type,data}; event types mood|neuron|suggestion|status
- Test gate: /config/clawd/pilotsuite_ops/AEGIS_SMOKE_GATE_DUAL_REPO.md
- Migration required: no

### Dashboard-Restrukturierung & 4 neue Lovelace Custom Cards

#### Dashboard 3-Tab-Layout (NEU)
- **Tab 1 "Styx"**: Brain-Visualisierung (iframe), Mood + Brain Grid, Chat-Interface, KI-Vorschlaege, Fehlerlog mit Reparaturvorschlaegen, Automatisierungen
- **Tab 2 "Haushalt"**: Haushaltsuebersicht (Health-Score, Wetter, Preise, Zonen), System-Status, Medien, Energie, Quicklinks
- **Tab 3+ pro Habitus-Zone**: Dynamisch generiert mit Licht, Klima, Media, Sensoren pro Zone
- `pilotsuite_dashboard_v14.yaml` als statische Referenz

#### Neue Lovelace Custom Cards
- **styx-chat-card.js**: Eingebettetes Chat-Interface mit Message-Bubbles, Typing-Indicator, History-Loading, AbortController-Timeouts (10s/30s)
- **styx-suggestions-card.js**: KI-Vorschlaege mit Konfidenz-Badges, Kategorie-/Risiko-Tags, Governance-Actions (Annehmen/Spaeter/Ablehnen), sichtbare Fehlermeldungen
- **styx-error-card.js**: Error-Digest mit Severity-Badges, Kategorie-Chips, aufklappbare Reparaturvorschlaege, Sensor-Fallback wenn Core nicht erreichbar
- **styx-household-card.js**: Haushaltsuebersicht mit SVG-Health-Ring, Wetter + Unwetterwarnungen, Strom-/Treibstoffpreise, Proaktive Alerts, Zonen-Chips mit Belegungsanzeige

#### Technische Verbesserungen
- **Event Delegation** statt direkte Listener in allen interaktiven Cards (kein Memory Leak)
- **AbortController-Timeouts** auf allen Fetch-Calls (10s fuer Lesen, 30s fuer Chat)
- **Auto-Registration** aller 8 Card-Dateien in `lovelace_resources.py`
- **Responsive Design**: CSS Grid/Flexbox mit auto-fit, flex-wrap, mobile-first

#### Metriken
- 8 Lovelace Custom Cards insgesamt
- 255 Tests bestanden, 41 skipped
- Version synchronisiert mit Core v13.5.0

---

## [13.3.0] - 2026-03-04

### Compatibility
- Core v13.3.0 ↔ HA v13.3.0
- Protocol/API contract: X-Auth-Token; Webhook envelope {type,data}; event types mood|neuron|suggestion|status
- Test gate: /config/clawd/pilotsuite_ops/AEGIS_SMOKE_GATE_DUAL_REPO.md
- Migration required: no

### Version Sync mit Core v13.3.0

- **Sync**: Kompatibel mit Zone Automation Controller (praesenzabhaengige Licht-/Musiksteuerung)
- **Entity-Management**: Neue Tag-basierte Entitaetszuordnung via Core API nutzbar
- **Version**: 13.3.0 synchronisiert

---

## [13.2.0] - 2026-03-04

### Compatibility
- Core v13.2.0 ↔ HA v13.2.0
- Protocol/API contract: X-Auth-Token; Webhook envelope {type,data}; event types mood|neuron|suggestion|status
- Test gate: /config/clawd/pilotsuite_ops/AEGIS_SMOKE_GATE_DUAL_REPO.md
- Migration required: no

### Styx Dashboard Integration & Habitus Dashboard Erweiterung

- **Styx Dashboard Link**: Jede Habitus-Zone enthält jetzt einen Link-Card zum Styx Dashboard für erweiterte Ansicht (Musikwolke, Vorschläge, KI-Chat)
- **Cross-Module Verknüpfung**: Nahtloser Übergang von HA Lovelace Zonen-Ansicht → Styx Dashboard SPA
- **Sync mit Core v13.2.0**: Kompatibel mit neuen Styx Dashboard Features (8 Tabs, Suggestions API, Musikwolke Sonos-Steuerung)

---

## [v13.1.0] - 2026-03-03

### Production Readiness Release — Bug Fixes, Hub Integration & RAG Pipeline

#### Critical Bug Fixes ✅

- **UniFi Module NameError**: `hass` → `ctx.hass` in `unifi_module.py:114` — Module konnte nicht initialisieren
- **37 Broken API Routes**: Double-prefix `/api/v1/api/v1/...` in Sharing (16 Routes), Federated Learning (15 Routes), HA Discovery (7 Routes), OpenAPI Spec (2 Routes) korrigiert
- **RAG Chat Pipeline**: ChatHandler komplett umgeschrieben — nutzt jetzt interne RAG Pipeline statt fehlgeschlagenem HTTP-Call zu `localhost:8765`
- **82 Test Failures**: Alle behoben (12 Core Cache/Alert Tests + 70 HA PROJECT_ROOT Tests)

#### Hub Module Integration ✅ NEW

- **17 Hub Engines** aktiviert und mit API verbunden:
  - Dashboard, Plugin Manager, Multi-Home, Predictive Maintenance
  - Anomaly Detection, Habitus Zones, Light Intelligence, Zone Modes
  - Media Follow, Energy Advisor, Automation Templates, Scene Intelligence
  - Presence Intelligence, Notification Intelligence, System Integration
  - Brain Architecture, Brain Activity
- **100+ API Routes** unter `/api/v1/hub/*` jetzt erreichbar

#### Version Synchronization ✅

- Alle VERSION-Dateien, manifest.json, config.yaml, OpenAPI Specs auf v13.1.0 synchronisiert
- Sync zwischen Core und HA Repos verifiziert

#### Test Coverage

- **Core**: 295 Tests passed (241 + 54 Monitoring)
- **HA**: 239 Tests passed, 41 skipped, 0 failed

---

## [v13.0.4] - 2026-03-03

### Version Sync & Documentation Fixes

- **VERSION Sync**: `custom_components/copilot_ha/VERSION` auf 13.0.4 synchronisiert (war 13.0.3)
- **OpenAPI Version**: `docs/openapi.yaml` Version auf 13.0.4 aktualisiert
- **GitHub URLs**: Falsche URLs `github.com/pilotsuite/` korrigiert zu `github.com/GreenhillEfka/`
- **Masterplan**: Konsolidierter Projektplan `PILOTSUITE_MASTERPLAN_2026-03-03.md` hinzugefuegt
- **Sync mit Core**: Alle Versionsdateien zwischen Core und HA synchronisiert

---

## [v13.0.3] - 2026-03-03

### Module Registry & Test Coverage

- **Module Registry**: Dynamic module discovery and registration (synced from Core)
- **Test Coverage**: 100% auf Module Registry
- **Version Sync**: Synchronisiert mit Core v13.0.3

---

## [v13.0.2] - 2026-03-02

### Security Hardening — RAG API P0-Fixes ✅ COMPLETE

**P0-01: Rate Limiting auf RAG-Endpoints** ✅
- **Rate Limit:** 15 req/min, burst 5 auf allen `/api/v1/rag/*` Endpoints
- **Endpoints betroffen:** `/search`, `/search/bm25`, `/search/semantic`, `/search/enhanced`, `/rerank`, `/stats`, `/index`
- **Implementation:** Token-basiertes Rate Limiting mit client-specific keys
- **Security Logs:** Rate-Limit-Exceeded Events werden protokolliert

**P0-02: Namespace-Sanitization** ✅
- **Regex-Validation:** `^[a-zA-Z0-9_-]+$` für alle namespace-Parameter
- **Max Length:** 128 Zeichen (DoS-Schutz)
- **Endpoints betroffen:** Alle RAG-Endpoints die namespace verwenden
- **Security:** Verhindert SQL-Injection und Path-Traversal-Angriffe

**P0-03: Swagger-UI Tests** ✅
- **Status:** Alle 6 Swagger-UI Tests laufen grün
- **Coverage:** OpenAPI-Spec Validation, Swagger-UI Loading

#### Changes in This Release
- **VERSION:** Updated to v13.0.2 (Core + HA synced)
- **app.py:** RAG-Registrierung auf Flask Blueprint v1 umgestellt
- **api/v1/rag.py:** Rate Limiting + Namespace-Validation implementiert
- **Tests:** Namespace-Validation Tests hinzugefügt (4/6 grün, 2 Test-Bugs bekannt)

#### Known Issues
- 2 Namespace-Validation Tests haben Test-Bugs (alte aiohttp API vs neue Flask API)
- Metrics API Blueprint-Registrierung hat Fehler (wird separat gefixt)

---

## [v12.17.0] - 2026-03-02

### Phase 6 Completion — Release Pipeline & Test Fixes (Iteration 15:40)

#### P0: Release-Pipeline Auto-Sync ✅ COMPLETE

**P0-102: Auto-Sync HA+Core vor jedem Release**
- **Script**: `scripts/sync-ha-core-versions.sh` (im Core Repo)
- **Funktion**: Synchronisiert VERSION, config.json, manifest.json zwischen Core und HA Repos
- **Features**:
  - Automatische Version-Synchronisation vor Release
  - CHANGELOG-Sync von Core zu HA
  - Git-Commit mit aussagekräftiger Message
  - Dry-Run und Force-Modus für manuelle Ausführung

- **GitHub Actions Workflows**:
  - `.github/workflows/sync-versions.yml` (HA Repo)
  - Schedule: Alle 20 Minuten
  - Trigger: Push zu main, manuell mit Force-Option

**Integration in Release-Pipeline**:
- Auto-Sync läuft vor jedem Release-Tag
- Stellt sicher, dass HA und Core immer gleiche Version haben
- Verhindert Version-Drift zwischen Repos

#### Changes in This Release
- **VERSION**: Updated to v12.17.0 (synced with Core)
- **manifest.json**: Version updated to v12.17.0
- **CHANGELOG**: Synced with Core repository

#### Test Coverage Summary
- Zone Editor Tests: 41/42 Tests ✅ (Core)
- Pool Metrics Tests: 9/9 Tests ✅ (Core)
- Alle neuen Endpoints vollständig getestet

---

## [v12.16.0] - 2026-03-02

### Phase 5 Completion — Security Hardening & Bugfixes (Iteration 15:00)

#### Security Hardening — P2 Issues ✅ COMPLETE

Alle P2 Security Issues wurden im Core implementiert und sind hier übernommen:

**P2-01: Zone ID Input Sanitization** ✅
- Validation für alle Zone-ID Parameter
- Max Length: 50 Zeichen
- Regex: `^[a-zA-Z0-9_-]+$`

**P2-02: Rate Limiting on Proactive Endpoints** ✅
- Rate Limits für Proactive-Endpoints
- 15 req/min mit burst von 5

**P2-03: Neuron ID Validation** ✅
- Validation für Neuron-ID Parameter
- Format: lowercase, underscores, optional dot-prefix

---

## [v12.0.0 - v12.15.0] - 2026-03-01 bis 2026-03-02

### Phase 12 — RAG Conversation, Connection Pooling, Security Hardening

- **RAG Conversation** (v12.1.0): `pilotSuite_rag_conversation` — Hybrid Search mit SearXNG-Integration
- **Connection Pooling** (v12.13.0): 28.5x schnellere API-Responses, Hybrid Cache (Redis + LRU), Query Optimizer
- **Security Hardening**: WebSocket Auth, Neuron State Override Protection, Zone-ID Sanitization, Rate-Limiting
- **Dashboard**: 3D Vision (Three.js), Energy Forecast, Swagger UI, Prometheus Monitoring, Voice Integration
- **HA Auto-Discovery** (v12.8.0): Habitus Dashboard, Zone Matching, Task Queue System
- **Codequalitaet**: 2201 Tests (Phase 5/6 production-ready), 8 kritische Bugs behoben

---

## [v11.1.0 - v11.9.0] - 2026-02-27 bis 2026-03-01

### Phase 11 — Dual-Repo Architektur, RAG Hybrid Search, Phase 5/6 APIs

- **Dual-Repo Architektur** (v11.1.0): System Message Merge, MUPL Feedback-Loop, HA-Core Sync-Protokoll
- **RAG Hybrid Search** (v11.5.0+): BM25 + Semantic mit RRF Fusion, SearXNG-Integration
- **Phase 5 APIs** (v11.3.0): Sharing, Notifications, Collective Intelligence — Integration Tests komplett
- **HA Notify Adapter**: Push-Notifications aus Core an HA
- **Zone-Editor v1** (v11.7.0): UX Dashboard Foundation, Frontend Zone-Dashboard
- **Neural Confidence Hardening** (v11.2.0): Docs Freshness Gate, Context-ID SHA256 Hashing
- **Deprecation Fixes**: `datetime.utcnow()` durch `datetime.now(UTC)` ersetzt

---

## [v10.0.0 - v10.4.2] - 2026-02-26 bis 2026-02-27

### Phase 10 — Override Modes, Mood Engine v3.0, Strukturbereinigung

- **Override Modes** (v10.0.0): Musikwolke Coordinator Handoff, Volume-Presets, Light-Presets
- **Mood Engine v3.0** (v10.2.0): Unified Mood Engine — Models, Engine, Service, API; defensive Input-Validierung
- **Habitus Miner Trends** (v10.1.x): Climate-aware Zone Automation, Shopping, Network, Calendar/Weather Dashboard
- **Security Hardening** (v10.3.0): Data-driven Blueprint-Registration (37 try/except Bloecke durch Loop ersetzt)
- **Strukturbereinigung**: 815 tote API-Stubs entfernt, FastAPI v2 Modul geloescht
- **EventBus Bridges**: Logik-Struktur gehaertet, Auto-Setup API Endpoints

---

## [v9.0.0 - v9.3.0] - 2026-02-26

### Phase 9 — Entity Search v2, HA Bridge, Dashboard Restrukturierung

- **HA Bridge**: HA-Daten aus Add-on heraus via REST + WebSocket entdecken
- **Entity Search v2** (v9.1.0): Device Cache, Manufacturer Filter, Labels, Bulk Import, Zone Suggestions, Role Inference
- **Dashboard Restrukturierung**: Tier-separierte Module, Overview Health Panel, Chat Tab
- **Neuronenlayer 3-Ring Visualization**: Tagged-not-in-Zone Panel
- **Config Services**: Endpoint-Fix, Dashboard Model Download + Manual Entry

---

## [v8.0.0 - v8.12.1] - 2026-02-24 bis 2026-02-26

### Phase 8 — Scene/Routine Extractors, Habitus Management, Self-Repair

- **Scene + Routine Pattern Extractors** (v8.0.0): Dashboard API, MCP Phase 2 Core Tools
- **Brain Graph + Habitus Sensors** (v8.2.0): Core API Integration, Dashboard Improvements
- **RAG Document Pipeline** (v8.7.0): Module Control erweitert, Knowledge Graph Guard
- **Habitus Automation Management** (v8.6.0): Neuron-Brain Dashboard, react-first Habitus Flow
- **HomeKit Zone Servers** (v8.10.0): QR Endpoints, Dashboard Controls
- **System Observability Dashboard**: Zone Summaries, System Health Registration gehaertet
- **Self-Repair API** (v8.11.0): Guarded Self-Repair, Workspace Clone + Branch Prep Flow
- **Musikwolke**: Cloud Model Defaults, Media Flow gehaertet

---

## [v7.0.0 - v7.125.0] - 2026-02-21 bis 2026-02-25

### Phase 7 — Brain Architecture, Presence Intelligence, MCP API-Expansion

- **Brain Architecture** (v7.4.0): Hirnregionen, Neuronen, Synapsen — Pulse, Sleep, Chat History
- **Presence Intelligence** (v7.1.0): Anwesenheits-Intelligence, Notification Intelligence (v7.2.0)
- **System Integration Hub** (v7.3.0): Cross-Engine Orchestration
- **Production-Ready** (v7.6.0): Full Engine Wiring, Granular Fault Isolation, Docker Build Fix (Alpine 3.21)
- **LLM Hardening** (v7.7.x): Ollama Readiness, Cloud Fallback, Self-Heal, Model Alias, interner Port 11435
- **MCP API Expansion** (v7.14.0-v7.125.0): Entity Management, Service Calls, Sensors, Lights, Climate, Switches, Media Players, Scenes, History, Weather, Scripts, Alerts, Webhooks, RBAC
- **Notification APIs** (v7.10.0-v7.13.0): Templates, Scheduling, Type Hints, Phase 5/6 Tests (142+ Tests gruen)
- **CI/CD**: HACS/HassFest Validation, Production Guard Workflow
