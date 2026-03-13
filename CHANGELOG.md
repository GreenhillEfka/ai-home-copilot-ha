# Changelog

Alle wesentlichen Aenderungen am PilotSuite Styx HA Add-on werden in dieser Datei dokumentiert.

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
- OpenAPI sync: HA + Core aligned (551/551 paths, 100%)

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
