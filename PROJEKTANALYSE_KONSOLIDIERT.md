# PilotSuite Styx — Konsolidierte Projektanalyse

**Erstellt:** 2026-03-04
**Analysiert von:** Claude Code (Opus 4.6)
**Repos:** `pilotsuite-styx-core` + `pilotsuite-styx-ha`
**Aktuelle Version:** v13.1.0

---

## 1. Vision & Mission

**PilotSuite Styx** ist ein privacy-first, local-first AI-Assistent fuer Home Assistant, der Haushaltsmuster lernt, Empfehlungen erklaert und niemals die Benutzer-Governance umgeht.

### Non-negotiable Principles

| Prinzip | Bedeutung |
|---------|-----------|
| **Local-first** | Keine Cloud-Abhaengigkeit fuer Kernfunktionen |
| **Privacy-first** | PII-Redaktion, bounded Storage, opt-in |
| **Governance-first** | Vorschlaege vor Aktionen, Human-in-the-Loop |
| **Safe Defaults** | Fail safe unter Unsicherheit, degraded mode statt crash |
| **Explainability** | Jeder Vorschlag hat traceable Evidence |

### Normative Loop

```
HA States → Neuron Context → Mood/Intent Weighting → Pattern Mining → Candidate → User Decision → Feedback
```

Regeln:
- Kein direkter State-to-Action Shortcut im Default-Modus
- High-Risk Klassen bleiben manuell, es sei denn explizit eskaliert
- Feedback (accept/defer/dismiss) ist Teil des Learning Loops

---

## 2. Systemarchitektur

### Dual-Repo-System

```
Home Assistant
├── HACS Integration (copilot_ha)          ← pilotsuite-styx-ha
│   ├── 94+ Sensory Entities
│   ├── 15+ Dashboard Cards
│   ├── 31 Runtime Modules
│   ├── Configuration Flow (Wizard)
│   └── HTTP REST API Client
│       │
│       ↓ Token-Auth (X-Auth-Token)
│       │
├── Core Add-on (copilot_core)             ← pilotsuite-styx-core
│   ├── Brain Graph Engine
│   ├── Habitus Pattern Miner
│   ├── Mood Engine (3D: Comfort/Joy/Frugality)
│   ├── Candidate Management
│   ├── 14+ Context Neurons
│   ├── LLM Provider Chain (Ollama local + Cloud fallback)
│   ├── RAG Pipeline (BM25 + Semantic + RRF)
│   ├── Knowledge Graph Store
│   ├── 130+ REST API Endpoints
│   └── Ollama LLM Runtime (qwen3:0.6b)
│
└── Port: 8909
```

### Kommunikationspfade

**Forward Path (HA → Core):**
```
HA State Changes → Events Forwarder (batched N3 envelope) → POST /api/v1/events
→ EventProcessor → BrainGraph → Habitus Mining → Candidate Generation
```

**Return Path (Core → HA):**
```
Core Candidates → HA Candidate Poller (alle 30s) → GET /api/v1/candidates
→ HA Repairs Workflow → User Decision → PUT /api/v1/candidates/:id → Core Feedback Learning
```

**Realtime Path (Optional):**
```
Core Webhook Push → HA Coordinator Merge → Entity Refresh
```

---

## 3. Tech Stack

### pilotsuite-styx-core (Backend)

| Komponente | Technologie |
|-----------|-------------|
| Sprache | Python 3.11+ |
| Web Framework | Flask 3.1.3 |
| WSGI Server | Waitress (multi-threaded) |
| Deployment | Home Assistant Add-on (Docker) |
| Datenbank | SQLite (WAL mode) |
| Cache | Hybrid (Redis + Local LRU) |
| LLM Runtime | Ollama (gebundled) |
| Default Model | qwen3:0.6b |
| ML | scikit-learn (IsolationForest), scipy |
| Search | BM25 + Semantic + RRF Fusion |
| Port | 8909 |

### pilotsuite-styx-ha (Frontend Integration)

| Komponente | Technologie |
|-----------|-------------|
| Sprache | Python 3.11+ |
| Framework | Home Assistant Custom Integration |
| HA Minimum | >= 2024.1.0 |
| HTTP Client | aiohttp (async) |
| Distribution | HACS Repository |
| E2E Tests | Playwright |
| CI/CD | GitHub Actions |

---

## 4. Feature-Inventar

### 22+ Backend-Services (Core)

| Service | Funktion |
|---------|----------|
| BrainGraphStore | State-Graph mit Nodes + Edges, Decay, Snapshots |
| HabitusMiner | Association Rule Mining, Zone-basiert |
| MoodService | 3D-Scoring (Comfort/Joy/Frugality), SQLite-Persistenz |
| CandidateStore | Vorschlaege mit Governance-Workflow |
| NeuronManager | 14 Bewertungs-Neuronen |
| EventStore | Event-Persistenz und -Abfrage |
| VectorStore | Bag-of-Words Embedding, Similarity Search |
| KnowledgeGraph | Entity-Beziehungen |
| TagRegistry | Entity-Tagging |
| NotificationService | Push-System (9 Endpoints) |
| SharingService | Cross-Home Sharing (7 Endpoints) |
| CollectiveIntelligence | Federated Learning (15 Endpoints) |
| ConnectionPoolManager | HA + Ollama Connection Pooling |
| HybridCache | Redis + Local LRU Cache |
| SystemHealthService | Health Checks (Zigbee, Z-Wave, Recorder) |
| MediaZoneManager | Media-Zonen Verwaltung |
| MCPServer | Skills fuer externe AI-Clients |
| TelegramBot | Telegram Integration mit Tool-Calling |
| ModuleRegistry | Dynamic Module Discovery + Lifecycle |
| EnergyService | Energie-Monitoring |
| WeatherService | Wetter-Integration |
| CalendarService | Kalender-Integration |

### 31 Runtime Modules (HA Integration)

**Core Plumbing (5):** legacy, events_forwarder, candidate_poller, history_backfill, dev_surface
**Intelligence/Context (6):** habitus_miner, brain_graph_sync, mood, mood_context, ml_context, knowledge_graph_sync
**Domain Context (8):** energy_context, weather_context, media_zones, network, camera_context, frigate_bridge, unifi_module, unifi_context
**User/Governance (6):** character_module, entity_tags, quick_search, voice_context, ops_runbook, user_preference
**Home Operations (8):** home_alerts, waste_reminder, birthday_reminder, person_tracking, scene_module, calendar_module, homekit_bridge, performance_scaling

### 94+ Sensory Entities

- Brain Graph Sensors (Neuron states, connections)
- Habitus Sensors (Zone states, pattern confidence)
- Mood Sensors (Comfort, Joy, Frugality)
- Energy Sensors (Verbrauch, Forecasts)
- Activity Sensors (Presence, Motion)
- Anomaly Detection Sensors
- Cognitive Sensors (Belief scores, Attention)
- Calendar, Battery, Weather, Network Sensors

### 130+ REST API Endpoints (Core)

Kategorien: Events, Brain Graph, Habitus, Candidates, Neurons, Mood, RAG Search, Knowledge Graph, Tags, Notifications, Sharing, Federated Learning, Hub, Metrics, Health, Config, MCP, Telegram, Media Zones, Energy, Weather, Calendar

---

## 5. Gefundene Bugs & Fixes (diese Analyse-Session)

### Produktions-Code Bugs (BEHOBEN)

| Bug | Datei | Fix |
|-----|-------|-----|
| **RAG Cache Key ignoriert include_text/include_metadata** — Cache gibt Ergebnisse mit Text zurueck auch wenn include_text=False | `api/v1/rag.py` | Cache Key um include_text/include_metadata Flags erweitert |
| **AnomalyDetector.get_feature_names()** existiert nicht — Method existiert auf FeatureExtractor, nicht AnomalyDetector | `api/v1/anomaly.py` | `detector.get_feature_names()` → `detector._feature_names or []` |
| **Multihome Blueprint url_prefix falsch** — /api/v1 statt /api/v1/multihome | `app.py` | url_prefix korrigiert |
| **RAG cache.get() fehlender asyncio.run()** — synchroner Call auf async Methode | `api/v1/rag.py` | `asyncio.run(cache.get(cache_key))` |

### Test-Isolation Bugs (BEHOBEN — 25 Test-Failures → 0)

| Bug | Dateien | Fix |
|-----|---------|-----|
| **Rate Limiter Reset benutzt falsches Attribut** — `_windows.clear()` statt `reset()` | test_rag_hybrid_api.py, test_rag_hybrid_search.py | `limiter._windows.clear()` → `get_rate_limiter().reset()` |
| **RAG Cache Singleton nicht zurueckgesetzt** — Cached Ergebnisse "leaken" zwischen Tests | test_rag_hybrid_api.py, test_rag_hybrid_search.py | `rag_mod._rag_cache = None` in Fixtures |
| **psutil Mock globale Pollution** — `sys.modules['psutil'] = mock` ohne Cleanup | test_dev_surface_simple.py | save/restore Original-psutil in teardown_module() |
| **Auth Env-Var Pollution** — `os.environ.setdefault("COPILOT_AUTH_REQUIRED", "false")` permanent | test_rag_hybrid_api.py | Umgestellt auf monkeypatch.setenv() |

### Ergebnis

```
VORHER:  3439 passed, 25 FAILED
NACHHER: 3464 passed, 0 failed ✅
```

---

## 6. Code-Vision Abgleich

### Vision vs. Implementierung

| Vision-Aspekt | Status | Details |
|--------------|--------|---------|
| Local-first | ✅ Umgesetzt | Ollama gebundled, kein Cloud fuer Kernfunktionen |
| Privacy-first | ✅ Umgesetzt | N3 Privacy-Envelope, PII-Redaktion |
| Governance-first | ✅ Umgesetzt | Candidate → Repair → User Decision Loop |
| Safe Defaults | ✅ Umgesetzt | Circuit Breaker, degraded mode, fail-safe |
| Explainability | ⚠️ Teilweise | Evidence vorhanden, aber UX fuer Erklaerungen ausbaufaehig |
| Zero-Config | ✅ Umgesetzt | Auto-Discovery, Default-Module, Random Token |
| Dashboard UX | ⚠️ In Arbeit | 15+ Cards vorhanden, aber Styx Dashboard v1.0 noch ausstehend |
| Cross-Home Sharing | ⚠️ API Ready | 7+15 Endpoints implementiert, E2E noch nicht validiert |
| Advanced ML | ⚠️ Grundlagen | IsolationForest vorhanden, LSTM/TFLite noch ausstehend |

### Inkonsistenzen

1. **Version in DEVELOPMENT_PLAN.md** sagt v13.0.4, aber manifest.json zeigt v13.1.0 — Dokument nicht aktualisiert
2. **TODOS.md** referenziert v12.0.0 baselines — veraltet, sollte v13.x reflektieren
3. **PROJECT_STATUS.md** referenziert v7.7.16 — stark veraltet
4. **Test-Zahlen** in TODOS.md (2569 Tests) vs. tatsaechlich (3464+ Tests) — nicht aktualisiert

---

## 7. Entwicklungsplan & Phasen

### Abgeschlossene Phasen

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Foundation (Flask, Brain Graph, Habitus, Events) | ✅ Complete |
| Phase 2 | Stabilization (Circuit Breakers, SQLite WAL) | ✅ Complete |
| Phase 3 | Feature Expansion (Neurons, Mood, MUPL, 32 Module) | ✅ Complete |
| Phase 4 | Production Release (hassfest, HACS Integration) | ✅ Complete |
| Phase 5 | Cross-Home Sharing (31 Endpoints, Federated Learning) | ✅ Complete |
| Phase 6 | Type Hints & Tests (2526+ Tests, 98% Pass Rate) | ✅ Complete |

### Aktuelle Phase: Phase 7 — Production Readiness & Advanced ML

**Sprint 1-2: Stabilisierung** (aktuell)
- [x] Version-Sync HA+Core (v13.1.0)
- [x] 37 Broken API Routes gefixt
- [x] RAG Chat Pipeline umgeschrieben
- [x] 25 Test-Failures behoben (diese Session)
- [ ] Module Registry Refinement

**Sprint 3-4: Performance & Security**
- [x] Connection Pooling (28.5x Speedup)
- [x] Hybrid Cache (Redis + LRU)
- [ ] Prometheus Metrics Integration
- [ ] Security Headers (CSP, HSTS)

**Sprint 5-6: Dashboard & UX**
- [ ] Styx Dashboard v1.0
- [ ] RAG Search Frontend
- [ ] Zone Editor Frontend
- [ ] Mobile-responsive Design

**Sprint 7-8: Advanced ML**
- [ ] On-device Inference (TFLite/ONNX)
- [ ] Isolation Forest Anomaly Detection (Grundlage vorhanden)
- [ ] LSTM Time-Series Forecasting
- [ ] Energy Load Shifting

---

## 8. Arbeitsplan — Naechste Schritte

### Sofort (Sprint 1-2 abschliessen)

| # | Task | Prioritaet | Aufwand |
|---|------|-----------|---------|
| 1 | Veraltete Dokumentation aktualisieren (DEVELOPMENT_PLAN.md, TODOS.md, PROJECT_STATUS.md) | P1 | Klein |
| 2 | Module Registry Tests vervollstaendigen | P1 | Mittel |
| 3 | CHANGELOG.md konsolidieren (viele verstreute Release Notes) | P2 | Klein |

### Kurzfristig (Sprint 3-4)

| # | Task | Prioritaet | Aufwand |
|---|------|-----------|---------|
| 4 | Prometheus Metrics Endpoint vervollstaendigen | P1 | Mittel |
| 5 | Security Headers (CSP, HSTS, X-Frame-Options) | P1 | Klein |
| 6 | Rate Limiter Konfigurierbarkeit verbessern (derzeit hardcoded 15 req/endpoint) | P2 | Klein |
| 7 | Scene Pattern Extraction implementieren | P2 | Gross |
| 8 | Routine Pattern Extraction implementieren | P2 | Gross |

### Mittelfristig (Sprint 5-6)

| # | Task | Prioritaet | Aufwand |
|---|------|-----------|---------|
| 9 | Styx Dashboard v1.0 (Ingress) | P1 | Gross |
| 10 | RAG Search Frontend Card | P1 | Mittel |
| 11 | Zone Editor Frontend | P2 | Mittel |
| 12 | Mobile Dashboard Optimierung | P2 | Mittel |

### Langfristig (Sprint 7-8)

| # | Task | Prioritaet | Aufwand |
|---|------|-----------|---------|
| 13 | LSTM Time-Series Forecasting | P2 | Gross |
| 14 | TFLite/ONNX On-device Inference | P2 | Gross |
| 15 | Energy Load Shifting Algorithmus | P2 | Gross |
| 16 | MCP Phase 2 erweiterte Skills | P3 | Mittel |
| 17 | MUPL Vertiefung | P3 | Mittel |

---

## 9. Strategie-Empfehlungen

### 1. Dokumentations-Konsolidierung (Sofort)

Das Projekt hat **70+ Markdown-Dateien** im Root von pilotsuite-styx-core. Viele sind veraltete Iterations-Reports, Dev-Summaries und WhatsApp-Zusammenfassungen. **Empfehlung:**
- Veraltete Dokumente in `/docs/archive/` verschieben
- DEVELOPMENT_PLAN.md, TODOS.md, PROJECT_STATUS.md auf v13.1.0 aktualisieren
- Eine einzige ROADMAP.md als Single Source of Truth

### 2. Test-Stabilitaet absichern (Sofort)

Die 25 behobenen Test-Failures zeigen ein systemisches Problem: **Test-Isolation**. Empfehlungen:
- Globale Singletons (Rate Limiter, Cache, Module-Level State) in conftest.py zuruecksetzen
- Keine `sys.modules` Manipulation ohne Cleanup
- Integration Tests mit eigenen Fixture-Scopes
- CI-Job der Tests in **zufaelliger Reihenfolge** ausfuehrt (`pytest -p random`)

### 3. API-Versionierung (Kurzfristig)

130+ Endpoints ohne API-Versionierungsstrategie. Alle unter `/api/v1/`. Empfehlung:
- API Changelog pro Release
- Breaking Changes nur mit Major Version Bump
- OpenAPI Spec aktuell halten

### 4. Performance Monitoring (Kurzfristig)

Connection Pooling und Cache sind implementiert, aber Monitoring fehlt:
- Prometheus Metrics aktivieren
- Dashboard fuer Response Times, Cache Hit Rates, Queue Depths
- Alerting bei Performance-Degradation

### 5. Security Hardening (Kurzfristig)

- Rate Limiter Limits aus Umgebungsvariablen konfigurierbar machen
- Security Headers in allen Responses
- Input Validation Review (OWASP Top 10)
- Token Rotation Mechanismus

---

## 10. Release-Meilensteine

| Version | Geplant | Focus |
|---------|---------|-------|
| **v13.1.1** | 2026-03-07 | Dokumentations-Update, Test-Stabilitaet |
| **v13.2.0** | 2026-03-15 | Prometheus Metrics, Security Headers |
| **v14.0.0** | 2026-04-01 | Styx Dashboard v1.0, RAG Search Frontend |
| **v15.0.0** | 2026-05-01 | Scene/Routine Pattern Extraction |
| **v16.0.0** | 2026-06-01 | Advanced ML (LSTM, TFLite) |

---

## 11. Zusammenfassung

**PilotSuite Styx** ist ein ambitioniertes, gut strukturiertes Projekt mit klarer Vision und starker technischer Grundlage. Die Dual-Repo-Architektur ist sauber getrennt, die Kommunikationspfade sind validiert, und die Test-Abdeckung ist mit 3464+ Tests solide.

**Staerken:**
- Klare Vision und Prinzipien (Local-first, Privacy-first, Governance-first)
- Robuste Architektur mit Circuit Breakers, Connection Pooling, Hybrid Cache
- Umfangreiche API (130+ Endpoints)
- Gute Test-Abdeckung (3464 Tests, 0 Failures)
- Automatisierte CI/CD mit 15-Minuten Production Guard

**Handlungsbedarf:**
- Dokumentation konsolidieren und aktualisieren (70+ verstreute MD-Dateien)
- Test-Isolation systematisch absichern
- Monitoring & Observability aufbauen
- Dashboard UX fuer Endbenutzer finalisieren
- Advanced ML Features priorisieren

**Gesamtbewertung:** Das Projekt ist production-ready fuer den aktuellen Funktionsumfang. Der naechste grosse Schritt ist die Konsolidierung (Docs, Tests, Monitoring) bevor neue Features hinzugefuegt werden.
