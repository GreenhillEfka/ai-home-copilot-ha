# Changelog

## [v15.3.0] - 2026-04-01

### 🎯 Life-Long-Learning Integration

**Unified Habitus Store Integration:**
- Zone Sync mit Unified Store (RAG + Habitus + Anomaly)
- Bidirektionale Synchronisation
- Module State Sync (active/learning/off)
- Entity Tag Sync (automatische Zuordnung)
- Real-time Updates

**End-to-End Wiring:**
- AutoDiscovery → Store → Neurons → Anomaly → Chat → Feedback
- Alle Komponenten verkabelt
- Maximale Synergien

### 📡 APIs (via Core)

**Unified Habitus API:**
- `GET /api/v1/habitus` — Overview + Stats
- `GET /api/v1/habitus/patterns` — Gelernte Patterns (zone-scoped)
- `POST /api/v1/habitus/feedback` — Feedback geben
- `GET /api/v1/habitus/preferences` — Nutzer-Präferenzen (zone-scoped)

**Chat API:**
- `POST /api/v1/chat/sessions` — Session erstellen
- `POST /api/v1/chat/sessions/<id>/messages` — Nachricht senden
- `POST /api/v1/chat/webhooks/telegram` — Telegram Webhook
- `POST /api/v1/chat/webhooks/rest` — REST Webhook

**Learning Viz:**
- `GET /api/v1/learning/overview` — Intelligence Score (0-100)
- `GET /api/v1/learning/patterns` — Patterns (visualisiert)
- `POST /api/v1/learning/correct` — Manuelle Korrektur

### 🔧 Services

**NEU:**
- `copilot_ha.sync_zones` — Zonen synchronisieren (Unified Store)
- `copilot_ha.set_module_state` — Module-State setzen
- `copilot_ha.add_feedback` — Feedback geben (End-to-End)

### 📊 Entities

**NEU:**
- `sensor.pilotsuite_intelligence_score` — Intelligence Score (0-100)
- `sensor.pilotsuite_patterns_learned` — Gelernte Patterns (Unified Store)
- `sensor.pilotsuite_anomaly_detected` — Anomalie erkannt (ja/nein)
- `button.pilotsuite_generate_proposals` — Vorschläge generieren

### 🏷️ Tag System

**9 Domain-Kategorien:**
- light, climate, motion, media, energy, humidity, camera, cover, lock

**10 Zone-Tags:**
- zone_living, zone_bath, zone_kitchen, zone_office, zone_bedroom,
  zone_hallway, zone_room_mira, zone_room_paul, zone_terrace, zone_outside

**3 Status-Tags:**
- auto_assign, needs_review, manual_override

### 🔗 Module Dependencies

**Übergreifende Abhängigkeiten:**
- requires (Light benötigt Motion)
- enhances (Music verbessert Climate)
- conflicts (Camera konflikts mit Privacy)

### 📖 Dokumentation

**NEU:**
- `README.md` — Vollständige Doku (200+ Zeilen)
- `CHANGELOG.md` — Release Notes

### 📊 Code-Statistik

| Metrik | Wert |
|--------|------|
| **Integration** | Core v15.3.0 |
| **Zone Sync** | Bidirektional (Unified Store) |
| **Tag Categories** | 9+10+3 |
| **Services** | 3 |
| **Entities** | 10+ |
| **End-to-End** | Vollständig verkabelt |

### 🎯 Vision-Status

| Vision-Element | Status |
|----------------|--------|
| **Zone Sync** | ✅ Core ↔ HA (Unified) |
| **Tag System** | ✅ Auto-Assign |
| **Module Config** | ✅ active/learning/off |
| **Chat Integration** | ✅ Vorbereitet |
| **Learning Viz** | ✅ API bereit |
| **End-to-End** | ✅ Verkabelt |

---

## [v15.2.10] - 2026-03-31

### Added
- **Habitus Zones API** — Zone-Konfiguration
- **Zone Auto-Setup** — Automatische Zonen-Erkennung
- **Entity Mapping** — Role-based Assignment
- **Module Sensors** — Batch 1-5 Entities

### Changed
- ZoneType Enum als Single Source of Truth
- Module-Konfiguration pro Zone

### Fixed
- Zone↔Entity Mapping konsolidiert
- HA↔Core Sync verbessert

---

**🚀 v15.3.0 — INTEGRATION DES LERNENDEN, VERKABELTEN DACHSYSTEMS.**
