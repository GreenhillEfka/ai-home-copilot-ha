# PilotSuite Styx — Entwicklungsplan & Vision

**Erstellt:** 2026-02-24  
**Status:** Aktiver Entwicklungsplan für PilotSuite 2.0

---

## 🎯 Vision

**PilotSuite Styx** ist ein privacy-first, lokaler KI-Assistent für Home Assistant, der:
- Die Muster deines Zuhauses lernt (Habitus)
- Die Stimmung und den Kontext bewertet (Mood)
- Intelligenten Automatisierungsvorschläge macht
- **Nur mit deiner Zustimmung** handelt (Governance-first)

### Non-negotiable Principles
| Prinzip | Bedeutung |
|---------|-----------|
| **Local-first** | Alles lokal, kein Cloud-API-Call für Kernfunktionen |
| **Privacy-first** | PII-Redaktion, bounded Storage, opt-in |
| **Governance-first** | Vorschläge vor Aktionen, Human-in-the-Loop |
| **Safe Defaults** | Fail safe unter Unsicherheit, degraded mode |
| **Explainability** | Jeder Vorschlag hat traceable Evidence |

---

## 📂 Dual-Repos-System

| Repo | Funktion | Status |
|------|----------|--------|
| `pilotsuite-styx-core` | Backend runtime, LLM, Brain Graph, Habitus, Candidates | v7.11.1 |
| `pilotsuite-styx-ha` | HACS Integration, Sensoren, Dashboard Cards, Module | v7.10.1 |

**Release-Baseline:** `7.11.1` (2026-02-24)

---

## 🔁 Groky Dev Loop — Optimierter Release-Workflow (seit v7.11.1)

```
Dev Loop (Phase 1-6)  →  Code Build  →  HA Release Pipeline  →  HA Conformance  →  Dev Loop Phase 7
```

### Schritte des Dev Loops:

1. **Phase 1: Repo Status** — Git fetch, status check
2. **Phase 2: Bugfix Round (P0)** — Error Isolation & Connection Pooling
3. **Phase 3: Feature Extension (P1/P2)** — SearXNG / Plugin System
4. **Phase 4: HA Conformance Check** — manifest.json, HACS structure
5. **Phase 5: HA Release Pipeline** — Version bump + Git + TAG + Push + **HA Conformance Check**
6. **Phase 6: Status Report** — Telegram an Mensch
7. **Phase 7: System Integrity** — Dashboard + UX Optimierung (**ERST NACH HA Release!**)

### HA Release Pipeline (Phase 5):

| Schritt | Aktion |
|---------|--------|
| **1** | CHANGELOG.md update (vX.Y.Z) |
| **2** | RELEASE_NOTES.md update |
| **3** | copilot_core/config.yaml version bump |
| **4** | copilot_core/manifest.json version bump |
| **5** | custom_components/ai_home_copilot/manifest.json version bump |
| **6** | Git commit + push to dev/groky-main |
| **7** | Checkout main + merge dev/groky-main |
| **8** | Git tag vX.Y.Z + push |
| **9** | **HA Conformance Check** (hassfest / hass check_config) |
| **10** | **Nur wenn OK → Phase 6/7 starten!** |

---

## 🏗️ Architektur

```
Home Assistant
+-- HACS Integration (ai_home_copilot)      <-- 94+ Sensoren, 28 Module, Dashboard
|     HTTP REST API (Token-Auth)
|     v
+-- Core Add-on (copilot_core) Port 8909    <-- Brain Graph, Habitus, Mood, LLM
      + Ollama (bundled, qwen3:0.6b default)
      + optional Cloud Fallback (ollama.com API)
```

### 22 Backend-Services (pilotsuite-styx-core)
| Service | Funktion |
|---------|----------|
| BrainGraphStore | State-Graph mit Nodes + Edges, Decay, Snapshots |
| HabitusMiner | Association Rule Mining, Zone-basiert |
| MoodService | 3D-Scoring (Comfort/Joy/Frugality), SQLite-Persistenz |
| CandidateStore | Vorschläge mit Governance-Workflow |
| NeuronManager | 14 Bewertungs-Neuronen |
| EventStore | Event-Persistenz und -Abfrage |
| VectorStore | Bag-of-Words Embedding, Similarity Search |
| KnowledgeGraph | Entity-Beziehungen |
| TagRegistry | Entity-Tagging |
| SearchIndex | Entity-Suche |
| NotificationService | Push-System |
| WeatherService | Wetter-Integration |
| EnergyService | Energie-Neuron |
| UserPreferenceStore | Per-User Präferenzen |
| HouseholdService | Familienkonfiguration |
| CalendarService | Kalender-Integration |
| CharacterService | Styx-Persönlichkeit |
| SystemHealthService | Health Checks (Zigbee, Z-Wave, Recorder) |
| MediaZoneManager | Media-Zonen Verwaltung |
| DevSurface | Debug/Diagnose Endpunkte |
| MCPServer | 8 Skills für externe AI-Clients |
| CollectiveIntelligence | Cross-Home Sharing (Phase 5) |

---

## 🔄 Aktueller Entwicklungs-Status (2026-02-24)

### ✅ Implemented Features (v7.10.1)
- **Plugin System v1** — base classes, search/llm plugins, React backend API
- **SearXNG Integration** — local web search (plugin)
- **LLM Plugin** — Ollama/Cloud integration (qwen3-coder-next:cloud, glm-5:cloud)
- **Web UI Toggle API** — `/api/plugins/*`
- **Cross-Home Sharing** — federated learning, model aggregation
- **Scene Extraction** — full scene management with presets
- **Push Notifications** — comprehensive notification system

### ✅ API Endpoints (31 total)
| Bereich | Endpoints | Beschreibung |
|---------|-----------|-------------|
| System | `/health`, `/version`, `/api/v1/status` | Health, Version, Capabilities |
| Chat | `/v1/chat/completions`, `/v1/models` | OpenAI-kompatibel |
| Brain Graph | `/api/v1/graph/*` | State, Snapshot, Stats, Patterns |
| Habitus | `/api/v1/habitus/*` | Status, Rules, Mine, Dashboard |
| Candidates | `/api/v1/candidates/*` | CRUD, Stats, Cleanup |
| Mood | `/api/v1/mood/*` | Mood Query, Update, History |
| Neurons | `/api/v1/neurons/*` | Neuron State, Evaluation |
| Events | `/api/v1/events` | Event Ingest + Query |
| Tags | `/api/v1/tag-system/*` | Tags, Assignments |
| Search | `/api/v1/search/*` | Entity Search, Index |
| Knowledge Graph | `/api/v1/kg/*` | Nodes, Edges, Query |
| Vector Store | `/api/v1/vector/*` | Store, Search, Stats |
| Weather | `/api/v1/weather/*` | Wetterdaten |
| Energy | `/api/v1/energy/*` | Energiemonitoring |
| Notifications | `/api/v1/notifications/*` | Push System (9 endpoints) |
| Sharing | `/api/v1/sharing/*` | Sharing, sync, discovery (7 endpoints) |
| Federated | `/api/v1/federated/*` | Federated learning (15 endpoints) |

---

## 📊 Cron-Jobs & Orchestrator

### Groky Dev Check (every 10min)
- **Agent:** `groky` (ollama/qwen3-coder-next:cloud, fallback: claude-opus-4.6)
- **Schedule:** `*/10 * * * *` (Europe/Berlin)
- **Workspace:** `/config/.openclaw/workspace`
- **Phasen:**
  1. Repo Status (Git fetch, log, status)
  2. Bugfix Round (P0: Error isolation, Connection pooling)
  3. Feature Extension (P1/P2: SearXNG, Plugin registry)
  4. HA Conformance (manifest.json, HACS structure)
  5. Release + Notes (Auto-increment, CHANGELOG, commit+tag+push)
  6. Status Report (Telegram to human)
  7. System Integrity (Dashboard + API validation, UX stress test)

**Ziel:** Jeder Loop = **SAUBERES RELEASE** (vX.Y.Z) → main (keine dev branches)

### Styx HA Release Check (every 15min)
- **Agent:** `styx` (ollama/qwen3-coder-next:cloud, fallback: claude-opus-4.6)
- **Schedule:** `*/15 * * * *` (Europe/Berlin)
- **Ziel:** Release-ready changes prüfen

---

## 🔧 Werkzeuge & Infrastruktur

### Ollama Setup
- **Service:** `ollama serve` (PID 1482)
- **Host:** `http://127.0.0.1:11434`
- **API Key:** Konfiguriert in Ollama config
- **Cloud Models (Remote Proxies):**
  - `ollama/qwen3-coder-next:cloud` → ✅ funktioniert
  - `ollama/glm-5:cloud` → ✅ funktioniert
  - `ollama/kimi-k2.5:cloud` → ❌ nicht gefunden
  - `ollama/minimax-m2.5:cloud` → ❌ nicht gefunden

**Wichtig:** Cloud Models (`:cloud`) sind Remote Proxies zu ollama.com, nicht lokal!

### Gateway & OpenClaw
- **Gateway:** `ws://127.0.0.1:18790` (foreground, PID 177)
- **Agenten:** `groky`, `styx`, `grok-4`, `qwen3-coder-next-cloud`, `claudya`, `viewona`, `codex`, `gemini`, `claude-sonnet-4-5`, `perplexya`, `cowdya`
- **Telegram Channel:** `1616970089` (enabled)

---

## 🎯 Nächste Schritte (P0 – Critical)

| Task | Status | Details |
|------|--------|---------|
| Cronjobs reparieren | ❌ WIP | Delivery channel ist "missing" |
| Error Isolation | ✅ Implemented | Module-Fehler isolieren, Crash-Kaskaden verhindern |
| Connection Pooling | ✅ Implemented | Resource-Leaks bei HA-Sessions verhindern |

---

## 🎯 Nächste Schritte (P1 – Important)

| Task | Status | Details |
|------|--------|---------|
| Scene Pattern Extraction | ✅ Implemented | User-Verhalten (Szenen-Aktivierung) Muster lernen |
| Routine Pattern Extraction | ✅ Implemented | tageszeitbasierte/wochentagsbasierte Rückschlüsse |
| Push Notifications | ✅ Implemented | Styx als zentraler Notify-Service (Mobile App, Telegram, Email) |
| Dashboard + UX Optimierung | ❌ WIP | Phase 7: Dashboard endpoint, API routes validation, UX stress test |

---

## 🎯 Nächste Schritte (P2 – Nice to have)

| Task | Status | Details |
|------|--------|---------|
| MCP Phase 2 | ⏳ Planung | Erweiterte Skills für AI-Clients |
| Test Suite Expansion | ⏳ Planung | Regressionssicherheit, Integrationstests |
| Multi-User Preference Learning | ⏳ Planung | MUPL深化 (bereits v0.8.x integriert, aber erweiterbar) |

---

## 🚀 Release Process

### Production Release Gate
Ein Release ist production-ready **nur wenn alle** folgende Bedingungen erfüllt sind:
1. Local critical tests green (`pytest -q tests/test_api_endpoints.py`)
2. Main CI green (GitHub Actions)
3. Production-guard workflow green (15-min cron in beiden repos)
4. Versions/changelogs/docs synchronized (pilotsuite-styx-core + -ha)

### Release Workflow (Groky Dev Check)
1. Repo Check (Git status, commits)
2. Quality Gate (Tests, Error isolation, Pool health)
3. Feature Extension (SearXNG, Plugins)
4. HA Conformance (manifest.json, HACS structure)
5. Auto-increment + CHANGELOG + commit + tag + push
6. Telegram Status Report

**Branch Policy:** **KEINE dev branches** — direkt nach `main`

---

## 📖 Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [README.md](README.md) | Installation, Features, API Overview |
| [VISION.md](VISION.md) | Mission, Principles, Architecture |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Production Audit, Module Status |
| [CHANGELOG.md](CHANGELOG.md) | Release History (v7.10.1) |
| [PHASE5_TODO.md](PHASE5_TODO.md) | Cross-Home Sharing, Push Notifications |
| [TODOS.md](TODOS.md) | P0/P1/P2 Tasks |
| [AGENTS.md](AGENTS.md) | Repository Guidelines |
| [docs/ARCHITECTURE.md](docs/) | Services, Data Flow, Persistence |
| [docs/ROADMAP.md](docs/) | Phase 5-6, Future Plans |

---

## 🧪 Testing

### Test Commands
```bash
# Core tests (recommended local loop)
cd /config/.openclaw/workspace/copilot_core/rootfs/usr/src/app
pytest -q tests/test_api_endpoints.py

# Dashboard/API regression tests
pytest -q tests/test_dashboard_endpoints.py tests/test_llm_provider_fallback.py

# Single test file
pytest -q tests/test_dashboard_template_habitus.py
```

### Test Coverage
- **Core:** 1959 passed, 1 skipped
- **HA Integration:** 527 passed, 5 skipped
- **Communication Roundtrip:** Integriert und passing

---

## 🌟 Besonderheiten

### Local-first Design
- Alles lokal, kein Cloud-API-Call für Kernfunktionen
- Cloud Fallback nur optional und ausnutzbar (Ollama Cloud API Key)

### Privacy-first Design
- PII-Redaktion in allen Logs und Responses
- Bounded Storage (max 500 Nodes, 1500 Edges)
- Opt-in Persistenz

### Governance-first Design
- Vorschläge vor Aktionen (Human-in-the-Loop)
- Feedback-Loop (accept/defer/dismiss)
- Traceable Evidence für jeden Vorschlag

---

## 📝 Notes

- **SoUL.md** beschreibt die Persönlichkeit von OpenClaw
- **TOOLS.md** beschreibt meine Setup-spezifischen Notizen
- **IDENTITY.md** beschreibt, wer ich bin (AI-Assistent)
- **USER.md** beschreibt, wer Andreas ist (my human)

---

**Letzte Aktualisierung:** 2026-02-24  
**Entwickelt mit:** Groky Dev Check (every 10min)  
**Basiert auf:** pilotsuite-styx-core v7.10.1 + pilotsuite-styx-ha v7.10.1
