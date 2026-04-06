# MEMORY.md — PilotSuite Research Tasks & Learnings

**Created:** 2026-04-01 03:47 Europe/Berlin  
**Owner:** openclaw-main  
**Purpose:** Persistent storage of all research-derived tasks for systematic execution

---

## 📚 RESEARCH SOURCES

| Source | Date | Topics |
|--------|------|--------|
| `AI_HOME_COPILOT_DEEP_RESEARCH_REPORT.md` | 2026-02-15 | Module Analysis, Neurons, Dashboard, Tests |
| `perplexity_research_2026-02-16.md` | 2026-02-16 | 5 Tracks: AI/ML, Presence, Energy, KG, Multi-User |
| `research_2026-02-17.md` | 2026-02-17 | SOTA Research (5 Prioritäten) |
| `DEEP_RESEARCH_PARALLEL.md` | 2026-03-xx | 5 Parallel Tracks (Architecture, Vector, Bayesian, Integration, UX) |
| `research_integration_map.md` | 2026-03-26 | Integration Status |
| `orakel.md` (Pull-Loop Logs) | 2026-03-24–29 | P0-103 Recovery (80h+ Blockade) |

---

## 🎯 MASTER TASK LIST (All Research-Derived Tasks)

### P0 — KRITISCH (Security/Stability)

| ID | Task | Source | Status | Priority |
|----|------|--------|--------|----------|
| **P0-001** | Security Fix: Token Auth prüfen/fixen | research_2026-02-17.md | ❌ Offen | 1 |
| **P0-002** | Vector Store Tests fixen (19 failures) | DEEP_RESEARCH_REPORT | ✅ Fixed (Blueprint registriert) | 2 |
| **P0-003** | Manifest-Drift fixen (15.2.21 synchronisiert) | Orakel Pull-Loop | ✅ Fixed | 3 |
| **P0-004** | Dev Surface Tests fixen (10 failures) | DEEP_RESEARCH_REPORT | ✅ Fixed (Import/Registry behoben) | 4 |

### P1 — HOCH (Core-Features)

| ID | Task | Source | Status | Priority |
|----|------|--------|--------|----------|
| **P1-001** | Bayesian Presence Detection | perplexity_2026-02-16 | ❌ Offen | 5 |
| **P1-002** | LSTM Energy Forecasting | perplexity_2026-02-16 | ❌ Offen | 6 |
| **P1-003** | Multi-User Preference Learning | perplexity_2026-02-16 | ❌ Offen | 7 |
| **P1-004** | TFLite/ONNX Integration | research_2026-02-17 | ❌ Offen | 8 |
| **P1-005** | Knowledge Graph Schema | perplexity_2026-02-16 | ❌ Offen | 9 |
| **P1-006** | Voice: Whisper/Piper Integration | research_2026-02-17 | ⚠️ Teilweise | 10 |
| **P1-007** | Brain Graph Store Tests fixen (4 failures) | DEEP_RESEARCH_REPORT | ❌ Offen | 11 |
| **P1-008** | Tag System Tests fixen (6 failures) | DEEP_RESEARCH_REPORT | ❌ Offen | 12 |

### P2 — MITTEL (Optimization)

| ID | Task | Source | Status | Priority |
|----|------|--------|--------|----------|
| **P2-001** | Multi-Sensor Fusion (3+ Typen) | perplexity_2026-02-16 | ❌ Offen | 13 |
| **P2-002** | OR-Tools Scheduling Optimizer | perplexity_2026-02-16 | ❌ Offen | 14 |
| **P2-003** | HNSW Vector Optimization | DEEP_RESEARCH_PARALLEL | ❌ Offen | 15 |
| **P2-004** | Wilson Score Interval (Bayesian) | DEEP_RESEARCH_PARALLEL | ❌ Offen | 16 |
| **P2-005** | Thompson Sampling | DEEP_RESEARCH_PARALLEL | ❌ Offen | 17 |
| **P2-006** | Event Propagation Systematics | DEEP_RESEARCH_PARALLEL | ❌ Offen | 18 |
| **P2-007** | State Consistency Checks | DEEP_RESEARCH_PARALLEL | ❌ Offen | 19 |
| **P2-008** | Federated Learning Math Library | DEEP_RESEARCH_REPORT | ❌ Offen | 20 |
| **P2-009** | Knowledge Transfer API Contract | DEEP_RESEARCH_REPORT | ❌ Offen | 21 |
| **P2-010** | Real-Time Pricing API | perplexity_2026-02-16 | ❌ Offen | 22 |
| **P2-011** | Battery Management Predictive | perplexity_2026-02-16 | ❌ Offen | 23 |

### P3 — NIEDRIG (UX/Dashboard)

| ID | Task | Source | Status | Priority |
|----|------|--------|--------|----------|
| **P3-001** | ReactBoard Integration (404 Fix) | DEEP_RESEARCH_REPORT | ❌ Offen | 24 |
| **P3-002** | WebSocket für Echtzeit-Updates | DEEP_RESEARCH_REPORT | ❌ Offen | 25 |
| **P3-003** | Interaktive Graph-Visualisierung | DEEP_RESEARCH_REPORT | ❌ Offen | 26 |
| **P3-004** | Learning Progress Visualization | DEEP_RESEARCH_PARALLEL | ❌ Offen | 27 |
| **P3-005** | Anomaly Detection Display | DEEP_RESEARCH_PARALLEL | ❌ Offen | 28 |
| **P3-006** | Neo4j/NetworkX Integration | perplexity_2026-02-16 | ❌ Offen | 29 |
| **P3-007** | SPARQL Query Interface | perplexity_2026-02-16 | ❌ Offen | 30 |
| **P3-008** | Wi-Fi/BLE Fingerprinting | perplexity_2026-02-16 | ❌ Offen | 31 |
| **P3-009** | mmWave Radar Integration (60GHz) | perplexity_2026-02-16 | ❌ Offen | 32 |
| **P3-010** | CQRS + Event Sourcing | DEEP_RESEARCH_PARALLEL | ❌ Offen | 33 |
| **P3-011** | Hexagonal Architecture Refactor | DEEP_RESEARCH_PARALLEL | ❌ Offen | 34 |

---

## ✅ COMPLETED TASKS

| ID | Task | Completed | Notes |
|----|------|-----------|-------|
| **C-001** | LLM-Integration: qwen3.5:9b Default | 2026-04-01 | Version API + Update-Button |
| **C-002** | Versions-/Update-System API | 2026-04-01 | `/api/v1/versions/*` |
| **C-003** | PII-Redaktion auf Node-Level | Vor 2026-02-16 | Bereits implementiert |
| **C-004** | Oracle/Orakel Files Cleanup | 2026-04-01 | Gelöscht (nicht verwendet) |
| **C-005** | P0-001: Security Fix (Token Auth) | 2026-04-01 | Bereits solide implementiert |
| **C-006** | P0-002: Vector Store Tests | 2026-04-01 | Blueprint registriert |
| **C-007** | P0-003: Manifest-Drift | 2026-04-01 | Alle auf 15.2.21 synchronisiert |
| **C-008** | P0-004: Dev Surface Tests | 2026-04-01 | Import/Registry behoben |
| **C-009** | B1-B4: Zone Sync Blocker | 2026-04-01 | Persistence + sync_from_ha() + API-Endpoint |
| **C-010** | B5-B6: Event-Wiring | 2026-04-01 | ModuleRouter → HubZoneEngine.update_entity_state() |
| **C-011** | P1-002: LSTM Energy Forecasting | 2026-04-01 | LSTMForecaster in energy/forecast.py |
| **C-012** | P1-004: TFLite/ONNX Runtime | 2026-04-01 | EdgeMLRuntime in ml/tflite_runtime.py |
| **C-013** | Presence Consolidation | 2026-04-01 | presence_extended.py → DEPRECATED, Features in zone_presence.py |
| **C-014** | Bayesian Presence | 2026-04-01 | Wilson Score + Bayesian in zone_presence.py |
| **C-015** | Unified Presence System | 2026-04-01 | presence/__init__.py created, API v4.0.0 consolidated |
| **C-016** | API Wiring | 2026-04-01 | core_setup.py → init_presence_api() with engines |
| **C-017** | Integration Tests | 2026-04-01 | test_presence_unified.py (20+ tests) |
| **C-018** | WebSocket Server | 2026-04-01 | presence/websocket_server.py (real-time updates) |
| **C-019** | Pattern Detection | 2026-04-01 | presence/pattern_detection.py (ML-based) |
| **C-020** | API Analytics | 2026-04-01 | /api/v1/presence/analytics/{patterns,predict,anomaly} |

---

## 📋 EXECUTION STRATEGY

### Phase 1: Foundation (Week 1)
- P0-001: Security Fix (Token Auth)
- P0-002: Vector Store Tests
- P0-003: Manifest-Drift
- P0-004: Dev Surface Tests

### Phase 2: Core Features (Week 2-3)
- P1-001: Bayesian Presence
- P1-002: LSTM Energy
- P1-004: TFLite Integration
- P1-005: Knowledge Graph

### Phase 3: Optimization (Week 4)
- P2-001 to P2-11: Various optimizations

### Phase 4: UX Polish (Week 5)
- P3-001 to P3-011: Dashboard/UX improvements

---

## 🔬 KEY LEARNINGS FROM RESEARCH

### Architecture Patterns
- **Local-First AI**: Privacy + Latency (Ollama bestätigt)
- **Hybrid Approach**: ML für Predictions, Rules für Actions
- **Event-Driven Microservices**: PilotSuite Core Architektur
- **CQRS + Event Sourcing**: Für State Consistency

### Presence Detection
- **Multi-Sensor Fusion**: 3+ Sensortypen kombinieren
- **Bayesian Approach**: P(present|sensor_data) mit Priors
- **Wi-Fi/BLE/mmWave**: Komplementäre Technologien

### Energy Optimization
- **LSTM Forecasting**: Zeitreihen-Vorhersage
- **OR-Tools Scheduling**: Optimizer für Last-Shift
- **Real-Time Pricing**: Dynamische Tarife nutzen

### Knowledge Graphs
- **Entity-Relation-Entity**: Devices, States, Relationships
- **Temporal Reasoning**: Time-based queries
- **SPARQL/GraphQL**: Query interfaces

### Multi-User Learning
- **Federated Learning**: Privacy-preserving
- **Per-User Profiles**: Individual settings
- **Context-Aware**: Temperature + time + occupancy

### Testing
- **52 Failed Tests** (Stand 2026-02-15): Hauptsächlich Mock/Import
- **Vector Endpoints**: 19 failures (API Response Format)
- **Dev Surface**: 10 failures (Mock Dependencies)

---

## 📊 METRICS & TARGETS

| Metric | Current | Target |
|--------|---------|--------|
| Test Pass Rate | ~90% (geschätzt) | 95%+ |
| P0 Tasks Open | 4 | 0 |
| P1 Tasks Open | 8 | 0 |
| Research Tasks Total | 34 | 0 (alle abgearbeitet) |
| Manifest Drift | 15.2.2 vs 14.9.0 | Synchronized |
| Security Issues | 1 (Token Auth) | 0 |

---

## 🔄 CONTINUOUS IMPROVEMENT

- **Nightly**: Test suite runs, report failures
- **Weekly**: Research task progress review
- **Monthly**: Architecture review, tech debt assessment

---

## 🧷 DURABLE EXECUTION DECISIONS (2026-04-02)

- **Gemeinsame Arbeitsgrundlage für alle Agenten festgezogen:**
  - `/config/clawd/team/PILOTSUITE_EXECUTION_FOUNDATION.md`
  - `/config/clawd/team/PILOTSUITE_PROGRESS_LEDGER.md`
  - `/config/clawd/memory/168H_ECHTER_ARBEITSPLAN.md`
- **Kanonische Arbeitsreihenfolge:** erst Foundation, dann Progress Ledger, dann Plan, dann Konzept-/Lane-Dokumente.
- **Repo-Wahrheit präzisiert:**
  - große API-/Runtime-Wahrheit primär in `/config/clawd/team/worktrees/pilotsuite-styx-core-current`
  - HA/HACS-Integrationswahrheit primär in `/config/clawd/team/worktrees/pilotsuite-styx-ha-current`
- **API-Truth-Hierarchie festgelegt:** aktiver Worktree → Runtime-Wiring (`rootfs/usr/src/app/...`) → Registry → verifizierte OpenAPI → Legacy-Doku.
- **Continuity-Regel:** relevanter Fortschritt darf nicht nur im Chat stehen; er muss in `PILOTSUITE_PROGRESS_LEDGER.md` so festgehalten werden, dass jeder Agent unmittelbar wieder übernehmen kann.
- **168h-Plan harmonisiert:** nicht mehr generische Iterationssammlung, sondern Wahrheit → Contract → Systemvereinheitlichung → HA/Core-Schluss → UX/Ops → Release/Continuity.
- **Ausführungsmodus für aktuellen H1-Abschnitt:** Andreas hat explizit festgelegt, dass openclaw-main diese Arbeit allein ausführt; keine Delegation/Subagents für diesen Abschnitt.
- **H1 real gestartet und mit Artefakten belegt:** im Core-Worktree wurden `scripts/h1_truth_map.py`, `tests/test_h1_truth_map.py`, `docs/analysis/H1_TRUTH_MAP.md` und `docs/analysis/h1_truth_map.json` erstellt. Zentrale Befunde: Core-Worktree + Runtime-Tree sind die Primärwahrheit, `docs/API_REFERENCE.md` und `docs/API_COMPLETE.md` sind Legacy-Referenz.
- **H2 real durchgeführt:** `core_setup.py`-Syntaxblocker wurde entfernt, Runtime-`copilot_core`-Package um Repo-Brücke erweitert, `events_ingest`-Blueprint auf doppelfreie Registrierung korrigiert und H2-Reconciliation mit `scripts/h2_blueprint_reconcile.py`, `tests/test_h2_blueprint_reconcile.py`, `docs/analysis/H2_BLUEPRINT_RECONCILIATION.md`, `docs/analysis/h2_blueprint_reconciliation.json` erzeugt. Stand nach H2: 101 Blueprint-Config-Einträge geprüft, 57 OK, 44 Driftfälle offen; Testbasis aktuell grün mit `9 passed`.
- **H4 aus H2 abgeleitet:** `docs/analysis/H4_FIX_BACKLOG_FROM_H2.md` priorisiert die nächsten echten Fixbatches: zuerst `media_ui`-NameError, dann fehlende Modulpfade, dann Importbrüche und Attribut-Mismatches aus `blueprints_config.py`.
- **P0-1 bereits erledigt:** `copilot_core/api/v1/media_ui.py` nutzt wieder konsistent `media_ui_bp`; `tests/test_media_ui_contract.py` ergänzt; Reconciliation verbessert sich auf 58 OK / 43 Driftfälle bei insgesamt `10 passed` Testbasis.
- **P0-2/P1 erster großer Registry-Driftbatch erledigt:** `copilot_core/blueprints_config.py` wurde gegen reale Runtime-Module/Blueprint-Exporte geschärft (u. a. `automation_api`, `module_router_api`, `multihome`, `knowledge_graph.api`, `dashboard.api.v1.widget_positions` plus viele `bp`-Attr-Fixes). Zusätzlich erhielten `copilot_core/rootfs/usr/src/app/copilot_core/homeassistant/__init__.py` und `.../habitus/__init__.py` Subpackage-Bridges zurück ins Repo. Ergebnis: H2-Reconciliation sprang auf **89 OK / 12 Driftfälle**, Importfehler sanken auf **9**, Testbasis blieb grün mit `10 passed`.

---

*Last Updated: 2026-04-02 Europe/Berlin*  
*Next Review: 2026-04-03 00:00 Europe/Berlin (cron)*
