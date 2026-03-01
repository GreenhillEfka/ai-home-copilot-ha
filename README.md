# PilotSuite — Styx (Core Add-on)

[![Release](https://img.shields.io/github/v/release/GreenhillEfka/pilotsuite-styx-core)](https://github.com/GreenhillEfka/pilotsuite-styx-core/releases)
[![CI](https://github.com/GreenhillEfka/pilotsuite-styx-core/actions/workflows/ci.yml/badge.svg)](https://github.com/GreenhillEfka/pilotsuite-styx-core/actions)

**Styx** — ein privacy-first, lokaler KI-Assistent fuer Home Assistant. Lernt die Muster deines Zuhauses, bewertet Stimmung und Kontext, schlaegt intelligente Automatisierungen vor — und handelt nur mit deiner Zustimmung.

Dieses Repo ist das **PilotSuite Backend (Core Add-on)** — es laeuft als Home Assistant Add-on auf Port **8909** mit Flask + Waitress und bundled Ollama (LLM).

Die dazugehoerige **HACS-Integration** (Sensoren, Dashboard Cards, Module):
[PilotSuite HACS Integration](https://github.com/GreenhillEfka/pilotsuite-styx-ha)

```
Home Assistant
+-- HACS Integration (ai_home_copilot)      <-- 94+ Sensoren, 28 Module, Dashboard
|     HTTP REST API (Token-Auth)
|     v
+-- Core Add-on (copilot_core) Port 8909    <-- Brain Graph, Habitus, Mood, LLM
      + Ollama (bundled, qwen3:0.6b default)
```

## Installation

### Core Add-on

1. Home Assistant → **Settings** → **Add-ons** → **Add-on Store**
2. Menue (⋮) → **Repositories** → URL hinzufuegen:
   ```
   https://github.com/GreenhillEfka/pilotsuite-styx-core
   ```
3. **PilotSuite Core** installieren und starten
4. Das Add-on laeuft auf Port **8909** mit bundled Ollama
5. Im Add-on-Info-Screen findest du die exakte Schritt-fuer-Schritt-Anleitung (`DOCS.md`)

### HACS Integration

Siehe: [pilotsuite-styx-ha Installation](https://github.com/GreenhillEfka/pilotsuite-styx-ha#schnellstart)

## Features

### Chat Pipeline (HA-Assist Integration)

**Natürliche Sprachsteuerung für dein Smart Home** — PilotSuite integriert sich nahtlos in Home Assistant Assist und bringt kontextbewusste Konversation mit automatischem LLM-Fallback.

```yaml
# configuration.yaml (MINIMAL — nur 3 Zeilen!)
conversation:
  - platform: pilotSuite_rag_conversation
    ha_token: !secret openclaw_ha_token
    # RAG-API wird automatisch auf localhost:8765 entdeckt
    # LLM-Fallback: OpenAI (optional) → Ollama → Ollama Tiny
```

#### LLM-Provider (mit automatischer Fallback-Chain)

| Provider | Modell | Beschreibung | Fallback-Level |
|----------|--------|--------------|----------------|
| **OpenAI** | `gpt-4` | Beste Qualität, Cloud | Primary |
| **Ollama** | `qwen3.5:397b-cloud` | Lokal, privacy-first | Fallback 1 |
| **Ollama Tiny** | `qwen2.5:1.5b` | Klein, robust, immer da! | Fallback 2 |
| **OpenClaw** | `Clawdya` | Optional, wenn installiert | Optional |

**So funktioniert die Fallback-Chain:**
1. **OpenAI** wird zuerst versucht (wenn API-Key konfiguriert)
2. Bei Timeout/Error → **Ollama** (lokal auf Port 11434)
3. Bei Timeout/Error → **Ollama Tiny** (immer verfügbar!)
4. Optional → **OpenClaw** (wenn installiert)

```yaml
# configuration.yaml (VOLLSTÄNDIG)
conversation:
  - platform: pilotSuite_rag_conversation
    
    # HA Token (ERFORDERLICH)
    ha_token: !secret openclaw_ha_token
    
    # RAG-API (optional, Default: localhost:8765)
    rag_api_url: http://localhost:8765
    
    # Primary LLM-Provider (optional, Default: OpenAI)
    provider: openai
    openai_api_key: !secret openai_api_key
    model: gpt-4
    
    # Fallback-Kette (optional, Default: [openai, ollama, ollama_tiny])
    fallback_enabled: true
    fallback_order:
      - openai
      - ollama
      - ollama_tiny
    
    # Ollama-Config (Fallback 1)
    ollama_url: http://localhost:11434
    ollama_model: qwen3.5:397b-cloud
    
    # Ollama Tiny (Fallback 2)
    ollama_tiny_model: qwen2.5:1.5b
    
    # Privacy (optional, Default: false)
    use_web_search: false
```

#### Zero-Config Setup-Guide

**Schritt 1: Long-Life HA Token erstellen (einmalig)**
1. Home Assistant → Klick auf dein **Profil** (unten links)
2. Tab **Long-Lived Access Token**
3. **Create Token** → Name: "PilotSuite"
4. Token kopieren

**Schritt 2: Token in secrets.yaml speichern**
```yaml
# secrets.yaml
openclaw_ha_token: YOUR_LONG_LIFE_TOKEN_HERE
```

**Schritt 3: Minimal-Konfiguration in configuration.yaml**
```yaml
# configuration.yaml
conversation:
  - platform: pilotSuite_rag_conversation
    ha_token: !secret openclaw_ha_token
```

**Schritt 4: Home Assistant neustarten**
```bash
# HA → Settings → System → Restart
```

**Fertig!** 🎉 PilotSuite ist jetzt betriebsbereit mit:
- ✅ Auto-Discovery der RAG-API (localhost:8765)
- ✅ Ollama-Fallback (lokal, privacy)
- ✅ Ollama Tiny als letztes Fallback (immer online!)

**Optional: OpenAI für bessere Qualität**
```yaml
# secrets.yaml
openai_api_key: sk-your-openai-api-key

# configuration.yaml
conversation:
  - platform: pilotSuite_rag_conversation
    ha_token: !secret openclaw_ha_token
    provider: openai
    openai_api_key: !secret openai_api_key
    model: gpt-4
    fallback_enabled: true
```

### LLM (Ollama bundled)

- Standard-Modell: `qwen3:0.6b` (schnell, low-RAM, Tool-Calling)
- Optionales Qualitaets-Modell: `qwen3:4b` (staerkere Hardware)
- OpenAI-kompatible API (`/v1/chat/completions`, `/v1/models`)
- Telegram Bot Integration mit Server-side Tool Loop

#### Optional Cloud Fallback (Self-Repair / High-Performance)

Im Add-on unter **Configuration**:
- `conversation_cloud_api_url` (z. B. `https://ollama.com/v1` oder `https://api.openai.com/v1`)
- `conversation_cloud_api_key`
- `conversation_cloud_model` (z. B. `gpt-oss:20b` fuer Ollama Cloud, `gpt-4o-mini` fuer OpenAI-kompatible APIs)
- `conversation_prefer_local` (`true` = Ollama zuerst, dann Cloud-Fallback)

Hinweis:
- Wenn ein Client ein nicht lokal installiertes Modell anfragt (z. B. `gpt-4o-mini`), versucht Styx zuerst den konfigurierten lokalen Ollama-Standard und faellt danach optional auf Cloud zurueck.
- Der externe API-Key wird ausschliesslich im Add-on Feld `conversation_cloud_api_key` gesetzt (nicht in der HACS-Integration).

### Optional: Onyx als Chat- und RAG-Frontend

Onyx laesst sich als zusaetzliche Chat-/RAG-Oberflaeche andocken.
Empfohlenes Setup: Onyx fuer Connector-RAG, Styx fuer Home-Actions (OpenAPI/MCP).
Details: `docs/ONYX_INTEGRATION.md`

Produktive Action-Definition:
- `docs/integrations/onyx_styx_actions.openapi.yaml`

Schneller E2E-Check (Onyx -> Styx -> HA -> Rueckkanal):
- `TOKEN=<styx_token> ./tools/onyx_styx_e2e.sh`

### Neural Pipeline

```
HA Events → Event Ingest → Brain Graph → Habitus Miner → Candidates
                              |               |
                          Neurons          Patterns
                              |               |
                          Mood Engine    Vorschlaege → HA Repairs UI
```

### 22 Backend-Services

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
| SearchIndex | Entity-Suche |
| NotificationService | Push-System |
| WeatherService | Wetter-Integration |
| EnergyService | Energie-Neuron |
| UserPreferenceStore | Per-User Praeferenzen |
| HouseholdService | Familienkonfiguration |
| CalendarService | Kalender-Integration |
| CharacterService | Styx-Persoenlichkeit |
| SystemHealthService | Health Checks (Zigbee, Z-Wave, Recorder) |
| MediaZoneManager | Media-Zonen Verwaltung |
| DevSurface | Debug/Diagnose Endpunkte |
| MCPServer | 8 Skills fuer externe AI-Clients |
| CollectiveIntelligence | Cross-Home Sharing (Phase 5) |

### OpenAI-kompatible API

Kompatibel mit `extended_openai_conversation` (jekalmin) und dem OpenAI SDK.

```
base_url: http://<host>:8909/v1
Authorization: Bearer <token>
```

### Sicherheit

- Token-Auth (Bearer / X-Auth-Token)
- Circuit Breaker (HA Supervisor: 5 Fails/30s, Ollama: 3 Fails/60s)
- Rate Limiting
- SQLite WAL Mode + busy_timeout=5000
- PII-Redaktion, bounded Storage

## API-Uebersicht (Port 8909)

| Bereich | Endpoints | Beschreibung |
|---------|-----------|-------------|
| **System** | `/health`, `/version`, `/api/v1/status` | Health, Version, Capabilities |
| **Chat** | `/v1/chat/completions`, `/v1/models` | OpenAI-kompatibel |
| **Brain Graph** | `/api/v1/graph/*` | State, Snapshot, Stats, Patterns |
| **Habitus** | `/api/v1/habitus/*` | Status, Rules, Mine, Dashboard |
| **Candidates** | `/api/v1/candidates/*` | CRUD, Stats, Cleanup |
| **Mood** | `/api/v1/mood/*` | Mood Query, Update, History |
| **Neurons** | `/api/v1/neurons/*` | Neuron State, Evaluation |
| **Events** | `/api/v1/events` | Event Ingest + Query |
| **Tags** | `/api/v1/tag-system/*` | Tags, Assignments |
| **Search** | `/api/v1/search/*` | Entity Search, Index |
| **Knowledge Graph** | `/api/v1/kg/*` | Nodes, Edges, Query |
| **Vector Store** | `/api/v1/vector/*` | Store, Search, Stats |
| **RAG Hybrid Search** | `/api/v1/rag/*` | BM25 + Vector Search mit RRF (neu) |
| **Weather** | `/api/v1/weather/*` | Wetterdaten |
| **Energy** | `/api/v1/energy/*` | Energiemonitoring |
| **Notifications** | `/api/v1/notifications/*` | Push System + HA Notify Adapter (neu) |
| **Media Zones** | `/api/v1/media-zones/*` | Media-Zonen Verwaltung |
| **Telegram** | `/telegram/webhook` | Telegram Bot |
| **MCP** | `/mcp/*` | Model Context Protocol |

## Grundprinzipien

| Prinzip | Bedeutung |
|---------|-----------|
| **Local-first** | Alles lokal, kein Cloud-API-Call |
| **Privacy-first** | PII-Redaktion, bounded Storage, opt-in |
| **Governance-first** | Vorschlaege vor Aktionen, Human-in-the-Loop |
| **Safe Defaults** | Max 500 Nodes, 1500 Edges, opt-in Persistenz |

## Dokumentation

### Core Documentation

| Dokument | Inhalt |
|----------|--------|
| [API_REFERENCE](docs/API_REFERENCE.md) | Alle Endpoints, Auth, Request/Response |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Services, Datenfluss, Persistenz |
| [ONYX_INTEGRATION](docs/ONYX_INTEGRATION.md) | Onyx + Styx Zielarchitektur, Security, Setup |
| [onyx_styx_actions.openapi](docs/integrations/onyx_styx_actions.openapi.yaml) | OpenAPI Actions fuer Onyx |
| [ROADMAP](docs/ROADMAP.md) | Phase 5-6, Zukunftsplaene |
| [CHANGELOG](CHANGELOG.md) | Release-Historie |
| [HACS Integration](https://github.com/GreenhillEfka/pilotsuite-styx-ha) | Sensoren, Module, Dashboard |

### Phase 6 API Documentation

| API | Endpoints | Beschreibung |
|-----|-----------|--------------|
| [RAG Hybrid Search](docs/RAG_HYBRID_SEARCH.md) | 6 | BM25 + Vector Search mit RRF Fusion |
| [Push Notifications](docs/PUSH_NOTIFICATIONS.md) | 8 | Multi-Channel Notifications, Templates, Scheduling |
| [Collective Intelligence](docs/COLLECTIVE_INTELLIGENCE.md) | 15 | Federated Learning, Knowledge Sharing |
| [Zone Editor](docs/ZONE_EDITOR.md) | 5 | Bidirektionaler Zonen-Sync HA ↔ Core |

**Total Phase 6 Endpoints:** 34 neue API-Endpoints

## Lizenz

Dieses Projekt ist privat. Alle Rechte vorbehalten.
