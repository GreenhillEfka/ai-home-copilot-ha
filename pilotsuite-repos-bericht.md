# PilotSuite Repositories — Vergleichsbericht

**Stand:** 28. Februar 2026  
**Version:** 11.1 (beide Repos)  
**Autor:** GreenhillEfka  
**Recherche:** Subagent via OpenClaw

---

## 1. Repository-Übersicht und Zweck

### 1.1 pilotsuite-styx-core
**URL:** https://github.com/GreenhillEfka/pilotsuite-styx-core  
**Typ:** Home Assistant Add-on (Docker-Container)  
**Rolle:** "Das Gehirn + Stimme"

**Zweck:**
- Hostet den Ollama LLM-Server (lokal, Port 11435 intern)
- Brain Graph Store (In-Memory Wissensgraph mit SQLite-Persistenz)
- Habitus Pattern Mining (Association Rule Learning)
- Mood Engine (3D-Scoring: Comfort/Joy/Frugality)
- 14 Bewertungs-Neuronen (60s Evaluations-Loop)
- RAG/Vector Store für semantische Suche
- OpenAI-kompatible API (`/v1/chat/completions`)
- Telegram Bot mit Server-side Tool-Execution
- MCP Server für externe AI-Clients
- Flask + Waitress auf Port 8909

**Haupt-Services (45+):**
- BrainGraphStore, HabitusMiner, MoodService, CandidateStore
- NeuronManager, EventProcessor, LLMProvider, VectorStore
- RAGService, ConversationMemory, WebhookPusher
- ProactiveContextEngine, ZoneAutomationController
- 17 Hub Engines (Anomaly, Energy, Light, Presence, etc.)

---

### 1.2 pilotsuite-styx-ha
**URL:** https://github.com/GreenhillEfka/pilotsuite-styx-ha  
**Typ:** Home Assistant Custom Integration (HACS)  
**Rolle:** "Die Sinne + Hände"

**Zweck:**
- Liest HA-States (4520+ Entities)
- Erstellt Sensoren/Entities (140+ Entities, 94+ Sensoren)
- Dashboard-Generierung (Lovelace YAML)
- Config Flow + Options Flow (Setup-UI)
- Events Forwarder (HA → Core, N3 Batching)
- Webhook-Empfänger (Core → HA Push)
- Repairs UI für Governance-Vorschläge
- 36+ Runtime-Module in 4 Tiers

**Modul-Architektur (4-Tier-System):**
- **TIER 0 — KERNEL** (6 Module, kein Opt-Out): legacy, coordinator, events_forwarder, entity_tags, brain_graph_sync, performance_scaling
- **TIER 1 — BRAIN** (12 Module, wenn Core erreichbar): knowledge_graph_sync, habitus_miner, candidate_poller, mood, mood_context, zone_sync, etc.
- **TIER 2 — KONTEXT** (7 Module, bei relevanten Entities): energy_context, weather_context, media_zones, camera_context, network, ml_context, voice_context
- **TIER 3 — ERWEITERUNGEN** (12 Module, explizit aktivieren): homekit_bridge, frigate_bridge, calendar_module, home_alerts, character_module, waste_reminder, birthday_reminder, automation_analyzer, etc.

---

### 1.3 Weitere PilotSuite-bezogene Repos

**Gesucht nach weiteren Repos im GreenhillEfka-Organization:**
- Keine weiteren öffentlichen PilotSuite-Repos gefunden (Stand: Feb 2026)
- Die Plattform besteht bewusst aus **zwei Repos** (Dual-Repo-Architektur)
- Dokumentation ist in den Haupt-Repos enthalten (`docs/`-Ordner)

---

## 2. Abhängigkeiten zwischen den Repos

### 2.1 Kommunikationsarchitektur

```
┌─────────────────────────────────────┐     ┌─────────────────────────────────────┐
│  pilotsuite-styx-ha (HACS)          │     │  pilotsuite-styx-core (Add-on)      │
│  "Die Sinne + Haende"               │     │  "Das Gehirn + Stimme"              │
│                                     │     │                                     │
│  - Liest HA-States (4520+ Entities) │     │  - Ollama LLM (qwen3:0.6b/4b)      │
│  - Erstellt Sensoren/Entities       │     │  - Brain Graph (500 Nodes)          │
│  - Dashboard-Generierung (YAML)     │     │  - Habitus Mining (A→B Patterns)    │
│  - Config Flow (UI)                 │     │  - 14 Evaluations-Neuronen          │
│  - Webhook-Empfaenger               │     │  - Event Processing Pipeline        │
│  - Event-Forwarder (N3 Batching)    │     │  - Mood Engine (3D Scoring)         │
│  - Conversation Agent (Proxy)       │     │  - Vector Store + RAG               │
│  - Self-Healing (Repair Issues)     │     │  - Candidate Store (Governance)     │
│  - Suggestion Panel (UI)            │     │  - 17 Hub Engines                   │
│  - Live Mood (lokaler Fallback)     │     │  - Webhook-Pusher → HA              │
│  - Zone Bootstrap + Auto-Setup      │     │  - Telegram Bot                     │
│  - 36+ Module in 4 Tiers            │     │  - MCP Server + SearXNG             │
│                                     │     │  - OpenAI-kompatibler Endpoint      │
│  Python: HA asyncio Framework       │     │  Flask+Waitress, Port 8909          │
│  Kein eigener Server moeglich       │     │  Docker-Container (HA Add-on)       │
└──────────────┬──────────────────────┘     └──────────────┬──────────────────────┘
               │           REST API + Webhooks             │
               └───────────────────────────────────────────┘
```

### 2.2 HA → Core (REST API)

Die HA-Integration nutzt `CopilotApiClient` (aiohttp) mit Multi-URL-Failover:

| Endpoint | Methode | Modul | Zweck |
|----------|---------|-------|-------|
| `/api/v1/events` | POST | EventsForwarder | Batched HA Events (N3 Envelope) |
| `/v1/chat/completions` | POST | Conversation | LLM Chat (OpenAI-kompatibel) |
| `/api/v1/neurons/mood` | GET | Coordinator | Mood-Zustand abfragen |
| `/api/v1/neurons` | GET | Coordinator | Alle 14 Neuronen-States |
| `/api/v1/neurons/evaluate` | POST | Coordinator | Neural Pipeline mit HA-Kontext |
| `/api/v1/candidates` | GET | CandidatePoller | Vorschlaege abholen (5min) |
| `/api/v1/candidates/{id}` | PUT | Repairs | Feedback zurueckmelden |
| `/api/v1/graph/state` | GET/POST | BrainGraphSync | Entity-Graph synchronisieren |
| `/api/v1/habitus/rules` | GET | Coordinator | Entdeckte Muster |
| `/api/v1/habitus/zones/sync` | POST | ZoneBootstrap | Zonen-Konfiguration synchronisieren |
| `/health` | GET | Coordinator | Health Check (120s Polling) |
| `/version` | GET | Coordinator | Core-Version |

**Authentifizierung:** `Authorization: Bearer <token>` + `X-Auth-Token: <token>` (Legacy)

**Failover:** Primary → HA internal_url → HA external_url → homeassistant.local → localhost → 127.0.0.1

### 2.3 Core → HA (Webhook Push)

Der Core pusht Echtzeit-Updates an die HA-Integration:

| Event-Typ | Payload | Aktion in HA |
|-----------|---------|-------------|
| `mood_changed` | `{mood, confidence, dimensions}` | Merge in `coordinator.data["mood"]` |
| `neuron_update` | `{neurons: {...}}` | Merge in `coordinator.data["neurons"]` |
| `suggestion_new` | `{suggestion data}` | Fire Event `ai_home_copilot_suggestion_received` |
| `proactive_suggestion` | `{suggestion data}` | Fire Event `ai_home_copilot_proactive_suggestion` |
| `status` | `{online, version}` | Update `coordinator.data["ok"]` |

### 2.4 Hybrid-Modus

```
Primaer:   Core → Webhook Push → HA (Echtzeit, <100ms)
Fallback:  HA → REST Polling → Core (alle 120 Sekunden)
```

Der Coordinator fusioniert beide Datenströme. Bei Webhook-Ausfall übernimmt Polling automatisch.

---

## 3. Build/Deploy-Prozess

### 3.1 Versionierung

Beide Repos werden **zusammen** versioniert und released:

```
HA v11.1.0  ←→  Core v11.1.0   (Paired Release)
```

Major/Minor-Mismatch wird dem Nutzer als HA Repair Issue angezeigt.

### 3.2 Release-Prozess

1. Feature in **beiden** Repos implementieren (wenn beidseitig relevant)
2. Tests in beiden Repos ausführen
3. Version in beiden `manifest.json` bumpen
4. Git Tag + GitHub Release in beiden Repos
5. HACS erkennt neues Release automatisch

### 3.3 Installation — Core Add-on

```
1. Home Assistant → Settings → Add-ons → Add-on Store
2. Menue (⋮) → Repositories → URL hinzufuegen:
   https://github.com/GreenhillEfka/pilotsuite-styx-core
3. PilotSuite Core installieren und starten
4. Das Add-on laeuft auf Port 8909 mit bundled Ollama
```

### 3.4 Installation — HACS Integration

```
1. HACS oeffnen
2. Integrations → Menue (⋮) → Custom repositories
3. URL eingeben: https://github.com/GreenhillEfka/pilotsuite-styx-ha
   Typ: Integration
4. PilotSuite installieren und Home Assistant neustarten
5. Settings → Devices & services → Add integration → PilotSuite
6. Zero Config waehlen — Styx startet sofort mit Standardwerten
```

### 3.5 Kompatibilitätsregeln

| Regel | Beschreibung |
|-------|-------------|
| **API-Stabilitaet** | Endpoint-Pfade und Payloads nur additiv aendern |
| **Fallback** | HA muss auch bei Core-Ausfall starten koennen |
| **Graceful Degradation** | Fehlende Core-Features → leere Sensoren, kein Crash |
| **Token-Format** | Bearer + X-Auth-Token parallel unterstuetzen |
| **Webhook-Format** | Event-Typen nur additiv erweitern |

---

## 4. Wichtige Dateien und Konfigurationen

### 4.1 pilotsuite-styx-core

**Add-on Metadata:**
- `config.yaml` — Add-on Konfiguration
- `build.yaml` — Build-Konfiguration
- `Dockerfile` — Container-Definition

**Runtime App:**
- `copilot_core/rootfs/usr/src/app/` — Hauptanwendung
- `copilot_core/rootfs/usr/src/app/copilot_core/` — API und Services
- `copilot_core/rootfs/usr/src/app/templates/` — Dashboard Templates
- `copilot_core/rootfs/usr/src/app/static/` — Statische Assets
- `copilot_core/rootfs/usr/src/app/start_dual.sh` — Startup Script
- `copilot_core/rootfs/usr/src/app/tests/` — Tests

**Dokumentation:**
- `docs/ARCHITECTURE_DUAL_REPO.md` — Gesamtkonzept
- `docs/API_REFERENCE.md` — Alle Endpoints, Auth, Request/Response
- `docs/ARCHITECTURE.md` — Core-seitige Services
- `docs/ONYX_INTEGRATION.md` — Onyx + Styx Zielarchitektur
- `docs/ROADMAP.md` — Zukunftspläne
- `CHANGELOG.md` — Release-Historie

**Wichtige Konfigurationen (im Add-on):**
- `auth_token` — API-Token für HA-Integration
- `conversation_cloud_api_url` — Cloud-Fallback URL
- `conversation_cloud_api_key` — Cloud-API-Key
- `conversation_cloud_model` — Cloud-Modell (z.B. gpt-4o-mini)
- `conversation_prefer_local` — true = Ollama zuerst, dann Cloud-Fallback

### 4.2 pilotsuite-styx-ha

**Hauptdateien:**
- `custom_components/ai_home_copilot/__init__.py` — Integration Setup
- `custom_components/ai_home_copilot/manifest.json` — HA Manifest
- `custom_components/ai_home_copilot/const.py` — Alle Konstanten
- `custom_components/ai_home_copilot/coordinator.py` — DataUpdateCoordinator + API-Client
- `custom_components/ai_home_copilot/config_flow.py` — Config Flow
- `custom_components/ai_home_copilot/config_options_flow.py` — Options Flow

**Core-Module:**
- `custom_components/ai_home_copilot/core/module.py` — CopilotModule Protocol
- `custom_components/ai_home_copilot/core/registry.py` — ModuleRegistry
- `custom_components/ai_home_copilot/core/runtime.py` — CopilotRuntime (Singleton)

**Wichtige Module:**
- `forwarder_n3.py` — N3 Event Forwarder (775 Zeilen)
- `habitus_zones_store_v2.py` — Zone Store v2 (1050 Zeilen)
- `storage.py` — Candidate Storage
- `repairs.py` — Repairs UI Flows (Governance)

**Dokumentation:**
- `docs/ARCHITECTURE_DUAL_REPO.md` — Dual-Repo Gesamtkonzept
- `docs/ARCHITECTURE.md` — HA-seitige Architektur
- `docs/HANDBOOK.md` — Setup, Module, Sensoren, Zonen
- `docs/DEVELOPER_GUIDE.md` — CI, Tests, Release-Prozess
- `CHANGELOG.md` — Release-Historie

**Persistente Daten (in `.storage/`):**
- `ai_home_copilot.habitus_zones_v2` — Zone-Definitionen
- `ai_home_copilot.habitus_zones_state` — Zone-Zustände
- `ai_home_copilot.candidates` — Candidate-Status
- `ai_home_copilot_n3_forwarder` — Event Queue
- `ai_home_copilot.entity_tags` — Entity-Tags
- `ai_home_copilot.config_snapshots` — Config-Snapshots

**Dashboard-Generierung:**
- `/config/pilotsuite-styx/pilotsuite_dashboard_latest.yaml`
- `/config/pilotsuite-styx/habitus_zones_dashboard_latest.yaml`

---

## 5. Integration zwischen Core und HA

### 5.1 Datenfluss (End-to-End)

#### Event-Pipeline
```
1. HA State Change (z.B. light.wohnzimmer → on)
   │
   ▼
2. EventsForwarder (HA)
   │ Batched (50 Events), PII-redacted, Idempotent
   │
   ▼
3. POST /api/v1/events ──▶ Core Event Store
   │
   ├──▶ Brain Graph Update (Nodes + Edges)
   ├──▶ Habitus Mining (A→B Patterns)
   └──▶ Neuronen-Evaluation (60s Loop)
        │
        ├──▶ Mood Scoring (Comfort/Joy/Frugality)
        └──▶ Candidate Generation (Vorschlaege)
             │
             ├── Webhook Push → HA (mood_changed, suggestion_new)
             └── REST Polling ← HA (GET /api/v1/candidates)
```

#### Chat-Pipeline
```
User spricht mit Styx (HA Conversation Agent)
   │
   ▼
conversation.py (HA)
   │ 1. System-Prompt bauen (lokal):
   │    - Live Mood, Zonen, Personen, Wetter
   │    - Top-3 Vorschlaege, Automations-Analyse
   │    (max 2000 Zeichen)
   │
   ▼
   │ 2. POST /v1/chat/completions ──▶ Core LLM Provider
   │                                      │
   │                                      ├─ Ollama (lokal, Port 11435)
   │                                      │  qwen3:0.6b (400MB) oder qwen3:4b (2.5GB)
   │                                      │
   │                                      ├─ Cloud Fallback (optional)
   │                                      │
   │                                      └─ Tool Calling (8+ Tools):
   │                                         - execute_ha_tool (HA Services steuern)
   │                                         - execute_create_automation
   │                                         - execute_web_search (SearXNG)
   │                                         - execute_play_zone (Sonos)
   │                                         - execute_waste_status
   │                                         - execute_get_news / get_warnings
   │                                         └─ ...
   ▼
Antwort zurueck an User (mit Kontext + Tool-Ergebnissen)
```

**Ohne Core = kein LLM = kein Chat.** Ollama läuft im Core-Container.

#### Suggestion-Pipeline
```
Quellen:                                              Ziel:
┌─────────────────────────┐
│ 1. initial_suggestions  │ (lokal, einmalig)
│    .json                │──┐
└─────────────────────────┘  │
┌─────────────────────────┐  │
│ 2. AutomationAnalyzer   │  │    ┌──────────────┐    ┌──────────────────┐
│    (lokal, HA Event)    │──┼──▶ │ Suggestion   │──▶ │ SuggestionPanel  │
└─────────────────────────┘  │    │ Loader (T1)  │    │ (WebSocket UI)   │
┌─────────────────────────┐  │    └──────────────┘    └────────┬─────────┘
│ 3. Core Webhook         │  │                                 │
│    (proactive_suggestion│──┤                                 ▼
└─────────────────────────┘  │                          Accept / Reject
┌─────────────────────────┐  │                                 │
│ 4. Core Polling         │  │                                 ▼
│    (suggestion_received)│──┘                          MUPL Feedback
└─────────────────────────┘                             (Preference Learning)
```

Quellen 1+2 funktionieren ohne Core. Quellen 3+4 liefern die **intelligenten** Vorschläge (aus Brain Graph + Neuronen + Pattern Mining).

#### Governance-Pipeline
```
Core erkennt Muster → Candidate Store (pending)
     │
     ▼
CandidatePoller (HA, 5min) → GET /api/v1/candidates
     │
     ▼
HA Repairs UI / SuggestionPanel (Nutzer sieht Vorschlag)
     │
     ▼
Nutzer: Akzeptieren / Verschieben / Ablehnen
     │
     ▼
PUT /api/v1/candidates/{id} → Feedback an Core
     │
     ▼
Brain Graph lernt aus Entscheidung
```

**Kein Vorschlag wird automatisch umgesetzt.** Jeder Vorschlag braucht explizite Nutzer-Zustimmung.

### 5.2 Was funktioniert OHNE Core?

- HA-Integration startet und läuft (Coordinator zeigt `ok: false`)
- Live Mood Engine (lokaler Fallback aus Entity-States)
- Dashboard-Generierung (rein lokal aus Zonen-Config)
- Automation Analyzer (lokale Analyse der HA-Automationen)
- Self-Healing Repair Issues (lokal)
- Zero-Config Auto-Setup (Zonen + Entity Classifier)
- Alle Config Flows und Options Flows
- SuggestionLoader (Quellen 1+2: JSON + Analyzer)

### 5.3 Was braucht zwingend Core?

- **LLM/Chat** (Ollama läuft im Core-Container)
- **Brain Graph** (persistenter Graph-Store)
- **Pattern Mining** (Habitus: Association Rules)
- **Neuronen-Evaluation** (14 Neuronen alle 60s)
- **RAG/Embeddings** (Vector Store)
- **Proaktive Vorschläge** (ProactiveContextEngine)
- **Tool Calling** (LLM steuert HA-Services)
- **Telegram Bot** (Server-Prozess)
- **Zone Automation** (Multi-Signal Controller)
- **Override Modes** (Party/Vacation/Sleep)
- **Intelligente Suggestions** (Quellen 3+4)

### 5.4 Technische Trennung — Warum zwei Repos?

**HA Custom Integrations** laufen _innerhalb_ des HA-Prozesses — sie können:
- Sensoren erstellen
- Events lauschen
- Webhooks empfangen

Aber sie können **nicht**:
- Eigene HTTP-Server hosten
- Langlebige Prozesse betreiben
- Ollama hosten

**Core Add-on** läuft als eigenständiger Docker-Container und kann all das.

---

## 6. LLM-Modelle und API

### 6.1 Verfügbare Modelle

| Modell | Größe | Tool-Calling | Beschreibung |
|--------|-------|-------------|--------------|
| `qwen3:0.6b` | 400 MB | Ja | Default: schnell, low-RAM, Tool-Calling |
| `qwen3:4b` | 2.5 GB | Ja | Optional für höhere Antwortqualität |
| `lfm2.5-thinking` | 731 MB | Nein | Optionales Legacy-Modell |
| `llama3.2:3b` | 2 GB | Ja | Meta 3B, 128K Kontext |
| `mistral:7b` | 4 GB | Ja | Bewährtes Function-Calling |
| `fixt/home-3b-v3` | 2 GB | Ja | HA-optimiert, 97% Genauigkeit |

### 6.2 OpenAI-kompatible API

**Base-URL:** `http://<host>:8909/v1`

**Beispiel:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://homeassistant.local:8909/v1",
    api_key="<token>"
)

response = client.chat.completions.create(
    model="qwen3:0.6b",
    messages=[{"role": "user", "content": "Schalte das Licht ein"}]
)
```

---

## 7. Sicherheit und Privacy

### 7.1 Prinzipien

| Prinzip | Bedeutung |
|---------|-----------|
| **Local-first** | Alles lokal, keine Cloud-Abhängigkeit |
| **Privacy-first** | PII-Redaktion, bounded Storage, opt-in |
| **Governance-first** | Vorschläge vor Aktionen, Human-in-the-Loop |
| **Safe Defaults** | Sicherheitsrelevante Aktionen immer Manual Mode |

### 7.2 PII-Redaktion (Events Forwarder)

- **Domain-Projektionen:** Nur erlaubte Attribute pro Domain
- **Globale Redaktion:** GPS-Koordinaten, Tokens, Zugangsschlüssel immer entfernt
- **Sensitive-Key-Pattern:** Regex `/token|key|secret|password/i` matcht und entfernt
- **Context-ID-Trunkierung:** Context-IDs werden auf 12 Zeichen gekürzt
- **Friendly-Name:** Standardmäßig entfernt (opt-in)

### 7.3 Circuit Breaker

| Service | Failure Threshold | Recovery Timeout |
|---------|-------------------|-----------------|
| `ha_supervisor` | 5 Fehler | 30 Sekunden |
| `ollama` | 3 Fehler | 60 Sekunden |

### 7.4 Rate Limiting

| Endpoint | Requests pro Minute |
|----------|---------------------|
| `/api/v1/events` | 200 |
| `/api/v1/habitus` | 100 |
| `/v1/chat/completions` | 60 pro Stunde |

---

## 8. Zusammenfassung

**PilotSuite Styx** ist eine duale Architektur aus:

1. **pilotsuite-styx-core** — Das Backend (Add-on) mit LLM, Brain Graph, Pattern Mining
2. **pilotsuite-styx-ha** — Die Frontend-Integration (HACS) mit Sensoren, Dashboards, UI

**Kommunikation:** REST API (HA → Core) + Webhook Push (Core → HA)

**Philosophie:** Local-first, Privacy-first, Governance-first — alles läuft lokal, Vorschläge brauchen Nutzer-Zustimmung, keine Cloud-Abhängigkeit.

**Version:** 11.1 (beide Repos synchron versioniert)

**Installation:** Core zuerst, dann HACS Integration, Zero-Config Setup möglich.

---

*Bericht erstellt am 28.02.2026 via OpenClaw Subagent*
