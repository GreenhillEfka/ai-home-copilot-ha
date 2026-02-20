# PilotSuite — Konsolidierte Gesamtuebersicht aller Repos & Branches

> **Erstellt:** 2026-02-18 | Analyse beider Repos mit allen Branches, Tags, Commits und Code
> **Repos:** pilotsuite-styx-core (Core Add-on) + pilotsuite-styx-ha (HACS Integration)
> **Zweck:** Alles was je gemacht wurde in ein Gesamtkonzept zusammengefuehrt

---

## 1. Projektuebersicht

**PilotSuite** (ehemals PilotSuite) ist ein zweiteiliges System fuer Home Assistant:

| Komponente | Repo | Rolle | Aktuelle Version | Technologie |
|-----------|------|-------|-----------------|-------------|
| **Core Add-on** | `pilotsuite-styx-core` | Backend: KI-Engine, Brain Graph, APIs | v0.9.8-alpha.1 | Flask/Waitress, Python 3.11+, Docker |
| **HACS Integration** | `pilotsuite-styx-ha` | Frontend: Sensoren, Dashboard, HA-Anbindung | v0.15.2 | HA asyncio, Python 3.11+ |

**Vision:** Ein privacy-first, lokaler KI-Assistent der Verhaltensmuster im Smart Home lernt und intelligente Automatisierungen vorschlaegt — ohne Cloud, ohne eigenmaechtige Aktionen, immer mit Zustimmung des Nutzers.

---

## 2. Philosophie & Grundprinzipien

### Die 5 Grundprinzipien

| Prinzip | Bedeutung | Konsequenz |
|---------|-----------|------------|
| **Local-first** | Alles laeuft lokal, keine Cloud | Kein externer API-Call, kein Log-Shipping |
| **Privacy-first** | PII-Redaktion, bounded Storage | Max 2KB Metadata/Node, Context-ID auf 12 Zeichen gekuerzt |
| **Governance-first** | Vorschlaege vor Aktionen | Human-in-the-Loop, kein stilles Automatisieren |
| **Safe Defaults** | Begrenzte Speicher, opt-in Persistenz | Max 500 Nodes, 1500 Edges, optional JSONL |
| **Offline Voice** | Lokale Sprachsteuerung | Ollama-Integration, kein Cloud-TTS/STT |

### Die Normative Kette (unverletzbar)

```
States → Neuronen → Moods → Synapsen → Vorschlaege → Dialog/Freigabe → HA-Aktion
```

**Regeln:**
- Kein direkter Sprung State → Mood (Neuronen sind zwingende Zwischenschicht)
- Mood kennt keine Sensoren/Geraete — nur Bedeutung
- Vorschlaege werden NIE ohne explizite Freigabe ausgefuehrt
- Unsicherheit/Konflikt reduziert Handlungsspielraum

### Rollenmodell

| Rolle | Verhalten | Standard |
|-------|-----------|----------|
| **CoPilot/Berater** | Schlaegt vor + begruendet | **Default** |
| **Agent** | Handelt autonom, NUR nach Freigabe | Opt-in pro Scope |
| **Autopilot** | Uebernimmt komplett, NUR wenn aktiviert | Explizit |
| **Nutzer** | Entscheidet final | Immer |

### Risikoklassen

| Klasse | Beispiele | Policy |
|--------|-----------|--------|
| **Sicherheit** | Tueren, Alarm, Heizung | Immer Manual Mode |
| **Privatsphaere** | Kameras, Mikrofone | Lokale Auswertung bevorzugen |
| **Komfort** | Licht, Musik, Klima | Assisted nach Opt-in |
| **Info** | Status, Wetter, Kalender | Sofort (read-only) |

---

## 3. Systemarchitektur

### Dual-Repo-Struktur

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Home Assistant                                │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │        HACS Integration (ai_home_copilot) — Port: —            │  │
│  │        Repo: pilotsuite-styx-ha                                 │  │
│  │                                                                  │  │
│  │  22+ Core-Module      80+ Sensoren      15+ Dashboard Cards    │  │
│  │  ┌──────────────┐   ┌─────────────┐   ┌────────────────────┐  │  │
│  │  │ Forwarder    │   │ Mood        │   │ Brain Graph Panel  │  │  │
│  │  │ Habitus      │   │ Presence    │   │ Mood Card          │  │  │
│  │  │ Candidates   │   │ Activity    │   │ Neurons Card       │  │  │
│  │  │ Brain Sync   │   │ Energy      │   │ Habitus Cards      │  │  │
│  │  │ Mood Context │   │ Neurons 14  │   │ Suggestion Panel   │  │  │
│  │  │ Media        │   │ Anomaly     │   │ Calendar Card      │  │  │
│  │  │ Energy       │   │ Predictive  │   │ Preference Card    │  │  │
│  │  │ Weather      │   │ Calendar    │   │                    │  │  │
│  │  │ UniFi        │   │ Cognitive   │   │                    │  │  │
│  │  │ ML Context   │   │ Media       │   │                    │  │  │
│  │  │ MUPL         │   │ Habit V2    │   │                    │  │  │
│  │  │ Character    │   │ Voice       │   │                    │  │  │
│  │  │ Home Alerts  │   │ Environment │   │                    │  │  │
│  │  │ Voice        │   │ Time        │   │                    │  │  │
│  │  │ KG Sync      │   │ Inspector   │   │                    │  │  │
│  │  │ Camera       │   │             │   │                    │  │  │
│  │  │ Household    │   │             │   │                    │  │  │
│  │  │ Perf Guards  │   │             │   │                    │  │  │
│  │  └──────────────┘   └─────────────┘   └────────────────────┘  │  │
│  └─────────────────────────────┬──────────────────────────────────┘  │
│                                 │ HTTP REST API (Token-Auth)          │
│                                 ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │        Core Add-on (copilot_core) — Port 8099                  │  │
│  │        Repo: pilotsuite-styx-core                             │  │
│  │                                                                  │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ │  │
│  │  │ Brain      │ │ Habitus    │ │ Mood       │ │ Candidates  │ │  │
│  │  │ Graph      │ │ Miner      │ │ Engine     │ │ Generator   │ │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ │  │
│  │  │ Tag        │ │ Vector     │ │ Knowledge  │ │ Collective  │ │  │
│  │  │ System     │ │ Store      │ │ Graph      │ │ Intel.      │ │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ │  │
│  │  │ Neurons    │ │ Search     │ │ Sharing    │ │ Performance │ │  │
│  │  │ (12)       │ │ API        │ │ (Cross-H.) │ │ Monitor     │ │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ │  │
│  │  │ Energy     │ │ Weather    │ │ UniFi      │ │ System      │ │  │
│  │  │ Neuron     │ │ API        │ │ Neuron     │ │ Health      │ │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ │  │
│  │  │ Ollama     │ │ MCP Tools  │ │ Dev        │ │ Swagger UI  │ │  │
│  │  │ Convers.   │ │ (HA)       │ │ Surface    │ │ (API Docs)  │ │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ │  │
│  │                                                                  │  │
│  │  37+ API-Blueprints | 24+ Module-Packages | SQLite + JSONL     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Datenfluss (End-to-End)

```
1. HA Event Bus (state_changed, automation_triggered, etc.)
      │
      ▼
2. EventsForwarder (HACS Module)
   - Batching (max 50 events / 30s)
   - Rate Limiting
   - PII-Redaktion (Namen, IDs gekuerzt)
   - Persistent Queue (survives restarts)
      │
      ▼
3. POST /api/v1/events → Core Add-on
      │
      ├──▶ Event Store (JSONL, bounded, max 10.000 Events)
      ├──▶ Brain Graph (Nodes + Edges, exponential decay)
      │     - Max 500 Nodes, 1500 Edges
      │     - SQLite + In-Memory Hybrid
      │     - Batch Processing Mode
      │     - Deterministic Pruning (alle 100 Ops)
      ├──▶ Knowledge Graph (SQLite/Neo4j dual backend)
      └──▶ Habitus Miner (A→B Pattern Mining)
           - Zone-basiertes Mining (Wohn/Schlaf/Kueche)
           - Association Rules (Support, Confidence, Lift)
           - Zeitbasierte, Trigger, Sequenz, Kontext-Muster
               │
               ▼
4. Candidate Generator
   - Confidence Scoring
   - Mood-basierte Suppression
   - Neuron-Bewertung (12 Neuronen)
      │
      ▼
5. GET /api/v1/candidates ← CandidatePollerModule (5min Intervall)
      │
      ▼
6. HA Repairs System + Dashboard Cards
   - Vorschlag mit Begruendung anzeigen
   - Zone + Mood + Risiko Kontext
      │
      ▼
7. User Entscheidung
   - Akzeptieren → Blueprint Import → HA-Automatisierung
   - Modifizieren → Parameter anpassen → erneut vorschlagen
   - Ablehnen → Gewicht reduzieren → aehnliche unterdruecken
```

---

## 4. Alle Module im Detail

### 4.1 Core Add-on Module (Backend)

#### Kern-Engine

| Modul | Package | Beschreibung | Status |
|-------|---------|-------------|--------|
| **Brain Graph** | `brain_graph/` | In-Memory + SQLite Zustandsgraph mit Nodes, Edges, Decay, SVG-Snapshots | ✅ Stabil |
| **Habitus Miner** | `habitus_miner/` + `habitus/` | Pattern-Discovery mit Association Rules, Zone-Mining | ✅ Stabil |
| **Mood Engine** | `mood/` | 3D-Bewertung (Comfort/Joy/Frugality), Orchestrator, Zone-Snapshots | ✅ Stabil |
| **Candidates** | `candidates/` | Vorschlags-Lifecycle (pending→offered→accepted/dismissed) | ✅ Stabil |
| **Event Ingest** | `ingest/` | Event Processing Pipeline, Deduplication, Idempotency | ✅ Stabil |
| **Neurons (12)** | `neurons/` | Presence, Mood, Energy, Weather, UniFi, Camera, Context, State | ✅ Stabil |

#### Erweiterungen

| Modul | Package | Beschreibung | Status |
|-------|---------|-------------|--------|
| **Knowledge Graph** | `knowledge_graph/` | SQLite/Neo4j dual backend, Entity-Beziehungen | ✅ Implementiert |
| **Vector Store** | `vector_store/` | Lokale Embeddings, optional Ollama | ✅ Implementiert |
| **Tag System** | `tags/` | `aicp.<kategorie>.<name>` Tagging mit Decision Matrix | ✅ v0.2 |
| **Collective Intelligence** | `collective_intelligence/` | Federated Learning, Privacy Preserving | ✅ Phase 5 |
| **Cross-Home Sharing** | `sharing/` | Sync zwischen Haushalten, mDNS Discovery | ✅ Phase 5 |
| **Synapses** | `synapses/` | Neurale Verbindungen zwischen Neuronen | ✅ Implementiert |
| **Search** | `api/v1/search.py` | Entity-Suche mit Index | ✅ Implementiert |
| **System Health** | `system_health/` | Zigbee, Z-Wave, Recorder Monitoring | ✅ Implementiert |
| **Energy Neuron** | `energy/` | PV-Forecast, Anomaly Detection, Load Shifting | ✅ v0.4.11 |
| **UniFi Neuron** | `unifi/` | WAN-Qualitaet, Latenz, Client-Tracking | ✅ v0.4.10 |
| **Weather API** | `api/v1/weather.py` | Wetterdaten-Integration | ✅ Implementiert |
| **Notifications** | `api/v1/notifications.py` | Push-System (HA notify Fallback) | ⚠️ Stub |
| **Dev Surface** | `dev_surface/` | Debug/Diagnose/Performance-Metriken | ✅ Implementiert |
| **Log Fixer TX** | `log_fixer_tx/` | Transaction Log fuer reversible Operationen | ✅ Implementiert |
| **Ollama Conversation** | `api/v1/conversation.py` | OpenAI-kompatibler Chat-Endpoint | ✅ v0.9.2 |
| **MCP Tools** | `mcp_tools.py` | HA Service Calls, Entity State, History, Scenes | ✅ v0.9.6 |
| **Swagger UI** | `api/v1/swagger_ui.py` | API-Dokumentation | ✅ v0.4.34 |
| **MUPL** | `api/v1/user_preferences.py` | Multi-User Preference Learning API | ✅ Implementiert |
| **Household** | `household.py` | Familienkonfiguration, Altersgruppen | ✅ v0.14.0 |

#### API-Endpoints (37+)

| Bereich | Endpoints | Methoden |
|---------|-----------|----------|
| **Basis** | `/health`, `/version`, `/api/v1/status`, `/api/v1/capabilities` | GET |
| **Events** | `/api/v1/events` | GET, POST |
| **Brain Graph** | `/api/v1/graph/state`, `/snapshot`, `/stats`, `/prune`, `/patterns`, `/ops` | GET, POST |
| **Habitus** | `/api/v1/habitus/status`, `/rules`, `/mine`, `/dashboard-cards` | GET, POST |
| **Candidates** | `/api/v1/candidates`, `/stats`, `/cleanup` | GET, POST, PUT, DELETE |
| **Mood** | `/api/v1/mood`, `/zones/{name}/orchestrate`, `/force`, `/status` | GET, POST |
| **Tags** | `/api/v1/tag-system/tags`, `/assignments` | GET, POST, DELETE |
| **Neurons** | `/api/v1/neurons/state` | GET |
| **Search** | `/api/v1/search`, `/index` | GET, POST |
| **Knowledge Graph** | `/api/v1/kg/nodes`, `/edges`, `/query` | GET, POST |
| **Vector Store** | `/api/v1/vector/store`, `/search`, `/stats` | GET, POST |
| **Weather** | `/api/v1/weather` | GET |
| **Energy** | `/api/v1/energy` | GET |
| **UniFi** | `/api/v1/unifi/wan`, `/clients`, `/roaming` | GET |
| **System Health** | `/api/v1/system_health` | GET |
| **Performance** | `/api/v1/performance/cache`, `/pool`, `/metrics` | GET |
| **Dashboard** | `/api/v1/dashboard/brain-summary` | GET |
| **Notifications** | `/api/v1/notifications` | GET, POST |
| **User Preferences** | `/api/v1/user/preferences`, `/mood` | GET, POST |
| **Collective Intel.** | `/api/v1/collective` | GET, POST |
| **Conversation** | `/api/v1/chat/completions` | POST |
| **Dev** | `/api/v1/dev/logs`, `/status`, `/support-bundle` | GET |

### 4.2 HACS Integration Module (Frontend)

#### Core-Module (22+)

| Modul | Datei | Funktion |
|-------|-------|----------|
| **EventsForwarder** | `events_forwarder.py` | HA Events an Core senden (batched, PII-redacted) |
| **HabitusMiner** | `habitus_miner.py` | Pattern-Discovery und Zone-Management |
| **CandidatePoller** | `candidate_poller.py` | Vorschlaege vom Core abholen (5min) |
| **BrainGraphSync** | `brain_graph_sync.py` | Brain Graph Synchronisation + D3.js Visualisierung |
| **MoodContextModule** | `mood_context_module.py` | Mood-Integration und Kontext |
| **MoodModule** | `mood_module.py` | Mood v0.2 mit Zone-Snapshots |
| **MediaContextModule** | `media_context_module.py` | Media-Player Tracking |
| **EnergyContextModule** | `energy_context_module.py` | Energiemonitoring |
| **WeatherContextModule** | `weather_context_module.py` | Wetter-Integration |
| **UniFiModule** | `unifi_module.py` | Netzwerk-Ueberwachung |
| **UniFiContextModule** | `unifi_context_module.py` | UniFi-Kontext |
| **MLContextModule** | `ml_context_module.py` | ML-Kontext und Features |
| **UserPreferenceModule** | `user_preference_module.py` | MUPL Integration |
| **CharacterModule** | `character_module.py` | CoPilot-Persoenlichkeit |
| **HomeAlertsModule** | `home_alerts_module.py` | Kritische Zustandsueberwachung |
| **VoiceContext** | `voice_context.py` | Sprachsteuerungs-Kontext |
| **KnowledgeGraphSync** | `knowledge_graph_sync.py` | Knowledge Graph Synchronisation |
| **CameraContextModule** | `camera_context_module.py` | Kamera-Integration |
| **DevSurface** | `dev_surface.py` | Debug/Diagnose Modul |
| **PerformanceGuardrails** | `performance_guardrails.py` | Performance-Ueberwachung |
| **PerformanceScaling** | `performance_scaling.py` | Auto-Scaling |
| **QuickSearch** | `quick_search.py` | Entity-Schnellsuche |
| **OpsRunbook** | `ops_runbook.py` | Operations-Handbuch |

#### Sensoren (80+)

| Sensor-Modul | Funktion | Entities |
|-------------|----------|----------|
| `mood_sensor` | Mood-Entity (Comfort/Joy/Frugality) | 3+ |
| `presence_sensors` | Anwesenheitserkennung | 5+ |
| `activity_sensors` | Aktivitaetserkennung | 5+ |
| `energy_sensors` | Energieueberwachung | 5+ |
| `energy_insights` | Energie-Analysen | 3+ |
| `neurons_14` | 14 Basis-Neuronen (Time, Calendar, Cognitive etc.) | 14+ |
| `neuron_dashboard` | Dashboard-Integration | 5+ |
| `anomaly_alert` | Anomalie-Erkennung | 3+ |
| `predictive_automation` | Praediktive Vorschlaege | 3+ |
| `environment_sensors` | Temperatur, Feuchtigkeit | 5+ |
| `calendar_sensors` | Kalender-Integration | 3+ |
| `cognitive_sensors` | Kognitive Last | 3+ |
| `media_sensors` | Media-Player Tracking | 5+ |
| `habit_learning_v2` | Habit-Learning | 5+ |
| `time_sensors` | Zeitbasierte Trigger | 3+ |
| `voice_context` | Sprachsteuerung | 3+ |
| `inspector` | Entity-Inspektion | variabel |

#### Dashboard Cards (15+)

| Card | Funktion |
|------|----------|
| Brain Graph Panel | Interaktive D3.js Visualisierung des Brain Graph |
| Mood Card | Mood-Status und Verlauf |
| Neurons Card | Neuronen-Uebersicht |
| Habitus Card | Pattern-Discovery Status |
| Habitus Dashboard Cards | Zone-aware Pattern-Karten |
| Suggestion Panel | Vorschlaege mit Kontext |
| Calendar Context Card | Kalender-Integration |
| Preference Input Card | Delegation Workflows |
| Camera Dashboard | Kamera-Uebersicht |
| PilotSuite Dashboard | Gesamt-Dashboard |
| Neuron Dashboard | Detaillierte Neuronen-Anzeige |

---

## 5. Neuronales System

### 12 Neuronen (Core)

| Neuron | Datei | Aspekt | Bewertung |
|--------|-------|--------|-----------|
| `presence.py` | Anwesenheit | Wer ist wo? (person.*, device_tracker.*) |
| `mood.py` | Stimmung | Comfort/Joy/Frugality je Zone |
| `energy.py` | Energie | PV-Forecast, Kosten, Grid, Anomalien |
| `weather.py` | Wetter | Bedingungen + Empfehlungen |
| `unifi.py` | Netzwerk | WAN-Qualitaet, Latenz, Roaming |
| `camera.py` | Kameras | Status + Presence Detection |
| `context.py` | Kontext | Tageszeit, Saison, Wochentag |
| `state.py` | Zustaende | Entity-State-Tracking |
| `base.py` | Basis | Abstrakte Neuron-Klasse |
| `manager.py` | Orchestrierung | NeuronManager mit Callbacks |

### 14+ Sensoren-Neuronen (HACS)

Ueber `neurons_14.py` werden 14+ Basis-Neuronen als HA-Sensoren exponiert:
- Time Neuron, Calendar Neuron, Cognitive Neuron
- Presence Neuron, Activity Neuron
- Energy Neuron, Weather Neuron
- Media Neuron, Environment Neuron
- etc.

---

## 6. Habitus — Das Lernende Zuhause

### Kernprinzipien

1. **Beobachten, nicht annehmen** — Lernt aus tatsaechlichem Verhalten
2. **Vorschlagen, nicht handeln** — Proposes, never executes
3. **Kontinuierlich lernen** — Passt sich Lifestyle-Aenderungen an
4. **Privacy respektieren** — Alles lokal, opt-in, loeschbar

### Mustertypen

| Mustertyp | Beispiel | Mining-Methode |
|-----------|----------|----------------|
| **Zeitbasiert** | Licht an um 7:00 Werktags | Time Window Analysis |
| **Trigger-basiert** | Bewegung → Licht an | Association Rules (A→B) |
| **Sequenz** | Tuer auf → Flur-Licht → Thermostat | Sequential Pattern Mining |
| **Kontextuell** | Filmabend → Licht dimmen | Context-aware Rules |

### Confidence-System

```
Confidence = (Support × Consistency × Recency) / Complexity
```

| Confidence | Bedeutung | Aktion |
|------------|-----------|--------|
| 0.9+ | Sehr starkes Muster | Hohe Empfehlung |
| 0.7-0.9 | Starkes Muster | Guter Vorschlag |
| 0.5-0.7 | Moderates Muster | Test empfohlen |
| <0.5 | Schwaches Muster | Nur informativ |

### Zone-basiertes Mining

```
Floor (EG, OG, UG)
  └── Area (Wohnbereich, Schlafbereich)
        └── Room (Wohnzimmer, Kueche, Bad)
```

Jede Zone hat eigene Mining-Regeln und Mood-Snapshots.

---

## 7. Mood Engine

### 3D-Bewertung

| Dimension | Bereich | Beschreibung |
|-----------|---------|-------------|
| **Comfort** | 0.0 – 1.0 | Wie gemuetlich ist das Zuhause? |
| **Joy** | 0.0 – 1.0 | Wie freudig/unterhaltsam? |
| **Frugality** | 0.0 – 1.0 | Wie sparsam/effizient? |

### Features

- Zone-spezifische Mood-Snapshots
- Exponential Smoothing fuer stabile Werte
- Suggestion-Suppression basierend auf Stimmung
- Orchestrator fuer zonenuebergreifende Mood-Bewertung
- Force-Mode fuer manuelles Mood-Setting

---

## 8. Multi-User Preference Learning (MUPL)

| Phase | Funktion | Status |
|-------|----------|--------|
| **User Detection** | Wer ist zu Hause? (person.*, device_tracker.*) | ✅ |
| **Action Attribution** | Wer hat was gemacht? (context.user_id) | ✅ |
| **Preference Learning** | Was mag wer? (Exponential Smoothing) | ✅ |
| **Multi-User Aggregation** | Konsens/Priority/Konflikt bei mehreren Usern | ✅ |
| **Vector Client Integration** | Reale Preferenzdaten fuer Recommendations | ✅ v0.15.1 |

**Privacy:** Opt-in, 90 Tage Retention, lokal in HA Storage, User kann eigene Daten loeschen.

### Geplante Rollen (P1.3)

| Rolle | Rechte | Status |
|-------|--------|--------|
| Device Manager | Volle Kontrolle | ⏳ Geplant |
| Everyday User | Standard-Nutzung | ⏳ Geplant |
| Restricted User | Eingeschraenkt (Kinder) | ⏳ Geplant |

---

## 9. Tag & Zone System

### Tag-Konvention

```
aicp.<kategorie>.<name>
```

| Kategorie | Beispiele |
|-----------|-----------|
| `kind` | `aicp.kind.light`, `aicp.kind.sensor` |
| `role` | `aicp.role.safety_critical`, `aicp.role.morning` |
| `state` | `aicp.state.needs_repair`, `aicp.state.low_battery` |
| `place` | `aicp.place.wohnzimmer` (auto bei Zone) |

### Integration

```
Zone erstellen → Tag aicp.place.{zone} automatisch erstellen
Entity mit Tag → automatisch in Zone eingeordnet
Brain Graph verlinkt: Tag ↔ Zone ↔ Entity (bidirektional)
Decision Matrix: Tag-basierte Entscheidungen mit Gewichtung
```

---

## 10. Sicherheit

| Feature | Status | Details |
|---------|--------|---------|
| Token-Auth (X-Auth-Token / Bearer) | ✅ | `validate_token(flask_request)` |
| PII-Redaktion | ✅ | Context-IDs gekuerzt, Namen reduziert |
| Bounded Storage (alle Stores) | ✅ | Max 500 Nodes, 1500 Edges, 10K Events |
| Source Allowlisting (Events) | ✅ | Nur erlaubte Event-Typen |
| Rate Limiting (Event Ingest) | ✅ | Pro-Endpoint konfigurierbar |
| Idempotency-Key Deduplication | ✅ | TTL+LRU Dedupe |
| `exec()` → `ast.parse()` | ✅ | Security Fix |
| SHA256 Hashing | ✅ | Fuer IDs und Tokens |
| Path Validation (Log Fixer) | ✅ | ALLOWED_RENAME_PATHS Whitelist |
| Error Sanitization | ✅ | Keine internen Details in Responses |
| Entity ID Sanitization | ✅ | brain_graph_sync |
| GZIP Compression | ✅ | Performance + Security |
| SQLite WAL Mode | ✅ | v0.9.1-alpha.5 |

---

## 11. Offline Conversation AI (PilotSuite Voice)

### Architektur

```
User Voice → HA Assist → Extended OpenAI Conversation → PilotSuite Core → Ollama
```

### Features

- **OpenAI-kompatibler Endpoint:** `/api/v1/chat/completions`
- **Ollama Integration:** `llm2.5-thinking:latest` oder eigene Modelle
- **Extended OpenAI Conversation:** HA HACS Custom Component (im Repo enthalten)
- **100% lokal:** Keine externen Calls
- **Character Presets:** CoPilot-Persoenlichkeit konfigurierbar

---

## 12. ML Pattern Recognition (Phase 4)

Implementiert im Branch `wip/phase4-ml-patterns` und `dev/autopilot-2026-02-15`:

| Komponente | Funktion | Status |
|-----------|----------|--------|
| **AnomalyDetector** | Isolation Forest fuer Anomalie-Erkennung | ✅ Implementiert |
| **HabitPredictor** | Zeitreihen-Analyse fuer Gewohnheiten | ✅ Implementiert |
| **EnergyOptimizer** | Load Shifting und PV-Optimierung | ✅ Implementiert |
| **MultiUserLearner** | Praeferenz-Lernen pro User | ✅ Implementiert |

Abhaengigkeiten: numpy, scikit-learn (in manifest.json)

---

## 13. Collective Intelligence & Cross-Home (Phase 5)

### Collective Intelligence (Federated Learning)

Implementiert im Branch `wip/phase5-collective-intelligence`:

| Komponente | Funktion |
|-----------|----------|
| `federated_learner.py` | Verteiltes Lernen ohne Datenaustausch |
| `knowledge_transfer.py` | Wissenstransfer zwischen Instanzen |
| `model_aggregator.py` | Modell-Aggregation |
| `privacy_preserver.py` | Differential Privacy |

### Cross-Home Sharing

Implementiert im Branch `wip/phase5-cross-home`:

| Komponente | Funktion |
|-----------|----------|
| `discovery.py` | mDNS-basierte Peer-Discovery mit TTL |
| `sync.py` | Synchronisation zwischen Haushalten |
| `conflict.py` | Conflict Resolution bei Sync |
| `registry.py` | Peer-Registry |

---

## 14. SDK & Tools

### Python SDK

```
sdk/python/src/ai_home_copilot_client/
├── __init__.py
├── client.py      # REST API Client
└── models.py      # Datenmodelle
```

### TypeScript SDK

Im Branch `wip/phase5-cross-home` angelegt (Grundgeruest).

### MCP Tools (v0.9.6)

- HA Service Calls
- Entity State Queries
- History Data
- Scene Activation

---

## 15. Komplette Branch-Uebersicht

### pilotsuite-styx-core (Core Add-on)

| Branch | Zweck | Status | Unique Features |
|--------|-------|--------|-----------------|
| **main** | Haupt-Branch (Release) | Aktiv | v0.9.8-alpha.1, TODOs, Error Handling |
| **master** | Aelterer Haupt-Branch | Inaktiv | Design-Docs, Autopilot-Logs, MUPL-Konzept |
| **dev** | Entwicklung | Historisch | Graph Feeding v0.2.5, Dev Surface, Diagnostics |
| **dev-habitus-dashboard-cards** | Dashboard Cards Feature | Gemerged | Brain Graph + Habitus Miner Cards, Zone-aware |
| **release/v0.4.1** | Release-Branch | Historisch | Brain Graph Module bis Tag System v0.2 |
| **wip/phase5-collective-intelligence** | Federated Learning | Feature-Complete | Collective Intelligence mit Privacy |
| **wip/phase5-cross-home** | Cross-Home Sync | Feature-Complete | mDNS Discovery, Peer Sync, SDKs, Neurons, Vector Store |
| **claude/research-repos-scope-4e3L6** | Research | Abgeschlossen | DeepSeek-R1 Integration Scope |
| **backup/pre-merge-20260216** | Backup | Archiv | Backup vor Merge-Refactoring |

### pilotsuite-styx-ha (HACS Integration)

| Branch | Zweck | Status | Unique Features |
|--------|-------|--------|-----------------|
| **development** | Haupt-Branch | Aktiv | v0.15.2, MUPL, Error Handling |
| **dev-habitus-dashboard-cards** | Dashboard Cards | Gemerged | Services Registration |
| **dev/autopilot-2026-02-15** | Autopilot Release | Feature-Complete | Brain Graph Panel, ML Context, CI Pipeline |
| **dev/mupl-phase2-v0.8.1** | MUPL Phase 2 | Gemerged | Action Attribution, Performance Optimization |
| **dev/openapi-spec-v0.8.2** | OpenAPI Spec | Gemerged | LazyHistoryLoader, OpenAPI Spec |
| **dev/tag-registry-v0.1** | Tag Registry | Leer/Gemerged | — |
| **dev/vector-store-v0.8.3** | Vector Store | Gemerged | Vector Store Client, Performance Module |
| **wip/module-forwarder_quality** | Forwarder QA | Gemerged | Token UX v0.6.6 |
| **wip/module-unifi_module** (2x) | UniFi Module | Gemerged | Module Architecture v0.7.0, Base Classes |
| **wip/phase4-ml-patterns** | ML Patterns | Feature-Complete | AnomalyDetector, HabitPredictor, EnergyOptimizer |
| **backup/pre-merge-20260216** | Backup | Archiv | Backup vor Merge |
| **claude/research-repos-scope-4e3L6** | Research | Abgeschlossen | DeepSeek-R1 Scope |

---

## 16. Versions-Historie (Chronologisch)

### Core Add-on Tags

| Version | Datum | Meilenstein |
|---------|-------|-------------|
| v0.1.0 | 2026-02-07 | MVP Scaffold: HA Add-on + copilot_core Service |
| v0.1.1 | 2026-02-07 | Build Fix (build.yaml) |
| copilot_core-v0.1.1 | 2026-02-07 | Dev Log Ingest Endpoint |
| copilot_core-v0.1.2 | 2026-02-07 | /devlogs HTML View |
| copilot_core-v0.2.0 | 2026-02-07 | API v1 Scaffold (events/candidates/mood) |
| copilot_core-v0.2.1–0.2.7 | 2026-02-08 | Port Fix, Graph Skeleton, Graph Feeding, Graph Ops |
| copilot_core-v0.4.0 | 2026-02-10 | Tag System + Event Ingest Pipeline |
| copilot_core-v0.4.1 | 2026-02-10 | Brain Graph Module |
| copilot_core-v0.4.2 | 2026-02-10 | Event Processing Pipeline |
| v0.4.3 | 2026-02-10 | Enhanced Brain Graph Intelligence |
| v0.4.4 | 2026-02-10 | N2 Candidate Storage System |
| v0.4.5 | 2026-02-10 | N2 Habitus A→B Pattern Miner |
| copilot_core-v0.4.6 | 2026-02-11 | API Security Decorator + E2E Tests |
| copilot_core-v0.4.7 | 2026-02-11 | Mood Module v0.1 |
| copilot_core-v0.4.8 | 2026-02-14 | Modular Architecture Refactor (47% Reduktion) |
| copilot_core-v0.4.9 | 2026-02-14 | SystemHealth Neuron |
| copilot_core-v0.4.10 | 2026-02-14 | UniFi Neuron v0.1 |
| copilot_core-v0.4.11 | 2026-02-14 | Energy Neuron |
| v0.4.12 | 2026-02-14 | Brain Graph Configurable Limits |
| v0.4.13 | 2026-02-14 | UniFi + Energy Neurons Release |
| v0.4.14 | 2026-02-14 | Tag System v0.2 |
| v0.4.15 | 2026-02-14 | Habitus Zones v2 |
| v0.4.16 | 2026-02-15 | Security Fixes (Path Validation) |
| v0.4.18 | 2026-02-15 | Knowledge Graph Module |
| v0.4.19 | 2026-02-15 | Vector Store Module |
| v0.4.30 | 2026-02-15 | Zone-based Mining + Tag Integration |
| v0.4.31 | 2026-02-15 | mmWave Presence + Predictive Energy |
| v0.4.33 | 2026-02-15 | Camera Context Neurons |
| v0.4.34 | 2026-02-15 | Swagger UI Documentation |
| v0.6.1 | 2026-02-15 | Collective Intelligence + Cross-Home Sharing |
| v0.6.2 | 2026-02-15 | CHANGELOG, API Fixes |
| v0.6.3 | 2026-02-15 | Import Fixes + GraphStore Alias |
| v0.7.0 | 2026-02-15 | Search + Notifications API |
| v0.8.4 | 2026-02-16 | Config Version Bump |
| v0.9.1-alpha.x | 2026-02-17 | Port Fix, Error Isolation, Mood API, MUPL, WAL Mode, Ollama |
| v0.9.4–0.9.8 | 2026-02-18 | Batch Processing, Pruning, Dev Surface, MCP Tools |

### HACS Integration Tags

| Version | Datum | Meilenstein |
|---------|-------|-------------|
| v0.2.1–0.2.21 | 2026-02-08+ | Fruehe Iterations (Sensors, Config) |
| v0.3.0–0.3.2 | Frueh | Stabilisierung |
| v0.4.0–0.4.9 | Frueh | Core API Integration |
| v0.5.0–0.5.9 | Frueh | Candidate Lifecycle, Modular Runtime |
| v0.6.0–0.6.7 | 2026-02-14 | Log Control, UniFi, Weather, Testing Suite, Error Grouping, Token UX |
| v0.7.0–0.7.6 | 2026-02-14+ | Modular Runtime Architecture |
| v0.8.0–0.8.19 | 2026-02-15 | MUPL, Brain Graph Panel, OpenAPI, Vector Store, ML Patterns, CI |
| v0.9.1–0.9.2 | 2026-02-15 | Interactive Brain Graph, ML Context |
| v0.13.5 | 2026-02-16 | Config Flow Modularization, Legacy Cleanup |
| v0.14.0-alpha.1 | 2026-02-16 | PilotSuite Umbenennung, Household Module |
| v0.14.1–0.14.2 | 2026-02-18 | button_debug Refactoring, Race Condition Fix, Pydantic |
| v0.15.1–0.15.2 | 2026-02-18 | MUPL Vector Integration, Error Handling |

---

## 17. Codebase-Metriken

| Metrik | Core Add-on | HACS Integration |
|--------|-------------|------------------|
| Python-Dateien | ~207 | ~278 |
| Gesamte Python-Zeilen | ~51.000 | ~51.000 |
| Test-Dateien | 53+ | 48+ |
| API-Blueprints | 37+ | — |
| Module-Packages | 24+ | 22+ Core-Module |
| Sensoren | — | 80+ |
| Dashboard Cards | — | 15+ |
| Neuronen (Backend) | 12 | 14+ (via neurons_14.py) |
| Branches (gesamt) | 8 | 13 |
| Tags (gesamt) | 49+ | 80+ |
| Entwicklungszeitraum | 2026-02-07 bis 2026-02-18 | 2026-02-07 bis 2026-02-18 |

---

## 18. Completed Milestones

| Milestone | Core Version | HACS Version | Status |
|-----------|-------------|-------------|--------|
| M0: Foundation (MVP) | v0.1.0 | v0.2.1 | ✅ Done |
| N2: Core API v1 | v0.4.3-0.4.5 | — | ✅ Done |
| M1: Suggestions E2E | v0.5.x | v0.5.x | ✅ Done |
| M2: Mood Ranking | v0.5.7 | v0.5.7 | ✅ Done |
| M3: SystemHealth/UniFi/Energy Neurons | v0.4.9-0.4.13 | v0.6.x | ✅ Done |
| N0: Modular Runtime | v0.5.4 | v0.7.0 | ✅ Done |
| N1: Candidate Lifecycle + UX | v0.5.0-0.5.2 | v0.5.0-0.5.2 | ✅ Done |
| N3: HA → Core Event Forwarder | v0.5.x | v0.5.x | ✅ Done |
| N4: Brain Graph | v0.6.x | v0.6.x | ✅ Done |
| N5: Core ↔ HA Integration Bridge | v0.5.0-0.5.2 | v0.5.0-0.5.2 | ✅ Done |
| Tag System v0.2 | v0.4.14 | — | ✅ Done |
| Habitus Zones v2 | v0.4.15 | — | ✅ Done |
| Character System v0.1 | — | v0.12.x | ✅ Done |
| Interactive Brain Graph Panel | v0.8.x | v0.9.x | ✅ Done |
| Multi-User Preference Learning | — | v0.8.0 | ✅ Done |
| Cross-Home Sync v0.2 | v0.6.0 | — | ✅ Done |
| Collective Intelligence v0.2 | v0.6.1 | — | ✅ Done |
| Security P0 Fixes | v0.4.16 | v0.12.x | ✅ Done |
| Architecture Merge | v0.8.7 | v0.13.4 | ✅ Done |
| Config Flow Modularization | — | v0.13.5 | ✅ Done |
| API Pydantic Validation | — | v0.14.2 | ✅ Done |
| button_debug.py Refactoring | — | v0.14.1 | ✅ Done |
| Ollama Conversation | v0.9.2 | — | ✅ Done |
| MCP Tools Integration | v0.9.6 | — | ✅ Done |
| Batch Processing + Pruning | v0.9.4-0.9.5 | — | ✅ Done |
| ML Pattern Recognition (Phase 4) | — | v0.8.19 | ✅ Done |

---

## 19. Offene TODOs (Konsolidiert)

### Prioritaet 1 — Kritisch

| TODO | Repo | Status |
|------|------|--------|
| Scene Pattern Extraction (bridge.py ~296) | Core | ⚠️ Stub |
| Routine Pattern Extraction (bridge.py ~306) | Core | ⚠️ Stub |
| Push Notifications (notifications.py ~207) | Core | ⚠️ HA notify Fallback |
| Legacy Code Cleanup (forwarder.py, habitus_zones_entities.py etc.) | HACS | ⏳ Teilweise |

### Prioritaet 2 — Features

| TODO | Repo | Status |
|------|------|--------|
| Extended User Roles (P1.3 — Device Manager, Everyday, Restricted) | Core | ⏳ Geplant |
| Enhanced Delegation Workflows (P1.4 — Conflict Resolution UI) | Core+HACS | ⏳ Geplant |
| API Documentation OpenAPI Spec (P1.5) | Core | ⏳ Geplant |
| MCP Phase 2 (Calendar, Weather, Energy Integration) | Core | ⏳ Geplant |
| User Hints Automation (service.py ~206) | HACS | ⚠️ Stub |

### Prioritaet 3 — Technical Debt

| TODO | Repo | Status |
|------|------|--------|
| Large File Refactoring (brain_graph_panel 947 LOC, forwarder_n3 772 LOC) | HACS | ⏳ |
| Test Suite Remediation (24 Fehler, 25 Errors) | HACS | ⏳ |
| Test Coverage >80% | Beide | ⏳ |
| Connection Pooling (SQLite Threading) | Core | ⏳ |

### Prioritaet 4 — Zukunft (Q2 2026)

| TODO | Beschreibung |
|------|-------------|
| LLM-Integration (P2.1) | Ollama + Brain Graph Kombination |
| Echtes ML-Training | TFLite/ONNX On-Device Inference |
| Predictive Suggestions | Beduerfnisse vorhersagen |
| Natural Language | Automatisierungen in Klartext beschreiben |
| v1.0 Release | Feature-Parity, full test coverage |

---

## 20. SWOT-Analyse

| | Positiv | Negativ |
|---|---------|---------|
| **Intern** | **Staerken:** Einzigartige Architektur (Normative Kette), Privacy-first (100% lokal), Governance-first (formalisiert), 80+ Sensoren, 15+ Dashboard Cards, 37+ API Endpoints, Error-Isolation, Batch Processing, Ollama Integration, ML Patterns, Phase 5 (Cross-Home + Collective Intelligence) | **Schwaechen:** Kein echtes Neural-Network ML (nur Association Rules + scikit-learn), Einzelentwickler, 24 Test-Fehler in HACS, Einige Stubs (Notifications, Scene Patterns), Hohe Komplexitaet (500+ Python-Dateien) |
| **Extern** | **Chancen:** Marktluecke (offen+lokal+lernend), LLM-Revolution (Ollama bereits integriert), DSGVO/AI-Act (Privacy-Vorteil), Matter/Thread Kompatibilitaet, HA Core 2026.x nutzt lokale KI | **Risiken:** Google/Amazon Privacy-Features, HA Core native AI-Integration, Komplexitaet vs. Nachhaltigkeit, LLM-Gap zu kommerziellen Loesungen |

---

## 21. Fazit

> **PilotSuite ist das einzige Open-Source-System, das Verhaltensmuster im Smart Home automatisch erkennt, erklaert und vorschlaegt — 100% lokal, mit formalem Governance-Modell und ohne jemals eigenmaechtig zu handeln.**

### Was in 11 Tagen (07.02.–18.02.2026) geschaffen wurde:

- **2 Repos** mit insgesamt **~485 Python-Dateien** und **~102.000 Zeilen Code**
- **37+ REST API Endpoints** im Core Add-on
- **80+ HA-Sensoren** in der HACS Integration
- **15+ Dashboard Cards** fuer Visualisierung
- **22+ Core-Module** in der HACS Integration
- **24+ Module-Packages** im Core Add-on
- **12 Neuronen** + **Mood Engine** + **Brain Graph** + **Habitus Miner**
- **Phase 4 (ML)** und **Phase 5 (Collective Intelligence + Cross-Home)** implementiert
- **Ollama Integration** fuer lokale Sprachsteuerung
- **MCP Tools** fuer HA Service Calls
- **Python SDK** und **TypeScript SDK** (Grundgeruest)
- **129+ Tags** ueber beide Repos
- **21+ Branches** mit unterschiedlichen Feature-Entwicklungen

### Naechste Schritte bis v1.0:

1. **P1.3** Extended User Roles (MUPL)
2. **P1.4** Enhanced Delegation Workflows
3. **P1.5** OpenAPI Spec fuer alle Endpoints
4. **P2.1** LLM-Integration (Brain Graph + Ollama)
5. **Test Suite** auf >80% Coverage bringen
6. **Legacy Code** aufraeumen
7. **v1.0 Stable Release**

---

*Dieses Dokument konsolidiert alle Informationen aus beiden Repos, allen Branches, allen Tags und allen Commits. Es ist die vollstaendige Uebersicht ueber alles was je im Projekt gemacht wurde.*

*Erstellt: 2026-02-18 durch automatisierte Repo-Analyse*
