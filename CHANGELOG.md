# Changelog

## [v15.3.0] - 2026-04-01

### 🎯 Life-Long-Learning Integration

**Zone Sync (Core ↔ HA):**
- Bidirektionale Synchronisation
- Module State Sync (active/learning/off)
- Entity Tag Sync (automatische Zuordnung)
- Real-time Updates

**Tag System:**
- 9 Domain-Kategorien
- 10 Zone-Tags
- 3 Status-Tags
- Automatische Entity→Zone Zuordnung

### 📡 APIs (via Core)

**Habitus API:**
- `GET /api/v1/habitus` — Overview + Stats
- `GET /api/v1/habitus/patterns` — Gelernte Patterns
- `POST /api/v1/habitus/feedback` — Feedback geben
- `GET /api/v1/habitus/preferences` — Nutzer-Präferenzen

**Chat API:**
- `POST /api/v1/chat/sessions` — Session erstellen
- `POST /api/v1/chat/sessions/<id>/messages` — Nachricht senden
- `POST /api/v1/chat/webhooks/telegram` — Telegram Webhook
- `POST /api/v1/chat/webhooks/rest` — REST Webhook

**Learning Viz:**
- `GET /api/v1/learning/overview` — Intelligence Score
- `GET /api/v1/learning/patterns` — Patterns (visualisiert)
- `POST /api/v1/learning/correct` — Manuelle Korrektur

### 🔧 Services

**NEU:**
- `copilot_ha.sync_zones` — Zonen synchronisieren
- `copilot_ha.set_module_state` — Module-State setzen
- `copilot_ha.add_feedback` — Feedback geben

### 📊 Entities

**Sensors:**
- `sensor.pilotsuite_system_health` — Core Health
- `sensor.pilotsuite_intelligence_score` — Intelligence Score (0-100)
- `sensor.pilotsuite_patterns_learned` — Gelernte Patterns
- `sensor.pilotsuite_active_automations` — Aktive Automatisierungen
- `sensor.pilotsuite_mood_state` — Aktuelle Stimmung

**Buttons:**
- `button.pilotsuite_sync_zones` — Zonen synchronisieren
- `button.pilotsuite_clear_cache` — Cache leeren

### 🎴 Lovelace Cards (Vorbereitet)

- `styx-modules-card` — Module-Übersicht
- `styx-zone-card` — Zonen-Status
- `styx-learning-card` — Lern-Fortschritt
- `styx-chat-card` — Chat-Interface

### 📖 Dokumentation

**NEU:**
- `README.md` — Vollständige Doku (180 Zeilen)

### 📊 Code-Statistik

| Metrik | Wert |
|--------|------|
| **Integration** | Core v15.3.0 |
| **Zone Sync** | Bidirektional |
| **Tag Categories** | 9+10+3 |
| **Services** | 3 |
| **Entities** | 7+ |

### 🎯 Vision-Status

| Vision-Element | Status |
|----------------|--------|
| **Zone Sync** | ✅ Core ↔ HA |
| **Tag System** | ✅ Auto-Assign |
| **Module Config** | ✅ active/learning/off |
| **Chat Integration** | ✅ Vorbereitet |
| **Learning Viz** | ✅ API bereit |

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

**🚀 v15.3.0 — INTEGRATION DES LERNENDEN DACHSYSTEMS.**
