# HA Concept Directive — PilotSuite HA Integration Layer

**Version:** 15.4.0  
**Lane:** HomeClaw / HA-Integration  
**Principle:** HA = Integration + Projection. Core holds truth.

---

## 1. Architektur-Prinzip

| Layer | Verantwortung | Darf NICHT |
|-------|------------|------------|
| **Core** | Semantische Wahrheit, Module, Brain, ML, Knowledge-Graph | Keine HA-spezifische Logik |
| **HA** | Integration, Projection, Sensoren, UI-Read-Models, Ausführung | Keine Core-Logik |

**Quelle:** Andreas Direktive 2026-03-21 — Core-Funktionalität MUSS in Core sein.

---

## 2. Projection-Regeln

HA-Sensoren projizieren Core-Truth. Regeln:

1. **Nur Core lesen** — Sensoren lesen `/api/v1/` Endpoints, keine eigene Semantik erfinden
2. **Rebatch-Kontrolle** — Core-State-Änderungen fließen in HA-Sensoren
3. **Keine Core-Logik replizieren** — brain_graph, habitus, ml/, knowledge_graph, vector_client = **Core**, nicht HA
4. **Coordinator-Only** — HA-Coordinator fungiert als Cache + Rebatch-Layer

---

## 3. Erlaubte HA-spezifische Logik

Diese Dateien sind **HA-lokal** (kein Core):

- `cognitive_sensors.py` — liest HA-States (media_player, calendar, etc.)
- `habit_learning_v2.py` — HA-lokales Lernen
- `media_sensors.py` — HA-lokale Medienerkennung
- `energy_sensors.py` — Coordinator-basiert
- `presence_sensors.py` — Coordinator-basiert
- `time_sensors.py` — HA-Zeit-basiert
- `sensors/activity_sensors.py` — HA-Coordinator
- `blueprints/automation/` — Benutzer-Automatisierungen

---

## 4. Core-Logik in HA (Architektur-Verletzungen — HA-67)

Diese Dateien gehören nach Core, nicht HA:

| Datei | Kern-Funktionalität |
|-------|-------------------|
| `brain_graph_panel.py` | Graph-Datenstruktur |
| `brain_graph_sync.py` | Graph-Sync-Logik |
| `brain_graph_viz.py` | Graph-Visualisierung |
| `habitus_adapter.py` | HabitUs-Adapter |
| `habitus_dashboard*.py` (5) | HabitUs-Dashboard |
| `habitus_zones*.py` (4) | HabitUs-Zonen |
| `habitus_entity_sorting.py` | Entity-Sorting |
| `habitus_miner_entities.py` | HabitUs-Miner |
| `habitus_module_schema.py` | HabitUs-Schema |
| `ml/patterns/*.py` (5) | ML-Pattern-Erkennung |
| `ml/inference/*.py` (1) | ML-Inferenz |
| `knowledge_graph_entities.py` | Knowledge-Graph |
| `vector_client.py` | Vektor-Suche |
| `ml_context.py` | ML-Kontext |
| `learning_analytics.py` | Lern-Analyse |

→ **Handoff an PilotClaw:** `/config/clawd/team/shared/handoffs/handoff_homeclaw_pilotclaw_2026-04-05_HA67_BRAINGRAPH_HABITUS.md`

---

## 5. Fehlende Core-Endpoints (Bug-Report)

Diese HA-Sensoren rufen Core-Endpoints auf, die nicht existieren:

| Sensor | Fehlender Endpoint | Aktion |
|--------|------------------|--------|
| `appliance_fingerprint_sensor.py` | `GET /api/v1/energy/fingerprints` | → Bug-Report PilotClaw |
| `comfort_index_sensor.py` | `GET /api/v1/comfort` | → Bug-Report PilotClaw |
| `demand_response_sensor.py` | `GET /api/v1/energy/demand-response/status` | → Bug-Report PilotClaw |

→ **Report:** `/config/clawd/team/shared/homeclaw/HA_BROKEN_SENSORS_2026-04-05.md`

---

## 6. Verhalten bei fehlenden Core-Endpoints

Solange Core-Endpoints fehlen:
- Sensor-State auf `unavailable` oder Default-Wert
- Keine Exceptions in `async_update`
- Logging via `_LOGGER.error()`

---

## 7. Test-Requirements

Alle Projection-Sensoren brauchen:
- `tests/test_*_projection.py` — Projection-Contract-Test
- PS-151 Drift Guard muss grün sein vor jedem Commit

---

## 8. Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 15.4.0 | 2026-04-05 | Projection-Testsuite, PS-151 Drift Guard, API-Syntax-Fix |
| 15.3.40 | 2026-04-05 | Projection Contract Test Suite (44 Sensoren) |

---

**Genehmigt:** Andreas Betz  
**Herausgeber:** HomeClaw / openclaw-main
