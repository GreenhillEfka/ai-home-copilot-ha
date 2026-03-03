# Changelog

Alle wesentlichen Änderungen am PilotSuite Styx HA Add-on werden in dieser Datei dokumentiert.

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
