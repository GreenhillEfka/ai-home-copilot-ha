# Changelog

Alle wesentlichen Änderungen am PilotSuite Styx HA Add-on werden in dieser Datei dokumentiert.

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
