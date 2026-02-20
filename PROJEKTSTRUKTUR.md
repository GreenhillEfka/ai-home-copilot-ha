# PilotSuite -- Projektstruktur und Moduluebersicht

> Technische Dokumentation der Verzeichnisstruktur, Module, API-Endpoints und Test-Struktur.

---

## Inhaltsverzeichnis

1. [Verzeichnisstruktur](#1-verzeichnisstruktur)
2. [Module und Abhaengigkeiten](#2-module-und-abhaengigkeiten)
3. [API Endpoints Uebersicht](#3-api-endpoints-uebersicht)
4. [Test-Struktur](#4-test-struktur)

---

## 1. Verzeichnisstruktur

### Repository-Root

```
Home-Assistant-Copilot/
+-- addons/
|   +-- copilot_core/              # HA Add-on Definition
|       +-- Dockerfile             # Container-Build (Python + Flask)
|       +-- config.yaml            # Add-on Manifest (Name, Port, Optionen)
|       +-- rootfs/usr/src/app/    # Applikationscode
|           +-- main.py            # Entry Point (Flask + Waitress, Port 8099)
|           +-- copilot_core/      # Hauptpaket
+-- core/
|   +-- sharing/                   # Cross-Home Sync Modul (Tests)
+-- docs/                          # Dokumentation
+-- scripts/                       # Hilfsskripte
+-- CLAUDE.md                      # KI-Kontext
+-- CHANGELOG.md                   # Release-Historie
+-- HANDBUCH.md                    # Installations-/Benutzerhandbuch
+-- PROJEKTSTRUKTUR.md             # Diese Datei
+-- PROJECT_STATUS.md              # Statusbericht und Roadmap
+-- README.md                      # Projekt-README
+-- VISION.md                      # Architektur-Vision (Single Source of Truth)
```

### Core Add-on Paketstruktur

```
copilot_core/
+-- app.py                   # Flask App Factory (create_app)
+-- core_setup.py            # init_services() + register_blueprints()
+-- base.py                  # Basis-Klassen
+-- debug.py                 # Debug-Hilfsfunktionen
+-- performance.py           # Performance-Optimierung (Caching, Pooling)
|
+-- api/
|   +-- security.py          # Token-Validierung (validate_token)
|   +-- rate_limit.py        # Rate Limiting Middleware
|   +-- performance.py       # Performance Middleware (GZIP)
|   +-- v1/
|       +-- blueprint.py     # Blueprint-Registry (alle Sub-Blueprints)
|       +-- candidates.py    # /api/v1/candidates/*
|       +-- dashboard.py     # /api/v1/dashboard/*
|       +-- dev.py           # /api/v1/dev/*
|       +-- graph.py         # /api/v1/graph/*
|       +-- graph_ops.py     # /api/v1/graph/ops/*
|       +-- habitus.py       # /api/v1/habitus/*
|       +-- habitus_dashboard_cards.py
|       +-- log_fixer_tx.py  # /api/v1/log-fixer/*
|       +-- models.py        # API Datenmodelle
|       +-- mood.py          # /api/v1/mood/*
|       +-- neurons.py       # /api/v1/neurons/*
|       +-- notifications.py # /api/v1/notifications/*
|       +-- search.py        # /api/v1/search/*
|       +-- service.py       # Service-Layer Helfer
|       +-- swagger_ui.py    # /api/v1/docs (Swagger UI)
|       +-- user_hints.py    # /api/v1/user-hints/*
|       +-- user_preferences.py  # /api/v1/user/*
|       +-- vector.py        # /api/v1/vector/*
|       +-- voice_context_bp.py  # /api/v1/voice_context
|       +-- weather.py       # /api/v1/weather/*
|
+-- brain_graph/             # Brain Graph Subsystem
|   +-- api.py               # Brain Graph API
|   +-- bridge.py            # Bridge zu anderen Modulen
|   +-- feeding.py           # Graph Feeding (Event -> Node/Edge)
|   +-- model.py             # Datenmodelle (Node, Edge, GraphState)
|   +-- provider.py          # Graph State Provider
|   +-- render.py            # SVG Rendering
|   +-- service.py           # Brain Graph Service (Pruning, Patterns)
|   +-- store.py             # In-Memory Store mit JSON-Persistenz
|
+-- candidates/              # Candidate Management
|   +-- api.py               # Candidates API
|   +-- store.py             # Candidate Store
|
+-- collective_intelligence/ # Federated Learning (Phase 5)
|   +-- api.py               # /api/v1/federated/*
|   +-- federated_learner.py
|   +-- knowledge_transfer.py
|   +-- model_aggregator.py
|   +-- models.py
|   +-- privacy_preserver.py # Differential Privacy
|   +-- service.py
|
+-- dev_surface/             # Debug und Diagnose
|   +-- api.py
|   +-- models.py
|   +-- service.py
|
+-- energy/                  # Energy Neuron
|   +-- api.py               # /api/v1/energy/*
|
+-- habitus/                 # Habitus Service Layer
|   +-- api.py               # /api/v1/habitus/*
|   +-- miner.py
|   +-- service.py
|
+-- habitus_miner/           # Habitus Mining Engine
|   +-- mining.py            # Association Rule Mining
|   +-- model.py
|   +-- service.py
|   +-- store.py             # Pattern Store
|   +-- zone_mining.py       # Zone-basiertes Mining
|
+-- ingest/                  # Event Processing Pipeline
|   +-- event_processor.py
|   +-- event_store.py
|
+-- knowledge_graph/         # Knowledge Graph
|   +-- api.py               # /api/v1/kg/*
|   +-- builder.py
|   +-- graph_store.py
|   +-- models.py
|   +-- pattern_importer.py
|
+-- log_fixer_tx/            # Log Recovery
|   +-- operations.py
|   +-- recovery.py
|
+-- mood/                    # Mood Engine
|   +-- actions.py
|   +-- api.py               # /api/v1/mood/*
|   +-- engine.py            # Scoring-Logik
|   +-- orchestrator.py
|   +-- scoring.py
|   +-- service.py
|
+-- neurons/                 # Bewertungs-Neuronen (12+)
|   +-- base.py              # Basis-Neuron Klasse
|   +-- camera.py
|   +-- context.py
|   +-- energy.py
|   +-- mood.py
|   +-- presence.py
|   +-- state.py
|   +-- unifi.py
|   +-- weather.py
|
+-- sharing/                 # Cross-Home Sync (Phase 5)
|   +-- api.py               # /api/v1/sharing/*
|
+-- storage/                 # Persistenz-Layer
|   +-- candidates.py
|   +-- events.py
|   +-- user_preferences.py
|
+-- synapses/                # Synapse Manager
|   +-- manager.py
|   +-- models.py
|
+-- system_health/           # System Health Checks
|   +-- service.py
|
+-- tags/                    # Tag Registry
```

---

## 2. Module und Abhaengigkeiten

### Abhaengigkeitsgraph (vereinfacht)

```
Event Ingest
    |
    v
Brain Graph  <-->  Knowledge Graph
    |                    |
    v                    v
Habitus Miner      Vector Store
    |
    v
Candidates  -->  Notifications
    |
    v
Mood Engine  <--  Neurons (12+)
    |
    v
Synapses  -->  User Preferences
```

### Modul-Details

| Modul | Abhaengigkeiten | Persistenz |
|-------|----------------|------------|
| Event Ingest | -- | Optional (JSONL) |
| Brain Graph | Event Ingest | Optional (JSON) |
| Habitus Miner | Brain Graph, Event Ingest | In-Memory |
| Candidates | Habitus Miner | Optional (JSON) |
| Mood Engine | Neurons | In-Memory |
| Neurons | Event Ingest, Brain Graph | In-Memory |
| Knowledge Graph | Brain Graph | In-Memory |
| Vector Store | -- | In-Memory |
| Tags | -- | In-Memory |
| Search | Brain Graph, Knowledge Graph | In-Memory |
| Notifications | Mood, Candidates | In-Memory |
| System Health | Alle Module | -- |
| Collective Intelligence | Brain Graph, Habitus | In-Memory |
| Cross-Home Sync | Brain Graph | In-Memory |

### Python-Abhaengigkeiten (Dockerfile)

| Paket | Version | Zweck |
|-------|---------|-------|
| flask | 3.0.2 | Web Framework |
| flask-compress | 1.14 | GZIP Compression |
| waitress | 3.0.0 | WSGI Server (Produktion) |
| python-ulid | 2.7.0 | Unique IDs |
| pyyaml | 6.0.1 | YAML Parsing |
| psutil | 6.1.0 | System-Metriken |
| neo4j | 5.26.0 | Graph DB (optional) |
| pydantic | 2.12.5 | Datenvalidierung |

---

## 3. API Endpoints Uebersicht

### Basis-Endpoints (direkt auf App)

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | `/` | Index / Info |
| GET | `/health` | Health Check |
| GET | `/version` | Version Info |
| GET | `/api/v1/status` | API Status |
| GET | `/api/v1/capabilities` | Modul-Capabilities |
| POST | `/api/v1/echo` | Echo (Auth-Test) |

### Blueprint-registrierte Endpoints

| Bereich | Prefix | Blueprint-Datei | Beschreibung |
|---------|--------|----------------|-------------|
| Events | `/api/v1/events` | events.py | Event Ingest und Query |
| Brain Graph | `/api/v1/graph/` | graph.py | State, Stats, Snapshot, Prune |
| Graph Ops | `/api/v1/graph/` | graph_ops.py | Link, Unlink, Patterns |
| Habitus | `/api/v1/habitus/` | habitus.py | Mine, Rules, Stats, Status |
| Habitus Cards | `/api/v1/habitus/` | habitus_dashboard_cards.py | Dashboard Cards |
| Candidates | `/api/v1/candidates/` | candidates.py | CRUD, Stats, Cleanup |
| Mood | `/api/v1/mood/` | mood.py | Snapshot, Zone, Summary |
| Neurons | `/api/v1/neurons/` | neurons.py | State, Updates |
| Search | `/api/v1/search/` | search.py | Entity Search, Index |
| Notifications | `/api/v1/notifications/` | notifications.py | Push, Subscribe |
| Dashboard | `/api/v1/dashboard/` | dashboard.py | Brain Summary |
| Weather | `/api/v1/weather/` | weather.py | Wetter, PV |
| User Preferences | `/api/v1/user/` | user_preferences.py | Praeferenzen |
| User Hints | `/api/v1/user-hints/` | user_hints.py | Nutzer-Hinweise |
| Voice Context | `/api/v1/voice_context` | voice_context_bp.py | Sprachsteuerung |
| Vector Store | `/api/v1/vector/` | vector.py | Store, Search |
| Knowledge Graph | `/api/v1/kg/` | knowledge_graph/api.py | Nodes, Edges |
| Dev | `/api/v1/dev/` | dev.py | Logs, Debug |
| Swagger UI | `/api/v1/docs` | swagger_ui.py | API Dokumentation |
| Sharing | `/api/v1/sharing/` | sharing/api.py | Cross-Home Sync |
| Federated | `/api/v1/federated/` | collective_intelligence/api.py | Federated Learning |

### Standalone Blueprints (via core_setup.register_blueprints)

Diese Blueprints haben absolute URL-Prefixes und werden direkt auf der Flask-App registriert:

- Energy API (`/api/v1/energy/`)
- UniFi API (`/api/v1/unifi/`)
- System Health API (`/api/v1/system-health/`)
- Tags API (`/api/v1/tag-system/`)
- Dev Surface API

Gesamt: **37+ API Blueprints**

---

## 4. Test-Struktur

### Testdateien im Repository

| Datei / Verzeichnis | Beschreibung |
|---------------------|-------------|
| `test_capabilities.py` | API Capabilities Test |
| `test_new_endpoints.py` | Neue Endpoint Tests |
| `core/sharing/tests/test_conflict.py` | Konfliktloesung Tests |
| `core/sharing/tests/test_discovery.py` | mDNS Discovery Tests |
| `core/sharing/tests/test_registry.py` | Registry Tests |
| `core/sharing/tests/test_sync.py` | Synchronisation Tests |
| `core/sharing/tests/test_integration.py` | Integrationstests |

### Test-Ausfuehrung

```bash
# Alle Tests ausfuehren
pytest

# Mit Verbose Output
pytest -v

# Einzelne Testdatei
pytest test_capabilities.py

# Sharing-Tests
pytest core/sharing/tests/
```

### Test-Abdeckung

| Bereich | Tests | Status |
|---------|-------|--------|
| Core API | 44+ | Bestanden |
| Brain Graph | 8+ | Bestanden |
| Habitus | 15+ | Bestanden |
| Federated Learning | 11+ | Bestanden |
| Cross-Home Sync | 9+ | Bestanden |
| System Health | 23+ | Bestanden |
| Home Alerts | 37+ | Bestanden |
| **Gesamt** | **521+** | **Bestanden** |

---

*Letzte Aktualisierung: 2026-02-16 -- PilotSuite v0.9.0-alpha.1*
